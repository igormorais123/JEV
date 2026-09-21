import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from executor.ledger import Ledger, BudgetError
from executor.pricing import load_prices, usd_to_nusd
from executor.shared import ask, import_legacy, strict_answers
from executor.assist import RUBRICS
from executor.runner import TransportTimeout, ContractError


@pytest.fixture
def wallet(tmp_path):
    db = tmp_path / 'wallet.sqlite3'
    with Ledger(db, 'setup') as ledger:
        ledger.set_wallet_cap(usd_to_nusd('5'))
    return db


def query(wallet, transport, state='Connection timed out'):
    return ask(state, {'decision': RUBRICS['log']}, consumer='e15', api_key='test', provider='openrouter',
               transport=transport, db_path=wallet, prices=load_prices(), legacy_paths=())


def response(*args):
    return 200, {'model': 'test', 'answers': {'decision': {
        'type': 'choice', 'choice': 'rede', 'confidence': .99}},
        'usage': {'input_tokens': 500, 'output_tokens': 10, 'cost': .000021}}


def test_full_input_is_sent(wallet):
    text = 'a' * 30000 + 'THE_TARGET'
    def capture(url, headers, payload, timeout):
        assert payload['state'].endswith('THE_TARGET')
        assert payload['state'] == text
        return response()
    answers, receipt = query(wallet, capture, text)
    assert answers['decision']['choice'] == 'rede'
    assert receipt['state_chars'] == len(text)
    assert receipt['evidence_level'] == 'simulation'


def test_oversized_input_abstains_without_dispatch(wallet):
    def never(*args):
        pytest.fail('Transport must not run')
    answers, receipt = query(wallet, never, 'a' * 100000)
    assert answers is None and receipt['sent'] is False


def test_timeout_keeps_reservation(wallet):
    def timeout(*args):
        raise TransportTimeout('test')
    answers, receipt = query(wallet, timeout)
    assert answers is None and receipt['custo_usd'] is None
    with Ledger(wallet, 'shared-e15') as ledger:
        assert ledger.wallet_committed_nusd() == 1344000


def test_legacy_import_is_idempotent_and_fail_closed(wallet, tmp_path):
    path = tmp_path / 'old.jsonl'
    path.write_text(json.dumps({'custo_usd': .01, 'http': 200}) + '\n', encoding='utf-8')
    with Ledger(wallet, 'legacy-test') as ledger:
        ledger.authorize(usd_to_nusd('1'))
        import_legacy(ledger, [path])
        first = ledger.wallet_committed_nusd()
        import_legacy(ledger, [path])
        assert ledger.wallet_committed_nusd() == first
        path.write_text('{}\n', encoding='utf-8')
        with pytest.raises(BudgetError):
            import_legacy(ledger, [path])


@pytest.mark.parametrize('confidence', [None, True, float('nan'), 2, 'high'])
def test_bad_confidence_rejected(confidence):
    with pytest.raises((ValueError, TypeError, ContractError)):
        strict_answers({'answers': {'decision': {'type': 'choice', 'choice': 'rede',
                                               'confidence': confidence}}},
                       {'decision': RUBRICS['log']})


def test_concurrent_consumers_share_wallet(wallet):
    with Ledger(wallet, 'setup') as ledger:
        ledger.set_wallet_cap(2_000_000)
    def timeout(*args):
        raise TransportTimeout('uncertain')
    def run(_):
        try:
            return query(wallet, timeout)[1]['status']
        except BudgetError:
            return 'blocked'
    with ThreadPoolExecutor(max_workers=4) as pool:
        result = list(pool.map(run, range(8)))
    assert result.count('timeout') == 1
    assert result.count('blocked') == 7
