"""Real repository retrieval experiment with a frozen lexical comparator."""
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path
import sys

from .run_e15 import excerpt, sha, encoded
from .shared import ROOT
from .assist import RUBRICS, evaluate

OUT = ROOT / 'runs/e16-recuperacao'
PROTOCOL = ROOT / 'planning/preregistro-E16-recuperacao.md'
QUERIES = [
    ('load_api_key', 'De onde o cliente carrega a chave quando ela nao esta no ambiente?'),
    ('estimate_input_tokens', 'Como e feita a estimativa informativa de tokens do payload?'),
    ('reservation_tokens', 'Qual teto de tokens de entrada e reservado antes da chamada?'),
    ('reservation_output_tokens', 'Como e validado o maximo publicado de tokens de saida?'),
    ('reported_cost_nusd', 'Como o custo reportado em usage.cost e convertido para nanodolares?'),
    ('usage_from', 'Como sao normalizados input_tokens e prompt_tokens na resposta?'),
    ('payload_sha256', 'Como e produzido o hash SHA256 do payload com ordem estavel das chaves?'),
    ('validate_contract', 'Como o contrato valida as opcoes de choice e a escala de score?'),
]


def prepare():
    OUT.mkdir(exist_ok=True, parents=True)
    if (OUT / 'manifest.json').exists():
        raise RuntimeError('Already frozen')
    sources = [excerpt('executor/runner.py', function) for function, _ in QUERIES]
    rng = random.Random(20260919)
    rows = []
    for index, (function, query) in enumerate(QUERIES):
        others = [i for i in range(len(sources)) if i != index]
        chosen = [index] + rng.sample(others, 3)
        rng.shuffle(chosen)
        for candidate in chosen:
            source, origin = sources[candidate]
            tokens = lambda text: set(re.findall(r'\w+', text.lower()))
            rows.append({'id': f'q{index}-c{candidate}', 'query_id': index,
                         'query': query, 'text': source, 'source': origin,
                         'source_sha256': sha(source.encode()), 'essential': candidate == index,
                         'lexical_score': len(tokens(query) & tokens(source))})
    data = encoded(rows)
    (OUT / 'corpus.json').write_bytes(data)
    (OUT / 'manifest.json').write_text(json.dumps({
        'created_at': datetime.now(timezone.utc).isoformat(), 'n': len(rows),
        'corpus_sha256': sha(data), 'protocol_sha256': sha(PROTOCOL.read_bytes()),
        'rubric_sha256': sha(encoded(RUBRICS['context']))}, indent=2), encoding='utf-8')
    print('Frozen 8 queries, 32 real code candidates')


def execute():
    raw = (OUT / 'corpus.json').read_bytes()
    manifest = json.loads((OUT / 'manifest.json').read_text())
    assert sha(raw) == manifest['corpus_sha256']
    assert sha(PROTOCOL.read_bytes()) == manifest['protocol_sha256']
    assert sha(encoded(RUBRICS['context'])) == manifest['rubric_sha256']
    path = OUT / 'results.jsonl'
    done = {r['id'] for r in read_results()}
    for row in json.loads(raw):
        if row['id'] in done:
            continue
        result = evaluate('context', f"PERGUNTA: {row['query']}\nTRECHO:\n{row['text']}", consumer='e15')
        result.update({k:v for k,v in row.items() if k != 'text'})
        result['text_bytes'] = len(row['text'].encode())
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(result, ensure_ascii=False) + '\n')
            stream.flush()
            __import__('os').fsync(stream.fileno())
        print(row['id'] + ' persisted', flush=True)
    report()


def read_results():
    path = OUT / 'results.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []


def report():
    rows = read_results()
    scores = {'essencial': 3, 'complementar': 2, 'incerto': 1, 'irrelevante': 0}
    details = []
    for index in range(8):
        group = [r for r in rows if r['query_id'] == index]
        if len(group) != 4:
            continue
        jev = sorted(group, key=lambda r: (scores.get(r['choice'], -1), r['confidence'] or 0), reverse=True)
        lexical = sorted(group, key=lambda r: r['lexical_score'], reverse=True)
        details.append({'query_id': index, 'jev_top1': jev[0]['essential'],
                        'jev_top2': any(r['essential'] for r in jev[:2]),
                        'lexical_top1': lexical[0]['essential'],
                        'lexical_top2': any(r['essential'] for r in lexical[:2]),
                        'all_bytes': sum(r['text_bytes'] for r in group),
                        'top2_bytes': sum(r['text_bytes'] for r in jev[:2]),
                        'order': [r['source'] for r in jev]})
    result = {'scheduled': 32, 'completed': len(rows),
              'invalid': sum(r['choice'] is None for r in rows),
              'queries': len(details), 'details': details,
              'jev_top1': sum(r['jev_top1'] for r in details),
              'jev_top2': sum(r['jev_top2'] for r in details),
              'lexical_top1': sum(r['lexical_top1'] for r in details),
              'lexical_top2': sum(r['lexical_top2'] for r in details),
              'cost_usd': sum(r['receipt'].get('custo_usd') or 0 for r in rows),
              'unknown_costs': sum(r['receipt'].get('custo_usd') is None for r in rows),
              'astra_savings_measured': None}
    (OUT / 'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    {'prepare': prepare, 'execute': execute, 'report': report}[sys.argv[1]]()
