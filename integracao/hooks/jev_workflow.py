"""Local workflow activation. Never sends prompts, reads transcripts or calls a provider."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def activate(event):
    if event.get('hook_event_name') not in (None, 'UserPromptSubmit'):
        return None
    prompt = event.get('prompt')
    if not isinstance(prompt, str) or len(prompt.strip()) < 18:
        return None
    message = (
        'Fluxo JEV ativo: antes de escolher entre ferramentas ou skills plausíveis nesta tarefa, '
        'chame jev_route com task (subtarefa sanitizada), tools e skills (listas de {id,description} '
        'do catálogo REAL desta sessão, até 10 cada). Para escolha explícita use required_tool_id '
        'ou required_skill_id. Não envie o prompt integral nem conteúdo privado sem autorização. '
        'Se não houver MCP jev carregado, grave {"name":"jev_route","arguments":{...}} em JSON '
        f'e execute "{sys.executable}" "{(ROOT / "integracao/usar.py").as_posix()}" --request CAMINHO. '
        'Depois use a ferramenta selecionada se apropriada e leia/aplique o SKILL.md escolhido; '
        'não pare na recomendação. Não repita uma seleção já resolvida sem mudança na tarefa. '
        'Para tarefa trivial ou escolha já explícita, siga direto. Se JEV falhar, abster-se ou '
        'ficar sem saldo, continue normalmente. Nunca delegue autorização, modelo ou esforço. '
        'Este hook não executou nenhuma chamada JEV; confira o recibo do seletor antes de alegar uso.'
    )
    return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext': message}}


def main():
    try:
        event = json.loads(sys.stdin.buffer.read(1_000_001))
        result = activate(event)
        if result:
            sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + '\n').encode('utf-8'))
    except Exception:
        pass


if __name__ == '__main__':
    main()
