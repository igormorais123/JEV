"""Testes offline dos seis fluxos do quadro: Jev simulado, agentes simulados, nenhuma chamada paga.

    python -m pytest hermes/tests/test_fluxos.py -q
"""
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AQUI))
FUSO = timezone(timedelta(hours=-3))
PY = sys.executable


@pytest.fixture
def jev(tmp_path, monkeypatch):
    monkeypatch.setenv('JEV_HERMES_RAIZ', str(tmp_path))
    monkeypatch.delenv('JEV_DESLIGADO', raising=False)
    monkeypatch.delenv('JEV_WORKFLOWS_OFFLINE', raising=False)
    (tmp_path / 'jev.env').write_text('OPENROUTER_API_KEY=sk-or-v1-' + 'a1b2c3d4' * 8 + '\n'
                                      'JEV_TETO_DIARIO_USD=1\nJEV_TETO_MENSAL_USD=5\n', encoding='utf-8')
    from jev_hermes import nucleo, workflows, ciclo, agenda, modelos, avaliacao, agentes, triagem, bancada
    for modulo in (nucleo, workflows, ciclo, agenda, modelos, avaliacao, agentes, triagem, bancada):
        importlib.reload(modulo)
    monkeypatch.setattr(nucleo, 'transporte_http', lambda *a, **k: pytest.fail('transporte real chamado'))
    return type('M', (), dict(nucleo=nucleo, workflows=workflows, ciclo=ciclo, agenda=agenda, modelos=modelos,
                              avaliacao=avaliacao, agentes=agentes, triagem=triagem, bancada=bancada))


class Jev:
    """Transporte falso: `regras[nome]` é (escolha, confiança) ou função(estado, pergunta) -> isso."""

    def __init__(self, **regras):
        self.regras = regras
        self.chamadas = []

    def __call__(self, url, cabecalhos, corpo, timeout):
        self.chamadas.append(corpo)
        respostas = {}
        for nome, pergunta in corpo['questions'].items():
            regra = self.regras.get(nome)
            if regra is None and nome.startswith('criterio_'):
                regra = self.regras.get('criterio_')
            escolha, confianca = (regra(corpo['state'], pergunta) if callable(regra) else regra) if regra \
                else (next(iter(pergunta['criteria'])), 0.97)
            respostas[nome] = {'type': 'choice', 'choice': escolha, 'confidence': confianca,
                               'probabilities': {escolha: confianca}}
        return 200, {'answers': respostas, 'usage': {'cost': 0.00001}}

    def perguntas(self):
        return [set(c['questions']) for c in self.chamadas]


# =============================================================================== ciclo

def fluxo_simples(m, *, regra=None, marcar_fim=True):
    def a(estado):
        estado['a'] = estado.get('a', 0) + 1
        return {'a': estado['a']}

    def fim(estado):
        return {'fim': True, 'resposta': 'pronto'}
    acoes = [m.ciclo.Acao('A', 'faz A', a, lambda e: e.get('a', 0) < 5),
             m.ciclo.Acao('B', 'faz B', lambda e: {'b': 1}, lambda e: e.get('a', 0) >= 1),
             m.ciclo.Acao('CONCLUIDO', 'fim', fim, lambda e: marcar_fim and e.get('a', 0) >= 2)]
    return m.ciclo.Fluxo('teste', acoes, lambda e: json.dumps(e.get('ultima') or {}), regra)


def test_guarda_com_uma_acao_nao_chama_o_jev(jev):
    t = Jev(acao=('A', 0.99))
    fluxo = fluxo_simples(jev)
    estado = jev.ciclo.novo(fluxo, 'objetivo')
    jev.ciclo.decidir(fluxo, estado, transporte=t)
    assert t.chamadas == []                      # só A é permitida no início
    estado['a'] = 1
    nome, fonte, _, _ = jev.ciclo.decidir(fluxo, estado, transporte=t)
    assert (nome, fonte) == ('A', 'jev') and len(t.chamadas) == 1
    opcoes = t.chamadas[0]['questions']['acao']['criteria']
    assert set(opcoes) == {'A', 'B', jev.ciclo.ESCAPE}   # CONCLUIDO ainda não é oferecido


def test_confianca_baixa_usa_a_regra_e_escape_sem_regra_vai_para_pessoa(jev):
    fluxo = fluxo_simples(jev, regra=lambda e: 'B')
    estado = jev.ciclo.novo(fluxo, 'x', a=1)
    assert jev.ciclo.decidir(fluxo, estado, transporte=Jev(acao=('A', 0.40)))[:2] == ('B', 'regra')
    sem_regra = fluxo_simples(jev)
    assert jev.ciclo.decidir(sem_regra, estado, transporte=Jev(acao=(jev.ciclo.ESCAPE, 0.95)))[0] == jev.ciclo.HUMANO


def test_ciclo_conclui_so_quando_a_guarda_do_fim_libera(jev):
    t = Jev(acao=lambda estado, p: ('CONCLUIDO', 0.95) if 'CONCLUIDO' in p['criteria'] else ('A', 0.95))
    fluxo = fluxo_simples(jev)
    fim = jev.ciclo.rodar(fluxo, jev.ciclo.novo(fluxo, 'x'), transporte=t)
    assert fim['situacao'] == 'concluido' and fim['a'] == 2 and fim['resposta'] == 'pronto'
    assert jev.ciclo.carregar(fim['id'])['situacao'] == 'concluido'      # gravado em disco


def test_repeticao_sem_mudanca_e_limite_de_passos_levam_a_pessoa(jev):
    fluxo = fluxo_simples(jev, marcar_fim=False)
    parado = jev.ciclo.rodar(fluxo, jev.ciclo.novo(fluxo, 'x', a=1), transporte=Jev(acao=('B', 0.99)))
    assert parado['situacao'] == 'humano' and 'repetida' in parado['motivo']
    curto = jev.ciclo.Fluxo('curto', fluxo.acoes, fluxo.descrever, max_passos=2)
    t = Jev(acao=lambda e, p: ('A', 0.99))
    assert jev.ciclo.rodar(curto, jev.ciclo.novo(curto, 'x'), transporte=t)['motivo'].startswith('limite')


def test_erros_seguidos_levam_a_pessoa(jev):
    def quebra(estado):
        raise RuntimeError('ferramenta caiu')
    fluxo = jev.ciclo.Fluxo('erro', [jev.ciclo.Acao('X', 'x', quebra)], lambda e: '')
    fim = jev.ciclo.rodar(fluxo, jev.ciclo.novo(fluxo, 'x'))
    assert fim['situacao'] == 'humano' and 'erros seguidos' in fim['motivo']


# ============================================================================== agenda

AGORA = datetime(2026, 9, 23, 10, 0, tzinfo=FUSO)   # quarta-feira


class AgendaFalsa:
    def __init__(self, ocupados=(), status='confirmed', ocupar_na_reserva=False):
        self.lista = list(ocupados)
        self.status = status
        self.ocupar_na_reserva = ocupar_na_reserva
        self.falhar_depois_de_criar = False
        self.criados = []

    def ocupados(self, inicio, fim):
        return [(a, b) for a, b in self.lista if a < fim and b > inicio]

    def criar(self, titulo, inicio, fim, descricao, ciclo_id):
        self.criados.append((titulo, inicio, fim, ciclo_id))
        if self.falhar_depois_de_criar:
            raise RuntimeError('gws: tempo esgotado')
        return {'id': f'ev{len(self.criados)}'}

    def do_ciclo(self, ciclo_id, inicio, fim):
        for i, c in enumerate(self.criados, 1):
            if c[3] == ciclo_id and c[1] < fim and c[2] > inicio:
                return {'id': f'ev{i}'}
        return None

    def ler(self, evento_id):
        return {'id': evento_id, 'status': self.status, 'htmlLink': 'https://agenda/x'}


PEDIDO_JEV = dict(janela=('proxima-semana', 0.97), periodo=('tarde', 0.95), duracao=('1-hora', 0.9))


def test_janela_das_semanas():
    from jev_hermes import agenda
    inicio, fim = agenda.janela('proxima-semana', AGORA)
    assert (inicio.weekday(), inicio.date().isoformat(), fim.date().isoformat()) == (0, '2026-09-28', '2026-10-03')
    inicio, fim = agenda.janela('esta-semana', AGORA)
    assert (inicio.date().isoformat(), fim.date().isoformat()) == ('2026-09-24', '2026-09-26')
    sexta = datetime(2026, 9, 25, 10, 0, tzinfo=FUSO)
    assert agenda.janela('esta-semana', sexta)[0].date().isoformat() == '2026-09-28'


def test_agendar_pergunta_tarde_com_tres_opcoes_e_so_conclui_depois_de_confirmado(jev):
    ocupado = datetime(2026, 9, 28, 13, 0, tzinfo=FUSO)
    falsa = AgendaFalsa([(ocupado, ocupado + timedelta(hours=2))])
    t = Jev(**PEDIDO_JEV)
    r = jev.agenda.agendar('Agende reunião com o contador semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    assert r['situacao'] == 'aguardando_usuario' and falsa.criados == []
    assert 'segunda 28/09 às 15:00' in r['pergunta'] and 'terça 29/09 às 13:00' in r['pergunta']
    assert r['passos'] == ['1. BUSCAR_HORARIO (guarda)', '2. PRECISA_DO_USUARIO (guarda)']
    fim = jev.agenda.responder(r['id'], '2', agenda=falsa, transporte=t, agora=AGORA)
    assert fim['situacao'] == 'concluido' and 'terça 29/09 às 13:00' in fim['resposta']
    assert len(falsa.criados) == 1 and falsa.criados[0][1].hour == 13
    assert [p.split(' ')[1] for p in fim['passos']][-3:] == ['RESERVAR', 'CONCLUIDO'] or \
        fim['passos'][-2:] == ['4. RESERVAR (guarda)', '5. CONCLUIDO (guarda)']


def test_reserva_nao_confirmada_nao_conclui(jev):
    falsa = AgendaFalsa(status='tentative')
    t = Jev(**PEDIDO_JEV)
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    fim = jev.agenda.responder(r['id'], '1', agenda=falsa, transporte=t, agora=AGORA)
    assert fim['situacao'] == 'humano' and fim['resposta'] is None


def test_conflito_na_hora_de_reservar_volta_a_buscar(jev):
    falsa = AgendaFalsa()
    t = Jev(**PEDIDO_JEV)
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    inicio = datetime(2026, 9, 28, 13, 0, tzinfo=FUSO)
    falsa.lista.append((inicio, inicio + timedelta(hours=1)))       # alguém ocupou o horário 1
    fim = jev.agenda.responder(r['id'], '1', agenda=falsa, transporte=t, agora=AGORA)
    assert fim['situacao'] == 'aguardando_usuario' and falsa.criados == []
    assert 'segunda 28/09 às 14:00' in fim['pergunta']              # nova busca, sem o horário tomado


def test_resposta_livre_e_recusa_passam_pelo_jev(jev):
    falsa = AgendaFalsa()
    t = Jev(**PEDIDO_JEV, escolha=lambda estado, p: ('opcao-1', 0.96) if 'quinta' in estado else ('nenhuma', 0.95))
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    recusa = jev.agenda.responder(r['id'], 'nenhum desses serve', agenda=falsa, transporte=t, agora=AGORA)
    assert recusa['situacao'] == 'aguardando_usuario' and 'segunda' not in recusa['pergunta']
    assert 'quinta 01/10 às 13:00' in recusa['pergunta']
    fim = jev.agenda.responder(r['id'], 'prefiro o de quinta', agenda=falsa, transporte=t, agora=AGORA)
    assert fim['situacao'] == 'concluido' and falsa.criados[0][1].weekday() == 3


def test_resposta_ambigua_pergunta_de_novo(jev):
    falsa = AgendaFalsa()
    t = Jev(**PEDIDO_JEV, escolha=('opcao-1', 0.55))
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    de_novo = jev.agenda.responder(r['id'], 'tanto faz, vê aí', agenda=falsa, transporte=t, agora=AGORA)
    assert de_novo['situacao'] == 'aguardando_usuario' and 'Responda só o número' in de_novo['pergunta']
    assert falsa.criados == []


def test_sem_horario_o_jev_escolhe_entre_ampliar_e_perguntar(jev):
    dia = datetime(2026, 9, 28, 0, 0, tzinfo=FUSO)
    tudo = [(dia + timedelta(days=d, hours=8), dia + timedelta(days=d, hours=18)) for d in range(5)]
    falsa = AgendaFalsa(tudo)
    t = Jev(**PEDIDO_JEV, acao=('AMPLIAR_BUSCA', 0.93))
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    assert '3. AMPLIAR_BUSCA (jev)' in r['passos'] or '2. AMPLIAR_BUSCA (jev)' in r['passos']
    assert r['situacao'] == 'aguardando_usuario' and 'semana' in r['pergunta']


# ============================================================================= modelos

def test_modelo_pelo_tipo_escalada_por_falha_e_orcamento(jev):
    m = jev.modelos
    orc = m.Orcamento(5.0)
    d = m.escolher('Corrigir função de frete', orc, transporte=Jev(tipo=('especialista', 0.95)))
    assert (d['nivel'], d['modelo'], d['fonte'], d['escalada']) == ('especialista', 'opus', 'jev', False)
    d2 = m.escolher('Corrigir função de frete', orc, tentativa=2, nivel_anterior='especialista')
    assert (d2['nivel'], d2['fonte'], d2['escalada']) == ('fronteira', 'falha', True)
    incerto = m.escolher('algo', orc, transporte=Jev(tipo=('pequeno', 0.5)))
    assert (incerto['nivel'], incerto['fonte']) == ('especialista', 'padrao')
    apertado = m.escolher('planejar migração', m.Orcamento(0.70), transporte=Jev(tipo=('fronteira', 0.99)))
    assert apertado['nivel'] == 'especialista' and 'não cabe' in apertado['motivo']
    assert m.escolher('x', m.Orcamento(0.05), transporte=Jev(tipo=('pequeno', 0.99)))['humano'] is True
    assert not any('Haiku' in n['modelo'] or 'haiku' in n['modelo'] for n in m.NIVEIS.values())


def test_resumo_conta_decisoes_e_escaladas(jev):
    m = jev.modelos
    for nivel in ['pequeno'] * 3 + ['fronteira']:
        m.registrar({'nivel': nivel, 'fonte': 'jev', 'escalada': nivel == 'fronteira'}, 0.1)
    assert m.resumo()['frase'] == '4 decisões → 1 escaladas ao nível de fronteira'


def test_executor_manda_o_pedido_pela_entrada_e_gasta_o_orcamento(jev, monkeypatch, tmp_path):
    visto = {}

    class Feito:
        returncode = 0
        stdout = json.dumps({'result': 'mudei x', 'total_cost_usd': 0.42, 'num_turns': 3, 'is_error': False})
    monkeypatch.setattr(jev.modelos.subprocess, 'run', lambda cmd, **k: visto.update(cmd=cmd, **k) or Feito())
    orc = jev.modelos.Orcamento(1.0)
    r = jev.modelos.executar_claude('faça x', tmp_path, jev.modelos.NIVEIS['pequeno'] | {'nivel': 'pequeno'},
                                    ferramentas=['Read', 'Bash(pytest:*)'], orcamento=orc)
    assert visto['input'] == 'faça x' and 'faça x' not in visto['cmd']
    assert visto['cmd'][visto['cmd'].index('--allowedTools') + 1] == 'Read,Bash(pytest:*)'
    assert visto['cmd'][visto['cmd'].index('--max-budget-usd') + 1] == '1.00'
    assert (r['texto'], r['custo_usd'], r['erro'], orc.restante) == ('mudei x', 0.42, False, 0.58)


# =========================================================================== avaliação

def test_contagem_de_pytest_e_unittest():
    from jev_hermes.avaliacao import contar
    assert contar('=== 1 failed, 4 passed in 0.2s ===', 1) == {'executados': 5, 'passaram': 4, 'falharam': 1,
                                                               'codigo_saida': 1}
    assert contar('Ran 3 tests in 0.001s\n\nFAILED (failures=1, errors=1)', 1)['falharam'] == 2
    assert contar('Ran 3 tests in 0.001s\n\nOK', 0)['passaram'] == 3
    assert contar('sem contagem', 0)['executados'] is None


def observacao_teste(m, falharam=0):
    return m.workflows.Observacao(tipo='teste', origem='harness:pytest', referencia='pytest', conteudo='saida',
                                  resultado={'executados': 3, 'passaram': 3 - falharam, 'falharam': falharam,
                                             'codigo_saida': 1 if falharam else 0})


def rodar_laco(m, sequencia, t, **opcoes):
    """sequencia: quantos testes falham em cada tentativa."""
    feitos = []

    def implementar(pedido, retorno, tentativa):
        feitos.append(retorno)
        return {'texto': f'tentativa {tentativa}', 'custo_usd': 0.1}
    estados = iter(sequencia)
    fim = m.avaliacao.laco('Corrigir frete', [{'id': 'frete', 'descricao': 'frete grátis a partir de 200'}],
                           implementar, lambda: [observacao_teste(m, next(estados))], transporte=t, **opcoes)
    return fim, feitos


def test_refazer_devolve_as_faltas_e_depois_aprova(jev):
    fim, feitos = rodar_laco(jev, [1, 0], Jev(criterio_=('atendido', 0.95), relato=('sustentado', 0.95),
                                              sentinela=('nao-tenta', 0.99)))
    assert fim['resultado'] == 'aprovado' and [h['veredito'] for h in fim['historico']] == ['retry', 'passou']
    assert feitos[0] is None and '1 teste(s) falharam' in feitos[1]['faltas'][0]


def test_mesmas_faltas_duas_vezes_vao_para_pessoa(jev):
    fim, _ = rodar_laco(jev, [1, 1, 1], Jev(), max_tentativas=3)
    assert fim['resultado'] == 'humano' and 'não mudou' in fim['motivo'] and fim['tentativas'] == 2


def test_criterio_nao_atendido_com_confianca_alta_refaz(jev):
    t = Jev(criterio_=lambda estado, p: ('nao-atendido', 0.96) if 'tentativa 1' in estado else ('atendido', 0.96),
            relato=('sustentado', 0.95), sentinela=('nao-tenta', 0.99))
    fim, feitos = rodar_laco(jev, [0, 0], t)
    assert fim['resultado'] == 'aprovado' and 'critério frete não atendido' in feitos[1]['faltas'][0]


def test_sensivel_e_sem_evidencia_nao_refazem(jev):
    fim, _ = rodar_laco(jev, [1, 0], Jev(), sensivel=True)
    assert fim['resultado'] == 'humano' and fim['tentativas'] == 1
    vazio = jev.avaliacao.laco('x', [{'id': 'c', 'descricao': 'y'}], lambda *a: {'texto': 'feito'}, lambda: [])
    assert vazio['resultado'] == 'humano' and vazio['tentativas'] == 1


def test_observar_testes_roda_o_comando_de_verdade(jev, tmp_path):
    obs = jev.avaliacao.observar_testes(f'"{PY}" -c "import sys; print(\'2 passed\'); sys.exit(0)"', tmp_path)
    assert obs.resultado == {'executados': 2, 'passaram': 2, 'falharam': 0, 'codigo_saida': 0}
    assert jev.avaliacao.observar_testes('comando-que-nao-existe-xyz', tmp_path).resultado['codigo_saida'] == 127


def test_diff_so_mede_o_agente(jev, tmp_path):
    (tmp_path / 'a.py').write_text('x = 1\n', encoding='utf-8')
    assert jev.avaliacao.preparar_git(tmp_path) is True
    (tmp_path / 'sujo.py').write_text('antes do agente\n', encoding='utf-8')
    (tmp_path / 'a.py').write_text('x = 5\n', encoding='utf-8')          # mudança anterior, não commitada
    base = jev.avaliacao.linha_de_base(tmp_path)
    (tmp_path / 'a.py').write_text('x = 2\n', encoding='utf-8')
    (tmp_path / 'novo.py').write_text('y = 3\n', encoding='utf-8')
    (tmp_path / 'segredo.env').write_text('CHAVE=abc\n', encoding='utf-8')
    obs = jev.avaliacao.observar_diff(tmp_path, base)
    assert '-x = 5' in obs.conteudo and '+x = 2' in obs.conteudo and 'novo.py' in obs.conteudo
    assert 'sujo.py' not in obs.conteudo and 'CHAVE=abc' not in obs.conteudo and 'segredo.env' in obs.conteudo
    import subprocess
    assert subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=tmp_path, capture_output=True,
                          text=True).stdout == ''   # o índice do repositório não foi tocado


# ============================================================================= agentes

@pytest.fixture
def oficina(jev, tmp_path, monkeypatch):
    """Pasta com um 'defeito' em ok.txt e agentes falsos que o programador conserta."""
    pasta = tmp_path / 'repo'
    pasta.mkdir()
    (pasta / 'ok.txt').write_text('0', encoding='utf-8')
    chamadas = []

    def executar_claude(prompt, pasta_, decisao, **k):
        papel = prompt.split('.')[0].split()[-1]
        chamadas.append((papel, decisao['nivel']))
        if papel == 'PROGRAMADOR':
            (Path(pasta_) / 'ok.txt').write_text('1', encoding='utf-8')
        texto = 'VEREDITO: aprovado' if papel == 'REVISOR' else f'{papel} fez'
        return {'texto': texto, 'custo_usd': 0.2, 'erro': False, 'modelo': decisao['modelo'], 'turnos': 1}
    monkeypatch.setattr(jev.modelos, 'executar_claude', executar_claude)
    teste = f'"{PY}" -c "import sys; sys.exit(0 if open(\'ok.txt\').read() == \'1\' else 1)"'
    return pasta, teste, chamadas


JUDGE_OK = dict(criterio_=('atendido', 0.95), relato=('sustentado', 0.95), sentinela=('nao-tenta', 0.99),
                tipo=('especialista', 0.95))


def test_roteador_pula_a_pesquisa_quando_o_estado_ja_diz_o_problema(jev, oficina):
    pasta, teste, chamadas = oficina
    preferencia = ('CONCLUIDO', 'REVISAR', 'TESTAR', 'PROGRAMAR')    # nunca pesquisa: o chamado já diz tudo
    t = Jev(**JUDGE_OK, acao=lambda estado, p: next((k, 0.95) for k in preferencia if k in p['criteria']))
    fim = jev.agentes.resolver(pasta, 'ok.txt deve conter 1', teste, transporte=t)
    assert fim['situacao'] == 'concluido' and fim['judge'] == 'passou'
    assert [p.split(' ')[1] for p in fim['passos']] == ['TESTAR', 'PROGRAMAR', 'TESTAR', 'REVISAR', 'CONCLUIDO']
    assert [c[0] for c in chamadas] == ['PROGRAMADOR', 'REVISOR']


def test_esteira_segue_a_ordem_e_para_quando_falha(jev, oficina, monkeypatch):
    pasta, teste, chamadas = oficina
    fim = jev.agentes.resolver(pasta, 'ok.txt deve conter 1', teste, esteira=True, transporte=Jev(**JUDGE_OK))
    assert [p.split(' ')[1] for p in fim['passos']] == ['PESQUISAR', 'PROGRAMAR', 'TESTAR', 'REVISAR', 'CONCLUIDO']
    (pasta / 'ok.txt').write_text('0', encoding='utf-8')
    monkeypatch.setattr(jev.modelos, 'executar_claude', lambda *a, **k: {'texto': 'nada', 'custo_usd': 0.1,
                                                                        'erro': False, 'modelo': 'opus'})
    falhou = jev.agentes.resolver(pasta, 'ok.txt deve conter 1', teste, esteira=True, transporte=Jev(**JUDGE_OK))
    assert falhou['situacao'] == 'humano' and len(falhou['passos']) == 5


def test_teste_que_falha_volta_para_o_programador_com_nivel_acima(jev, oficina, monkeypatch):
    pasta, teste, chamadas = oficina
    original = jev.modelos.executar_claude
    vezes = {'n': 0}

    def dois_passos(prompt, pasta_, decisao, **k):
        if 'PROGRAMADOR' in prompt.split('.')[0]:
            vezes['n'] += 1
            if vezes['n'] == 1:
                chamadas.append(('PROGRAMADOR', decisao['nivel']))
                return {'texto': 'tentei', 'custo_usd': 0.2, 'erro': False, 'modelo': decisao['modelo']}
        return original(prompt, pasta_, decisao, **k)
    monkeypatch.setattr(jev.modelos, 'executar_claude', dois_passos)
    fim = jev.agentes.resolver(pasta, 'ok.txt deve conter 1', teste, transporte=Jev(**JUDGE_OK, acao=('PROGRAMAR', 0.3)))
    assert fim['situacao'] == 'concluido'
    assert [n for p, n in chamadas if p == 'PROGRAMADOR'] == ['especialista', 'fronteira']


# ============================================================================= triagem

def respostas(rota, confianca, ordem='nao-tenta'):
    return {'fluxo': {'choice': rota, 'confidence': confianca}, 'ordem': {'choice': ordem, 'confidence': 0.99}}


ITEM = {'id': 'm1', 'origem': 'e-mail', 'de': 'Ana Souza <ana@empresa.com>', 'assunto': 'Proposta de pesquisa',
        'trecho': 'Queremos contratar uma pesquisa'}


def test_oportunidade_vira_cartao_com_acompanhamento_e_lembrete_unico(jev):
    criados = []
    d = jev.triagem.despachar(ITEM, respostas('oportunidade-de-venda', 0.95),
                              criar=lambda *a: criados.append(a) or 't_abc', agora=AGORA)
    assert d['acao'] == 'cartao' and criados[0][0] == 'gabinete-igor' and criados[0][3] == 'e-mail:m1'
    assert d['acompanhamento'].startswith('2026-09-25') and 'Oportunidade registrada (t_abc' in d['linha']
    depois = AGORA + timedelta(days=3)
    assert jev.triagem.acompanhamentos_vencidos(depois, situacao=lambda q, c: 'blocked') == \
        ['⏰ Acompanhamento vencido: Oportunidade: Ana Souza — Proposta de pesquisa (t_abc)']
    assert jev.triagem.acompanhamentos_vencidos(depois, situacao=lambda q, c: 'blocked') == []


def test_rotulos_por_destino_duvida_ordem_e_falha(jev):
    criados = []
    criar = lambda *a: criados.append(a) or 't_1'   # noqa: E731
    incidente = jev.triagem.despachar(ITEM, respostas('defeito-critico', 0.93), criar=criar, agora=AGORA)
    pedido = jev.triagem.despachar(ITEM, respostas('pedido-de-funcionalidade', 0.91), criar=criar, agora=AGORA)
    assert [c[0] for c in criados] == ['colmeia-operacional', 'engenharia-inteia']
    assert incidente['linha'].startswith('🚨') and pedido['linha'] is None and pedido['acao'] == 'cartao'
    duvida = jev.triagem.despachar(ITEM, respostas('defeito-critico', 0.70), criar=criar, agora=AGORA)
    assert duvida['acao'] == 'conferir' and 'confira' in duvida['linha'] and len(criados) == 2
    suspeito = jev.triagem.despachar(ITEM, respostas('defeito-critico', 0.99, 'tenta-instruir'), criar=criar)
    assert suspeito['acao'] == 'suspeito' and len(criados) == 2
    assert jev.triagem.despachar(ITEM, respostas('nao-pede-fluxo', 0.99), criar=criar)['acao'] == 'nada'
    assert jev.triagem.despachar(ITEM, None, criar=criar)['acao'] == 'nada'

    def quebra(*a):
        raise RuntimeError('kanban fora')
    falhou = jev.triagem.despachar(ITEM, respostas('defeito-critico', 0.99), criar=quebra)
    assert falhou['acao'] == 'falhou' and 'kanban falhou' in falhou['linha']


def test_triar_manda_as_duas_perguntas_num_pedido_so(jev):
    t = Jev(fluxo=('pedido-de-funcionalidade', 0.95), ordem=('nao-tenta', 0.99))
    saida = jev.triagem.triar([ITEM], criar=lambda *a: 't_9', transporte=t)
    assert t.perguntas() == [{'fluxo', 'ordem'}] and saida[0]['cartao'] == 't_9'


# ============================================================================= bancada

def test_bancada_mede_pelo_verificador_oculto_e_compara(jev, monkeypatch):
    tarefa = {'id': 't', 'tipo': 'defeito', 'pedido': 'x', 'arquivos': {'a.txt': '0'},
              'verificador': {'comando': f'"{PY}" -c "import sys; sys.exit(0 if open(\'a.txt\').read()==\'1\' else 1)"',
                              'arquivos': {'oculto.txt': 'escondido'}}}

    def boa(tarefa_, pasta, orcamento, transporte=None):
        assert not (pasta / 'oculto.txt').exists()          # o verificador só chega depois
        (pasta / 'a.txt').write_text('1', encoding='utf-8')
        return {'humano': False, 'custo_usd': 0.5, 'novas_tentativas': 1}

    def diz_que_fez(tarefa_, pasta, orcamento, transporte=None):
        return {'humano': False, 'custo_usd': 0.2, 'novas_tentativas': 0}
    execucoes = jev.bancada.rodar([tarefa], ['b', 'a'], repeticoes=2,
                                  arquiteturas={'b': boa, 'a': diz_que_fez})
    assert [(e['arquitetura'], e['sucesso']) for e in execucoes] == [('b', True), ('a', False), ('a', False), ('b', True)]
    analise = jev.bancada.comparar(execucoes, amostra_minima=2)
    tabela = {c['id']: c['resultados'] for c in analise['configuracoes']}
    assert tabela['b']['taxa_sucesso'] == {'sucessos': 2, 'total': 2} and tabela['a']['custo_usd']['media'] == 0.2
    assert analise['comparacao']['comparacao']['resultado'] in ('inconclusivo', 'vencedor')
    texto = jev.bancada.relatorio(execucoes, analise)
    assert '| b | 2/2 |' in texto and '| a | 0/2 |' in texto


def test_tarefas_da_bancada_cobrem_os_quatro_tipos(jev):
    tarefas = jev.bancada.carregar_tarefas()
    assert {t['tipo'] for t in tarefas} == {'defeito', 'funcionalidade', 'pesquisa', 'refatoracao'}
    for t in tarefas:
        assert 'verificador_oculto.py' in t['verificador']['arquivos'] and 'verificador_oculto.py' not in t['arquivos']


# ============================================================================== plugin

def test_plugin_valida_operacao_e_lista_abertos(jev):
    import importlib.util
    spec = importlib.util.spec_from_file_location('plugin_fluxos', AQUI / 'plugin' / 'jev-fluxos' / '__init__.py')
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    assert json.loads(plugin.handle({'operacao': 'xyz'}))['status'] == 'invalid_input'
    assert json.loads(plugin.handle({'operacao': 'abertos'})) == {'abertos': []}
    assert json.loads(plugin.handle({'operacao': 'responder', 'id': 'nao-existe', 'resposta': '1'}))['status'] == 'invalid_input'


def test_chamado_que_cita_cliente_pode_ser_aprovado_pelo_harness(jev, oficina):
    """Caso real da bancada de 23/09: a regra por palavra marcava 'clientes' como sensível e nada fechava."""
    pasta, teste, _ = oficina
    t = Jev(**JUDGE_OK, acao=lambda e, p: next((k, 0.95) for k in ('CONCLUIDO', 'REVISAR', 'TESTAR', 'PROGRAMAR')
                                                if k in p['criteria']))
    fim = jev.agentes.resolver(pasta, 'Clientes com compra de R$ 200 pagam frete: ok.txt deve conter 1', teste,
                               transporte=t)
    assert fim['situacao'] == 'concluido'
    sensivel = jev.agentes.resolver(pasta, 'Clientes: ok.txt deve conter 1', teste, sensivel=True, transporte=t)
    assert sensivel['situacao'] == 'humano' and 'avaliação final pede uma pessoa' in sensivel['motivo']
    pela_ferramenta = jev.workflows.executar('judge', {'pedido_original': 'clientes', 'resultado': 'feito',
                                                       'criterios': [{'id': 'c', 'descricao': 'x'}]})
    assert pela_ferramenta['veredito'] == 'revisao_humana'


def test_criacao_que_expira_mas_grava_nao_duplica(jev):
    falsa = AgendaFalsa()
    falsa.falhar_depois_de_criar = True
    t = Jev(**PEDIDO_JEV)
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    fim = jev.agenda.responder(r['id'], '1', agenda=falsa, transporte=t, agora=AGORA)
    assert fim['situacao'] == 'concluido' and len(falsa.criados) == 1


def test_horario_que_ja_passou_nao_e_reservado(jev):
    falsa = AgendaFalsa()
    t = Jev(**PEDIDO_JEV)
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    depois = datetime(2026, 10, 5, 10, 0, tzinfo=FUSO)
    fim = jev.agenda.responder(r['id'], '1', agenda=falsa, transporte=t, agora=depois)
    assert falsa.criados == [] and fim['situacao'] != 'concluido'


def test_resposta_simultanea_e_recusada(jev):
    falsa = AgendaFalsa()
    t = Jev(**PEDIDO_JEV)
    r = jev.agenda.agendar('reunião semana que vem à tarde', agenda=falsa, transporte=t, agora=AGORA)
    trava = jev.ciclo.caminho(r['id']).with_suffix('.trava')
    trava.write_text('outra chamada em curso')
    with pytest.raises(ValueError, match='já está processando'):
        jev.agenda.responder(r['id'], '1', agenda=falsa, transporte=t, agora=AGORA)
    assert falsa.criados == []


def test_agente_que_enfraquece_o_teste_nao_e_aprovado(jev, tmp_path):
    pasta = tmp_path / 'r'
    (pasta / 'tests').mkdir(parents=True)
    (pasta / 'tests' / 'test_a.py').write_text('def test_a():\n    assert 1 == 2\n', encoding='utf-8')
    jev.avaliacao.preparar_git(pasta)
    base = jev.avaliacao.linha_de_base(pasta)
    assert jev.avaliacao.observar_integridade(pasta, base) is None
    (pasta / 'tests' / 'test_b.py').write_text('def test_b():\n    pass\n', encoding='utf-8')   # teste novo: livre
    assert jev.avaliacao.observar_integridade(pasta, base) is None
    (pasta / 'tests' / 'test_a.py').write_text('def test_a():\n    assert 1 == 1\n', encoding='utf-8')
    (pasta / 'conftest.py').write_text('', encoding='utf-8')
    obs = jev.avaliacao.observar_integridade(pasta, base)
    assert obs.resultado['falharam'] == 1 and 'test_a.py' in obs.conteudo and 'conftest.py' in obs.conteudo


def test_laco_sem_criterio_usa_o_padrao(jev):
    t = Jev(criterio_=('atendido', 0.95), relato=('sustentado', 0.95), sentinela=('nao-tenta', 0.99))
    fim = jev.avaliacao.laco('x', [], lambda *a: {'texto': 'feito'}, lambda: [observacao_teste(jev)], transporte=t)
    assert fim['resultado'] == 'aprovado'


def test_triagem_sentinela_incerto_nao_age_e_conversa_e_a_chave(jev):
    criados = []
    criar = lambda *a: criados.append(a) or 't_1'   # noqa: E731
    incerto = jev.triagem.despachar(ITEM, respostas('defeito-critico', 0.99, 'nao-tenta') | {
        'ordem': {'choice': 'nao-tenta', 'confidence': 0.6}}, criar=criar)
    assert incerto['acao'] == 'suspeito' and criados == []
    jev.triagem.despachar(ITEM | {'conversa': 'th9'}, respostas('pedido-de-funcionalidade', 0.99), criar=criar)
    assert criados[0][3] == 'e-mail:th9'


def test_jev_que_insiste_em_programar_e_barrado_pela_guarda(jev, oficina):
    """Bancada de 23/09: o Jev pedia PROGRAMAR oito vezes seguidas; a guarda obriga o teste."""
    pasta, teste, chamadas = oficina
    t = Jev(**JUDGE_OK, acao=lambda e, p: ('PROGRAMAR', 0.99) if 'PROGRAMAR' in p['criteria']
            else next((k, 0.95) for k in ('CONCLUIDO', 'REVISAR', 'TESTAR') if k in p['criteria']))
    fim = jev.agentes.resolver(pasta, 'Implemente: ok.txt deve conter 1', teste, transporte=t)
    assert fim['situacao'] == 'concluido', (fim['motivo'], fim['passos'])
    passos = [p.split(' ')[1] for p in fim['passos']]
    assert passos == ['PROGRAMAR', 'TESTAR', 'REVISAR', 'CONCLUIDO']


def test_programador_recebe_o_comando_de_teste(jev, oficina, monkeypatch):
    pasta, teste, _ = oficina
    prompts = []
    original = jev.modelos.executar_claude
    monkeypatch.setattr(jev.modelos, 'executar_claude', lambda p, *a, **k: prompts.append(p) or original(p, *a, **k))
    t = Jev(**JUDGE_OK, acao=lambda e, p: next((k, 0.95) for k in ('CONCLUIDO', 'REVISAR', 'TESTAR', 'PROGRAMAR')
                                                if k in p['criteria']))
    jev.agentes.resolver(pasta, 'ok.txt deve conter 1', teste, transporte=t)
    assert prompts and all(f'COMANDO DE TESTE DO PROJETO: {teste}' in p for p in prompts)


def test_isolamento_sem_rede_so_grava_na_pasta(jev, monkeypatch, tmp_path):
    from jev_hermes import isolamento
    monkeypatch.delenv('JEV_ISOLAMENTO', raising=False)
    monkeypatch.setattr(isolamento.shutil, 'which', lambda nome: '/usr/bin/bwrap' if nome == 'bwrap' else None)
    cmd = isolamento.isolar(['python3', '-m', 'pytest'], tmp_path)
    pasta = str(tmp_path.resolve())
    assert cmd[0] == '/usr/bin/bwrap' and cmd[-3:] == ['python3', '-m', 'pytest']
    assert ['--tmpfs', '/root'] == cmd[4:6] and '--unshare-all' in cmd and '--share-net' not in cmd
    assert cmd[cmd.index('--bind') + 1:cmd.index('--bind') + 3] == [pasta, pasta]
    com_rede = isolamento.isolar(['claude', '-p'], tmp_path, rede=True, claude=True)
    assert '--share-net' in com_rede
    monkeypatch.setenv('JEV_ISOLAMENTO', '0')
    assert isolamento.isolar(['python3'], tmp_path) == ['python3']


def test_limite_da_assinatura_desce_de_nivel_ate_o_reinicio(jev, monkeypatch, tmp_path):
    from datetime import timezone as tz

    class Limite:
        returncode = 1
        stdout = json.dumps({'result': "You've hit your session limit · resets 8:20am (UTC)", 'is_error': True,
                             'total_cost_usd': 0})
        stderr = ''
    monkeypatch.setattr(jev.modelos.subprocess, 'run', lambda cmd, **k: Limite())
    r = jev.modelos.executar_claude('x', tmp_path, jev.modelos.NIVEIS['especialista'] | {'nivel': 'especialista'})
    assert r['erro'] and r['limite']
    ate = jev.modelos.no_limite('opus')
    assert ate and (ate.hour, ate.minute) == (8, 20) and ate.tzinfo is not None
    d = jev.modelos.escolher('corrigir função', jev.modelos.Orcamento(5), tentativa=2, nivel_anterior='pequeno')
    assert d['nivel'] == 'pequeno' and 'limite da assinatura' in d['motivo']
    depois = datetime.now(tz.utc) + timedelta(days=2)
    assert jev.modelos.no_limite('opus', agora=depois) is None


def test_diff_ignora_cache_do_python(jev, tmp_path):
    (tmp_path / 'a.py').write_text('x = 1\n', encoding='utf-8')
    jev.avaliacao.preparar_git(tmp_path)
    base = jev.avaliacao.linha_de_base(tmp_path)
    (tmp_path / '__pycache__').mkdir()
    (tmp_path / '__pycache__' / 'a.cpython-311.pyc').write_bytes(b'\x00\x01')
    (tmp_path / 'novo.py').write_text('y = 2\n', encoding='utf-8')
    conteudo = jev.avaliacao.observar_diff(tmp_path, base).conteudo
    assert 'novo.py' in conteudo and 'pyc' not in conteudo


def test_laudo_leva_ao_juiz_o_codigo_que_cita(jev, tmp_path):
    (tmp_path / 'pedidos').mkdir()
    (tmp_path / 'pedidos' / 'cupom.py').write_text('def aplicar(s, p):\n    return s\n', encoding='utf-8')
    (tmp_path / 'outro.py').write_text('x = 1\n', encoding='utf-8')
    jev.avaliacao.preparar_git(tmp_path)
    base = jev.avaliacao.linha_de_base(tmp_path)
    (tmp_path / 'CAUSA.md').write_text('A causa está em `pedidos/cupom.py:2`, função aplicar.\n', encoding='utf-8')
    obs = jev.avaliacao.observar_tudo(f'"{PY}" -c "print(\'1 passed\')"', tmp_path, base)
    citados = [o for o in obs if o.tipo == 'artefato']
    assert Path(citados[0].referencia).as_posix().endswith('pedidos/cupom.py') and 'def aplicar' in citados[0].conteudo
    assert not any('outro.py' in o.referencia for o in citados)


def test_lembrete_so_cala_bloqueio_pessoal_com_confianca(jev):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'lembrete', Path(__file__).resolve().parents[1] / 'rotinas' / 'jev_rotina_lembrete_compromisso.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    agora = datetime(2026, 9, 28, 13, 5, tzinfo=m.FUSO)
    ev = lambda t, link='': {'titulo': t, 'inicio': datetime(2026, 9, 28, 14, 0, tzinfo=m.FUSO),   # noqa: E731
                             'link': link, 'local': ''}
    r = lambda nat, conf, prep=0.1: {'natureza': {'choice': nat, 'confidence': conf},   # noqa: E731
                                     'preparo': {'noul': prep}}
    linhas, pessoais = m.decidir([ev('Foco'), ev('Almoço'), ev('Audiência', 'https://meet'), ev('Sem Jev')],
                                 [(r('bloqueio-pessoal', 0.98), {}), (r('bloqueio-pessoal', 0.77), {}),
                                  (r('com-outras-pessoas', 0.99, 0.88), {}), (None, {})], agora)
    assert pessoais == 1 and len(linhas) == 3
    assert linhas[1] == '⏰ Em 55 min (14:00): Audiência — Meet: https://meet — ⚠ pede preparo'
