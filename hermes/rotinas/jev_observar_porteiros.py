#!/usr/bin/env python3
"""Observa as primeiras execuções agendadas dos porteiros novos e escreve o que o agente fez.

Roda na VPS, solto do terminal. Para cada job, registra em `estado/primeiras-execucoes.md`: a
decisão do porteiro, quantas buscas na web o agente ainda fez (a medida de o porteiro ter
mesmo substituído a descoberta) e o tamanho do prompt da execução.
"""
import json
import re
import time
from pathlib import Path

ESTADO = Path('/root/.hermes/integrations/jev/estado')
SAIDAS = Path('/root/.hermes/cron/output')
RELATORIO = ESTADO / 'primeiras-execucoes.md'
JOBS = {'boletim-taguatinga': '7e5e2b895040', 'tese-diaria': '8f2260d9fe4a'}
FERRAMENTAS = ('web_search', 'web_extract', 'browser_navigate', 'execute_code', 'terminal',
               'read_file', 'search_files', 'skill_view')
LIMITE = 8 * 3600


def portoes():
    linhas = []
    try:
        for linha in (ESTADO / 'portoes.jsonl').read_text(encoding='utf-8').splitlines():
            try:
                linhas.append(json.loads(linha))
            except ValueError:
                pass
    except OSError:
        pass
    return linhas


def ultima_saida(job_id):
    pasta = SAIDAS / job_id
    arquivos = sorted(pasta.glob('*.md')) if pasta.exists() else []
    return arquivos[-1] if arquivos else None


def relatar(nome, job_id, antes):
    arquivo = ultima_saida(job_id)
    texto = arquivo.read_text(encoding='utf-8', errors='replace') if arquivo else ''
    prompt = texto[:texto.find('\n## Response')] if '\n## Response' in texto else texto
    resposta = texto.split('\n## Response', 1)[1] if '\n## Response' in texto else ''
    usos = {f: len(re.findall(rf'\b{f}\b', texto)) for f in FERRAMENTAS}
    porteiro = [p for p in portoes() if p.get('job') == nome][-1:]
    with RELATORIO.open('a', encoding='utf-8') as saida:
        saida.write(f'\n## {nome} — {arquivo.name if arquivo else "sem saída"}\n\n')
        saida.write(f'- Porteiro: {json.dumps(porteiro[-1], ensure_ascii=False) if porteiro else "—"}\n')
        saida.write(f'- Prompt da execução: {len(prompt)} caracteres (antes do porteiro havia '
                    f'{antes} caracteres de média)\n')
        saida.write(f'- Ferramentas citadas na saída: {usos}\n')
        saida.write(f'- Resposta (começo):\n\n```\n{resposta.strip()[:800]}\n```\n')


def main():
    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO.write_text(f'# Primeiras execuções agendadas dos porteiros novos\n\n'
                         f'Observador iniciado em {time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}.\n',
                         encoding='utf-8')
    pendentes = {}
    for nome, job_id in JOBS.items():
        arquivo = ultima_saida(job_id)
        pendentes[nome] = (job_id, arquivo.name if arquivo else '', len(
            (arquivo.read_text(encoding='utf-8', errors='replace') if arquivo else '').split('\n## Response')[0]))
    inicio = time.time()
    while pendentes and time.time() - inicio < LIMITE:
        time.sleep(60)
        for nome, (job_id, visto, antes) in list(pendentes.items()):
            arquivo = ultima_saida(job_id)
            if arquivo and arquivo.name != visto:
                time.sleep(90)  # deixa a execução terminar de escrever
                relatar(nome, job_id, antes)
                del pendentes[nome]
    if pendentes:
        with RELATORIO.open('a', encoding='utf-8') as saida:
            saida.write(f'\nSem execução em {LIMITE // 3600} h para: {", ".join(pendentes)}.\n')


if __name__ == '__main__':
    main()
