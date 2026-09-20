"""R20 — replicar a curva com amostra nova, e deixar a confiança escolher quantos trechos mandar.

A R18 deixou dois fios soltos.

**O primeiro é de poder.** "Mais contexto atrapalha" apareceu três vezes na mesma direção — k=2
ganha 4 a 0 de k=3, 4 a 0 de k=5, 7 a 2 de carregar tudo — e nenhuma dessas comparações atinge
p < 0,05 sozinha. Com 74 perguntas não dá. Esta rodada gera **um lote novo**, com outra semente,
e o teste do fio solto é feito no conjunto dos dois lotes, ~148 perguntas, declarado assim
antes de rodar.

**O segundo é de política.** k foi sempre fixo. Mas o Jev devolve classe e confiança para cada
candidato, e o estudo inteiro mostra que essa confiança é informativa. Se o topo vem como
`essencial` com confiança alta, um trecho basta; se vem `incerto`, talvez três. Nunca se testou.

    k=1                mais barato, 91,9% na R18
    k=2                melhor acerto, 93,2%
    k adaptativo       1 quando o topo é `essencial` e confiante; 2 em caso normal; 3 na dúvida

**H20a.** No conjunto dos dois lotes, k=2 supera k=3 com p < 0,05. (Se não superar, "mais
contexto atrapalha" fica como direção consistente sem demonstração, e o guia dirá isso.)
**H20b.** O k adaptativo gasta menos que o k=2 fixo sem perder acerto.
**H20c.** A confiança da ordenação prediz o acerto da resposta: casos em que o topo veio incerto
erram mais.

    python laboratorio/r20_k_adaptativo.py --gerar
    python laboratorio/r20_k_adaptativo.py --rodar
"""
import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import chave, em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r15_adversario_externo import http  # noqa: E402
from laboratorio.r17_economia_de_contexto import CRITERIOS_JEV, ORDEM_JEV, pool  # noqa: E402
from laboratorio.r18_escala import PEDIDO, RESPONDEDOR, responder  # noqa: E402

PERGUNTAS = RAIZ / 'laboratorio' / 'r20-perguntas.json'
DESTINO = RAIZ / 'laboratorio' / 'r20-k-adaptativo.json'
R18 = RAIZ / 'laboratorio' / 'r18-escala.json'
SEMENTE = 20260921          # diferente da R18 de propósito: lote novo, funções novas
ALVOS = 130
CANDIDATOS = 8
GERADOR = 'openai/gpt-oss-120b'

# A política adaptativa, congelada antes de rodar.
CONFIANCA_ALTA = 0.90


def k_adaptativo(ordenados):
    """Quantos trechos mandar, olhando só o topo da ordenação.

    A regra é deliberadamente simples: uma linha de decisão, três resultados possíveis. Uma
    política com mais parâmetros ficaria ajustada a estes 148 casos e não sobreviveria ao
    próximo corpus -- é o erro que o corte de confiança do E12 cometeu e o E11 pagou.
    """
    topo = ordenados[0]
    if topo.get('classe') == 'essencial' and (topo.get('confianca') or 0) >= CONFIANCA_ALTA:
        return 1
    if topo.get('classe') in ('incerto', 'irrelevante'):
        return 3
    return 2


def gerar(api_key):
    todas = pool()
    sorteio = random.Random(SEMENTE)
    chaves = sorted(todas)
    sorteio.shuffle(chaves)
    # Tira as funções que já viraram pergunta na R18: lote novo quer dizer material novo.
    ja_usadas = set()
    if (RAIZ / 'laboratorio' / 'r18-perguntas.json').exists():
        antigas = json.loads((RAIZ / 'laboratorio' / 'r18-perguntas.json')
                             .read_text(encoding='utf-8'))
        ja_usadas = {a['alvo'] for a in antigas['aprovadas']}
    escolhidos = [c for c in chaves
                  if 300 < len(todas[c]) < 3000 and c not in ja_usadas][:ALVOS]
    print(f'{len(escolhidos)} funções novas vão ao gerador ({len(ja_usadas)} já usadas na R18)')

    def uma(alvo):
        corpo = {'model': GERADOR, 'max_tokens': 1600, 'temperature': 0.4,
                 'response_format': {'type': 'json_object'},
                 'messages': [{'role': 'user',
                               'content': PEDIDO.format(trecho=todas[alvo][:3000])}]}
        status, resposta = http(corpo, api_key, rodada='R20-geracao', modelo=GERADOR)
        if status != 200:
            return None
        try:
            mensagem = resposta['choices'][0]['message']
        except (KeyError, IndexError, TypeError):
            return None
        bruto = (mensagem.get('content') or '').strip()
        if not bruto:
            achado = re.search(r'\{[^{}]*"pergunta"[^{}]*\}', mensagem.get('reasoning') or '', re.S)
            bruto = achado.group(0) if achado else ''
        try:
            bloco = json.loads(bruto)
            return {'alvo': alvo, 'pergunta': str(bloco['pergunta']).strip(),
                    'regex': str(bloco['regex']).strip()}
        except (KeyError, TypeError, ValueError):
            return None

    brutas = [p for p in em_paralelo(escolhidos, uma, trabalhadores=8, rotulo='R20-gera') if p]
    print(f'{len(brutas)} perguntas geradas')

    sorteio2 = random.Random(SEMENTE + 7)
    aprovadas, recusas = [], Counter()
    for item in brutas:
        alvo, texto_alvo = item['alvo'], todas[item['alvo']]
        try:
            padrao = re.compile(item['regex'], re.IGNORECASE)
        except re.error:
            recusas['regex invalida'] += 1
            continue
        nome = alvo.split('::')[1]
        arquivo = alvo.split('::')[0].split('/')[-1].replace('.py', '')
        if nome.lower() in item['pergunta'].lower() or arquivo.lower() in item['pergunta'].lower():
            recusas['a pergunta cita o nome'] += 1
            continue
        if not padrao.search(texto_alvo):
            recusas['a resposta nao esta no alvo'] += 1
            continue
        outros = [c for c in chaves if c != alvo]
        sorteio2.shuffle(outros)
        distratores = outros[:CANDIDATOS - 1]
        casam = sum(1 for d in distratores if padrao.search(todas[d]))
        if casam > 2:
            recusas[f'a regex casa com {casam} distratores'] += 1
            continue
        item['distratores'] = distratores
        aprovadas.append(item)

    print(f'{len(aprovadas)} aprovadas; recusas: {dict(recusas)}')
    PERGUNTAS.write_text(json.dumps({'semente': SEMENTE, 'gerador': GERADOR,
                                     'aprovadas': aprovadas, 'recusas': dict(recusas),
                                     'geradas': len(brutas)}, ensure_ascii=False, indent=1),
                         encoding='utf-8')
    return aprovadas


def ordenar(caso):
    def julgar(candidato):
        estado = (f"Pergunta: {caso['pergunta']}\n\n"
                  f"Trecho de codigo ({candidato['chave']}):\n{candidato['texto']}")
        respostas, _ = perguntar(estado, {'relevancia': {
            'type': 'choice',
            'instructions': 'Este trecho de codigo responde a pergunta acima?',
            'criteria': dict(CRITERIOS_JEV)}}, rodada='R20')
        bloco = (respostas or {}).get('relevancia') or {}
        return {**candidato, 'classe': bloco.get('choice'), 'confianca': bloco.get('confidence')}

    julgados = [julgar(c) for c in caso['candidatos']]
    julgados.sort(key=lambda c: (ORDEM_JEV.get(c['classe'], 9), -(c['confianca'] or 0)))
    return julgados


def rodar(api_key):
    dados = json.loads(PERGUNTAS.read_text(encoding='utf-8'))
    todas = pool()
    sorteio = random.Random(SEMENTE + 13)
    casos = []
    for i, item in enumerate(dados['aprovadas']):
        chaves = [item['alvo']] + item['distratores']
        sorteio.shuffle(chaves)
        casos.append({'id': f'n{i:03d}', 'pergunta': item['pergunta'], 'alvo': item['alvo'],
                      'aceita': item['regex'],
                      'candidatos': [{'chave': c, 'texto': todas[c],
                                      'bytes': len(todas[c].encode('utf-8'))} for c in chaves]})

    print(f'{len(casos)} casos × {CANDIDATOS} = {len(casos) * CANDIDATOS} chamadas de ordenação')
    ordens = em_paralelo(casos, ordenar, trabalhadores=8, rotulo='R20-ord')

    tarefas = []
    for caso, ordenados in zip(casos, ordens):
        caso['_ordem'] = [{k: c[k] for k in ('chave', 'classe', 'confianca')} for c in ordenados]
        k = k_adaptativo(ordenados)
        caso['_k'] = k
        for nome, trechos in (('todos', caso['candidatos']), ('jev-1', ordenados[:1]),
                              ('jev-2', ordenados[:2]), ('jev-3', ordenados[:3]),
                              ('adaptativo', ordenados[:k])):
            tarefas.append({'caso': caso, 'arranjo': nome, 'trechos': trechos})

    print(f'{len(tarefas)} chamadas de resposta | k escolhido: '
          f'{Counter(c["_k"] for c in casos).most_common()}')
    saidas = em_paralelo(tarefas,
                         lambda t: responder(t['caso'], t['trechos'], 'texto', api_key),
                         trabalhadores=6, rotulo='R20-resp')

    linhas = []
    for tarefa, (texto, bytes_enviados) in zip(tarefas, saidas):
        caso = tarefa['caso']
        try:
            certo = bool(texto and re.search(caso['aceita'], texto, re.IGNORECASE))
        except re.error:
            certo = False
        topo = caso['_ordem'][0]
        linhas.append({'id': caso['id'], 'arranjo': tarefa['arranjo'], 'certo': certo,
                       'bytes': bytes_enviados, 'k': caso['_k'],
                       'classe_do_topo': topo['classe'], 'confianca_do_topo': topo['confianca'],
                       'alvo_presente': any(t['chave'] == caso['alvo'] for t in tarefa['trechos']),
                       'resposta': (texto or '')[:140]})

    analisar(linhas, casos)


def analisar(linhas, casos):
    resultado = {'casos': len(casos), 'corte_da_politica': CONFIANCA_ALTA, 'arranjos': {},
                 'detalhe': linhas}
    base = sum(l['bytes'] for l in linhas if l['arranjo'] == 'todos')

    print(f"\n   {'arranjo':12} {'acertos':>10} {'taxa':>7} {'IC95':>18} {'bytes':>10} {'economia':>9}")
    for arranjo in ('todos', 'jev-1', 'jev-2', 'jev-3', 'adaptativo'):
        grupo = [l for l in linhas if l['arranjo'] == arranjo]
        acertos = sum(1 for l in grupo if l['certo'])
        enviados = sum(l['bytes'] for l in grupo)
        bloco = {'n': len(grupo), 'acertos': acertos, 'taxa': round(acertos / len(grupo), 4),
                 'ic95': wilson(acertos, len(grupo)), 'bytes': enviados,
                 'economia': round(1 - enviados / base, 4) if base else None}
        resultado['arranjos'][arranjo] = bloco
        print(f"   {arranjo:12} {acertos:>5}/{len(grupo):<4} {bloco['taxa']:>7.1%} "
              f"{str(bloco['ic95']):>18} {enviados:>10,} {bloco['economia']:>8.1%}")

    por_id = {l['id']: {} for l in linhas}
    for l in linhas:
        por_id[l['id']][l['arranjo']] = l['certo']

    def pareado(a, b, mapa=por_id):
        sa = sum(1 for v in mapa.values() if v.get(a) and not v.get(b))
        sb = sum(1 for v in mapa.values() if v.get(b) and not v.get(a))
        return {'so_' + a: sa, 'so_' + b: sb, 'p': mcnemar_exato(sa, sb)}

    print('\n   neste lote (McNemar exato)')
    resultado['pareado'] = {}
    for a, b in (('jev-2', 'jev-3'), ('jev-2', 'todos'), ('adaptativo', 'jev-2'),
                 ('adaptativo', 'jev-1')):
        bloco = pareado(a, b)
        resultado['pareado'][f'{a} vs {b}'] = bloco
        print(f"   {a:11} vs {b:8} {bloco}{' *' if bloco['p'] < 0.05 else ''}")

    # H20a: o teste com poder, nos dois lotes juntos, declarado antes de rodar.
    if R18.exists():
        antigo = json.loads(R18.read_text(encoding='utf-8'))
        juntos = dict(por_id)
        for l in antigo['detalhe']:
            juntos.setdefault('r18-' + l['id'], {})[l['arranjo']] = l['certo']
        resultado['H20a_dois_lotes'] = {
            'n': len(juntos),
            'jev-2 vs jev-3': pareado('jev-2', 'jev-3', juntos),
            'jev-2 vs todos': pareado('jev-2', 'todos', juntos),
        }
        print(f"\n   H20a — os dois lotes juntos, n = {len(juntos)}")
        for nome, bloco in resultado['H20a_dois_lotes'].items():
            if isinstance(bloco, dict):
                print(f"   {nome:18} {bloco}{' *' if bloco['p'] < 0.05 else ''}")

    # H20c: a classe do topo prediz o acerto?
    print('\n   H20c — o acerto por classe do topo da ordenação (arranjo jev-2)')
    grupo = [l for l in linhas if l['arranjo'] == 'jev-2']
    por_classe = {}
    for classe in ('essencial', 'complementar', 'incerto', 'irrelevante', None):
        sub = [l for l in grupo if l['classe_do_topo'] == classe]
        if not sub:
            continue
        acertos = sum(1 for l in sub if l['certo'])
        por_classe[str(classe)] = {'n': len(sub), 'acertos': acertos,
                                   'taxa': round(acertos / len(sub), 4),
                                   'ic95': wilson(acertos, len(sub)),
                                   'alvo_presente': sum(1 for l in sub if l['alvo_presente'])}
        bloco = por_classe[str(classe)]
        print(f"   topo={str(classe):14} {acertos:>3}/{len(sub):<3} {bloco['taxa']:>7.1%} "
              f"alvo presente {bloco['alvo_presente']}/{len(sub)}")
    resultado['por_classe_do_topo'] = por_classe

    alto = [l for l in grupo if (l['confianca_do_topo'] or 0) >= CONFIANCA_ALTA]
    baixo = [l for l in grupo if (l['confianca_do_topo'] or 0) < CONFIANCA_ALTA]
    resultado['por_confianca_do_topo'] = {
        f'>= {CONFIANCA_ALTA}': {'n': len(alto), 'taxa': round(sum(l['certo'] for l in alto) / len(alto), 4) if alto else None},
        f'< {CONFIANCA_ALTA}': {'n': len(baixo), 'taxa': round(sum(l['certo'] for l in baixo) / len(baixo), 4) if baixo else None}}
    print(f"   confiança do topo ≥ {CONFIANCA_ALTA}: "
          f"{resultado['por_confianca_do_topo'][f'>= {CONFIANCA_ALTA}']} | "
          f"< {CONFIANCA_ALTA}: {resultado['por_confianca_do_topo'][f'< {CONFIANCA_ALTA}']}")

    ada, fixo2 = resultado['arranjos']['adaptativo'], resultado['arranjos']['jev-2']
    resultado['veredito'] = {
        'H20a': ('sustentada'
                 if resultado.get('H20a_dois_lotes', {}).get('jev-2 vs jev-3', {}).get('p', 1) < 0.05
                 else 'direcao consistente sem demonstracao'),
        'H20b': ('sustentada' if ada['bytes'] < fixo2['bytes'] and ada['acertos'] >= fixo2['acertos']
                 else 'nao sustentada'),
    }
    print(f"\n   veredito: {resultado['veredito']}")

    for caso in casos:
        caso.pop('candidatos', None)
    resultado['casos_detalhe'] = [{'id': c['id'], 'alvo': c['alvo'], 'k': c['_k'],
                                   'ordem': c['_ordem']} for c in casos]
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'   gravado em {DESTINO.name}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gerar', action='store_true')
    parser.add_argument('--rodar', action='store_true')
    args = parser.parse_args()
    api_key = chave()
    if args.gerar or not PERGUNTAS.exists():
        gerar(api_key)
    if args.rodar:
        rodar(api_key)


if __name__ == '__main__':
    main()
