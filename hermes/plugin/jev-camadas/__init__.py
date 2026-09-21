"""Plugin jev-camadas: o Jev decide o que entra no contexto do modelo caro do Hermes.

Registra cinco ganchos, todos falhando para o lado aberto (qualquer erro devolve None e o
Hermes segue como seguiria sem o plugin). O código de decisão mora em
`/root/.hermes/integrations/jev/jev_hermes/camadas.py`; este arquivo só liga os ganchos.

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

TODAS = ('tema', 'leitura', 'busca', 'sentinela', 'saida')
FERRAMENTAS_DE_BUSCA = {'search_files', 'web_search', 'session_search'}
FERRAMENTAS_EXTERNAS = {'web_extract', 'browser_snapshot', 'browser_navigate', 'browser_console'}
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


def _pre_llm_call(session_id=None, user_message=None, platform=None, parent_session_id=None,
                  is_first_turn=None, **_):
    try:
        if not isinstance(user_message, str):
            return None
        camadas = _camadas()
        camadas.guardar_pedido(session_id, user_message)
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
        if tool_name == 'read_file' and 'leitura' in ativas:
            novo, decisao = camadas.leitura(result, args, camadas.pedido_vigente(session_id))
            camadas.registrar('leitura', sessao=str(session_id)[:40], **decisao)
            if novo:
                _marcar_leitura_parcial(task_id, args)
            return novo
        if tool_name in FERRAMENTAS_DE_BUSCA and 'busca' in ativas:
            novo, decisao = camadas.busca(tool_name, result, args, camadas.pedido_vigente(session_id))
            camadas.registrar('busca', sessao=str(session_id)[:40], **decisao)
            return novo
        externa = tool_name in FERRAMENTAS_EXTERNAS or str(tool_name or '').startswith('mcp_')
        if externa and 'sentinela' in ativas:
            nota, decisao = camadas.sentinela(tool_name, camadas.texto_de(result))
            camadas.registrar('sentinela', sessao=str(session_id)[:40], **decisao)
            return result + '\n\n' + nota if nota else None
    except Exception as erro:
        logger.debug('jev-camadas transform_tool_result: %s', erro)
    return None


def _transform_terminal_output(command=None, output=None, returncode=None, task_id=None, **_):
    try:
        if not isinstance(output, str) or not output:
            return None
        ativas = _ativas()
        camadas = _camadas()
        acrescimos = []
        comando = command or ''
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
        return output + ''.join(acrescimos) if acrescimos else None
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
