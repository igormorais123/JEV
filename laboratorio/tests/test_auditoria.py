"""Prende a auditoria na suíte: nenhum número publicado pode divergir do dado bruto.

Sem este teste, a auditoria é um programa que alguém precisa lembrar de rodar. Com ele,
editar um número no guia sem o dado que o sustente quebra a suíte na hora.
"""

import pytest

from laboratorio import auditoria


@pytest.fixture(scope='module')
def placar():
    return auditoria.rodar()


def test_todo_numero_publicado_fecha_com_o_dado_bruto(placar):
    falhas = ['{bloco} / {item}: publicado {publicado!r}, recalculado {recalculado!r}'.format(**f)
              for f in placar.falhas]
    assert not falhas, 'divergências:\n' + '\n'.join(falhas)


def test_a_auditoria_confere_algo_de_cada_rodada(placar):
    """Um auditor que deixa de enxergar uma rodada passa em silêncio; isto o impede."""
    blocos = set(linha['bloco'] for linha in placar.linhas)
    esperados = {'R1-R3', 'R8', 'R9', 'R10', 'R11', 'R15', 'R15b', 'R16', 'R17', 'R18',
                 'R19', 'R20', 'consolidado', 'documentação', 'caixa'}
    assert esperados <= blocos, f'rodadas sem nenhuma conferência: {esperados - blocos}'


def test_a_estatistica_independente_reproduz_a_do_laboratorio():
    """O Wilson e o McNemar do `nucleo` têm de dar o mesmo que scipy e statsmodels.

    É o que autoriza a auditoria a comparar contra os resumos: se as duas implementações
    discordassem, não haveria como saber qual das duas está publicada.
    """
    from laboratorio import nucleo
    for acertos, total in [(0, 12), (1, 20), (22, 27), (89, 95), (158, 169), (12, 12)]:
        assert list(nucleo.wilson(acertos, total)) == auditoria.wilson(acertos, total)
    for so_a, so_b in [(22, 5), (8, 2), (3, 4), (22, 1), (0, 0), (46, 1)]:
        assert nucleo.mcnemar_exato(so_a, so_b) == auditoria.mcnemar(so_a, so_b)


def test_o_teto_de_gasto_autorizado_nao_foi_ultrapassado(placar):
    teto = [linha for linha in placar.linhas if linha['item'] == 'dentro do teto de US$ 5,00']
    assert teto and all(linha['ok'] for linha in teto)
