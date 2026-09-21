#!/usr/bin/env python
"""Hook PostToolUse (Bash, PowerShell): em saída longa com erro, o Jev aponta a parte da causa.

Só age com 3.000 caracteres ou mais e alguma marca de erro na saída; injeta uma linha com a
parte a olhar, com a ressalva de que a aplicação não foi medida. Lógica em `camadas/saida.py`.

Modo, pela variável `JEV_SAIDA_MODO` ou por `modo-saida.txt`: sombra registra; ativo injeta.
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
    from camadas import nucleo, saida
    if dados.get('tool_name') not in saida.FERRAMENTAS:
        return 0
    modo = nucleo.modo_vigente('JEV_SAIDA_MODO', RAIZ / 'modo-saida.txt')
    sessao = dados.get('session_id')
    comando = (dados.get('tool_input') or {}).get('command') or ''
    try:
        decisao = saida.analisar(dados.get('tool_response'), comando)
    except Exception as erro:
        nucleo.registrar('saida', modo=modo, sessao=sessao, acao='nada',
                         motivo=f'erro: {type(erro).__name__}')
        return 0
    if decisao.get('motivo') in ('saida curta', 'sem marca de erro'):
        return 0  # o caso comum; não vale uma linha de registro por comando
    nucleo.registrar('saida', modo=modo, sessao=sessao, **decisao)
    if decisao['acao'] != 'apontar' or modo != 'ativo':
        return 0
    saida_json = json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': saida.nota_para_o_agente(decisao),
    }}, ensure_ascii=False)
    sys.stdout.buffer.write(saida_json.encode('utf-8') + b'\n')
    sys.stdout.buffer.flush()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
