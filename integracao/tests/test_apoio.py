from unittest.mock import patch
import pytest
from integracao import apoio
from executor import shared
from executor.ledger import BudgetError


def question(identity='tema'):
    return {'id': identity, 'instructions': 'Classifique o tema do texto.',
            'choices': {'tecnico': 'Trata de software.', 'incerto': 'Não há informação suficiente.'}}


def test_independent_questions_share_one_call():
    with patch.object(shared, 'ask', return_value=({'tema': {'choice': 'tecnico', 'confidence': .9}}, {'status': 'success'})) as ask:
        result = apoio.judge('Public software example', [question(), question('outro')])
    ask.assert_called_once()
    assert len(ask.call_args.args[1]) == 2
    assert result['autonomous'] is False


@pytest.mark.parametrize('questions', [[], [question(), question()],
    [{'id': 'a', 'instructions': 'tema', 'choices': {'a': 'A', 'b': 'B'}}],
    [question(str(i)) for i in range(9)]])
def test_invalid_rubrics_never_reach_transport(questions):
    with patch.object(shared, 'ask') as ask:
        with pytest.raises(ValueError):
            apoio.judge('x', questions)
    ask.assert_not_called()


def test_missing_wallet_status_creates_nothing(tmp_path):
    path = tmp_path / 'absent.sqlite3'
    with patch.object(shared, 'DB', path), patch.object(shared, 'active_runtime', return_value=None):
        result = apoio.status()
    assert result['reason'] == 'missing_wallet'
    assert not path.exists()


def test_missing_wallet_blocks_before_credentials_or_network(tmp_path):
    path = tmp_path / 'absent.sqlite3'
    with patch.object(shared, 'load_api_key') as key, patch.object(shared, 'current_prices') as price:
        with pytest.raises(BudgetError):
            shared.ask('x', {'q': {'type': 'choice'}}, db_path=path, provider='openrouter')
    key.assert_not_called()
    price.assert_not_called()
    assert not path.exists()
