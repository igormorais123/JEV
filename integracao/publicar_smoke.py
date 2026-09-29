"""Publish actual TypeSafe smoke records through the dashboard's revision-checked API."""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.server import validate_state


def main():
    folder = ROOT / 'runs/typesafe-smoke-20260921'
    source = json.loads((folder / 'resultados.json').read_text(encoding='utf-8'))
    batch = json.loads((folder / 'mcp-lote-resultado.json').read_text(encoding='utf-8'))
    protocol = json.loads((folder / 'mcp-lote-protocolo.json').read_text(encoding='utf-8'))
    attempts, decisions = [], []
    def attempt(receipt):
        usage = receipt.get('usage') or {}
        settled = receipt.get('settled_nusd')
        return {'id': receipt['attempt_id'], 'status': 'success', 'latency_ms': receipt['latency_ms'],
                'input_tokens': usage.get('input_tokens'), 'output_tokens': usage.get('output_tokens'),
                'cost_usd': settled / 1e9 if settled is not None else None,
                'reserved_usd': 0, 'cache_hit': False}
    for row in source['cases']:
        if row['receipt']['status'] != 'success':
            raise ValueError('Incomplete smoke; review before publishing')
        attempts.append(attempt(row['receipt']))
        decisions.append({'id': 'typesafe-smoke:' + row['id'], 'case_id': 'typesafe-smoke:' + row['id'],
            'attempt_id': row['receipt']['attempt_id'], 'task': row['task'], 'split': 'diagnostic',
            'expected': row['expected'], 'predicted': row['predicted'], 'correct': row['correct'],
            'confidence': row['confidence']})
    if batch['receipt']['status'] != 'success':
        raise ValueError('Batch did not succeed')
    attempts.append(attempt(batch['receipt']))
    for key, answer in batch['answers'].items():
        decisions.append({'id': 'typesafe-mcp:' + key, 'case_id': 'typesafe-mcp:' + key,
            'group_id': 'typesafe-mcp:same-message', 'attempt_id': batch['receipt']['attempt_id'],
            'task': key, 'split': 'diagnostic', 'expected': protocol['expected'][key],
            'predicted': answer['choice'], 'correct': answer['choice'] == protocol['expected'][key],
            'confidence': answer['confidence']})
    run = {'id': 'typesafe-local-smoke-20260921', 'system_id': 'S01', 'phase': 'pilot',
        'evidence': 'live_component', 'status': 'completed', 'started_at': source['started_at'],
        'finished_at': datetime.now(timezone.utc).isoformat(), 'provider': 'typesafe', 'model': source['model'],
        'dataset': 'Smoke sintético e lote de duas perguntas; gabaritos prévios do assistente',
        'notes': 'Piloto do componente JEV e ferramentas locais; não execução integral do CLI S01. '
                 'Orçamento NOVO separado de US$ 0,03. Custo calculado por usage e tarifa, não extrato '
                 'do provedor. 8 casos individuais e 2 decisões dependentes sobre a mesma mensagem.',
        'attempts': attempts, 'decisions': decisions, 'artifacts': []}
    package = {'kind': 'jev-lab-results', 'schema_version': 1, 'runs': [run]}
    (folder / 'painel-importar.json').write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding='utf-8')
    url = 'http://127.0.0.1:8766/api/state'
    with urllib.request.urlopen(url, timeout=5) as response:
        state = json.load(response)
    if any(r['id'] == run['id'] for r in state['runs']):
        print('Already published; no duplicate costs.')
        return
    state['runs'].append(run)
    state['events'].append({'at': datetime.now(timezone.utc).isoformat(), 'kind': 'evidence',
        'text': 'TypeSafe local: 9 chamadas reais, 10 decisões corretas; piloto sintético. Orçamento separado de US$ 0,03.'})
    state['events'] = state['events'][-500:]
    validate_state(state)
    request = urllib.request.Request(url, data=json.dumps(state).encode(), method='PUT',
        headers={'Content-Type': 'application/json', 'X-Jev-Lab': '1'})
    with urllib.request.urlopen(request, timeout=5) as response:
        print('Published:', response.status)


if __name__ == '__main__':
    main()
