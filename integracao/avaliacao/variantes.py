"""Testa formulações concorrentes da pergunta de roteamento contra o gabarito do autor.

A primeira formulação, com quatro classes abstratas de esforço, colapsou: 55 de 60 pedidos
reais viraram `investigacao` e o roteador não economizou nada. Antes de concluir que a
aplicação não serve, vale testar a hipótese óbvia — a pergunta estava vaga e pedia ao modelo
um julgamento sobre trabalho futuro, que não está escrito no texto.

As variantes abaixo perguntam sobre o que o texto mostra, e em forma binária, que é onde o
estudo mediu o Jev mais forte (E3, verificação, 95,8%).

    python avaliacao/variantes.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from jev_router import cliente  # noqa: E402

AMOSTRA = RAIZ / 'avaliacao' / 'amostra.json'
GABARITO = RAIZ / 'avaliacao' / 'gabarito-autor.json'
DESTINO = RAIZ / 'avaliacao' / 'variantes.json'

BARATO = ('resposta-direta', 'tarefa-local')

VARIANTES = {
    'B1-alvo-nomeado': {'alvo': {
        'type': 'choice',
        'instructions': (
            'Leia o pedido abaixo, feito a um programador. O pedido ja diz onde mexer, ou o '
            'programador vai ter que descobrir isso primeiro?'),
        'criteria': {
            'ja-diz': ('O pedido nomeia o arquivo, a pasta, a tela, o texto ou o comando em que '
                       'se deve mexer, ou pede algo que se responde sem mexer em nada.'),
            'precisa-descobrir': ('O pedido descreve um sintoma, um objetivo ou um assunto, e '
                                  'nao diz onde esta a coisa a ser mexida.'),
        },
    }},
    'B2-esforco-humano': {'alvo': {
        'type': 'choice',
        'instructions': (
            'Um programador experiente, que ja conhece este projeto, recebeu o pedido abaixo. '
            'Quanto tempo ele leva para atender?'),
        'criteria': {
            'minutos': 'Poucos minutos: e uma resposta, um ajuste pontual ou um comando.',
            'horas': 'Horas ou mais: exige procurar, entender, decidir ou construir.',
        },
    }},
    'B3-continuacao': {'alvo': {
        'type': 'choice',
        'instructions': (
            'O pedido abaixo foi escrito no meio de uma conversa de trabalho com um assistente '
            'de programacao. Ele se explica sozinho?'),
        'criteria': {
            'autossuficiente': ('Da para entender o que fazer lendo so este texto.'),
            'depende-do-anterior': ('Depende do que foi dito antes: e uma continuacao, uma '
                                    'correcao, uma confirmacao ou uma reacao a algo ja em '
                                    'andamento.'),
        },
    }},
}

ESPERADO_BINARIO = {
    'B1-alvo-nomeado': {'ja-diz': 'barato', 'precisa-descobrir': 'caro'},
    'B2-esforco-humano': {'minutos': 'barato', 'horas': 'caro'},
}


def main():
    amostra = json.loads(AMOSTRA.read_text(encoding='utf-8'))['amostra']
    gabarito = json.loads(GABARITO.read_text(encoding='utf-8'))['gabarito']
    resultado = {}

    for nome, perguntas in VARIANTES.items():
        linhas = []
        for caso in amostra:
            estado = f"Pedido do usuário:\n{caso['pedido']}"
            respostas, detalhe = cliente.perguntar(estado, perguntas, origem=f'variante/{nome}')
            escolha = (respostas or {}).get('alvo', {}).get('choice')
            confianca = (respostas or {}).get('alvo', {}).get('confidence')
            linhas.append({'id': caso['id'], 'escolha': escolha, 'confianca': confianca,
                           'erro': None if respostas else (detalhe or {}).get('erro')})
        resultado[nome] = linhas

        if nome in ESPERADO_BINARIO:
            mapa = ESPERADO_BINARIO[nome]
            acertos = total = 0
            falsos_baratos = []   # o modelo diz barato e o gabarito diz caro: o erro que estraga
            for linha in linhas:
                alvo = gabarito.get(linha['id'])
                if not alvo or not linha['escolha']:
                    continue
                verdade = 'barato' if alvo['esforco'] in BARATO else 'caro'
                obtido = mapa.get(linha['escolha'])
                total += 1
                if obtido == verdade:
                    acertos += 1
                elif obtido == 'barato':
                    falsos_baratos.append({'id': linha['id'], 'confianca': linha['confianca']})
            altos = [f for f in falsos_baratos if (f['confianca'] or 0) >= 0.99]
            print(f'{nome}: {acertos}/{total} = {acertos / total:.1%} | '
                  f'disse barato quando era caro: {len(falsos_baratos)} '
                  f'(acima do corte 0,99: {len(altos)})')
            resultado[nome + '/resumo'] = {
                'acuracia': round(acertos / total, 4) if total else None,
                'falsos_baratos': falsos_baratos,
                'falsos_baratos_acima_do_corte': altos,
                'distribuicao': Counter(l['escolha'] for l in linhas).most_common(),
            }
        else:
            print(f'{nome}: {Counter(l["escolha"] for l in linhas).most_common()}')
            resultado[nome + '/resumo'] = {
                'distribuicao': Counter(l['escolha'] for l in linhas).most_common()}

    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\nEscrito em {DESTINO.relative_to(RAIZ)}')


if __name__ == '__main__':
    main()
