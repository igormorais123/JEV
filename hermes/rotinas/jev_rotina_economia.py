#!/usr/bin/env python3
"""Medição do Jev no Hermes. `--gravar`: regrava o relatório local (diário, silencioso).
`--semanal`: resumo curto para o WhatsApp (segundas às 8h05). Sem modelo principal."""
import sys

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import medir  # noqa: E402


def main():
    medida = medir.medir()
    medir.RELATORIO.write_text(medir.pagina(medida), encoding='utf-8')
    if '--semanal' not in sys.argv:
        return
    s = medida['situacao']
    evitadas = sum(e['agente_evitado'] for e in medida['portoes'].values())
    acordadas = sum(e['agente_acordado'] for e in medida['portoes'].values())
    tokens = f"{medida['tokens_do_modelo_caro_evitados_piso']:,}".replace(',', '.')
    print('🧮 Jev no Hermes — economia acumulada')
    print(f'• Execuções do modelo principal evitadas pelos porteiros: {evitadas} (acordou em {acordadas}).')
    print(f'• Tokens do modelo principal poupados (piso): {tokens}.')
    gasto = f"{s['gasto_mes_usd']:.4f}".replace('.', ',')
    teto = f"{s['teto_mensal_usd']:.2f}".replace('.', ',')
    print(f'• Custo do Jev no mês: US$ {gasto} de US$ {teto}.')
    print(f'• Relatório completo: {medir.RELATORIO}')


if __name__ == '__main__':
    main()
