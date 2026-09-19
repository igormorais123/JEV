"""Sorteia prompts reais do histórico do Claude Code para avaliar o roteador.

Todo o estudo do Jev foi feito com casos construídos — é o cuidado nº 4 do guia prático. Aqui
o material é real: 13 mil pedidos que o Igor de fato escreveu. A amostra sai ANTES de qualquer
chamada ao Jev, e o gabarito é anotado sobre ela às cegas, para que a anotação não possa ser
influenciada pela resposta do modelo.

    python avaliacao/amostrar.py --n 60
"""
import argparse
import json
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
HISTORICO = Path.home() / '.claude' / 'history.jsonl'
DESTINO = RAIZ / 'avaliacao' / 'amostra.json'
SEMENTE = 20260919


def carregar():
    vistos, pedidos = set(), []
    for linha in HISTORICO.read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            registro = json.loads(linha)
        except ValueError:
            continue
        texto = (registro.get('display') or '').strip()
        # Comandos de barra e pedidos curtos não são roteados pelo hook: ficam de fora da
        # amostra para que ela meça o que o roteador de fato decide.
        if len(texto) < 25 or texto.startswith('/'):
            continue
        marca = texto.lower()
        if marca in vistos:
            continue
        vistos.add(marca)
        pedidos.append({'pedido': texto, 'projeto': registro.get('project')})
    return pedidos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=60)
    args = parser.parse_args()

    pedidos = carregar()
    random.Random(SEMENTE).shuffle(pedidos)
    amostra = [{'id': f'real-{i + 1:03d}', **p} for i, p in enumerate(pedidos[:args.n])]
    DESTINO.write_text(json.dumps(
        {'semente': SEMENTE, 'universo': len(pedidos), 'amostra': amostra},
        ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(amostra)} pedidos sorteados de {len(pedidos)} distintos '
          f'-> {DESTINO.relative_to(RAIZ)}')


if __name__ == '__main__':
    main()
