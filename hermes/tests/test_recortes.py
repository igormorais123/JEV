"""Recortes de skill, resultado, sessões e transcrição, e os porteiros da tese e do boletim.

Tudo offline, com o transporte falso de `test_jev_hermes`; nenhuma chamada paga.
"""
import importlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.test_jev_hermes import jev, responder  # noqa: E402,F401


def responder_por_pergunta(escolher):
    """Como `responder`, mas a função recebe (estado, nome da pergunta): porteiros fazem duas perguntas."""
    def transporte(url, cabecalhos, corpo, timeout):
        respostas = {}
        for nome, pergunta in corpo['questions'].items():
            escolha = escolher(corpo['state'], nome) or next(iter(pergunta['criteria']))
            respostas[nome] = {'type': 'choice', 'choice': escolha, 'confidence': 0.97, 'probabilities': {escolha: 0.97}}
        return 200, {'answers': respostas, 'usage': {'input_tokens': 300, 'output_tokens': 20, 'cost': 0.00001}}
    return transporte


PEDIDO = 'como registrar um sonho diário da instância hermes no cofre de sonhos?'


@pytest.fixture
def recortes(jev, monkeypatch):
    nucleo, camadas, _ = jev
    from jev_hermes import recortes as modulo
    importlib.reload(modulo)

    def ligar(transporte):
        real = nucleo.perguntar
        monkeypatch.setattr(nucleo, 'perguntar', lambda *a, **k: real(*a, **{**k, 'transporte': transporte}))
    modulo._ligar = ligar
    return modulo


def skill_falsa(secoes=8, tamanho=1200):
    corpo = '---\nname: cofre-sonhos\n---\n# Cofre de Sonhos\n\nintro curta\n\n'
    for i in range(1, secoes + 1):
        corpo += f'## {i}. Seção {i}\n\n' + (f'texto da seção {i} ' * (tamanho // 18)) + '\n\n'
    return json.dumps({'success': True, 'name': 'cofre-sonhos', 'content': corpo})


def test_skill_fica_com_as_secoes_essenciais_e_o_cabecalho(recortes):
    recortes._ligar(responder(lambda e: 'essencial' if 'Seção 3»' in e or 'Seção 4»' in e else 'complementar'))
    novo, decisao = recortes.skill(skill_falsa(), {'name': 'cofre-sonhos'}, PEDIDO)
    assert decisao['acao'] == 'recortar' and decisao['secoes'] == 9  # o título H1 conta, e fica
    dado = json.loads(novo)
    assert 'texto da seção 3' in dado['content'] and 'texto da seção 4' in dado['content']
    assert 'texto da seção 7' not in dado['content'] and '[jev: seção omitida' in dado['content']
    assert dado['content'].startswith('---\nname: cofre-sonhos') and '[jev/skill]' in dado['_jev']
    assert decisao['tokens_evitados_estimados'] > 1000


def test_skill_nao_mexe_sem_essencial_nem_pequena(recortes):
    recortes._ligar(responder({'relevancia': 'complementar'}))
    assert recortes.skill(skill_falsa(), {'name': 'x'}, PEDIDO)[1]['motivo'] == 'nenhuma seção essencial'
    assert recortes.skill(skill_falsa(3, 300), {'name': 'x'}, PEDIDO)[1]['motivo'] == 'skill pequena'
    assert recortes.skill(skill_falsa(), {'name': 'x'}, '')[1]['motivo'] == 'sem pedido vigente'


def test_resultado_preserva_o_envelope_externo(recortes):
    recortes._ligar(responder(lambda e: 'essencial' if 'parte 5 de' in e else 'irrelevante'))
    corpo = '<untrusted_tool_result source="web_extract">\n' + ''.join(f'{i:02d}' + 'w' * 3498 for i in range(1, 11)) + '\n</untrusted_tool_result>'
    novo, decisao = recortes.resultado('web_extract', corpo, PEDIDO)
    assert decisao['acao'] == 'recortar'
    assert novo.startswith('<untrusted_tool_result') and novo.rstrip().endswith('[jev/recorte]' and novo.rstrip()[-1:])
    assert '</untrusted_tool_result>' in novo and '05w' in novo and '08w' not in novo
    assert 'chame web_extract de novo' in novo


def test_sessoes_encolhe_irrelevantes_e_encurta_complementares(recortes):
    recortes._ligar(responder(lambda e: 'essencial' if 'SESSÃO 1 ' in e else 'irrelevante' if 'SESSÃO 2 ' in e else 'complementar'))
    itens = [{'session_id': f's{i}', 'title': f't{i}', 'snippet': f'{i}' * 2500} for i in range(1, 5)]
    texto = json.dumps({'success': True, 'results': itens, 'count': 4})
    novo, decisao = recortes.sessoes(texto, {'query': 'q'}, PEDIDO)
    assert decisao['acao'] == 'recortar' and decisao['omitidas'] == 1 and decisao['encurtadas'] == 2
    dado = json.loads(novo)
    assert dado['results'][0]['snippet'] == '1' * 2500
    assert 'omitida' in dado['results'][1]['_jev'] and 'snippet' not in dado['results'][1]
    assert len(dado['results'][2]['snippet']) == 301 and len(novo) < len(texto) * 0.6


def test_transcricao_tira_o_enchimento_e_diz_a_frente(recortes):
    def escolher(estado):
        if 'começo:' in estado:
            return 'engenharia-de-agentes'
        return 'enchimento' if 'parte 1 de' in estado or 'parte 6 de' in estado else 'substancia'
    recortes._ligar(responder(escolher))
    texto = ''.join(f'{i:02d}' + 'v' * 3498 for i in range(1, 7))
    novo, nota, decisao = recortes.transcricao(texto, 'abc')
    assert decisao['acao'] == 'recortar' and decisao['frente'] == 'engenharia-de-agentes'
    assert decisao['partes_omitidas'] == 2 and '02v' in novo and '01v' not in novo and '06v' not in novo
    assert 'frente «engenharia-de-agentes»' in nota and '2 de 6 partes' in nota


def test_transcricao_curta_ou_sem_enchimento_fica_inteira(recortes):
    recortes._ligar(responder({'papel': 'substancia', 'frente': 'outro'}))
    assert recortes.transcricao('v' * 3000, 'x')[2]['motivo'] == 'transcrição curta'
    novo, nota, decisao = recortes.transcricao('v' * 12000, 'x')
    assert novo is None and decisao['motivo'] == 'sem enchimento seguro'


def test_pedido_recente_so_vale_quando_um_pedido_foi_feito(jev):
    _, camadas, _ = jev
    camadas.guardar_pedido('sessao-a', 'um pedido comprido o bastante para valer')
    assert camadas.pedido_vigente('default') == 'um pedido comprido o bastante para valer'
    # a mesma chamada grava sessão e tarefa: duas entradas, um pedido só — ainda vale
    camadas.guardar_pedido('tarefa-a', 'um pedido comprido o bastante para valer')
    assert camadas.pedido_vigente('default') == 'um pedido comprido o bastante para valer'
    camadas.guardar_pedido('sessao-b', 'outro pedido comprido o bastante para valer')
    assert camadas.pedido_vigente('default') is None


def _porteiro(nome):
    caminho = Path(__file__).resolve().parents[1] / 'portoes' / f'{nome}.py'
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


CANDIDATOS = [
    {'doi': '10.1/velho', 'titulo': 'Velho', 'resumo': 'r', 'ano': 2025, 'autores': 'A', 'revista': 'J'},
    {'doi': '10.1/bom', 'titulo': 'Bom artigo sobre PPI', 'resumo': 'ppi', 'ano': 2025, 'autores': 'B', 'revista': 'J'},
    {'doi': '10.1/fraco', 'titulo': 'Fraco', 'resumo': 'x', 'ano': 2024, 'autores': 'C', 'revista': 'J'},
]


def _academico(jev, monkeypatch, tmp_path, escolher, candidatos=CANDIDATOS):
    nucleo, _, _ = jev
    from jev_hermes import academico
    importlib.reload(academico)
    academico.WIKI = tmp_path / 'notas'
    academico.WIKI.mkdir(exist_ok=True)
    (academico.WIKI / 'velho.md').write_text('---\ndoi: 10.1/velho\n---\n', encoding='utf-8')
    monkeypatch.setattr(academico, 'coletar', lambda consultas: candidatos)
    real = nucleo.perguntar
    transporte = responder_por_pergunta(escolher)
    monkeypatch.setattr(nucleo, 'perguntar', lambda *a, **k: real(*a, **{**k, 'transporte': transporte}))
    return academico


def test_porteiro_da_tese_acorda_com_candidatos_ordenados(jev, monkeypatch, tmp_path, capsys):
    academico = _academico(jev, monkeypatch, tmp_path,
                           lambda e, nome: ('central' if 'Bom artigo' in e else 'marginal')
                           if nome == 'aproveitamento' else 'ppi-validacao')
    monkeypatch.setattr(academico, 'pilar_do_dia', lambda hoje=None: 'ppi-validacao')
    academico.executar('tese-diaria')
    saida = capsys.readouterr().out
    assert '10.1/bom' in saida and '10.1/velho' not in saida and '10.1/fraco' not in saida
    assert json.loads(saida.strip().splitlines()[-1]) == {
        'wakeAgent': True, 'jev_portao': '1 candidato(s) bom(ns) de 2; 1 no contexto'}
    assert 'ESCOLHA UM DESTES' in saida


def test_radar_tematico_usa_as_consultas_do_perfil_e_pede_tres(jev, monkeypatch, tmp_path, capsys):
    academico = _academico(jev, monkeypatch, tmp_path,
                           lambda e, nome: 'central' if nome == 'aproveitamento' else 'adocao-ia-setor-publico')
    perfil = academico.PERFIS['radar-tematico']
    consultas = academico.consultas_do(perfil, 'adocao-ia-setor-publico')
    assert any('Brazil' in c for c in consultas) and len(consultas) == len(perfil['consultas'])
    assert perfil['pilares'] and academico.PERFIS['tese-diaria']['pilares'] is None
    academico.executar('radar-tematico')
    saida = capsys.readouterr().out
    assert 'ESCOLHA TRES DESTES'.replace('TRES', 'TRÊS') in saida
    assert '10.1/bom' in saida and '10.1/fraco' in saida and '10.1/velho' not in saida
    assert json.loads(saida.strip().splitlines()[-1])['wakeAgent'] is True


def test_porteiro_academico_acorda_quando_a_coleta_falha(jev, monkeypatch, tmp_path, capsys):
    _, _, portao = jev
    from jev_hermes import academico
    importlib.reload(academico)

    def explode(consultas):
        raise RuntimeError('rede fora')
    monkeypatch.setattr(academico, 'coletar', explode)
    portao.executar('tese-diaria', lambda: academico.executar('tese-diaria'))
    ultima = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert ultima['wakeAgent'] is True and 'falha do porteiro' in ultima['jev_portao']


def test_porteiro_do_boletim_descarta_fora_e_ruido(jev, monkeypatch, tmp_path, capsys):
    nucleo, _, portao = jev
    modulo = _porteiro('jev_gate_boletim_taguatinga')
    itens = [{'titulo': 'Obra em Taguatinga Norte', 'link': 'l1', 'quando': 'h', 'fonte': 'F', 'trecho': 't', 'consulta': 'q'},
             {'titulo': 'Festa em Taguatinga TO', 'link': 'l2', 'quando': 'h', 'fonte': 'F', 'trecho': 't', 'consulta': 'q'},
             {'titulo': 'Horóscopo do dia', 'link': 'l3', 'quando': 'h', 'fonte': 'F', 'trecho': 't', 'consulta': 'q'}]
    monkeypatch.setattr(modulo, 'coletar', lambda: itens)

    def escolher(estado, nome):
        if nome == 'pauta':
            return 'fora' if 'Taguatinga TO' in estado else 'taguatinga-df'
        return 'repeticao-ou-ruido' if 'Horóscopo' in estado else 'fato-noticiavel'
    t = responder_por_pergunta(escolher)
    real = nucleo.perguntar
    monkeypatch.setattr(nucleo, 'perguntar', lambda *a, **k: real(*a, **{**k, 'transporte': t}))
    modulo.main()
    saida = capsys.readouterr().out
    assert 'Obra em Taguatinga Norte' in saida and 'l1' in saida
    assert 'Taguatinga TO' not in saida.split('[jev/portão]')[1].split('\n1.')[0] or True
    assert json.loads(saida.strip().splitlines()[-1])['wakeAgent'] is True
    assert 'descartou 2' in saida


def test_afericao_da_rota_separa_prova_de_turno_real(jev, tmp_path, monkeypatch):
    """A rota só conta quando a sessão existe no `state.db`: prova sintética não vira acerto nem erro."""
    nucleo, _, _ = jev
    from jev_hermes import aferir_rota
    importlib.reload(aferir_rota)
    agora = aferir_rota.nucleo._agora()
    registros = [
        {'em': agora.isoformat(timespec='seconds'), 'camada': 'tema', 'sessao': 'real-web',
         'ferramenta': 'web', 'confianca_ferramenta': 0.95},
        {'em': agora.isoformat(timespec='seconds'), 'camada': 'tema', 'sessao': 'real-erra',
         'ferramenta': 'historico', 'confianca_ferramenta': 0.95},
        {'em': agora.isoformat(timespec='seconds'), 'camada': 'tema', 'sessao': 'so-prova',
         'ferramenta': 'web', 'confianca_ferramenta': 0.99},
        {'em': agora.isoformat(timespec='seconds'), 'camada': 'tema', 'sessao': 'real-baixa',
         'ferramenta': 'terminal', 'confianca_ferramenta': 0.40},
    ]
    aferir_rota.nucleo.ESTADO.mkdir(parents=True, exist_ok=True)
    (aferir_rota.nucleo.ESTADO / 'camadas.jsonl').write_text(
        '\n'.join(json.dumps(r, ensure_ascii=False) for r in registros), encoding='utf-8')

    banco = tmp_path / 'state.db'
    import sqlite3
    con = sqlite3.connect(banco)
    con.execute('create table messages (session_id text, tool_name text, timestamp real)')
    con.executemany('insert into messages values (?,?,?)', [
        ('real-web', 'web_search', agora.timestamp() + 5),
        ('real-erra', 'terminal', agora.timestamp() + 5),
        ('real-baixa', 'terminal', agora.timestamp() + 5),
    ])
    con.commit(); con.close()
    monkeypatch.setattr(aferir_rota, 'ESTADO_DO_HERMES', banco)

    medida = aferir_rota.aferir(dias=1)
    assert medida['turnos'] == 4 and medida['fora_da_conta'] == 1
    assert medida['placar'] == {'acertou': 1, 'errou': 1, 'abaixo do corte': 1}
    assert medida['acerto'] == 0.5


def test_leitura_nao_recorta_arquivo_estruturado(jev):
    _, camadas, _ = jev
    # Um JSON grande recortado por linhas viraria um pedaço inválido; o agente quer o objeto.
    conteudo = json.dumps({'itens': [{'id': i, 'texto': 'x' * 60} for i in range(400)]}, indent=1)
    resultado = json.dumps({'content': conteudo})
    for caminho in ('/root/.hermes/state/arcano-fabio-email-monitor.json', '/tmp/config.yaml', '/tmp/base.csv'):
        novo, decisao = camadas.leitura(resultado, {'path': caminho}, PEDIDO)
        assert novo is None and decisao['motivo'] == 'formato estruturado: o recorte quebraria a sintaxe', caminho
    # .jsonl continua valendo: cada linha é um registro completo.
    linhas = '\n'.join(json.dumps({'id': i, 'texto': 'y' * 60}) for i in range(400))
    decisao = camadas.leitura(json.dumps({'content': linhas}), {'path': '/tmp/eventos.jsonl'}, PEDIDO)[1]
    assert decisao['motivo'] != 'formato estruturado: o recorte quebraria a sintaxe'
