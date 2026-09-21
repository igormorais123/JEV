#!/usr/bin/env python3
"""Porteiro do job email-revisao-diaria-whatsapp (a3288e4d3f60), uma vez ao dia.

Antes: o modelo principal listava os não lidos da semana, abria os cabeçalhos um a um e
separava o relevante do promocional — triagem pura, a aplicação 1 do estudo (Jev 92,5% a 98,9%
contra 60% da regra por palavra).

Agora o porteiro lista e abre os cabeçalhos por código, e o Jev classifica cada e-mail. Um
e-mail é descartado quando a probabilidade somada das classes descartáveis (newsletter,
promocional, notificação rotineira) chega a 0,90, ou a 0,50 com o próprio Gmail já o tendo
posto em Promoções, Social ou Fóruns — dois sinais independentes concordando. O agente só
acorda se sobrar algo, e acorda com a lista pronta, sem precisar abrir nada para triar.
"""
import sys

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

JOB = 'email-revisao-diaria'
CONSULTA = 'is:unread newer_than:7d'
MAXIMO = 20
CATEGORIA = portao.CATEGORIA_DE_EMAIL


def main():
    ids = portao.gmail_listar(CONSULTA, maximo=MAXIMO)
    if not ids:
        portao.encerrar(JOB, False, 'nenhum não lido na semana')
        return
    mensagens = [portao.gmail_cabecalhos(i) for i in ids]
    estados = [f"DE: {m['de']}\nASSUNTO: {m['assunto']}\nTRECHO: {m['trecho']}" for m in mensagens]
    resultados = nucleo.classificar_em_paralelo(estados, CATEGORIA, origem='portao-email-diario',
                                                tempo_total=25, limite=4000)
    resumo = nucleo.resumo_das_chamadas(resultados)
    relevantes, descartados = [], 0
    for m, (respostas, _) in zip(mensagens, resultados):
        classe, confianca = nucleo.escolha(respostas, 'categoria')
        if portao.email_descartavel(respostas, m):
            descartados += 1
        else:
            relevantes.append((m, classe or 'sem triagem', confianca))
    if not relevantes:
        portao.encerrar(JOB, False, f'{descartados} não lidos, todos descartáveis',
                        listados=len(ids), custo_jev_usd=resumo['custo_usd'])
        return
    linhas = [f'[jev/portão] Triagem pronta dos {len(ids)} não lidos da semana: {len(relevantes)} relevante(s) '
              f'abaixo; {descartados} newsletter(s), promoção(ões) ou aviso(s) rotineiro(s) já descartado(s). '
              'Use esta lista; abra um ID só se precisar do corpo para decidir.']
    for m, classe, confianca in relevantes:
        linhas.append(f"- {m['id']} | {classe} ({nucleo.dec(confianca)}) | {m['de'][:80]} | {m['assunto'][:120]}")
    portao.encerrar(JOB, True, f'{len(relevantes)} e-mail(s) relevante(s)', '\n'.join(linhas),
                    listados=len(ids), relevantes=len(relevantes), custo_jev_usd=resumo['custo_usd'])


if __name__ == '__main__':
    portao.executar(JOB, main)
