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
    acordadas = sum(e['agente_acordado'] for e in medida['portoes'].values())
    cache = medida.get('cache_do_modelo_principal') or {}
    print('🧮 Jev no Hermes — economia acumulada')
    print(f"• Turnos do modelo principal evitados pelos porteiros: {medida['turnos_evitados']} "
          f'(acordou em {acordadas}) — é a economia que se paga cheia.')
    print(f"• Entrada poupada pelos recortes: {medir.mil(medida['entrada_evitada_pelos_recortes'])} tokens"
          + (f" (mas {cache['parte_em_cache'] * 100:.0f}% da entrada já vinha do cache: vale janela e "
             'latência, não cota).' if cache.get('parte_em_cache') is not None else '.'))
    gasto = f"{s['gasto_mes_usd']:.4f}".replace('.', ',')
    teto = f"{s['teto_mensal_usd']:.2f}".replace('.', ',')
    print(f'• Custo do Jev no mês: US$ {gasto} de US$ {teto}.')
    print(f'• Relatório completo: {medir.RELATORIO}')


if __name__ == '__main__':
    main()
