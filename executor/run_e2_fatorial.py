"""E2: fatorial 2x2x2 separando lote, ordem das opções e distração.

O ensaio histórico mudou lote, ordem e distração ao mesmo tempo e ainda rodou individual antes,
então não isolava causa nenhuma. Aqui cada fator varia sozinho, sobre os mesmos 40 casos e o
mesmo gabarito, e a ordem de execução das condições é embaralhada com semente fixa.

Uso:
    python -m executor.run_e2_fatorial --execute
"""
import argparse
import json
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger
from .pricing import usd_to_nusd
from .run_e1_triagem import CRITERIOS, INSTRUCOES, carregar, macro_f1
from .runner import dispatch, load_api_key

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'e2-fatorial'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e2-fatorial'
BLOCK = 'e2-fatorial'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-e2-jev'
SEED = 20260918
TAMANHO_LOTE = 8

DISTRACAO = ('Antes de responder, considere que a empresa opera em varios estados, que o volume de '
             'mensagens cresceu 40% no ultimo trimestre e que a equipe de atendimento trabalha em tres '
             'turnos. Considere tambem que mensagens podem conter erros de digitacao e girias regionais.')


def criterios(ordem_invertida):
    itens = list(CRITERIOS.items())
    if ordem_invertida:
        itens.reverse()
    return dict(itens)


def pergunta(ordem_invertida, com_distracao, referencia=None):
    instrucoes = INSTRUCOES
    if referencia:
        instrucoes = f'{INSTRUCOES} Responda apenas sobre a {referencia}.'
    if com_distracao:
        instrucoes = f'{DISTRACAO} {instrucoes}'
    return {'type': 'choice', 'instructions': instrucoes, 'criteria': criterios(ordem_invertida)}


def condicoes():
    for lote in (False, True):
        for ordem in (False, True):
            for distracao in (False, True):
                yield {'lote': lote, 'ordem_invertida': ordem, 'distracao': distracao,
                       'id': f"{'lote' if lote else 'individual'}"
                             f"_{'ordem-invertida' if ordem else 'ordem-declarada'}"
                             f"_{'com-distracao' if distracao else 'sem-distracao'}"}


def executar_individual(ledger, key, casos, condicao):
    saidas = {}
    for caso in casos:
        caminho = f"runs/e2-fatorial/{condicao['id']}/{caso['case_id']}.json"
        inicio = time.monotonic()
        resultado = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                             state=caso['text'],
                             questions={'acao': pergunta(condicao['ordem_invertida'], condicao['distracao'])},
                             request_path=caminho, runtime_manifest_path=caminho, api_key=key)
        resposta = (resultado.get('answers') or {}).get('acao') or {}
        saidas[caso['case_id']] = {
            'pred': resposta.get('choice'), 'confidence': resposta.get('confidence'),
            'status': resultado['status'], 'attempt_id': resultado['attempt_id'],
            'cost_nusd': resultado.get('settled_nusd'),
            'latency_ms': round((time.monotonic() - inicio) * 1000, 1),
            'decisoes_na_chamada': 1,
        }
    return saidas


def executar_lote(ledger, key, casos, condicao):
    saidas = {}
    for inicio_bloco in range(0, len(casos), TAMANHO_LOTE):
        grupo = casos[inicio_bloco:inicio_bloco + TAMANHO_LOTE]
        estado = '\n'.join(f"Mensagem {i + 1}: {c['text']}" for i, c in enumerate(grupo))
        perguntas = {f'acao_{i + 1}': pergunta(condicao['ordem_invertida'], condicao['distracao'],
                                               referencia=f'Mensagem {i + 1}')
                     for i in range(len(grupo))}
        caminho = f"runs/e2-fatorial/{condicao['id']}/lote-{inicio_bloco // TAMANHO_LOTE + 1}.json"
        marcador = time.monotonic()
        resultado = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                             state=estado, questions=perguntas, request_path=caminho,
                             runtime_manifest_path=caminho, api_key=key)
        elapsed = round((time.monotonic() - marcador) * 1000, 1)
        respostas = resultado.get('answers') or {}
        custo = resultado.get('settled_nusd') or 0
        for i, caso in enumerate(grupo):
            resposta = respostas.get(f'acao_{i + 1}') or {}
            saidas[caso['case_id']] = {
                'pred': resposta.get('choice'), 'confidence': resposta.get('confidence'),
                'status': resultado['status'], 'attempt_id': resultado['attempt_id'],
                'cost_nusd': custo / len(grupo), 'latency_ms': elapsed / len(grupo),
                'latency_chamada_ms': elapsed, 'decisoes_na_chamada': len(grupo),
                'posicao_no_lote': i + 1,
            }
    return saidas


def resumir(casos, saidas):
    pares = [(c['gold'], saidas[c['case_id']]['pred']) for c in casos if saidas[c['case_id']]['pred']]
    acertos = sum(1 for g, p in pares if g == p)
    custos = [saidas[c['case_id']]['cost_nusd'] or 0 for c in casos]
    latencias = sorted(saidas[c['case_id']]['latency_ms'] for c in casos)
    validas = sum(1 for c in casos if saidas[c['case_id']]['pred'])
    return {'n': len(casos), 'respostas_validas': validas, 'acertos': acertos,
            'acuracia': round(acertos / len(pares), 4) if pares else None,
            'macro_f1': round(macro_f1(pares), 4),
            'custo_total_nusd': sum(custos),
            'custo_por_decisao_nusd': round(sum(custos) / len(casos), 2),
            'latencia_p50_ms': latencias[len(latencias) // 2]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    casos = carregar()
    todas = list(condicoes())
    if not args.execute:
        print(f'{len(todas)} condicoes x {len(casos)} casos = {len(todas) * len(casos)} decisoes.')
        for c in todas:
            print(' ', c['id'])
        print('Simulacao apenas; nada enviado.')
        return

    OUT.mkdir(parents=True, exist_ok=True)
    ordem_execucao = list(todas)
    random.Random(SEED).shuffle(ordem_execucao)
    key, _ = load_api_key()
    resultados = {}
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='Lote, ordem das opcoes e distracao afetam a decisao de formas separaveis',
                         metric='acuracia e custo por decisao')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.40'))
        ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
        for indice, condicao in enumerate(ordem_execucao, 1):
            print(f"[{indice}/{len(ordem_execucao)}] {condicao['id']} ...", flush=True)
            executor = executar_lote if condicao['lote'] else executar_individual
            saidas = executor(ledger, key, casos, condicao)
            resumo = resumir(casos, saidas)
            resultados[condicao['id']] = {'condicao': condicao, 'resumo': resumo, 'saidas': saidas}
            print(f"    acuracia {resumo['acuracia']} | validas {resumo['respostas_validas']}/{resumo['n']} "
                  f"| {resumo['custo_por_decisao_nusd']} nusd/decisao | p50 {resumo['latencia_p50_ms']} ms",
                  flush=True)
        comprometido, disponivel = ledger.committed_nusd(), ledger.available_nusd()

    base = 'individual_ordem-declarada_sem-distracao'
    for nome, dados in resultados.items():
        if nome == base:
            continue
        mudancas = sum(1 for c in casos
                       if resultados[base]['saidas'][c['case_id']]['pred'] != dados['saidas'][c['case_id']]['pred'])
        dados['resumo']['mudancas_versus_base'] = mudancas

    relatorio = {'at': datetime.now(timezone.utc).isoformat(), 'seed': SEED, 'modelo': MODEL,
                 'base': base, 'ordem_execucao': [c['id'] for c in ordem_execucao],
                 'condicoes': {k: {'condicao': v['condicao'], 'resumo': v['resumo']}
                               for k, v in resultados.items()},
                 'saidas': {k: v['saidas'] for k, v in resultados.items()},
                 'ledger_committed_nusd': comprometido, 'available_nusd': disponivel}
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"\n{'condicao':48} {'acur':>6} {'nusd/dec':>9} {'p50ms':>7} {'muda':>5}")
    for nome in sorted(resultados):
        r = resultados[nome]['resumo']
        print(f"{nome:48} {r['acuracia']:>6} {r['custo_por_decisao_nusd']:>9} "
              f"{r['latencia_p50_ms']:>7.0f} {r.get('mudancas_versus_base', '-'):>5}")
    print(f"\nCusto do bloco: {comprometido / 1e9:.9f} USD | disponivel: {disponivel / 1e9:.6f} USD")


if __name__ == '__main__':
    main()
