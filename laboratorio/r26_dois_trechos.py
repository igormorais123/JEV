"""R26 — a pergunta cuja resposta exige dois trechos: o teste adversarial da recomendação central.

Toda a demonstração de que selecionar bate carregar tudo (R17, R18, R20, 169 perguntas) vem de
perguntas com **uma** fonte de resposta. Q095 nomeou o teste que falta: se a resposta estiver
dividida em dois trechos, mandar um deve ser pior que mandar oito, e a recomendação central —
k = 1, com a regra de recall de graça — inverte exatamente onde o usuário mais precisaria dela.

A construção é mecânica, como sempre: dois casos aprovados dos lotes da R18 e da R20, com alvos distintos,
viram uma pergunta dupla ("responda às duas"), e a resposta só conta como certa se as **duas**
regex casarem. Os candidatos são os dois alvos mais seis distratores. O Jev ordena os oito como
na R18, e o mesmo respondedor barato recebe k = 1, 2, 3 ou os oito.

O que se mede além do acerto: quantas vezes o Jev põe os dois alvos no topo (recall@2 dos dois),
e o que a regra de recall de graça vê — se o topo vier `essencial`, a regra não dispara, e é aí
que k = 1 falha sem avisar. Um controle pareado roda a primeira pergunta de cada par sozinha,
com os mesmos oito candidatos, para confirmar que a queda é da divisão e não do candidato.

**Falsificação.** Se `jev-1` acertar dentro de 5 pontos de `todos` nas perguntas duplas, a
divisão da resposta não é um limite e Q095 estava errada. Se `jev-2` recuperar o nível de
`todos`, a recomendação sobrevive com k = 2 e o guia passa a dizer isso. Se nem `jev-3`
recuperar, o guia precisa de uma regra que este estudo ainda não tem.

    python laboratorio/r26_dois_trechos.py --rodar
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import chave, em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r15_adversario_externo import http  # noqa: E402
from laboratorio.r17_economia_de_contexto import CRITERIOS_JEV, ORDEM_JEV, pool  # noqa: E402
from laboratorio.r21_generalizacao import Medidor  # noqa: E402

# Os dois lotes aprovados do estudo, R18 e R20: 169 perguntas de fonte única viram 80 pares.
PERGUNTAS = [RAIZ / 'laboratorio' / 'r18-perguntas.json', RAIZ / 'laboratorio' / 'r20-perguntas.json']
DESTINO = RAIZ / 'laboratorio' / 'r26-dois-trechos.json'
# O bruto vai ao disco antes da análise. A primeira corrida desta rodada pagou todas as
# chamadas e perdeu tudo numa exceção da análise -- a lição do E11, reaprendida a US$ 0,02.
BRUTO = RAIZ / 'laboratorio' / 'r26-bruto.json'
SEMENTE = 20260926
PARES = 80
CANDIDATOS = 8
RESPONDEDOR = 'mistralai/mistral-nemo'
CUSTO_MAXIMO_PREVISTO = 0.10


def montar_casos():
    aprovadas = [a for arquivo in PERGUNTAS
                 for a in json.loads(arquivo.read_text(encoding='utf-8'))['aprovadas']]
    todas = pool()
    aprovadas = [a for a in aprovadas if a['alvo'] in todas]
    sorteio = random.Random(SEMENTE)
    sorteio.shuffle(aprovadas)
    casos = []
    for k in range(min(PARES, len(aprovadas) // 2)):
        a, b = aprovadas[2 * k], aprovadas[2 * k + 1]
        if a['alvo'] == b['alvo']:
            continue
        distratores = [d for d in a['distratores'] + b['distratores']
                       if d not in (a['alvo'], b['alvo']) and d in todas]
        distratores = list(dict.fromkeys(distratores))[:CANDIDATOS - 2]
        chaves = [a['alvo'], b['alvo']] + distratores
        sorteio.shuffle(chaves)
        candidatos = [{'chave': c, 'texto': todas[c], 'bytes': len(todas[c].encode('utf-8'))}
                      for c in chaves]
        casos.append({'id': f'd{k:03d}',
                      'dupla': f"Responda as duas perguntas, em uma frase cada: (1) {a['pergunta']} "
                               f"(2) {b['pergunta']}",
                      'simples': a['pergunta'],
                      'alvos': [a['alvo'], b['alvo']], 'aceita': [a['regex'], b['regex']],
                      'candidatos': candidatos})
    return casos


def ordenar(caso, pergunta):
    def julgar(candidato):
        estado = (f"Pergunta: {pergunta}\n\n"
                  f"Trecho de codigo ({candidato['chave']}):\n{candidato['texto']}")
        respostas, _ = perguntar(estado, {'relevancia': {
            'type': 'choice', 'instructions': 'Este trecho de codigo responde a pergunta acima?',
            'criteria': dict(CRITERIOS_JEV)}}, rodada='R26')
        bloco = (respostas or {}).get('relevancia') or {}
        return {**candidato, 'classe': bloco.get('choice'), 'confianca': bloco.get('confidence')}
    julgados = [julgar(c) for c in caso['candidatos']]
    julgados.sort(key=lambda c: (ORDEM_JEV.get(c['classe'], 9), -(c['confianca'] or 0)))
    return julgados


def responder(pergunta, trechos, api_key):
    contexto = '\n\n'.join(f"--- {t['chave']} ---\n{t['texto']}" for t in trechos)
    corpo = {'model': RESPONDEDOR, 'max_tokens': 300, 'temperature': 0,
             'messages': [{'role': 'user', 'content':
                           f'Com base apenas nos trechos de codigo abaixo, responda de forma '
                           f'curta e direta.\n\nPergunta: {pergunta}\n\n{contexto}'}]}
    status, resposta = http(corpo, api_key, rodada='R26-resposta', modelo=RESPONDEDOR)
    if status != 200:
        return None, len(contexto.encode('utf-8'))
    try:
        return resposta['choices'][0]['message']['content'], len(contexto.encode('utf-8'))
    except (KeyError, IndexError, TypeError):
        return None, len(contexto.encode('utf-8'))


def casa(regexes, texto):
    try:
        return all(re.search(r, texto or '', re.IGNORECASE) for r in regexes)
    except re.error:
        return False


def rodar(api_key):
    casos = montar_casos()
    print(f'{len(casos)} pares; {len(casos) * CANDIDATOS * 2} chamadas de ordenação')
    ordem_dupla = em_paralelo(casos, lambda c: ordenar(c, c['dupla']), trabalhadores=8,
                              rotulo='R26-ord-dupla')
    ordem_simples = em_paralelo(casos, lambda c: ordenar(c, c['simples']), trabalhadores=8,
                                rotulo='R26-ord-simples')

    tarefas = []
    for caso, dupla, simples in zip(casos, ordem_dupla, ordem_simples):
        for k in (1, 2, 3):
            tarefas.append({'caso': caso, 'tipo': 'dupla', 'arranjo': f'jev-{k}',
                            'trechos': dupla[:k], 'pergunta': caso['dupla'],
                            'aceita': caso['aceita'], 'alvos': caso['alvos']})
        tarefas.append({'caso': caso, 'tipo': 'dupla', 'arranjo': 'todos',
                        'trechos': caso['candidatos'], 'pergunta': caso['dupla'],
                        'aceita': caso['aceita'], 'alvos': caso['alvos']})
        for arranjo, trechos in (('jev-1', simples[:1]), ('todos', caso['candidatos'])):
            tarefas.append({'caso': caso, 'tipo': 'simples', 'arranjo': arranjo,
                            'trechos': trechos, 'pergunta': caso['simples'],
                            'aceita': caso['aceita'][:1], 'alvos': caso['alvos'][:1]})
    print(f'{len(tarefas)} chamadas de resposta')
    saidas = em_paralelo(tarefas, lambda t: responder(t['pergunta'], t['trechos'], api_key),
                         trabalhadores=6, rotulo='R26-resp')

    linhas = []
    for tarefa, (texto, enviados) in zip(tarefas, saidas):
        presentes = [t['chave'] for t in tarefa['trechos']]
        linhas.append({'id': tarefa['caso']['id'], 'tipo': tarefa['tipo'],
                       'arranjo': tarefa['arranjo'],
                       'alvos_presentes': sum(1 for a in tarefa['alvos'] if a in presentes),
                       'certo': casa(tarefa['aceita'], texto), 'bytes': enviados,
                       'resposta': (texto or '')[:200]})

    ordens = []
    for caso, dupla in zip(casos, ordem_dupla):
        topo = dupla[0]
        ordens.append({'id': caso['id'],
                       'classe_do_topo': topo['classe'],
                       'topo_e_alvo': topo['chave'] in caso['alvos'],
                       'dois_no_top2': sum(1 for c in dupla[:2] if c['chave'] in caso['alvos']) == 2,
                       'dois_no_top3': sum(1 for c in dupla[:3] if c['chave'] in caso['alvos']) == 2,
                       'essenciais': sum(1 for c in dupla if c['classe'] == 'essencial'),
                       'alvos_essenciais': sum(1 for c in dupla
                                               if c['chave'] in caso['alvos'] and c['classe'] == 'essencial')})
    BRUTO.write_text(json.dumps({'linhas': linhas, 'ordens': ordens}, ensure_ascii=False),
                     encoding='utf-8')
    return analisar(linhas, ordens, casos)


def analisar(linhas, ordens, casos):
    saida = {'pares': len(casos), 'candidatos': CANDIDATOS, 'respondedor': RESPONDEDOR,
             'arranjos': {}, 'ordenacao': {}, 'detalhe': linhas, 'ordens': ordens}
    base = {l['id']: l['certo'] for l in linhas if l['tipo'] == 'dupla' and l['arranjo'] == 'todos'}
    for tipo in ('dupla', 'simples'):
        esperados = 2 if tipo == 'dupla' else 1
        for arranjo in ('jev-1', 'jev-2', 'jev-3', 'todos'):
            grupo = [l for l in linhas if l['tipo'] == tipo and l['arranjo'] == arranjo]
            if not grupo:
                continue
            acertos = sum(1 for l in grupo if l['certo'])
            bloco = {'n': len(grupo), 'acertos': acertos, 'taxa': round(acertos / len(grupo), 4),
                     'ic95': wilson(acertos, len(grupo)),
                     'bytes': sum(l['bytes'] for l in grupo),
                     'todos_os_alvos_presentes': sum(1 for l in grupo
                                                     if l['alvos_presentes'] == esperados)}
            if tipo == 'dupla' and arranjo != 'todos':
                so_todos = sum(1 for l in grupo if base.get(l['id']) and not l['certo'])
                so_k = sum(1 for l in grupo if l['certo'] and base.get(l['id']) is False)
                bloco['pareado_contra_todos'] = {'certo_so_todos': so_todos,
                                                 'certo_so_selecao': so_k,
                                                 'p': mcnemar_exato(so_todos, so_k)}
            saida['arranjos'][f'{tipo}/{arranjo}'] = bloco
    n = len(ordens)
    saida['ordenacao'] = {
        'n': n,
        'topo_e_alvo': sum(1 for o in ordens if o['topo_e_alvo']),
        'dois_no_top2': sum(1 for o in ordens if o['dois_no_top2']),
        'dois_no_top3': sum(1 for o in ordens if o['dois_no_top3']),
        'topo_essencial': sum(1 for o in ordens if o['classe_do_topo'] == 'essencial'),
        'regra_de_recall_dispararia': sum(1 for o in ordens if o['classe_do_topo'] != 'essencial'),
        'media_de_essenciais': round(sum(o['essenciais'] for o in ordens) / n, 2) if n else None,
        'casos_com_dois_alvos_essenciais': sum(1 for o in ordens if o['alvos_essenciais'] == 2)}
    return saida


def main():
    analise = argparse.ArgumentParser(description=__doc__)
    analise.add_argument('--rodar', action='store_true')
    args = analise.parse_args()
    api_key = chave()
    medidor = Medidor()
    if not args.rodar:
        casos = montar_casos()
        print(f'{len(casos)} pares prontos; exemplo: {casos[0]["dupla"][:160]}')
        return
    resultado = rodar(api_key)
    for nome, b in resultado['arranjos'].items():
        print(f"   {nome:14} {b['acertos']:>3}/{b['n']:<3} {b['taxa']}  alvos presentes "
              f"{b['todos_os_alvos_presentes']}  {b.get('pareado_contra_todos', '')}")
    print('   ordenação', resultado['ordenacao'])
    gasto, chamadas, _ = medidor.gasto()
    resultado['custo_usd'] = round(gasto, 6)
    resultado['chamadas'] = chamadas
    if gasto > CUSTO_MAXIMO_PREVISTO:
        print(f'ATENÇÃO: passou do teto previsto de US$ {CUSTO_MAXIMO_PREVISTO}')
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{chamadas} chamadas nesta corrida, US$ {gasto:.6f}')


if __name__ == '__main__':
    main()
