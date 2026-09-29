from unittest.mock import patch
import pytest
from integracao.seletores import select

CANDIDATES = [{'id': 'pdf', 'description': 'Ler PDFs'}, {'id': 'slides', 'description': 'Criar slides'}]


@pytest.mark.parametrize('kind', ['tool', 'skill'])
def test_maps_model_choice_to_available_id(kind):
    with patch('integracao.seletores.shared.ask', return_value=(
        {'selection': {'choice': 'c0', 'confidence': .95}}, {'status': 'success', 'sent': True})):
        result = select(kind, 'Extrair texto PDF', CANDIDATES)
    assert result['selected_id'] == 'pdf'
    assert result['candidates'] == ['pdf', 'slides']
    assert result['autonomous'] is False


@pytest.mark.parametrize('choice,confidence,reason', [('c0', .5, 'low_confidence'),
    ('nenhum', .99, 'no_match'), ('inventado', .99, 'unavailable_or_invalid_response'),
    ('c0', float('nan'), 'unavailable_or_invalid_response')])
def test_abstains(choice, confidence, reason):
    with patch('integracao.seletores.shared.ask', return_value=(
        {'selection': {'choice': choice, 'confidence': confidence}}, {'status': 'success'})):
        result = select('skill', 'tarefa', CANDIDATES)
    assert result['selected_id'] is None
    assert result['reason'] == reason


def test_user_explicit_choice_never_calls_provider():
    with patch('integracao.seletores.shared.ask') as ask:
        result = select('skill', 'tarefa', CANDIDATES, required_id='slides')
    ask.assert_not_called()
    assert result['selected_id'] == 'slides'
    assert result['paid_call'] is False


def test_duplicate_ids_rejected_before_payment():
    with patch('integracao.seletores.shared.ask') as ask:
        with pytest.raises(ValueError):
            select('tool', 'tarefa', [CANDIDATES[0], CANDIDATES[0]])
    ask.assert_not_called()
