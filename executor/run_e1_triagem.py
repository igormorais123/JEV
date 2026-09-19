"""E1 piloto, tarefa de triagem: Jev contra regra simples, no corpus pré-registrado.

Uso:
    python -m executor.run_e1_triagem            # só a regra, sem gasto
    python -m executor.run_e1_triagem --execute  # inclui as chamadas ao Jev
"""
import argparse
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .baseline_regra import CLASSES, classificar
from .ledger import Ledger
from .pricing import usd_to_nusd
from .runner import dispatch, load_api_key

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-piloto.jsonl'
OUT = ROOT / 'runs' / 'e1-triagem'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e1-triagem-piloto'
BLOCK = 'e1-piloto'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-e1-jev'

CRITERIOS = {
    'cancelar': 'O remetente pede encerrar, cancelar ou desistir de um pedido, servico ou contrato.',
    'rastrear': 'O remetente pede informacao sobre onde esta, quando chega ou qual o status da entrega.',
    'trocar': 'O remetente pede troca, devolucao com substituicao, reparo ou conserto em garantia.',
    'cobranca': 'O remetente pede segunda via, estorno, reembolso, parcelamento, ou contesta um valor.',
    'informacao': 'O remetente pede apenas esclarecimento ou dado, sem solicitar nenhuma das acoes acima.',
}
INSTRUCOES = ('Classifique a acao que o remetente pede na mensagem. Vale a acao pedida, nao o assunto '
              'mencionado. Acao citada como fala de terceiro, negada, condicional ou ja concluida nao e '
              'a acao pedida.')


def carregar():
    return [json.loads(linha) for linha in CORPUS.read_text(encoding='utf-8').splitlines() if linha.strip()]


def wilson(acertos, total, z=1.96):
    if total == 0:
        return (0.0, 1.0)
    p = acertos / total
    denom = 1 + z * z / total
    centro = (p + z * z / (2 * total)) / denom
    margem = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denom
    return (max(0.0, centro - margem), min(1.0, centro + margem))


def macro_f1(pares):
    """pares: lista de (esperado, predito)."""
    f1s = []
    for classe in CLASSES:
        tp = sum(1 for e, p in pares if e == classe and p == classe)
        fp = sum(1 for e, p in pares if e != classe and p == classe)
        fn = sum(1 for e, p in pares if e == classe and p != classe)
        if tp + fp + fn == 0:
            continue
        precisao = tp / (tp + fp) if tp + fp else 0.0
        revocacao = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * precisao * revocacao / (precisao + revocacao) if precisao + revocacao else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0


def resumo(nome, resultados):
    """Resume um braco SEM deixar resposta ausente sumir da conta.

    Uma chamada que deu timeout, erro HTTP ou resposta invalida nao e um caso a menos:
    e uma falha do braco. Reportamos cobertura, acuracia condicional as respostas validas
    e acuracia sobre todos os casos programados, contando ausencia como erro.
    """
    programados = len(resultados)
    pares = [(r['gold'], r[nome]) for r in resultados if r.get(nome)]
    acertos = sum(1 for e, p in pares if e == p)
    por_familia = defaultdict(list)
    for r in resultados:
        # Caso sem resposta entra na familia como falha, nunca como ausencia silenciosa.
        por_familia[r['family']].append(bool(r.get(nome)) and r['gold'] == r[nome])
    familias_perfeitas = sum(1 for v in por_familia.values() if all(v))
    graves = sum(1 for r in resultados
                 if r.get(nome) and ((r['gold'] == 'cancelar') != (r[nome] == 'cancelar')))
    return {
        'casos_programados': programados, 'respostas_validas': len(pares),
        'cobertura': round(len(pares) / programados, 4) if programados else None,
        'n_casos': len(pares), 'acertos': acertos,
        'acuracia': round(acertos / len(pares), 4) if pares else None,
        'acuracia_sobre_programados': round(acertos / programados, 4) if programados else None,
        'macro_f1': round(macro_f1(pares), 4),
        'n_familias': len(por_familia), 'familias_sem_erro': familias_perfeitas,
        'ic95_familias': [round(x, 4) for x in wilson(familias_perfeitas, len(por_familia))],
        'erros_graves_cancelar': graves,
        'erros': [{'case_id': r['case_id'], 'family': r['family'], 'kind': r['kind'],
                   'gold': r['gold'], 'pred': r[nome], 'text': r['text']}
                  for r in resultados if r.get(nome) and r[nome] != r['gold']],
        'sem_resposta': [r['case_id'] for r in resultados if not r.get(nome)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Chama o Jev de verdade.')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    casos = carregar()
    resultados = [dict(c) for c in casos]

    for r in resultados:
        r['regra'] = classificar(r['text'])
    print(f"Regra simples: {resumo('regra', resultados)['acertos']}/{len(resultados)}")

    if args.execute:
        key, _ = load_api_key()
        with Ledger(DB, EXPERIMENT) as ledger:
            ledger.authorize(usd_to_nusd('5.00'),
                             hypothesis='Jev supera regra simples na triagem em portugues',
                             metric='acuracia pareada por caso')
            ledger.set_block_cap(BLOCK, usd_to_nusd('0.25'))
            ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
            for r in resultados:
                caminho = f"runs/e1-triagem/{r['case_id']}.json"
                inicio = time.monotonic()
                saida = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                                 state=r['text'],
                                 questions={'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                                     'criteria': CRITERIOS}},
                                 request_path=caminho, runtime_manifest_path=caminho, api_key=key)
                resposta = (saida.get('answers') or {}).get('acao') or {}
                r['jev'] = resposta.get('choice')
                r['jev_confidence'] = resposta.get('confidence')
                r['jev_probabilities'] = resposta.get('probabilities')
                r['jev_status'] = saida['status']
                r['jev_attempt_id'] = saida['attempt_id']
                r['jev_cost_nusd'] = saida.get('settled_nusd')
                r['latency_ms'] = round((time.monotonic() - inicio) * 1000, 1)
                marca = 'ok ' if r['jev'] == r['gold'] else 'ERRO'
                print(f"  {r['case_id']}: {marca} gold={r['gold']} jev={r['jev']} "
                      f"conf={r['jev_confidence']} {r['latency_ms']}ms")
            comprometido = ledger.committed_nusd()
            disponivel = ledger.available_nusd()

        relatorio = {'at': datetime.now(timezone.utc).isoformat(),
                     'preregistro': 'planning/preregistro-E1-triagem.md',
                     'corpus': str(CORPUS.relative_to(ROOT)), 'modelo': MODEL,
                     'regra': resumo('regra', resultados), 'jev': resumo('jev', resultados),
                     'ledger_committed_nusd': comprometido, 'available_nusd': disponivel,
                     'casos': resultados}
        (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                            encoding='utf-8')
        r_regra, r_jev = relatorio['regra'], relatorio['jev']
        print(f"\n{'':10} {'acuracia':>9} {'macroF1':>8} {'fam. sem erro':>14} {'graves':>7}")
        for nome, d in (('regra', r_regra), ('jev', r_jev)):
            print(f"{nome:10} {d['acuracia']:>9} {d['macro_f1']:>8} "
                  f"{str(d['familias_sem_erro']) + '/' + str(d['n_familias']):>14} "
                  f"{d['erros_graves_cancelar']:>7}")
        diferenca = (r_jev['acuracia'] or 0) - (r_regra['acuracia'] or 0)
        print(f"\nDiferenca pareada Jev - regra: {diferenca:+.4f}")
        print(f"Custo do bloco: {comprometido / 1e9:.9f} USD | disponivel: {disponivel / 1e9:.6f} USD")
        print(f"Relatorio em {(OUT / 'relatorio.json').relative_to(ROOT)}")


if __name__ == '__main__':
    main()
