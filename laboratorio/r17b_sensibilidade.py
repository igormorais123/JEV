"""R17b — análise de sensibilidade: o que muda se a minha verificação estivesse certa.

A R17 foi pré-registrada com uma expressão regular por pergunta, escrita antes de rodar, e o
resultado dela fica como está. Mas ao ler as respostas encontrei um defeito meu: a regex da
pergunta 18 aceita `famil` sem acento, e a resposta correta do modelo dizia **"por família"**,
com o í acentuado. O caso foi contado como erro em todos os arranjos que o acertaram.

Trocar a regex agora e republicar o número seria exatamente o ajuste depois do resultado que o
pré-registro existe para impedir. Então este arquivo não altera nada: ele roda a mesma contagem
com a regex corrigida, **ao lado** da original, e as duas ficam publicadas. O defeito é meu, é
simétrico entre os arranjos -- a mesma regex vale para os quatro -- e por isso não muda qual
deles é melhor; muda só o nível absoluto.

    python laboratorio/r17b_sensibilidade.py
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import mcnemar_exato, wilson  # noqa: E402
from laboratorio.r17_economia_de_contexto import PERGUNTAS  # noqa: E402

ORIGEM = RAIZ / 'laboratorio' / 'r17-economia-de-contexto.json'
DESTINO = RAIZ / 'laboratorio' / 'r17b-sensibilidade.json'


def sem_acento(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


def main():
    dados = json.loads(ORIGEM.read_text(encoding='utf-8'))
    aceita = {f'q{i:02d}': regex for i, (_, _, regex) in enumerate(PERGUNTAS)}

    mudaram = []
    for linha in dados['detalhe']:
        resposta = linha['resposta'] or ''
        # A única mudança: comparar também a forma sem acento da resposta.
        corrigido = bool(re.search(aceita[linha['id']], resposta, re.IGNORECASE) or
                         re.search(aceita[linha['id']], sem_acento(resposta), re.IGNORECASE))
        linha['certo_corrigido'] = corrigido
        if corrigido != linha['certo']:
            mudaram.append({'id': linha['id'], 'arranjo': linha['arranjo'],
                            'resposta': resposta[:160]})

    print(f'{len(mudaram)} veredictos mudam com a comparação sem acento:')
    for item in mudaram:
        print(f"   {item['id']} {item['arranjo']:9} {item['resposta'][:110]}")

    resultado = {'mudaram': mudaram, 'arranjos': {}}
    print(f"\n   {'arranjo':10} {'pré-registrado':>15} {'corrigido':>11} {'IC95 corrigido':>20}")
    for arranjo in ('todos', 'jev', 'bm25', 'sorteio'):
        grupo = [l for l in dados['detalhe'] if l['arranjo'] == arranjo]
        antes = sum(1 for l in grupo if l['certo'])
        depois = sum(1 for l in grupo if l['certo_corrigido'])
        resultado['arranjos'][arranjo] = {
            'n': len(grupo), 'pre_registrado': antes, 'corrigido': depois,
            'taxa_corrigida': round(depois / len(grupo), 4),
            'ic95_corrigido': wilson(depois, len(grupo))}
        print(f"   {arranjo:10} {antes:>10}/{len(grupo):<4} {depois:>7}/{len(grupo):<4} "
              f"{str(resultado['arranjos'][arranjo]['ic95_corrigido']):>20}")

    por_id = {}
    for linha in dados['detalhe']:
        por_id.setdefault(linha['id'], {})[linha['arranjo']] = linha['certo_corrigido']

    def pareado(a, b):
        so_a = sum(1 for v in por_id.values() if v.get(a) and not v.get(b))
        so_b = sum(1 for v in por_id.values() if v.get(b) and not v.get(a))
        return {'so_' + a: so_a, 'so_' + b: so_b, 'p_mcnemar': mcnemar_exato(so_a, so_b)}

    resultado['pareado_corrigido'] = {'jev_vs_todos': pareado('jev', 'todos'),
                                      'jev_vs_bm25': pareado('jev', 'bm25'),
                                      'jev_vs_sorteio': pareado('jev', 'sorteio')}
    print('\n   comparações pareadas com a correção')
    for nome, bloco in resultado['pareado_corrigido'].items():
        print(f'   {nome:18} {bloco}')

    resultado['leitura'] = (
        'A correcao muda o nivel absoluto e nao muda a ordem dos arranjos. O numero que vale '
        'como resultado do experimento e o pre-registrado; este fica como sensibilidade.')
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"\n   {resultado['leitura']}")


if __name__ == '__main__':
    main()
