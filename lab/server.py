"""Local dashboard server. No inference endpoints or access to .env.

Run: python lab/server.py --port 8766
"""
import argparse
import json
import math
import os
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / 'lab/data/execution.json'
LOCK = threading.Lock()
MAX_BYTES = 8 * 1024 * 1024
STATUSES = {'planned', 'running', 'done', 'blocked', 'paused'}
SYSTEMS = {f'S{i:02}' for i in range(1, 16)}
ARTIFACTS = {
    'pdf': 'output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf',
    'plan': 'docs/PLANO-CIENTIFICO-JEV-HELENA.md',
    'matrix': 'planning/matriz-testes.csv',
    'sources': 'research/FONTES.md',
    'schema': 'planning/schema.sql',
    'audit': 'research/hermes/auditoria-local.json',
    'historical': 'research/hermes/fase2-decisoes-do-pdf.csv',
    'guide': 'lab/README.md',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(obj, allowed, label):
    require(isinstance(obj, dict), f'Objeto inválido: {label}')
    require(set(obj).issubset(set(allowed)), f'Campos não reconhecidos em {label}')


def text(value, label, limit=6000):
    require(isinstance(value, str) and len(value) <= limit, f'Texto inválido: {label}')


def numeric(value, label, nullable=False, integer=False):
    if nullable and value is None:
        return
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, f'Número inválido: {label}')
    if integer:
        require(int(value) == value, f'Inteiro esperado: {label}')


def timestamp(value):
    require(isinstance(value, str), 'Data inválida')
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        raise ValueError('Data inválida') from None


def validate_state(state):
    keys(state, ['schema_version', 'revision', 'updated_at', 'system_progress', 'stage_progress',
                 'runs', 'events', 'decision'], 'estado')
    require(type(state.get('schema_version')) is int and state['schema_version'] == 1, 'Versão de formato inválida')
    numeric(state.get('revision'), 'revision', integer=True)
    timestamp(state.get('updated_at'))
    if state.get('decision') is not None:
        # O placar e derivado dos relatorios por executor/placar.py; aqui so conferimos a forma,
        # para que um arquivo torto nao derrube o servidor inteiro.
        decision = state['decision']
        require(isinstance(decision, dict), 'Placar inválido')
        keys(decision, ['atualizado_em', 'veredito', 'cartoes', 'orcamento', 'pendencias',
                        'relatorio_final'], 'placar')
        timestamp(decision.get('atualizado_em'))
        require(isinstance(decision.get('veredito'), dict), 'Veredito inválido')
        require(isinstance(decision.get('cartoes'), list), 'Cartões do placar inválidos')
        require(isinstance(decision.get('pendencias'), list), 'Pendências do placar inválidas')
    require(isinstance(state.get('system_progress'), dict), 'Acompanhamento inválido')
    require(isinstance(state.get('stage_progress'), dict), 'Etapas inválidas')
    for sid, progress in state['system_progress'].items():
        require(sid in SYSTEMS, 'Sistema desconhecido')
        keys(progress, ['simple', 'deep', 'notes', 'updated_at'], 'acompanhamento')
        for field in ['simple', 'deep']:
            if field in progress:
                require(progress[field] in STATUSES, 'Status inválido')
        if 'notes' in progress:
            text(progress['notes'], 'notes')
        if 'updated_at' in progress:
            timestamp(progress['updated_at'])
    for sid, progress in state['stage_progress'].items():
        require(sid in {str(i) for i in range(1, 9)}, 'Etapa inválida')
        keys(progress, ['status', 'updated_at'], 'etapa')
        require(progress.get('status') in STATUSES, 'Status inválido')
        if 'updated_at' in progress:
            timestamp(progress['updated_at'])
    runs = state.get('runs')
    require(isinstance(runs, list) and len(runs) <= 2000, 'Lista de execuções inválida')
    run_ids, global_attempts = set(), set()
    for run in runs:
        keys(run, ['id', 'system_id', 'phase', 'evidence', 'status', 'started_at', 'finished_at', 'provider', 'model', 'dataset', 'notes', 'attempts', 'decisions', 'artifacts'], 'execução')
        text(run.get('id'), 'run.id', 160)
        require(run['id'].strip() and run['id'] not in run_ids, 'ID de execução vazio ou duplicado')
        run_ids.add(run['id'])
        require(run.get('system_id') in SYSTEMS, 'Sistema desconhecido')
        require(run.get('phase') in {'simple', 'deep', 'pilot', 'confirmation'}, 'Rodada inválida')
        require(run.get('evidence') in {'offline', 'replay', 'live_component', 'mock_integration', 'live_e2e'}, 'Evidência inválida')
        require(run.get('status') in {'running', 'completed', 'failed'}, 'Status de execução inválido')
        timestamp(run.get('started_at'))
        if run.get('finished_at') is not None:
            timestamp(run['finished_at'])
        for field in ['provider', 'model', 'dataset', 'notes']:
            if field in run:
                text(run[field], field)
        attempts, decisions = run.get('attempts'), run.get('decisions')
        require(isinstance(attempts, list) and len(attempts) <= 10000, 'Tentativas inválidas')
        require(isinstance(decisions, list) and len(decisions) <= 50000, 'Decisões inválidas')
        ids = set()
        for attempt in attempts:
            keys(attempt, ['id', 'status', 'latency_ms', 'input_tokens', 'output_tokens', 'cost_usd', 'reserved_usd', 'cache_hit', 'error'], 'tentativa')
            text(attempt.get('id'), 'attempt.id', 160)
            aid = attempt['id']
            require(aid and aid not in global_attempts, 'ID de tentativa vazio ou duplicado; duplicaria custo')
            ids.add(aid)
            global_attempts.add(aid)
            require(attempt.get('status') in {'success', 'timeout', 'error', 'pending'}, 'Status de tentativa inválido')
            require('cost_usd' in attempt and 'latency_ms' in attempt, 'Custo/latência ausentes; use null se desconhecidos')
            numeric(attempt['cost_usd'], 'cost_usd', nullable=True)
            numeric(attempt.get('reserved_usd'), 'reserved_usd')
            numeric(attempt['latency_ms'], 'latency_ms', nullable=True)
            for field in ['input_tokens', 'output_tokens']:
                require(field in attempt, 'Contagem de tokens ausente; use null')
                numeric(attempt[field], field, nullable=True, integer=True)
            require(type(attempt.get('cache_hit')) is bool, 'cache_hit inválido')
            if 'error' in attempt:
                text(attempt['error'], 'error')
        decision_ids = set()
        for decision in decisions:
            keys(decision, ['id', 'case_id', 'attempt_id', 'task', 'split', 'expected', 'predicted', 'correct', 'confidence', 'question_id', 'group_id'], 'decisão')
            for field in ['id', 'case_id', 'attempt_id', 'task', 'split']:
                text(decision.get(field), field, 250)
            require(decision['id'] and decision['id'] not in decision_ids, 'Decisão duplicada ou vazia')
            decision_ids.add(decision['id'])
            require(decision['attempt_id'] in ids, 'Decisão sem tentativa correspondente')
            require(decision['split'] in {'pilot', 'development', 'calibration', 'test', 'diagnostic'}, 'Partição inválida')
            for field in ['expected', 'predicted']:
                require(field in decision and (decision[field] is None or isinstance(decision[field], str)), 'Rótulo deve ser texto ou null')
            require('correct' in decision and (decision['correct'] is None or type(decision['correct']) is bool), 'Acerto inválido')
            require('confidence' in decision, 'Confidence ausente; use null')
            numeric(decision['confidence'], 'confidence', nullable=True)
            require(decision['confidence'] is None or decision['confidence'] <= 1, 'Confidence maior que 1')
            for field in ['question_id', 'group_id']:
                if field in decision:
                    text(decision[field], field, 250)
        if 'artifacts' in run:
            require(isinstance(run['artifacts'], list) and len(run['artifacts']) <= 100, 'Artefatos inválidos')
            for artifact in run['artifacts']:
                keys(artifact, ['label', 'url'], 'artefato')
                text(artifact.get('label'), 'label', 250)
                text(artifact.get('url'), 'url', 2000)
    require(isinstance(state.get('events'), list) and len(state['events']) <= 500, 'Eventos inválidos')
    for event in state['events']:
        keys(event, ['at', 'text', 'kind'], 'evento')
        timestamp(event.get('at'))
        text(event.get('text'), 'event.text', 1200)
        require(event.get('kind') in {'manual', 'import', 'evidence'}, 'Tipo de evento inválido')
    encoded = json.dumps(state, ensure_ascii=False)
    require(not re.search(r'sk-or-v1-[a-zA-Z0-9]{20,}|"(?:api[_-]?key|authorization|secret|password)"\s*:', encoded, re.I), 'Possível credencial no pacote')
    return state


def read_state():
    require(STATE_PATH.stat().st_size <= MAX_BYTES, 'Estado excede o tamanho máximo')
    return validate_state(json.loads(STATE_PATH.read_text(encoding='utf-8')))


def validate_run_update(old, new):
    for field in ['id', 'system_id', 'phase', 'evidence', 'started_at', 'provider', 'model', 'dataset', 'finished_at']:
        if old.get(field) is not None and old.get(field) != '':
            require(new.get(field) == old[field], 'Atualização alteraria a identidade ou proveniência da execução')
    if old['status'] != 'running':
        require(new['status'] == old['status'], 'Desfecho de execução encerrada não pode ser reescrito')
    attempts = {a['id']: a for a in new['attempts']}
    for prior in old['attempts']:
        current = attempts.get(prior['id'])
        require(current is not None, 'Atualização removeria uma tentativa')
        for field, value in prior.items():
            if field == 'reserved_usd':
                continue
            if field == 'status' and value == 'pending':
                continue
            if value is None and field in {'cost_usd', 'latency_ms', 'input_tokens', 'output_tokens'}:
                continue
            require(current.get(field) == value, 'Atualização alteraria valor conhecido de tentativa')
    decisions = {d['id']: d for d in new['decisions']}
    require(all(decisions.get(d['id']) == d for d in old['decisions']), 'Atualização alteraria ou removeria decisão')


def write_state(state):
    payload = (json.dumps(state, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    require(len(payload) <= MAX_BYTES, 'Estado excede o tamanho máximo')
    temporary = STATE_PATH.with_suffix('.tmp')
    with temporary.open('wb') as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    # One previous valid revision for recovery; never silently reset a corrupt state.
    backup = STATE_PATH.with_name('execution.previous.json')
    backup.write_bytes(STATE_PATH.read_bytes())
    os.replace(temporary, STATE_PATH)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def allowed_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def reply(self, status, body, mime='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed_host():
            return self.reply(403, {'error': 'Host inválido'})
        path = urlparse(self.path).path
        if path == '/api/state':
            try:
                with LOCK:
                    state = read_state()
                return self.reply(200, state)
            except (OSError, ValueError, KeyError, TypeError):
                return self.reply(422, {'error': 'Arquivo de acompanhamento inválido ou indisponível. Original preservado.'})
        if path in {'/', '/index.html'}:
            file = ROOT / 'lab/index.html'
        elif path.startswith('/artifacts/') and path.rsplit('/', 1)[-1] in ARTIFACTS:
            file = ROOT / ARTIFACTS[path.rsplit('/', 1)[-1]]
        else:
            return self.reply(404, {'error': 'Arquivo não disponível'})
        try:
            mime = {'pdf': 'application/pdf', 'html': 'text/html; charset=utf-8', 'json': 'application/json; charset=utf-8', 'csv': 'text/csv; charset=utf-8'}.get(file.suffix[1:], 'text/plain; charset=utf-8')
            return self.reply(200, file.read_bytes(), mime)
        except OSError:
            return self.reply(404, {'error': 'Arquivo não encontrado'})

    def do_PUT(self):
        origin = self.headers.get('Origin')
        allowed_origins = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        if not self.allowed_host() or (origin and origin not in allowed_origins) or self.headers.get('X-Jev-Lab') != '1':
            return self.reply(403, {'error': 'Origem inválida'})
        if urlparse(self.path).path != '/api/state':
            return self.reply(404, {'error': 'Rota inexistente'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.reply(415, {'error': 'Enviar JSON'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            require(0 < length <= MAX_BYTES, 'Tamanho inválido ou maior que 8 MB')
            new_state = validate_state(json.loads(self.rfile.read(length)))
            with LOCK:
                current = read_state()
                if new_state['revision'] != current['revision']:
                    return self.reply(409, {'error': 'Revisão desatualizada; recarregue os dados'})
                # Edits/imports cannot silently erase evidence from a concurrent run.
                existing = {r['id']: r for r in current['runs']}
                incoming = {r['id']: r for r in new_state['runs']}
                for key, prior in existing.items():
                    require(key in incoming, 'Atualização removeria uma execução')
                    validate_run_update(prior, incoming[key])
                new_state['revision'] += 1
                new_state['updated_at'] = datetime.now(timezone.utc).isoformat()
                write_state(new_state)
            return self.reply(200, new_state)
        except (ValueError, KeyError, TypeError) as error:
            return self.reply(400, {'error': str(error) if isinstance(error, ValueError) else 'Estrutura inválida'})
        except OSError:
            return self.reply(503, {'error': 'Falha ao gravar. A revisão anterior foi preservada.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    read_state()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'JEV Lab: http://127.0.0.1:{server.server_port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
