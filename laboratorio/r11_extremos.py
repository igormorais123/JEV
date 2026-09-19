"""R11 — a varredura dos extremos: onde exatamente o Jev quebra.

Tudo que medi até aqui ficou acima de 90%, e medir onde o instrumento funciona não diz qual é a
margem dele. Esta rodada empurra seis dimensões até o ponto de ruptura, uma de cada vez, sobre
o mesmo corpus, para que a queda seja atribuível à dimensão. O produto não é uma acurácia: é um
**mapa de limites** — para cada dimensão, o nível em que a acurácia cai abaixo de 90%, de 75% e
de 50%.

As seis dimensões, e por que cada uma:

1. `opcoes`     — R6 mostrou queda em 20 e 40. Até onde vai? 80 e 160 classes.
2. `ruido`      — R3 mediu 5% e 15%. Aqui 30%, 50% e 70%: texto quase ilegível.
3. `diluicao`   — encher o `state` de texto irrelevante até perto do contexto publicado (32k).
4. `sobreposicao` — critérios que se sobrepõem de propósito. Testa se o gargalo é o modelo ou a
   definição das classes, que é a suspeita do guia desde o passo 1.
5. `idioma`     — instrução e texto em inglês, em português sem acento, e misturados.
6. `instrucao`  — instrução completa, curta, vazia e **contraditória**.

    python laboratorio/r11_extremos.py
"""
import json
import random
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor.run_e12_replicacao import CRITERIOS, INSTRUCOES  # noqa: E402
from laboratorio.nucleo import em_paralelo, perguntar, wilson  # noqa: E402
from laboratorio.r1_r3_estresse import DISTRATORES, com_erro  # noqa: E402
from laboratorio.r4_r7_limites import MAIS_DISTRATORES  # noqa: E402

CORPUS = RAIZ / 'data' / 'corpus' / 'triagem-replicacao.jsonl'
DESTINO = RAIZ / 'laboratorio' / 'r11-extremos.json'
SEMENTE = 20260919
N_CASOS = 30  # um terço do corpus, sorteado com semente: mapa de limites não precisa de 90

# --------------------------------------------------------------- dimensão: opções

SETORES = ['financeiro', 'logistica', 'tecnico', 'comercial', 'juridico', 'ouvidoria',
           'retencao', 'cadastro', 'fidelidade', 'parcerias']
VERBOS = ['solicitar', 'revisar', 'confirmar', 'suspender', 'reativar', 'transferir',
          'auditar', 'antecipar', 'prorrogar', 'validar']


def distratores_em_massa(quantos):
    """Distratores plausíveis gerados por combinação. Nenhum colide com as cinco classes reais."""
    saida = {}
    for setor in SETORES:
        for verbo in VERBOS:
            if len(saida) >= quantos:
                return saida
            saida[f'{verbo}-{setor}'] = (f'O remetente pede {verbo} algo junto ao setor de '
                                         f'{setor}, sem pedir nenhuma das acoes principais.')
    return saida


def criterios_com(n):
    tudo = dict(CRITERIOS)
    for fonte in (DISTRATORES, MAIS_DISTRATORES, distratores_em_massa(n)):
        for chave, valor in fonte.items():
            if len(tudo) >= n:
                return tudo
            tudo.setdefault(chave, valor)
    return tudo


# --------------------------------------------------------------- dimensão: sobreposição

# Critérios escritos para se sobreporem de propósito, mantendo os mesmos cinco rótulos. Se a
# acurácia cair aqui e não nas outras dimensões, o gargalo é a definição das classes.
SOBREPOSTO_PARCIAL = {
    'cancelar': 'O remetente quer interromper algo, ou reduzir o que contratou, ou sair.',
    'rastrear': 'O remetente quer saber de status, prazo, andamento ou posicao de qualquer coisa.',
    'trocar': 'O remetente quer que algo seja substituido, corrigido, devolvido ou refeito.',
    'cobranca': 'O remetente fala de valores, de dinheiro devolvido, de documento de pagamento ou de prazo.',
    'informacao': 'O remetente quer saber alguma coisa, ou esclarecer algo, ou entender uma regra.',
}
SOBREPOSTO_TOTAL = {
    'cancelar': 'O remetente entrou em contato para tratar de um assunto do seu pedido ou contrato.',
    'rastrear': 'O remetente entrou em contato para tratar de um assunto do seu pedido ou contrato.',
    'trocar': 'O remetente entrou em contato para tratar de um assunto do seu pedido ou contrato.',
    'cobranca': 'O remetente entrou em contato para tratar de um assunto do seu pedido ou contrato.',
    'informacao': 'O remetente entrou em contato para tratar de um assunto do seu pedido ou contrato.',
}

# --------------------------------------------------------------- dimensão: idioma

CRITERIOS_EN = {
    'cancelar': 'The sender asks to end, cancel or give up an order, service or contract.',
    'rastrear': 'The sender asks where the delivery is, when it arrives, or its status.',
    'trocar': 'The sender asks for an exchange, a replacement, a repair or warranty service.',
    'cobranca': 'The sender asks for a duplicate bill, a refund, an installment plan, or disputes a charge.',
    'informacao': 'The sender only asks for clarification or data, without requesting any action above.',
}
INSTRUCOES_EN = ('Classify the action the sender requests in the message. What counts is the '
                 'requested action, not the topic mentioned. An action quoted as a third '
                 "party's speech, denied, conditional or already completed is not the requested "
                 'action.')

# --------------------------------------------------------------- dimensão: instrução

INSTRUCAO_CURTA = 'Classifique a mensagem.'
INSTRUCAO_VAZIA = ''
INSTRUCAO_CONTRADITORIA = ('Classifique a acao que o remetente pede. Considere sempre a acao '
                           'citada no texto, mesmo quando ela for negada, condicional, de '
                           'terceiro ou ja concluida. Ao mesmo tempo, ignore acoes negadas, '
                           'condicionais, de terceiro ou ja concluidas.')

RECHEIO = (
    'Politica interna de atendimento, secao {n}. O colaborador deve registrar o protocolo no '
    'sistema antes de encerrar o contato, conferir os dados cadastrais do cliente, verificar a '
    'existencia de pendencias financeiras e anotar o resumo no campo proprio. O tempo medio de '
    'atendimento deve ser monitorado semanalmente pelo supervisor da celula, que reporta ao '
    'gerente regional. Feriados municipais seguem o calendario publicado no portal do '
    'colaborador. Equipamentos de uso pessoal nao devem ser utilizados durante o expediente. '
)


def diluir(texto, caracteres):
    """Enche o estado de texto irrelevante ANTES da mensagem, como um contexto real faria."""
    if not caracteres:
        return texto
    partes, tamanho = [], 0
    n = 0
    while tamanho < caracteres:
        n += 1
        pedaco = RECHEIO.format(n=n)
        partes.append(pedaco)
        tamanho += len(pedaco)
    return ''.join(partes)[:caracteres] + '\n\n' + texto


def sem_acento(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')


# --------------------------------------------------------------- montagem

def corpus():
    casos = [json.loads(linha) for linha in
             CORPUS.read_text(encoding='utf-8').splitlines() if linha.strip()]
    sorteio = random.Random(SEMENTE)
    sorteio.shuffle(casos)
    return casos[:N_CASOS]


def condicoes():
    """(dimensão, nível, função que monta a chamada a partir do caso)."""
    sorteio = random.Random(SEMENTE)
    lista = [('referencia', 'base', 0,
              lambda c: (c['text'], dict(CRITERIOS), INSTRUCOES))]

    for n in (40, 80, 160):
        criterios = criterios_com(n)
        lista.append(('opcoes', f'{len(criterios)}', len(criterios),
                      lambda c, k=criterios: (c['text'], dict(k), INSTRUCOES)))

    for taxa in (0.30, 0.50, 0.70):
        lista.append(('ruido', f'{int(taxa * 100)}%', taxa,
                      lambda c, t=taxa: (com_erro(c['text'], t, sorteio), dict(CRITERIOS),
                                         INSTRUCOES)))

    for tamanho in (2000, 8000, 20000, 30000):
        lista.append(('diluicao', f'{tamanho // 1000}k', tamanho,
                      lambda c, t=tamanho: (diluir(c['text'], t), dict(CRITERIOS), INSTRUCOES)))

    lista.append(('sobreposicao', 'parcial', 1,
                  lambda c: (c['text'], dict(SOBREPOSTO_PARCIAL), INSTRUCOES)))
    lista.append(('sobreposicao', 'total', 2,
                  lambda c: (c['text'], dict(SOBREPOSTO_TOTAL), INSTRUCOES)))

    lista.append(('idioma', 'ingles', 1,
                  lambda c: (c['text'], dict(CRITERIOS_EN), INSTRUCOES_EN)))
    lista.append(('idioma', 'misto', 2,
                  lambda c: (c['text'], dict(CRITERIOS_EN), INSTRUCOES)))
    lista.append(('idioma', 'sem-acento', 3,
                  lambda c: (sem_acento(c['text']),
                             {k: sem_acento(v) for k, v in CRITERIOS.items()},
                             sem_acento(INSTRUCOES))))

    lista.append(('instrucao', 'curta', 1,
                  lambda c: (c['text'], dict(CRITERIOS), INSTRUCAO_CURTA)))
    lista.append(('instrucao', 'vazia', 2,
                  lambda c: (c['text'], dict(CRITERIOS), INSTRUCAO_VAZIA)))
    lista.append(('instrucao', 'contraditoria', 3,
                  lambda c: (c['text'], dict(CRITERIOS), INSTRUCAO_CONTRADITORIA)))

    # O extremo dos extremos: tudo junto, para ver se as degradações se somam ou se multiplicam.
    lista.append(('combinado', 'ruido50+160opcoes+8k', 99,
                  lambda c: (diluir(com_erro(c['text'], 0.50, sorteio), 8000),
                             criterios_com(160), INSTRUCOES)))
    return lista


def executar(tarefa):
    texto, criterios, instrucao = tarefa['montar'](tarefa['caso'])
    pergunta = {'type': 'choice', 'criteria': criterios}
    if instrucao:
        pergunta['instructions'] = instrucao
    respostas, detalhe = perguntar(f"Mensagem do cliente:\n{texto}", {'acao': pergunta},
                                   rodada='R11')
    alvo = (respostas or {}).get('acao') or {}
    return {'dimensao': tarefa['dimensao'], 'nivel': tarefa['nivel'],
            'ordem': tarefa['ordem'], 'case_id': tarefa['caso']['case_id'],
            'alvo': tarefa['caso']['gold'], 'escolha': alvo.get('choice'),
            'confianca': alvo.get('confidence'),
            'erro': None if respostas else (detalhe or {}).get('erro'),
            'tipo_de_falha': None if respostas else (detalhe or {}).get('tipo')}


def resumo(linhas):
    validas = [l for l in linhas if l['escolha']]
    certos = [l for l in validas if l['escolha'] == l['alvo']]
    errados = [l for l in validas if l['escolha'] != l['alvo']]
    return {'n': len(validas), 'sem_resposta': len(linhas) - len(validas),
            'acuracia': round(len(certos) / len(validas), 4) if validas else None,
            'ic95': wilson(len(certos), len(validas)),
            'conf_media': round(sum(l['confianca'] or 0 for l in validas) / len(validas), 4) if validas else None,
            'conf_acertos': round(sum(l['confianca'] or 0 for l in certos) / len(certos), 4) if certos else None,
            'conf_erros': round(sum(l['confianca'] or 0 for l in errados) / len(errados), 4) if errados else None,
            'erros_acima_de_090': sum(1 for l in errados if (l['confianca'] or 0) >= 0.90)}


def main():
    casos = corpus()
    lista = condicoes()
    tarefas = [{'dimensao': d, 'nivel': n, 'ordem': o, 'montar': f, 'caso': caso}
               for d, n, o, f in lista for caso in casos]
    print(f'{len(casos)} casos × {len(lista)} condições = {len(tarefas)} chamadas')

    linhas = em_paralelo(tarefas, executar, trabalhadores=12, rotulo='R11')

    por = {}
    for linha in linhas:
        por.setdefault((linha['dimensao'], linha['nivel']), []).append(linha)

    resultado = {'casos': len(casos), 'chamadas': len(tarefas), 'condicoes': {}, 'detalhe': linhas}
    for (dimensao, nivel), grupo in por.items():
        resultado['condicoes'][f'{dimensao}/{nivel}'] = {'dimensao': dimensao, 'nivel': nivel,
                                                         'ordem': grupo[0]['ordem'],
                                                         **resumo(grupo)}
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')

    base = resultado['condicoes']['referencia/base']['acuracia']
    print(f"\n== R11: mapa de limites (referência = {base:.1%})\n")
    print(f"   {'dimensão':14} {'nível':22} {'acurácia':>9} {'queda':>8} {'conf.':>7} "
          f"{'conf.erros':>11} {'erro≥0,90':>10} {'s/resp':>7}")
    ordem_das_dimensoes = ['referencia', 'opcoes', 'ruido', 'diluicao', 'sobreposicao',
                           'idioma', 'instrucao', 'combinado']
    for dimensao in ordem_das_dimensoes:
        for chave, bloco in sorted(resultado['condicoes'].items(),
                                   key=lambda kv: kv[1]['ordem']):
            if bloco['dimensao'] != dimensao:
                continue
            if bloco['acuracia'] is None:
                print(f"   {dimensao:14} {bloco['nivel']:22} {'—':>9} (sem resposta válida)")
                continue
            queda = bloco['acuracia'] - base
            print(f"   {dimensao:14} {bloco['nivel']:22} {bloco['acuracia']:>8.1%} "
                  f"{queda:>+8.1%} {str(bloco['conf_media']):>7} "
                  f"{str(bloco['conf_erros']):>11} {bloco['erros_acima_de_090']:>10} "
                  f"{bloco['sem_resposta']:>7}")


if __name__ == '__main__':
    main()
