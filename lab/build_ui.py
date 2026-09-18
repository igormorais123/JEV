"""Build a standalone HTML dashboard from local, credential-free data."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def build():
    lab = ROOT / 'lab'
    plan = json.loads((ROOT / 'planning/plan.json').read_text(encoding='utf-8'))
    with (ROOT / 'research/hermes/fase2-decisoes-do-pdf.csv').open(encoding='utf-8', newline='') as f:
        history = list(csv.DictReader(f))
    state = json.loads((lab / 'data/execution.json').read_text(encoding='utf-8'))
    template = (lab / 'dashboard.html').read_text(encoding='utf-8')
    for marker, value in [('PLAN', plan), ('HISTORY', history), ('INITIAL_STATE', state)]:
        template = template.replace('__'+marker+'__', json.dumps(value, ensure_ascii=False).replace('</', '<\\/'))
    template = template.replace('__CSS__', (lab / 'dashboard.css').read_text(encoding='utf-8'))
    javascript = '\n'.join((lab / file).read_text(encoding='utf-8') for file in ['metrics.js', 'terminal.js', 'dashboard.js'])
    template = template.replace('__JS__', javascript)
    (lab / 'index.html').write_text(template, encoding='utf-8')
    print('Painel gerado: lab/index.html')


if __name__ == '__main__':
    build()
