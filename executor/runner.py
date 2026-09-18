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
from .pricing import PricingError, entry

DECISIONS_URL = 'https://openrouter.ai/api/alpha/decisions'
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TransportTimeout(Exception):
    """A requisicao pode ter chegado ao provedor; a reserva nao e liberada."""


class ContractError(Exception):
    """Resposta fora do contrato tipado esperado."""


def load_api_key(env_path=None):
    """Le a chave do .env do projeto ou do ambiente. Nunca registra o valor."""
    if os.environ.get('OPENROUTER_API_KEY'):
        return os.environ['OPENROUTER_API_KEY'], 'ambiente'
    path = Path(env_path) if env_path else PROJECT_ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            if line.strip().startswith('OPENROUTER_API_KEY='):
                value = line.split('=', 1)[1].strip().strip('"').strip("'")
                if value:
                    return value, str(path)
    raise RuntimeError('OPENROUTER_API_KEY ausente. Configure o .env local do projeto antes de despachar.')


def payload_for(model, state, questions):
    return {'model': model, 'state': state, 'questions': questions}


def payload_sha256(payload):
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def estimate_input_tokens(payload):
    """Estimativa conservadora: 1 token a cada 3 caracteres, com margem de 20%."""
    size = len(json.dumps(payload, ensure_ascii=False))
    return int(size / 3 * 1.2) + 64


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
    """Exige decisao tipada por pergunta, dentro das opcoes enviadas."""
    decisions = body.get('decisions')
    if not isinstance(decisions, list) or len(decisions) != len(questions):
        raise ContractError('Resposta sem uma decisao por pergunta')
    for question, decision in zip(questions, decisions):
        if not isinstance(decision, dict):
            raise ContractError('Decisao nao e objeto')
        choice = decision.get('choice', decision.get('answer'))
        if choice is None:
            raise ContractError('Decisao sem escolha')
        options = question.get('options')
        if options and choice not in options:
            raise ContractError(f'Escolha "{choice}" fora das opcoes declaradas')
    return decisions


def usage_from(body):
    usage = body.get('usage') or {}
    input_tokens = usage.get('input_tokens', usage.get('prompt_tokens'))
    output_tokens = usage.get('output_tokens', usage.get('completion_tokens'))
    if isinstance(input_tokens, int) and isinstance(output_tokens, int):
        return {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'raw': usage}
    return usage or None


def dry_run(ledger, provider, model, payload, max_output_tokens=1):
    """Valida payload, preco e teto sem reservar e sem enviar nada."""
    price = entry(ledger.prices, provider, model)
    tokens = estimate_input_tokens(payload)
    context = price.get('context_length')
    if context and tokens > context:
        raise ContractError(f'Payload estimado em {tokens} tokens excede o contexto de {context}')
    from .pricing import worst_case_nusd
    worst = worst_case_nusd(ledger.prices, provider, model, tokens, max_output_tokens)
    return {
        'estimated_input_tokens': tokens,
        'worst_case_nusd': worst,
        'available_nusd': ledger.available_nusd(),
        'fits': worst <= ledger.available_nusd(),
        'payload_sha256': payload_sha256(payload),
    }


def dispatch(ledger, *, arm_id, block_id, provider, model, state, questions, request_path,
             runtime_manifest_path, max_output_tokens=1, timeout=45.0, transport=http_transport,
             api_key=None, evidence_level='live_component'):
    """Reserva, envia e liquida uma chamada. Sem reserva nao ha envio."""
    payload = payload_for(model, state, questions)
    tokens = estimate_input_tokens(payload)
    reservation = ledger.reserve(arm_id=arm_id, block_id=block_id, provider=provider, model=model,
                                 max_input_tokens=tokens, max_output_tokens=max_output_tokens,
                                 payload_sha256=payload_sha256(payload), request_path=request_path,
                                 runtime_manifest_path=runtime_manifest_path, evidence_level=evidence_level)
    attempt_id = reservation['attempt_id']
    key = api_key or load_api_key()[0]
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
               'User-Agent': 'jev-lab/1.0'}
    ledger.mark_sent(attempt_id)
    try:
        status, body = transport(DECISIONS_URL, headers, payload, timeout)
    except TransportTimeout as error:
        ledger.mark_timeout(attempt_id, {'kind': 'timeout', 'detail': str(error)[:200]})
        return {'attempt_id': attempt_id, 'status': 'timeout', 'reserved_nusd': reservation['reserved_nusd']}
    except Exception as error:  # transporte quebrou apos o envio: reserva conservada
        ledger.mark_timeout(attempt_id, {'kind': type(error).__name__, 'detail': str(error)[:200]})
        return {'attempt_id': attempt_id, 'status': 'transport_error', 'reserved_nusd': reservation['reserved_nusd']}

    usage = usage_from(body)
    if status != 200:
        settled = ledger.settle(attempt_id, status='http_error', usage=usage,
                                provider_request_id=body.get('id'), latency_ms=None)
        return {'attempt_id': attempt_id, 'status': 'http_error', 'http_status': status,
                'error': str(body.get('error'))[:300], **settled}
    try:
        decisions = validate_contract(body, questions)
    except ContractError as error:
        settled = ledger.settle(attempt_id, status='invalid_response', usage=usage,
                                provider_request_id=body.get('id'))
        return {'attempt_id': attempt_id, 'status': 'invalid_response', 'error': str(error), **settled}

    settled = ledger.settle(attempt_id, status='success', usage=usage, provider_request_id=body.get('id'),
                            model_resolved=body.get('model'), response_path=request_path)
    return {'attempt_id': attempt_id, 'status': 'success', 'decisions': decisions, **settled}


CANARIES = [
    {
        'id': 'canary-01-escolha-trivial',
        'state': 'O usuario escreveu: "Bom dia, gostaria de cancelar meu pedido numero 4471."',
        'questions': [{'id': 'q1', 'question': 'Qual acao o usuario pediu?',
                       'options': ['cancelar', 'rastrear', 'trocar']}],
        'expected': 'cancelar',
    },
    {
        'id': 'canary-02-evidencia-ausente',
        'state': 'Documento: "A reuniao foi agendada para quinta." Pergunta sobre pagamento.',
        'questions': [{'id': 'q1', 'question': 'O documento confirma que o pagamento foi feito?',
                       'options': ['sim', 'nao', 'nao informado']}],
        'expected': 'nao informado',
    },
    {
        'id': 'canary-03-opcao-fora-do-conjunto',
        'state': 'Mensagem: "Preciso da segunda via do boleto."',
        'questions': [{'id': 'q1', 'question': 'A mensagem e sobre cobranca ou sobre entrega?',
                       'options': ['cobranca', 'entrega']}],
        'expected': 'cobranca',
    },
]
