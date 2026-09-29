"""Classificação em lote pelo Jev para programas em outra linguagem (Node, PowerShell...).

Entrada (stdin, JSON):  {"perguntas": {...}, "estados": ["texto", ...], "origem": "sala-sentimento",
                         "tempo_total": 60}
Saída (stdout, JSON):   {"respostas": [{...} | null, ...], "custo_usd": 0.0012, "falha": null}

Passa pelo mesmo cliente dos hooks (`camadas.nucleo` → `jev_router.cliente`): redação de
credenciais, teto diário e livro-caixa. Falha para o lado aberto: item sem resposta vem `null`
e quem chama segue com o que já fazia. Nunca imprime chave nem texto no log.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    try:
        pedido = json.loads(sys.stdin.buffer.read().decode('utf-8'))
        perguntas, estados = pedido['perguntas'], [str(e) for e in pedido['estados']]
    except (ValueError, KeyError, TypeError) as erro:
        sys.stdout.write(json.dumps({'respostas': [], 'custo_usd': 0, 'falha': f'entrada inválida: {erro}'}))
        return 2
    from camadas import nucleo
    resultados = nucleo.classificar_em_paralelo(estados, perguntas, origem=str(pedido.get('origem') or 'lote'),
                                                tempo_total=float(pedido.get('tempo_total') or 60))
    resumo = nucleo.resumo_das_chamadas(resultados)
    sys.stdout.buffer.write(json.dumps({'respostas': [r for r, _ in resultados], 'custo_usd': resumo['custo_usd'],
                                        'falha': resumo.get('falha')}, ensure_ascii=False).encode('utf-8'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
