#!/usr/bin/env python3
"""Porteiro do job Sono de memória (99ce108c2539), diário, entrega local.

Antes: o modelo principal rodava a colheita, lia o snapshot e escolhia de 3 a 7 itens duráveis
entre ~20 candidatos — 47 milhões de tokens em 60 dias, com 33 de 50 execuções sem promover nada.

Agora o porteiro roda a colheita e o snapshot (passos 2 e 3 do prompt, que são scripts) e o Jev
classifica cada candidato: fato durável, procedimento, histórico de sessão, temporário ou nada.
O agente só acorda se algum candidato tiver probabilidade ≥ 0,30 de ser durável (fato ou
procedimento) — corte baixo de propósito: acordar à toa custa um sono, perder um durável custa
uma lição. Sem nenhum, o porteiro grava o relatório local do dia e o agente não roda.
"""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

JOB = 'sono-memoria'
RAIZ = Path('/root/.hermes/memory_pipeline')
SCRIPTS = Path('/root/.hermes/scripts')
CORTE_DURAVEL = 0.30
DURAVEIS = ('fato-duravel', 'procedimento')
PERGUNTA = {
    'destino': {
        'type': 'choice',
        'instructions': ('Trecho de uma conversa do assistente pessoal de Igor. O que este trecho deveria virar '
                         'na memoria do assistente? Considere se ainda vale daqui a um mes.'),
        'criteria': {
            'fato-duravel': 'Preferencia estavel de Igor, fato de ambiente ou convencao que vale por meses.',
            'procedimento': 'Metodo reutilizavel de varios passos ou erro superado que vira regra.',
            'historico-de-sessao': 'Trabalho feito ou resultado pontual, melhor achado na busca de sessoes.',
            'temporario': 'Status do dia, progresso, commit, alerta ou dado que envelhece em dias.',
            'nada': 'Nao vale guardar.',
        },
    },
}


def main():
    for script in ('hermes_memory_harvest.py', 'hermes_memory_snapshot.py'):
        processo = subprocess.run([sys.executable, str(SCRIPTS / script)], capture_output=True, text=True, timeout=600)
        if processo.returncode:
            raise RuntimeError(f'{script}: {(processo.stderr or processo.stdout)[-300:]}')
    try:
        decidir()
    except Exception as erro:
        # A colheita já rodou: se o agente rodar os passos 2 e 3 de novo, a colheita incremental
        # volta vazia e o snapshot perde os candidatos do dia.
        portao.encerrar(JOB, True, f'porteiro falhou depois da colheita: {type(erro).__name__}',
                        '[jev/portão] Colheita e snapshot já rodaram hoje; NÃO rode os passos 2 e 3 de novo. '
                        'Comece pelo passo 4 com o snapshot do dia.')


def decidir():
    hoje = date.today().isoformat()
    caixa = RAIZ / 'inbox' / f'candidates_{hoje}.jsonl'
    candidatos = []
    if caixa.exists():
        for linha in caixa.read_text(encoding='utf-8', errors='ignore').splitlines():
            try:
                candidatos.append(json.loads(linha))
            except ValueError:
                pass
    candidatos = sorted(candidatos, key=lambda c: -int(c.get('score', 0)))[:80]
    if not candidatos:
        relatorio(hoje, 0, [])
        portao.encerrar(JOB, False, 'nenhum candidato novo')
        return
    estados = [f"SESSAO: {c.get('session_title', '')}\nTRECHO: {(c.get('excerpt') or '')[:1500]}" for c in candidatos]
    resultados = nucleo.classificar_em_paralelo(estados, PERGUNTA, origem='portao-sono-memoria',
                                                tempo_total=90, limite=2500)
    resumo = nucleo.resumo_das_chamadas(resultados)
    if resumo['falha'] and resumo['chamadas'] + resumo['do_cache'] < len(candidatos):
        raise RuntimeError(f"Jev incompleto: {resumo['falha']}")
    provaveis = []
    for c, (respostas, _) in zip(candidatos, resultados):
        p = portao.probabilidade(respostas, 'destino', DURAVEIS)
        if p >= CORTE_DURAVEL:
            provaveis.append((p, c, nucleo.escolha(respostas, 'destino')[0]))
    if not provaveis:
        relatorio(hoje, len(candidatos), [])
        portao.encerrar(JOB, False, f'{len(candidatos)} candidato(s), nenhum durável', custo_jev_usd=resumo['custo_usd'])
        return
    provaveis.sort(key=lambda x: -x[0])
    linhas = [f'[jev/portão] Colheita e snapshot já rodaram (NÃO rode os passos 2 e 3 de novo). {len(candidatos)} '
              f'candidato(s); o Jev marcou {len(provaveis)} como provavelmente duráveis — comece por eles:']
    linhas += [f"- id={c.get('id')} ({classe}, p={nucleo.dec(p)}): {(c.get('excerpt') or '')[:160]}"
               for p, c, classe in provaveis[:15]]
    portao.encerrar(JOB, True, f'{len(provaveis)} candidato(s) durável(is)', '\n'.join(linhas),
                    custo_jev_usd=resumo['custo_usd'])


def relatorio(hoje, total, _):
    destino = RAIZ / 'reports' / f'sono_memoria_{hoje}.md'
    if destino.exists():
        return
    destino.write_text(f'# Sono de Memória — {hoje}\n\n- Porteiro do Jev: {total} candidato(s) colhido(s), nenhum com '
                       f'probabilidade ≥ {CORTE_DURAVEL} de ser fato durável ou procedimento.\n- Nenhuma promoção; '
                       'modelo principal não acordado. Sem sonho registrado neste ciclo.\n', encoding='utf-8')


if __name__ == '__main__':
    portao.executar(JOB, main)
