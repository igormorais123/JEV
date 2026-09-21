"""Despacho de chamadas Jev com reserva financeira obrigatoria.

Contrato: POST https://openrouter.ai/api/alpha/decisions com {model, state, questions},
identificado no jev-cli e nos payloads do dossie. O transporte e injetavel para que
todo o caminho possa ser exercitado offline, sem rede e sem custo.
"""
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from .ledger import Ledger
from .pricing import PricingError, entry, usd_to_nusd, worst_case_nusd

DECISIONS_URL = 'https://openrouter.ai/api/alpha/decisions'
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TransportTimeout(Exception):
    """A requisicao pode ter chegado ao provedor; a reserva nao e liberada."""


class ContractError(Exception):
    """Resposta fora do contrato tipado esperado."""


def load_api_key(env_path=None, provider='openrouter'):
    """Le a chave do provedor: ambiente, .env do projeto ou ~/.secrets/jev.env. Nunca registra o valor."""
    from . import credenciais
    if env_path:
        return credenciais.chave(provider, arquivos=(Path(env_path),) + credenciais.ARQUIVOS[1:])
    return credenciais.chave(provider)


def url_for(provider):
    """O endpoint de decisões de cada provedor; o OpenRouter é o padrão histórico."""
    from . import credenciais
    return credenciais.PROVEDORES.get(provider, {}).get('url', DECISIONS_URL)


def payload_for(model, state, questions):
    return {'model': model, 'state': state, 'questions': questions}


def payload_sha256(payload):
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def estimate_input_tokens(payload):
    """Estimativa informativa do tamanho do payload. NAO serve para reservar.

    Medicao real na sondagem: um payload estimado em 159 tokens consumiu 379,
    porque o provedor acrescenta instrucoes de sistema e serializacao propria.
    """
    size = len(json.dumps(payload, ensure_ascii=False))
    return int(size / 3 * 1.2) + 64


def reservation_tokens(prices, provider, model):
    """Teto de entrada da reserva: o contexto publicado do modelo.

    Nao existe teto menor declarado pelo cliente. O payload vai por POST com {model, state,
    questions} e o endpoint nao aceita limite de tokens, entao qualquer numero menor seria
    promessa sem garantia: bastaria declarar 1 token para reservar quase nada e enviar 32 mil.
    """
    price = entry(prices, provider, model)
    context = price.get('context_length')
    if not context:
        raise PricingError(f'{provider}:{model} sem context_length publicado; nao ha teto verificavel')
    return int(context)


def reservation_output_tokens(prices, provider, model):
    """Teto de saida da reserva. Sem maximo publicado nao ha teto verificavel: nao despacha."""
    price = entry(prices, provider, model)
    maximo = price.get('max_completion_tokens')
    if not isinstance(maximo, int) or maximo <= 0:
        raise PricingError(f'{provider}:{model} sem max_completion_tokens publicado; nao ha teto verificavel')
    return maximo


def http_transport(url, headers, body, timeout):
    request = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
                                     headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read().decode('utf-8'))
        except (ValueError, OSError):
            return error.code, {}
    except TimeoutError as error:
        raise TransportTimeout(str(error)) from error
    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise TransportTimeout(str(error)) from error
        raise


def validate_contract(body, questions):
    """Exige uma resposta tipada por pergunta, coerente com o tipo pedido.

    Formatos confirmados por sondagem em 18 e 19/09/2026:
      choice -> {"type":"choice","choice":<opcao>,"probabilities":{...},"confidence":0..1}
      score  -> {"type":"score","score":<float>,"legend":{...},"probabilities":{...},"confidence":0..1}
      noul   -> {"type":"noul","noul":<probabilidade 0..1>}   (sem campo confidence)
    """
    answers = body.get('answers')
    if not isinstance(answers, dict):
        raise ContractError('Resposta sem o mapa answers')
    if set(answers) != set(questions):
        raise ContractError(f'Perguntas respondidas {sorted(answers)} diferem das enviadas {sorted(questions)}')
    for question_id, answer in answers.items():
        if not isinstance(answer, dict):
            raise ContractError(f'Resposta de {question_id} nao e objeto')
        pedido = questions[question_id].get('type')
        devolvido = answer.get('type')
        if pedido and devolvido and pedido != devolvido:
            raise ContractError(f'{question_id}: pedimos {pedido} e voltou {devolvido}')
        tipo = devolvido or pedido or 'choice'
        if tipo == 'choice':
            escolha = answer.get('choice')
            if escolha is None:
                raise ContractError(f'Resposta de {question_id} sem escolha')
            criterios = questions[question_id].get('criteria')
            if isinstance(criterios, dict) and escolha not in criterios:
                raise ContractError(f'Escolha "{escolha}" fora dos criterios declarados em {question_id}')
        elif tipo == 'score':
            nota = answer.get('score')
            if not isinstance(nota, (int, float)):
                raise ContractError(f'Resposta de {question_id} sem score numerico')
            criterios = questions[question_id].get('criteria')
            if isinstance(criterios, list) and not 0 <= nota <= len(criterios) - 1:
                raise ContractError(f'Score {nota} fora da escala declarada em {question_id}')
        elif tipo == 'noul':
            valor = answer.get('noul')
            if not isinstance(valor, (int, float)) or not 0 <= valor <= 1:
                raise ContractError(f'Resposta de {question_id} sem probabilidade valida em noul')
        else:
            raise ContractError(f'Tipo de resposta desconhecido em {question_id}: {tipo}')
        confianca = answer.get('confidence')
        if confianca is not None and not 0 <= confianca <= 1:
            raise ContractError(f'Confidence fora de [0,1] em {question_id}')
    return answers


def usage_from(body):
    usage = body.get('usage') or {}
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens'))
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens'))
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        return {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'raw': usage}
    return usage or None


def reported_cost_nusd(body):
    """O provedor devolve usage.cost em USD; e o valor autoritativo da cobranca."""
    cost = (body.get('usage') or {}).get('cost')
    if cost is None:
        return None
    return usd_to_nusd(cost)


def dry_run(ledger, provider, model, payload):
    """Valida payload, preco e teto sem reservar e sem enviar nada."""
    price = entry(ledger.prices, provider, model)
    tokens = estimate_input_tokens(payload)
    context = price.get('context_length')
    if context and tokens > context:
        raise ContractError(f'Payload estimado em {tokens} tokens excede o contexto de {context}')
    cap_tokens = reservation_tokens(ledger.prices, provider, model)
    max_output_tokens = reservation_output_tokens(ledger.prices, provider, model)
    reservation = worst_case_nusd(ledger.prices, provider, model, cap_tokens, max_output_tokens)
    return {
        'estimated_input_tokens': tokens,
        'reservation_tokens': cap_tokens,
        'reservation_nusd': reservation,
        'available_nusd': ledger.available_nusd(),
        'fits': reservation <= ledger.available_nusd(),
        'payload_sha256': payload_sha256(payload),
    }


def dispatch(ledger, *, arm_id, block_id, provider, model, state, questions, request_path,
             runtime_manifest_path, timeout=45.0, transport=None, api_key=None,
             evidence_level='live_component'):
    """Reserva, envia e liquida uma chamada. Sem reserva nao ha envio.

    A reserva usa o teto de contexto publicado, nao a estimativa do payload: a sondagem
    mostrou que o provedor acrescenta tokens que o cliente nao ve.
    """
    transport = transport or http_transport
    payload = payload_for(model, state, questions)
    tokens = reservation_tokens(ledger.prices, provider, model)
    max_output_tokens = reservation_output_tokens(ledger.prices, provider, model)
    # A chave vem ANTES da reserva: falhar depois dela deixaria uma tentativa aberta
    # segurando saldo sem que nenhuma requisicao tenha saido.
    key = api_key or load_api_key(provider=provider)[0]
    reservation = ledger.reserve(arm_id=arm_id, block_id=block_id, provider=provider, model=model,
                                 max_input_tokens=tokens, max_output_tokens=max_output_tokens,
                                 payload_sha256=payload_sha256(payload), request_path=request_path,
                                 runtime_manifest_path=runtime_manifest_path, evidence_level=evidence_level)
    attempt_id = reservation['attempt_id']
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
               'User-Agent': 'jev-lab/1.0'}
    ledger.mark_sent(attempt_id)
    try:
        status, body = transport(url_for(provider), headers, payload, timeout)
    except TransportTimeout as error:
        ledger.mark_timeout(attempt_id, {'kind': 'timeout', 'detail': str(error)[:200]})
        return {'attempt_id': attempt_id, 'status': 'timeout', 'reserved_nusd': reservation['reserved_nusd']}
    except Exception as error:  # transporte quebrou apos o envio: reserva conservada
        ledger.mark_timeout(attempt_id, {'kind': type(error).__name__, 'detail': str(error)[:200]})
        return {'attempt_id': attempt_id, 'status': 'transport_error', 'reserved_nusd': reservation['reserved_nusd']}

    usage = usage_from(body)
    reported = reported_cost_nusd(body)
    if status != 200:
        settled = ledger.settle(attempt_id, status='http_error', usage=usage,
                                provider_reported_cost_nusd=reported,
                                provider_request_id=body.get('id'), latency_ms=None)
        return {'attempt_id': attempt_id, 'status': 'http_error', 'http_status': status,
                'error': str(body.get('error'))[:300], **settled}
    try:
        answers = validate_contract(body, questions)
    except ContractError as error:
        settled = ledger.settle(attempt_id, status='invalid_response', usage=usage,
                                provider_reported_cost_nusd=reported, provider_request_id=body.get('id'))
        return {'attempt_id': attempt_id, 'status': 'invalid_response', 'error': str(error), **settled}

    settled = ledger.settle(attempt_id, status='success', usage=usage, provider_reported_cost_nusd=reported,
                            provider_request_id=body.get('id'), model_resolved=body.get('model'),
                            response_path=request_path)
    return {'attempt_id': attempt_id, 'status': 'success', 'answers': answers, **settled}


CANARIES = [
    {
        'id': 'canary-01-escolha-trivial',
        'state': 'O usuario escreveu: "Bom dia, gostaria de cancelar meu pedido numero 4471."',
        'questions': {'acao': {
            'type': 'choice',
            'instructions': 'Classifique a acao que o usuario pediu na mensagem.',
            'criteria': {
                'cancelar': 'O usuario pede para cancelar um pedido.',
                'rastrear': 'O usuario pede informacao sobre entrega ou localizacao.',
                'trocar': 'O usuario pede troca ou devolucao.',
            },
        }},
        'question_id': 'acao',
        'expected': 'cancelar',
    },
    {
        'id': 'canary-02-evidencia-ausente',
        'state': 'Documento: "A reuniao com o fornecedor foi agendada para quinta-feira."',
        'questions': {'pagamento': {
            'type': 'choice',
            'instructions': 'Use apenas o documento fornecido. O documento confirma que o pagamento foi feito?',
            'criteria': {
                'sim': 'O documento afirma que o pagamento foi realizado.',
                'nao': 'O documento afirma que o pagamento nao foi realizado.',
                'nao_informado': 'O documento nao trata do pagamento.',
            },
        }},
        'question_id': 'pagamento',
        'expected': 'nao_informado',
    },
    {
        'id': 'canary-03-assunto',
        'state': 'Mensagem: "Preciso da segunda via do boleto deste mes."',
        'questions': {'assunto': {
            'type': 'choice',
            'instructions': 'A mensagem trata de cobranca ou de entrega?',
            'criteria': {
                'cobranca': 'Fala de boleto, fatura, pagamento ou valores.',
                'entrega': 'Fala de envio, prazo, transporte ou endereco.',
            },
        }},
        'question_id': 'assunto',
        'expected': 'cobranca',
    },
]
