"""Prende o registro das cem hipóteses e as provas delas.

O que estes testes protegem é a propriedade que torna a varredura utilizável: que cada hipótese
tenha um critério capaz de reprová-la, que cada prova produza um número, e que ninguém possa
afrouxar um limiar depois de ver o resultado sem que isso apareça.
"""

import pytest

from laboratorio.h100 import avaliar, provas, registro


@pytest.fixture(scope='module')
def resultados():
    return avaliar.rodar()


def test_o_registro_tem_cem_hipoteses_com_identificador_unico():
    assert len(registro.HIPOTESES) == 100
    assert len({h['id'] for h in registro.HIPOTESES}) == 100


def test_toda_hipotese_declara_previsao_fonte_e_criterio():
    for h in registro.HIPOTESES:
        for campo in ('enunciado', 'previsao', 'fonte', 'criterio'):
            assert h[campo] and h[campo].strip(), f'{h["id"]} sem {campo}'
        assert h['natureza'] in registro.NATUREZA, f'{h["id"]} com natureza desconhecida'
        assert h['familia'] in registro.FAMILIAS, f'{h["id"]} com família desconhecida'


def test_toda_hipotese_tem_prova():
    faltam = [h['id'] for h in registro.HIPOTESES if h['id'] not in provas.PROVAS]
    assert not faltam, f'sem prova: {faltam}'


def test_nenhuma_prova_quebra(resultados):
    quebradas = [f'{r["id"]}: {r["detalhe"]}' for r in resultados if r['veredito'] == 'erro']
    assert not quebradas, 'provas com exceção:\n' + '\n'.join(quebradas)


def test_todo_veredito_vem_com_numero_ou_com_motivo(resultados):
    """Um veredito sem medida não deixa ninguém discordar dele, e isso é o oposto do método."""
    for r in resultados:
        if r['veredito'] == 'inconclusiva':
            assert r['detalhe'], f'{r["id"]} inconclusiva sem dizer por quê'
        else:
            assert r['medido'] is not None, f'{r["id"]} decidida sem medida'
            assert r['detalhe'], f'{r["id"]} decidida sem detalhe'


def test_a_varredura_encontra_dos_dois_lados(resultados):
    """Cem hipóteses todas sustentadas seria sinal de critério frouxo, não de modelo bom."""
    vereditos = {r['veredito'] for r in resultados}
    assert 'sustentada' in vereditos and 'falsificada' in vereditos


def test_as_emendas_estao_datadas_e_justificadas():
    for emenda in registro.EMENDAS:
        assert emenda['em'] and emenda['o_que'] and emenda['por_que']
        for identificador in emenda['atinge']:
            assert identificador in registro.POR_ID


def test_nenhuma_hipotese_se_apoia_em_condicao_retratada_sem_avisar(resultados):
    from laboratorio.h100 import dados
    for bloco in dados.retratacoes()['retratadas']:
        for condicao in bloco['condicoes']:
            for r in resultados:
                if condicao in (r['detalhe'] or ''):
                    texto = r['detalhe'].lower()
                    assert 'retratad' in texto or 'truncamento' in texto, (
                        f'{r["id"]} cita `{condicao}` sem dizer que está retratada')
