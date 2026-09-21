"""R28 — o Jev lê o tema ou o ato de fala? E quantas perguntas cabem de graça no mesmo payload?

De onde vem. Relendo as linhas brutas da R19, da R21 e da R25 por molde, sem chamada nova: nos
moldes em que quem escreve pede a ação para si, o Jev acerta 27 de 27 no jurídico e 33 de 33 na
clínica. Todos os erros dos dois domínios novos (14 de 14 e 28 de 28) têm gabarito `informacao`,
e em 41 dos 42 a classe escolhida é a ação que o texto menciona. A "queda de domínio" de 98,9%
para 78,5% e 63,2% não está no vocabulário do domínio: está em mensagens que falam de uma ação
sem pedi-la. A tese desta rodada é que o Jev responde "de que ação o texto fala" com acerto
quase total e que o que falha é o ato de fala — se quem escreve pede, para si, agora.

A R19 tentou decompor com "de quem é a ação?" e falhou: a auxiliar acertava 68,7% e destruiu o
molde oposto. Aqui a auxiliar é outra pergunta (há pedido de quem escreve, sim ou não), medida
sozinha antes de ser usada, como a própria R19 mandou fazer.

**Arranjos**, sobre as 85 mensagens de atendimento (R19), 69 jurídicas (R21) e 76 de clínica (R25):

    base      a pergunta original de cada domínio, refeita hoje para parear no mesmo dia
    painel    quatro perguntas no mesmo payload: a original, `ato`, `tema` e o sentinela da R22
    ato       a pergunta `ato` sozinha
    rotulo    a pergunta original com a classe `informacao` renomeada para `nao-pede-acao`

Composição medida: `tema` quando `ato` diz que há pedido, `informacao` quando diz que não há.
O gabarito de `ato` e o de `tema` saem do molde e do campo `classe` do corpus, fixados antes de
existir texto; nenhum foi escrito por quem analisa.

**Previsões e falsificação, escritas antes de rodar.**

H28a  `tema` acerta a ação mencionada em 90% ou mais em cada domínio, contando os moldes de
      gabarito `informacao`. Abaixo de 80% em algum domínio falsifica a tese do detector de tema.
H28b  `ato`, sozinha, acerta 85% ou mais no conjunto. Abaixo de 75% a composição herda o mesmo
      gargalo da R19 e a rodada diz isso.
H28c  A composição ganha da `base` no conjunto dos três domínios, McNemar exato p < 0,05, e
      nenhum molde perde mais de 10 pontos. Um molde destruído falsifica, como na R19.
H28d  O rótulo renomeado ganha da `base` no conjunto, p < 0,05 (pela R11, o rótulo decide).
H28e  Dentro do painel de quatro perguntas, a resposta da pergunta original é a mesma da `base`
      em 97% ou mais dos casos, e a chamada custa menos de 1,5 vez a chamada de uma pergunta.
      Abaixo de 90% de concordância, "perguntas a mais saem de graça" é falso: elas interferem.
H28f  O sentinela fica calado em 95% ou mais destas 230 mensagens limpas, em domínios em que
      nunca foi medido.

    python laboratorio/r28_ato_de_fala.py --rodar
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor.run_e12_replicacao import CRITERIOS, INSTRUCOES  # noqa: E402
from laboratorio.nucleo import em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r21_generalizacao import CLASSES_PT, INSTRUCAO_PT, Medidor  # noqa: E402
from laboratorio.r22_defesas import SENTINELA  # noqa: E402
from laboratorio.r25_terceiro_dominio import CLASSES as CLASSES_CLINICA  # noqa: E402
from laboratorio.r25_terceiro_dominio import INSTRUCAO as INSTRUCAO_CLINICA  # noqa: E402

DESTINO = RAIZ / 'laboratorio' / 'r28-ato-de-fala.json'
CUSTO_MAXIMO_PREVISTO = 0.10

PEDE = {'pedido-direto', 'terceiro-contra-eu-quero', 'eu-peco-terceiro-cita'}

ATO = {
    'type': 'choice',
    'instructions': 'Quem escreve esta pedindo, para si mesmo e agora, que alguma acao seja feita?',
    'criteria': {
        'pede-para-si': 'Quem escreve pede claramente que uma acao seja feita para ele mesmo.',
        'nao-pede': ('Quem escreve so pergunta, so relata, ou fala do pedido ou da acao de outra '
                     'pessoa; nao pede que nada seja feito para si agora.'),
    },
}
INSTRUCAO_TEMA = ('De qual acao a mensagem fala? Nao importa quem quer a acao nem se ha pedido: '
                  'importa so de qual acao o texto trata.')
NAO_PEDE = ('Quem escreve nao pede que nenhuma acao seja feita para si agora: so pergunta, so '
            'relata, ou fala do pedido de outra pessoa.')

DOMINIOS = {
    'atendimento': {
        'arquivo': 'r19-corpus.json', 'campo': 'texto', 'quem': 'O cliente',
        'instrucao': INSTRUCOES, 'criterios': CRITERIOS,
        'tema': {'cancelar': 'A mensagem fala de encerrar, cancelar ou desistir de pedido, servico ou contrato.',
                 'rastrear': 'A mensagem fala de onde esta, quando chega ou do status de uma entrega.',
                 'trocar': 'A mensagem fala de troca, devolucao, reparo ou conserto.',
                 'cobranca': 'A mensagem fala de boleto, segunda via, estorno, reembolso ou valor cobrado.'}},
    'juridico': {
        'arquivo': 'r21-corpus.json', 'campo': 'pt', 'quem': 'O cliente',
        'instrucao': INSTRUCAO_PT, 'criterios': CLASSES_PT,
        'tema': {'protocolar': 'A mensagem fala de entrar com acao, recurso ou peticao.',
                 'prazo': 'A mensagem fala de prazo, andamento ou data de audiencia.',
                 'documento': 'A mensagem fala de copia de documento, procuracao ou comprovante.',
                 'encerrar': 'A mensagem fala de desistir do caso, encerrar o servico ou revogar a procuracao.'}},
    'clinica': {
        'arquivo': 'r25-corpus.json', 'campo': 'texto', 'quem': 'O paciente',
        'instrucao': INSTRUCAO_CLINICA, 'criterios': CLASSES_CLINICA,
        'tema': {'agendar': 'A mensagem fala de marcar consulta ou exame.',
                 'remarcar': 'A mensagem fala de mudar a data ou cancelar consulta ja marcada.',
                 'resultado': 'A mensagem fala de resultado ou laudo de exame.',
                 'documento': 'A mensagem fala de receita, atestado, declaracao ou relatorio medico.'}},
}
ARRANJOS = ('base', 'painel', 'ato', 'rotulo')


def perguntas_do(arranjo, dominio):
    d = DOMINIOS[dominio]
    original = {'type': 'choice', 'instructions': d['instrucao'], 'criteria': dict(d['criterios'])}
    if arranjo == 'base':
        return {'pedido': original}
    if arranjo == 'ato':
        return {'ato': dict(ATO)}
    if arranjo == 'rotulo':
        criterios = {k: v for k, v in d['criterios'].items() if k != 'informacao'}
        criterios['nao-pede-acao'] = NAO_PEDE
        return {'pedido': {'type': 'choice', 'instructions': d['instrucao'], 'criteria': criterios}}
    return {'pedido': original, 'ato': dict(ATO),
            'tema': {'type': 'choice', 'instructions': INSTRUCAO_TEMA, 'criteria': dict(d['tema'])},
            'sentinela': dict(SENTINELA)}


def classificar(tarefa):
    d = DOMINIOS[tarefa['dominio']]
    estado = f"{d['quem']} escreveu: \"{tarefa['caso'][d['campo']]}\""
    respostas, detalhe = perguntar(estado, perguntas_do(tarefa['arranjo'], tarefa['dominio']),
                                   rodada='R28')
    linha = {'dominio': tarefa['dominio'], 'i': tarefa['i'], 'arranjo': tarefa['arranjo'],
             'molde': tarefa['caso']['molde'], 'gold': tarefa['caso']['gold'],
             'acao_mencionada': tarefa['caso']['classe'],
             'gold_ato': 'pede-para-si' if tarefa['caso']['molde'] in PEDE else 'nao-pede',
             'custo_usd': ((detalhe or {}).get('settled_nusd') or 0) / 1e9 or (detalhe or {}).get('custo_usd'),
             'attempt_id': (detalhe or {}).get('attempt_id')}
    for nome, bloco in (respostas or {}).items():
        linha[nome] = (bloco or {}).get('choice')
        linha['conf_' + nome] = (bloco or {}).get('confidence')
    return linha


def taxa(acertos, n):
    return {'acertos': acertos, 'n': n, 'taxa': round(acertos / n, 4) if n else None,
            'ic95': wilson(acertos, n) if n else None}


def pareado(certo_a, certo_b):
    comuns = [i for i in certo_a if i in certo_b]
    so_a = sum(1 for i in comuns if certo_a[i] and not certo_b[i])
    so_b = sum(1 for i in comuns if certo_b[i] and not certo_a[i])
    return {'pares': len(comuns), 'so_primeiro': so_a, 'so_segundo': so_b, 'p': mcnemar_exato(so_a, so_b)}


def analisar(linhas):
    por = {}
    for l in linhas:
        por.setdefault(l['arranjo'], {})[(l['dominio'], l['i'])] = l
    normal = lambda escolha: 'informacao' if escolha == 'nao-pede-acao' else escolha

    def composicao(l, fonte):
        if not l.get('ato') or not l.get(fonte):
            return None
        return l[fonte] if l['ato'] == 'pede-para-si' else 'informacao'

    leituras = {
        'base': {k: l.get('pedido') for k, l in por['base'].items()},
        'rotulo': {k: normal(l.get('pedido')) for k, l in por['rotulo'].items()},
        'pedido-no-painel': {k: l.get('pedido') for k, l in por['painel'].items()},
        'composicao-tema': {k: composicao(l, 'tema') for k, l in por['painel'].items()},
        'composicao-pedido': {k: composicao(l, 'pedido') for k, l in por['painel'].items()},
    }
    gold = {k: l['gold'] for k, l in por['base'].items()}
    molde = {k: l['molde'] for k, l in por['base'].items()}
    saida = {'leituras': {}, 'pareado_contra_base': {}, 'detalhe': linhas}
    certos = {}
    for nome, escolhas in leituras.items():
        validas = {k: e for k, e in escolhas.items() if e}
        certos[nome] = {k: e == gold[k] for k, e in validas.items()}
        bloco = {'conjunto': taxa(sum(certos[nome].values()), len(validas)), 'por_dominio': {}, 'por_molde': {}}
        for dominio in DOMINIOS:
            do = [k for k in validas if k[0] == dominio]
            bloco['por_dominio'][dominio] = taxa(sum(certos[nome][k] for k in do), len(do))
            for m in sorted({molde[k] for k in do}):
                dm = [k for k in do if molde[k] == m]
                bloco['por_molde'][f'{dominio}/{m}'] = taxa(sum(certos[nome][k] for k in dm), len(dm))
        saida['leituras'][nome] = bloco
    for nome in leituras:
        if nome != 'base':
            saida['pareado_contra_base'][nome] = pareado(certos[nome], certos['base'])

    # as perguntas auxiliares, medidas sozinhas e dentro do painel
    aux = {}
    for nome, arranjo, campo, alvo in (('ato-sozinha', 'ato', 'ato', 'gold_ato'), ('ato-no-painel', 'painel', 'ato', 'gold_ato'),
                                       ('tema-no-painel', 'painel', 'tema', 'acao_mencionada')):
        bloco = {'por_dominio': {}, 'por_molde': {}}
        validas = [l for l in por[arranjo].values() if l.get(campo)]
        bloco['conjunto'] = taxa(sum(l[campo] == l[alvo] for l in validas), len(validas))
        for dominio in DOMINIOS:
            do = [l for l in validas if l['dominio'] == dominio]
            bloco['por_dominio'][dominio] = taxa(sum(l[campo] == l[alvo] for l in do), len(do))
            for m in sorted({l['molde'] for l in do}):
                dm = [l for l in do if l['molde'] == m]
                bloco['por_molde'][f'{dominio}/{m}'] = taxa(sum(l[campo] == l[alvo] for l in dm), len(dm))
        aux[nome] = bloco
    saida['auxiliares'] = aux

    # interferência e custo do painel
    comuns = [k for k in por['base'] if por['base'][k].get('pedido') and por['painel'].get(k, {}).get('pedido')]
    iguais = sum(por['base'][k]['pedido'] == por['painel'][k]['pedido'] for k in comuns)
    comuns_ato = [k for k in por['ato'] if por['ato'][k].get('ato') and por['painel'].get(k, {}).get('ato')]
    iguais_ato = sum(por['ato'][k]['ato'] == por['painel'][k]['ato'] for k in comuns_ato)
    custo = lambda arranjo: [l['custo_usd'] for l in por[arranjo].values() if l.get('custo_usd')]
    media = lambda xs: sum(xs) / len(xs) if xs else None
    saida['painel'] = {
        'pedido_igual_a_base': taxa(iguais, len(comuns)),
        'ato_igual_a_sozinha': taxa(iguais_ato, len(comuns_ato)),
        'custo_medio_base_usd': media(custo('base')), 'custo_medio_painel_usd': media(custo('painel')),
        'diferenca_media_de_confianca': media([abs((por['base'][k].get('conf_pedido') or 0) - (por['painel'][k].get('conf_pedido') or 0)) for k in comuns]),
    }
    calados = [l for l in por['painel'].values() if l.get('sentinela')]
    saida['sentinela_em_texto_limpo'] = taxa(sum(l['sentinela'] == 'nao-tenta' for l in calados), len(calados))
    return saida


def main():
    analise = argparse.ArgumentParser(description=__doc__)
    analise.add_argument('--rodar', action='store_true')
    args = analise.parse_args()
    if not args.rodar:
        analise.print_help()
        return
    medidor = Medidor()
    tarefas = []
    for dominio, d in DOMINIOS.items():
        casos = json.loads((RAIZ / 'laboratorio' / d['arquivo']).read_text(encoding='utf-8'))['casos']
        tarefas += [{'dominio': dominio, 'i': i, 'caso': c, 'arranjo': a} for i, c in enumerate(casos) for a in ARRANJOS]
    print(f'{len(tarefas)} chamadas')
    linhas = em_paralelo(tarefas, classificar, trabalhadores=8, rotulo='R28')
    bruto = DESTINO.with_name('r28-bruto.json')
    bruto.write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding='utf-8')  # o bruto antes da análise (lição da R26)
    resultado = analisar(linhas)
    gasto, chamadas, _ = medidor.gasto()
    resultado['custo_usd'], resultado['chamadas'] = round(gasto, 6), chamadas
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    for nome, b in resultado['leituras'].items():
        print(f"  {nome:20} {b['conjunto']['acertos']}/{b['conjunto']['n']} = {b['conjunto']['taxa']}  "
              + '  '.join(f"{d} {v['taxa']}" for d, v in b['por_dominio'].items()))
    for nome, b in resultado['auxiliares'].items():
        print(f"  {nome:20} {b['conjunto']['taxa']}  " + '  '.join(f"{d} {v['taxa']}" for d, v in b['por_dominio'].items()))
    print('  pareado contra base', resultado['pareado_contra_base'])
    print('  painel', resultado['painel'])
    print('  sentinela calado', resultado['sentinela_em_texto_limpo'])
    print(f'{chamadas} chamadas, US$ {gasto:.6f}')
    if gasto > CUSTO_MAXIMO_PREVISTO:
        print('ATENÇÃO: passou do teto previsto')


if __name__ == '__main__':
    main()
