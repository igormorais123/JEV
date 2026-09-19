"""Roteia a amostra de pedidos reais com o Jev e compara com os gabaritos.

O gabarito do autor está fechado antes desta execução. O do anotador local (qwen2.5:7b via
Ollama, custo zero) é produzido por `anotador_local.py` e entra aqui se existir — é ele que
diz se a vantagem sobrevive a um critério que não é o desta casa.

    python avaliacao/rodar.py            # roteia e compara
    python avaliacao/rodar.py --so-comparar
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from jev_router import politica, roteador  # noqa: E402

AMOSTRA = RAIZ / 'avaliacao' / 'amostra.json'
RESPOSTAS = RAIZ / 'avaliacao' / 'respostas-jev.json'
GABARITOS = {'autor': RAIZ / 'avaliacao' / 'gabarito-autor.json',
             'anotador local': RAIZ / 'avaliacao' / 'gabarito-anotador-local.json'}
RELATORIO = RAIZ / 'avaliacao' / 'relatorio.json'


def rodar():
    amostra = json.loads(AMOSTRA.read_text(encoding='utf-8'))['amostra']
    saida = []
    for caso in amostra:
        decisao = roteador.rotear(caso['pedido'], contexto=caso.get('projeto') or '',
                                  modo='avaliacao', usar_cache=False, origem='avaliacao')
        saida.append({'id': caso['id'], 'pedido': caso['pedido'][:300],
                      'decisao': decisao})
        marca = decisao['classe'] if decisao else 'SEM CLASSIFICAÇÃO'
        print(f"{caso['id']}: {marca}"
              + (f" ({decisao['confianca']:.3f}) risco={decisao['risco']}" if decisao else ''))
    RESPOSTAS.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding='utf-8')
    return saida


def carregar_gabaritos():
    saida = {}
    for nome, caminho in GABARITOS.items():
        if caminho.exists():
            saida[nome] = json.loads(caminho.read_text(encoding='utf-8'))['gabarito']
    return saida


def comparar(respostas, gabaritos):
    relatorio = {'casos': len(respostas), 'por_gabarito': {}}
    classificados = [r for r in respostas if r['decisao']]
    relatorio['classificados'] = len(classificados)

    for nome, gabarito in gabaritos.items():
        acertos_esforco = erros = 0
        confusao = Counter()
        rebaixa_indevido = []   # o Jev simplificou algo que o gabarito diz ser pesado
        eleva_a_mais = []
        risco_perdido = []      # gabarito diz irreversível e o Jev não viu
        acertos_risco = 0
        for r in classificados:
            esperado = gabarito.get(r['id'])
            if not esperado:
                continue
            d = r['decisao']
            obtido = d['classe'] if d['aplicada'] else d.get('classe_sugerida', d['classe'])
            # A comparação é com a classificação crua do Jev, não com o efeito da política:
            # a política é conservadora de propósito e mascararia o erro do modelo.
            cru = d.get('classe_sugerida') or d['classe']
            if cru == esperado['esforco']:
                acertos_esforco += 1
            else:
                erros += 1
                confusao[f"{esperado['esforco']} -> {cru}"] += 1
                if politica.ORDEM.index(cru) < politica.ORDEM.index(esperado['esforco']):
                    rebaixa_indevido.append({'id': r['id'], 'esperado': esperado['esforco'],
                                             'jev': cru, 'confianca': d.get('confianca'),
                                             'aplicada': d['aplicada']})
                else:
                    eleva_a_mais.append({'id': r['id'], 'esperado': esperado['esforco'], 'jev': cru})
            if d.get('risco') == esperado['risco']:
                acertos_risco += 1
            if esperado['risco'] == 'irreversivel' and d.get('risco') != 'irreversivel':
                risco_perdido.append({'id': r['id'], 'jev': d.get('risco')})

        total = acertos_esforco + erros
        # Rebaixamento indevido que a política DEIXOU passar é o único erro que faz estrago:
        # é o pedido difícil que perde subagente e raciocínio.
        estrago = [e for e in rebaixa_indevido if e['aplicada']]
        relatorio['por_gabarito'][nome] = {
            'casos_comparados': total,
            'acuracia_esforco': round(acertos_esforco / total, 4) if total else None,
            'acuracia_risco': round(acertos_risco / total, 4) if total else None,
            'confusoes': confusao.most_common(),
            'rebaixamento_indevido': rebaixa_indevido,
            'rebaixamento_indevido_aplicado': estrago,
            'elevacao_a_mais': eleva_a_mais,
            'irreversivel_nao_visto': risco_perdido,
        }
    return relatorio


def economia(respostas):
    """Quanto do trabalho o roteador tira do modelo caro, sob a política vigente."""
    aplicadas = [r['decisao'] for r in respostas if r['decisao'] and r['decisao']['aplicada']]
    sem_subagente = [d for d in aplicadas if not d['subagente']]
    return {
        'pedidos': len(respostas),
        'classificados': sum(1 for r in respostas if r['decisao']),
        'politica_aplicada': len(aplicadas),
        'roteados_para_modelo_barato': len(sem_subagente),
        'fracao_para_modelo_barato': round(len(sem_subagente) / len(respostas), 4),
        'distribuicao': Counter(
            r['decisao']['classe'] for r in respostas if r['decisao']).most_common(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--so-comparar', action='store_true')
    args = parser.parse_args()

    if args.so_comparar:
        respostas = json.loads(RESPOSTAS.read_text(encoding='utf-8'))
    else:
        respostas = rodar()

    relatorio = comparar(respostas, carregar_gabaritos())
    relatorio['economia'] = economia(respostas)
    RELATORIO.write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding='utf-8')

    print('')
    for nome, bloco in relatorio['por_gabarito'].items():
        print(f"== {nome}: esforço {bloco['acuracia_esforco']:.1%} | "
              f"risco {bloco['acuracia_risco']:.1%} | "
              f"rebaixou indevidamente {len(bloco['rebaixamento_indevido'])} "
              f"(a política deixou passar {len(bloco['rebaixamento_indevido_aplicado'])}) | "
              f"irreversível não visto: {len(bloco['irreversivel_nao_visto'])}")
        for c, n in bloco['confusoes'][:6]:
            print(f"     {c}: {n}")
    print('')
    print(json.dumps(relatorio['economia'], ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
