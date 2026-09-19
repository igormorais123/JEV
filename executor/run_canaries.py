"""Etapa 2 do plano: tres canarios de contrato com reserva financeira e conciliacao real.

Uso:
    python -m executor.run_canaries --dry-run
    python -m executor.run_canaries --execute
"""
import argparse
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger
from .pricing import usd_to_nusd
from .runner import CANARIES, dispatch, dry_run, load_api_key, payload_for

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs' / 'canaries'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-canarios-contrato'
BLOCK = 'canarios'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-canario-jev'


def provider_snapshot(key):
    request = urllib.request.Request('https://openrouter.ai/api/v1/key',
                                     headers={'Authorization': f'Bearer {key}', 'User-Agent': 'jev-lab/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)['data']
    # label vem truncado pelo provedor, mas nao guardamos nem isso.
    return {'usage_usd': data.get('usage'), 'limit_usd': data.get('limit'),
            'limit_remaining_usd': data.get('limit_remaining'), 'is_free_tier': data.get('is_free_tier')}


def prepare(ledger):
    ledger.authorize(usd_to_nusd('5.00'), hypothesis='O contrato tipado do Jev responde como documentado',
                     metric='contratos validos por chamada')
    ledger.set_block_cap(BLOCK, usd_to_nusd('0.05'))
    ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Despacha de verdade; sem isso apenas simula.')
    args = parser.parse_args()

    RUNS.mkdir(parents=True, exist_ok=True)
    DB.parent.mkdir(parents=True, exist_ok=True)
    key, source = load_api_key()
    print(f'Credencial carregada de {source}')

    with Ledger(DB, EXPERIMENT) as ledger:
        prepare(ledger)
        print(f'Teto global: {ledger.cap_nusd() / 1e9:.6f} USD | disponivel: {ledger.available_nusd() / 1e9:.6f} USD')

        for canary in CANARIES:
            payload = payload_for(MODEL, canary['state'], canary['questions'])
            preview = dry_run(ledger, PROVIDER, MODEL, payload)
            print(f"  {canary['id']}: payload ~{preview['estimated_input_tokens']} tokens, "
                  f"reserva pelo contexto cheio {preview['reservation_nusd'] / 1e9:.9f} USD, "
                  f"cabe: {preview['fits']}")

        if not args.execute:
            print('\nSimulacao apenas. Nada foi enviado e nada foi reservado.')
            return

        before = provider_snapshot(key)
        ledger.reconcile(PROVIDER, usd_to_nusd(str(before['usage_usd'])), before,
                         key_limit_nusd=usd_to_nusd(str(before['limit_usd'])))
        print(f"\nBaseline do provedor: uso {before['usage_usd']} USD, limite {before['limit_usd']} USD")

        results = []
        for canary in CANARIES:
            request_path = str((RUNS / f"{canary['id']}.json").relative_to(ROOT))
            started = time.monotonic()
            result = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                              state=canary['state'], questions=canary['questions'],
                              request_path=request_path, runtime_manifest_path=request_path,
                              api_key=key)
            elapsed = (time.monotonic() - started) * 1000
            answers = result.get('answers') or {}
            answer = answers.get(canary['question_id']) or {}
            choice = answer.get('choice')
            record = {'canary': canary['id'], 'status': result['status'], 'expected': canary['expected'],
                      'observed': choice, 'match': choice == canary['expected'],
                      'latency_ms': round(elapsed, 1), 'attempt_id': result['attempt_id'],
                      'settled_nusd': result.get('settled_nusd'), 'cost_source': result.get('cost_source'),
                      'confidence': answer.get('confidence'),
                      'probabilities': answer.get('probabilities'),
                      'error': result.get('error'), 'http_status': result.get('http_status'),
                      'answers': answers}
            (RUNS / f"{canary['id']}.json").write_text(
                json.dumps({'request': {'model': MODEL, 'state': canary['state'], 'questions': canary['questions']},
                            'result': record, 'at': datetime.now(timezone.utc).isoformat()},
                           ensure_ascii=False, indent=2), encoding='utf-8')
            results.append(record)
            print(f"  {record['canary']}: {record['status']} | esperado {record['expected']} | "
                  f"observado {record['observed']} | {record['latency_ms']} ms | "
                  f"{(record['settled_nusd'] or 0) / 1e9:.9f} USD ({record['cost_source']})")

        after = provider_snapshot(key)
        reconciliation = ledger.reconcile(PROVIDER, usd_to_nusd(str(after['usage_usd'])), after,
                                          key_limit_nusd=usd_to_nusd(str(after['limit_usd'])))
        print(f"\nExtrato depois: uso {after['usage_usd']} USD")
        print(f"Delta do provedor: {reconciliation['delta_nusd'] / 1e9:.9f} USD | "
              f"ledger comprometido: {reconciliation['ledger_committed_nusd'] / 1e9:.9f} USD")
        print(f"Disponivel no teto de US$ 5: {ledger.available_nusd() / 1e9:.6f} USD")

        summary = {'at': datetime.now(timezone.utc).isoformat(), 'results': results,
                   'provider_before': before, 'provider_after': after,
                   'reconciliation': reconciliation,
                   'ledger_committed_nusd': ledger.committed_nusd(),
                   'available_nusd': ledger.available_nusd()}
        (RUNS / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Resumo em {(RUNS / 'summary.json').relative_to(ROOT)}")


if __name__ == '__main__':
    main()
