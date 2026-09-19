"""E10b: o mesmo comparador econômico nas 10 famílias do piloto, para dobrar o poder.

Análise **secundária e declarada**, sob a Emenda 1 do pré-registro do E10, escrita antes desta
execução. O resultado primário continua sendo o da partição de confirmação.

O viés deste braço é conhecido e vai no sentido contrário da conclusão nova: o piloto guiou o
desenho do prompt do Jev, e o comparador recebe esse mesmo prompt sem nunca ter visto aqueles
casos. Se mesmo assim o intervalo continuar contendo zero, a leitura de ausência de evidência
sai mais forte, não mais fraca.

Uso:
    python -m executor.run_e10b_piloto
    python -m executor.run_e10b_piloto --execute
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .analise import bootstrap_cluster
from .pricing import load_prices, worst_case_nusd
from .run_e1_triagem import resumo
from .run_e10_llm_economico import (BLOCK, MODEL, PROVIDER, executar, reservation_output_tokens,
                                    reservation_tokens)
from .runner import load_api_key

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-piloto.jsonl'
OUT = ROOT / 'runs' / 'e10b-piloto'
E10 = ROOT / 'runs' / 'e10-llm-economico' / 'relatorio.json'
E1 = ROOT / 'runs' / 'e1-triagem' / 'relatorio.json'


def carregar():
    return [json.loads(linha) for linha in CORPUS.read_text(encoding='utf-8').splitlines()
            if linha.strip()]


def pareamento(casos):
    clusters = {}
    for caso in casos:
        clusters.setdefault(caso['family'], []).append(
            (1 if caso.get('jev') == caso['gold'] else 0,
             1 if caso.get('llm') == caso['gold'] else 0))
    return clusters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    casos = carregar()
    precos = load_prices()
    entrada = reservation_tokens(precos, PROVIDER, MODEL)
    saida = reservation_output_tokens(precos, PROVIDER, MODEL)
    pior = worst_case_nusd(precos, PROVIDER, MODEL, entrada, saida)

    if not args.execute:
        print('%d chamadas a %s no corpus piloto.' % (len(casos), MODEL))
        print('US$ %.9f no pior caso. Nada enviado.' % (pior * len(casos) / 1e9))
        return

    # O bloco e o mesmo do E10: e o mesmo experimento, com o teto ja autorizado.
    OUT.mkdir(parents=True, exist_ok=True)
    comprometido, _ = executar(casos, load_api_key()[0], precos)

    e1 = json.loads(E1.read_text(encoding='utf-8'))
    do_jev = {c['case_id']: c['jev'] for c in e1['casos']}
    for caso in casos:
        caso['jev'] = do_jev.get(caso['case_id'])

    e10 = json.loads(E10.read_text(encoding='utf-8'))
    juntos = e10['casos'] + casos

    d_llm, d_jev = resumo('llm', casos), resumo('jev', casos)
    par_piloto = bootstrap_cluster(pareamento(casos))
    par_juntos = bootstrap_cluster(pareamento(juntos))
    so_jev = [c['case_id'] for c in juntos
              if c.get('jev') == c['gold'] and c.get('llm') != c['gold']]
    so_llm = [c['case_id'] for c in juntos
              if c.get('llm') == c['gold'] and c.get('jev') != c['gold']]
    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(),
        'modelo': MODEL, 'bloco': BLOCK,
        'preregistro': 'planning/preregistro-E10-llm-economico.md (Emenda 1)',
        'natureza': ('analise SECUNDARIA: o resultado primario e o da particao de confirmacao. '
                     'O piloto guiou o desenho do prompt do Jev, entao o vies favorece o Jev.'),
        'corpus': str(CORPUS.relative_to(ROOT)),
        'llm_no_piloto': d_llm, 'jev_no_piloto': d_jev,
        'pareada_piloto': par_piloto,
        'pareada_80_casos': par_juntos,
        'so_jev_acerta_nos_80': so_jev, 'so_llm_acerta_nos_80': so_llm,
        'respostas_invalidas': [c['case_id'] for c in casos if c.get('llm') is None],
        'casos': casos,
        'wallet_committed_nusd': comprometido,
    }
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print('\nNo piloto: LLM %d/%d (%.4f) | Jev %d/%d (%.4f)'
          % (d_llm['acertos'], d_llm['casos_programados'],
             d_llm['acuracia_sobre_programados'], d_jev['acertos'],
             d_jev['casos_programados'], d_jev['acuracia_sobre_programados']))
    print('Pareada no piloto  %+.4f, IC95 [%.4f; %.4f] sobre %d familias'
          % (par_piloto['diferenca_observada'], par_piloto['ic95'][0], par_piloto['ic95'][1],
             par_piloto['n_familias']))
    print('Pareada nos 80     %+.4f, IC95 [%.4f; %.4f] sobre %d familias  <- SECUNDARIA'
          % (par_juntos['diferenca_observada'], par_juntos['ic95'][0], par_juntos['ic95'][1],
             par_juntos['n_familias']))
    print('So o Jev acerta: %d | so o LLM: %d' % (len(so_jev), len(so_llm)))
    print('Carteira: %.9f USD' % (comprometido / 1e9))


if __name__ == '__main__':
    main()
