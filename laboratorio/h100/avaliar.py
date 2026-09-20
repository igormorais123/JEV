"""Roda as cem provas, guarda o veredito e devolve o placar.

    python -m laboratorio.h100.avaliar          # roda e imprime
    python -m laboratorio.h100.avaliar --salvar # e grava laboratorio/h100-resultados.json

Uma prova que levanta exceção não vira `falsificada`: vira `erro`. A diferença importa, porque
falsificar uma hipótese é um resultado e quebrar o avaliador é um defeito, e confundir os dois
produziria a pior espécie de achado — o que nasce de um bug e é publicado como descoberta.
"""

from __future__ import annotations

import collections
import json
import sys
import traceback
from pathlib import Path

from laboratorio.h100 import provas, registro

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = RAIZ / 'laboratorio' / 'h100-resultados.json'


def rodar():
    resultados = []
    for hipotese in registro.HIPOTESES:
        funcao = provas.PROVAS.get(hipotese['id'])
        if funcao is None:
            resultados.append({**hipotese, 'veredito': 'sem prova',
                               'medido': None,
                               'detalhe': 'a medição desta hipótese ainda não foi feita'})
            continue
        try:
            saida = funcao()
        except Exception as erro:  # noqa: BLE001 — o erro é o resultado que interessa aqui
            saida = {'veredito': 'erro', 'medido': None,
                     'detalhe': f'{type(erro).__name__}: {erro}',
                     'traco': traceback.format_exc(limit=3)}
        resultados.append({**hipotese, **saida})
    return resultados


def placar(resultados):
    return collections.Counter(r['veredito'] for r in resultados)


def por_familia(resultados):
    agrupado = collections.defaultdict(collections.Counter)
    for r in resultados:
        agrupado[r['familia']][r['veredito']] += 1
    return agrupado


def main():
    resultados = rodar()
    conta = placar(resultados)
    for r in resultados:
        marca = {'sustentada': 'ok    ', 'falsificada': 'FALSA ',
                 'inconclusiva': 'incon.', 'erro': 'ERRO  ', 'sem prova': '  --  '}[r['veredito']]
        medido = '' if r['medido'] is None else f'  [{r["medido"]}]'
        print(f'{marca} {r["id"]} {r["familia"]} {r["enunciado"][:72]}{medido}')
        if r['veredito'] in ('erro',):
            print(f'         {r["detalhe"]}')
    print()
    for familia, nome in registro.FAMILIAS.items():
        c = por_familia(resultados)[familia]
        print(f'  {familia} {nome:<48} ' + ' '.join(f'{k}={v}' for k, v in sorted(c.items())))
    print('\n' + ' '.join(f'{k}={v}' for k, v in sorted(conta.items())))

    if '--salvar' in sys.argv:
        DESTINO.write_text(json.dumps(
            {'total': len(resultados), 'placar': dict(conta),
             'resultados': [{k: v for k, v in r.items() if k != 'traco'} for r in resultados]},
            ensure_ascii=False, indent=1), encoding='utf-8')
        print(f'\nresultados em {DESTINO}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
