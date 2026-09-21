"""R45 — a lista lida nas duas ordens.

De onde vem. A R43 pôs o alvo em primeiro em 88,8% com 32 trechos numa chamada, mas com o alvo
na segunda metade da lista o acerto cai (85% contra 92%; com 16 trechos, 83% contra 100%). Há
viés de posição em lista longa. A salvaguarda barata é ler a mesma lista na ordem inversa e só
aceitar sem conferência quando as duas leituras escolhem o mesmo trecho.

H45a  As duas ordens concordam em 75% ou mais dos 80 casos, e entre os concordantes o alvo está
      em primeiro em 97% ou mais.
H45b  O alvo está entre as duas escolhas (uma de cada ordem) em 95% ou mais dos casos.
Falsifica: acerto entre concordantes abaixo de 93% — concordar não basta como sinal.

    python laboratorio/r45_lista_nas_duas_ordens.py --rodar
"""

import argparse
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import em_paralelo  # noqa: E402
from laboratorio.r31_r37_segunda_leva import gravar, medidas, taxa  # noqa: E402
from laboratorio.r42_r44_quarta_leva import SEMENTE, lista, perguntas_de_codigo  # noqa: E402


def main():
    analise = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analise.add_argument('--rodar', action='store_true')
    if not analise.parse_args().rodar:
        return
    itens, todas = perguntas_de_codigo()
    sorteio = random.Random(SEMENTE)  # a mesma semente e o mesmo sorteio da R43: os mesmos 80 casos de 32
    sorteio.shuffle(itens)
    chaves = sorted(todas)
    tarefas = []
    for n, item in enumerate(itens[:80]):
        for tamanho in (16, 32):
            extras = [c for c in sorteio.sample(chaves, tamanho + 8) if c != item['alvo'] and c not in item['distratores']]
            candidatos = [item['alvo']] + item['distratores'] + extras[:tamanho - 1 - len(item['distratores'])]
            sorteio.shuffle(candidatos)
            if tamanho == 32:
                pares = [(c, todas[c][:2500]) for c in candidatos]
                tarefas.append({'caso': n, 'ordem': 'direta', 'pergunta': item['pergunta'], 'alvo': item['alvo'], 'candidatos': pares})
                tarefas.append({'caso': n, 'ordem': 'inversa', 'pergunta': item['pergunta'], 'alvo': item['alvo'], 'candidatos': pares[::-1]})

    def uma(t):
        topo, confianca, _, _, detalhe = lista(t['pergunta'], t['candidatos'], 'R45')
        return {'caso': t['caso'], 'ordem': t['ordem'], 'alvo': t['alvo'], 'topo': topo, 'confianca': confianca, **medidas(detalhe)}

    def analisar(linhas):
        por = {}
        for l in linhas:
            if l['topo']:
                por.setdefault(l['caso'], {})[l['ordem']] = l
        completos = [v for v in por.values() if len(v) == 2]
        concordam = [v for v in completos if v['direta']['topo'] == v['inversa']['topo']]
        return {'casos': len(completos),
                'direta': taxa(sum(v['direta']['topo'] == v['direta']['alvo'] for v in completos), len(completos)),
                'inversa': taxa(sum(v['inversa']['topo'] == v['inversa']['alvo'] for v in completos), len(completos)),
                'concordam': len(concordam),
                'acerto_entre_concordantes': taxa(sum(v['direta']['topo'] == v['direta']['alvo'] for v in concordam), len(concordam)),
                'alvo_entre_as_duas_escolhas': taxa(sum(v['direta']['alvo'] in (v['direta']['topo'], v['inversa']['topo']) for v in completos), len(completos))}

    gravar('r45-lista-nas-duas-ordens', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R45'), analisar)


if __name__ == '__main__':
    main()
