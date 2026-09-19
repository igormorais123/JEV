"""Linha de comando do roteador, para quem não tem hook: Codex, scripts, ou o próprio agente.

    python -m jev_router.cli "corrigir o typo no README"
    echo "..." | python -m jev_router.cli --stdin --json
    python -m jev_router.cli --situacao

Sai com código 0 sempre que classifica, e com 3 quando não classificou — assim um script pode
distinguir "não há tema" de "o classificador não opinou".
"""
import argparse
import json
import os
import sys

from . import orcamento, politica, roteador


def main(argv=None):
    parser = argparse.ArgumentParser(description='Classifica um pedido antes de gastar modelo caro.')
    parser.add_argument('pedido', nargs='*', help='o pedido a classificar')
    parser.add_argument('--stdin', action='store_true', help='lê o pedido da entrada padrão')
    parser.add_argument('--cwd', default='', help='diretório de trabalho, como contexto')
    parser.add_argument('--json', action='store_true', help='imprime a decisão inteira em JSON')
    parser.add_argument('--sem-cache', action='store_true')
    parser.add_argument('--situacao', action='store_true', help='mostra o gasto do roteador')
    args = parser.parse_args(argv)

    if args.situacao:
        print(json.dumps(orcamento.situacao(), ensure_ascii=False, indent=1))
        print(f'custo máximo por chamada: US$ {orcamento.custo_maximo_por_chamada_usd():.8f}')
        return 0

    pedido = sys.stdin.read() if args.stdin else ' '.join(args.pedido)
    modo = os.environ.get('JEV_ROUTER_MODO', 'sombra').strip().lower()
    decisao = roteador.classificar(pedido, contexto=args.cwd, modo=modo,
                              usar_cache=not args.sem_cache, origem='cli')
    if not decisao:
        print('sem classificação: siga o fluxo normal.', file=sys.stderr)
        return 3
    if args.json:
        print(json.dumps(decisao, ensure_ascii=False, indent=1))
    else:
        nota = politica.texto_para_o_agente(decisao, modo)
        print(nota or f"tema {decisao['tema']} (confiança {decisao['confianca']}): "
                      f"nada a sugerir.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
