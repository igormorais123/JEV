"""Tabela de precos e custo em nanodolares inteiros.

Provedores publicam preco por milhao de tokens. Dividir em ponto flutuante
introduz erro de arredondamento que pode subestimar gasto, entao toda conversao
usa inteiros com arredondamento para cima.
"""
import json
from pathlib import Path

NUSD_PER_USD = 1_000_000_000
PRICES_PATH = Path(__file__).resolve().parent / 'prices.json'


class PricingError(Exception):
    """Preco ausente, incompleto ou sem limite verificavel."""


def load_prices(path=None):
    source = Path(path) if path else PRICES_PATH
    data = json.loads(source.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise PricingError('Versao de tabela de precos nao suportada')
    if not isinstance(data.get('models'), dict):
        raise PricingError('Tabela de precos sem secao models')
    return data


def snapshot_id(prices):
    return prices['snapshot_id']


def entry(prices, provider, model):
    found = prices['models'].get(f'{provider}:{model}')
    if not found:
        raise PricingError(f'Sem preco publicado para {provider}:{model}')
    for field in ('input_nusd_per_million_tokens', 'output_nusd_per_million_tokens'):
        value = found.get(field)
        if not isinstance(value, int) or value < 0:
            raise PricingError(f'Preco invalido em {provider}:{model}.{field}')
    taxa = found.get('request_surcharge_nusd', 0)
    if not isinstance(taxa, int) or taxa < 0:
        raise PricingError(f'request_surcharge_nusd invalido em {provider}:{model}: precisa ser inteiro >= 0')
    return found


def _ceil_div(numerator, denominator):
    return -(-numerator // denominator)


def _cost(price, input_tokens, output_tokens):
    total = _ceil_div(input_tokens * price['input_nusd_per_million_tokens'], 1_000_000)
    total += _ceil_div(output_tokens * price['output_nusd_per_million_tokens'], 1_000_000)
    return total + int(price.get('request_surcharge_nusd', 0))


def worst_case_nusd(prices, provider, model, max_input_tokens, max_output_tokens):
    """Teto de custo da tentativa. Sem limite de tokens declarado nao ha teto verificavel."""
    price = entry(prices, provider, model)
    for name, value in (('max_input_tokens', max_input_tokens), ('max_output_tokens', max_output_tokens)):
        if not isinstance(value, int) or value <= 0:
            raise PricingError(f'{name} precisa ser inteiro positivo para calcular o pior caso')
    return _cost(price, max_input_tokens, max_output_tokens)


def observed_nusd(prices, provider, model, input_tokens, output_tokens):
    """Custo observado a partir do usage; arredonda para cima e nunca subestima."""
    price = entry(prices, provider, model)
    for name, value in (('input_tokens', input_tokens), ('output_tokens', output_tokens)):
        if not isinstance(value, int) or value < 0:
            raise PricingError(f'{name} invalido no usage')
    return _cost(price, input_tokens, output_tokens)


def usd_to_nusd(value_usd):
    """Converte USD para nanodolares, arredondando para cima.

    Um float que veio de json.loads ja perdeu exatidao antes de chegar aqui; Decimal(float)
    preserva o valor binario real em vez de reintroduzir erro pelo str(). Texto e int seguem
    pelo caminho exato.
    """
    from decimal import Decimal, ROUND_CEILING
    if isinstance(value_usd, float):
        bruto = Decimal(value_usd)
    else:
        bruto = Decimal(str(value_usd))
    return int((bruto * NUSD_PER_USD).to_integral_value(rounding=ROUND_CEILING))
