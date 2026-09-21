"""Atualiza os números de contabilidade do guia para o que o livro-caixa registra agora.

A auditoria confere chamadas e custo declarados contra o livro-caixa **por igualdade exata**, de
propósito: quem gasta atualiza o número, ou a suíte quebra. Isso é a disciplina certa e cria uma
tarefa mecânica depois de toda rodada paga. Este programa faz a tarefa mecânica — ele não afrouxa
a conferência, só evita que ela seja resolvida na mão e com erro de digitação.

Desde que os hooks do Claude Code gastam a toda hora, a igualdade é contra o **instantâneo**
que este programa grava em `runs/caixa-conciliado.json` (ver `laboratorio/caixa.py`): os
geradores de página e a auditoria leem dele, e a auditoria confere que ele é recente.

    python laboratorio/conciliar_caixa.py          # mostra o que mudaria
    python laboratorio/conciliar_caixa.py --gravar # grava
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:  # rodado como script, o pacote laboratorio precisa estar no caminho
    sys.path.insert(0, str(RAIZ))
GUIA = RAIZ / 'docs' / 'GUIA-PRATICO-JEV.md'


def livro_caixa():
    from laboratorio import caixa
    dado = caixa.ao_vivo()
    return dado['chamadas'], dado['usd']


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
        if '--gravar' in sys.argv:
            from laboratorio import caixa
            caixa.gravar_instantaneo()
        print(f'nada a mudar: o guia já declara {mil} chamadas e US$ {usd}')
        return 0
    print(f'guia passa a declarar {mil} chamadas e US$ {usd} '
          f'(restam US$ {5 - gasto:.4f} do teto)')
    if '--gravar' in sys.argv:
        from laboratorio import caixa
        instantaneo = caixa.gravar_instantaneo()
        # O guia declara exatamente o instantâneo, nunca uma leitura posterior do SQLite.
        mil = f"{instantaneo['chamadas']:,}".replace(',', '.')
        usd = f"{instantaneo['usd']:.4f}".replace('.', ',')
        novo = re.sub(r'[\d.]+ chamadas reais \| US\$ [\d,]+ \(',
                      f'{mil} chamadas reais | US$ {usd} (', texto, count=1)
        novo = re.sub(r'[\d.]+(\s+)chamadas reais, US\$ [\d,]+(\s+)pelo',
                      lambda m: f'{mil}{m.group(1)}chamadas reais, US$ {usd}{m.group(2)}pelo',
                      novo, count=1)
        GUIA.write_text(novo, encoding='utf-8')
        print('gravado')
    else:
        print('use --gravar para aplicar')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
