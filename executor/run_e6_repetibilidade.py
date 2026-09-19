"""E6: o mesmo caso, sozinho, repetido. Separa instabilidade do modelo de efeito do lote.

O E2b achou 3 casos que mudam de resposta conforme os vizinhos do lote. Ficou uma pergunta
aberta: eles são instáveis por causa do lote, ou o modelo já responde diferente ao mesmo caso
isolado? Aqui cada caso vai sozinho, uma pergunta por chamada, repetido N vezes. Se um caso
oscilar também assim, a causa não é o lote.

Uso:
    python -m executor.run_e6_repetibilidade              # só a conta, sem gasto
    python -m executor.run_e6_repetibilidade --execute
"""
import argparse
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger
from .pricing import load_prices, usd_to_nusd, worst_case_nusd
from .run_e1_triagem import CRITERIOS, INSTRUCOES, carregar
from .runner import dispatch, load_api_key, reservation_output_tokens, reservation_tokens

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'e6-repetibilidade'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e6-repetibilidade'
BLOCK = 'e6-repetibilidade'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-e6-jev'


def entropia(contagem, total):
    """Entropia de Shannon em bits. Zero quer dizer sempre a mesma resposta."""
    import math
    return round(-sum((n / total) * math.log2(n / total) for n in contagem.values() if n), 4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--repeticoes', type=int, default=5)
    parser.add_argument('--casos', type=int, default=40)
    args = parser.parse_args()
    casos = carregar()[:args.casos]
    chamadas = len(casos) * args.repeticoes

    precos = load_prices()
    tokens = reservation_tokens(precos, PROVIDER, MODEL)
    saida_max = reservation_output_tokens(precos, PROVIDER, MODEL)
    pior = worst_case_nusd(precos, PROVIDER, MODEL, tokens, saida_max)
    if not args.execute:
        print(f'{len(casos)} casos x {args.repeticoes} repeticoes = {chamadas} chamadas individuais.')
        print(f'Pior caso reservado: {chamadas * pior / 1e9:.6f} USD. Nada enviado.')
        return

    OUT.mkdir(parents=True, exist_ok=True)
    key = load_api_key()[0]
    observacoes = []
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='O mesmo caso isolado recebe sempre a mesma decisao',
                         metric='proporcao de casos com resposta unica nas repeticoes')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.50'))
        ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
        for repeticao in range(1, args.repeticoes + 1):
            # Repeticao por rodada, nao caso a caso: assim uma deriva do servico ao longo do
            # tempo aparece como diferenca ENTRE rodadas, e nao some dentro de um caso so.
            for caso in casos:
                caminho = f"runs/e6-repetibilidade/r{repeticao}-{caso['case_id']}.json"
                marcador = time.monotonic()
                saida = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                                 state=caso['text'],
                                 questions={'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                                     'criteria': CRITERIOS}},
                                 request_path=caminho, runtime_manifest_path=caminho, api_key=key)
                resposta = (saida.get('answers') or {}).get('acao') or {}
                observacoes.append({
                    'repeticao': repeticao, 'case_id': caso['case_id'], 'family': caso['family'],
                    'gold': caso['gold'], 'pred': resposta.get('choice'),
                    'confidence': resposta.get('confidence'), 'status': saida['status'],
                    'attempt_id': saida['attempt_id'], 'cost_nusd': saida.get('settled_nusd'),
                    'latency_ms': round((time.monotonic() - marcador) * 1000, 1),
                })
            acertos = sum(1 for o in observacoes if o['repeticao'] == repeticao and o['pred'] == o['gold'])
            print(f'  rodada {repeticao}: {acertos}/{len(casos)} acertos', flush=True)
        comprometido = ledger.wallet_committed_nusd()
        disponivel = ledger.wallet_available_nusd()

    por_caso = {}
    for caso in casos:
        respostas = [o['pred'] for o in observacoes if o['case_id'] == caso['case_id']]
        contagem = Counter(r for r in respostas if r)
        acertos = sum(1 for r in respostas if r == caso['gold'])
        por_caso[caso['case_id']] = {
            'family': caso['family'], 'gold': caso['gold'],
            'respostas': dict(contagem), 'distintas': len(contagem),
            'acertos': acertos, 'repeticoes': len(respostas),
            'entropia_bits': entropia(contagem, sum(contagem.values())) if contagem else None,
            'majoritaria': contagem.most_common(1)[0][0] if contagem else None,
        }
    instaveis = [c for c, d in por_caso.items() if d['distintas'] > 1]
    por_rodada = {r: sum(1 for o in observacoes if o['repeticao'] == r and o['pred'] == o['gold'])
                  for r in range(1, args.repeticoes + 1)}
    # Voto majoritario: a acuracia que teriamos pagando N chamadas em vez de uma.
    majoritaria = sum(1 for c, d in por_caso.items() if d['majoritaria'] == d['gold'])
    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(), 'modelo': MODEL,
        'repeticoes': args.repeticoes, 'casos': len(casos),
        'formato': 'individual, uma pergunta por chamada',
        'casos_instaveis': instaveis, 'n_instaveis': len(instaveis),
        'acuracia_por_rodada': {str(r): round(a / len(casos), 4) for r, a in por_rodada.items()},
        'acertos_por_rodada': {str(r): a for r, a in por_rodada.items()},
        'acuracia_voto_majoritario': round(majoritaria / len(casos), 4),
        'por_caso': por_caso, 'observacoes': observacoes,
        'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel,
    }
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print(f"\nCasos com mais de uma resposta em {args.repeticoes} repeticoes individuais: "
          f"{len(instaveis)} de {len(casos)}")
    for c in instaveis:
        print(f"  {c}: {por_caso[c]['respostas']} (gold {por_caso[c]['gold']})")
    print(f"Acuracia por rodada: {relatorio['acuracia_por_rodada']}")
    print(f"Acuracia com voto majoritario de {args.repeticoes}: "
          f"{relatorio['acuracia_voto_majoritario']}")
    print(f"Carteira: {comprometido / 1e9:.9f} USD comprometidos | {disponivel / 1e9:.6f} disponiveis")


if __name__ == '__main__':
    main()
