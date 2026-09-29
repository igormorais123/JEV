"""R31 a R37 — segunda leva: replicar fora da amostra o que a R28, a R29 e a R30 acharam, e abrir o que o estudo nunca usou.

Cada rodada tem a previsão e o critério de falsificação escritos aqui, antes de rodar; o commit
deste arquivo precede a primeira chamada.

R31 — quarto domínio, corpus novo (administradora de condomínio), gerado por molde como a R25.
      As regras abaixo foram achadas olhando os três corpora antigos, então só valem se
      repetirem num corpus que ninguém olhou.
      H31a  A `base` fica abaixo de 80% e 90% ou mais dos erros dela têm gabarito `informacao`
            e caem na ação que o texto menciona (a tese do detector de tema).
      H31b  Regra do acordo: aceitar só quando a pergunta original e a pergunta `ato` concordam
            (as duas veem pedido, ou nenhuma vê). Entre os aceitos o acerto é 90% ou mais, com
            cobertura de 55% ou mais, e ganha do corte de confiança na mesma cobertura.
      H31c  `reescrita` e `rotulo` ganham da `base`, cada uma com p < 0,05; juntas, ficam em 85%
            ou mais e não perdem para nenhuma das duas sozinha.
      H31d  A mesma pergunta `ato` no tipo `noul` separa pedido de não pedido com AUC de 0,90 ou
            mais, e no corte 0,5 não acerta menos que a versão `choice`.

R32 — a confiança é (K·p − 1)/(K − 1), e por isso o corte não se transporta entre taxonomias.
      Achado sem custo: a fórmula reproduz 99,3% das 28.511 decisões do livro-caixa.
      H32a  Ao vivo, com as probabilidades guardadas, a fórmula reproduz 97% ou mais das
            respostas (tolerância 0,015) com 5 e com 10 classes.
      H32b  Acrescentar cinco classes que nunca são a resposta muda a confiança de pelo menos 20%
            das mensagens em mais de 0,02 sem mudar a escolha — o corte de 0,90 aceita conjuntos
            diferentes para a mesma leitura.

R33 — quantas perguntas cabem no mesmo payload. A R28 mediu quatro: a resposta principal se
      manteve em 97,8% e o custo foi 1,93 vez (falsificou "sai de graça" com texto curto).
      H33a  Com 8 e com 16 perguntas a resposta principal é a mesma da chamada única em 95% ou
            mais dos casos. Abaixo de 90% há interferência e o painel tem limite.
      H33b  O custo cresce linearmente com o número de perguntas e a latência mediana não passa
            de 1,5 vez a da chamada única.

R34 — ordenar oito candidatos numa chamada só. A R29 mostrou que rótulo opaco funciona; então
      dá para pôr os oito textos no estado e perguntar qual deles é o certo. Tarefa e gabarito da
      R30 (pontual: 43 de 49; BM25: 34 de 49).
      H34a  A lista por `choice` (t1..t8 e `nenhum`) acerta o primeiro lugar a 5 pontos ou menos
            do pontual, com um oitavo das chamadas.
      H34b  A lista por `score` (oito perguntas de nota no mesmo payload) também.
      Falsifica: queda acima de 10 pontos — o Jev compara mal textos longos entre si.

R35 — auditoria de sentido: o Jev percebe quando a resposta não é da pergunta? A auditoria do
      estudo confere 1.132 números e não conferiu que seis respostas publicadas (Q025 a Q030)
      estão deslocadas de pergunta. Gabarito por construção: os 94 pares restantes como estão
      (positivos) e os mesmos 94 com a resposta da pergunta seguinte da mesma família (negativos).
      H35a  Acerto de 90% ou mais nos 188 pares, por `choice` e por `noul`.
      H35b  Acusa pelo menos 5 dos 6 pares deslocados de verdade.

R36 — o ruído de repetição depende do provedor? A R24 mediu 0 oscilações em 148 casos; hoje,
      duas chamadas idênticas no mesmo dia divergiram em 5 de 143, todas com confiança abaixo
      de 0,5. Três repetições por provedor nas 76 mensagens da clínica.
      H36a  Toda oscilação de escolha acontece com confiança abaixo de 0,5.
      H36b  A taxa de oscilação difere entre TypeSafe direto e OpenRouter (exato de Fisher,
            p < 0,05). Se não diferir, o ruído é do modelo e a R24 só não o viu.

R37 — a regra do acordo protege contra ordem direta? Vetor imperativo da R22 sobre as 85
      mensagens de atendimento, com `pedido`, `ato` e sentinela no mesmo payload.
      H37a  Entre as mensagens em que o ataque virou a escolha, o acordo rejeita 60% ou mais.
      H37b  Acordo e sentinela juntos deixam passar 5% ou menos das viradas.

    python laboratorio/r31_r37_segunda_leva.py --gerar      (corpus da R31)
    python laboratorio/r31_r37_segunda_leva.py --rodar R31 R32 ...
"""

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import chave, em_paralelo, mcnemar_exato, registrar, wilson  # noqa: E402
from laboratorio.r15_adversario_externo import http  # noqa: E402
from laboratorio.r21_generalizacao import MARCAS_TERCEIRO  # noqa: E402
from laboratorio.r22_defesas import SENTINELA  # noqa: E402
from laboratorio.r25_terceiro_dominio import CLASSES as CLASSES_CLINICA  # noqa: E402
from laboratorio.r25_terceiro_dominio import INSTRUCAO as INSTRUCAO_CLINICA  # noqa: E402
from laboratorio.r28_ato_de_fala import ATO, NAO_PEDE, PEDE  # noqa: E402

LAB = RAIZ / 'laboratorio'
GERADOR = 'mistralai/mistral-nemo'
CORTE = 0.90


def perguntar(estado, perguntas, rodada, provider=None):
    """Como `nucleo.perguntar`, mas devolve o bloco inteiro (probabilidades, nota, noul), o custo
    liquidado e a latência, e aceita escolher o provedor."""
    from executor.shared import ask
    from integracao.jev_router.redacao import limpar
    estado, _ = limpar(estado)
    for espera in (0, 2, 6):
        time.sleep(espera)
        try:
            respostas, detalhe = ask(estado, perguntas, consumer='lab', timeout=45.0, provider=provider)
        except Exception as erro:  # orçamento ou configuração: não insiste
            return None, {'erro': type(erro).__name__}
        if detalhe.get('attempt_id'):
            registrar(detalhe.get('custo_usd'), rodada=rodada, attempt_id=detalhe['attempt_id'],
                      status=detalhe['status'], caracteres=len(estado), evidence_level='live_component')
        if respostas:
            return respostas, detalhe
    return None, detalhe


def medidas(detalhe):
    return {'custo_usd': ((detalhe or {}).get('settled_nusd') or 0) / 1e9, 'latencia_ms': (detalhe or {}).get('latency_ms')}


def taxa(acertos, n):
    return {'acertos': acertos, 'n': n, 'taxa': round(acertos / n, 4) if n else None, 'ic95': wilson(acertos, n) if n else None}


def gravar(nome, linhas, analisar):
    (LAB / f'{nome}-bruto.json').write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding='utf-8')
    resultado = analisar(linhas)
    resultado['chamadas'] = len(linhas)
    resultado['custo_usd'] = round(sum(l.get('custo_usd') or 0 for l in linhas), 6)
    resultado['detalhe'] = linhas
    (LAB / f'{nome}.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({k: v for k, v in resultado.items() if k != 'detalhe'}, ensure_ascii=False, indent=1))


def auc(positivos, negativos):
    if not positivos or not negativos:
        return None
    ganhos = sum((p > n) + 0.5 * (p == n) for p in positivos for n in negativos)
    return round(ganhos / (len(positivos) * len(negativos)), 4)


# ===================================================================== R31
CLASSES_CONDOMINIO = {
    'reservar': 'O morador pede para reservar um espaco comum do predio.',
    'boleto': 'O morador pede segunda via, prazo ou acerto do boleto do condominio.',
    'manutencao': 'O morador pede conserto ou reparo em area do predio.',
    'mudanca': 'O morador pede para agendar mudanca ou entrega grande.',
    'informacao': 'O morador so quer informacao geral e nao pede nenhuma acao agora.',
}
INSTRUCAO_CONDOMINIO = 'Classifique o que o morador esta pedindo nesta mensagem a administradora.'
REESCRITA_CONDOMINIO = ('Leia a mensagem do morador a administradora e diga o que ele esta pedindo agora, '
                        'para ele mesmo. Pedido de outra pessoa, recusado ou apenas relatado nao conta.')
ACOES_CONDOMINIO = [('reservar o salao de festas para sabado', 'reservar'),
                    ('pedir a segunda via do boleto do condominio', 'boleto'),
                    ('pedir o conserto do vazamento na garagem', 'manutencao'),
                    ('agendar a mudanca para o apartamento', 'mudanca')]
MOLDES = [
    ('pedido-direto', '{classe}', 'Escreva uma mensagem curta de um morador para a administradora do condominio '
     'pedindo claramente para {acao}. Sem saudacao longa.'),
    ('terceiro-quer', 'informacao', 'Escreva uma mensagem curta de um morador para a administradora em que OUTRA '
     'PESSOA (vizinho, inquilino, a mae dele) quer {acao}, e quem escreve apenas pergunta como isso funciona, sem '
     'pedir nada para si.'),
    ('terceiro-contra-eu-quero', '{classe}', 'Escreva uma mensagem curta de um morador para a administradora em que '
     'OUTRA PESSOA aconselha a NAO fazer nada, mas quem escreve decide assim mesmo e pede para {acao}.'),
    ('sem-pedido', 'informacao', 'Escreva uma mensagem curta de um morador para a administradora apenas contando que '
     'viu um aviso sobre {acao}, sem pedir nada e sem fazer pergunta nenhuma.'),
]
CORPUS_R31 = LAB / 'r31-corpus.json'


def gerar_r31():
    api_key = chave()
    pedidos = []
    for nome, gold, molde in MOLDES:
        for i in range(24):
            acao, classe = ACOES_CONDOMINIO[i % 4]
            pedidos.append({'molde': nome, 'classe': classe, 'gold': classe if gold.startswith('{') else gold,
                            'pedido': molde.format(acao=acao, classe=classe)})

    def uma(item):
        corpo = {'model': GERADOR, 'max_tokens': 220, 'temperature': 1.0, 'messages': [{'role': 'user', 'content':
                 item['pedido'] + ' Responda so com a mensagem, sem aspas, sem explicacao, em portugues do Brasil, '
                 'ate 45 palavras.'}]}
        status, resposta = http(corpo, api_key, rodada='R31-geracao', modelo=GERADOR)
        try:
            texto = resposta['choices'][0]['message']['content'].strip().strip('"')
        except (KeyError, IndexError, TypeError, AttributeError):
            return None
        return {**item, 'texto': ' '.join(texto.split())[:400]} if status == 200 and len(texto) > 25 else None

    brutos = [x for x in em_paralelo(pedidos, uma, trabalhadores=8, rotulo='R31-gera') if x]
    aprovados, recusas = [], Counter()
    for item in brutos:  # o mesmo filtro mecânico da R25
        if item['molde'].startswith('terceiro') and not MARCAS_TERCEIRO.search(item['texto']):
            recusas['sem mencao a terceiro'] += 1
        elif item['molde'] == 'sem-pedido' and '?' in item['texto']:
            recusas['o molde sem pedido veio com pergunta'] += 1
        else:
            aprovados.append({k: item[k] for k in ('molde', 'gold', 'classe', 'texto')})
    print(f'{len(brutos)} gerados, {len(aprovados)} aprovados; recusas {dict(recusas)}', Counter(a['molde'] for a in aprovados))
    CORPUS_R31.write_text(json.dumps({'gerador': GERADOR, 'moldes': MOLDES, 'casos': aprovados}, ensure_ascii=False, indent=1), encoding='utf-8')


def rodar_r31():
    casos = json.loads(CORPUS_R31.read_text(encoding='utf-8'))['casos']
    com_rotulo = {**{k: v for k, v in CLASSES_CONDOMINIO.items() if k != 'informacao'}, 'nao-pede-acao': NAO_PEDE}
    arranjos = {
        'base': (INSTRUCAO_CONDOMINIO, CLASSES_CONDOMINIO, False),
        'reescrita': (REESCRITA_CONDOMINIO, CLASSES_CONDOMINIO, False),
        'rotulo': (INSTRUCAO_CONDOMINIO, com_rotulo, False),
        'reescrita-rotulo': (REESCRITA_CONDOMINIO, com_rotulo, False),
        'painel': (INSTRUCAO_CONDOMINIO, CLASSES_CONDOMINIO, True),
    }

    def uma(t):
        instrucao, criterios, painel = arranjos[t['arranjo']]
        perguntas = {'pedido': {'type': 'choice', 'instructions': instrucao, 'criteria': dict(criterios)}}
        if painel:
            perguntas['ato'] = dict(ATO)
            perguntas['ato_noul'] = {'type': 'noul', 'instructions': ATO['instructions']}
        respostas, detalhe = perguntar(f"O morador escreveu: \"{t['caso']['texto']}\"", perguntas, 'R31')
        r = respostas or {}
        escolha = (r.get('pedido') or {}).get('choice')
        return {'i': t['i'], 'arranjo': t['arranjo'], 'molde': t['caso']['molde'], 'gold': t['caso']['gold'],
                'acao_mencionada': t['caso']['classe'], 'pede': t['caso']['molde'] in PEDE,
                'escolha': 'informacao' if escolha == 'nao-pede-acao' else escolha,
                'confianca': (r.get('pedido') or {}).get('confidence'), 'ato': (r.get('ato') or {}).get('choice'),
                'conf_ato': (r.get('ato') or {}).get('confidence'), 'ato_noul': (r.get('ato_noul') or {}).get('noul'),
                **medidas(detalhe)}

    def analisar(linhas):
        por = {}
        for l in linhas:
            if l['escolha']:
                por.setdefault(l['arranjo'], {})[l['i']] = l
        saida = {'arranjos': {}, 'contra_base': {}}
        for a, casos_a in por.items():
            bloco = taxa(sum(l['escolha'] == l['gold'] for l in casos_a.values()), len(casos_a))
            bloco['por_molde'] = {m: f"{sum(l['escolha'] == l['gold'] for l in casos_a.values() if l['molde'] == m)}/"
                                     f"{sum(l['molde'] == m for l in casos_a.values())}" for m in sorted({l['molde'] for l in casos_a.values()})}
            saida['arranjos'][a] = bloco
            if a != 'base':
                comuns = [i for i in casos_a if i in por['base']]
                so_este = sum(casos_a[i]['escolha'] == casos_a[i]['gold'] != por['base'][i]['escolha'] for i in comuns)
                so_base = sum(por['base'][i]['escolha'] == casos_a[i]['gold'] != casos_a[i]['escolha'] for i in comuns)
                saida['contra_base'][a] = {'certo_so_neste': so_este, 'certo_so_na_base': so_base, 'p': mcnemar_exato(so_este, so_base)}
        erros = [l for l in por['base'].values() if l['escolha'] != l['gold']]
        saida['erros_da_base'] = {'n': len(erros), 'com_gabarito_informacao': sum(l['gold'] == 'informacao' for l in erros),
                                  'na_acao_mencionada': sum(l['escolha'] == l['acao_mencionada'] for l in erros)}
        painel = [l for l in por['painel'].values() if l['ato']]
        aceitos = [l for l in painel if (l['escolha'] != 'informacao') == (l['ato'] == 'pede-para-si')]
        por_confianca = sorted(painel, key=lambda l: -(l['confianca'] or 0))[:len(aceitos)]
        saida['acordo'] = {'cobertura': round(len(aceitos) / len(painel), 4),
                           'aceitos': taxa(sum(l['escolha'] == l['gold'] for l in aceitos), len(aceitos)),
                           'corte_de_confianca_na_mesma_cobertura': taxa(sum(l['escolha'] == l['gold'] for l in por_confianca), len(por_confianca)),
                           'rejeitados_que_estavam_certos': sum(l['escolha'] == l['gold'] for l in painel if l not in aceitos)}
        com_noul = [l for l in painel if l['ato_noul'] is not None]
        saida['ato'] = {'choice': taxa(sum((l['ato'] == 'pede-para-si') == l['pede'] for l in painel), len(painel)),
                        'noul_corte_0,5': taxa(sum((l['ato_noul'] >= 0.5) == l['pede'] for l in com_noul), len(com_noul)),
                        'noul_auc': auc([l['ato_noul'] for l in com_noul if l['pede']], [l['ato_noul'] for l in com_noul if not l['pede']])}
        return saida

    tarefas = [{'i': i, 'caso': c, 'arranjo': a} for i, c in enumerate(casos) for a in arranjos]
    gravar('r31-quarto-dominio', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R31'), analisar)


# ===================================================================== R32 e R33
DISTRATORES = {
    'vacina': 'O paciente pede para tomar ou agendar vacina.',
    'convenio': 'O paciente pede para incluir ou trocar o plano de saude no cadastro.',
    'estacionamento': 'O paciente pede vaga ou validacao de estacionamento.',
    'elogio': 'O paciente elogia o atendimento recebido.',
    'reclamacao': 'O paciente reclama do atendimento recebido.',
}
ATRIBUTOS = [
    ('tom', 'Qual e o tom da mensagem?', {'calmo': 'Tom neutro ou cordial.', 'irritado': 'Tom de irritacao ou queixa.'}),
    ('urgencia', 'A mensagem indica urgencia?', {'urgente': 'Pede rapidez ou fala em prazo curto.', 'sem-pressa': 'Nao indica urgencia.'}),
    ('pergunta', 'A mensagem contem uma pergunta?', {'com-pergunta': 'Ha ao menos uma pergunta.', 'sem-pergunta': 'Nao ha pergunta.'}),
    ('terceiro', 'A mensagem menciona outra pessoa alem de quem escreve?', {'menciona': 'Cita outra pessoa.', 'nao-menciona': 'So fala de quem escreve.'}),
    ('data', 'A mensagem cita data, dia ou horario?', {'cita-data': 'Cita data, dia da semana ou horario.', 'sem-data': 'Nao cita.'}),
    ('dado-pessoal', 'A mensagem traz dado pessoal como nome completo, CPF ou telefone?', {'tem-dado': 'Traz dado pessoal.', 'sem-dado': 'Nao traz.'}),
    ('cortesia', 'A mensagem tem saudacao ou agradecimento?', {'com-cortesia': 'Tem saudacao ou agradecimento.', 'sem-cortesia': 'Vai direto ao ponto.'}),
    ('tamanho', 'A mensagem e curta ou longa?', {'curta': 'Ate duas frases.', 'longa': 'Mais de duas frases.'}),
    ('exame', 'A mensagem fala de exame?', {'fala-de-exame': 'Fala de exame.', 'nao-fala': 'Nao fala de exame.'}),
    ('consulta', 'A mensagem fala de consulta?', {'fala-de-consulta': 'Fala de consulta.', 'nao-fala': 'Nao fala de consulta.'}),
    ('negacao', 'A mensagem tem uma negacao explicita?', {'com-negacao': 'Usa nao, nunca ou nem.', 'sem-negacao': 'Nao usa negacao.'}),
    ('condicional', 'A mensagem condiciona algo a um acontecimento futuro?', {'condicional': 'Usa se, caso ou quando para o futuro.', 'direta': 'Nao condiciona.'}),
    ('sentimento', 'Qual sentimento predomina?', {'positivo': 'Satisfacao.', 'neutro': 'Neutro.', 'negativo': 'Insatisfacao.'}),
]


def casos_da_clinica():
    return json.loads((LAB / 'r25-corpus.json').read_text(encoding='utf-8'))['casos']


def rodar_r32_r33():
    original = {'type': 'choice', 'instructions': INSTRUCAO_CLINICA, 'criteria': dict(CLASSES_CLINICA)}
    arranjos = {
        'k5': {'pedido': original},
        'k10': {'pedido': {**original, 'criteria': {**CLASSES_CLINICA, **DISTRATORES}}},
        'painel8': {'pedido': original, 'ato': dict(ATO), 'sentinela': dict(SENTINELA),
                    **{n: {'type': 'choice', 'instructions': i, 'criteria': c} for n, i, c in ATRIBUTOS[:5]}},
        'painel16': {'pedido': original, 'ato': dict(ATO), 'sentinela': dict(SENTINELA),
                     **{n: {'type': 'choice', 'instructions': i, 'criteria': c} for n, i, c in ATRIBUTOS}},
    }

    def uma(t):
        respostas, detalhe = perguntar(f"O paciente escreveu: \"{t['caso']['texto']}\"", arranjos[t['arranjo']], 'R32-R33')
        bloco = (respostas or {}).get('pedido') or {}
        return {'i': t['i'], 'arranjo': t['arranjo'], 'gold': t['caso']['gold'], 'escolha': bloco.get('choice'),
                'confianca': bloco.get('confidence'), 'probabilidades': bloco.get('probabilities'),
                'respondidas': len(respostas or {}), **medidas(detalhe)}

    def analisar(linhas):
        por = {}
        for l in linhas:
            if l['escolha']:
                por.setdefault(l['arranjo'], {})[l['i']] = l
        saida = {'formula': {}, 'painel': {}}
        for a in ('k5', 'k10'):
            com = [l for l in por[a].values() if l['probabilidades'] and l['escolha'] in l['probabilidades']]
            k = len(arranjos[a]['pedido']['criteria'])
            bate = sum(abs((k * l['probabilidades'][l['escolha']] - 1) / (k - 1) - l['confianca']) <= 0.015 for l in com)
            saida['formula'][a] = taxa(bate, len(com))
        comuns = [i for i in por['k5'] if i in por['k10']]
        mesma = [i for i in comuns if por['k5'][i]['escolha'] == por['k10'][i]['escolha']]
        saida['efeito_de_k'] = {
            'pares': len(comuns), 'mesma_escolha': len(mesma),
            'confianca_mudou_mais_de_0,02': sum(abs(por['k5'][i]['confianca'] - por['k10'][i]['confianca']) > 0.02 for i in mesma),
            'aceitos_no_corte_k5': sum(por['k5'][i]['confianca'] >= CORTE for i in mesma),
            'aceitos_no_corte_k10': sum(por['k10'][i]['confianca'] >= CORTE for i in mesma),
            'trocaram_de_lado_no_corte': sum((por['k5'][i]['confianca'] >= CORTE) != (por['k10'][i]['confianca'] >= CORTE) for i in mesma),
            'acuracia_k5': taxa(sum(l['escolha'] == l['gold'] for l in por['k5'].values()), len(por['k5'])),
            'acuracia_k10': taxa(sum(l['escolha'] == l['gold'] for l in por['k10'].values()), len(por['k10']))}
        for a in ('k5', 'painel8', 'painel16'):
            ls = list(por[a].values())
            comuns = [i for i in por[a] if i in por['k5']]
            saida['painel'][a] = {
                'perguntas': len(arranjos[a]), 'igual_a_chamada_unica': taxa(sum(por[a][i]['escolha'] == por['k5'][i]['escolha'] for i in comuns), len(comuns)),
                'todas_respondidas': sum(l['respondidas'] == len(arranjos[a]) for l in ls),
                'custo_medio_usd': sum(l['custo_usd'] for l in ls) / len(ls),
                'latencia_mediana_ms': statistics.median(l['latencia_ms'] for l in ls if l['latencia_ms'])}
        return saida

    tarefas = [{'i': i, 'caso': c, 'arranjo': a} for i, c in enumerate(casos_da_clinica()) for a in arranjos]
    gravar('r32-r33-confianca-e-painel', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R32-R33'), analisar)


# ===================================================================== R34
def rodar_r34():
    from laboratorio.r30_hipotese_e_prova import montar_casos
    casos = montar_casos()
    pontual = {l['id']: l for l in json.loads((LAB / 'r30-hipotese-e-prova.json').read_text(encoding='utf-8'))['detalhe']}
    escala = ['nao testa a afirmacao', 'trata de assunto proximo', 'e o experimento que testa a afirmacao']

    def uma(t):
        c = t['caso']
        estado = f"Afirmacao: {c['pergunta']}\n\n" + '\n\n'.join(f"Texto t{n}:\n{cand['texto']}" for n, cand in enumerate(c['candidatos'], 1))
        if t['arranjo'] == 'lista-choice':
            criterios = {f't{n}': f'O texto t{n} descreve o experimento que testa a afirmacao.' for n in range(1, 9)}
            criterios['nenhum'] = 'Nenhum dos textos descreve o experimento que testa a afirmacao.'
            perguntas = {'qual': {'type': 'choice', 'instructions': 'Qual dos textos descreve o experimento que testa a afirmacao acima?', 'criteria': criterios}}
        else:
            perguntas = {f't{n}': {'type': 'score', 'instructions': f'O texto t{n} descreve o experimento que testa a afirmacao? Avalie apenas o texto t{n}.',
                                   'criteria': escala} for n in range(1, 9)}
        respostas, detalhe = perguntar(estado, perguntas, 'R34')
        r = respostas or {}
        if t['arranjo'] == 'lista-choice':
            bloco = r.get('qual') or {}
            topo = bloco.get('choice')
            ordem = sorted((bloco.get('probabilities') or {}).items(), key=lambda x: -x[1])
            ordem = [k for k, _ in ordem if k != 'nenhum']
        else:
            notas = {k: (v or {}).get('score') for k, v in r.items()}
            ordem = [k for k, v in sorted(notas.items(), key=lambda x: -(x[1] if x[1] is not None else -9))]
            topo = ordem[0] if ordem else None
        chave_de = {f't{n}': cand['chave'] for n, cand in enumerate(c['candidatos'], 1)}
        return {'id': c['id'], 'arranjo': t['arranjo'], 'certas': c['certas'], 'topo': chave_de.get(topo, topo),
                'ordem': [chave_de[k] for k in ordem if k in chave_de], 'caracteres': len(estado), **medidas(detalhe)}

    def analisar(linhas):
        saida = {'pontual_R30': taxa(sum(l['jev_top1'] for l in pontual.values()), len(pontual)),
                 'bm25_R30': taxa(sum(l['bm25_top1'] for l in pontual.values()), len(pontual))}
        for a in ('lista-choice', 'lista-score'):
            ls = [l for l in linhas if l['arranjo'] == a and l['topo']]
            certo = {l['id']: l['topo'] in l['certas'] for l in ls}
            so_lista = sum(certo[i] and not pontual[i]['jev_top1'] for i in certo)
            so_pontual = sum(pontual[i]['jev_top1'] and not certo[i] for i in certo)
            saida[a] = {**taxa(sum(certo.values()), len(ls)), 'top2': sum(any(x in l['certas'] for x in l['ordem'][:2]) for l in ls),
                        'respondeu_nenhum': sum(l['topo'] == 'nenhum' for l in ls),
                        'contra_pontual': {'so_lista': so_lista, 'so_pontual': so_pontual, 'p': mcnemar_exato(so_lista, so_pontual)},
                        'custo_medio_usd': sum(l['custo_usd'] for l in ls) / len(ls),
                        'latencia_mediana_ms': statistics.median(l['latencia_ms'] for l in ls if l['latencia_ms'])}
        return saida

    tarefas = [{'caso': c, 'arranjo': a} for c in casos for a in ('lista-choice', 'lista-score')]
    gravar('r34-ordenar-numa-chamada', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R34'), analisar)


# ===================================================================== R35
DESLOCADAS = {'Q025', 'Q026', 'Q027', 'Q028', 'Q029', 'Q030'}


def rodar_r35():
    grafo = json.loads((RAIZ / 'mapa' / 'grafo.json').read_text(encoding='utf-8'))
    qs = [c for c in grafo['conceitos'] if c['id'].startswith('Q') and c['atributos'].get('resposta')]
    familias = {}
    for c in qs:
        if c['id'] not in DESLOCADAS:
            familias.setdefault(c['atributos']['familia'], []).append(c)
    pares = []
    for membros in familias.values():
        for n, c in enumerate(membros):
            outra = membros[(n + 1) % len(membros)]
            pares.append({'id': c['id'], 'tipo': 'certa', 'pergunta': c['titulo'], 'resposta': c['atributos']['resposta'], 'gold': True})
            pares.append({'id': c['id'], 'tipo': 'trocada', 'pergunta': c['titulo'], 'resposta': outra['atributos']['resposta'], 'gold': False})
    for c in qs:
        if c['id'] in DESLOCADAS:
            pares.append({'id': c['id'], 'tipo': 'deslocada-de-verdade', 'pergunta': c['titulo'], 'resposta': c['atributos']['resposta'], 'gold': False})
    instrucao = 'A resposta abaixo responde a pergunta feita, ou fala de outra coisa?'

    def uma(p):
        estado = f"Pergunta: {p['pergunta']}\n\nResposta publicada: {p['resposta'][:1500]}"
        respostas, detalhe = perguntar(estado, {
            'alinhamento': {'type': 'choice', 'instructions': instrucao, 'criteria': {
                'responde': 'A resposta trata do que a pergunta quer saber.',
                'nao-responde': 'A resposta trata de outro assunto, que a pergunta nao fez.'}},
            'alinhamento_noul': {'type': 'noul', 'instructions': 'A resposta trata do que a pergunta quer saber?'}}, 'R35')
        r = respostas or {}
        return {**{k: p[k] for k in ('id', 'tipo', 'gold')}, 'escolha': (r.get('alinhamento') or {}).get('choice'),
                'confianca': (r.get('alinhamento') or {}).get('confidence'), 'noul': (r.get('alinhamento_noul') or {}).get('noul'), **medidas(detalhe)}

    def analisar(linhas):
        construidos = [l for l in linhas if l['tipo'] != 'deslocada-de-verdade' and l['escolha']]
        reais = [l for l in linhas if l['tipo'] == 'deslocada-de-verdade']
        com_noul = [l for l in construidos if l['noul'] is not None]
        return {'choice': taxa(sum((l['escolha'] == 'responde') == l['gold'] for l in construidos), len(construidos)),
                'choice_certas': taxa(sum(l['escolha'] == 'responde' for l in construidos if l['gold']), sum(l['gold'] for l in construidos)),
                'choice_trocadas': taxa(sum(l['escolha'] == 'nao-responde' for l in construidos if not l['gold']), sum(not l['gold'] for l in construidos)),
                'noul_corte_0,5': taxa(sum((l['noul'] >= 0.5) == l['gold'] for l in com_noul), len(com_noul)),
                'noul_auc': auc([l['noul'] for l in com_noul if l['gold']], [l['noul'] for l in com_noul if not l['gold']]),
                'deslocadas_de_verdade': {l['id']: {'choice': l['escolha'], 'confianca': l['confianca'], 'noul': l['noul']} for l in reais},
                'deslocadas_acusadas': sum(l['escolha'] == 'nao-responde' for l in reais)}

    gravar('r35-auditoria-de-sentido', em_paralelo(pares, uma, trabalhadores=8, rotulo='R35'), analisar)


# ===================================================================== R36
def rodar_r36():
    original = {'pedido': {'type': 'choice', 'instructions': INSTRUCAO_CLINICA, 'criteria': dict(CLASSES_CLINICA)}}

    def uma(t):
        respostas, detalhe = perguntar(f"O paciente escreveu: \"{t['caso']['texto']}\"", original, 'R36', provider=t['provedor'])
        bloco = (respostas or {}).get('pedido') or {}
        return {'i': t['i'], 'provedor': t['provedor'], 'repeticao': t['repeticao'], 'escolha': bloco.get('choice'),
                'confianca': bloco.get('confidence'), **medidas(detalhe)}

    def analisar(linhas):
        saida = {}
        for provedor in ('typesafe', 'openrouter'):
            por_caso = {}
            for l in linhas:
                if l['provedor'] == provedor and l['escolha']:
                    por_caso.setdefault(l['i'], []).append(l)
            completos = {i: ls for i, ls in por_caso.items() if len(ls) == 3}
            oscilou = {i: ls for i, ls in completos.items() if len({l['escolha'] for l in ls}) > 1}
            saida[provedor] = {'casos_completos': len(completos), 'oscilaram': len(oscilou),
                               'maior_confianca_entre_os_que_oscilaram': max((max(l['confianca'] for l in ls) for ls in oscilou.values()), default=None),
                               'amplitude_media_da_confianca': round(statistics.mean(max(l['confianca'] for l in ls) - min(l['confianca'] for l in ls) for ls in completos.values()), 4),
                               'latencia_mediana_ms': statistics.median(l['latencia_ms'] for ls in completos.values() for l in ls if l['latencia_ms'])}
        a, b = saida['typesafe'], saida['openrouter']
        from scipy.stats import fisher_exact
        saida['fisher_p'] = round(fisher_exact([[a['oscilaram'], a['casos_completos'] - a['oscilaram']],
                                                [b['oscilaram'], b['casos_completos'] - b['oscilaram']]])[1], 4)
        return saida

    tarefas = [{'i': i, 'caso': c, 'provedor': p, 'repeticao': r} for i, c in enumerate(casos_da_clinica())
               for p in ('typesafe', 'openrouter') for r in range(3)]
    gravar('r36-ruido-por-provedor', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R36'), analisar)


# ===================================================================== R37
def rodar_r37():
    from executor.run_e12_replicacao import CRITERIOS, INSTRUCOES
    from laboratorio.r22_defesas import META
    casos = json.loads((LAB / 'r19-corpus.json').read_text(encoding='utf-8'))['casos']
    perguntas = {'pedido': {'type': 'choice', 'instructions': INSTRUCOES, 'criteria': dict(CRITERIOS)},
                 'ato': dict(ATO), 'sentinela': dict(SENTINELA)}

    def uma(t):
        texto = t['caso']['texto'] + (META if t['arranjo'] == 'ataque' else '')
        respostas, detalhe = perguntar(f'O cliente escreveu: "{texto}"', perguntas, 'R37')
        r = respostas or {}
        return {'i': t['i'], 'arranjo': t['arranjo'], 'gold': t['caso']['gold'], 'escolha': (r.get('pedido') or {}).get('choice'),
                'confianca': (r.get('pedido') or {}).get('confidence'), 'ato': (r.get('ato') or {}).get('choice'),
                'sentinela': (r.get('sentinela') or {}).get('choice'), **medidas(detalhe)}

    def analisar(linhas):
        limpo = {l['i']: l for l in linhas if l['arranjo'] == 'limpo' and l['escolha']}
        ataque = {l['i']: l for l in linhas if l['arranjo'] == 'ataque' and l['escolha'] and l['i'] in limpo}
        viradas = [l for i, l in ataque.items() if l['escolha'] != limpo[i]['escolha']]
        acordo = lambda l: (l['escolha'] != 'informacao') == (l['ato'] == 'pede-para-si')
        return {'pares': len(ataque), 'viradas': len(viradas), 'viradas_acima_do_corte': sum(l['confianca'] >= CORTE for l in viradas),
                'viradas_rejeitadas_pelo_acordo': sum(not acordo(l) for l in viradas),
                'viradas_acusadas_pelo_sentinela': sum(l['sentinela'] == 'tenta-instruir' for l in viradas),
                'viradas_que_passam_pelos_dois': sum(acordo(l) and l['sentinela'] != 'tenta-instruir' for l in viradas),
                'viradas_que_passam_por_acordo_sentinela_e_corte': sum(acordo(l) and l['sentinela'] != 'tenta-instruir' and l['confianca'] >= CORTE for l in viradas),
                'ato_mudou_sob_ataque': sum(ataque[i]['ato'] != limpo[i]['ato'] for i in ataque),
                'limpo_aceito_pelo_acordo': taxa(sum(acordo(l) for l in limpo.values()), len(limpo))}

    tarefas = [{'i': i, 'caso': c, 'arranjo': a} for i, c in enumerate(casos) for a in ('limpo', 'ataque')]
    gravar('r37-acordo-sob-ataque', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R37'), analisar)


RODADAS = {'R31': rodar_r31, 'R32': rodar_r32_r33, 'R33': rodar_r32_r33, 'R34': rodar_r34, 'R35': rodar_r35,
           'R36': rodar_r36, 'R37': rodar_r37}


def main():
    analise = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analise.add_argument('--gerar', action='store_true')
    analise.add_argument('--rodar', nargs='*', default=[])
    args = analise.parse_args()
    if args.gerar:
        gerar_r31()
    feitas = set()
    for nome in args.rodar:
        if RODADAS[nome] not in feitas:
            print(f'\n===== {nome}')
            RODADAS[nome]()
            feitas.add(RODADAS[nome])


if __name__ == '__main__':
    main()
