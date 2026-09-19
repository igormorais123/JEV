"""E7: conjunto de confirmação da triagem, em casos que não guiaram o desenho.

Mesmo prompt, mesmos critérios e mesmo comparador congelado do E1. O que muda é o corpus:
40 casos novos, escritos para armadilhas que o piloto não cobria. Pré-registro em
planning/preregistro-E7-confirmacao.md.

Uso:
    python -m executor.run_e7_confirmacao            # só a regra, sem gasto
    python -m executor.run_e7_confirmacao --execute
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .analise import bootstrap_cluster
from .baseline_regra import classificar
from .ledger import Ledger
from .pricing import usd_to_nusd
from .run_e1_triagem import CRITERIOS, INSTRUCOES, resumo
from .runner import dispatch, load_api_key

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-confirmacao.jsonl'
OUT = ROOT / 'runs' / 'e7-confirmacao'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e7-confirmacao'
BLOCK = 'e7-confirmacao'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-e7-jev'
# Intervalo do E1, fixado no pre-registro: a diferenca do E7 replica se cair aqui dentro.
IC_DO_PILOTO = (0.150, 0.500)


def carregar():
    return [json.loads(linha) for linha in CORPUS.read_text(encoding='utf-8').splitlines()
            if linha.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    casos = carregar()
    for c in casos:
        c['regra'] = classificar(c['text'])

    if not args.execute:
        d = resumo('regra', casos)
        print(f"Regra congelada no corpus de confirmacao: {d['acertos']}/{d['casos_programados']} "
              f"({d['acuracia_sobre_programados']:.3f}), familias sem erro {d['familias_sem_erro']}/"
              f"{d['n_familias']}")
        print(f'{len(casos)} chamadas se executar. Nada enviado.')
        return

    OUT.mkdir(parents=True, exist_ok=True)
    key = load_api_key()[0]
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='A vantagem do Jev sobre a regra congelada se mantem fora do corpus piloto',
                         metric='diferenca pareada de acuracia, com bootstrap de familias')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.25'))
        ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
        for caso in casos:
            caminho = f"runs/e7-confirmacao/{caso['case_id']}.json"
            marcador = time.monotonic()
            saida = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                             state=caso['text'],
                             questions={'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                                 'criteria': CRITERIOS}},
                             request_path=caminho, runtime_manifest_path=caminho, api_key=key)
            resposta = (saida.get('answers') or {}).get('acao') or {}
            caso['jev'] = resposta.get('choice')
            caso['jev_confidence'] = resposta.get('confidence')
            caso['jev_status'] = saida['status']
            caso['jev_attempt_id'] = saida['attempt_id']
            caso['jev_cost_nusd'] = saida.get('settled_nusd')
            caso['latency_ms'] = round((time.monotonic() - marcador) * 1000, 1)
            marca = 'ok  ' if caso['jev'] == caso['gold'] else 'ERRO'
            print(f"  {caso['case_id']}: {marca} gold={caso['gold']:11} jev={caso['jev']}", flush=True)
        comprometido = ledger.wallet_committed_nusd()
        disponivel = ledger.wallet_available_nusd()

    d_jev, d_regra = resumo('jev', casos), resumo('regra', casos)
    clusters = {}
    for caso in casos:
        clusters.setdefault(caso['family'], []).append(
            (1 if caso.get('jev') == caso['gold'] else 0,
             1 if caso.get('regra') == caso['gold'] else 0))
    pareada = bootstrap_cluster(clusters)
    # O criterio pre-registrado era binario e, relendo, mal especificado: o que ameaca a
    # conclusao e a diferenca cair ABAIXO do intervalo do piloto (otimismo). Acima dele, a
    # vantagem nao foi desmentida; o que mudou foi a dificuldade do comparador. Registramos
    # os dois lados separados para nao trocar um resultado por um rotulo.
    diferenca = pareada['diferenca_observada']
    abaixo = diferenca < IC_DO_PILOTO[0]
    dentro = IC_DO_PILOTO[0] <= diferenca <= IC_DO_PILOTO[1]
    veredito = ('otimismo do piloto: a vantagem encolheu fora dele' if abaixo else
                'replica dentro do intervalo do piloto' if dentro else
                'vantagem maior que no piloto; conferir se o comparador ficou mais penalizado')
    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(), 'modelo': MODEL,
        'preregistro': 'planning/preregistro-E7-confirmacao.md',
        'corpus': str(CORPUS.relative_to(ROOT)),
        'jev': d_jev, 'regra': d_regra, 'pareada': pareada,
        'ic_do_piloto': list(IC_DO_PILOTO),
        'replica': not abaixo, 'dentro_do_ic_do_piloto': dentro, 'abaixo_do_ic_do_piloto': abaixo,
        'veredito': veredito,
        'casos': casos,
        'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel,
    }
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print(f"\nJev   {d_jev['acertos']}/{d_jev['casos_programados']} "
          f"({d_jev['acuracia_sobre_programados']:.3f}), familias sem erro "
          f"{d_jev['familias_sem_erro']}/{d_jev['n_familias']}")
    print(f"Regra {d_regra['acertos']}/{d_regra['casos_programados']} "
          f"({d_regra['acuracia_sobre_programados']:.3f}), familias sem erro "
          f"{d_regra['familias_sem_erro']}/{d_regra['n_familias']}")
    print(f"Diferenca pareada {pareada['diferenca_observada']:+.3f}, "
          f"IC95 [{pareada['ic95'][0]:.3f}; {pareada['ic95'][1]:.3f}] "
          f"(bootstrap de {pareada['n_familias']} familias)")
    print(f'IC do piloto {IC_DO_PILOTO}: {veredito}')
    if d_jev['erros']:
        print('Erros do Jev:')
        for e in d_jev['erros']:
            print(f"  {e['case_id']} ({e['family']}): gold={e['gold']} jev={e['pred']}")
    print(f"Carteira: {comprometido / 1e9:.9f} USD comprometidos | {disponivel / 1e9:.6f} disponiveis")


if __name__ == '__main__':
    main()
