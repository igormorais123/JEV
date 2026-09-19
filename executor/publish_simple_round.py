"""Publica as fichas da rodada simples no painel local, sem inventar desempenho.

Cada sistema vira um run com nivel de evidencia explicito. Teste offline do codigo nao
e inferencia real e nao recebe metrica de acuracia.
"""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'runs' / 'simple'
BASE = 'http://127.0.0.1:8766'


def state():
    return json.load(urllib.request.urlopen(BASE + '/api/state'))


def save(payload):
    request = urllib.request.Request(BASE + '/api/state',
                                     data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                                     method='PUT',
                                     headers={'Content-Type': 'application/json', 'X-Jev-Lab': '1'})
    return json.load(urllib.request.urlopen(request))


def note_for(record):
    counts = record.get('counts') or {}
    if record['status'] == 'blocked':
        return f"Bloqueado: {record.get('reason')}. Nada foi executado; o sistema permanece em inspecao."
    parts = ', '.join(f'{v} {k}' for k, v in sorted(counts.items())) or 'sem contagem no relatorio'
    return (f"Suite propria do repositorio ({record.get('command')}): {parts}. "
            f"Saida {record.get('exit_code')} em {record.get('seconds')}s. "
            'Teste offline do codigo; nao e inferencia real do componente.')


def main():
    current = state()
    now = datetime.now(timezone.utc).isoformat()
    existing = {r['id'] for r in current['runs']}
    added = 0
    for file in sorted(RESULTS.glob('S*.json')):
        record = json.loads(file.read_text(encoding='utf-8'))
        run_id = f"rodada-simples-offline-{record['id']}"
        if run_id in existing:
            continue
        current['runs'].append({
            'id': run_id, 'system_id': record['id'], 'phase': 'simple', 'evidence': 'offline',
            'status': 'completed' if record['status'] != 'blocked' else 'failed',
            'started_at': record['at'], 'finished_at': now,
            'notes': note_for(record)[:6000], 'attempts': [], 'decisions': [],
        })
        # Passar na suite offline nao conclui a rodada simples: o plano exige inferencia
        # real do componente. So 'blocked' e terminal aqui.
        status = {'passed': 'running', 'failed': 'running', 'blocked': 'blocked'}[record['status']]
        progress = current['system_progress'].setdefault(record['id'], {})
        progress['simple'] = status
        progress['notes'] = note_for(record)[:6000]
        progress['updated_at'] = now
        added += 1
    if added:
        current['events'].append({
            'at': now, 'kind': 'evidence',
            'text': (f'Rodada simples, camada offline: {added} sistemas receberam ficha com o resultado da '
                     'suite declarada pelo proprio repositorio, em ambiente limpo das variaveis de LLM da '
                     'maquina. Nenhuma inferencia paga nesta camada.')[:1200],
        })
        current['events'] = current['events'][-500:]
        result = save(current)
        print(f"{added} fichas publicadas | revisao {result['revision']}")
    else:
        print('Nada novo a publicar.')


if __name__ == '__main__':
    main()
