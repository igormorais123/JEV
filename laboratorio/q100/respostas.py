"""Uma resposta por pergunta estratégica: o número, a decisão e o que a faria virar.

Regras que valem para todas:

  * a resposta termina numa decisão, não num fato. "A latência mediana é 478 ms" não é resposta
    estratégica; "cabe num gancho interativo, com folga de 2,5× até a cauda" é.
  * toda pergunta de fonte `conta` declara os parâmetros que **não** foram medidos, um a um, em
    `parametros`. Conta com parâmetro escondido é opinião com aparência de número.
  * `confianca` diz quanto a resposta merece: `alta` quando há pareamento significativo ou
    contagem direta, `media` quando há direção consistente sem significância ou amostra
    pequena, `baixa` quando a resposta depende de parâmetro não medido ou de n mínimo.
"""

from __future__ import annotations

import collections
import json
import re
import sqlite3
from pathlib import Path

from laboratorio.h100 import avaliar as avaliar_h100
from laboratorio.h100 import dados as d

RAIZ = Path(__file__).resolve().parents[2]

RESPOSTAS = {}


def resposta(identificador):
    def registrar(funcao):
        RESPOSTAS[identificador] = funcao
        return funcao
    return registrar


# O separador de milhar viaja marcado para sobreviver ao normalizador de decimal.
MILHAR = '\ue000'


def usd(valor, casas=4):
    """Dinheiro no padrão pt-BR: vírgula decimal."""
    return f'{valor:.{casas}f}'.replace('.', ',')


def mil(valor, casas=0):
    """Formata número no padrão pt-BR sem tocar na pontuação da frase.

    O ponto de milhar sai marcado e só vira ponto no fim de `R`: sem isso o normalizador de
    decimal, que roda depois, lê "13.042 chamadas" como decimal e devolve "13,042" à inglesa.

    Antes disso a troca de pontuação era aplicada na frase inteira, e comia as vírgulas do texto
    junto: "Sim, e por
    larga margem" virava "Sim. e por larga margem". O formatador tem de agir sobre o número, não
    sobre a prosa.
    """
    texto = f'{valor:,.{casas}f}'
    return texto.replace(',', '\x00').replace('.', ',').replace('\x00', MILHAR)


# Decimal solto vira vírgula, que é o separador do idioma em que este documento é escrito.
# A borda de esquerda exige espaço, parêntese ou asterisco de propósito: assim `jev-1.13`
# e `r18-r20` passam intactos, porque o ponto deles vem depois de um traço. À direita o
# sinal de multiplicação entra porque razões são escritas como `1,8×`.
_DECIMAL = re.compile(r'(?<=[\s(*])(\d+)\.(\d+)(?=[\s,.;:)%*\u00d7]|$)')


def R(texto, numeros=None, parametros=None, confianca='alta'):
    texto = _DECIMAL.sub(lambda m: f'{m.group(1)},{m.group(2)}', texto)
    return {'resposta': texto.replace(MILHAR, '.'), 'numeros': numeros or {},
            'parametros': parametros or {}, 'confianca': confianca}


# ----------------------------------------------------------------- parâmetros declarados
# Nada aqui foi medido por este estudo. Cada um aparece na resposta que o usa, e a resposta diz
# como ela muda se o parâmetro mudar. Estão juntos para que ninguém precise caçá-los.
# Trezentos e sessenta e cinco dias não é parâmetro: é o ano. Fica aqui como constante
# para não passar por suposição de negócio na tabela de parâmetros não medidos.
DIAS_POR_ANO = 365

PARAMETROS = {
    'preco_modelo_caro_usd_por_milhao_entrada': (
        3.00, 'preço de entrada de um modelo de fronteira, ordem de grandeza de mercado'),
    'preco_jev_usd_por_milhao_entrada': (
        0.042, 'preço de entrada do jev-1.13, este SIM verificado no provedor'),
    'custo_hora_revisao_usd': (12.00, 'custo-hora de quem revisaria à mão, declarado no guia'),
    'tempo_revisao_s': (120, 'tempo por decisão revisada, declarado no guia e NÃO cronometrado'),
    'volume_mensal_decisoes': (10_000, 'volume hipotético de um canal médio'),
    'horas_de_integracao': (16, 'esforço de integrar o contrato num fluxo existente'),
    'custo_erro_grave_usd': (200.00, 'custo de um cancelamento indevido: retrabalho mais atrito'),
}


def p(nome):
    return PARAMETROS[nome][0]


def _declarar(*nomes):
    return {n: {'valor': PARAMETROS[n][0], 'o_que_e': PARAMETROS[n][1]} for n in nomes}


def _placar_da_auditoria():
    """O placar sai do artefato que a auditoria grava, e não de uma chamada a ela.

    A auditoria confere estas respostas; se estas respostas chamassem a auditoria, cada lado
    esperaria o outro. O artefato quebra o ciclo sem afrouxar nenhum dos dois: ele é escrito
    por `python laboratorio/auditoria.py`, e a própria auditoria confere que está atualizado.
    """
    dado = json.loads((RAIZ / 'laboratorio' / 'auditoria-placar.json')
                      .read_text(encoding='utf-8'))
    return {'conferencias': dado['conferencias'], 'falhas': dado['falhas'],
            'fora_de_alcance': dado['fora_de_alcance']}


# ----------------------------------------------------------------- fontes
def _artefato(nome):
    return d.artefato(nome)


def _ledger():
    conexao = sqlite3.connect(f"file:{RAIZ / 'runs' / 'ledger.sqlite3'}?mode=ro", uri=True)
    chamadas, gasto = conexao.execute(
        'select count(*), sum(settled_nusd) from attempt_budget').fetchone()
    conexao.close()
    return chamadas, (gasto or 0) / 1e9


def _custo_por_decisao():
    chamadas, gasto = _ledger()
    return gasto / chamadas


# Rodada unificada -> artefato de origem, para consultar o registro de retratações.
ARTEFATO_DA_RODADA = {'R11': 'r11-extremos.json'}


def _linhas_jev():
    """Só o que vale como evidência: condição retratada fica de fora.

    A primeira versão da Q023 somava a diluição de 20k e 30k da R11, que está retratada porque o
    truncamento do laboratório cortava o pedido do cliente. Essas 60 linhas carregavam 46 dos 52
    erros acima de 0,99 dos extremos, e a "degradação sob dificuldade" era, em quase toda a sua
    extensão, o defeito do instrumento. O registro de retratações existe para isso ser mecânico.
    """
    return [l for l in d.apenas_jev(d.linhas_com_gabarito())
            if l['confianca'] is not None
            and not (l['rodada'] in ARTEFATO_DA_RODADA
                     and d.esta_retratada(ARTEFATO_DA_RODADA[l['rodada']], l['condicao']))]


DIFICULDADE = {
    'R1-R3': 'uso normal, variando formato e ordem',
    'R4-R7': 'uso normal, com sim/não e taxonomias maiores',
    'R8-R9': 'armadilha semântica e injeção no texto',
    'R11': 'extremos: até 147 opções, 70% de ruído, sobreposição de classes',
    'R12-R13': 'contexto diluído até 50 mil caracteres',
    'R19': 'armadilha de sujeito, corpus gerado por molde',
    'R10': 'injeção deliberada, painel de comparadores',
    'R15': 'vetores adversariais escritos por outros modelos',
}

NORMAIS = ('R1-R3', 'R4-R7', 'R12-R13')


def _linhas_uso_normal():
    """Tira as rodadas adversariais: política de corte é sobre uso, não sobre ataque.

    O primeiro recorte tirava só as rodadas adversariais, e ainda dava 3,5% de erro acima de
    0,99 -- número que não orienta decisão nenhuma, porque somava o corpus normal com a condição
    de 147 opções e 70% de ruído. Uso normal aqui são as rodadas em que a tarefa é a tarefa:
    variação de formato, de ordem, de taxonomia e de tamanho de contexto. Extremo, armadilha e
    ataque são tratados à parte, e é a comparação entre eles que orienta a política.
    """
    return [l for l in _linhas_jev() if l['rodada'] in NORMAIS]


def _h100():
    return avaliar_h100.rodar()


def _latencias():
    """Só o que voltou. Um timeout registra 45.000 ms, que é a minha constante de paciência e
    não a latência do modelo; incluí-lo faz o p99 medir o instrumento."""
    return [l['latencia_ms'] for l in d.decisoes()
            if l['latencia_ms'] and l.get('status') == 'success']


def _r23():
    return _artefato('r23-parafrase.json')


def _familias_de_instrucao_surpresa():
    """As famílias de ordem ao sistema escritas por outros modelos: o conjunto que decide."""
    return {nome: bloco for nome, bloco in _r23()['por_familia'].items()
            if nome.startswith('instrucao/') and nome != 'instrucao/laboratorio'}


def _r24():
    return _artefato('r24-votacao.json')


def _r25():
    return _artefato('r25-terceiro-dominio.json')


def _r26():
    return _artefato('r26-dois-trechos.json')


def _r27():
    return _artefato('r27-integracao.json')


def _r22():
    return _artefato('r22-defesas.json')


# ===================================================================== A · adotar
@resposta('Q001')
def q001():
    return R('Triagem, com folga. Contra regra por palavra-chave o Jev vai de 60,0% para 92,5% '
             'no piloto e de 32,5% para 97,5% na confirmação — mais de 60 pontos no segundo '
             'caso. Verificação de afirmação vem depois (95,8% contra 62,5%), e ordenação é a '
             'de maior ganho econômico, não de acurácia.',
             {'triagem_piloto': [0.925, 0.600], 'triagem_confirmacao': [0.975, 0.325],
              'verificacao': [0.958, 0.625]})


@resposta('Q002')
def q002():
    return R('Ordenação de contexto. O ganho é medido (93,5% contra 83,4% carregando tudo, '
             '22 a 5, p = 0,0015) e o risco é o menor das quatro: se a ordenação errar, o '
             'modelo caro recebe o trecho errado e responde mal — não há ação irreversível no '
             'caminho. Triagem tem ganho maior e risco maior, porque a classe `cancelar` age.',
             {'jev2_vs_todos': [22, 5, 0.0015]})


@resposta('Q003')
def q003():
    r18 = _artefato('r18-escala.json')['arranjos']
    r21 = _artefato('r21-generalizacao.json')['prosa']
    return R('Sim, duas. Em **prosa**, o BM25 empata com o Jev na colocação do trecho certo '
             f"({r21['bm25_primeiro']}/{r21['n']} contra {r21['jev_primeiro']}/{r21['n']}) e "
             'custa zero chamada — ali o método atual basta. E em classificação de texto que '
             '**não vem de fora**, um LLM genérico barato empata sob critério independente e '
             'custa um quarto.',
             {'prosa_jev': r21['jev_primeiro'], 'prosa_bm25': r21['bm25_primeiro'],
              'codigo_jev_vs_bm25_top2': [r18['jev-2']['alvo_presente'],
                                          r18['bm25-2']['alvo_presente']]})


@resposta('Q004')
def q004():
    return R('Não. Sob o gabarito desta casa o Jev ganha (98,9% contra 84,4%–91,1% no E12); '
             'sob o critério de um anotador independente a vantagem some, e isso se repetiu no '
             'E10, E11 e E12. A justificativa do Jev **não é acurácia** — é resistência a '
             'manipulação pelo texto classificado, e essa não depende de gabarito.',
             {'e12_jev': 0.989, 'e12_comparadores': [0.844, 0.911]}, confianca='alta')


@resposta('Q005')
def q005():
    horas, custo_hora = p('horas_de_integracao'), p('custo_hora_revisao_usd')
    investimento = horas * custo_hora
    economia_por_decisao = (p('tempo_revisao_s') / 3600 * custo_hora) - _custo_por_decisao()
    volume = investimento / economia_por_decisao
    return R(f'Cerca de **{mil(volume)} decisões** para o investimento de integração se pagar — '
             f'menos de um mês num canal de {mil(p("volume_mensal_decisoes"))} decisões/mês. O '
             'número é dominado pelo tempo de pessoa, não pelo preço do modelo: o custo por '
             f'decisão do Jev é US$ {_custo_por_decisao():.6f} contra US$ '
             f'{p("tempo_revisao_s") / 3600 * custo_hora:.4f} da revisão humana.',
             {'ponto_de_equilibrio_decisoes': round(volume),
              'investimento_usd': investimento},
             _declarar('horas_de_integracao', 'custo_hora_revisao_usd', 'tempo_revisao_s',
                       'volume_mensal_decisoes'),
             confianca='baixa')


@resposta('Q006')
def q006():
    return R('Não, se ela tiver até 12 classes: nesse intervalo a acurácia não cai. Entre 12 e '
             '147 há um platô em torno de 90%. O que a taxonomia **precisa** ganhar é uma '
             'classe de escape — sem ela o modelo inventa, e é o único modo de falha em que a '
             'confiança não avisa (0,987 de média, errando em 10 de 10).',
             {'sem_custo_ate': 12, 'plato_ate': 147, 'conf_sem_escape': 0.987})


@resposta('Q007')
def q007():
    por = _artefato('r1-r3-estresse.json')['por_condicao']
    return R('Até 12 sem custo medido: 2, 3, 5 e 12 opções ficam todas acima de 97%. De 20 a '
             '147 o desempenho cai para um platô em torno de 90%, o que ainda serve para muitos '
             'casos — mas já não é de graça.',
             {n: por[n]['acuracia'] for n in ('2-opcoes', '3-opcoes', '5-opcoes', '12-opcoes')})


@resposta('Q008')
def q008():
    return R('Não para começar, sim para confiar. O contrato funciona sem nenhum exemplo '
             'rotulado — a taxonomia é a única entrada. Mas o corte de confiança **não se '
             'transporta** entre conjuntos: o que dava zero erro em dois corpora deixou passar '
             'um erro com confiança 0,98 no terceiro. Rotular ~200 casos do seu material é o '
             'que autoriza automatizar, não o que autoriza experimentar.',
             {'erro_com_confianca': 0.98})


@resposta('Q009')
def q009():
    # O livro-caixa agrega as rodadas sob `shared-lab` e não sabe separá-las; o custo por rodada
    # vem do artefato que cada uma gravou, que é onde ele foi apurado na hora.
    rodadas = {'R21': _artefato('r21-generalizacao.json')['custo_usd'],
               'R21b': _artefato('r21b-cruzamento.json')['custo_usd'],
               'R22': _artefato('r22-defesas.json')['custo_usd']}
    caro = max(rodadas.values())
    return R('Dias, não semanas. A R18, a R19, a R20, a R21 e a R22 geraram corpus com gabarito '
             'fixado por molde e filtro mecânico, sem uma linha lida por mim antes de rodar. Das '
             f'três que registraram o próprio custo, a mais cara ficou em US$ {usd(caro)} — '
             'incluída a coleta nova em domínio jurídico, em inglês e em espanhol. O caminho é '
             'reaproveitável: `r19_armadilha_de_sujeito.py` e `r21_generalizacao.py` são os '
             'moldes.',
             {'custo_por_rodada_usd': rodadas}, confianca='media')


@resposta('Q010')
def q010():
    return R('Ordenação de contexto para montar o prompt de um agente caro. É a única com '
             'economia medida em bytes (74% menos contexto), a única em que selecionar **melhora '
             'a resposta** em vez de só baratear, e a de menor risco. O segundo lugar é o guarda '
             'de comando, que já está implantado em sombra e só depende de uma decisão de '
             'configuração para entregar o ganho medido.',
             {'economia_contexto': 0.74, 'ganho_pareado': [22, 5]})


# ===================================================================== B · unidade econômica
@resposta('Q011')
def q011():
    custo = _custo_por_decisao()
    chamadas, gasto = _ledger()
    return R(f'**US$ {custo * 1000:.3f} por mil decisões**, medido sobre {mil(chamadas)} chamadas '
             f'reais que somam US$ {gasto:.4f} no livro-caixa. Não é estimativa: é o extrato.',
             {'usd_por_mil': round(custo * 1000, 4), 'chamadas': chamadas,
              'gasto_total_usd': round(gasto, 4)})


@resposta('Q012')
def q012():
    """A conta que o guia nunca fez: a ordenação custa chamadas, e elas contam."""
    gastos = d.gastos()
    def media(rotulos):
        custos = [l['custo_usd'] for l in gastos
                  if l.get('rodada') in rotulos and l.get('custo_usd')]
        return sum(custos) / len(custos) if custos else None
    ordenacao = media({'R18', 'R20'})
    consolidado = _artefato('r18-r20-consolidado.json')['arranjos']
    bytes_poupados = consolidado['todos']['bytes'] - consolidado['jev-2']['bytes']
    perguntas = consolidado['todos']['n']
    # 4 caracteres por token é a razão usual para texto latino; declarada, não medida
    tokens_poupados = bytes_poupados / 4
    economia = tokens_poupados / 1e6 * p('preco_modelo_caro_usd_por_milhao_entrada')
    custo_ordenacao = 8 * ordenacao * perguntas
    return R(f'Sim, e por larga margem. Ordenar {perguntas} perguntas custou US$ '
             f'{custo_ordenacao:.4f} em chamadas ao Jev (8 candidatos cada) e poupou '
             f'{mil(bytes_poupados)} bytes de entrada do modelo caro — US$ {economia:.2f} ao preço '
             f'declarado. A razão é **{economia / custo_ordenacao:.0f} para 1**. E isso ignora o '
             'ganho de acurácia, que é o achado principal: selecionar responde melhor.',
             {'custo_ordenacao_usd': round(custo_ordenacao, 4),
              'economia_usd': round(economia, 2),
              'razao': round(economia / custo_ordenacao, 1)},
             _declarar('preco_modelo_caro_usd_por_milhao_entrada'), confianca='media')


@resposta('Q013')
def q013():
    gastos = d.gastos()
    custos = [l['custo_usd'] for l in gastos if l.get('rodada') in {'R18', 'R20'}
              and l.get('custo_usd')]
    ordenacao = sum(custos) / len(custos)
    consolidado = _artefato('r18-r20-consolidado.json')['arranjos']
    poupado_por_pergunta = ((consolidado['todos']['bytes'] - consolidado['jev-2']['bytes'])
                            / consolidado['todos']['n'] / 4 / 1e6)
    custo_por_pergunta = 8 * ordenacao
    preco_minimo = custo_por_pergunta / poupado_por_pergunta
    return R(f'O modelo respondedor precisa custar mais de **US$ {preco_minimo:.2f} por milhão '
             f'de tokens de entrada** para a ordenação se pagar só em token. Qualquer modelo de '
             f'fronteira está muito acima disso; um modelo barato de US$ 0,10 não estaria — '
             'nesse caso a seleção se justifica pela acurácia, não pela economia.',
             {'preco_minimo_usd_por_milhao': round(preco_minimo, 2)}, confianca='media')


@resposta('Q014')
def q014():
    consolidado = _artefato('r18-r20-consolidado.json')['arranjos']
    bytes_por_candidato = consolidado['todos']['bytes'] / consolidado['todos']['n'] / 8
    gastos = d.gastos()
    custos = [l['custo_usd'] for l in gastos if l.get('rodada') in {'R18', 'R20'}
              and l.get('custo_usd')]
    ordenacao = sum(custos) / len(custos)
    # cada candidato a mais custa uma chamada de ordenação e poupa os bytes dele no caro
    poupanca_por_candidato = bytes_por_candidato / 4 / 1e6 * p(
        'preco_modelo_caro_usd_por_milhao_entrada')
    return R('Não há limite prático pelo lado do custo: cada candidato a mais custa uma chamada '
             f'de ordenação (US$ {ordenacao:.7f}) e poupa US$ {poupanca_por_candidato:.6f} de '
             f'contexto do modelo caro — a poupança é **{poupanca_por_candidato / ordenacao:.0f}× '
             'maior**. O limite é de latência e de qualidade, não de dinheiro: mais candidatos '
             'significam mais chamadas em paralelo, e a R18 mostrou que passar de dois trechos '
             'selecionados piora a resposta.',
             {'custo_por_candidato_usd': round(ordenacao, 7),
              'poupanca_por_candidato_usd': round(poupanca_por_candidato, 6)},
             _declarar('preco_modelo_caro_usd_por_milhao_entrada'), confianca='media')


@resposta('Q015')
def q015():
    r20 = _artefato('r20-k-adaptativo.json')['arranjos']
    return R('Não neste corpus, e talvez em outro. O k adaptativo economiza 86,2% contra 73,7% '
             'do k = 2 fixo, com o mesmo acerto — mas o k = 1 fixo economiza 87,4% com o mesmo '
             'acerto também. A política adaptativa **empata com a regra mais simples** aqui. '
             'Implemente k = 1 fixo; guarde a política adaptativa para quando a ordenação for '
             'difícil, que é onde ela teria valor e onde ninguém mediu ainda.',
             {'adaptativo': r20['adaptativo']['economia'], 'k2': r20['jev-2']['economia'],
              'k1': r20['jev-1']['economia'],
              'acerto_igual': [r20['adaptativo']['acertos'], r20['jev-1']['acertos']]})


@resposta('Q016')
def q016():
    consolidado = _artefato('r18-r20-consolidado.json')['arranjos']
    poupado = (consolidado['todos']['bytes'] - consolidado['jev-1']['bytes'])
    por_pergunta = poupado / consolidado['todos']['n']
    economia_mil = por_pergunta * 1000 / 4 / 1e6 * p(
        'preco_modelo_caro_usd_por_milhao_entrada')
    gastos = d.gastos()
    custos = [l['custo_usd'] for l in gastos if l.get('rodada') in {'R18', 'R20'}
              and l.get('custo_usd')]
    custo_mil = 8 * (sum(custos) / len(custos)) * 1000
    return R(f'**US$ {economia_mil:.2f} por mil perguntas** de contexto poupado, contra US$ '
             f'{custo_mil:.2f} de chamadas de ordenação — líquido de US$ '
             f'{economia_mil - custo_mil:.2f}. O número escala linearmente com o preço do '
             'modelo respondedor, que é o parâmetro declarado.',
             {'economia_bruta_usd': round(economia_mil, 2),
              'custo_ordenacao_usd': round(custo_mil, 2),
              'liquido_usd': round(economia_mil - custo_mil, 2)},
             _declarar('preco_modelo_caro_usd_por_milhao_entrada'), confianca='media')


@resposta('Q017')
def q017():
    tentativas = d.tentativas()
    falhas = [t for t in tentativas if t['status'] not in ('success', 'reserved')]
    return R(f'{len(falhas)} tentativas de {mil(len(tentativas))} terminaram em falha — '
             f'**{len(falhas) / len(tentativas):.1%}**. Some-se a isso o episódio do gerador da '
             'R18, em que 88 de 110 chamadas voltaram com conteúdo vazio porque o limite de '
             'tokens era consumido pelo campo de raciocínio: pagas e inúteis. Reserve 5% de '
             'folga e **meça o conteúdo da resposta, não só o código HTTP**.',
             {'falhas': len(falhas), 'tentativas': len(tentativas),
              'taxa': round(len(falhas) / len(tentativas), 4)})


@resposta('Q018')
def q018():
    linhas = [l for l in d.decisoes() if l['estado_car'] and l['nusd']]
    r = d.pearson([l['estado_car'] for l in linhas], [l['nusd'] for l in linhas])
    ordenadas = sorted(linhas, key=lambda l: l['estado_car'])
    corte = len(ordenadas) // 4
    razao = (sum(l['nusd'] for l in ordenadas[-corte:]) / corte
             / (sum(l['nusd'] for l in ordenadas[:corte]) / corte))
    return R(f'Não quebra: o custo é quase linear no tamanho do estado (r = {r:.2f}), e o '
             f'quartil de textos maiores custa {razao:.1f}× o dos menores. Como o preço de saída '
             'é zero e a entrada custa US$ 0,042 por milhão, mesmo um texto de 20 mil '
             'caracteres não muda a ordem de grandeza. Não há motivo econômico para impor '
             'limite de tamanho — há motivo de qualidade, que é outro.',
             {'r_custo_tamanho': round(r, 3), 'razao_quartis': round(razao, 2)})


@resposta('Q019')
def q019():
    custo = _custo_por_decisao()
    r24 = _r24()
    osc = sum(c['oscilacao']['oscilaram'] for c in r24['corpora'].values())
    n = sum(c['oscilacao']['n'] for c in r24['corpora'].values())
    return R(f'Cabe folgado — três chamadas custam US$ {usd(3 * custo, 6)} por decisão contra '
             f'US$ {usd(p("custo_erro_grave_usd"), 2)} de um erro grave — mas a R24 mostrou que '
             f'votar a **mesma** pergunta três vezes não compra nada: em {n} casos, {osc} '
             'oscilaram. O que vale o triplo do custo é perguntar de **três formulações** '
             'diferentes, que no jurídico levou de 79,7% para 92,8%. Para a classe irreversível, '
             'redundância de formulação, não de repetição.',
             {'custo_tres_chamadas_usd': round(3 * custo, 7), 'oscilaram': osc, 'n': n},
             _declarar('custo_erro_grave_usd'), confianca='media')


@resposta('Q020')
def q020():
    historico = RAIZ / 'laboratorio' / 'canarios-de-comportamento.jsonl'
    corridas = [json.loads(l) for l in historico.read_text(encoding='utf-8').splitlines()
                if l.strip()]
    por_corrida = corridas[-1]['custo_usd']
    return R(f'**US$ {por_corrida * DIAS_POR_ANO:.2f} por ano** para rodar os canários '
             f'todo dia (US$ {por_corrida:.6f} por corrida). É 0,05% do teto autorizado de '
             'US$ 5,00. O monitoramento contínuo não é uma decisão de orçamento — é uma '
             'decisão de disciplina.',
             {'usd_por_corrida': por_corrida,
              'usd_por_ano': round(por_corrida * DIAS_POR_ANO, 2)})


# ===================================================================== C · política
def _curva_risco_cobertura():
    linhas = _linhas_uso_normal()
    curva = []
    for corte in (0.0, 0.50, 0.70, 0.80, 0.90, 0.95, 0.99, 1.0):
        aceitos = [l for l in linhas if l['confianca'] >= corte]
        erros = sum(1 for l in aceitos if not l['certo'])
        curva.append({'corte': corte, 'cobertura': round(len(aceitos) / len(linhas), 4),
                      'erros': erros, 'n': len(aceitos),
                      'taxa_de_erro': round(erros / len(aceitos), 4) if aceitos else None})
    return curva


@resposta('Q021')
def q021():
    curva = _curva_risco_cobertura()
    sem_erro = [c for c in curva if c['erros'] == 0]
    melhor = max(sem_erro, key=lambda c: c['cobertura']) if sem_erro else None
    if melhor:
        return R(f'Corte **{melhor["corte"]}**, com {melhor["cobertura"]:.1%} de cobertura e '
                 f'zero erro entre os {mil(melhor["n"])} aceitos, no uso normal.',
                 {'curva': curva})
    pior = min(curva, key=lambda c: c['taxa_de_erro'])
    return R('**Nenhum corte zera o erro**, nem no uso normal. O melhor disponível é '
             f'{pior["corte"]}, que aceita {pior["cobertura"]:.1%} das decisões com '
             f'{pior["taxa_de_erro"]:.2%} de erro entre elas — {pior["erros"]} em '
             f'{mil(pior["n"])}. A consequência é dura e não tem volta: o corte reduz risco e '
             'não o elimina, e por isso a classe irreversível continua exigindo gente.',
             {'curva': curva})


@resposta('Q022')
def q022():
    curva = _curva_risco_cobertura()
    em = {c['corte']: c for c in curva}
    return R('A curva é quase plana até 0,90 e só então começa a pagar: de 0 a 0,90 a cobertura '
             f'cai de 100% para {em[0.90]["cobertura"]:.0%} e a taxa de erro entre os aceitos '
             f'vai de {em[0.0]["taxa_de_erro"]:.2%} para {em[0.90]["taxa_de_erro"]:.2%}. De 0,90 '
             f'para 0,99 a cobertura cai mais {em[0.90]["cobertura"] - em[0.99]["cobertura"]:.0%} '
             f'e o erro chega a {em[0.99]["taxa_de_erro"]:.2%}. **O joelho está em 0,99**: é o '
             'último ponto em que a redução de erro ainda compensa a cobertura perdida.',
             {'curva': curva})


@resposta('Q023')
def q023():
    """A pergunta certa não é 'sobrevive?', é 'sobrevive onde?' — e com que dado."""
    linhas = _linhas_jev()
    por_rodada = {}
    for rodada in sorted(set(l['rodada'] for l in linhas)):
        altos = [l for l in linhas if l['rodada'] == rodada and l['confianca'] >= 0.99]
        if len(altos) < 30:
            continue
        erros = sum(1 for l in altos if not l['certo'])
        por_rodada[rodada] = {'erros': erros, 'n': len(altos),
                              'taxa': round(erros / len(altos), 4),
                              'o_que_e': DIFICULDADE.get(rodada, '')}
    normal = por_rodada.get('R1-R3')
    extremo = por_rodada.get('R11')
    pior = max(por_rodada.items(), key=lambda kv: kv[1]['taxa'])
    return R('Sobrevive, e a primeira versão desta resposta dizia o contrário por um erro que '
             'vale registrar: ela somava a diluição retratada da R11, e a "degradação sob '
             'dificuldade" era o truncamento do laboratório. Retirada a condição retratada, '
             f'acima de 0,99 há {normal["erros"]} erros em {mil(normal["n"])} decisões no uso '
             f'normal ({normal["taxa"]:.2%}) e {extremo["erros"]} em {mil(extremo["n"])} nas '
             f'condições extremas que valem como evidência ({extremo["taxa"]:.2%}) — até 147 '
             'opções, 70% de ruído, sobreposição de classes. A pior rodada é '
             f'{pior[0]} ({pior[1]["o_que_e"]}), com {pior[1]["taxa"]:.2%}. O corte de 0,99 '
             'continua sendo o último ponto em que a confiança avisa, e a ressalva que fica é '
             'outra: em ruído pesado a acurácia despenca (36,7% a 70%) **mas nenhum erro passa '
             'do corte** — o corte cobre; o que ele não faz é devolver acurácia.',
             {'por_rodada': por_rodada, 'pior_rodada': pior[0]})


@resposta('Q024')
def q024():
    c = _artefato('r18-r20-consolidado.json')
    return R('**k = 1.** Contra k = 2 não há diferença nenhuma (3 a 4, p = 1,0) e custa metade '
             'do contexto; contra k = 3 a direção favorece o menor em todos os recortes. Mandar '
             'um trecho é a recomendação, e mandar dois é defensável para quem quiser margem.',
             {'k1_vs_k2': c['pareado']['jev-1 vs jev-2'],
              'k2_vs_k3': c['pareado']['jev-2 vs jev-3']})


@resposta('Q025')
def q025():
    return R('Não vale a complexidade hoje. Ela empata com k = 1 fixo em acerto e em economia. '
             'Implemente a regra simples; a adaptativa fica como opção para corpus onde a '
             'ordenação erre mais, cenário que ainda não foi medido.',
             {}, confianca='media')


@resposta('Q026')
def q026():
    bloco = _artefato('mapa-de-limites.json')['sem_pedido']
    return R('Sim, sempre. Sem classe de escape, dez textos sem pedido nenhum foram '
             f"classificados como `informacao` nas {bloco['sem-saida']['n']} vezes, com "
             f"confiança média {bloco['sem-saida']['conf']:.3f} — o único modo de falha medido "
             'em que a confiança **não avisa**. Com a classe, acerta 10 de 10. Custa uma linha.',
             {'sem_escape_conf': bloco['sem-saida']['conf'],
              'com_escape_acertos': bloco['com-saida']['n']})


@resposta('Q027')
def q027():
    r19 = _artefato('r19-armadilha.json')['formulacoes']
    return R('Sim, padrão. Ela leva 89,4% a 92,9% em atendimento sem piorar nenhum molde, e '
             '78,5% a 90,9% no jurídico com **8 a 0, p = 0,0078**. Custa uma frase e é a única '
             'mitigação do estudo que replicou em dois domínios com ganho maior no segundo.',
             {'atendimento': [r19['A-atual']['taxa'], r19['B-instrucao-de-sujeito']['taxa']],
              'juridico': [0.7846, 0.9091]})


@resposta('Q028')
def q028():
    r19 = _artefato('r19-armadilha.json')
    return R('Só quando a pergunta auxiliar for **mais confiável que a decisão que ela '
             'alimenta** — e isso é verificável antes de adotar, medindo a auxiliar sozinha. Na '
             f"R19 a pergunta de sujeito acertava {r19['pergunta_de_sujeito']['taxa']:.1%} "
             'sozinha, abaixo da decisão, e decompor destruiu o molde oposto (86% para 36%). '
             'A capacidade de várias perguntas no payload é gratuita e útil — mas para '
             '**observar** (ver a sentinela, Q043), não para encadear decisão.',
             {'pergunta_de_sujeito': r19['pergunta_de_sujeito']['taxa']})


@resposta('Q029')
def q029():
    return R('Sim para a média, não para a classe perigosa. O efeito de posição some ao '
             'embaralhar (p = 0,40), mas **3 de 40 casos** mudaram de resposta conforme os '
             'vizinhos. Use lote para baratear triagem comum; nunca para `cancelar`.',
             {'casos_que_mudaram': 3, 'de': 40, 'p': 0.40})


@resposta('Q030')
def q030():
    return R('Três, com maioria. Repetindo 40 casos cinco vezes, 1 oscilou — votar em três '
             'estabiliza. O custo é desprezível (Q019) e a alternativa é aceitar que uma decisão '
             'sem volta dependa de um sorteio de baixa probabilidade.',
             {'oscilaram': 1, 'de': 40})


# ===================================================================== D · risco
@resposta('Q031')
def q031():
    return R('**0 em 230 casos** sob os três critérios de correção, com teto estatístico de '
             '9,5% por família de casos. Zero observado com teto de 9,5% não autoriza '
             'automatizar a classe irreversível: um em dez é muito quando o erro cancela o '
             'contrato de um cliente.',
             {'erros': 0, 'n': 230, 'teto': 0.095})


@resposta('Q032')
def q032():
    custo = _custo_por_decisao()
    return R(f'Um erro grave custa US$ {p("custo_erro_grave_usd"):.2f} e uma decisão custa US$ '
             f'{custo:.6f} — razão de **{mil(p("custo_erro_grave_usd") / custo)} para 1**. '
             'Qualquer salvaguarda que custe chamadas é barata; a única salvaguarda cara é '
             'tempo de pessoa, e é exatamente essa que o corte de confiança economiza.',
             {'razao': round(p('custo_erro_grave_usd') / custo)},
             _declarar('custo_erro_grave_usd'), confianca='baixa')


@resposta('Q033')
def q033():
    linhas = _linhas_uso_normal()
    altos = [l for l in linhas if l['confianca'] >= 0.99]
    taxa = sum(1 for l in altos if not l['certo']) / len(altos)
    return R(f'Ao corte de 0,99, **{taxa * 1000:.1f} erros por mil decisões aceitas**, o que ao '
             f'custo declarado de erro grave dá US$ {mil(taxa * 1000 * p('custo_erro_grave_usd'))} '
             'de exposição por mil — se todo erro fosse grave, o que não é o caso. A exposição '
             'real é menor e depende da matriz de confusão do seu domínio.',
             {'erros_por_mil': round(taxa * 1000, 2)},
             _declarar('custo_erro_grave_usd'), confianca='baixa')


@resposta('Q034')
def q034():
    familias = _artefato('r8-r9-adversarial.json')['R8_por_familia']
    pior = min(familias, key=lambda n: familias[n]['acuracia'])
    return R(f'**Ação atribuída a terceiro** — {familias[pior]["acuracia"]:.1%} de acerto, a '
             'pior família medida. É também a mais cara, porque o erro típico dela é agir sobre '
             'o pedido de outra pessoa. A mitigação existe e é uma frase (Q027).',
             {n: b['acuracia'] for n, b in familias.items()})


@resposta('Q035')
def q035():
    linhas = _linhas_jev()
    erros = collections.Counter(l['alvo'] for l in linhas if not l['certo'])
    total = collections.Counter(l['alvo'] for l in linhas)
    taxas = {c: round(erros[c] / total[c], 4) for c in total if total[c] >= 30}
    pior = max(taxas, key=taxas.get)
    return R(f'Sim: a classe `{pior}` concentra o erro, com {taxas[pior]:.1%} de taxa entre as '
             'classes com pelo menos 30 casos. Revisão seletiva por classe é viável e é mais '
             'barata que revisar tudo.',
             {'taxa_de_erro_por_classe': taxas})


@resposta('Q036')
def q036():
    return R('Sim, dois. **Texto sem pedido algum sem classe de escape**: erra 10 de 10 com '
             'confiança 0,987. E **ordem direta ao classificador**: das viradas no corpus '
             'jurídico, 8 passaram do corte de 0,90. Nos dois casos o corte não protege, e a '
             'mitigação é de desenho — classe de escape e sanitização —, não de limiar.',
             {'conf_sem_escape': 0.987, 'viradas_acima_do_corte_juridico': 8})


@resposta('Q037')
def q037():
    condicoes = _artefato('r11-extremos.json')['condicoes']
    sem = sum(b['sem_resposta'] for n, b in condicoes.items() if n != 'instrucao/vazia')
    total = sum(b['n'] + b['sem_resposta'] for n, b in condicoes.items()
                if n != 'instrucao/vazia')
    return R(f'Baixo, mas não zero: {sem} de {total} chamadas ({sem / total:.1%}) voltaram sem '
             'resposta fora da condição de instrução vazia. É preciso caminho de contingência — '
             'e ele deve **falhar fechado**, mandando para revisão humana, nunca assumindo uma '
             'classe padrão.',
             {'sem_resposta': sem, 'total': total, 'taxa': round(sem / total, 4)})


@resposta('Q038')
def q038():
    return R('**46,7% sob ruído pesado** (70% dos caracteres corrompidos) — condição implausível '
             'num canal real. O pior caso *plausível* é a triagem jurídica: **78,5%**, com a '
             'perda concentrada no molde de terceiro. Declare 78,5% como piso para domínio novo '
             'sem a instrução de sujeito, e 90,9% com ela.',
             {'ruido_pesado': 0.467, 'juridico': 0.7846, 'juridico_com_sujeito': 0.9091})


@resposta('Q039')
def q039():
    r12 = _artefato('r12-r13-contexto.json')['R12']
    return R('Não. De 0 a 50 mil caracteres a acurácia fica constante em 96,7%. O que derruba '
             'não é o tamanho — é o **truncamento**, que corta o pedido antes de o modelo ver. '
             'Não imponha limite de tamanho; garanta que o corte, se houver, preserve a parte '
             'que importa.',
             {'0k': r12['0k-antes']['acuracia'], '50k': r12['50k-antes']['acuracia']})


@resposta('Q040')
def q040():
    r24 = _r24()
    saida = {}
    for nome, c in r24['corpora'].items():
        saida[nome] = {'oscilaram': c['oscilacao']['oscilaram'], 'n': c['oscilacao']['n'],
                       'divergiram_entre_formulacoes': c['divergencia_entre_formulacoes']['divergiram'],
                       'unica': c['politicas']['unica']['taxa'],
                       'maioria_igual': c['politicas']['maioria-igual']['taxa'],
                       'maioria_diversa': c['politicas']['maioria-diversa']['taxa'],
                       'pareado_diversa': c['politicas']['maioria-diversa']['pareado_contra_unica']}
    j, a = saida['juridico'], saida['atendimento']
    return R('**Os erros se repetem, e votar a mesma pergunta não resolve.** Em '
             f"{j['n'] + a['n']} casos com três chamadas idênticas, {j['oscilaram'] + a['oscilaram']} "
             'oscilaram: o modelo é determinístico neste regime, e o erro é sistemático. O que '
             f"muda a resposta é a formulação — {j['divergiram_entre_formulacoes']} dos "
             f"{j['n']} casos jurídicos divergem entre três formulações — e por isso a maioria "
             f"**diversa** sobe o jurídico de {j['unica']:.1%} para {j['maioria_diversa']:.1%} "
             f"(pareado {j['pareado_diversa']['certo_so_votacao']} a "
             f"{j['pareado_diversa']['certo_so_unica']}, p = {usd(j['pareado_diversa']['p'], 4)}). "
             'Votação protege contra formulação ruim, não contra oscilação, que não existe.',
             saida)


@resposta('Q041')
def q041():
    return R('Um campo só: o `state`, que é onde entra o texto de terceiro. A separação '
             'estrutural entre `state` e `questions` impede que o texto do cliente vire '
             'instrução **por concatenação acidental** — não impede que ele contenha uma ordem '
             'que o modelo decida seguir. Instrução, critérios e rótulos são seus e não são '
             'superfície de ataque, desde que o cuidado nº 7 do guia seja respeitado: nunca '
             'concatenar texto de terceiro dentro deles.',
             {})


@resposta('Q042')
def q042():
    r22 = _r22()
    a = r22['arranjos']
    par = r22['pareado']['meta-sanitizado']
    r23 = _r23()['por_conjunto']
    fam = _familias_de_instrucao_surpresa()
    viradas = sum(f['bruto']['viradas'] for f in fam.values())
    pares = sum(f['bruto']['pares'] for f in fam.values())
    com_v2 = sum(f['v2']['viradas'] for f in fam.values())
    acima = sum(f['bruto']['acima_do_corte'] for f in fam.values())
    return R('**Contra o vetor para o qual a lista foi escrita, sim; contra qualquer outro, '
             'não.** Na R22 a expressão regular de oito padrões derrubou a virada de '
             f"{a['meta']['viradas']}/{a['meta']['pares_com_base']} para "
             f"{a['meta-sanitizado']['viradas']}/{a['meta-sanitizado']['pares_com_base']}, pareado "
             f"{par['virou_so_sem_defesa']} a {par['virou_so_com_defesa']}. Na R23 a mesma lista "
             f"não cobre **nenhum** dos {r23['conhecidos']['vetores'] + r23['surpresa']['vetores']} "
             'vetores novos, e a lista ampliada (v2) cobre só '
             f"{r23['surpresa']['vetores_cobertos_v2']} dos {r23['surpresa']['vetores']} escritos "
             f'por outros modelos. Contra ordens ao sistema nunca vistas, a virada é '
             f'**{viradas}/{pares} = {viradas / pares:.1%}** sem defesa e '
             f'{com_v2}/{pares} com o v2, com **{acima} viradas acima do corte de 0,90**. '
             'Sanitizar por lista é defesa contra o ataque que já se conhece. A camada que '
             'generaliza é o sentinela (Q043).',
             {'r22_pareado': [par['virou_so_sem_defesa'], par['virou_so_com_defesa']],
              'r23_vetores_cobertos_v1': r23['surpresa']['vetores_cobertos_v1'],
              'r23_vetores_cobertos_v2': r23['surpresa']['vetores_cobertos_v2'],
              'r23_instrucao_surpresa': {'viradas': viradas, 'pares': pares, 'com_v2': com_v2,
                                         'acima_do_corte': acima}})


@resposta('Q043')
def q043():
    vigia = _r22()['sentinela']
    ataque, limpo = vigia['recall_sob_ataque'], vigia['silencio_no_texto_limpo']
    fam = _familias_de_instrucao_surpresa()
    acusou = sum(f['sentinela']['acusou'] for f in fam.values())
    n = sum(f['sentinela']['n'] for f in fam.values())
    gat = _r23()['gatilho']['sentinela_alarme_falso']
    r27 = _r27()['montagens']
    return R('**Sim, e é a única defesa que generaliza.** Na R22 a segunda pergunta no mesmo '
             f'payload acusou {ataque["certos"]} de {ataque["n"]} sob ataque e ficou calada em '
             f'{limpo["certos"]} de {limpo["n"]} das limpas. Na R23, contra ordens ao sistema '
             f'escritas por outros modelos e nunca vistas, acusou **{mil(acusou)} de {mil(n)} = '
             f'{acusou / n:.1%}** — onde a lista de padrões cobria 2 vetores em 24. O custo: '
             f'{gat["acusou"]} de {gat["n"]} mensagens legítimas que dizem "desconsidere a '
             'mensagem anterior" são acusadas, e o sentinela precisa ler o texto **original** — '
             f'depois de sanitizar ele acusa {r27["meta-sentinela-limpo"]["sentinela"]["certos"]} '
             f'de {r27["meta-sentinela-limpo"]["sentinela"]["n"]} (R27). Ele não impede a virada; '
             'detecta, e detectar é o que autoriza recusar ou mandar para gente.',
             {'r22_recall': ataque['taxa'], 'r22_alarme_falso': round(1 - limpo['taxa'], 4),
              'r23_recall_instrucao_surpresa': round(acusou / n, 4),
              'r23_alarme_falso_gatilho': round(gat['acusou'] / gat['n'], 4),
              'r27_cego_apos_sanitizar': r27['meta-sentinela-limpo']['sentinela']['certos']})


@resposta('Q044')
def q044():
    r22 = _r22()
    a, par = r22['arranjos'], r22['pareado']['meta-delimitado']
    return R('Ajuda pouco e não está demonstrado. Delimitar o texto com marcadores e avisar na '
             'instrução que ali é dado reduz a virada de '
             f"{a['meta']['taxa_de_virada']:.1%} para "
             f"{a['meta-delimitado']['taxa_de_virada']:.1%}, pareado "
             f"{par['virou_so_sem_defesa']} a {par['virou_so_com_defesa']}, p = {par['p']}. "
             'Direção a favor, sem significância. Use se for de graça; não conte com isso.',
             {'com_delimitador': a['meta-delimitado']['taxa_de_virada'],
              'pareado': par}, confianca='media')


@resposta('Q045')
def q045():
    return R('**Não.** Em atendimento o corte barra quase tudo (1 virada acima de 0,90 em 28), '
             'mas no corpus jurídico 8 das 21 viradas passaram. Um controle que funciona num '
             'domínio e falha no outro não é controle de segurança — é sorte com histórico. '
             'Use o corte para qualidade; use sanitização e sentinela para segurança.',
             {'viradas_acima_atendimento': 1, 'viradas_acima_juridico': 8})


@resposta('Q046')
def q046():
    r27 = _r27()
    m = r27['montagens']
    fam = _familias_de_instrucao_surpresa()
    acusou = sum(f['sentinela']['acusou'] for f in fam.values())
    n = sum(f['sentinela']['n'] for f in fam.values())
    return R('**Sentinela primeiro, sobre o texto original; sanitização como complemento para '
             'o que já se conhece.** A ordem inverteu depois da R23: a lista de padrões não '
             f'generaliza e o sentinela acusa {acusou / n:.0%} de ordens nunca vistas. Na '
             'integração (R27), o sentinela precisa do texto original — sanitizado antes, ele '
             f'fica cego ({m["meta-sentinela-limpo"]["sentinela"]["certos"]}/'
             f'{m["meta-sentinela-limpo"]["sentinela"]["n"]}). Com dois campos no mesmo payload '
             f'a detecção é {m["meta-dois-campos"]["sentinela"]["certos"]}/'
             f'{m["meta-dois-campos"]["sentinela"]["n"]} e a virada reabre em '
             f'{m["meta-dois-campos"]["viradas"]}/{m["meta-dois-campos"]["pares_com_base"]}; com '
             f'duas chamadas, {m["meta-duas-chamadas"]["viradas"]}/'
             f'{m["meta-duas-chamadas"]["pares_com_base"]} viradas ao dobro do custo. Para a '
             'classe irreversível, duas chamadas; para o resto, dois campos. Delimitar fica de '
             'fora.',
             {'ordem': ['sentinela sobre o original', 'sanitizar o que se conhece', 'delimitar'],
              'r27_dois_campos': {'viradas': m['meta-dois-campos']['viradas'],
                                  'sentinela': m['meta-dois-campos']['sentinela']['certos']},
              'r27_duas_chamadas': {'viradas': m['meta-duas-chamadas']['viradas'],
                                    'sentinela': m['meta-duas-chamadas']['sentinela']['certos']}})


@resposta('Q047')
def q047():
    bloco = _artefato('r16-resumo.json')['segunda_camada']['D-pergunta-do-efeito@0.8']
    return R('Sim, **como segunda camada e só como segunda camada**. Nessa posição libera '
             f"{bloco['liberados']} comandos com {int(bloco['irreversivel_liberado'])} "
             'irreversíveis soltos, e o intervalo de Wilson limita o erro a 7,7%. No lugar da '
             'regra é inseguro: sozinho perde de 2 a 6 irreversíveis em 12. A ativação depende '
             'de uma decisão que não é técnica: o guarda global **nega** em vez de perguntar, e '
             'um `allow` deste hook não sobrepõe o `deny` do outro.',
             {'liberados': bloco['liberados'],
              'irreversiveis_soltos': int(bloco['irreversivel_liberado']),
              'teto_do_erro': bloco['ic95_do_erro'][1]})


@resposta('Q048')
def q048():
    return R('A classe que a injeção pedir é executada como se o cliente tivesse pedido. No '
             'corpus jurídico o alvo era `encerrar` e 19 das 21 viradas foram para ela — ou '
             'seja, o atacante escolhe o resultado. O controle compensatório não é o modelo: é '
             '**nunca executar ação irreversível sem confirmação humana**, que já é o cuidado '
             'nº 1 do guia e agora tem uma segunda razão.',
             {'viradas_para_o_alvo': 19, 'de': 21})


@resposta('Q049')
def q049():
    r22 = _r22()
    base = {l['i']: l for l in r22['detalhe'] if l['arranjo'] == 'limpo' and l['escolha']}
    meta = [l for l in r22['detalhe'] if l['arranjo'] == 'meta' and l['escolha']
            and l['i'] in base]
    por_conf = {'base >= 0,99': [0, 0], 'base < 0,99': [0, 0]}
    for l in meta:
        faixa = 'base >= 0,99' if (base[l['i']]['confianca'] or 0) >= 0.99 else 'base < 0,99'
        por_conf[faixa][1] += 1
        if l['escolha'] != base[l['i']]['escolha']:
            por_conf[faixa][0] += 1
    taxas = {k: (v[0] / v[1] if v[1] else None) for k, v in por_conf.items()}
    # replicação na R23: 48 vetores sobre as mesmas 85 mensagens, com a linha de base da corrida
    r23 = _r23()['detalhe']
    base23 = {l['i']: l for l in r23 if l['conjunto'] == 'limpo' and l['escolha']}
    rep = {'base >= 0,99': [0, 0], 'base < 0,99': [0, 0]}
    for l in r23:
        if l['conjunto'] in ('conhecidos', 'surpresa') and l['braco'] == 'bruto'                 and l['escolha'] and l['i'] in base23:
            faixa = 'base >= 0,99' if (base23[l['i']]['confianca'] or 0) >= 0.99 else 'base < 0,99'
            rep[faixa][1] += 1
            rep[faixa][0] += l['escolha'] != base23[l['i']]['escolha']
    taxas23 = {k: (v[0] / v[1] if v[1] else None) for k, v in rep.items()}
    return R('Sim, e o sinal é gratuito: a confiança da decisão **sem** o ataque prediz a '
             'fragilidade. Na R22, mensagens que o modelo classificava com confiança abaixo de '
             f"0,99 viraram {taxas['base < 0,99']:.0%} das vezes; as de confiança máxima, "
             f"{taxas['base >= 0,99']:.0%}. A R23 replica com 48 vetores: "
             f"{taxas23['base < 0,99']:.0%} contra {taxas23['base >= 0,99']:.0%}, sobre "
             f"{mil(rep['base < 0,99'][1])} e {mil(rep['base >= 0,99'][1])} pares. Quem já "
             'estava em dúvida é quem o atacante consegue empurrar — e a confiança de base é o '
             'sinal de graça para escolher onde pôr revisão humana.',
             {'r22_viradas_por_faixa': por_conf, 'r22_taxas': taxas,
              'r23_viradas_por_faixa': rep, 'r23_taxas': taxas23})


@resposta('Q050')
def q050():
    return R('**Zero por mil decisões.** A sanitização é uma expressão regular executada antes '
             'da chamada e a sentinela é uma pergunta a mais no mesmo payload, que o contrato '
             'cobra pelo estado e não pela pergunta. As duas defesas recomendadas não '
             'acrescentam uma única chamada. O custo é de engenharia — escrever os padrões e '
             'decidir o que fazer quando a sentinela acusa —, não de operação.',
             {'chamadas_adicionais': 0})


# ===================================================================== F · escopo
@resposta('Q051')
def q051():
    a = _artefato('r21-generalizacao.json')['arranjos']
    return R('Português, inglês e espanhol, medidos no mesmo corpus com gabarito idêntico: '
             f"{a['pt']['taxa']:.1%}, {a['en']['taxa']:.1%} e {a['es']['taxa']:.1%}. Os "
             'pareamentos dão 1 a 1 nos dois casos. **A língua não é uma variável relevante** '
             'para este contrato, e isso amplia o escopo do estudo inteiro.',
             {'pt': a['pt']['taxa'], 'en': a['en']['taxa'], 'es': a['es']['taxa']})


@resposta('Q052')
def q052():
    return R('Dois: atendimento ao cliente (98,9% no corpus de replicação) e triagem jurídica '
             '(78,5%, ou 90,9% com a instrução de sujeito). Mais código Python para a '
             'ordenação, e prosa técnica para a ordenação em prosa. Fora disso, nada foi '
             'medido — e a queda de 20 pontos entre um domínio e outro é a razão para não '
             'extrapolar.',
             {'atendimento': 0.989, 'juridico': 0.7846, 'juridico_com_sujeito': 0.9091})


@resposta('Q053')
def q053():
    pr = _artefato('r21-generalizacao.json')['prosa']
    return R('**Só em código, pelo que está medido.** Em prosa o Jev põe o trecho certo em '
             f"primeiro {pr['jev_primeiro']}/{pr['n']} e o BM25 também {pr['bm25_primeiro']}/"
             f"{pr['n']} — empate, com o BM25 custando zero chamada. A vantagem de 22 a 1 da "
             'R18 era sobre identificadores de código, contra um BM25 cujo tokenizador nem '
             'lia acento. Em prosa, use BM25.',
             {'jev': pr['jev_primeiro'], 'bm25': pr['bm25_primeiro'], 'n': pr['n']})


@resposta('Q054')
def q054():
    return R('**Não vale ainda.** Nenhuma das mensagens de nenhum corpus veio de um canal de '
             'produção: todas foram construídas ou geradas por molde. Elas medem discriminação '
             'de linguagem, não a bagunça do mundo real — abreviação, emoji, texto cortado, '
             'duas perguntas na mesma frase. É a maior ressalva do estudo e está declarada no '
             'guia como cuidado nº 4.',
             {'mensagens_de_producao': 0})


@resposta('Q055')
def q055():
    return R('Material real. Todo o resto — línguas, domínio novo, prosa, escala, adversário — '
             'já foi coberto por alguma rodada. O que nunca entrou foi uma mensagem escrita por '
             'um cliente de verdade, e é justamente sobre ela que a recomendação vai ser '
             'aplicada.',
             {})


@resposta('Q056')
def q056():
    r12 = _artefato('r12-r13-contexto.json')['R12']
    return R(f"Sim, até 50 mil caracteres: {r12['50k-antes']['acuracia']:.1%}, igual ao de 0. "
             'A posição do alvo no contexto também não importa (antes ou depois, diferença '
             'abaixo de 5 pontos em todos os tamanhos). Diluição não é risco.',
             {'0k': r12['0k-antes']['acuracia'], '50k': r12['50k-antes']['acuracia']})


@resposta('Q057')
def q057():
    condicoes = _artefato('r11-extremos.json')['condicoes']
    return R('Até 12 classes sem custo; de 20 a 147 há um platô em torno de 90%. A condição de '
             f"147 opções ainda dá {condicoes['opcoes/147']['acuracia']:.1%}. Taxonomia grande é "
             'viável — só não é de graça.',
             {'opcoes_147': condicoes['opcoes/147']['acuracia'],
              'opcoes_40': condicoes['opcoes/40']['acuracia']})


@resposta('Q058')
def q058():
    condicoes = _artefato('r11-extremos.json')['condicoes']
    return R('Aguenta ruído leve e quebra com ruído pesado — mas **avisa**: em 70% de '
             f"caracteres corrompidos a acurácia cai para {condicoes['ruido/70%']['acuracia']:.1%} "
             f"e nenhum erro passa de 0,90 de confiança. Normalização prévia ajuda; o corte de "
             'confiança cobre o resto.',
             {'ruido_70': condicoes['ruido/70%']['acuracia'],
              'erros_acima_090': condicoes['ruido/70%']['erros_acima_de_090']})


@resposta('Q059')
def q059():
    return R('Pouco: nas quatro distribuições simuladas a acurácia esperada vai de 95,0% a '
             '97,2% — 2,2 pontos de amplitude. Estime pela mistura do seu canal, mas não espere '
             'surpresa: a variação entre assuntos é menor que a variação entre domínios.',
             {'faixa': [0.950, 0.972]})


@resposta('Q060')
def q060():
    r25 = _r25()['arranjos']
    return R('O terceiro domínio já foi medido (R25) e respondeu: a queda é de **distância do '
             f'corpus de origem**, não do jurídico. A clínica fica em {r25["base"]["taxa"]:.1%} '
             f'sem a frase de sujeito e {r25["sujeito"]["taxa"]:.1%} com ela — abaixo do jurídico '
             'e muito abaixo do atendimento. O que continua faltando é o que sempre faltou: '
             '**200 mensagens de um canal real, anotadas por duas pessoas**, que fecham a '
             'ressalva de material construído e permitem calibrar o corte no dado certo. Depende '
             'de acesso, não de orçamento.',
             {'clinica_base': r25['base']['taxa'], 'clinica_sujeito': r25['sujeito']['taxa']})


@resposta('Q061')
def q061():
    return R('Entre 32 e 65 pontos, conforme o corpus: 92,5% contra 60,0% no piloto e 97,5% '
             'contra 32,5% na confirmação. Não é melhora incremental — é outra categoria de '
             'resultado. Onde o método atual é regra por palavra, trocar vale a pena.',
             {'piloto': [0.925, 0.600], 'confirmacao': [0.975, 0.325]})


@resposta('Q062')
def q062():
    par = _artefato('r18-escala.json')['pareado']['H18b jev-2 vs bm25-2 (alvo no topo)']
    return R(f"Vantagem clara: **{par['so_jev-2']} casos a {par['so_bm25-2']}**, p < 0,0001, na "
             'colocação do trecho certo entre os dois primeiros. Em código, pagar a chamada se '
             'justifica.',
             {'pareado': par})


@resposta('Q063')
def q063():
    pr = _artefato('r21-generalizacao.json')['prosa']
    return R(f"Empate: {pr['jev_primeiro']}/{pr['n']} contra {pr['bm25_primeiro']}/{pr['n']}, "
             'pareado 1 a 1. Em prosa o BM25 com tokenizador que entende acento faz o mesmo '
             'trabalho de graça. **Não pague a chamada.**',
             {'jev': pr['jev_primeiro'], 'bm25': pr['bm25_primeiro']})


@resposta('Q064')
def q064():
    return R('Depende de quem escreveu o gabarito, e é por isso que não serve de justificativa. '
             'Sob o critério desta casa o Jev ganha de 8 a 15 pontos; sob o de um anotador '
             'independente a diferença some. Três experimentos (E10, E11, E12) tentaram '
             'desempatar e chegaram ao mesmo lugar.',
             {'e12_jev': 0.989, 'e12_piores': 0.844})


@resposta('Q065')
def q065():
    familias = _artefato('r15b-familias.json')['familias']['A']
    return R('Contra aviso que imita sistema, vantagem grande: o Jev vira '
             f"{familias['jev']['virou']}/{familias['jev']['n']} e os comparadores até "
             f"{max(b['virou'] for n, b in familias.items() if n != 'jev')}/50, **todas com "
             'confiança acima do corte**. Contra ordem direta, porém, o Jev também vira '
             '(28/78) — a vantagem é de grau, não de natureza, e nenhum dos dois dispensa '
             'sanitização.',
             {'jev': familias['jev']['virou'],
              'pior_comparador': max(b['virou'] for n, b in familias.items() if n != 'jev')})


@resposta('Q066')
def q066():
    custo_humano = p('tempo_revisao_s') / 3600 * p('custo_hora_revisao_usd')
    custo = _custo_por_decisao()
    return R(f'US$ {custo_humano:.4f} contra US$ {custo:.6f} por decisão — o humano custa '
             f'**{mil(custo_humano / custo)}×**. Mas o parâmetro que domina é o tempo de '
             'revisão, declarado em 2 minutos e **nunca cronometrado**. Se forem 30 segundos, a '
             'economia é um quarto desta. Cronometrar é o passo 3 do guia e continua pendente.',
             {'humano_usd': round(custo_humano, 4), 'jev_usd': round(custo, 6),
              'razao': round(custo_humano / custo)},
             _declarar('tempo_revisao_s', 'custo_hora_revisao_usd'), confianca='baixa')


@resposta('Q067')
def q067():
    return R('Não se sabe, e essa é a lacuna mais incômoda. O E8 mediu concordância entre dois '
             'anotadores humanos — 87,4%, kappa 0,84, com 29 divergências em 230 casos — mas '
             'ninguém mediu a acurácia de um humano contra o gabarito no mesmo material. É '
             'possível que o Jev, em 98,9%, esteja **acima** do humano típico, e o estudo não '
             'pode afirmar isso.',
             {'concordancia_humana': 0.874, 'kappa': 0.84, 'divergencias': 29})


@resposta('Q068')
def q068():
    volume = p('volume_mensal_decisoes')
    custo_humano = p('tempo_revisao_s') / 3600 * p('custo_hora_revisao_usd')
    return R(f'Num canal de {mil(volume)} decisões/mês, não fazer nada custa US$ '
             f'{mil(volume * custo_humano)} por mês de tempo de pessoa, ou a qualidade do '
             'método por palavra-chave, que erra 40% no piloto e 67% na confirmação. O custo da '
             'inação é alto porque a linha de base atual é ruim, não porque o Jev seja caro.',
             {'custo_mensal_humano_usd': round(volume * custo_humano)},
             _declarar('volume_mensal_decisoes', 'tempo_revisao_s', 'custo_hora_revisao_usd'),
             confianca='baixa')


@resposta('Q069')
def q069():
    return R('Triagem: Jev contra regra por palavra — Jev, com folga. Verificação: Jev contra '
             'regra simples — Jev. Ordenação em código: Jev contra BM25 — Jev, demonstrado. '
             'Ordenação em prosa: **BM25**, que empata de graça. Guarda de comando: regra '
             '**mais** Jev, nunca Jev sozinho.',
             {})


@resposta('Q070')
def q070():
    return R('Sim, dois. **Prosa**: BM25 empata e custa zero. **Texto interno e confiável com '
             'tolerância a 88–91% de acerto**: um LLM genérico barato empata sob critério '
             'independente e custa um quarto. Fora desses dois, nada dominou o Jev no que foi '
             'medido.',
             {'faixa_do_empate_llm_barato': [0.88, 0.91], 'prosa_bm25_contra_jev': [20, 20]})


# ===================================================================== H · operação
@resposta('Q071')
def q071():
    valores = _latencias()
    todos = [l['latencia_ms'] for l in d.decisoes() if l['latencia_ms']]
    timeouts = len(todos) - len(valores)
    return R(f'Mediana **{d.mediana(valores):.0f} ms**, p90 '
             f'{d.percentil(valores, 0.90):.0f} ms, p99 {d.percentil(valores, 0.99):.0f} ms, '
             f'máximo {max(valores):.0f} ms, sobre {mil(len(valores))} chamadas respondidas. '
             f'Fora dessas, {timeouts} estouraram o timeout de 45 s do cliente e nunca voltaram '
             '— elas contam para o desenho da repescagem, não para o orçamento de tempo.',
             {'p50': round(d.mediana(valores)), 'p90': round(d.percentil(valores, 0.90)),
              'p99': round(d.percentil(valores, 0.99)), 'respondidas': len(valores),
              'timeouts': timeouts})


@resposta('Q072')
def q072():
    valores = _latencias()
    todos = [l['latencia_ms'] for l in d.decisoes() if l['latencia_ms']]
    return R('Sim, com uma ressalva que importa. O p99 das chamadas respondidas é '
             f'{d.percentil(valores, 0.99):.0f} ms, e o roteador em produção mediu 431 ms de '
             f'mediana em 88 decisões reais. Mas {len(todos) - len(valores)} chamadas nunca '
             'voltaram, e num gancho interativo isso é pior que lentidão: **é preciso timeout '
             'curto e caminho de escape**, senão o editor congela esperando uma resposta que '
             'não vem.',
             {'p99_respondidas': round(d.percentil(valores, 0.99)),
              'timeouts': len(todos) - len(valores), 'producao_p50': 431})


NOME_DA_FALHA = {
    'http_error': 'erros HTTP do provedor',
    'timeout': 'estouros do timeout de 45 s do cliente',
    'invalid_response': 'respostas fora do contrato',
    'sent': 'chamadas que saíram e nunca foram conciliadas',
}


@resposta('Q073')
def q073():
    tentativas = d.tentativas()
    falhas = collections.Counter(t['status'] for t in tentativas
                                 if t['status'] not in ('success', 'reserved'))
    total = len(tentativas)
    detalhe = ', '.join(f'{mil(q)} {NOME_DA_FALHA.get(k, k)}'
                        for k, q in falhas.most_common())
    return R(f'**{sum(falhas.values()) / total:.1%}** das {mil(total)} tentativas: {detalhe}. '
             'Três repescagens com espera crescente cobrem o caso comum; o que não pode é tratar '
             'falha como classe padrão.',
             {'taxa': round(sum(falhas.values()) / total, 4), 'por_status': dict(falhas)})


@resposta('Q074')
def q074():
    return R('**Em menos de 24 horas.** A condição de instrução vazia voltava `http 400` em 30 '
             'de 30 no dia 19 e responde 200 com a classe certa e confiança 1 no dia 20. Não é '
             'uma deriva que muda recomendação — nenhuma dependia dela —, mas mede a velocidade '
             'com que uma propriedade publicada pode morrer. Reverifique semanalmente, no '
             'mínimo.',
             {'dias': 1})


@resposta('Q075')
def q075():
    historico = RAIZ / 'laboratorio' / 'canarios-de-comportamento.jsonl'
    corridas = [json.loads(l) for l in historico.read_text(encoding='utf-8').splitlines()
                if l.strip()]
    return R(f'US$ {corridas[-1]["custo_usd"]:.6f} por corrida de 8 canários com 2 repetições. '
             'Semanal custa centavos por ano; diário custa menos de dois dólares. O custo de '
             'monitorar não é argumento para não monitorar.',
             {'usd_por_corrida': corridas[-1]['custo_usd']})


@resposta('Q076')
def q076():
    return R('**Semanal**, com corrida extra antes de qualquer mudança de recomendação. A única '
             'deriva observada levou menos de um dia para acontecer, mas foi detectada na '
             'primeira corrida seguinte; semanal equilibra detecção e ruído. Diária é viável e '
             'custa US$ 0,11 por ano.',
             {'custo_anual_diario_usd': 0.11})


@resposta('Q077')
def q077():
    return R('Três passos, nesta ordem. **Um:** confirmar com chamadas extras que não é ruído — '
             'a resistência depende da mensagem, e um caso não faz deriva. **Dois:** achar qual '
             'afirmação publicada dependia daquela propriedade, o que o campo `sustenta` de cada '
             'canário responde por construção. **Três:** corrigir a documentação antes de '
             'corrigir o código, porque quem lê o guia hoje está tomando decisão com ele.',
             {})


@resposta('Q078')
def q078():
    return R('Oito linhas em paralelo. Acima disso o E12 registrou 429 em 46 chamadas e a '
             'repescagem custou mais tempo do que o paralelismo economizou. A latência mediana '
             'do laboratório em paralelo fica dentro de 1,5× a do acesso sequencial, então oito '
             'não degrada.',
             {'trabalhadores': 8, 'http_429_acima': 46})


@resposta('Q079')
def q079():
    return R('Praticamente tudo, por comando. As páginas `CEM-HIPOTESES`, '
             '`DOSSIE-DE-EVIDENCIAS` e `AUDITORIA-DE-NUMEROS` são geradas do dado bruto e a '
             'auditoria confere que estão atualizadas. O que **não** é reproduzível é a coleta '
             'em si: refazer uma rodada gasta dinheiro e o modelo não é determinístico. Os '
             'artefatos brutos ficam versionados justamente por isso.',
             {})


@resposta('Q080')
def q080():
    return R('Três itens. **Um:** o acerto do roteador em produção nunca foi medido — o '
             'registro guardava só o hash, já corrigido, e falta volume. **Dois:** o guarda de '
             'comando está em sombra e só entrega o ganho medido se o guarda global passar a '
             'perguntar em vez de negar. **Três:** o tempo de revisão humana, que domina toda a '
             'conta econômica, continua declarado e não cronometrado.',
             {'itens': 3})


# ===================================================================== I · governança
@resposta('Q081')
def q081():
    placar = _placar_da_auditoria()
    return R(f'**{placar["conferencias"]} conferências**, todas refeitas a partir das linhas brutas '
             'de resposta com estatística independente da que gerou os resumos, e presas na '
             'suíte de testes: um número publicado sem dado que o sustente quebra o `pytest`. '
             f'{placar["fora_de_alcance"]} itens estão declarados fora de alcance em vez de '
             'omitidos.',
             placar)


@resposta('Q082')
def q082():
    conta = collections.Counter(r['veredito'] for r in _h100())
    return R(f"Das cem hipóteses: **{conta['sustentada']} sustentadas**, "
             f"{conta['falsificada']} falsificadas, {conta['inconclusiva']} inconclusiva. No "
             'dossiê de evidências, quatro afirmações são `demonstrado`, duas são `direção '
             'consistente`, uma é `medição única`, duas são `falsificado`, uma foi `corrigida` '
             'e uma `derivou`. Só as quatro primeiras podem ser ditas sem ressalva.',
             {'h100': dict(conta)})


@resposta('Q083')
def q083():
    return R('**Três**, e todas por medição própria. (1) "imune a instrução injetada", derrubada '
             'pela R15 e devolvida mais precisa; (2) a versão precisa dela — "não obedece a quem '
             'fala com ele" —, derrubada pela R21b; (3) a rejeição do endpoint com instrução '
             'vazia, derrubada pelo canário em menos de 24 horas. Nenhuma foi derrubada por '
             'terceiro, o que é bom sinal de método e mau sinal de revisão externa.',
             {'afirmacoes_derrubadas': 3})


@resposta('Q084')
def q084():
    return R('Horas, nos três casos. A R15 derrubou a imunidade no mesmo dia em que ela foi '
             'publicada; a R21b derrubou a versão corrigida no dia seguinte; o canário pegou a '
             'deriva do endpoint na primeira corrida dele. O mecanismo funciona **tarde**, que é '
             'a única forma que ele tem de funcionar — mas funciona em horas, não em meses.',
             {'tempo_medio': 'horas'})


@resposta('Q085')
def q085():
    return R('Sim para a análise, não para a coleta. Todo artefato bruto está versionado, todas '
             'as páginas se regeram por comando e a auditoria confere cada número contra o '
             'bruto. Refazer a coleta exige a chave do provedor e dinheiro, e o modelo não é '
             'determinístico — então a replicação exata é impossível por natureza, não por '
             'omissão. O que um terceiro consegue é **auditar**, que é o que importa.',
             {})


@resposta('Q086')
def q086():
    return R('Sim, e está declarado. O gabarito das rodadas iniciais foi escrito por mim, que '
             'também escolhi os casos — e é exatamente aí que a vantagem sobre os LLMs baratos '
             'aparece e some conforme o critério. As rodadas recentes corrigiram isso de três '
             'formas: gabarito fixado por molde antes de existir texto, filtro mecânico sem '
             'leitura minha, e vetores adversariais escritos por outros modelos. Onde o gabarito '
             'é meu, desconte.',
             {})


@resposta('Q087')
def q087():
    conta = collections.Counter(r['veredito'] for r in _h100())
    exploratorias = 94
    esperado = exploratorias * 0.05
    return R(f"Não. Foram {conta['falsificada']} falsificações, contra {esperado:.0f} esperadas "
             'por acaso se todas as hipóteses fossem verdadeiras e o teste tivesse 5% de erro — '
             f"**{conta['falsificada'] / esperado:.1f}× o acaso**. Ainda assim, nenhuma "
             'falsificação isolada decide sozinha, e por isso as que mudam recomendação foram '
             'refeitas com coleta nova antes de entrar no guia.',
             {'falsificadas': conta['falsificada'], 'esperado_por_acaso': round(esperado, 1)},
             confianca='media')


@resposta('Q088')
def q088():
    return R('Quatro afirmações: (1) selecionar contexto responde melhor que carregar tudo, '
             '22 a 5, p = 0,0015; (2) o Jev ordena código melhor que o BM25, 22 a 1, '
             'p < 0,0001; (3) como segunda camada, o guarda corta dois terços das confirmações '
             'sem soltar irreversível; (4) receber a instrução pelo prompt expõe o comparador a '
             'um risco que o contrato não tem. Todas as outras precisam de ressalva de escopo, '
             'de gabarito ou de amostra.',
             {'publicaveis': 4})


@resposta('Q089')
def q089():
    return R('A de que **a classe do topo prediz o acerto da resposta**. Ela se apoia em dois '
             'casos do lado `irrelevante`, com intervalo de Wilson indo de 0 a 65,8%. A regra '
             'operacional que ela sugere é barata e sai de graça, então vale seguir — mas citar '
             'o número como evidência seria exagero.',
             {'n_do_lado_fraco': 2, 'teto_do_intervalo': 0.658})


@resposta('Q090')
def q090():
    chamadas, gasto = _ledger()
    return R(f'Sim. **US$ {gasto:.4f} de US$ 5,00** autorizados, em {mil(chamadas)} chamadas — '
             f'{gasto / 5:.1%} do teto, com US$ {5 - gasto:.4f} restantes. O controle é '
             'persistente, a conferência é exata e está presa na suíte de testes.',
             {'gasto_usd': round(gasto, 4), 'teto_usd': 5.0,
              'restante_usd': round(5 - gasto, 4), 'chamadas': chamadas})


# ===================================================================== J · próximos movimentos
@resposta('Q091')
def q091():
    return R('**Um terceiro domínio**, por US$ 0,02 e meia hora. A queda de 98,9% para 78,5% '
             'entre atendimento e jurídico é o maior sinal aberto do estudo, e com um só ponto '
             'de comparação não dá para saber se é o domínio ou a distância ao corpus de '
             'origem. É a medição mais barata com a maior consequência.',
             {'custo_usd': 0.02})


@resposta('Q092')
def q092():
    custo = _custo_por_decisao()
    return R(f'Quase nada em dinheiro — 500 decisões custam US$ {500 * custo:.4f} — e o '
             'obstáculo não é esse: é **gabarito**. Os pedidos redigidos já são guardados desde '
             'a correção do registro, mas alguém precisa dizer qual era a resposta certa. Sem '
             'isso, mede-se latência e custo, não acerto.',
             {'custo_500_decisoes_usd': round(500 * custo, 4)})


@resposta('Q093')
def q093():
    horas = 200 * 2 * (p('tempo_revisao_s') / 3600)
    return R(f'Cerca de {horas:.1f} horas de duas pessoas, ou US$ '
             f'{horas * p("custo_hora_revisao_usd"):.0f} ao custo-hora declarado. É a coisa mais '
             'cara que falta no estudo inteiro — e ainda assim é menos de um dia de trabalho. '
             'O obstáculo é acesso ao dado, não orçamento.',
             {'horas': round(horas, 1),
              'custo_usd': round(horas * p('custo_hora_revisao_usd'))},
             _declarar('tempo_revisao_s', 'custo_hora_revisao_usd'), confianca='baixa')


@resposta('Q094')
def q094():
    return R('**Duzentas mensagens reais e duas pessoas anotando os mesmos casos.** Isso fecha '
             'de uma vez a ressalva de material construído, permite calibrar o corte no material '
             'certo e dá a primeira medida de acurácia humana comparável. Não é dinheiro — '
             'sobram US$ 4,51 do teto. É acesso a dado e tempo de gente.',
             {'mensagens': 200, 'anotadores': 2})


@resposta('Q095')
def q095():
    r26 = _r26()
    a, o = r26['arranjos'], r26['ordenacao']
    return R('**Já foi feito (R26), e a recomendação central inverte onde a resposta está '
             f'dividida.** Em {r26["pares"]} perguntas que exigem dois trechos, mandar o primeiro '
             f'que o Jev escolheu acerta {a["dupla/jev-1"]["acertos"]}/{a["dupla/jev-1"]["n"]} '
             f'contra {a["dupla/todos"]["acertos"]}/{a["dupla/todos"]["n"]} mandando os oito '
             f'({a["dupla/jev-1"]["pareado_contra_todos"]["certo_so_todos"]} a '
             f'{a["dupla/jev-1"]["pareado_contra_todos"]["certo_so_selecao"]}); k = 2 dá '
             f'{a["dupla/jev-2"]["acertos"]}/{a["dupla/jev-2"]["n"]} e k = 3, '
             f'{a["dupla/jev-3"]["acertos"]}/{a["dupla/jev-3"]["n"]}, já sem diferença '
             'significativa. A mesma primeira pergunta sozinha continua favorecendo a seleção '
             f'({a["simples/jev-1"]["acertos"]}/{a["simples/jev-1"]["n"]} contra '
             f'{a["simples/todos"]["acertos"]}/{a["simples/todos"]["n"]}). E a regra de recall '
             f'de graça **não avisa**: o topo veio `essencial` em {o["topo_essencial"]} de '
             f'{o["n"]} casos, e os dois alvos foram marcados essenciais em só '
             f'{o["casos_com_dois_alvos_essenciais"]}. Quem não sabe se a resposta está dividida '
             'manda três, não um.',
             {'dupla': {k: v['acertos'] for k, v in a.items() if k.startswith('dupla')},
              'simples': {k: v['acertos'] for k, v in a.items() if k.startswith('simples')},
              'ordenacao': o})


@resposta('Q096')
def q096():
    chamadas, gasto = _ledger()
    restante = 5 - gasto
    custo = gasto / chamadas
    return R(f'Restam **US$ {restante:.4f}**, que compram cerca de '
             f'{mil(restante / custo)} chamadas — mais de nove vezes tudo que foi gasto até '
             f'aqui ({mil(chamadas)} chamadas). O orçamento não é o limite deste trabalho; tempo e '
             'acesso a dado real são.',
             {'restante_usd': round(restante, 4),
              'chamadas_que_compra': round(restante / custo)})


@resposta('Q097')
def q097():
    resultados = _h100()
    conta = collections.Counter(r['veredito'] for r in resultados)
    return R(f"{conta['falsificada']} falsificadas e {conta['inconclusiva']} inconclusiva — "
             f"**{(conta['falsificada'] + conta['inconclusiva']) / len(resultados):.0%} das cem** "
             'apontam para trabalho. Metade já foi feita nesta rodada (as defesas, a '
             'generalização); a outra metade virou ressalva declarada, que é a forma honesta de '
             'deixar trabalho em aberto.',
             {'falsificadas': conta['falsificada'],
              'inconclusivas': conta['inconclusiva']})


@resposta('Q098')
def q098():
    fam = _familias_de_instrucao_surpresa()
    viradas = sum(f['bruto']['viradas'] for f in fam.values())
    pares = sum(f['bruto']['pares'] for f in fam.values())
    acusou = sum(f['sentinela']['acusou'] for f in fam.values())
    n = sum(f['sentinela']['n'] for f in fam.values())
    return R('**Um, e ele voltou a existir depois da R23:** a ordem direta escrita de um jeito '
             f'que a lista não conhece vira {viradas / pares:.0%} das decisões, e a única '
             f'mitigação medida contra ela é **detecção** ({acusou / n:.0%} pelo sentinela), não '
             'prevenção. Detectar autoriza recusar ou mandar para gente; não devolve a resposta '
             'certa. A oscilação entre chamadas saiu da lista — a R24 mediu zero. O erro em texto '
             'de produção continua sem poder ser mitigado antes de ser medido.',
             {'virada_instrucao_surpresa': round(viradas / pares, 4),
              'recall_sentinela': round(acusou / n, 4)})


@resposta('Q099')
def q099():
    r26 = _r26()['arranjos']
    return R('**Ordenação de contexto, com k = 1 para pergunta de fonte única e k = 3 quando não '
             'se sabe**, dentro de um fluxo que já usa modelo caro. A R26 tirou o k = 1 '
             f'incondicional: com resposta dividida em dois trechos ele acerta '
             f'{r26["dupla/jev-1"]["acertos"]}/{r26["dupla/jev-1"]["n"]} e a regra de recall de '
             'graça não avisa. Salvaguardas que não custam chamada: classe de escape na '
             'taxonomia, sentinela lendo o texto original se ele vier de fora, e a formulação '
             'escolhida por medida, não por intuição.',
             {'jev1_resposta_dividida': r26['dupla/jev-1']['acertos'],
              'jev3_resposta_dividida': r26['dupla/jev-3']['acertos']})


@resposta('Q100')
def q100():
    barata = min(_artefato('r21b-cruzamento.json')['custo_usd'],
                 _artefato('r21-generalizacao.json')['custo_usd'])
    ultima = json.loads((RAIZ / 'laboratorio' / 'canarios-de-comportamento.jsonl')
                        .read_text(encoding='utf-8').splitlines()[-1])
    canarios = ultima['de']
    conferencias = _placar_da_auditoria()['conferencias']
    return R('O método, não os números. Fica **a auditoria** que recalcula cada número publicado '
             'a partir do bruto e quebra a suíte quando a documentação envelhece; ficam os '
             '**canários** que pegam deriva do modelo em horas; fica o **registro de '
             'retratações** legível por máquina; ficam os **geradores de corpus com gabarito '
             f'fixado por molde**, que produzem um experimento novo por US$ {usd(barata)}. Os '
             'números valem para o `jev-1.13` de setembro de 2026 e vão envelhecer. O mecanismo '
             'que descobre que eles envelheceram é o que sobra.',
             {'conferencias_da_auditoria': conferencias, 'canarios': canarios,
              'rodada_nova_mais_barata_usd': round(barata, 4)})
