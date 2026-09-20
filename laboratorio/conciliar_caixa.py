"""Atualiza os números de contabilidade do guia para o que o livro-caixa registra agora.

A auditoria confere chamadas e custo declarados contra o livro-caixa **por igualdade exata**, de
propósito: quem gasta atualiza o número, ou a suíte quebra. Isso é a disciplina certa e cria uma
tarefa mecânica depois de toda rodada paga. Este programa faz a tarefa mecânica — ele não afrouxa
a conferência, só evita que ela seja resolvida na mão e com erro de digitação.

    python laboratorio/conciliar_caixa.py          # mostra o que mudaria
    python laboratorio/conciliar_caixa.py --gravar # grava
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GUIA = RAIZ / 'docs' / 'GUIA-PRATICO-JEV.md'


def livro_caixa():
    conexao = sqlite3.connect(f"file:{RAIZ / 'runs' / 'ledger.sqlite3'}?mode=ro", uri=True)
    chamadas, gasto = conexao.execute(
        'select count(*), sum(settled_nusd) from attempt_budget').fetchone()
    conexao.close()
    return chamadas, (gasto or 0) / 1e9


def main():
    chamadas, gasto = livro_caixa()
    if gasto > 5.0:
        raise SystemExit(f'PARE: o livro-caixa registra US$ {gasto:.4f}, acima do teto '
                         f'autorizado de US$ 5,00. Nada foi gravado.')
    mil = f'{chamadas:,}'.replace(',', '.')
    usd = f'{gasto:.4f}'.replace('.', ',')

    texto = GUIA.read_text(encoding='utf-8')
    novo = re.sub(r'[\d.]+ chamadas reais \| US\$ [\d,]+ \(',
                  f'{mil} chamadas reais | US$ {usd} (', texto, count=1)
    novo = re.sub(r'[\d.]+(\s+)chamadas reais, US\$ [\d,]+(\s+)pelo',
                  lambda m: f'{mil}{m.group(1)}chamadas reais, US$ {usd}{m.group(2)}pelo',
                  novo, count=1)

    if novo == texto:
        print(f'nada a mudar: o guia já declara {mil} chamadas e US$ {usd}')
        return 0
    print(f'guia passa a declarar {mil} chamadas e US$ {usd} '
          f'(restam US$ {5 - gasto:.4f} do teto)')
    if '--gravar' in sys.argv:
        GUIA.write_text(novo, encoding='utf-8')
        print('gravado')
    else:
        print('use --gravar para aplicar')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
