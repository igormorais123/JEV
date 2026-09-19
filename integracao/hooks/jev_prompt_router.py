#!/usr/bin/env python
"""Hook UserPromptSubmit: o Jev diz o tema do pedido e sugere a skill certa.

Substitui, com medição, o que os oito `hookify.suggest-skill-*` fazem hoje por `regex_match`.
No mesmo conjunto de 60 pedidos reais do Igor, com corte de confiança 0,90: o Jev aponta 9 dos
23 temas reais e não sugere nada em nenhuma das 37 mensagens sem tema; os regex apontam 5 e
erram 1. O detalhe está em `avaliacao/skills-resultado.json`.

Serve ao Claude Code e ao Codex, que usam o mesmo contrato de hook nesta máquina: JSON pelo
stdin, JSON pelo stdout, `hookSpecificOutput.additionalContext` para injetar a nota.

Falha para o lado aberto em qualquer situação: sem chave, sem rede, fora do teto ou fora do
contrato, sai em silêncio com código 0 e a sessão segue como seguiria sem ele.

Modo, pela variável de ambiente `JEV_ROUTER_MODO`:
  sombra (padrão) — classifica e registra em `decisoes.jsonl`; não injeta nada no contexto.
  ativo           — injeta a sugestão de skill e o aviso de risco.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

ESTADO = RAIZ / 'estado'
MODO = RAIZ / 'modo.txt'


def modo_vigente():
    """O modo vem do ambiente; sem ele, do arquivo; sem os dois, é sombra.

    O Claude Code define `JEV_ROUTER_MODO` pelo `env` do settings. O Codex não tem esse campo,
    e por isso existe o arquivo: sem ele o hook ficaria em sombra lá para sempre, silencioso,
    parecendo instalado.
    """
    do_ambiente = os.environ.get('JEV_ROUTER_MODO')
    if do_ambiente:
        return do_ambiente.strip().lower()
    try:
        return MODO.read_text(encoding='utf-8').strip().lower() or 'sombra'
    except OSError:
        return 'sombra'


def guardar_estado(sessao, decisao):
    if not sessao:
        return
    try:
        ESTADO.mkdir(parents=True, exist_ok=True)
        (ESTADO / f'{sessao}.json').write_text(
            json.dumps(decisao, ensure_ascii=False), encoding='utf-8')
    except OSError:
        pass


def main():
    try:
        sys.stdin.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    try:
        dados = json.load(sys.stdin)
    except Exception:
        return 0

    pedido = dados.get('prompt') or ''
    if not isinstance(pedido, str):
        return 0

    from jev_router import politica, roteador

    modo = modo_vigente()
    decisao = roteador.classificar(pedido, contexto=dados.get('cwd') or '', modo=modo,
                                   origem='claude-code/UserPromptSubmit')
    if not decisao:
        return 0

    guardar_estado(dados.get('session_id'), decisao)
    if modo != 'ativo':
        return 0

    nota = politica.texto_para_o_agente(decisao, modo)
    if not nota:
        return 0

    # Escrito em bytes de propósito. O console do Windows entrega cp1252, e por `print` a nota
    # chegava ao cliente como "confianÃ§a" -- acento corrompido no caminho até o modelo.
    saida = json.dumps({'hookSpecificOutput': {
        'hookEventName': 'UserPromptSubmit',
        'additionalContext': nota,
    }}, ensure_ascii=False)
    sys.stdout.buffer.write(saida.encode('utf-8') + b'\n')
    sys.stdout.buffer.flush()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
