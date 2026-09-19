"""Regressão dos achados da SEXTA e da SÉTIMA rodadas de revisão (Grok 4.6 via Cursor, 2026-09-19).

Esta rodada foi a mais dura do estudo, e com razão: ela mostrou que o painel tinha começado a
contar meia verdade. Os testes de defeito financeiro estão aqui; os defeitos de leitura do
placar estão registrados no relatório final e corrigidos em `executor/placar.py`.
"""
import json
import tempfile
import unittest
from pathlib import Path

from executor.ledger import BudgetError, Ledger
from executor.pricing import usd_to_nusd
from executor.run_e8_anotador import kappa_cohen
from executor.run_e9_prevalencia import acuracia_por_classe, aceitacao

PRECOS = {
    'schema_version': 1, 'snapshot_id': 'tarifa-A',
    'models': {'openrouter:m': {'input_nusd_per_million_tokens': 1_000_000,
                                'output_nusd_per_million_tokens': 0,
                                'context_length': 1000, 'max_completion_tokens': 100}},
}


def reserva(**over):
    args = dict(arm_id='arm-1', block_id='b1', provider='openrouter', model='m',
                max_input_tokens=1000, max_output_tokens=100, payload_sha256='0' * 64,
                request_path='r.jsonl', runtime_manifest_path='m.json')
    args.update(over)
    return args


class PausaResisteAReautorizacao(unittest.TestCase):
    """[R6-1] O defeito mais grave da sexta rodada.

    Todo runner chama authorize() no arranque. Como era INSERT OR REPLACE com status fixo em
    'running', relançar o script apagava uma pausa por estouro de teto — e apagava também as
    emendas registradas. A trava criada na quinta rodada não valia nada no caminho real.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.temp.name) / 'l.sqlite3', 'exp', prices=PRECOS)
        self.ledger.set_wallet_cap(usd_to_nusd('5.00'))
        self.ledger.authorize(usd_to_nusd('5.00'))
        self.ledger.set_block_cap('b1', usd_to_nusd('5.00'))
        self.ledger.register_arm('arm-1', 'S01', 'openrouter', 'm')

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def test_reautorizar_nao_retoma_experimento_pausado(self):
        self.ledger.db.execute("UPDATE experiments SET status = 'paused' WHERE experiment_id = 'exp'")
        with self.assertRaises(BudgetError) as ctx:
            self.ledger.authorize(usd_to_nusd('5.00'))
        self.assertIn('retomar_experimento', str(ctx.exception))
        estado = self.ledger.db.execute(
            "SELECT status FROM experiments WHERE experiment_id = 'exp'").fetchone()
        self.assertEqual(estado['status'], 'paused')

    def test_reserva_continua_negada_depois_de_reautorizar(self):
        self.ledger.db.execute("UPDATE experiments SET status = 'paused' WHERE experiment_id = 'exp'")
        with self.assertRaises(BudgetError):
            self.ledger.authorize(usd_to_nusd('5.00'))
        with self.assertRaises(BudgetError):
            self.ledger.reserve(**reserva())

    def test_reautorizar_preserva_emendas(self):
        self.ledger.db.execute(
            """UPDATE experiments SET amendments_json = '[{"n":1}]' WHERE experiment_id = 'exp'""")
        self.ledger.authorize(usd_to_nusd('4.00'))
        linha = self.ledger.db.execute(
            "SELECT amendments_json, budget_cap_nusd FROM experiments WHERE experiment_id = 'exp'"
        ).fetchone()
        self.assertEqual(json.loads(linha['amendments_json']), [{'n': 1}])
        self.assertEqual(linha['budget_cap_nusd'], usd_to_nusd('4.00'))


class ChaveAntesDaReserva(unittest.TestCase):
    """[R6-3] Falhar ao ler a chave depois de reservar deixava saldo preso sem requisição."""

    def test_dispatch_carrega_a_chave_antes_de_reservar(self):
        import inspect

        from executor import runner
        fonte = inspect.getsource(runner.dispatch)
        posicao_chave = fonte.index('key = api_key or load_api_key()')
        posicao_reserva = fonte.index('ledger.reserve(')
        self.assertLess(posicao_chave, posicao_reserva,
                        'A chave precisa ser resolvida antes da reserva')


class AnaliseNaoApagaCalibracaoDeConfirmacao(unittest.TestCase):
    """[R6-2] Rodar o analisador oficial apagava a calibração da partição de teste."""

    def test_main_grava_confirmacao_quando_o_relatorio_existe(self):
        import inspect

        from executor import analise
        fonte = inspect.getsource(analise.main)
        self.assertIn('calibracao_confirmacao_', fonte)
        self.assertIn("conjunto='confirmacao'", fonte)


class MetricasDoE8eE9(unittest.TestCase):
    """[R6-4] E8 e E9 entraram no painel sem nenhum teste."""

    def test_kappa_e_um_quando_concordam_sempre(self):
        pares = [('a', 'a')] * 5 + [('b', 'b')] * 5
        self.assertEqual(kappa_cohen(pares), 1.0)

    def test_kappa_e_zero_no_nivel_do_acaso(self):
        # Dois anotadores que sorteiam independentemente a mesma marginal.
        pares = [('a', 'a'), ('a', 'b'), ('b', 'a'), ('b', 'b')]
        self.assertEqual(kappa_cohen(pares), 0.0)

    def test_classe_sem_erro_recebe_limite_superior(self):
        casos = [{'gold': 'x', 'jev': 'x'} for _ in range(16)]
        saida = acuracia_por_classe(casos)
        self.assertEqual(saida['x']['taxa'], 1.0)
        # Zero erro em 16 nao e risco zero: o limite tem que existir e ser grande.
        self.assertGreater(saida['x']['limite_superior_erro'], 0.15)

    def test_politica_conta_erro_entre_aceitos(self):
        casos = [{'gold': 'x', 'jev': 'y', 'confidence': 0.99, 'custo_nusd': 0, 'latency_ms': 1},
                 {'gold': 'x', 'jev': 'x', 'confidence': 0.50, 'custo_nusd': 0, 'latency_ms': 1}]
        saida = aceitacao(casos, 0.90)
        self.assertEqual(saida['aceitos'], 1)
        self.assertEqual(saida['erros_entre_aceitos'], 1)
        self.assertEqual(saida['enviados_a_revisao'], 1)

    def test_ambigua_em_texto_nao_vira_verdadeiro(self):
        """bool('false') e True; o parser tem que tratar a string."""
        from executor import run_e8_anotador
        import inspect
        fonte = inspect.getsource(run_e8_anotador.perguntar)
        self.assertIn('isinstance(bruto, str)', fonte)


class PlacarNaoUsaAcuraciaCondicional(unittest.TestCase):
    """[R6-5] O cartão lia `acuracia`, que ignora resposta ausente, em vez do denominador certo."""

    def test_sobre_programados_conta_ausencia_como_erro(self):
        from executor.placar import sobre_programados
        bloco = {'acertos': 8}
        casos = [{}] * 10  # 10 programados, 8 acertos: duas respostas sumiram
        acuracia, programados = sobre_programados(bloco, casos)
        self.assertEqual(programados, 10)
        self.assertEqual(acuracia, 0.8)

    def test_relatorio_novo_usa_o_campo_proprio(self):
        from executor.placar import sobre_programados
        bloco = {'acertos': 8, 'acuracia_sobre_programados': 0.8, 'casos_programados': 10}
        self.assertEqual(sobre_programados(bloco, []), (0.8, 10))



class SetimaRodada(unittest.TestCase):
    """[R7] A correção da sexta rodada criou defeitos novos, como sempre."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.temp.name) / 'l.sqlite3', 'exp', prices=PRECOS)
        self.ledger.set_wallet_cap(usd_to_nusd('5.00'))
        self.ledger.authorize(usd_to_nusd('5.00'))

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def teto(self):
        return self.ledger.db.execute(
            "SELECT budget_cap_nusd FROM experiments WHERE experiment_id = 'exp'").fetchone()[0]

    def test_reautorizar_nao_devolve_teto_que_a_emenda_tirou(self):
        """[R7-1] Todo runner chama authorize(US$ 5) no arranque.

        Enquanto isso reescrevia o teto, uma emenda que baixou o limite para US$ 1 virava
        decoração: bastava relançar o script para ter os US$ 5 de volta, sem registro.
        """
        self.ledger.db.execute('UPDATE experiments SET budget_cap_nusd = ? WHERE experiment_id = ?',
                               (usd_to_nusd('1.00'), 'exp'))
        efetivo = self.ledger.authorize(usd_to_nusd('5.00'))
        self.assertEqual(self.teto(), usd_to_nusd('1.00'))
        self.assertEqual(efetivo, usd_to_nusd('1.00'))

    def test_reautorizar_ainda_pode_reduzir(self):
        self.ledger.authorize(usd_to_nusd('0.50'))
        self.assertEqual(self.teto(), usd_to_nusd('0.50'))

    def test_ampliar_exige_motivo_evidencia_e_respeita_a_carteira(self):
        self.ledger.authorize(usd_to_nusd('1.00'))
        from executor.ledger import BudgetError, LedgerStateError
        with self.assertRaises(LedgerStateError):
            self.ledger.ampliar_teto_do_experimento(usd_to_nusd('2.00'), motivo='', evidence={'e': 1})
        with self.assertRaises(BudgetError):
            self.ledger.ampliar_teto_do_experimento(usd_to_nusd('9.00'), motivo='mais casos',
                                                    evidence={'plano': 'x'})
        self.ledger.ampliar_teto_do_experimento(usd_to_nusd('2.00'), motivo='mais casos',
                                                evidence={'plano': 'x'})
        self.assertEqual(self.teto(), usd_to_nusd('2.00'))

    def test_titulo_do_veredito_cai_quando_a_politica_deixa_erro(self):
        """[R7-2] O título recomendava o corte 0,90 mesmo que ele passasse a errar."""
        from executor.placar import titulo_do_veredito
        ruim = {'por_particao': {'confirmacao (teste)': {'politicas': [
            {'corte': 0.90, 'erros_entre_aceitos': 2},
            {'corte': 0.99, 'erros_entre_aceitos': 0}]}}}
        self.assertIn('0.99', titulo_do_veredito(ruim))
        pior = {'por_particao': {'confirmacao (teste)': {'politicas': [
            {'corte': 0.90, 'erros_entre_aceitos': 2},
            {'corte': 0.99, 'erros_entre_aceitos': 1}]}}}
        self.assertIn('Revisao humana de todas', titulo_do_veredito(pior))
        self.assertIn('Sem analise', titulo_do_veredito(None))

    def test_classe_com_erro_tambem_recebe_limite(self):
        """[R7-3] A função de limite existia e nunca era chamada; classe com erro ficava sem."""
        from executor.run_e9_prevalencia import acuracia_por_classe
        casos = [{'gold': 'x', 'jev': 'x'} for _ in range(15)] + [{'gold': 'x', 'jev': 'y'}]
        saida = acuracia_por_classe(casos)
        self.assertIn('limite_superior_erro', saida['x'])
        self.assertGreater(saida['x']['limite_superior_erro'], 0.06)

    def test_ambigua_ausente_e_desconhecida_nao_falsa(self):
        """[R7-4] Campo ausente virava 'o modelo disse que não é ambíguo'."""
        import inspect

        from executor import run_e8_anotador
        fonte = inspect.getsource(run_e8_anotador.perguntar)
        self.assertIn('if bruto is None', fonte)

if __name__ == '__main__':
    unittest.main()
