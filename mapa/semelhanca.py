"""Semelhança de conteúdo: liga o que fala da mesma coisa, mesmo quando um não cita o outro.

Cada conceito e cada arquivo vira um texto (título, enunciado, previsão, critério, resposta; ou descrição,
seções e nomes de função), reduzido a radicais e pesado por TF-IDF. Dois nós são `semelhante` quando o
cosseno entre eles passa do corte e um está entre os mais próximos do outro. Pares que já têm ligação
direta ficam de fora: a aresta nova só vale se disser algo que o grafo ainda não diz.

Sobre a semelhança entre conceitos, uma propagação de rótulos agrupa os temas do estudo. Cada tema recebe
o nome das palavras que mais pesam nos seus membros, e os pares semelhantes com resultado diferente
(hipótese sustentada ao lado de falsificada ou inconclusiva) viram contrastes, que é onde o estudo tem mais a explicar.
Só biblioteca padrão e determinístico: a mesma entrada dá o mesmo mapa.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict

PARADAS = set('''
a ao aos as ate com como da das de dela dele deles do dos e ela ele eles em entre era essa esse esta este eu foi
for ha isso isto ja la lhe mais mas me mesmo muito na nas nao nem no nos o os ou para pela pelas pelo pelos por
qual quando que quem se sem ser seu sua sao so tambem te tem tinha um uma umas uns vai ver vez voce cada outro
outra outros outras todo toda todos todas onde depois antes sobre ainda aqui ali assim entao porque pois quanto
quantos quantas qualquer nunca sempre tudo nada algo alguma algum sim duas dois tres ter sera seria fica ficar
the and for with from this that into over not are was
jev arquivo arquivos python define script texto pagina linha linhas
'''.split())
# Pesam na semelhança, mas não dizem do que um tema trata: ficam fora só do nome dele.
GENERICAS_NO_NOME = {radical for radical in (
    'melhor', 'favor', 'manda', 'mandar', 'sob', 'cai', 'prese', 'presente', 'segun', 'segunda', 'dia', 'palavra', 'palav',
    'sorte', 'aguenta', 'aguen', 'queda', 'refer', 'condi', 'media', 'medio', 'fraca', 'fracao', 'metade', 'alvo', 'tamanho',
    'taman', 'escri', 'escrita', 'mes', 'resposta', 'respo', 'erro')}
CORTE = 0.2
VIZINHOS = 4


def normalizar(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')


def radicais(texto: str, formas: dict[str, Counter] | None = None) -> list[str]:
    """Radical de 5 letras: junta `injecao` e `injecoes`, `confianca` e `confiante`, sem dicionário."""
    saida = []
    for palavra in re.findall(r'[a-zà-ú][a-zà-ú0-9_]{2,}', texto.lower()):
        base = normalizar(palavra)
        if base in PARADAS or base.isdigit():
            continue
        if len(base) > 4 and base.endswith('s'):
            base = base[:-1]
        raiz = base[:5] if len(base) > 6 else base
        saida.append(raiz)
        if formas is not None:
            formas[raiz][palavra] += 1
    return saida


def texto_do_conceito(c: dict) -> str:
    a = c['atributos']
    partes = [c['titulo']] + [str(a.get(k, '')) for k in ('previsao', 'criterio', 'resposta', 'decide', 'detalhe', 'familia')]
    partes += [s.get('titulo', '') for s in a.get('secoes', []) if isinstance(s, dict)]
    return ' '.join(partes)


def texto_do_arquivo(n: dict, texto: str) -> str:
    partes = [n['descricao'], ' '.join(s['nome'].replace('_', ' ') for s in n['simbolos'])]
    if n['id'].endswith('.md'):
        partes.append(' '.join(re.findall(r'^#+ (.+)$', texto, re.M)[:40]))
    return ' '.join(partes)


def calcular(conceitos: dict, nos: dict, textos: dict, ligados: set[tuple[str, str]]) -> dict:
    formas: dict[str, Counter] = defaultdict(Counter)
    docs = {}
    for cid, c in conceitos.items():
        if cid[0] in 'ERHQ':
            docs[cid] = radicais(texto_do_conceito(c), formas)
    for arq, n in nos.items():
        if n['tipo'] in ('código', 'doc') and '/tests/' not in arq:
            docs[arq] = radicais(texto_do_arquivo(n, textos.get(arq, '')), formas)
    docs = {k: v for k, v in docs.items() if len(v) >= 4}
    df = Counter(t for v in docs.values() for t in set(v))
    total = len(docs)
    idf = {t: math.log((1 + total) / (1 + f)) + 1 for t, f in df.items() if f >= 2 and f <= total * 0.35}
    vetores = {}
    for k, v in docs.items():
        tf = Counter(t for t in v if t in idf)
        vetor = {t: (1 + math.log(f)) * idf[t] for t, f in tf.items()}
        norma = math.sqrt(sum(x * x for x in vetor.values())) or 1
        vetores[k] = {t: x / norma for t, x in vetor.items()}
    # índice invertido: só compara quem divide pelo menos um termo
    por_termo = defaultdict(list)
    for k, v in vetores.items():
        for t, x in v.items():
            por_termo[t].append((k, x))
    proximos = {}
    for k, v in vetores.items():
        acumulado = Counter()
        for t, x in v.items():
            for outro, y in por_termo[t]:
                if outro != k:
                    acumulado[outro] += x * y
        proximos[k] = [(o, s) for o, s in acumulado.most_common(VIZINHOS * 3) if s >= CORTE]
    arestas = {}
    for k, lista in proximos.items():
        escolhidos = 0
        for outro, s in lista:
            if (k, outro) in ligados or (outro, k) in ligados:
                continue
            par = tuple(sorted((k, outro)))
            arestas[par] = max(arestas.get(par, 0), round(s, 3))
            escolhidos += 1
            if escolhidos >= VIZINHOS:
                break

    # temas: propagação de rótulos sobre a semelhança entre conceitos (inclusive pares já ligados)
    viz = defaultdict(dict)
    for k, lista in proximos.items():
        if k in conceitos:
            for outro, s in lista[:VIZINHOS + 2]:
                if outro in conceitos:
                    viz[k][outro] = max(viz[k].get(outro, 0), s)
                    viz[outro][k] = max(viz[outro].get(k, 0), s)
    rotulo = {k: k for k in sorted(viz)}
    for _ in range(30):
        mudou = False
        for k in sorted(viz):
            peso = Counter()
            for outro, s in viz[k].items():
                peso[rotulo[outro]] += s
            if peso:
                melhor = max(sorted(peso), key=lambda r: (peso[r], r == rotulo[k]))
                if melhor != rotulo[k]:
                    rotulo[k], mudou = melhor, True
        if not mudou:
            break
    grupos = defaultdict(list)
    for k, r in rotulo.items():
        grupos[r].append(k)
    grupos = sorted((sorted(m) for m in grupos.values() if len(m) >= 4), key=lambda m: -len(m))

    def nome(membros):
        soma = Counter()
        for m in membros:
            for t, x in vetores.get(m, {}).items():
                if t not in GENERICAS_NO_NOME:
                    soma[t] += x
        termos = [formas[t].most_common(1)[0][0] for t, _ in soma.most_common(4)]
        return termos

    temas = {}
    for i, membros in enumerate(grupos, 1):
        tid = f'T{i:02d}'
        termos = nome(membros)
        vereditos = Counter(conceitos[m]['atributos'].get('veredito') for m in membros if m[0] == 'H')
        confianca = Counter(conceitos[m]['atributos'].get('confianca') for m in membros if m[0] == 'Q')
        contrastes = []
        for a in membros:
            for b, s in viz[a].items():
                if a < b and b in membros and a[0] == b[0] == 'H':
                    va, vb = conceitos[a]['atributos'].get('veredito'), conceitos[b]['atributos'].get('veredito')
                    if va and vb and va != vb:
                        contrastes.append((a, b, round(s, 3)))
        temas[tid] = {'titulo': ', '.join(termos[:3]), 'termos': termos, 'membros': membros,
                      'vereditos': dict(vereditos), 'confianca': dict(confianca), 'contrastes': sorted(contrastes, key=lambda x: -x[2])}
    return {'arestas': arestas, 'temas': temas}
