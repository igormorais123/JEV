"""R30 — ligar uma afirmação à rodada que a testou: o Jev ordena prosa melhor que o BM25 longe do teto?

De onde vem. H100 foi falsificada com 21 perguntas em que o Jev e o BM25 acertaram 20 cada:
empate no teto, que não separa ninguém. A conclusão publicada ("em prosa, use BM25") se apoia
nessa amostra. Esta rodada refaz a comparação numa tarefa de prosa mais difícil e com gabarito
que ninguém escreveu para ela: o grafo do repositório sabe, por construção, em que rodada cada
hipótese se apoia (as arestas `apoia-se em` de `mapa/grafo.json`, lidas do campo `fonte` de cada
prova). A pergunta é a hipótese (título, previsão e critério); os candidatos são os textos de
oito rodadas em `laboratorio/PREREGISTRO.md`, a certa entre eles. Os identificadores de rodada,
hipótese e experimento são apagados dos dois lados, para que ninguém ache por nome.

É também o ensaio de um uso novo: o Jev como ligador de grafo de conhecimento, que decide a que
evidência uma afirmação pertence.

**Previsões e falsificação, escritas antes de rodar.**

H30a  O Jev põe uma rodada certa em primeiro lugar mais vezes que o BM25, McNemar exato
      p < 0,05. Empate ou vitória do BM25 confirma H100 com o quádruplo da amostra.
H30b  A tarefa não está no teto. Isto deixou de ser previsão: o BM25 é determinístico e grátis,
      e foi medido ao montar os casos, antes de qualquer chamada ao Jev: 34 de 49 em primeiro lugar.

Viés declarado: hipóteses e rodadas foram escritas pela mesma autora, com o mesmo vocabulário, o
que favorece a busca por palavra.

    python laboratorio/r30_hipotese_e_prova.py --rodar
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r21_generalizacao import Medidor, ordenar_prosa_bm25  # noqa: E402

DESTINO = RAIZ / 'laboratorio' / 'r30-hipotese-e-prova.json'
SEMENTE = 20260921
CANDIDATOS = 8
LIMITE_DO_TEXTO = 3500
CUSTO_MAXIMO_PREVISTO = 0.10
IDENTIFICADOR = re.compile(r'\b[RHEQ]\d{1,3}[a-z]?\b')
TITULO = re.compile(r'^#{2,3} (R\d+b?(?:(?:, | e )R\d+b?)*)\b', re.M)
CRITERIOS = {
    'testa': 'O texto descreve o experimento que mede exatamente o que a afirmacao diz.',
    'relacionado': 'O texto trata de assunto proximo, mas nao mede o que a afirmacao diz.',
    'outro-assunto': 'O texto trata de outra coisa.',
}
ORDEM = {'testa': 0, 'relacionado': 1, 'outro-assunto': 2}


def textos_das_rodadas():
    fonte = (RAIZ / 'laboratorio' / 'PREREGISTRO.md').read_text(encoding='utf-8')
    # uma rodada vai do próprio título até o título da rodada seguinte ou de um bloco novo
    cortes = [m.start() for m in re.finditer(r'^(?:# |#{2,3} R\d)', fonte, re.M)] + [len(fonte)]
    textos = {}
    for inicio, fim in zip(cortes, cortes[1:]):
        bloco = fonte[inicio:fim]
        achado = TITULO.match(bloco)
        if not achado:
            continue
        for rodada in re.findall(r'R\d+b?', achado.group(1)):
            textos[rodada] = (textos.get(rodada, '') + '\n' + bloco).strip()
    return {r: ' '.join(IDENTIFICADOR.sub('', t).split())[:LIMITE_DO_TEXTO] for r, t in textos.items()}


def montar_casos():
    grafo = json.loads((RAIZ / 'mapa' / 'grafo.json').read_text(encoding='utf-8'))
    rodadas = textos_das_rodadas()
    certas = {}
    for a in grafo['arestas']:
        if a['tipo'] == 'apoia-se em' and a['de'].startswith('H') and a['para'] in rodadas:
            certas.setdefault(a['de'], set()).add(a['para'])
    sorteio = random.Random(SEMENTE)
    casos = []
    for c in grafo['conceitos']:
        if c['id'] not in certas or len(certas[c['id']]) > 2:  # hipótese de muitas rodadas é agregado, não ligação
            continue
        a = c['atributos']
        pergunta = IDENTIFICADOR.sub('', f"{c['titulo']} Previsao: {a.get('previsao', '')} Criterio: {a.get('criterio', '')}")
        iguais = {rodadas[r] for r in certas[c['id']]}  # R9 e R10 dividem o mesmo texto: não pode ser distrator
        outras = sorted(r for r in rodadas if r not in certas[c['id']] and rodadas[r] not in iguais)
        escolhidas = sorted(certas[c['id']]) + sorteio.sample(outras, CANDIDATOS - len(certas[c['id']]))
        sorteio.shuffle(escolhidas)
        casos.append({'id': c['id'], 'pergunta': ' '.join(pergunta.split()), 'certas': sorted(certas[c['id']]),
                      'candidatos': [{'chave': r, 'texto': rodadas[r]} for r in escolhidas]})
    return casos


def julgar(tarefa):
    estado = f"Afirmacao: {tarefa['pergunta']}\n\nTexto de um experimento:\n{tarefa['texto']}"
    respostas, _ = perguntar(estado, {'ligacao': {
        'type': 'choice', 'instructions': 'Este texto descreve o experimento que testa a afirmacao acima?',
        'criteria': dict(CRITERIOS)}}, rodada='R30')
    bloco = (respostas or {}).get('ligacao') or {}
    return {'id': tarefa['id'], 'chave': tarefa['chave'], 'classe': bloco.get('choice'),
            'confianca': bloco.get('confidence')}


def main():
    analise = argparse.ArgumentParser(description=__doc__)
    analise.add_argument('--rodar', action='store_true')
    args = analise.parse_args()
    casos = montar_casos()
    print(f'{len(casos)} hipóteses com rodada certa entre {len(textos_das_rodadas())} rodadas com texto')
    if not args.rodar:
        return
    medidor = Medidor()
    tarefas = [{'id': c['id'], 'pergunta': c['pergunta'], **cand} for c in casos for cand in c['candidatos']]
    julgados = em_paralelo(tarefas, julgar, trabalhadores=8, rotulo='R30')
    DESTINO.with_name('r30-bruto.json').write_text(json.dumps(julgados, ensure_ascii=False, indent=1), encoding='utf-8')
    por_caso = {}
    for j in julgados:
        por_caso.setdefault(j['id'], []).append(j)
    linhas = []
    for c in casos:
        jev = sorted(por_caso[c['id']], key=lambda j: (ORDEM.get(j['classe'], 9), -(j['confianca'] or 0)))
        bm25 = ordenar_prosa_bm25(c)
        linhas.append({'id': c['id'], 'certas': c['certas'], 'jev': [j['chave'] for j in jev],
                       'classe_do_topo': jev[0]['classe'], 'confianca_do_topo': jev[0]['confianca'],
                       'quantas_testa': sum(j['classe'] == 'testa' for j in jev),
                       'bm25': [b['chave'] for b in bm25],
                       'jev_top1': jev[0]['chave'] in c['certas'], 'bm25_top1': bm25[0]['chave'] in c['certas'],
                       'jev_top2': any(j['chave'] in c['certas'] for j in jev[:2]),
                       'bm25_top2': any(b['chave'] in c['certas'] for b in bm25[:2])})
    n = len(linhas)
    resumo = {}
    for braco in ('jev', 'bm25'):
        for k in ('top1', 'top2'):
            acertos = sum(l[f'{braco}_{k}'] for l in linhas)
            resumo[f'{braco}_{k}'] = {'acertos': acertos, 'n': n, 'taxa': round(acertos / n, 4), 'ic95': wilson(acertos, n)}
    so_jev = sum(l['jev_top1'] and not l['bm25_top1'] for l in linhas)
    so_bm25 = sum(l['bm25_top1'] and not l['jev_top1'] for l in linhas)
    resumo['pareado_top1'] = {'so_jev': so_jev, 'so_bm25': so_bm25, 'p': mcnemar_exato(so_jev, so_bm25)}
    sem_testa = [l for l in linhas if l['classe_do_topo'] != 'testa']
    resumo['topo_sem_testa'] = {'n': len(sem_testa), 'acertos_top1': sum(l['jev_top1'] for l in sem_testa)}
    gasto, chamadas, _ = medidor.gasto()
    resultado = {'casos': n, 'candidatos': CANDIDATOS, 'resumo': resumo, 'detalhe': linhas,
                 'custo_usd': round(gasto, 6), 'chamadas': chamadas}
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    print(f'{chamadas} chamadas, US$ {gasto:.6f}')


if __name__ == '__main__':
    main()
