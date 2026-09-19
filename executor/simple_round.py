"""Rodada simples: teste offline do codigo de cada sistema, no ambiente que o proprio repo declara.

Nao faz inferencia paga. Registra o comando usado, o resultado e o motivo exato de cada bloqueio.
Instalar nao conta como testar; mock nao conta como servico real.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'research' / 'sources'
OUT = ROOT / 'runs' / 'simple'

# Variaveis da maquina que redirecionam clientes de LLM e contaminariam o experimento.
POISON = ['OPENAI_BASE_URL', 'OPENAI_API_BASE', 'OPENAI_API_KEY', 'OPENAI_MODEL',
          'ANTHROPIC_BASE_URL', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN']

SUMMARY = re.compile(r'(\d+) (passed|failed|error|errors|passing|failing)', re.I)


def clean_env():
    env = dict(os.environ)
    for name in POISON:
        env.pop(name, None)
    env['CI'] = '1'
    return env


def detect(path):
    """Descobre como o proprio repositorio manda rodar seus testes."""
    if (path / 'Cargo.toml').exists():
        if not shutil.which('cargo'):
            return None, 'rust', 'cargo ausente nesta maquina'
        return ['cargo', 'test', '--quiet'], 'rust', None
    if (path / 'uv.lock').exists():
        if not shutil.which('uv'):
            return None, 'python', 'uv ausente nesta maquina'
        return ['uv', 'run', '--frozen', '--all-extras', 'pytest', '-q', '--no-header'], 'python', None
    if (path / 'pyproject.toml').exists() or (path / 'requirements.txt').exists():
        if not shutil.which('uv'):
            return None, 'python', 'uv ausente nesta maquina'
        return ['uv', 'run', '--with', 'pytest', 'pytest', '-q', '--no-header'], 'python', None
    if (path / 'package.json').exists():
        try:
            pkg = json.loads((path / 'package.json').read_text(encoding='utf-8'))
        except ValueError:
            return None, 'node', 'package.json ilegivel'
        script = (pkg.get('scripts') or {}).get('test')
        if not script:
            return None, 'node', 'package.json sem script de teste'
        if 'npm' not in (shutil.which('npm') or ''):
            if not shutil.which('npm'):
                return None, 'node', 'npm ausente nesta maquina'
        return ['npm', 'test', '--silent'], 'node', None
    return None, 'desconhecido', 'sem manifesto de projeto reconhecido'


def install_node(path, env, timeout):
    lock = (path / 'package-lock.json').exists()
    command = ['npm', 'ci', '--silent', '--no-audit', '--no-fund'] if lock else \
              ['npm', 'install', '--silent', '--no-audit', '--no-fund']
    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=path, env=env, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, shell=(os.name == 'nt'))
    except subprocess.TimeoutExpired:
        return {'ok': False, 'reason': f'instalacao excedeu {timeout}s', 'seconds': timeout}
    return {'ok': done.returncode == 0, 'reason': (done.stderr or done.stdout)[-600:] if done.returncode else None,
            'seconds': round(time.monotonic() - started, 1), 'command': ' '.join(command)}


def run_one(system, timeout=900, install_timeout=600):
    path = SOURCES / system['repo'].split('/')[-1]
    record = {'id': system['id'], 'name': system['name'], 'repo': system['repo'],
              'at': datetime.now(timezone.utc).isoformat(), 'evidence_level': 'offline'}
    if not path.exists():
        record.update(status='blocked', reason='repositorio nao clonado')
        return record
    command, stack, blocked = detect(path)
    record['stack'] = stack
    if blocked:
        record.update(status='blocked', reason=blocked)
        return record
    env = clean_env()
    if stack == 'node':
        install = install_node(path, env, install_timeout)
        record['install'] = install
        if not install['ok']:
            record.update(status='blocked', reason=f"instalacao falhou: {install['reason']}")
            return record
    record['command'] = ' '.join(command)
    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=path, env=env, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=timeout, shell=(os.name == 'nt'))
    except subprocess.TimeoutExpired:
        record.update(status='blocked', reason=f'teste excedeu {timeout}s',
                      seconds=timeout)
        return record
    output = (done.stdout or '') + (done.stderr or '')
    record['seconds'] = round(time.monotonic() - started, 1)
    record['exit_code'] = done.returncode
    record['tail'] = output.strip()[-1200:]
    counts = {}
    for number, label in SUMMARY.findall(output):
        counts[label.lower()] = counts.get(label.lower(), 0) + int(number)
    record['counts'] = counts
    record['status'] = 'passed' if done.returncode == 0 else 'failed'
    return record


def main():
    plan = json.loads((ROOT / 'planning' / 'plan.json').read_text(encoding='utf-8'))
    wanted = sys.argv[1:] or [s['id'] for s in plan['systems']]
    OUT.mkdir(parents=True, exist_ok=True)
    for system in plan['systems']:
        if system['id'] not in wanted:
            continue
        print(f"[{system['id']}] {system['name']} ...", flush=True)
        record = run_one(system)
        (OUT / f"{system['id']}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2),
                                                  encoding='utf-8')
        counts = record.get('counts') or {}
        detail = ' '.join(f'{v} {k}' for k, v in sorted(counts.items())) or record.get('reason', '')
        print(f"  -> {record['status']}: {detail}", flush=True)


if __name__ == '__main__':
    main()
