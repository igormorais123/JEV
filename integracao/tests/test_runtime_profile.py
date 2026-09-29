import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from executor import shared
from executor.ledger import Ledger, BudgetError
from executor.pricing import load_prices, usd_to_nusd


@pytest.fixture
def profile(tmp_path):
    config = tmp_path / 'runtime.local.json'
    config.write_text(json.dumps({'schema_version': 1, 'profile': 'typesafe-local-20260921'}))
    folder = tmp_path / 'runs/typesafe-smoke-20260921'
    folder.mkdir(parents=True)
    with Ledger(folder / 'ledger.sqlite3', 'setup') as ledger:
        ledger.set_wallet_cap(usd_to_nusd('0.03'))
    prices = load_prices()
    prices['captured_at_utc'] = datetime.now(timezone.utc).isoformat()
    prices['models']['typesafe:jev-1.13.0']['output_nusd_per_million_tokens'] = 0
    (folder / 'precos.json').write_text(json.dumps(prices))
    with patch.object(shared, 'ROOT', tmp_path), patch.object(shared, 'ACTIVE_PROFILE', config):
        yield folder, config


def test_profile_reuses_existing_wallet(profile):
    folder, _ = profile
    runtime = shared.active_runtime()
    assert runtime['db_path'] == folder / 'ledger.sqlite3'
    assert runtime['provider'] == 'typesafe'
    assert runtime['legacy_paths'] == ()
    assert shared.CAPS[runtime['consumer']] == '0.03'


def test_unknown_profile_cannot_fall_back(profile):
    _, config = profile
    config.write_text('{"profile":"other"}')
    with pytest.raises(BudgetError):
        shared.active_runtime()


def test_stale_price_blocks_calls_but_allows_status(profile):
    folder, _ = profile
    path = folder / 'precos.json'
    prices = json.loads(path.read_text())
    prices['captured_at_utc'] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    path.write_text(json.dumps(prices))
    with pytest.raises(BudgetError):
        shared.active_runtime()
    assert shared.active_runtime(require_fresh=False)


def test_wallet_cannot_silently_expand(profile):
    folder, _ = profile
    with Ledger(folder / 'ledger.sqlite3', 'setup') as ledger:
        ledger.set_wallet_cap(usd_to_nusd('5'))
    with pytest.raises(BudgetError):
        shared.active_runtime()
