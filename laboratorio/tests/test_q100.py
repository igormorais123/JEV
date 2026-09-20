"""Prende o registro das cem perguntas estratégicas e as respostas delas.

O que estes testes protegem é a propriedade que torna a página utilizável para decidir: que
toda pergunta informe uma decisão nomeada, que toda resposta calcule o número na hora, e que
nenhuma conta use um parâmetro que não foi medido sem dizer que usou.
"""

import re

import pytest

from laboratorio.q100 import registro, respostas


@pytest.fixture(scope='module')
def respondidas():
    return {q['id']: {**q, **respostas.RESPOSTAS[q['id']]()} for q in registro.PERGUNTAS}


def test_o_registro_tem_cem_perguntas_com_identificador_unico():
    assert len(registro.PERGUNTAS) == 100
    assert len({q['id'] for q in registro.PERGUNTAS}) == 100


def test_toda_pergunta_declara_decisao_fonte_e_gatilho_de_virada():
    for q in registro.PERGUNTAS:
        for campo in ('pergunta', 'decisao', 'vira_se'):
            assert q[campo] and q[campo].strip(), f'{q["id"]} sem {campo}'
        assert q['fonte'] in registro.FONTES, f'{q["id"]} com fonte desconhecida'
        assert q['familia'] in registro.FAMILIAS, f'{q["id"]} com família desconhecida'


def test_toda_pergunta_tem_resposta():
    faltam = [q['id'] for q in registro.PERGUNTAS if q['id'] not in respostas.RESPOSTAS]
    assert not faltam, f'sem resposta: {faltam}'


def test_nenhuma_resposta_quebra(respondidas):
    assert len(respondidas) == 100


def test_nenhuma_resposta_usa_parametro_que_nao_declarou():
    """Conta com parâmetro escondido é opinião com aparência de número.

    Não basta conferir o que a resposta declarou: é preciso conferir o que ela **usou**. O teste
    troca `p` por um espião, roda as cem e exige que o usado caiba no declarado. Uma conta pode
    não declarar nada, se só combinar valores medidos; nenhuma pode usar um parâmetro calada.
    """
    original = respostas.p
    usados = []

    def espiao(nome):
        usados.append(nome)
        return original(nome)

    try:
        respostas.p = espiao
        for identificador, funcao in sorted(respostas.RESPOSTAS.items()):
            usados.clear()
            declarados = set(funcao()['parametros'])
            escondidos = set(usados) - declarados
            assert not escondidos, f'{identificador} usa {sorted(escondidos)} sem declarar'
    finally:
        respostas.p = original


def test_alguma_conta_declara_parametro(respondidas):
    """Se nenhuma declarasse, o espião do teste acima estaria vigiando o nada."""
    com_parametro = [i['id'] for i in respondidas.values() if i['parametros']]
    assert len(com_parametro) >= 5, com_parametro


def test_todo_parametro_declarado_existe_e_diz_o_que_e(respondidas):
    for item in respondidas.values():
        for nome, bloco in item['parametros'].items():
            assert nome in respostas.PARAMETROS, f'{item["id"]} declara `{nome}`, que não existe'
            assert bloco['o_que_e'], f'{item["id"]} declara `{nome}` sem dizer o que é'


def test_resposta_que_depende_de_parametro_nao_se_diz_de_alta_confianca(respondidas):
    for item in respondidas.values():
        if item['parametros']:
            assert item['confianca'] in ('media', 'baixa'), (
                f'{item["id"]} depende de parâmetro não medido e se declara confiança alta')


def test_nenhuma_resposta_usa_decimal_a_inglesa(respondidas):
    """O separador decimal do Python é ponto, e este documento é escrito em português."""
    decimal_ingles = re.compile(r'\d\.\d{1,2}(?!\d)')
    for item in respondidas.values():
        texto = item['resposta']
        assert respostas.MILHAR not in texto, f'{item["id"]} vazou a marca de milhar'
        for achado in decimal_ingles.finditer(texto):
            trecho = texto[max(0, achado.start() - 12):achado.end()]
            assert 'jev-1.13' in trecho, f'{item["id"]} com decimal à inglesa: {trecho!r}'


def test_nenhuma_resposta_despeja_estrutura_de_dado_na_prosa(respondidas):
    """Um `dict` impresso no meio da frase é rascunho, não resposta."""
    for item in respondidas.values():
        assert '{' not in item['resposta'] and '[' not in item['resposta'], (
            f'{item["id"]} tem estrutura crua na prosa')


def test_resposta_que_afirma_medida_carrega_a_medida_conferivel(respondidas):
    """Sem os números em `numeros`, a auditoria não tem como reconferir a frase.

    Nem toda resposta estratégica tem número — "o que falta é material real" é uma resposta
    inteira e correta. O que não pode existir é resposta que **cita** percentual, valor em
    dólar ou p-valor na prosa e não deixa esse número conferível ao lado.
    """
    afirma_medida = re.compile(r'\d+(?:,\d+)?%|US\$ \d|p < |p = ')
    faltam = [i['id'] for i in respondidas.values()
              if afirma_medida.search(i['resposta']) and not i['numeros']]
    assert not faltam, f'afirmam medida sem carregá-la: {faltam}'


def test_toda_resposta_termina_em_decisao_e_nao_em_curiosidade(respondidas):
    """A pergunta declara a decisão que informa; a resposta tem de ter tamanho para informá-la."""
    curtas = [i['id'] for i in respondidas.values() if len(i['resposta']) < 80]
    assert not curtas, f'resposta curta demais para decidir: {curtas}'


def test_as_familias_todas_tem_pergunta():
    usadas = {q['familia'] for q in registro.PERGUNTAS}
    assert usadas == set(registro.FAMILIAS)


def test_a_pagina_se_gera_e_cita_todas_as_perguntas():
    from laboratorio.q100 import relatorio
    texto = relatorio.montar()
    for q in registro.PERGUNTAS:
        assert f'{q["id"]} — ' in texto, f'{q["id"]} não saiu na página'


def test_nenhuma_resposta_se_apoia_em_condicao_retratada():
    """Foi assim que a Q023 publicou 13,5% de erro que era truncamento do laboratório."""
    from laboratorio.h100 import dados
    linhas = respostas._linhas_jev()
    for bloco in dados.retratacoes()['retratadas']:
        for condicao in bloco['condicoes']:
            assert not any(l['condicao'] == condicao for l in linhas), (
                f'`{condicao}` está retratada e ainda entra nas respostas')
