"""O teste decisivo: a mesma pergunta, com e sem o contexto anterior da conversa.

Se o contexto não melhorar a classificação, o roteamento por prompt está morto neste fluxo de
trabalho — porque a informação que decide não está no texto do pedido, e o hook não tem por
onde buscá-la de graça.

Mede três coisas, na ordem em que elas importam para a aplicação:

1. **Acurácia** contra o gabarito anotado às cegas.
2. **Falso barato**, o erro que estraga: o modelo diz que dá para simplificar e não dava.
3. **Cobertura útil**: quantos pedidos ele consegue mandar para o caminho barato com confiança
   acima do corte. Um classificador perfeito que nunca diz "barato" não economiza nada.

    python avaliacao/com_contexto.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from jev_router import cliente  # noqa: E402

AMOSTRA = RAIZ / 'avaliacao' / 'amostra-com-contexto.json'
GABARITO = RAIZ / 'avaliacao' / 'gabarito-contexto.json'
DESTINO = RAIZ / 'avaliacao' / 'com-contexto.json'

CORTE = 0.99

PERGUNTA = {'alvo': {
    'type': 'choice',
    'instructions': (
        'Leia o pedido abaixo, feito a um assistente de programacao no meio de um trabalho. '
        'O pedido ja diz onde mexer e o que fazer, ou o assistente vai ter que descobrir isso '
        'antes de agir?'),
    'criteria': {
        'ja-diz': ('O pedido nomeia o arquivo, a tela, o texto, a pasta ou o comando, ou pede '
                   'algo que se responde ou se executa direto, sem procurar.'),
        'precisa-descobrir': ('O pedido descreve um sintoma, um objetivo, uma insatisfacao ou '
                              'um assunto amplo, e nao diz onde esta a coisa a ser mexida.'),
    },
}}

MAPA = {'ja-diz': 'barato', 'precisa-descobrir': 'caro'}


def estado_sem(caso):
    return f"Pedido do usuário:\n{caso['pedido']}"


def estado_com(caso):
    return (
        'Conversa anterior, para contexto.\n'
        f"O usuário havia dito: {caso['anterior_usuario']}\n"
        f"O assistente respondeu: {caso['anterior_assistente']}\n\n"
        f"Pedido do usuário agora:\n{caso['pedido']}")


def rodar(amostra, construtor, etiqueta):
    linhas = []
    for caso in amostra:
        respostas, detalhe = cliente.perguntar(construtor(caso), PERGUNTA,
                                               origem=f'com-contexto/{etiqueta}')
        alvo = (respostas or {}).get('alvo') or {}
        linhas.append({'id': caso['id'], 'escolha': alvo.get('choice'),
                       'confianca': alvo.get('confidence'),
                       'erro': None if respostas else (detalhe or {}).get('erro')})
    return linhas


def medir(linhas, gabarito):
    acertos = total = 0
    falso_barato, falso_barato_no_corte, barato_no_corte = [], [], []
    for linha in linhas:
        esperado = gabarito.get(linha['id'])
        if not esperado or not linha['escolha']:
            continue
        total += 1
        obtido = MAPA[linha['escolha']]
        confianca = linha['confianca'] or 0
        if obtido == esperado['esforco']:
            acertos += 1
        elif obtido == 'barato':
            falso_barato.append(linha['id'])
            if confianca >= CORTE:
                falso_barato_no_corte.append(linha['id'])
        if obtido == 'barato' and confianca >= CORTE:
            barato_no_corte.append(linha['id'])
    return {
        'casos': total,
        'acuracia': round(acertos / total, 4) if total else None,
        'falso_barato': falso_barato,
        'falso_barato_acima_do_corte': falso_barato_no_corte,
        'barato_acima_do_corte': barato_no_corte,
        'cobertura_util': round(len(barato_no_corte) / total, 4) if total else None,
        'distribuicao': Counter(l['escolha'] for l in linhas).most_common(),
    }


def main():
    amostra = json.loads(AMOSTRA.read_text(encoding='utf-8'))['amostra']
    gabarito = json.loads(GABARITO.read_text(encoding='utf-8'))['gabarito']

    resultado = {}
    for etiqueta, construtor in (('sem-contexto', estado_sem), ('com-contexto', estado_com)):
        linhas = rodar(amostra, construtor, etiqueta)
        resumo = medir(linhas, gabarito)
        resultado[etiqueta] = {'linhas': linhas, 'resumo': resumo}
        print(f"{etiqueta}: acurácia {resumo['acuracia']:.1%} em {resumo['casos']} casos | "
              f"falso barato {len(resumo['falso_barato'])} "
              f"(acima do corte: {len(resumo['falso_barato_acima_do_corte'])}) | "
              f"cobertura útil {resumo['cobertura_util']:.1%}")

    # Os mesmos casos nos dois braços: a comparação é pareada, como no resto do estudo.
    mudaram = [a['id'] for a, b in zip(resultado['sem-contexto']['linhas'],
                                       resultado['com-contexto']['linhas'])
               if a['escolha'] != b['escolha']]
    resultado['mudaram_com_o_contexto'] = mudaram
    print(f'\npedidos que mudaram de classe ao receber o contexto: {len(mudaram)} '
          f'{mudaram}')

    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
