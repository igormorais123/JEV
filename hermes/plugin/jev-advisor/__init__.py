"""Plugin jev-advisor v3: a ferramenta que o modelo do Hermes chama para delegar Sistema 1 ao Jev.

v3 (2026-09-21): chamadas passam pelo núcleo `jev_hermes.nucleo` (chaves compartilhadas do PC,
OpenRouter com reserva na TypeSafe, redação de credenciais, cache exato, teto diário e mensal).
Dado privado é permitido por decisão do Igor; credenciais continuam mascaradas antes do envio.
Novo modo `lote`: uma pergunta, até 60 textos, uma chamada de ferramenta.

Os contratos legados (`triage`, `evidence`, `claim`, `system1` com presets) continuam iguais,
construídos pelo `operational.py` da fase anterior.
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(os.environ.get('JEV_HERMES_RAIZ', '/root/.hermes/integrations/jev'))
for caminho in (RAIZ, RAIZ / 'lab'):
    if str(caminho) not in sys.path:
        sys.path.insert(0, str(caminho))

MAXIMO_DO_LOTE = 60

SCHEMA = {
    "name": "jev_advisor",
    "description": (
        "Jev: classificador barato e rápido (Sistema 1), milhares de vezes mais barato que você. "
        "USE POR PADRÃO sempre que a decisão for fechada: classificar, triar, filtrar, priorizar, "
        "ordenar por relevância, checar se uma afirmação se sustenta num texto, decidir sim/não sobre "
        "um texto. Prefira `lote` para muitos itens (e-mails, mensagens, resultados de busca, linhas "
        "de log, trechos): uma pergunta, até 60 textos, uma chamada — e só leia você mesmo o que o Jev "
        "marcar como relevante. Opções com nomes claros, sempre com uma opção de escape "
        "('nao-se-aplica'). Não use para cálculo/regra determinística (use código) nem para escrever "
        "texto. Resposta é consultiva: nunca autoriza ação irreversível sozinha; confiança < 0,90 "
        "pede sua revisão."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "app": {
                "type": "string",
                "enum": ["lote", "system1", "triage", "evidence", "claim"],
                "description": (
                    "lote: {question:{type,instructions,criteria}, states:[texto,...]} — a mesma pergunta "
                    "sobre muitos textos. system1: {state, questions} ou {preset, state}. "
                    "triage {message}; evidence {query,passage}; claim {claim,evidence}."
                ),
            },
            "input": {
                "type": "object",
                "description": (
                    "Pergunta choice: {type:'choice', instructions:'...', criteria:{'rotulo':'descrição',...}}. "
                    "score: criteria é lista ordenada. noul: sim/não probabilístico, sem criteria. "
                    "Presets system1: task_route_v1, evidence_utility_v1, claim_check_v1, "
                    "tool_effect_shadow_v1, memory_gate_shadow_v1, priority_shadow_v1."
                ),
            },
            "review_threshold": {
                "type": "number", "minimum": 0.5, "maximum": 1, "default": 0.9,
                "description": "Abaixo deste limiar a resposta vem marcada para sua revisão.",
            },
            "data_classification": {
                "type": "string", "enum": ["synthetic", "public", "private"],
                "description": "Opcional, só para registro. Credenciais são mascaradas antes do envio.",
            },
            "allow_external_text": {"type": "boolean", "description": "Mantido por compatibilidade; ignorado."},
        },
        "required": ["app", "input"],
        "additionalProperties": False,
    },
}


def _fallback(motivo):
    return {"status": "fallback", "reason": motivo, "continue_with": "hermes", "action_executed": False}


def _revisao(respostas, limiar):
    marcas = {}
    for nome, r in (respostas or {}).items():
        if r.get('type') == 'noul':
            p = r.get('noul')
            marcas[nome] = (1 - limiar) < p < limiar
        else:
            marcas[nome] = (r.get('confidence') or 0) < limiar
    return marcas


def _compacto(respostas):
    saida = {}
    for nome, r in (respostas or {}).items():
        if r.get('type') == 'noul':
            saida[nome] = {'sim': r.get('noul')}
        elif r.get('type') == 'score':
            saida[nome] = {'score': r.get('score'), 'confianca': r.get('confidence')}
        else:
            saida[nome] = {'escolha': r.get('choice'), 'confianca': r.get('confidence')}
    return saida


def _lote(entrada, limiar):
    from jev_hermes import nucleo
    pergunta = entrada.get('question')
    textos = entrada.get('states')
    if not isinstance(pergunta, dict) or not isinstance(textos, list) or not textos:
        raise ValueError('lote exige question e states')
    if len(textos) > MAXIMO_DO_LOTE:
        raise ValueError(f'no máximo {MAXIMO_DO_LOTE} textos por lote')
    perguntas = {'decisao': pergunta}
    estados = [t if isinstance(t, str) else json.dumps(t, ensure_ascii=False) for t in textos]
    resultados = nucleo.classificar_em_paralelo(estados, perguntas, origem='tool-jev-lote',
                                                tempo_total=40, limite=12000)
    itens = []
    for indice, (respostas, detalhe) in enumerate(resultados):
        if respostas is None:
            itens.append({'i': indice, 'erro': detalhe.get('erro'), 'revisar': True})
            continue
        itens.append({'i': indice, **_compacto(respostas)['decisao'],
                      'revisar': _revisao(respostas, limiar)['decisao']})
    resumo = nucleo.resumo_das_chamadas(resultados)
    return {"status": "advisory", "app": "lote", "itens": itens, "chamadas_pagas": resumo['chamadas'],
            "do_cache": resumo['do_cache'], "custo_usd": resumo['custo_usd'],
            "authorizes_action": False, "can_discard_evidence": False}


def _unica(app, entrada, limiar):
    from jev_hermes import nucleo
    import operational  # contratos legados e presets da fase anterior
    if app == 'system1':
        if 'preset' in entrada:
            if entrada['preset'] not in operational.PRESETS:
                raise ValueError('preset desconhecido')
            estado, perguntas = entrada['state'], operational.PRESETS[entrada['preset']]
        else:
            estado, perguntas = entrada['state'], entrada['questions']
    else:
        payload = operational.apps.request(app, entrada)
        estado, perguntas = payload['state'], payload['questions']
    respostas, detalhe = nucleo.perguntar(estado, perguntas, origem=f'tool-jev-{app}', timeout=15,
                                          limite=30000)
    if respostas is None:
        return _fallback(detalhe.get('erro') or 'sem resposta')
    resultado = {"status": "advisory", "app": app, "answers": _compacto(respostas),
                 "revisar": _revisao(respostas, limiar), "cache": detalhe.get('cache'),
                 "custo_usd": detalhe.get('custo_usd'), "authorizes_action": False,
                 "can_discard_evidence": False, "can_certify_truth": False}
    if app != 'system1':
        resultado['decision'] = operational.policy(app, respostas['decision'])
    return resultado


def handle(args, **kwargs):
    try:
        limiar = float(args.get('review_threshold') or 0.9)
        app, entrada = args['app'], args['input']
        if app == 'lote':
            resultado = _lote(entrada, limiar)
        else:
            resultado = _unica(app, entrada, limiar)
    except (KeyError, TypeError, ValueError) as erro:
        resultado = {"status": "invalid_input", "reason": str(erro)[:200], "action_executed": False}
    except Exception as erro:
        resultado = _fallback(f'adapter_error: {type(erro).__name__}')
    return json.dumps(resultado, ensure_ascii=False)


def register(ctx):
    ctx.register_tool(name="jev_advisor", toolset="jev_advisor", schema=SCHEMA, handler=handle)
