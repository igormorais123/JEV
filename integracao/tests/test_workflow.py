from unittest.mock import patch
from integracao.hooks.jev_workflow import activate
from integracao.seletores import route


def test_installer_preserves_other_hooks_and_is_idempotent(tmp_path):
    import json
    from integracao.instalar_workflow import configure
    path = tmp_path / 'hooks.json'
    original = {'hooks': {'PreToolUse': [{'hooks': [{'type': 'command', 'command': 'existing_guard'}]}]},
                'env': {'PREFERENCE': 'value'}}
    path.write_text(json.dumps(original))
    configure(path)
    configure(path)
    data = json.loads(path.read_text())
    assert data['hooks']['PreToolUse'] == original['hooks']['PreToolUse']
    assert data['env'] == original['env']
    assert len(data['hooks']['UserPromptSubmit']) == 1
    configure(path, remove=True)
    assert json.loads(path.read_text())['hooks']['UserPromptSubmit'] == []


def test_hook_contains_no_prompt_or_session_private_values():
    prompt = 'Informação privada que não pode sair do computador: segredo 123'
    result = activate({'prompt': prompt, 'cwd': 'PRIVATE_PATH'})
    text = result['hookSpecificOutput']['additionalContext']
    assert prompt not in text
    assert 'PRIVATE_PATH' not in text
    assert 'jev_route' in text
    assert 'não executou nenhuma chamada' in text


def test_short_confirmation_does_not_route_again():
    assert activate({'prompt': 'sim'}) is None


def test_route_failure_keeps_agent_working():
    with patch('integracao.seletores.select', side_effect=RuntimeError('private diagnostic')):
        result = route('task', [{'id': 'x', 'description': 'd'}], [])
    assert result['tool']['reason'] == 'unavailable'
    assert 'private diagnostic' not in str(result)
    assert result['skill']['reason'] == 'no_candidates'


def test_explicit_choices_do_not_pay():
    c = [{'id': 'x', 'description': 'd'}]
    with patch('integracao.seletores.shared.ask') as ask:
        result = route('task', c, c, 'x', 'x')
    ask.assert_not_called()
    assert result['tool']['selected_id'] == result['skill']['selected_id'] == 'x'
