"""R4, R6 e R7 — coerência lógica, ponto de quebra da taxonomia, e os dois tipos de dificuldade.

R4: perguntar "é X?" e "não é X?" produz probabilidades complementares?
R6: onde a acurácia cai, se em 12 opções ela não caiu? 20 e 40.
R7: a confiança distingue texto sujo de sentido ambíguo? É a hipótese nascida de R5, e a que
    tem consequência operacional direta no guia.

    python laboratorio/r4_r7_limites.py
"""
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor.run_e12_replicacao import CRITERIOS, INSTRUCOES  # noqa: E402
from laboratorio.nucleo import em_paralelo, perguntar, wilson  # noqa: E402
from laboratorio.r1_r3_estresse import DISTRATORES, com_erro  # noqa: E402

CORPUS = RAIZ / 'data' / 'corpus' / 'triagem-replicacao.jsonl'
DESTINO = RAIZ / 'laboratorio' / 'r4-r7-limites.json'
SEMENTE = 20260919

# ---------------------------------------------------------------- R6: 35 distratores a mais

MAIS_DISTRATORES = {
    'agendar-visita': 'Pede marcar visita tecnica presencial.',
    'remarcar-entrega': 'Pede mudar a data combinada de entrega.',
    'cancelar-agendamento': 'Pede desmarcar uma visita ja agendada, mantendo o servico.',
    'alterar-endereco': 'Pede mudar o endereco de entrega ou de cadastro.',
    'alterar-titularidade': 'Pede passar o contrato para o nome de outra pessoa.',
    'atualizar-telefone': 'Pede corrigir telefone ou e-mail no cadastro.',
    'segunda-via-boleto': 'Pede especificamente o boleto novamente.',
    'comprovante-pagamento': 'Envia ou pede comprovante de um pagamento ja feito.',
    'negociar-divida': 'Pede acordo ou desconto sobre valor em atraso.',
    'contestar-multa': 'Discorda de uma multa contratual aplicada.',
    'pedir-nota-fiscal': 'Pede a nota fiscal do pedido.',
    'upgrade-plano': 'Pede subir para um plano maior.',
    'downgrade-plano': 'Pede descer para um plano menor, sem encerrar.',
    'pausar-servico': 'Pede suspender temporariamente, com intencao de voltar.',
    'reativar-servico': 'Pede religar um servico suspenso.',
    'contratar-adicional': 'Pede incluir servico ou produto extra.',
    'indicar-amigo': 'Quer indicar outra pessoa para o servico.',
    'duvida-contrato': 'Pergunta sobre clausula, prazo ou regra do contrato.',
    'duvida-uso': 'Pergunta como usar o produto ou o aplicativo.',
    'relatar-falha-app': 'Relata erro no aplicativo ou no site.',
    'suporte-remoto': 'Pede ajuda tecnica a distancia para fazer algo funcionar.',
    'garantia-estendida': 'Pergunta ou pede garantia adicional.',
    'devolver-sem-troca': 'Quer devolver e nao quer outro produto no lugar.',
    'recusar-entrega': 'Avisa que vai recusar a entrega na porta.',
    'reclamar-atendimento': 'Registra insatisfacao com o atendimento, sem pedir acao.',
    'elogiar-atendimento': 'Agradece ou elogia o atendimento.',
    'pedir-supervisor': 'Pede falar com supervisor ou instancia superior.',
    'ameacar-orgao': 'Menciona Procon, ANATEL ou processo judicial.',
    'privacidade-exclusao': 'Pede exclusao dos dados pessoais.',
    'privacidade-acesso': 'Pede saber quais dados a empresa guarda.',
    'cancelar-marketing': 'Pede parar de receber mensagens promocionais.',
    'confirmar-pedido': 'Pede confirmacao de que o pedido foi registrado.',
    'trocar-forma-pagamento': 'Pede mudar cartao, boleto ou debito automatico.',
    'informar-mudanca': 'Avisa uma mudanca, sem pedir nada.',
    'pedir-prazo': 'Pergunta quanto tempo algo vai levar.',
}


def criterios_com(n):
    """Cinco classes reais mais distratores, até somar n opções. Ordem fixa e determinística."""
    tudo = dict(CRITERIOS)
    extras = list(DISTRATORES.items()) + list(MAIS_DISTRATORES.items())
    for chave, valor in extras:
        if len(tudo) >= n:
            break
        if chave not in tudo:
            tudo[chave] = valor
    return tudo


# ---------------------------------------------------------------- R7: corpus adversarial

SIM_NAO = {'sim': 'A afirmacao e verdadeira para esta mensagem.',
           'nao': 'A afirmacao e falsa para esta mensagem.'}

# Vinte casos de dificuldade SEMANTICA, em portugues limpo: a armadilha esta no sentido.
# Escritos antes da execucao, com o gabarito junto. Nenhum reaproveita texto de corpus anterior.
SEMANTICOS = [
    ('sem-01', 'informacao', 'Se eu cancelar agora, perco o desconto? So quero saber antes de decidir.'),
    ('sem-02', 'informacao', 'Meu marido falou em cancelar o plano. Eu nao concordo, queria entender as regras.'),
    ('sem-03', 'cancelar', 'Ja tentei de tudo e nao adiantou. Pode encerrar o contrato de uma vez.'),
    ('sem-04', 'informacao', 'Cancelei a compra no site ontem e deu certo. So confirmando se precisa mais alguma coisa.'),
    ('sem-05', 'cancelar', 'Do pedido inteiro, tira fora o item da luminaria. O resto pode vir normal.'),
    ('sem-06', 'informacao', 'Voces mandaram um e-mail falando de troca. Eu nao pedi troca nenhuma, o que e isso?'),
    ('sem-07', 'cobranca', 'Nao quero trocar o produto. Quero o dinheiro de volta na fatura.'),
    ('sem-08', 'rastrear', 'Nao precisa cancelar nada, so me diz onde esta a encomenda.'),
    ('sem-09', 'informacao', 'Caso o produto nao chegue ate sexta, eu vou querer cancelar. Ainda da tempo de chegar?'),
    ('sem-10', 'trocar', 'Recebi o tamanho errado. Nao quero devolver o dinheiro, quero o tamanho certo.'),
    ('sem-11', 'informacao', 'Uma amiga cancelou e disse que cobraram multa. No meu caso cobrariam tambem?'),
    ('sem-12', 'cancelar', 'Nao me interessa mais. Pode tirar meu nome de tudo e encerrar a assinatura.'),
    ('sem-13', 'cobranca', 'A entrega chegou certinha, o problema e que veio cobrado duas vezes no cartao.'),
    ('sem-14', 'informacao', 'Se eu pedir a segunda via, o vencimento muda? Antes de pedir queria confirmar.'),
    ('sem-15', 'rastrear', 'Ja paguei, ja conferi a nota, ja esta tudo certo. So falta saber quando chega.'),
    ('sem-16', 'informacao', 'Meu filho usou meu cartao e pediu troca sem me avisar. Como funciona isso?'),
    ('sem-17', 'trocar', 'Nao e problema de cobranca nem de entrega: o aparelho veio quebrado e preciso de outro.'),
    ('sem-18', 'cancelar', 'Assim que terminar o mes vigente, nao renove. Encerra por ali.'),
    ('sem-19', 'informacao', 'Voces tem politica de cancelamento em ate sete dias? Pergunto por curiosidade.'),
    ('sem-20', 'cobranca', 'A troca ja foi feita e resolvida. Falta estornar a diferenca que paguei a mais.'),
]

# Vinte casos semanticamente TRIVIAIS: qualquer pessoa acerta lendo. A dificuldade sera so
# de superficie, aplicada depois com ruido pesado.
FACEIS = [
    ('fac-01', 'cancelar', 'Quero cancelar meu pedido numero 4471 agora.'),
    ('fac-02', 'rastrear', 'Onde esta meu pedido? Ja faz uma semana.'),
    ('fac-03', 'trocar', 'Quero trocar o produto que recebi por outro igual.'),
    ('fac-04', 'cobranca', 'Preciso da segunda via do boleto deste mes.'),
    ('fac-05', 'informacao', 'Qual o horario de atendimento de voces?'),
    ('fac-06', 'cancelar', 'Por favor cancele minha assinatura mensal.'),
    ('fac-07', 'rastrear', 'Qual o codigo de rastreio da minha entrega?'),
    ('fac-08', 'trocar', 'O produto veio com defeito, quero um novo no lugar.'),
    ('fac-09', 'cobranca', 'Quero parcelar o valor da fatura em tres vezes.'),
    ('fac-10', 'informacao', 'Voces entregam no interior de Sergipe?'),
    ('fac-11', 'cancelar', 'Desisti da compra, pode cancelar tudo.'),
    ('fac-12', 'rastrear', 'Meu pedido saiu para entrega hoje?'),
    ('fac-13', 'trocar', 'Quero trocar a cor do item que comprei.'),
    ('fac-14', 'cobranca', 'Fui cobrado a mais, quero o estorno.'),
    ('fac-15', 'informacao', 'Qual e o prazo de garantia do aparelho?'),
    ('fac-16', 'cancelar', 'Cancela o contrato, nao quero mais o servico.'),
    ('fac-17', 'rastrear', 'A encomenda esta em qual cidade agora?'),
    ('fac-18', 'trocar', 'Recebi o modelo errado, preciso do modelo certo.'),
    ('fac-19', 'cobranca', 'Quero pagar no debito automatico a partir do mes que vem.'),
    ('fac-20', 'informacao', 'Voces tem loja fisica em Brasilia?'),
]


# ---------------------------------------------------------------- tarefas

def corpus():
    return [json.loads(linha) for linha in
            CORPUS.read_text(encoding='utf-8').splitlines() if linha.strip()]


def tarefas_r4(casos):
    """Mesma proposição, afirmada e negada. Se a crença é uma crença, as probabilidades somam 1."""
    saida = []
    for caso in casos[:60]:
        for forma, afirmacao in (
                ('afirmada', 'O remetente esta pedindo o cancelamento de um pedido, servico ou contrato.'),
                ('negada', 'O remetente NAO esta pedindo o cancelamento de nenhum pedido, servico ou contrato.')):
            saida.append({'rodada': 'R4', 'condicao': forma, 'case_id': caso['case_id'],
                          'gold': caso['gold'], 'texto': caso['text'],
                          'perguntas': {'juizo': {'type': 'choice',
                                                  'instructions': f'Afirmacao: "{afirmacao}" Ela e verdadeira?',
                                                  'criteria': dict(SIM_NAO)}},
                          'chave': 'juizo', 'alvo': None})
    return saida


def tarefas_r6(casos):
    saida = []
    for n in (20, 40):
        criterios = criterios_com(n)
        for caso in casos:
            saida.append({'rodada': 'R6', 'condicao': f'{len(criterios)}-opcoes',
                          'case_id': caso['case_id'], 'gold': caso['gold'],
                          'texto': caso['text'],
                          'perguntas': {'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                                 'criteria': criterios}},
                          'chave': 'acao', 'alvo': caso['gold']})
    return saida


def tarefas_r7():
    sorteio = random.Random(SEMENTE)
    saida = []
    for identificador, gold, texto in SEMANTICOS:
        saida.append({'rodada': 'R7', 'condicao': 'semantico', 'case_id': identificador,
                      'gold': gold, 'texto': texto,
                      'perguntas': {'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                             'criteria': dict(CRITERIOS)}},
                      'chave': 'acao', 'alvo': gold})
    for identificador, gold, texto in FACEIS:
        # O mesmo caso fácil em duas versões: limpa (controle) e suja (tratamento).
        saida.append({'rodada': 'R7', 'condicao': 'facil-limpo', 'case_id': identificador,
                      'gold': gold, 'texto': texto,
                      'perguntas': {'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                             'criteria': dict(CRITERIOS)}},
                      'chave': 'acao', 'alvo': gold})
        saida.append({'rodada': 'R7', 'condicao': 'facil-sujo', 'case_id': identificador,
                      'gold': gold, 'texto': com_erro(texto, 0.22, sorteio),
                      'perguntas': {'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                             'criteria': dict(CRITERIOS)}},
                      'chave': 'acao', 'alvo': gold})
    return saida


def executar(tarefa):
    respostas, detalhe = perguntar(f"Mensagem do cliente:\n{tarefa['texto']}",
                                   tarefa['perguntas'], rodada=tarefa['rodada'])
    alvo = (respostas or {}).get(tarefa['chave']) or {}
    return {'rodada': tarefa['rodada'], 'condicao': tarefa['condicao'],
            'case_id': tarefa['case_id'], 'gold': tarefa['gold'], 'alvo': tarefa['alvo'],
            'escolha': alvo.get('choice'), 'confianca': alvo.get('confidence'),
            'probabilidades': alvo.get('probabilities'),
            'erro': None if respostas else (detalhe or {}).get('erro')}


def acuracia(linhas):
    validas = [l for l in linhas if l['escolha']]
    acertos = sum(1 for l in validas if l['escolha'] == l['alvo'])
    return {'n': len(validas), 'acuracia': round(acertos / len(validas), 4) if validas else None,
            'ic95': wilson(acertos, len(validas)),
            'conf_acertos': round(sum(l['confianca'] or 0 for l in validas
                                      if l['escolha'] == l['alvo']) / acertos, 4) if acertos else None,
            'conf_erros': round(sum(l['confianca'] or 0 for l in validas
                                    if l['escolha'] != l['alvo']) / (len(validas) - acertos), 4)
            if len(validas) - acertos else None,
            'erros': [l['case_id'] for l in validas if l['escolha'] != l['alvo']]}


def main():
    casos = corpus()
    tarefas = tarefas_r4(casos) + tarefas_r6(casos) + tarefas_r7()
    print(f'{len(tarefas)} chamadas: R4={len(tarefas_r4(casos))}, R6={len(tarefas_r6(casos))}, '
          f'R7={len(tarefas_r7())}')

    linhas = em_paralelo(tarefas, executar, trabalhadores=12, rotulo='R4/R6/R7')
    por_condicao = {}
    for linha in linhas:
        por_condicao.setdefault(linha['condicao'], []).append(linha)

    resultado = {'chamadas': len(tarefas), 'detalhe': linhas}

    # ---- R4: soma das probabilidades de "sim" nas duas formas
    def probabilidade_sim(linha):
        probabilidades = linha.get('probabilidades') or {}
        if isinstance(probabilidades, dict) and 'sim' in probabilidades:
            return probabilidades['sim']
        if linha['escolha'] == 'sim':
            return linha['confianca']
        if linha['escolha'] == 'nao' and linha['confianca'] is not None:
            return 1 - linha['confianca']
        return None

    afirmada = {l['case_id']: l for l in por_condicao.get('afirmada', [])}
    negada = {l['case_id']: l for l in por_condicao.get('negada', [])}
    somas, incoerentes = [], []
    for case_id, linha in afirmada.items():
        outra = negada.get(case_id)
        if not outra:
            continue
        pa, pb = probabilidade_sim(linha), probabilidade_sim(outra)
        if pa is None or pb is None:
            continue
        soma = pa + pb
        somas.append({'case_id': case_id, 'p_afirmada': pa, 'p_negada': pb,
                      'soma': round(soma, 4), 'desvio': round(soma - 1.0, 4)})
        # Incoerência dura: dizer "sim" para a afirmação E "sim" para a negação dela.
        if linha['escolha'] == outra['escolha']:
            incoerentes.append(case_id)
    somas.sort(key=lambda s: abs(s['desvio']))
    desvios = sorted(abs(s['desvio']) for s in somas)
    resultado['R4'] = {
        'pares': len(somas),
        'desvio_mediano': round(desvios[len(desvios) // 2], 4) if desvios else None,
        'desvio_medio': round(sum(desvios) / len(desvios), 4) if desvios else None,
        'contradicoes_duras': incoerentes,
        'piores': somas[-5:],
    }

    # ---- R6 e R7
    resultado['R6'] = {nome: acuracia(grupo) for nome, grupo in por_condicao.items()
                       if nome.endswith('-opcoes')}
    resultado['R7'] = {nome: acuracia(grupo) for nome, grupo in por_condicao.items()
                       if nome in ('semantico', 'facil-limpo', 'facil-sujo')}

    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')

    print('\n== R4: coerência lógica (afirmação vs negação da mesma proposição)')
    print(f"   pares {resultado['R4']['pares']} | desvio mediano da soma "
          f"{resultado['R4']['desvio_mediano']} | médio {resultado['R4']['desvio_medio']}")
    print(f"   contradições duras (sim para A e sim para não-A): "
          f"{len(resultado['R4']['contradicoes_duras'])}")
    for pior in resultado['R4']['piores']:
        print(f"      {pior['case_id']}: {pior['p_afirmada']} + {pior['p_negada']} = {pior['soma']}")

    print('\n== R6: ponto de quebra do número de opções')
    for nome, bloco in sorted(resultado['R6'].items(), key=lambda kv: int(kv[0].split('-')[0])):
        print(f"   {nome:12} {bloco['acuracia']:.4f} IC95 {bloco['ic95']} n={bloco['n']}")

    print('\n== R7: dificuldade semântica contra dificuldade de superfície')
    for nome in ('facil-limpo', 'facil-sujo', 'semantico'):
        bloco = resultado['R7'].get(nome)
        if not bloco:
            continue
        print(f"   {nome:12} acurácia {bloco['acuracia']:.4f} n={bloco['n']} | "
              f"conf. acertos {bloco['conf_acertos']} | conf. erros {bloco['conf_erros']} | "
              f"erros {bloco['erros']}")


if __name__ == '__main__':
    main()
