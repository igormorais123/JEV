#!/usr/bin/env python
"""Hook PreToolUse (Bash): o filtro de leitura do Jev para `cat ARQUIVO` dentro de um comando.

A maior parte do texto que entra no contexto vem do `Bash`, não do `Read`. Quando o comando é
só leitura e um segmento lê um arquivo grande inteiro, esse segmento vira `sed -n 'A,Bp'` com
a janela que o Jev escolheu para o pedido vigente, e o agente recebe uma nota dizendo o que
ficou de fora e como pedir o resto. As regras, todas estreitas, estão em `camadas/shell.py`.

Modo, pela variável `JEV_LEITURA_SHELL_MODO` ou por `modo-leitura-shell.txt`:
  sombra — classifica e registra o que teria feito; não muda o comando.
  ativo  — reescreve o comando.

Os registros vão para a camada `leitura`, com `via: bash`, para que a releitura de um arquivo
estreitado seja contada do mesmo jeito, venha ela por `Read` ou por `sed`.

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
    if dados.get('tool_name') != 'Bash':
        return 0
    entrada = dados.get('tool_input') or {}
    comando = entrada.get('command')
    if not comando or len(comando) > 2000:
        return 0

    from camadas import nucleo, shell
    # Antes de qualquer custo: a maioria dos comandos não é leitura pura, e sai aqui.
    if shell.dividir(comando) is None:
        return 0
    modo = nucleo.modo_vigente('JEV_LEITURA_SHELL_MODO', RAIZ / 'modo-leitura-shell.txt')
    sessao = dados.get('session_id')
    try:
        pedido = nucleo.pedido_vigente(sessao, dados.get('transcript_path'))
        decisao = shell.analisar(comando, pedido, dados.get('cwd'))
    except Exception as erro:
        nucleo.registrar('leitura', via='bash', modo=modo, sessao=sessao, acao='nada',
                         motivo=f'erro: {type(erro).__name__}')
        return 0
    for leitura in decisao['leituras']:
        nucleo.registrar('leitura', via='bash', modo=modo, sessao=sessao, com_pedido=bool(pedido),
                         **{k: v for k, v in leitura.items() if k != 'classes'},
                         blocos_classes=[(c['classe'], c['confianca'], c.get('mantido', False))
                                         for c in leitura.get('classes', [])])
    if decisao['acao'] != 'reescrever' or modo != 'ativo':
        return 0

    saida = json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'allow',
        'updatedInput': {**entrada, 'command': decisao['comando']},
        'additionalContext': shell.nota_para_o_agente(decisao),
    }}, ensure_ascii=False)
    sys.stdout.buffer.write(saida.encode('utf-8') + b'\n')
    sys.stdout.buffer.flush()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
