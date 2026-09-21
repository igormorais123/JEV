#!/usr/bin/env python3
"""Porteiro do job Monitor Fábio Osório — WhatsApp pessoal (19fa0f01b2c5), 3 vezes ao dia.

Antes: o modelo principal acordava, lia o painel canônico e o SQLite, e em 49 das 50 execuções
anteriores concluía que não havia mudança.

Agora o porteiro faz as duas checagens que o prompt manda fazer primeiro:
1. painel canônico (`office-demand-panel priorities --json`): o fingerprint mudou em relação ao
   heartbeat, ou o estado ok/stale mudou desde a última checagem? Então acorda.
2. mensagens do chat depois do cursor do monitor: se houver, o Jev lê a conversa nova e diz se
   há mudança operacional. Só dorme se o Jev disser conversa social ou nada aplicável com
   confiança ≥ 0,99 (o corte do guia para decisão automática); qualquer outra resposta acorda.
Sem mensagem nova e sem mudança no painel, o agente não acorda.
"""
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

JOB = 'monitor-fabio-whatsapp'
BANCO = Path('/root/.hermes/state/whatsapp-personal/messages.sqlite')
CURSOR = Path('/root/.hermes/state/fabio_osorio_monitor.json')
HEARTBEAT = Path('/root/.hermes/state/office-demand-panel/heartbeat-monitor-fabio.json')
MEMORIA = nucleo.ESTADO / 'portao-fabio-whatsapp.json'
PAINEL = ['/root/.hermes/bin/office-demand-panel', 'priorities', '--json', '--limit', '20']
CHAT = '60855441973370@lid'
FUSO = timezone(timedelta(hours=-3))
CORTE_PARA_DORMIR = 0.99

MUDANCA = {
    'mudanca': {
        'type': 'choice',
        'instructions': ('Trecho novo da conversa de WhatsApp entre Igor e o advogado Fabio, cliente '
                         'de Igor. Ha mudanca operacional para Igor? Considere o que Fabio pede ou '
                         'informa agora; conversa ja resolvida ou cortesia nao conta.'),
        'criteria': {
            'pedido-novo': 'Fabio pede algo novo a Igor ou muda um pedido anterior.',
            'prazo-ou-cobranca': 'Fabio cobra pendencia, informa prazo, audiencia ou urgencia.',
            'entrega-ou-documento': 'Fabio envia ou pede documento, anexo ou peca.',
            'resposta-a-pendencia': 'Fabio responde ou decide sobre algo que Igor enviou.',
            'conversa-social': 'Cumprimento, agradecimento, confirmacao simples, sem acao.',
            'nao-se-aplica': 'Nada disso se aplica.',
        },
    },
}


def mensagens_novas(desde):
    conexao = sqlite3.connect(f'file:{BANCO}?mode=ro', uri=True)
    try:
        return conexao.execute(
            'SELECT timestamp, direction, sender_name, body, message_type, has_media FROM messages '
            'WHERE chat_id=? AND timestamp>? ORDER BY timestamp', (CHAT, desde)).fetchall()
    finally:
        conexao.close()


def main():
    cursor = json.loads(CURSOR.read_text(encoding='utf-8')) if CURSOR.exists() else {}
    heartbeat = json.loads(HEARTBEAT.read_text(encoding='utf-8')) if HEARTBEAT.exists() else {}
    memoria = json.loads(MEMORIA.read_text(encoding='utf-8')) if MEMORIA.exists() else {}
    painel = portao.json_da_saida(portao.rodar(PAINEL, timeout=90))
    situacao_painel = {'ok': painel.get('ok'), 'stale': painel.get('stale')}
    motivos = []
    if painel.get('notificationFingerprint') != heartbeat.get('notificationFingerprint'):
        motivos.append('fingerprint do painel mudou')
    if memoria.get('situacao_painel') not in (None, situacao_painel):
        motivos.append(f'painel mudou de estado: {situacao_painel}')
    MEMORIA.parent.mkdir(parents=True, exist_ok=True)
    MEMORIA.write_text(json.dumps({'situacao_painel': situacao_painel,
                                   'em': datetime.now(FUSO).isoformat()}, ensure_ascii=False), encoding='utf-8')

    desde = int(cursor.get('last_timestamp') or 0) or int(datetime.now(FUSO).timestamp()) - 86400
    novas = mensagens_novas(desde)
    contexto = []
    custo = 0.0
    if novas:
        def linha(t, d, n, b, tipo):
            quem = 'Igor' if d == 'outbound' else (n or 'Fábio')
            texto = (b or '').strip() or '[' + (tipo or 'mídia') + ']'
            return f'{datetime.fromtimestamp(t, FUSO):%d/%m %H:%M} {quem}: {texto}'
        conversa = '\n'.join(linha(t, d, n, b, tipo) for t, d, n, b, tipo, _ in novas)[-11000:]
        respostas, detalhe = nucleo.perguntar(f'CONVERSA NOVA:\n{conversa}', MUDANCA,
                                              origem='portao-fabio-whatsapp', timeout=12)
        custo = detalhe.get('custo_usd') or 0.0
        classe, confianca = nucleo.escolha(respostas, 'mudanca')
        social = classe in ('conversa-social', 'nao-se-aplica') and (confianca or 0) >= CORTE_PARA_DORMIR
        tem_midia = any(m[5] for m in novas)
        if respostas is None or not social or tem_midia:
            motivos.append(f'{len(novas)} mensagem(ns) nova(s)')
        contexto.append(f'[jev/portão] {len(novas)} mensagem(ns) nova(s) no chat de Fábio desde o cursor; '
                        f'leitura do Jev: {classe or "sem resposta"} (confiança {nucleo.dec(confianca)})'
                        f'{"; há mídia" if tem_midia else ""}. Consultivo: confira no SQLite antes de avisar.')
    if not motivos:
        portao.encerrar(JOB, False, 'painel igual e nada novo que peça ação', novas=len(novas),
                        custo_jev_usd=round(custo, 8))
        return
    contexto.insert(0, '[jev/portão] motivos para acordar: ' + '; '.join(motivos) + '.')
    portao.encerrar(JOB, True, '; '.join(motivos), '\n'.join(contexto), novas=len(novas),
                    custo_jev_usd=round(custo, 8))


if __name__ == '__main__':
    portao.executar(JOB, main)
