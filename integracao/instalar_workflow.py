"""Install/remove the local task-entry hook without replacing other handlers."""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def configure(path, remove=False):
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if path.exists():
        shutil.copy2(path, path.with_name(path.name + '.bak-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f')))
    groups = data.setdefault('hooks', {}).setdefault('UserPromptSubmit', [])
    kept = []
    for group in groups:
        handlers = [h for h in group.get('hooks', []) if 'jev_workflow.py' not in h.get('command', '')]
        if handlers:
            kept.append({**group, 'hooks': handlers})
    if not remove:
        command = f'"{sys.executable}" "{(ROOT / "integracao/hooks/jev_workflow.py").as_posix()}"'
        kept.append({'hooks': [{'type': 'command', 'command': command, 'timeout': 3}]})
    data['hooks']['UserPromptSubmit'] = kept
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    for path in (Path.home() / '.codex/hooks.json', Path.home() / '.claude/settings.json'):
        configure(path, args.remove)
        print(('Removed: ' if args.remove else 'Installed: ') + str(path))


if __name__ == '__main__':
    main()
