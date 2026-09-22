#!/usr/bin/env python3
"""Caixa vigiada pelo Jev: e-mail que pede atenção vira alerta no WhatsApp na hora.

Roda a cada 30 minutos, das 7h às 22h, sem acordar o modelo principal. O código lista o que
chegou na caixa de entrada nas últimas 24 horas e ainda não foi visto; o Jev classifica cada
e-mail com a mesma triagem da revisão diária; o código formata o alerta.

Alerta só quando a probabilidade somada de ação, cliente/pessoa, jurídico ou financeiro chega
a 0,60 e o e-mail não é descartável (newsletter, promoção, aviso rotineiro). Alertas técnicos
ficam para a revisão diária. E-mails de Fábio ficam com o ARCANO, que já os trata.
Na primeira execução só marca o que existe como visto, para não despejar a caixa inteira.
"""
import json
import sys

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

JOB = 'caixa-vigiada'
ESTADO = nucleo.ESTADO / 'rotina-caixa-vigiada.json'
CONSULTA = 'in:inbox newer_than:1d -from:fabio@medinaosorio.adv.br -category:promotions -category:social'
IMPORTANTES = {'acao-de-igor', 'pessoal-ou-cliente', 'juridico-ou-governo', 'financeiro'}
CORTE = 0.60
ROTULO = {'acao-de-igor': 'pede ação sua', 'pessoal-ou-cliente': 'pessoa/cliente',
          'juridico-ou-governo': 'jurídico/órgão público', 'financeiro': 'financeiro'}


def main():
    estado = json.loads(ESTADO.read_text(encoding='utf-8')) if ESTADO.exists() else {}
    vistos = set(estado.get('vistos') or [])
    ids = portao.gmail_listar(CONSULTA, maximo=40)
    novos = [i for i in ids if i not in vistos]
    primeira = not estado
    alertas = []
    custo = 0.0
    if novos and not primeira:
        mensagens = [portao.gmail_cabecalhos(i) for i in novos[:15]]
        estados = [f"DE: {m['de']}\nASSUNTO: {m['assunto']}\nTRECHO: {m['trecho']}" for m in mensagens]
        resultados = nucleo.classificar_em_paralelo(estados, portao.CATEGORIA_DE_EMAIL, origem='rotina-caixa-vigiada',
                                                    tempo_total=30, limite=4000)
        custo = nucleo.resumo_das_chamadas(resultados)['custo_usd']
        for m, (respostas, _) in zip(mensagens, resultados):
            if respostas is None:
                continue  # sem triagem não alerta; a revisão diária cobre
            classe, _ = nucleo.escolha(respostas, 'categoria')
            if portao.email_descartavel(respostas, m):
                continue
            if portao.probabilidade(respostas, 'categoria', IMPORTANTES) >= CORTE and classe in IMPORTANTES:
                remetente = m['de'].split('<')[0].strip().strip('"') or m['de']
                alertas.append(f"• {ROTULO[classe]} — {remetente[:60]}: {m['assunto'][:110]}")
    estado['vistos'] = (list(novos) + [i for i in (estado.get('vistos') or []) if i in set(ids)])[:500]
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False), encoding='utf-8')
    portao.registrar(JOB, bool(alertas), f'{len(novos)} novo(s), {len(alertas)} alerta(s)'
                     + (' (primeira execução: só marcou)' if primeira else ''), custo_jev_usd=custo)
    if alertas:
        print('📬 E-mail que pede sua atenção (triagem do Jev)')
        print('\n'.join(alertas))


if __name__ == '__main__':
    main()
