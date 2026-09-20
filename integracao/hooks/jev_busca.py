#!/usr/bin/env python
"""Hook PostToolUse (Grep): quando o Grep devolve muitos arquivos, o Jev diz por onde começar.

Injeta uma nota curta com os arquivos classificados como essenciais ao pedido vigente e os
que ficaram como irrelevantes com confiança ≥ 0,99. Não esconde nada: a lista do Grep já está
no contexto. Lógica em `camadas/busca.py`.

Modo, pela variável `JEV_BUSCA_MODO` ou por `modo-busca.txt`: sombra registra; ativo injeta.
Falha para o lado aberto: sai em silêncio com código 0.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def main():
    try:
        sys.stdin.reconfigure(encoding='utf-8')
        dados = json.load(sys.stdin)
    except Exception:
        return 0
    if dados.get('tool_name') != 'Grep':
        return 0

    from camadas import busca, nucleo
    modo = nucleo.modo_vigente('JEV_BUSCA_MODO', RAIZ / 'modo-busca.txt')
    sessao = dados.get('session_id')
    try:
        pedido = nucleo.pedido_vigente(sessao, dados.get('transcript_path'))
        decisao = busca.analisar(dados.get('tool_response'), pedido, dados.get('tool_input'))
    except Exception as erro:
        nucleo.registrar('busca', modo=modo, sessao=sessao, acao='nada',
                         motivo=f'erro: {type(erro).__name__}')
        return 0
    nucleo.registrar('busca', modo=modo, sessao=sessao, com_pedido=bool(pedido), **decisao)
    if decisao['acao'] != 'sugerir' or modo != 'ativo':
        return 0
    saida = json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': busca.nota_para_o_agente(decisao),
    }}, ensure_ascii=False)
    sys.stdout.buffer.write(saida.encode('utf-8') + b'\n')
    sys.stdout.buffer.flush()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
