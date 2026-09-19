"""R0 — a confiança do Jev é uma probabilidade, ou apenas uma ordenação?

A seção 6.1 do relatório mostrou que o corte de 0,90 furou no E12. Corte e calibração são
coisas diferentes: um número pode ordenar perfeitamente (mais confiança, menos erro) e ainda
mentir sobre a probabilidade. Se ele ordena mas não calibra, toda política de corte tem de ser
ajustada por dado — e a recomendação do guia passa a ter um mecanismo, não só um susto.

Custo zero: os 230 casos já foram pagos nos experimentos E1, E7, E11 e E12.

    python laboratorio/r0_calibracao.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor import gabarito  # noqa: E402
from laboratorio.nucleo import wilson  # noqa: E402

CORPORA = {'E1 piloto': 'runs/e1-triagem/relatorio.json',
           'E7 confirmação': 'runs/e7-confirmacao/relatorio.json',
           'E11 desempate': 'runs/e11-desempate/relatorio.json',
           'E12 replicação': 'runs/e12-replicacao/relatorio.json'}
DESTINO = RAIZ / 'laboratorio' / 'r0-calibracao.json'

FAIXAS = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 0.95), (0.95, 0.99), (0.99, 1.01)]


def casos():
    saida = []
    for nome, caminho in CORPORA.items():
        arquivo = RAIZ / caminho
        if not arquivo.exists():
            continue
        for caso in json.loads(arquivo.read_text(encoding='utf-8'))['casos']:
            if caso.get('jev_confidence') is None or caso.get('jev') is None:
                continue
            saida.append({'origem': nome, 'case_id': caso['case_id'], 'family': caso['family'],
                          'gold': caso['gold'], 'jev': caso['jev'],
                          'confianca': caso['jev_confidence']})
    return saida


def gabaritos_disponiveis(todos):
    """Os três critérios de correção do estudo, para que o achado não dependa de um só."""
    oficial, _ = gabarito.adjudicado()
    mapas = {'autor': {k: v['gold'] for k, v in gabarito.do_autor().items()},
             'anotador local': gabarito.do_anotador_local(),
             'oficial': {k: v['gold'] for k, v in oficial.items()}}
    return {nome: mapa for nome, mapa in mapas.items() if mapa}


def calibrar(casos_com_acerto):
    """Curva em faixas, ECE e separação."""
    faixas = []
    ece = 0.0
    total = len(casos_com_acerto)
    for baixo, alto in FAIXAS:
        dentro = [c for c in casos_com_acerto if baixo <= c['confianca'] < alto]
        if not dentro:
            continue
        acertos = sum(c['acertou'] for c in dentro)
        media_declarada = sum(c['confianca'] for c in dentro) / len(dentro)
        taxa = acertos / len(dentro)
        ece += len(dentro) / total * abs(taxa - media_declarada)
        faixas.append({'faixa': f'[{baixo:.2f}, {alto:.2f})', 'n': len(dentro),
                       'confianca_media': round(media_declarada, 4),
                       'acerto_observado': round(taxa, 4),
                       'desvio': round(taxa - media_declarada, 4),
                       'ic95_do_acerto': wilson(acertos, len(dentro))})

    acertos = [c['confianca'] for c in casos_com_acerto if c['acertou']]
    erros = [c['confianca'] for c in casos_com_acerto if not c['acertou']]
    # Probabilidade de um acerto sorteado ter confiança maior que a de um erro sorteado:
    # é a separação, e mede ordenação, que é coisa distinta de calibração.
    if acertos and erros:
        pares = sum(1 for a in acertos for e in erros if a > e)
        empates = sum(1 for a in acertos for e in erros if a == e)
        separacao = (pares + 0.5 * empates) / (len(acertos) * len(erros))
    else:
        separacao = None

    return {'n': total, 'ece': round(ece, 4), 'faixas': faixas,
            'confianca_media_dos_acertos': round(sum(acertos) / len(acertos), 4) if acertos else None,
            'confianca_media_dos_erros': round(sum(erros) / len(erros), 4) if erros else None,
            'separacao': round(separacao, 4) if separacao is not None else None,
            'erros': len(erros)}


def main():
    todos = casos()
    mapas = gabaritos_disponiveis(todos)
    resultado = {'casos': len(todos), 'por_gabarito': {}, 'por_corpus': {}}

    for nome, mapa in mapas.items():
        marcados = [{**c, 'acertou': c['jev'] == mapa.get(c['case_id'], c['gold'])}
                    for c in todos]
        resultado['por_gabarito'][nome] = calibrar(marcados)

    oficial = mapas.get('oficial') or mapas['autor']
    marcados = [{**c, 'acertou': c['jev'] == oficial.get(c['case_id'], c['gold'])} for c in todos]
    por_corpus = defaultdict(list)
    for caso in marcados:
        por_corpus[caso['origem']].append(caso)
    for nome, grupo in por_corpus.items():
        resultado['por_corpus'][nome] = calibrar(grupo)

    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')

    print(f"R0 — calibração em {resultado['casos']} casos já pagos\n")
    for nome, bloco in resultado['por_gabarito'].items():
        print(f"== gabarito {nome}: ECE {bloco['ece']:.4f} | separação {bloco['separacao']} | "
              f"{bloco['erros']} erros")
        print(f"   confiança média: acertos {bloco['confianca_media_dos_acertos']} | "
              f"erros {bloco['confianca_media_dos_erros']}")
        for faixa in bloco['faixas']:
            print(f"   {faixa['faixa']} n={faixa['n']:3d} declarou {faixa['confianca_media']:.3f} "
                  f"acertou {faixa['acerto_observado']:.3f} "
                  f"desvio {faixa['desvio']:+.3f}")
        print('')

    print('== por corpus, sob o gabarito oficial')
    for nome, bloco in resultado['por_corpus'].items():
        print(f"   {nome:16} ECE {bloco['ece']:.4f} | separação {bloco['separacao']} | "
              f"{bloco['erros']} erros em {bloco['n']}")


if __name__ == '__main__':
    main()
