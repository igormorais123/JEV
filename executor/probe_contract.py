"""Sonda o contrato real do endpoint de decisoes, sempre com reserva financeira.

Cada variante e uma tentativa registrada no ledger. Respostas brutas ficam em runs/probe/.
"""
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger
from .pricing import usd_to_nusd
from .runner import DECISIONS_URL, estimate_input_tokens, load_api_key, payload_sha256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'probe'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-canarios-contrato'
BLOCK = 'sondagem'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-sonda-jev'

STATE = 'O usuario escreveu: "Bom dia, gostaria de cancelar meu pedido numero 4471."'
OPTIONS = ['cancelar', 'rastrear', 'trocar']

VARIANTS = {
    'L_score_array_strings': {'q1': {
        'type': 'score',
        'instructions': 'Quao relevante e a mensagem para o assunto cobranca?',
        'criteria': ['nada relevante', 'pouco relevante', 'muito relevante'],
    }},
    'M_score_array_objetos': {'q1': {
        'type': 'score',
        'instructions': 'Quao relevante e a mensagem para o assunto cobranca?',
        'criteria': [
            {'label': 'nada', 'description': 'Nao trata de valores.'},
            {'label': 'muito', 'description': 'Trata diretamente de valores.'},
        ],
    }},
    'N_noul_sem_criteria': {'q1': {
        'type': 'noul',
        'instructions': 'O usuario pediu cancelamento de pedido?',
    }},
}


def send(key, payload):
    request = urllib.request.Request(DECISIONS_URL, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                                     headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json',
                                              'User-Agent': 'jev-lab/1.0'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as error:
        raw = error.read().decode('utf-8', 'replace')
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, {'raw': raw[:1000]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    key, _ = load_api_key()
    findings = []
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.02'))
        ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
        for name, questions in VARIANTS.items():
            payload = {'model': MODEL, 'state': STATE, 'questions': questions}
            tokens = estimate_input_tokens(payload)
            path = f'runs/probe/{name}.json'
            reservation = ledger.reserve(arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                                         max_input_tokens=tokens, max_output_tokens=1,
                                         payload_sha256=payload_sha256(payload), request_path=path,
                                         runtime_manifest_path=path, evidence_level='live_component')
            attempt = reservation['attempt_id']
            ledger.mark_sent(attempt)
            status, body = send(key, payload)
            usage = body.get('usage')
            ledger.settle(attempt, status='success' if status == 200 else 'http_error',
                          usage=usage if isinstance(usage, dict) else None,
                          provider_request_id=body.get('id'), model_resolved=body.get('model'),
                          response_path=path)
            (OUT / f'{name}.json').write_text(json.dumps(
                {'payload': payload, 'http_status': status, 'body': body,
                 'at': datetime.now(timezone.utc).isoformat()}, ensure_ascii=False, indent=2), encoding='utf-8')
            message = body.get('message') or body.get('error') or ''
            findings.append({'variant': name, 'http_status': status, 'message': str(message)[:400]})
            print(f'{name}: HTTP {status} | {str(message)[:220]}')
        print(f'\nComprometido no ledger: {ledger.committed_nusd() / 1e9:.9f} USD | '
              f'disponivel: {ledger.available_nusd() / 1e9:.6f} USD')
    (OUT / 'findings.json').write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
