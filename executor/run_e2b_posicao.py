"""E2b: desconfunde posição no lote e identidade do caso.

No E2 a ordem dos casos dentro do lote era fixa, então "posição 4 erra mais" e "o caso que
cai na posição 4 é difícil" eram a mesma coisa. Aqui cada caso passa por posições diferentes
em permutações distintas, com sementes registradas, e aí a posição vira estimável.

Uso:
    python -m executor.run_e2b_posicao --execute
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
from .run_e1_triagem import CRITERIOS, INSTRUCOES, carregar
from .runner import dispatch, load_api_key

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'e2b-posicao'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e2b-posicao'
BLOCK = 'e2b-posicao'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-e2b-jev'
TAMANHO_LOTE = 8
SEMENTES = [20260918, 20260919, 20260920, 20260921, 20260922]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    casos = carregar()
    if not args.execute:
        print(f'{len(SEMENTES)} permutacoes x {len(casos) // TAMANHO_LOTE} lotes = '
              f'{len(SEMENTES) * len(casos) // TAMANHO_LOTE} chamadas; nada enviado.')
        return

    OUT.mkdir(parents=True, exist_ok=True)
    key, _ = load_api_key()
    observacoes = []
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='A posicao dentro do lote afeta a decisao',
                         metric='acuracia por posicao, com caso desconfundido')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.10'))
        ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
        for semente in SEMENTES:
            embaralhados = list(casos)
            random.Random(semente).shuffle(embaralhados)
            for inicio in range(0, len(embaralhados), TAMANHO_LOTE):
                grupo = embaralhados[inicio:inicio + TAMANHO_LOTE]
                estado = '\n'.join(f"Mensagem {i + 1}: {c['text']}" for i, c in enumerate(grupo))
                perguntas = {f'acao_{i + 1}': {
                    'type': 'choice',
                    'instructions': f'{INSTRUCOES} Responda apenas sobre a Mensagem {i + 1}.',
                    'criteria': CRITERIOS} for i in range(len(grupo))}
                caminho = f'runs/e2b-posicao/{semente}-{inicio // TAMANHO_LOTE + 1}.json'
                marcador = time.monotonic()
                saida = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                                 state=estado, questions=perguntas, request_path=caminho,
                                 runtime_manifest_path=caminho, api_key=key)
                elapsed = round((time.monotonic() - marcador) * 1000, 1)
                respostas = saida.get('answers') or {}
                for i, caso in enumerate(grupo):
                    resposta = respostas.get(f'acao_{i + 1}') or {}
                    observacoes.append({
                        'semente': semente, 'lote': inicio // TAMANHO_LOTE + 1, 'posicao': i + 1,
                        'case_id': caso['case_id'], 'family': caso['family'], 'gold': caso['gold'],
                        'pred': resposta.get('choice'), 'confidence': resposta.get('confidence'),
                        'acerto': resposta.get('choice') == caso['gold'],
                        'attempt_id': saida['attempt_id'], 'latency_chamada_ms': elapsed,
                        'cost_nusd': (saida.get('settled_nusd') or 0) / len(grupo)})
                print(f'  semente {semente} lote {inicio // TAMANHO_LOTE + 1}: {saida["status"]} '
                      f'{elapsed:.0f} ms', flush=True)
        comprometido = ledger.wallet_committed_nusd()
        disponivel = ledger.wallet_available_nusd()

    por_posicao = defaultdict(lambda: [0, 0])
    for o in observacoes:
        por_posicao[o['posicao']][0] += o['acerto']
        por_posicao[o['posicao']][1] += 1
    por_caso = defaultdict(lambda: [0, 0])
    for o in observacoes:
        por_caso[o['case_id']][0] += o['acerto']
        por_caso[o['case_id']][1] += 1

    relatorio = {'at': datetime.now(timezone.utc).isoformat(), 'sementes': SEMENTES,
                 'tamanho_lote': TAMANHO_LOTE, 'observacoes': observacoes,
                 'por_posicao': {str(k): v for k, v in sorted(por_posicao.items())},
                 'por_caso': {k: v for k, v in sorted(por_caso.items())},
                 'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel}
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')

    print(f'\n{len(observacoes)} observacoes, cada caso em varias posicoes.')
    print('\nAcuracia por posicao no lote:')
    for posicao, (acertos, total) in sorted(por_posicao.items()):
        print(f'  posicao {posicao}: {acertos}/{total} = {acertos / total:.3f}')
    instaveis = {c: v for c, v in por_caso.items() if 0 < v[0] < v[1]}
    print(f'\nCasos sempre certos: {sum(1 for v in por_caso.values() if v[0] == v[1])}/{len(por_caso)}')
    print(f'Casos sempre errados: {sum(1 for v in por_caso.values() if v[0] == 0)}/{len(por_caso)}')
    for caso, (acertos, total) in sorted(instaveis.items(), key=lambda kv: kv[1][0] / kv[1][1]):
        print(f'  instavel {caso}: {acertos}/{total}')
    print(f'\nCarteira: comprometido {comprometido / 1e9:.9f} USD | '
          f'disponivel {disponivel / 1e9:.6f} USD')


if __name__ == '__main__':
    main()
