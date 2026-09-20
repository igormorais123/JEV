#!/usr/bin/env python
"""Hook PostToolUse (conteúdo externo): o sentinela lê o que a ferramenta devolveu.

Para WebFetch, WebSearch, leitura de página, e-mail e documento do Drive, o Jev responde se
o texto tenta dar ordens ao sistema. Se sim, injeta um aviso; o conteúdo continua no
contexto e a decisão continua com o agente. Lógica em `camadas/sentinela.py`.

Modo, pela variável `JEV_SENTINELA_MODO` ou por `modo-sentinela.txt`: sombra registra; ativo
avisa. Falha para o lado aberto: sai em silêncio com código 0.
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
    ferramenta = dados.get('tool_name') or ''

    from camadas import nucleo, sentinela
    if ferramenta not in sentinela.FERRAMENTAS:
        return 0
    modo = nucleo.modo_vigente('JEV_SENTINELA_MODO', RAIZ / 'modo-sentinela.txt')
    sessao = dados.get('session_id')
    try:
        decisao = sentinela.analisar(dados.get('tool_response'), ferramenta)
    except Exception as erro:
        nucleo.registrar('sentinela', modo=modo, sessao=sessao, ferramenta=ferramenta,
                         acao='nada', motivo=f'erro: {type(erro).__name__}')
        return 0
    nucleo.registrar('sentinela', modo=modo, sessao=sessao, **decisao)
    if decisao['acao'] != 'avisar' or modo != 'ativo':
        return 0
    saida = json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': sentinela.nota_para_o_agente(decisao),
    }}, ensure_ascii=False)
    sys.stdout.buffer.write(saida.encode('utf-8') + b'\n')
    sys.stdout.buffer.flush()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
