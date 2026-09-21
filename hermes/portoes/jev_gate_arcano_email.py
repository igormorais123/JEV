#!/usr/bin/env python3
"""Porteiro do job ARCANO — e-mails de Fábio (6b539f9271ed), a cada 30 minutos.

Antes: o modelo principal acordava 48 vezes por dia, com prompt de ~71 KB, para descobrir que
não havia e-mail novo; 43 das 50 execuções anteriores terminaram em [SILENT].

Agora: o código lista os IDs de fabio@medinaosorio.adv.br dos últimos 30 dias e compara com
`processed_message_ids` do estado canônico. Sem ID novo, o agente não acorda. Com ID novo, ele
sempre acorda — e-mail de cliente não é vetado pelo Jev —, mas já recebe a triagem do Jev
de cada mensagem (natureza, se exige resposta), para ir direto ao que importa.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

JOB = 'arcano-email-fabio'
ESTADO = Path('/root/.hermes/state/arcano-fabio-email-monitor.json')
CONSULTA = 'from:fabio@medinaosorio.adv.br newer_than:30d'

TRIAGEM = {
    'natureza': {
        'type': 'choice',
        'instructions': ('E-mail recebido por Igor de um cliente advogado. Considere apenas o que '
                         'quem escreve pede a Igor. Classifique a natureza da mensagem.'),
        'criteria': {
            'pedido-ou-tarefa': 'Pede que Igor faca, revise, envie ou decida algo.',
            'prazo-ou-cobranca': 'Cobra algo pendente ou informa prazo, audiencia ou urgencia.',
            'documento-ou-informacao': 'Envia documento ou informacao sem pedir acao imediata.',
            'confirmacao-ou-agradecimento': 'Confirma recebimento, agradece ou encerra assunto.',
            'automatica-ou-encaminhada': 'Mensagem automatica, convite de agenda ou encaminhamento sem pedido.',
            'nao-se-aplica': 'Nao se encaixa em nenhuma das opcoes acima.',
        },
    },
    'exige_resposta': {
        'type': 'noul',
        'instructions': 'A mensagem espera uma resposta escrita de Igor?',
    },
}


def main():
    estado = json.loads(ESTADO.read_text(encoding='utf-8'))
    processados = set(estado.get('processed_message_ids') or [])
    ids = portao.gmail_listar(CONSULTA)
    novos = [i for i in ids if i not in processados]
    if not novos:
        portao.encerrar(JOB, False, 'nenhum e-mail novo de Fábio', listados=len(ids))
        return
    linhas = [f'[jev/portão] {len(novos)} e-mail(s) novo(s) de Fábio ainda não processado(s). '
              'Triagem do Jev (consultiva; leia cada mensagem antes de agir):']
    custo = 0.0
    for identificador in novos[:10]:
        m = portao.gmail_cabecalhos(identificador)
        estado_jev = (f"DE: {m['de']}\nASSUNTO: {m['assunto']}\nDATA: {m['data']}\n"
                      f"TRECHO: {m['trecho']}")
        respostas, detalhe = nucleo.perguntar(estado_jev, TRIAGEM, origem='portao-arcano', timeout=10)
        custo += detalhe.get('custo_usd') or 0.0
        if respostas:
            natureza, confianca = nucleo.escolha(respostas, 'natureza')
            resposta = (respostas.get('exige_resposta') or {}).get('noul')
            triagem = (f'{natureza} (confiança {nucleo.dec(confianca)}), '
                       f'exige resposta p={nucleo.dec(resposta)}')
        else:
            triagem = f"sem triagem do Jev ({detalhe.get('erro')})"
        linhas.append(f"- {identificador} | {m['data']} | {m['assunto'][:120]} — {triagem}")
    if len(novos) > 10:
        linhas.append(f'- e mais {len(novos) - 10} mensagem(ns) sem triagem.')
    portao.encerrar(JOB, True, 'e-mail novo de Fábio', '\n'.join(linhas), novos=len(novos),
                    custo_jev_usd=round(custo, 8))


if __name__ == '__main__':
    portao.executar(JOB, main)
