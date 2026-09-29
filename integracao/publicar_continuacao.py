"""Reconcile harness evidence with the original plan, without claiming smoke completion."""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.server import validate_state
from integracao.harness.agent_client import Client

NAMES = ['jev-cli', 'jev-search', 'Janus', 'pi-warden', 'jev-ultrafast',
         'jevcal', 'jev-rerank-bench', 'system-one-adapter-python', 'jev-review',
         'every', 'heist-one', 'openjev', 'pi-model-router', 'should-ai-kill-us-all', 'Jeeves']
NEXT = [
    'Completar os 12 cenários contratuais do plano; smoke real existente: 7/7 sintéticos. Aprofundamento: corpus real separado por tarefa.',
    'Configurar Search1API e adaptar inferência à carteira antes de busca real; ranking pode avançar com candidatos congelados.',
    'Reproduzir roteamento com pares locais e separação dev/calibração/teste; replay histórico não valida limiar local.',
    'Corrigir 4 falhas de caminhos/permissões e testar episódios no Pi; integração de supervisão no Codex não existe.',
    'Adaptar os dois clientes pagos à carteira antes de executar tarefas de navegador com limite de passos.',
    'Avaliar calibração nos mesmos pares locais do Janus; demonstração sintética não mede qualidade real.',
    'Congelar consultas, candidatos e relevâncias; integrar transporte compartilhado antes de ranking real e comparação com baseline.',
    'Diagnosticar 31 falhas de fixtures/autenticação antes de validar o adaptador ponta a ponta.',
    'Preparar diffs pequenos com defeitos conhecidos e controles limpos para revisão real pela ponte.',
    'Ampliar além das duas funções sintéticas já acertadas; medir falsos positivos em funções com gabarito independente.',
    'Separar ações roteirizadas de decisões reais; preparar estados idênticos por semente e ponte financeira.',
    'Verificar licença, tamanho e compatibilidade dos pesos antes de download e medir inferência em CPU; CUDA ausente.',
    'Testar roteamento dentro do Pi em tarefas pareadas; não controla modelos do Codex.',
    'Preparar conjuntos fixos de manchetes e adaptar cliente à carteira; os dois checks atuais são simulados.',
    'Configurar PostgreSQL descartável para os 24 testes ignorados; contas Discord/Twitch permanecem fora desta rodada.',
]


def main():
    source = json.loads((ROOT / 'integracao/harness/resultados.json').read_text(encoding='utf-8'))
    records = {r['system']: r for r in source['systems']}
    url = 'http://127.0.0.1:8766/api/state'
    state = json.load(urllib.request.urlopen(url, timeout=5))
    existing = {r['id'] for r in state['runs']}
    now = datetime.now(timezone.utc).isoformat()
    added = 0
    for i, name in enumerate(NAMES):
        sid = f'S{i+1:02}'
        row = records[name]
        run_id = 'harness-instalacao-20260921-' + sid
        summary = (f"Instalação 21/09: {row['tests_passed']} testes passaram, "
                   f"{row['tests_failed']} falharam, {row['tests_skipped']} ignorados. "
                   if row['tests_passed'] is not None else
                   'Instalação 21/09: tipagem, dependências e sintaxe verificadas; sem contagem de testes funcionais. ')
        summary += 'Fonte: integracao/harness/resultados.json e RELATORIO.md. Revisão ' + row['revision'] + '. '
        if run_id not in existing:
            state['runs'].append(dict(id=run_id, system_id=sid, phase='simple', evidence='offline',
                status='failed' if row['tests_failed'] else 'completed',
                started_at=source['date']+'T00:00:00+00:00', finished_at=now,
                notes=summary + 'Data da coleta; horário original não registrado neste resumo. Não é aprovação do smoke integral.',
                attempts=[], decisions=[]))
            progress = state['system_progress'].setdefault(sid, {})
            if progress.get('simple') == 'blocked':
                progress['simple'] = 'running'
            progress['notes'] = summary + 'Próximo passo: ' + NEXT[i] + ' Rodada completa ainda depende dos critérios e amostras do plano.'
            progress['updated_at'] = now
            added += 1
    client = Client()
    for path in sorted((ROOT/'runs/continuacao-20260921').glob('*.json')):
        job = json.loads(path.read_text(encoding='utf-8'))
        if 'job_id' not in job:
            continue
        run_id = 'harness-job-' + job['job_id']
        if run_id in existing:
            continue
        logs, offset = [], 0
        while True:
            page = client.call('logs', {'job_id':job['job_id'], 'offset':offset})
            logs.append(page['text'])
            if not page['has_more']: break
            offset = page['next_offset']
        path.with_suffix('.log').write_text(''.join(logs), encoding='utf-8')
        state['runs'].append(dict(id=run_id, system_id=f"S{NAMES.index(job['tool'])+1:02}",
            phase='simple', evidence='mock_integration' if job['tool']=='should-ai-kill-us-all' else 'offline',
            status='completed' if job['state']=='succeeded' else 'failed',
            started_at=datetime.fromtimestamp(job['started_at_unix'],timezone.utc).isoformat(),
            finished_at=datetime.fromtimestamp(job['finished_at_unix'],timezone.utc).isoformat(),
            notes=f"Nova execução {job['tool']}: {job['state']}, saída {job['exit_code']}, {job['duration_seconds']} segundos. Job {job['job_id']}. Sem inferência paga. Logs: {path.with_suffix('.log').relative_to(ROOT).as_posix()}. Teste local não conclui o smoke integral.",
            attempts=[], decisions=[]))
        added += 1
    if not added:
        print('Sem novas evidências; nada alterado.')
        return
    state['events'].append(dict(at=now, kind='evidence', text=f'Continuação: {added} registros de evidência. Bloqueios antigos de instalação substituídos por pendências específicas; testes completos não declarados concluídos. Central executável: http://127.0.0.1:8767'))
    state['events'] = state['events'][-500:]
    validate_state(state)
    request = urllib.request.Request(url, data=json.dumps(state).encode(), method='PUT',
        headers={'Content-Type':'application/json','X-Jev-Lab':'1'})
    with urllib.request.urlopen(request, timeout=5) as response:
        print(f'{added} registros publicados, HTTP {response.status}')


if __name__ == '__main__':
    main()
