"""Carregadores das fontes que decidem as cem hipóteses.

São três fontes, e elas respondem a coisas diferentes:

  `artefato(nome)`   os JSON do laboratório, com a decisão e o gabarito lado a lado. É o que
                     permite falar de acurácia.
  `decisoes()`       os 3.180 recibos do livro-caixa, com latência, bytes, custo e o **vetor
                     completo de probabilidades**. Não tem gabarito, então não fala de acurácia
                     — fala de como o modelo decide, e nenhuma rodada tinha olhado para isso.
  `tentativas()`     a tabela de tentativas do livro-caixa, com status e uso de tokens. É o que
                     permite falar de falha de transporte.

`linhas_com_gabarito()` junta o que as rodadas têm em comum num formato só, para as hipóteses
que atravessam rodadas. O preço dessa unificação é declarado na própria função.
"""

from __future__ import annotations

import json
import math
import sqlite3
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LAB = RAIZ / 'laboratorio'
LEDGER = RAIZ / 'runs' / 'ledger.sqlite3'


@lru_cache(maxsize=None)
def artefato(nome):
    return json.loads((LAB / nome).read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def decisoes():
    """Os recibos de decisão do livro-caixa, com o vetor de probabilidades intacto."""
    conexao = sqlite3.connect(f'file:{LEDGER}?mode=ro', uri=True)
    linhas = []
    from laboratorio import caixa
    corte = caixa.corte_utc()
    consulta = 'select receipt_json, answers_json from shared_decisions'
    if corte:
        consulta += f" where recorded_at <= '{corte}'"
    for recibo, respostas in conexao.execute(consulta):
        r = json.loads(recibo)
        # chamada que deu timeout grava `null` no lugar das respostas; ela conta como tentativa
        # e como custo, mas não tem decisão nenhuma para analisar
        a = json.loads(respostas)
        if not isinstance(a, dict):
            a = {}
        linhas.append({
            'status': r.get('status'),
            'consumidor': r.get('consumer'),
            'latencia_ms': r.get('latency_ms'),
            'rede_ms': r.get('network_ms'),
            'estado_car': r.get('state_chars'),
            'payload_bytes': r.get('payload_bytes'),
            'custo_usd': r.get('custo_usd'),
            'nusd': r.get('settled_nusd'),
            'uso': r.get('usage'),
            'perguntas': len(a),
            'respostas': a,
        })
    conexao.close()
    return linhas


@lru_cache(maxsize=1)
def tentativas():
    conexao = sqlite3.connect(f'file:{LEDGER}?mode=ro', uri=True)
    colunas = ['attempt_id', 'experiment_id', 'status', 'latency_ms',
               'input_tokens', 'output_tokens', 'started_at_utc', 'ended_at_utc']
    from laboratorio import caixa
    corte = caixa.corte_utc()
    consulta = ('select a.attempt_id, a.arm_id, a.status, a.latency_ms, a.input_tokens, '
                'a.output_tokens, a.started_at_utc, a.ended_at_utc from attempts a')
    if corte:
        consulta += f" where a.started_at_utc is null or a.started_at_utc <= '{corte}'"
    linhas = [dict(zip(colunas, linha)) for linha in conexao.execute(consulta)]
    conexao.close()
    return linhas


@lru_cache(maxsize=1)
def custo_por_experimento():
    from laboratorio import caixa
    dado = caixa.conciliado()
    return list(dado['por_experimento']) if dado else []


@lru_cache(maxsize=1)
def retratacoes():
    """As condições cujo número está no artefato mas não vale como evidência.

    A retratação da diluição da R11 vivia só na prosa do mapa de limites, e a varredura das cem
    hipóteses caiu direto nela: H087 foi "falsificada" por um número que mede um defeito do
    laboratório, não o modelo. Legível por máquina, isso não se repete.
    """
    caminho = LAB / 'retratacoes.json'
    return json.loads(caminho.read_text(encoding='utf-8'))


def esta_retratada(artefato_nome, condicao):
    for bloco in retratacoes()['retratadas']:
        if bloco['artefato'] == artefato_nome and condicao in bloco['condicoes']:
            return bloco
    return None


@lru_cache(maxsize=1)
def gastos():
    """O diário do laboratório, que é o único lugar com o rótulo da rodada por chamada."""
    caminho = LAB / 'gastos.jsonl'
    return [json.loads(linha) for linha in caminho.read_text(encoding='utf-8').splitlines()
            if linha.strip()]


# ----------------------------------------------------------------- unificação
def linhas_com_gabarito():
    """Junta num formato só as linhas em que há decisão e gabarito comparáveis.

    O que essa unificação **custa**, declarado: ela descarta a R16, cujo espaço de rótulos é
    outro (efeito de comando, não intenção de cliente), e descarta as linhas da R4 em que a
    pergunta é de sim/não sem alvo. Também trata a condição como texto livre, porque cada
    rodada nomeia a sua do seu jeito. Serve para afirmações que atravessam rodadas; para
    afirmações sobre uma rodada, use o artefato dela.
    """
    unidas = []

    def juntar(rodada, linhas, campo_alvo, condicao):
        for linha in linhas:
            alvo = linha.get(campo_alvo)
            if not alvo or not linha.get('escolha'):
                continue
            unidas.append({
                'rodada': rodada,
                'condicao': condicao(linha),
                'alvo': alvo,
                'escolha': linha['escolha'],
                'confianca': linha.get('confianca'),
                'probabilidades': linha.get('probabilidades'),
                'certo': linha['escolha'] == alvo,
            })

    juntar('R1-R3', artefato('r1-r3-estresse.json')['detalhe'], 'alvo',
           lambda l: l['condicao'])
    juntar('R4-R7', [l for l in artefato('r4-r7-limites.json')['detalhe'] if l.get('alvo')],
           'alvo', lambda l: f"{l['rodada']}/{l['condicao']}")
    juntar('R8-R9', artefato('r8-r9-adversarial.json')['detalhe'], 'alvo',
           lambda l: f"{l['rodada']}/{l['condicao']}")
    juntar('R10', artefato('r10-injecao-comparada.json')['detalhe'], 'alvo',
           lambda l: f"{l['comparador']}/{l['condicao']}")
    juntar('R11', artefato('r11-extremos.json')['detalhe'], 'alvo',
           lambda l: f"{l['dimensao']}/{l['nivel']}")
    juntar('R12-R13', artefato('r12-r13-contexto.json')['detalhe'], 'alvo',
           lambda l: l['condicao'])
    juntar('R15', artefato('r15-adversario-externo.json')['detalhe'], 'gold',
           lambda l: f"{l['alvo']}/{l['vetor']}")
    juntar('R19', artefato('r19-armadilha.json')['detalhe'], 'gold',
           lambda l: f"{l['formulacao']}/{l['molde']}")
    return unidas


def apenas_jev(linhas):
    """Tira os comparadores: a R10 e a R15 medem cinco modelos no mesmo arquivo."""
    return [l for l in linhas
            if not (l['rodada'] == 'R10' and not l['condicao'].startswith('jev'))
            and not (l['rodada'] == 'R15' and not l['condicao'].startswith('jev'))]


# ----------------------------------------------------------------- estatística de apoio
def entropia(probabilidades):
    """Entropia de Shannon em bits. Distribuição degenerada dá zero."""
    total = 0.0
    for p in probabilidades.values():
        if p > 0:
            total -= p * math.log2(p)
    return total


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def auc(escores, rotulos):
    """Área sob a curva ROC pelo método de Mann-Whitney, com empate valendo meio ponto."""
    positivos = [e for e, r in zip(escores, rotulos) if r]
    negativos = [e for e, r in zip(escores, rotulos) if not r]
    if not positivos or not negativos:
        return None
    ganhos = 0.0
    negativos_ordenados = sorted(negativos)
    import bisect
    for p in positivos:
        menores = bisect.bisect_left(negativos_ordenados, p)
        iguais = bisect.bisect_right(negativos_ordenados, p) - menores
        ganhos += menores + iguais * 0.5
    return ganhos / (len(positivos) * len(negativos))


def percentil(valores, q):
    if not valores:
        return None
    ordenados = sorted(valores)
    posicao = min(int(q * len(ordenados)), len(ordenados) - 1)
    return ordenados[posicao]


def mediana(valores):
    return percentil(valores, 0.5)


def taxa(acertos, total):
    return acertos / total if total else None
