"""Plugin jev-camadas: o Jev decide o que entra no contexto do modelo caro do Hermes.

Registra quatro ganchos, todos falhando para o lado aberto (qualquer erro devolve None e o
Hermes segue como seguiria sem o plugin). O código de decisão mora em
`/root/.hermes/integrations/jev/jev_hermes/camadas.py` e `recortes.py`; este arquivo só liga
os ganchos.

Camadas (2026-09-21, depois do estudo de 30 dias do `state.db`):
  tema        pre_llm_call            — sobre o que é o pedido; sugere skill; anota "delegue"
  leitura     read_file               — janela do arquivo que importa ao pedido
  skill       skill_view              — seções da skill que importam ao pedido
  busca       search_files, web_search, session_search — "abra primeiro"
  sessoes     session_search          — sessões irrelevantes viram uma linha
  resultado   web_extract, apify, execute_code… ≥ 16 mil caracteres — partes essenciais
  sentinela   conteúdo externo        — acusa texto que tenta dar ordens
  recorte     terminal ≥ 16 mil       — partes essenciais da saída longa sem erro
  saida       terminal com erro       — onde está a causa
  (transcrição do YouTube: no plugin youtube-auto-bridge, que chama `recortes.transcricao`)

Interruptores: `touch /root/.hermes/integrations/jev/DESLIGADO` desliga todo uso do Jev sem
reiniciar nada; `JEV_CAMADAS=tema,leitura,...` no ambiente restringe as camadas ativas.
"""
import logging
import os
import sys
from pathlib import Path

RAIZ = Path(os.environ.get('JEV_HERMES_RAIZ', '/root/.hermes/integrations/jev'))
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

logger = logging.getLogger(__name__)

TODAS = ('tema', 'leitura', 'skill', 'busca', 'sessoes', 'resultado', 'sentinela', 'saida', 'recorte')
FERRAMENTAS_DE_BUSCA = {'search_files', 'web_search', 'session_search'}
FERRAMENTAS_EXTERNAS = {'web_extract', 'browser_snapshot', 'browser_navigate', 'browser_console'}
# Resultado longo que não é leitura de arquivo nem listagem: o mesmo recorte da saída de terminal.
FERRAMENTAS_DE_RESULTADO = {'web_extract', 'execute_code', 'browser_snapshot', 'browser_navigate',
                            'tool_describe', 'cronjob'}
PLATAFORMAS_SEM_TEMA = {'cron', ''}
COMANDO_EXTERNO = ('gws gmail', 'gws drive', 'himalaya', 'curl ', 'wget ', 'lynx ', 'w3m ')


def _ativas():
    escolha = os.environ.get('JEV_CAMADAS')
    if not escolha:
        return set(TODAS)
    return {c.strip() for c in escolha.split(',') if c.strip()}


def _camadas():
    from jev_hermes import camadas
    return camadas


def _recortes():
    from jev_hermes import recortes
    return recortes


def _pre_llm_call(session_id=None, user_message=None, platform=None, parent_session_id=None,
                  is_first_turn=None, task_id=None, **_):
    try:
        if not isinstance(user_message, str):
            return None
        camadas = _camadas()
        camadas.guardar_pedido(session_id, user_message)
        if task_id and task_id != session_id:
            camadas.guardar_pedido(task_id, user_message)
        if 'tema' not in _ativas() or (platform or '') in PLATAFORMAS_SEM_TEMA or parent_session_id:
            return None
        nota, decisao = camadas.tema(user_message)
        camadas.registrar('tema', sessao=str(session_id)[:40], plataforma=platform, **decisao)
        return {'context': nota} if nota else None
    except Exception as erro:
        logger.debug('jev-camadas pre_llm_call: %s', erro)
        return None


def _marcar_leitura_parcial(task_id, argumentos):
    """O recorte vira leitura parcial para o Hermes: escrever depois dela passa a gerar aviso."""
    try:
        from tools import file_state
        from tools.file_tools import _resolve_path_for_task
        caminho = _resolve_path_for_task(argumentos.get('path'), task_id or 'default')
        file_state.record_read(task_id or 'default', str(caminho), partial=True)
    except Exception as erro:
        logger.debug('jev-camadas leitura parcial: %s', erro)


def _transform_tool_result(tool_name=None, args=None, result=None, task_id=None, session_id=None,
                           status=None, **_):
    try:
        if not isinstance(result, str) or status == 'error':
            return None
        ativas = _ativas()
        camadas = _camadas()
        args = args or {}
        sessao = str(session_id)[:40]
        pedido = camadas.pedido_vigente(session_id)
        if tool_name == 'read_file' and 'leitura' in ativas:
            novo, decisao = camadas.leitura(result, args, pedido)
            camadas.registrar('leitura', sessao=sessao, **decisao)
            if novo:
                _marcar_leitura_parcial(task_id, args)
            return novo
        if tool_name == 'skill_view' and 'skill' in ativas:
            novo, decisao = _recortes().skill(result, args, pedido)
            camadas.registrar('skill', sessao=sessao, **decisao)
            return novo
        if tool_name == 'session_search' and 'sessoes' in ativas:
            novo, decisao = _recortes().sessoes(result, args, pedido)
            camadas.registrar('sessoes', sessao=sessao, **decisao)
            if novo:
                return novo
        if tool_name in FERRAMENTAS_DE_BUSCA and 'busca' in ativas:
            novo, decisao = camadas.busca(tool_name, result, args, pedido)
            camadas.registrar('busca', sessao=sessao, **decisao)
            return novo
        externa = tool_name in FERRAMENTAS_EXTERNAS or str(tool_name or '').startswith('mcp_')
        saida = result
        acrescimo = ''
        if (tool_name in FERRAMENTAS_DE_RESULTADO or externa) and 'resultado' in ativas \
                and len(result) >= camadas.MINIMO_DO_RECORTE:
            novo, decisao = _recortes().resultado(tool_name, result, pedido)
            camadas.registrar('resultado', sessao=sessao, **decisao)
            if novo:
                saida = novo
        if externa and 'sentinela' in ativas:
            nota, decisao = camadas.sentinela(tool_name, camadas.texto_de(result))
            camadas.registrar('sentinela', sessao=sessao, **decisao)
            if nota:
                acrescimo = '\n\n' + nota
        if saida is not result or acrescimo:
            return saida + acrescimo
    except Exception as erro:
        logger.debug('jev-camadas transform_tool_result: %s', erro)
    return None


def _transform_terminal_output(command=None, output=None, returncode=None, task_id=None, **_):
    try:
        if not isinstance(output, str) or not output:
            return None
        original = output
        ativas = _ativas()
        camadas = _camadas()
        acrescimos = []
        comando = command or ''
        if 'recorte' in ativas and returncode in (0, None) and len(output) >= camadas.MINIMO_DO_RECORTE:
            novo, decisao = camadas.recortar_terminal(comando, output, camadas.pedido_vigente(task_id))
            camadas.registrar('recorte', **decisao)
            if novo:
                output = novo
        if 'sentinela' in ativas and any(marca in comando for marca in COMANDO_EXTERNO):
            nota, decisao = camadas.sentinela('terminal', output)
            camadas.registrar('sentinela', ferramenta_real='terminal', **decisao)
            if nota:
                acrescimos.append('\n\n' + nota)
        if 'saida' in ativas and (returncode not in (0, None) or len(output) >= camadas.MINIMO_DA_SAIDA):
            nota, decisao = camadas.saida(comando, output, returncode)
            if decisao.get('motivo') not in ('saída curta', 'sem marca de erro'):
                camadas.registrar('saida', **decisao)
            if nota:
                acrescimos.append(nota)
        if acrescimos or output is not original:
            return output + ''.join(acrescimos)
        return None
    except Exception as erro:
        logger.debug('jev-camadas transform_terminal_output: %s', erro)
        return None


def _on_session_end(**_):
    try:
        _camadas().limpar_sessoes()
    except Exception:
        pass


def register(ctx):
    ctx.register_hook('pre_llm_call', _pre_llm_call)
    ctx.register_hook('transform_tool_result', _transform_tool_result)
    ctx.register_hook('transform_terminal_output', _transform_terminal_output)
    ctx.register_hook('on_session_end', _on_session_end)
