#!/usr/bin/env python
"""Hook PreToolUse (Read): antes de ler um arquivo grande, o Jev encolhe o intervalo.

Lê o `Read` que o agente pediu, o pedido vigente da sessão e o arquivo; classifica o arquivo
em blocos contra o pedido; se puder estreitar, devolve `updatedInput` com `offset` e `limit`
e uma nota curta dizendo o que ficou de fora e como pedir o resto. A lógica e as regras estão
em `camadas/leitura.py`; aqui só há entrada, saída e registro.

Modo, pela variável `JEV_LEITURA_MODO` ou por `modo-leitura.txt`:
  sombra — classifica e registra o que teria feito; não muda o Read.
  ativo  — estreita o Read.

Falha para o lado aberto em qualquer situação: sai em silêncio com código 0.
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
    if dados.get('tool_name') != 'Read':
        return 0
    entrada = dados.get('tool_input') or {}
    caminho = entrada.get('file_path')
    if not caminho:
        return 0

    from camadas import leitura, nucleo
    modo = nucleo.modo_vigente('JEV_LEITURA_MODO', RAIZ / 'modo-leitura.txt')
    sessao = dados.get('session_id')
    try:
        pedido = nucleo.pedido_vigente(sessao, dados.get('transcript_path'))
        decisao = leitura.analisar(caminho, pedido, entrada)
    except Exception as erro:
        nucleo.registrar('leitura', modo=modo, sessao=sessao, arquivo=caminho,
                         acao='nada', motivo=f'erro: {type(erro).__name__}')
        return 0
    nucleo.registrar('leitura', modo=modo, sessao=sessao, com_pedido=bool(pedido),
                     **{k: v for k, v in decisao.items() if k != 'classes'},
                     blocos_classes=[(c['classe'], c['confianca'], c.get('mantido', False))
                                     for c in decisao.get('classes', [])])
    if decisao['acao'] != 'estreitar' or modo != 'ativo':
        return 0

    saida = json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'allow',
        'updatedInput': {**entrada, 'offset': decisao['offset'], 'limit': decisao['limit']},
        'additionalContext': leitura.nota_para_o_agente(decisao),
    }}, ensure_ascii=False)
    # Bytes em UTF-8, não `print`: o console desta máquina é cp1252 e já corrompeu acento.
    sys.stdout.buffer.write(saida.encode('utf-8') + b'\n')
    sys.stdout.buffer.flush()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
