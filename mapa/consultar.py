"""Pergunta ao grafo do repositório, sem abrir os arquivos: o que é, onde está, com que se liga.

    python mapa/consultar.py TERMO                    busca e mostra o nó (arquivo, conceito ou função)
    python mapa/consultar.py --caminho A B            o caminho mais curto entre dois nós, com o tipo de cada ligação
    python mapa/consultar.py --vizinhos X [--profundidade 2] [--tipo apoia-se-em]

TERMO pode ser um id exato (`H012`, `R17`, `executor/ledger.py`, `executor/ledger.py::Ledger`), o nome de
uma função (`Ledger`, `usd_to_nusd`) ou palavras soltas, que casam com id, título e descrição.
Lê só `mapa/grafo.json`; regenere o mapa com `python mapa/gerar_mapa.py` se ele estiver velho.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

GRAFO = Path(__file__).resolve().parent / 'grafo.json'


def normal(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')


def carregar() -> tuple[dict, dict, dict]:
    g = json.loads(GRAFO.read_text(encoding='utf-8'))
    nos = {}
    for n in g['nos']:
        nos[n['id']] = {'classe': 'arquivo', 'titulo': n['descricao'], **n}
    for c in g['conceitos']:
        nos[c['id']] = {'classe': 'conceito', **c}
    for s in g['simbolos']:
        nos[s['id']] = {'classe': 'símbolo', 'titulo': f'{s["tipo"]} em {s["arquivo"]}:{s["linha"]}', **s}
    saem, chegam = defaultdict(list), defaultdict(list)
    for a in g['arestas']:
        saem[a['de']].append((a['para'], a['tipo'], a.get('peso')))
        chegam[a['para']].append((a['de'], a['tipo'], a.get('peso')))
    for s in g['simbolos']:  # o arquivo contém seus símbolos
        saem[s['arquivo']].append((s['id'], 'contém', None))
        chegam[s['id']].append((s['arquivo'], 'contém', None))
    return nos, saem, chegam


def buscar(nos: dict, termo: str) -> list[str]:
    if termo in nos:
        return [termo]
    t = normal(termo)
    exatos = [i for i in nos if normal(i) == t or normal(i).endswith('::' + t) or normal(i).endswith('/' + t)]
    if exatos:
        return sorted(exatos, key=lambda i: (nos[i]['classe'] != 'conceito', nos[i]['classe'] != 'arquivo', len(i)))
    palavras = t.split()
    pontos = []
    for i, n in nos.items():
        alvo = normal(f'{i} {n.get("titulo", "")} {n.get("descricao", "")} {json.dumps(n.get("atributos", {}), ensure_ascii=False)}')
        if all(p in alvo for p in palavras):
            classe = {'conceito': 2, 'arquivo': 1}.get(n['classe'], 0)
            pontos.append((sum(p in normal(i) for p in palavras) * 3 + sum(p in normal(n.get('titulo', '')) for p in palavras) + classe, i))
    return [i for _, i in sorted(pontos, key=lambda x: (-x[0], x[1]))]


def rotulo(nos: dict, i: str) -> str:
    n = nos.get(i, {})
    titulo = n.get('titulo', '')
    return f'{i} — {titulo[:110]}' if titulo else i


def mostrar(nos, saem, chegam, i: str) -> None:
    n = nos[i]
    print(f'{i}  [{n["classe"]}{" · " + n["tipo"] if n.get("tipo") and n["classe"] != "arquivo" else ""}]')
    if n.get('titulo'):
        print(f'  {n["titulo"]}')
    for chave, valor in n.get('atributos', {}).items():
        if isinstance(valor, str):
            print(f'  {chave}: {valor[:300]}')
        elif isinstance(valor, list):
            print(f'  {chave}: {len(valor)} — ' + '; '.join(str(v)[:120] for v in valor[:3]))
    for d in n.get('definido_em', []):
        print(f'  {d["papel"]}: {d["arquivo"]}' + (f':{d["linha"]}' if d.get('linha') else ''))
    if n['classe'] == 'arquivo':
        print(f'  pasta: {n["pasta"]} · {n.get("linhas") or n["bytes"]} {"linhas" if n.get("linhas") else "bytes"}')
    if n.get('pagina'):
        print(f'  página: {n["pagina"]}')
    for titulo, lista in (('saem', saem[i]), ('chegam', chegam[i])):
        if not lista:
            continue
        por_tipo = defaultdict(list)
        for outro, tipo, peso in lista:
            por_tipo[tipo].append((outro, peso))
        print(f'  {titulo}:')
        for tipo, itens in sorted(por_tipo.items(), key=lambda x: -len(x[1])):
            itens.sort(key=lambda x: (-(x[1] or 0), x[0]))
            mostra = ', '.join(o + (f' ({p}×)' if p else '') for o, p in itens[:15])
            print(f'    {tipo} ({len(itens)}): {mostra}' + (' …' if len(itens) > 15 else ''))


# Ligação fraca custa mais: um documento que cita tudo não deve virar o atalho de todo caminho.
CUSTO = {'menciona': 4, 'cita': 3, 'link': 2, 'contém': 1}


def caminho(saem, chegam, a: str, b: str) -> list[tuple[str, str, str]] | None:
    """Caminho de menor custo sem direção; devolve (de, tipo, para) na direção em que cada aresta existe."""
    import heapq
    custo, anterior, fila = {a: 0}, {a: None}, [(0, a)]
    while fila:
        c, atual = heapq.heappop(fila)
        if atual == b:
            break
        if c > custo[atual]:
            continue
        vizinhos = [(o, t, '→') for o, t, _ in saem[atual]] + [(o, t, '←') for o, t, _ in chegam[atual]]
        for outro, tipo, sentido in vizinhos:
            novo = c + CUSTO.get(tipo, 1)
            if novo < custo.get(outro, float('inf')):
                custo[outro], anterior[outro] = novo, (atual, tipo, sentido)
                heapq.heappush(fila, (novo, outro))
    if b not in anterior:
        return None
    passos, atual = [], b
    while anterior[atual]:
        de, tipo, sentido = anterior[atual]
        passos.append((de, tipo, atual) if sentido == '→' else (atual, tipo, de))
        atual = de
    return list(reversed(passos))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('termo', nargs='*')
    ap.add_argument('--caminho', nargs=2, metavar=('A', 'B'))
    ap.add_argument('--vizinhos')
    ap.add_argument('--profundidade', type=int, default=1)
    ap.add_argument('--tipo', help='filtra arestas por tipo: importa, usa, menciona, apoia-se-em, executa, resultado...')
    ap.add_argument('--limite', type=int, default=20)
    args = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    nos, saem, chegam = carregar()

    def resolver(termo: str) -> str | None:
        achados = buscar(nos, termo)
        if not achados:
            print(f'nada casa com "{termo}"')
            return None
        if len(achados) > 1 and achados[0] != termo:
            print(f'"{termo}" → {achados[0]} (outros: {", ".join(achados[1:6])}{" …" if len(achados) > 6 else ""})')
        return achados[0]

    if args.caminho:
        a, b = (resolver(x) for x in args.caminho)
        if not (a and b):
            return 1
        passos = caminho(saem, chegam, a, b)
        if passos is None:
            print(f'{a} e {b} não se ligam no grafo')
            return 1
        print(f'{len(passos)} passo(s):')
        for de, tipo, para in passos:
            print(f'  {rotulo(nos, de)}\n      —[{tipo}]→ {rotulo(nos, para)}')
        return 0
    if args.vizinhos:
        origem = resolver(args.vizinhos)
        if not origem:
            return 1
        filtro = args.tipo.replace(' ', '-') if args.tipo else None
        vistos, fronteira = {origem: 0}, [origem]
        for nivel in range(1, args.profundidade + 1):
            proxima = []
            for atual in fronteira:
                for outro, tipo, _ in saem[atual] + chegam[atual]:
                    if (filtro is None or tipo.replace(' ', '-') == filtro) and outro not in vistos:
                        vistos[outro] = nivel
                        proxima.append(outro)
            fronteira = proxima
        for i, nivel in sorted(vistos.items(), key=lambda x: (x[1], x[0])):
            if nivel:
                print(f'{"  " * nivel}{nivel}: {rotulo(nos, i)}')
        return 0
    if not args.termo:
        ap.print_help()
        return 1
    achados = buscar(nos, ' '.join(args.termo))
    if not achados:
        print('nada encontrado')
        return 1
    mostrar(nos, saem, chegam, achados[0])
    if len(achados) > 1:
        print(f'\noutros {len(achados) - 1} resultados:')
        for i in achados[1:args.limite]:
            print(f'  {rotulo(nos, i)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
