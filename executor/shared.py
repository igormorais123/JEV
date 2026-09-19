"""Single financial path for local JEV consumers. Never truncates inputs.

Legacy JSONL entries are imported once, conservatively, into the existing wallet.
No prompt or credential is stored in the financial ledger.
"""
import hashlib
import json
import math
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger, BudgetError
from .pricing import load_prices, usd_to_nusd, worst_case_nusd
from .runner import dispatch, load_api_key, payload_sha256, validate_contract

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'typesafe/jev-1.13'
PROVIDER = 'openrouter'
DB = ROOT / 'runs/ledger.sqlite3'
PRICE_URL = 'https://openrouter.ai/api/v1/models/typesafe/jev-1.13/endpoints'
LEGACY = (ROOT / 'laboratorio/gastos.jsonl', ROOT / 'integracao/gastos.jsonl')
PRICE_CACHE = ROOT / 'runs/shared-price.json'
CAPS = {'e15': '2.00', 'lab': '2.00', 'router': '1.00', 'tools': '0.20'}


def current_prices():
    """Public pricing refreshed every hour. No stale-price fallback."""
    if PRICE_CACHE.exists():
        saved = json.loads(PRICE_CACHE.read_text(encoding='utf-8'))
        if 0 <= time.time() - saved['checked_epoch'] < 3600:
            return saved['prices']
    with urllib.request.urlopen(PRICE_URL, timeout=15) as response:
        raw = json.load(response)
    endpoints = raw['data']['endpoints']
    if not endpoints:
        raise ValueError('No published endpoint')
    # Conservative across every available route, not only the cheapest one.
    for endpoint in endpoints:
        if not endpoint.get('context_length') or not endpoint.get('max_completion_tokens'):
            raise ValueError('Published token caps missing')
        if set(endpoint['pricing']) - {'prompt', 'completion', 'discount', 'request'}:
            raise ValueError('Unknown pricing component')
    from decimal import Decimal
    def tariff(field):
        return max(usd_to_nusd(Decimal(str(e['pricing'][field])) * 1_000_000)
                   for e in endpoints)
    prices = load_prices()
    prices['snapshot_id'] = 'shared-' + datetime.now(timezone.utc).isoformat()
    prices['models'][f'{PROVIDER}:{MODEL}'] = {
        'input_nusd_per_million_tokens': tariff('prompt'),
        'output_nusd_per_million_tokens': tariff('completion'),
        'request_surcharge_nusd': max(usd_to_nusd(e['pricing'].get('request', 0)) for e in endpoints),
        'context_length': max(e['context_length'] for e in endpoints),
        'max_completion_tokens': max(e['max_completion_tokens'] for e in endpoints),
        'source': PRICE_URL,
    }
    PRICE_CACHE.parent.mkdir(exist_ok=True)
    temporary = PRICE_CACHE.with_suffix('.tmp-' + str(__import__('uuid').uuid4()))
    temporary.write_text(json.dumps({'checked_epoch': time.time(), 'prices': prices}), encoding='utf-8')
    temporary.replace(PRICE_CACHE)
    return prices


def import_legacy(ledger, paths=LEGACY):
    """Idempotent append-only import. Unknown old costs remain worst-case liabilities.

    Known zero charges remain zero only when explicitly marked as reported, or 429.
    Entries from the new shared path have an attempt_id and must not be counted twice.
    """
    ledger.db.execute('CREATE TABLE IF NOT EXISTS shared_imports '
                      '(source TEXT, line INTEGER, digest TEXT, PRIMARY KEY(source,line))')
    price = ledger.prices['models'][f'{PROVIDER}:{MODEL}']
    worst = worst_case_nusd(ledger.prices, PROVIDER, MODEL,
                            price['context_length'], price['max_completion_tokens'])
    with ledger._tx(immediate=True):
        for path in paths:
            if not path.exists():
                continue
            source = str(path.resolve())
            lines = path.read_text(encoding='utf-8').splitlines()
            count = ledger.db.execute('SELECT COUNT(*) FROM shared_imports WHERE source=?', (source,)).fetchone()[0]
            if len(lines) < count:
                raise BudgetError('Legacy log was shortened; reconciliation required')
            for number, line in enumerate(lines, 1):
                digest = hashlib.sha256(line.encode()).hexdigest()
                previous = ledger.db.execute('SELECT digest FROM shared_imports WHERE source=? AND line=?',
                                             (source, number)).fetchone()
                if previous:
                    if previous[0] != digest:
                        raise BudgetError('Legacy log changed; reconciliation required')
                    continue
                row = json.loads(line)  # Corrupt logs block spending, never silently disappear.
                if not row.get('attempt_id') and row.get('evidence_level') != 'simulation':
                    value = row.get('custo_usd')
                    known = value is not None and (value > 0 or row.get('custo_reportado') or row.get('http') == 429)
                    cost = usd_to_nusd(value) if known else worst
                    if cost < 0:
                        raise BudgetError('Negative legacy cost')
                    identity = 'legacy:' + hashlib.sha256(f'{source}:{number}:{digest}'.encode()).hexdigest()
                    ledger.db.execute(
                        'INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,'
                        'settled_nusd,cost_source,priced_provider,priced_model) VALUES(?,?,?,?,?,?,?,?)',
                        (identity, ledger.experiment_id, 'legacy', cost, cost,
                         'legacy_reported' if known else 'legacy_unknown_worst_case', PROVIDER, MODEL))
                ledger.db.execute('INSERT INTO shared_imports VALUES(?,?,?)', (source, number, digest))


def strict_answers(body, questions):
    answers = validate_contract(body, questions)
    for name, answer in answers.items():
        if answer.get('type') != questions[name].get('type'):
            raise ValueError('Missing or different answer type')
        if answer['type'] in ('choice', 'score'):
            confidence = answer.get('confidence')
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                raise ValueError('Invalid confidence')
        if answer['type'] == 'score' and not math.isfinite(answer['score']):
            raise ValueError('Invalid score')
    return answers


def ask(state, questions, *, consumer='tools', timeout=15, api_key=None,
        transport=None, db_path=DB, prices=None, legacy_paths=LEGACY):
    """Reserve, measure, settle. Injected test transports require an isolated DB."""
    if consumer not in CAPS:
        raise ValueError('Unknown consumer')
    if transport is not None and Path(db_path).resolve() == DB.resolve():
        raise ValueError('Test transport requires isolated ledger')
    if not isinstance(state, str) or not isinstance(questions, dict) or not questions:
        raise ValueError('Invalid request')
    payload = {'model': MODEL, 'state': state, 'questions': questions}
    # Bytes are a conservative input guard, NOT a billing/token estimate. Never cut text.
    if len(json.dumps(payload, ensure_ascii=False).encode('utf-8')) > 90_000:
        return None, {'status': 'abstain', 'erro': 'input_too_large', 'sent': False}
    key = api_key or load_api_key()[0]
    price_table = prices or current_prices()
    start = time.perf_counter()
    experiment = 'shared-' + consumer
    captured = {}
    from .runner import http_transport
    def measured(url, headers, body, request_timeout):
        network_start = time.perf_counter()
        status, result = (transport or http_transport)(url, headers, body, request_timeout)
        captured.update({'http': status, 'usage': result.get('usage'), 'model': result.get('model'),
                         'network_ms': round((time.perf_counter()-network_start)*1000, 2)})
        return status, result
    with Ledger(db_path, experiment, prices=price_table) as ledger:
        # Never silently create a fresh USD 5 wallet in production.
        if ledger.wallet_cap_nusd() > usd_to_nusd('5'):
            raise BudgetError('Wallet exceeds authorized total')
        ledger.authorize(usd_to_nusd(CAPS[consumer]))
        import_legacy(ledger, legacy_paths)
        ledger.set_block_cap(consumer, usd_to_nusd(CAPS[consumer]))
        arm = 'shared-arm-' + consumer
        ledger.register_arm(arm, 'S01', PROVIDER, MODEL)
        receipt = dispatch(ledger, arm_id=arm, block_id=consumer, provider=PROVIDER,
                           model=MODEL, state=state, questions=questions,
                           request_path='sha256:' + payload_sha256(payload),
                           runtime_manifest_path='executor/shared.py', timeout=timeout, api_key=key,
                           transport=measured, evidence_level='mock_integration' if transport else 'live_component')
        receipt.update({'latency_ms': round((time.perf_counter()-start)*1000, 2),
                        'payload_sha256': payload_sha256(payload),
                        'state_chars': len(state), 'payload_bytes': len(json.dumps(payload, ensure_ascii=False).encode()),
                        'consumer': consumer, 'usage': captured.get('usage'),
                        'network_ms': captured.get('network_ms'),
                        'model_resolved': captured.get('model'), 'price_snapshot': price_table['snapshot_id'],
                        'wallet_committed_nusd': ledger.wallet_committed_nusd(),
                        'evidence_level': 'simulation' if transport else 'live_component', 'sent': True})
        cost = (captured.get('usage') or {}).get('cost')
        receipt['custo_usd'] = cost  # Unknown stays null, not zero.
        answers = receipt.pop('answers', None)
        if receipt['status'] == 'success':
            try:
                strict_answers({'answers': answers}, questions)
            except Exception as error:
                answers = None
                receipt.update({'status': 'invalid_response', 'erro': type(error).__name__})
                ledger.db.execute('UPDATE attempts SET status=? WHERE attempt_id=?',
                                  ('invalid_response', receipt['attempt_id']))
        ledger.db.execute('CREATE TABLE IF NOT EXISTS shared_decisions '
                          '(attempt_id TEXT PRIMARY KEY, recorded_at TEXT, receipt_json TEXT, answers_json TEXT)')
        ledger.db.execute('INSERT INTO shared_decisions VALUES(?,?,?,?)',
                          (receipt['attempt_id'], datetime.now(timezone.utc).isoformat(),
                           json.dumps(receipt, ensure_ascii=False), json.dumps(answers, ensure_ascii=False)))
        if receipt['status'] != 'success':
            receipt['erro'] = receipt['status']
            return None, receipt
        return answers, receipt
