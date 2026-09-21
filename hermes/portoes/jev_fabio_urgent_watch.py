#!/usr/bin/env python3
"""Watchdog urgente de mensagens novas de Fábio Medina Osório (job 07bde220eec7, sem agente).

Versão com o Jev do `fabio_osorio_urgent_watch.py`, que continua no lugar como referência. A
diferença é uma só: quem decide se as mensagens novas são relevantes. Antes era uma lista de
22 palavras ("hoje", "email", "preciso"...), que dispara em cortesia e perde pedido escrito
com outras palavras — o E1 mediu palavra-chave a 60% e o Jev a 92,5% nessa tarefa.

Regra: mídia recebida sempre alerta. Sem mídia, o Jev lê a conversa nova; alerta se ele disser
qualquer coisa que não seja conversa social ou nada aplicável, ou se a confiança dele ficar
abaixo de 0,90. Se o Jev falhar, volta a valer a lista de palavras antiga.
"""
import json
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

DB = Path('/root/.hermes/state/whatsapp-personal/messages.sqlite')
STATE = Path('/root/.hermes/state/fabio_osorio_urgent_watch.json')
CHAT_ID = '60855441973370@lid'
FABIO = 'Fábio Medina Osório'
TZ = timezone(timedelta(hours=-3))
CORTE = 0.90
KEYWORDS = [
    'finep', 'proposta', 'email', 'e-mail', 'amanhã', 'hoje', 'urgente', 'prazo',
    'contrato', 'acordo', 'laudo', 'parecer', 'rescisória', 'embargos', 'document',
    'enviei', 'vou te enviar', 'me diga', 'preciso', 'consulta', 'sófia', 'sofia'
]
PERGUNTA = {
    'mudanca': {
        'type': 'choice',
        'instructions': ('Mensagens novas do advogado Fabio, cliente de Igor, no WhatsApp. Elas pedem '
                         'atencao de Igor agora? Considere o que Fabio pede ou informa a Igor.'),
        'criteria': {
            'pedido-ou-tarefa': 'Pede algo a Igor, manda fazer, revisar ou decidir.',
            'prazo-ou-urgencia': 'Cobra pendencia, informa prazo, audiencia ou urgencia.',
            'documento-ou-informacao': 'Envia ou pede documento, informacao ou contato relevante.',
            'conversa-social': 'Cumprimento, agradecimento, confirmacao simples, sem acao.',
            'nao-se-aplica': 'Nada disso se aplica.',
        },
    },
}


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save_state(ts):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({'last_ts': ts, 'updated_at': datetime.now(TZ).isoformat()},
                                ensure_ascii=False, indent=2))


def fmt_ts(ts):
    return datetime.fromtimestamp(ts, timezone.utc).astimezone(TZ).strftime('%d/%m %H:%M')


def main():
    if not DB.exists():
        print('ALERTA FÁBIO: não consegui acessar o banco do WhatsApp pessoal.')
        return
    last_ts = int(load_state().get('last_ts') or (time.time() - 2 * 3600))
    con = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute('select timestamp, sender_name, body, message_type, has_media from messages '
                       'where chat_id=? and timestamp>? and sender_name=? order by timestamp asc',
                       (CHAT_ID, last_ts, FABIO)).fetchall()
    con.close()
    if not rows:
        save_state(max(last_ts, int(time.time()) - 60))
        return
    max_ts = max(int(r['timestamp'] or 0) for r in rows)
    has_media = any(int(r['has_media'] or 0) for r in rows)
    conversa = '\n'.join(f"{fmt_ts(int(r['timestamp']))}: {(r['body'] or '').strip() or '[mídia]'}"
                         for r in rows)[-11000:]
    respostas, detalhe = nucleo.perguntar(f'MENSAGENS NOVAS DE FABIO:\n{conversa}', PERGUNTA,
                                          origem='watchdog-fabio', timeout=12)
    classe, confianca = nucleo.escolha(respostas, 'mudanca')
    if respostas is None:
        blob = '\n'.join((r['body'] or '') + ' ' + (r['message_type'] or '') for r in rows).lower()
        relevant = has_media or any(k in blob for k in KEYWORDS) or len(rows) >= 4
        criterio = f"palavras-chave (Jev indisponível: {detalhe.get('erro')})"
    else:
        social = classe in ('conversa-social', 'nao-se-aplica') and (confianca or 0) >= CORTE
        relevant = has_media or not social
        criterio = f'Jev: {classe} (confiança {nucleo.dec(confianca)})'
    portao.registrar('watchdog-fabio', relevant, criterio, novas=len(rows),
                     custo_jev_usd=detalhe.get('custo_usd'))
    save_state(max_ts)
    if not relevant:
        return
    snippets = []
    for r in rows[-5:]:
        body = (r['body'] or '').replace('\n', ' ').strip()
        if not body and int(r['has_media'] or 0):
            body = f"[{r['message_type'] or 'mídia'} recebida]"
        snippets.append(f"- {fmt_ts(int(r['timestamp']))}: {body[:220] + ('…' if len(body) > 220 else '')}")
    print('ALERTA FÁBIO — mensagens novas relevantes')
    print(f'{len(rows)} mensagem(ns) nova(s) de Fábio desde a última checagem.')
    print('Sinal: ' + ('anexo/mídia; ' if has_media else '') + criterio + '.')
    print('Últimos sinais:')
    print('\n'.join(snippets))
    print('Ação: peça ao Hermes “analise o Fábio agora” ou responda com prioridade se houver pedido direto.')


if __name__ == '__main__':
    main()
