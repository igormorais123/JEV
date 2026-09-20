"""Controle persistente de gasto do roteador, separado do livro-caixa dos experimentos.

O livro-caixa de `executor/ledger.py` reserva pelo pior caso e serve para experimento: cada
chamada abre transação em SQLite. Um hook roda em toda mensagem, às vezes em duas sessões ao
mesmo tempo, e não pode travar num lock de banco. Aqui o registro é um JSONL de acréscimo, que
não bloqueia, e o teto é verificado antes de cada envio.

O custo máximo por chamada é conhecido antes de enviar, e não estimado: a entrada é truncada em
`LIMITE_DE_CARACTERES` e o preço de saída do `typesafe/jev-1.13` é zero.
"""
import json
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / 'gastos.jsonl'

# Preço publicado em executor/prices.json, em USD por milhão de tokens.
USD_POR_MILHAO_DE_ENTRADA = 0.042
USD_POR_MILHAO_DE_SAIDA = 0.0

LIMITE_DE_CARACTERES = 4000
# Três caracteres por token é a razão conservadora usada no runner do estudo.
TETO_DE_TOKENS_POR_CHAMADA = LIMITE_DE_CARACTERES // 3 + 700  # + as instruções fixas

# Era US$ 0,05 (~3.500 roteamentos). Com as camadas de leitura, busca e sentinela, um dia de
# trabalho pesado classifica alguns milhares de trechos; o teto sobe para US$ 0,20 e o
# acumulado continua em US$ 1,00, dentro do teto de US$ 5,00 autorizado para o projeto.
TETO_DIARIO_USD = 0.20
TETO_ACUMULADO_USD = 1.00


def custo_maximo_por_chamada_usd(caracteres=LIMITE_DE_CARACTERES):
    """Pior caso conhecido ANTES do envio, para a entrada truncada em `caracteres`."""
    tokens = caracteres // 3 + 700
    return tokens / 1e6 * USD_POR_MILHAO_DE_ENTRADA


def _linhas():
    if not REGISTRO.exists():
        return []
    saida = []
    for linha in REGISTRO.read_text(encoding='utf-8', errors='replace').splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            saida.append(json.loads(linha))
        except ValueError:
            continue
    return saida


def situacao():
    hoje = date.today().isoformat()
    linhas = _linhas()
    gasto_hoje = sum(r.get('custo_usd', 0.0) for r in linhas if r.get('dia') == hoje)
    return {
        'dia': hoje,
        'chamadas_hoje': sum(1 for r in linhas if r.get('dia') == hoje),
        'gasto_hoje_usd': gasto_hoje,
        'gasto_total_usd': sum(r.get('custo_usd', 0.0) for r in linhas),
        'chamadas_total': len(linhas),
        'teto_diario_usd': TETO_DIARIO_USD,
        'teto_acumulado_usd': TETO_ACUMULADO_USD,
    }


def pode_gastar(caracteres=LIMITE_DE_CARACTERES):
    """Devolve (permitido, motivo). Verificado ANTES de qualquer envio."""
    s = situacao()
    maximo = custo_maximo_por_chamada_usd(caracteres)
    if s['gasto_hoje_usd'] + maximo > TETO_DIARIO_USD:
        return False, f"teto diário de US$ {TETO_DIARIO_USD:.2f} alcançado"
    if s['gasto_total_usd'] + maximo > TETO_ACUMULADO_USD:
        return False, f"teto acumulado de US$ {TETO_ACUMULADO_USD:.2f} alcançado"
    return True, 'dentro do teto'


def registrar(custo_usd, **campos):
    """Acréscimo de uma linha. Falha aqui nunca derruba o fluxo de quem chamou."""
    linha = {'dia': date.today().isoformat(), 'em': time.strftime('%Y-%m-%dT%H:%M:%S'),
             'custo_usd': float(custo_usd or 0.0), **campos}
    try:
        with REGISTRO.open('a', encoding='utf-8') as arquivo:
            arquivo.write(json.dumps(linha, ensure_ascii=False) + '\n')
    except OSError:
        pass
    return linha
