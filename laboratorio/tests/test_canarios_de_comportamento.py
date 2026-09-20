"""Testa o desenho dos canários sem gastar um centavo.

Um canário que passa com qualquer resposta não é canário, é enfeite. Estes testes prendem as
propriedades que fazem a suíte valer alguma coisa: que os vereditos discriminam, que o payload
é válido, e que o teto de gasto está declarado e é conferido.
"""

import pytest

from laboratorio import canarios_de_comportamento as canarios


@pytest.fixture(scope='module')
def lista():
    return canarios.canarios()


def test_todo_canario_declara_o_que_sustenta(lista):
    for canario in lista:
        assert canario['sustenta'], f"{canario['nome']} não diz que afirmação protege"


def test_o_payload_de_cada_canario_e_valido(lista):
    for canario in lista:
        assert canario['estado'], f"{canario['nome']} não tem estado"
        for chave, pergunta in canario['perguntas'].items():
            assert pergunta['type'] == 'choice'
            assert len(pergunta['criteria']) >= 2, (
                f"{canario['nome']}/{chave}: uma escolha só não é escolha")
            assert all(pergunta['criteria'].values()), (
                f"{canario['nome']}/{chave}: critério sem descrição")


def test_o_veredito_reprova_a_resposta_errada(lista):
    """Respondendo sempre o primeiro critério, quase todo canário tem de reprovar.

    O `classificacao-trivial` é a exceção legítima: a classe certa dele **é** a primeira, e
    inverter a ordem só para fazer o teste passar seria trapaça.
    """
    reprovados = 0
    for canario in lista:
        falsa = {chave: {'choice': next(iter(pergunta['criteria'])), 'confidence': 0.99}
                 for chave, pergunta in canario['perguntas'].items()}
        ok, _ = canario['veredito'](falsa, {})
        reprovados += 0 if ok else 1
    assert reprovados >= len(lista) - 1, 'vereditos frouxos demais para detectar deriva'


def test_o_veredito_reprova_a_ausencia_de_resposta(lista):
    """Sem resposta é alerta — menos no canário cuja propriedade é justamente não responder."""
    for canario in lista:
        ok, _ = canario['veredito'](None, {})
        if canario['nome'] == 'instrucao-vazia-nao-responde':
            continue
        assert not ok, f"{canario['nome']} passa mesmo sem resposta nenhuma"


def test_o_teto_de_gasto_da_corrida_esta_declarado():
    assert 0 < canarios.CUSTO_MAXIMO_PREVISTO <= 0.05


def test_a_suite_cabe_no_teto_declarado(lista):
    """Estado curto é o que mantém o custo previsível; um canário gigante entraria sem aviso."""
    caracteres = sum(len(c['estado']) for c in lista) * 2
    # US$ 0,042 por milhão de tokens de entrada, e 1 token não passa de 1 caractere
    custo_maximo = caracteres / 1e6 * 0.042
    assert custo_maximo < canarios.CUSTO_MAXIMO_PREVISTO
