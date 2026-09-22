#!/usr/bin/env python3
"""Compara as execuções de um job de cron antes e depois de ganhar porteiro.

A promessa do porteiro é substituir a descoberta feita pelo modelo caro. A prova está nas
sessões do próprio job: quantos tokens de entrada e quantas chamadas de ferramenta cada
execução consumiu, e quanto o contexto injetado engordou o prompt — que é pago de novo a cada
volta de ferramenta.

    python3 jev_comparar_job.py 8f2260d9fe4a          # id do job no `hermes cron list`
    python3 jev_comparar_job.py 7e5e2b895040 --dias 30
"""
import argparse
import collections
import json
import sqlite3
import sys
import time

BANCO = '/root/.hermes/state.db'


def sessoes(job, dias):
    conexao = sqlite3.connect(f'file:{BANCO}?mode=ro', uri=True)
    conexao.row_factory = sqlite3.Row
    linhas = []
    for s in conexao.execute(
            "select id, user_id, started_at, input_tokens, output_tokens, tool_call_count "
            "from sessions where source='cron' and started_at > ? order by started_at",
            (time.time() - dias * 86400,)):
        if job not in (s['user_id'] or '') and job not in s['id']:
            continue
        primeira = conexao.execute(
            "select content from messages where session_id=? and role='user' order by timestamp limit 1",
            (s['id'],)).fetchone()
        prompt = primeira[0] if primeira and isinstance(primeira[0], str) else ''
        ferramentas = collections.Counter()
        for m in conexao.execute("select tool_calls from messages where session_id=? and role='assistant' "
                                 "and tool_calls is not null", (s['id'],)):
            try:
                for chamada in json.loads(m['tool_calls']) or []:
                    ferramentas[(chamada.get('function') or {}).get('name')] += 1
            except Exception:
                pass
        linhas.append({'quando': time.strftime('%d/%m %H:%M', time.localtime(s['started_at'])),
                       'prompt': len(prompt), 'entrada': s['input_tokens'] or 0,
                       'saida': s['output_tokens'] or 0, 'ferramentas': s['tool_call_count'] or 0,
                       'principais': dict(ferramentas.most_common(5))})
    return linhas


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('job', help='id do job de cron')
    p.add_argument('--dias', type=int, default=16)
    p.add_argument('--depois', type=int, default=1, help='quantas execuções finais já são "depois"')
    a = p.parse_args()

    linhas = sessoes(a.job, a.dias)
    if not linhas:
        print(f'nenhuma sessão de cron do job {a.job} nos últimos {a.dias} dias')
        return
    print(f"{'quando':12} {'prompt':>7} {'tok in':>9} {'out':>7} {'tools':>6}  principais")
    for l in linhas:
        print(f"{l['quando']:12} {l['prompt']:7} {l['entrada']:9} {l['saida']:7} "
              f"{l['ferramentas']:6}  {l['principais']}")
    antes, depois = linhas[:-a.depois], linhas[-a.depois:]
    if not antes:
        return

    def media(grupo, campo):
        return sum(l[campo] for l in grupo) // len(grupo)

    print(f'\nANTES, média de {len(antes)}: prompt {media(antes, "prompt")}, '
          f'tokens de entrada {media(antes, "entrada")}, ferramentas {media(antes, "ferramentas")}')
    print(f'DEPOIS, média de {len(depois)}: prompt {media(depois, "prompt")}, '
          f'tokens de entrada {media(depois, "entrada")}, ferramentas {media(depois, "ferramentas")}')


if __name__ == '__main__':
    main()
