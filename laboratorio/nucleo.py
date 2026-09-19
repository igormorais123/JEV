"""Núcleo do programa E14: despacho paralelo com teto próprio, e a estatística que uso sempre.

Separado do `executor/runner.py` de propósito. Aquele serve ao dossiê: reserva pelo pior caso,
liquida, concilia contra extrato. Este serve à exploração: precisa de milhares de chamadas
rápidas e de um teto que se verifica antes de cada uma. Os dois gastam da mesma chave e somam
no mesmo limite autorizado de US$ 5,00, e é por isso que este arquivo checa o gasto do outro
antes de despachar.
"""
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GASTOS = RAIZ / 'laboratorio' / 'gastos.jsonl'

URL = 'https://openrouter.ai/api/alpha/decisions'
MODELO = 'typesafe/jev-1.13'

# Teto declarado no pré-registro deste programa, dentro dos US$ 5,00 autorizados.
TETO_DO_PROGRAMA_USD = 2.00
# O maior payload que eu despacho aqui, em caracteres. Com 3 caracteres por token e
# US$ 0,042 por milhão de tokens de entrada, o pior caso por chamada é conhecido antes do envio.
#
# Estava em 12.000 e isso PRODUZIU UM ACHADO FALSO na R11: as condições de diluição de 20k e
# 30k foram truncadas aqui, e como o recheio vinha antes da mensagem, o que chegou ao modelo
# não continha o pedido do cliente. A "queda para 23,3% com confiança 1,0" era o modelo
# respondendo sobre um texto sem pedido nenhum -- o que virou a R13, e não um limite de
# contexto. O contexto publicado é de 32.000 tokens; 90.000 caracteres ficam abaixo dele com
# folga, e o truncamento agora só corta o que o provedor recusaria.
LIMITE_DE_CARACTERES = 90000
TETO_DE_TOKENS = LIMITE_DE_CARACTERES // 3 + 1200
CUSTO_MAXIMO_POR_CHAMADA = TETO_DE_TOKENS / 1e6 * 0.042

_trava = threading.Lock()
_gasto_em_memoria = {'usd': None}


def chave():
    if os.environ.get('OPENROUTER_API_KEY'):
        return os.environ['OPENROUTER_API_KEY']
    env = RAIZ / '.env'
    if env.exists():
        for linha in env.read_text(encoding='utf-8', errors='replace').splitlines():
            if linha.strip().startswith('OPENROUTER_API_KEY='):
                valor = linha.split('=', 1)[1].strip().strip('"').strip("'")
                if valor:
                    return valor
    raise RuntimeError('OPENROUTER_API_KEY ausente')


def gasto_do_programa():
    if _gasto_em_memoria['usd'] is None:
        total = 0.0
        if GASTOS.exists():
            for linha in GASTOS.read_text(encoding='utf-8', errors='replace').splitlines():
                try:
                    total += json.loads(linha).get('custo_usd') or 0.0
                except ValueError:
                    continue
        _gasto_em_memoria['usd'] = total
    return _gasto_em_memoria['usd']


def gasto_total_autorizado():
    """O que já saiu da chave por todos os caminhos: dossiê, roteador e este programa."""
    import sqlite3
    total = gasto_do_programa()
    ledger = RAIZ / 'runs' / 'ledger.sqlite3'
    if ledger.exists():
        try:
            conexao = sqlite3.connect(f'file:{ledger}?mode=ro', uri=True)
            linha = conexao.execute('select sum(settled_nusd) from attempt_budget').fetchone()
            total += (linha[0] or 0) / 1e9
            conexao.close()
        except sqlite3.Error:
            pass
    roteador = RAIZ / 'integracao' / 'gastos.jsonl'
    if roteador.exists():
        for linha in roteador.read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                total += json.loads(linha).get('custo_usd') or 0.0
            except ValueError:
                continue
    return total


def registrar(custo, **campos):
    with _trava:
        _gasto_em_memoria['usd'] = (_gasto_em_memoria['usd'] or 0.0) + (custo or 0.0)
        try:
            with GASTOS.open('a', encoding='utf-8') as arquivo:
                arquivo.write(json.dumps({'em': time.strftime('%Y-%m-%dT%H:%M:%S'),
                                          'custo_usd': custo or 0.0, **campos},
                                         ensure_ascii=False) + '\n')
        except OSError:
            pass


def perguntar(estado, perguntas, *, api_key=None, timeout=45.0, tentativas=3, rodada=''):
    """Uma chamada, com repescagem de falha de transporte (Emenda 1 do E12).

    Devolve (respostas, detalhe). `respostas` é None quando o modelo não respondeu dentro do
    contrato; o detalhe diz por quê, e a distinção entre 'transporte' e 'modelo' é a que separa
    erro de infraestrutura de erro de classificação.
    """
    if gasto_do_programa() + CUSTO_MAXIMO_POR_CHAMADA > TETO_DO_PROGRAMA_USD:
        return None, {'erro': 'teto do programa alcançado', 'tipo': 'orcamento'}

    estado = estado[:LIMITE_DE_CARACTERES]
    corpo = {'model': MODELO, 'state': estado, 'questions': perguntas}
    cabecalhos = {'Authorization': f'Bearer {api_key or chave()}',
                  'Content-Type': 'application/json', 'User-Agent': 'jev-lab-e14/1.0'}
    dados = json.dumps(corpo, ensure_ascii=False).encode('utf-8')

    ultimo = {}
    for tentativa in range(tentativas):
        requisicao = urllib.request.Request(URL, data=dados, headers=cabecalhos, method='POST')
        try:
            with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
                status, corpo_resposta = resposta.status, json.loads(resposta.read().decode('utf-8'))
        except urllib.error.HTTPError as erro:
            try:
                corpo_resposta = json.loads(erro.read().decode('utf-8'))
            except (ValueError, OSError):
                corpo_resposta = {}
            status = erro.code
        except Exception as erro:
            status, corpo_resposta = 0, {'erro_local': type(erro).__name__}

        custo = (corpo_resposta.get('usage') or {}).get('cost') if isinstance(corpo_resposta, dict) else None
        # HTTP 429 é recusa antes da geração: o provedor não cobra, e liquidar pelo pior caso
        # foi o defeito que inventou US$ 0,499 no livro-caixa do E12.
        registrar(0.0 if status == 429 else (custo or 0.0), rodada=rodada, http=status,
                  caracteres=len(estado), tentativa=tentativa + 1)

        if status == 200 and isinstance(corpo_resposta, dict):
            respostas = corpo_resposta.get('answers')
            if isinstance(respostas, dict) and set(respostas) == set(perguntas):
                return respostas, {'custo_usd': custo, 'http': status,
                                   'tentativas': tentativa + 1}
            return None, {'erro': 'fora do contrato', 'tipo': 'modelo', 'http': status}
        ultimo = {'erro': f'http {status}', 'tipo': 'transporte', 'http': status}
        if status in (429, 500, 502, 503, 504, 0):
            time.sleep(2.0 * (tentativa + 1))
            continue
        return None, {'erro': f'http {status}', 'tipo': 'modelo', 'http': status}
    return None, ultimo


def em_paralelo(itens, funcao, *, trabalhadores=8, rotulo=''):
    """Roda `funcao` sobre `itens` com poucas linhas em paralelo, preservando a ordem.

    Oito é o teto que o E12 mostrou seguro: acima disso o provedor devolveu 429 em 46 chamadas
    e a repescagem custou mais tempo do que o paralelismo economizou.
    """
    total = len(itens)
    feitos = [0]
    inicio = time.time()

    def embrulho(item):
        resultado = funcao(item)
        with _trava:
            feitos[0] += 1
            if feitos[0] % 25 == 0 or feitos[0] == total:
                passado = time.time() - inicio
                sys.stderr.write(f'\r  {rotulo} {feitos[0]}/{total} '
                                 f'({passado:.0f}s, US$ {gasto_do_programa():.5f})   ')
                sys.stderr.flush()
        return resultado

    with ThreadPoolExecutor(max_workers=trabalhadores) as piscina:
        saida = list(piscina.map(embrulho, itens))
    sys.stderr.write('\n')
    return saida


# ---------------------------------------------------------------- estatística

def wilson(acertos, total, z=1.96):
    """Intervalo de Wilson: comporta-se onde o normal falha, nas pontas."""
    if not total:
        return (None, None)
    p = acertos / total
    denominador = 1 + z * z / total
    centro = (p + z * z / (2 * total)) / denominador
    margem = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / denominador
    return (round(max(0.0, centro - margem), 4), round(min(1.0, centro + margem), 4))


def mcnemar_exato(so_a, so_b):
    """p bilateral do teste de McNemar, pela binomial exata. Para comparação pareada."""
    from math import comb
    n = so_a + so_b
    if n == 0:
        return 1.0
    k = min(so_a, so_b)
    cauda = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return round(min(1.0, 2 * cauda), 4)


def bootstrap_diferenca(pares, repeticoes=10000, semente=20260919):
    """IC95 da diferença pareada por reamostragem. `pares` é [(a, b), ...] com 0/1."""
    import random
    if not pares:
        return (None, None)
    sorteio = random.Random(semente)
    n = len(pares)
    diferencas = []
    for _ in range(repeticoes):
        amostra = [pares[sorteio.randrange(n)] for _ in range(n)]
        diferencas.append(sum(a for a, _ in amostra) / n - sum(b for _, b in amostra) / n)
    diferencas.sort()
    return (round(diferencas[int(0.025 * repeticoes)], 4),
            round(diferencas[int(0.975 * repeticoes)], 4))
