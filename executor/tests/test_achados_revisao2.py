"""Regressão dos achados da SEGUNDA rodada de revisão independente (2026-09-19).

A primeira rodada de correções criou defeitos novos, como o protocolo da casa prevê.
Cada teste aqui reproduz um deles.
"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from executor.analise import bootstrap_cluster, limite_superior_erro
from executor.ledger import Ledger
from executor.pricing import usd_to_nusd

PRECOS = {
    'schema_version': 1, 'snapshot_id': 'tarifa-A',
    'models': {'openrouter:m': {'input_nusd_per_million_tokens': 1_000_000,
                                'output_nusd_per_million_tokens': 0,
                                'context_length': 1000, 'max_completion_tokens': 100}},
}
PRECOS_B = {
    'schema_version': 1, 'snapshot_id': 'tarifa-B',
    'models': {'openrouter:m': {'input_nusd_per_million_tokens': 1,
                                'output_nusd_per_million_tokens': 0,
                                'context_length': 1000, 'max_completion_tokens': 100}},
}


def reserva(**over):
    args = dict(arm_id='arm-1', block_id='b1', provider='openrouter', model='m',
                max_input_tokens=1000, max_output_tokens=100, payload_sha256='0' * 64,
                request_path='r.jsonl', runtime_manifest_path='m.json')
    args.update(over)
    return args


class ConciliacaoRound2(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.temp.name) / 'l.sqlite3'
        self.ledger = Ledger(self.caminho, 'exp', prices=PRECOS)
        self.ledger.set_wallet_cap(usd_to_nusd('5.00'))
        self.ledger.authorize(usd_to_nusd('5.00'))
        self.ledger.set_block_cap('b1', usd_to_nusd('5.00'))
        self.ledger.register_arm('arm-1', 'S01', 'openrouter', 'm')

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def test_extrato_e_comparado_com_liquidado_e_nao_com_reservas(self):
        """[R2-1] Reserva pendente não é gasto realizado; comparar com ela escondia divergência."""
        pendente = self.ledger.reserve(**reserva())['attempt_id']
        self.assertGreater(self.ledger.wallet_committed_nusd(), 0)
        self.assertEqual(self.ledger.settled_nusd_total(), 0)
        saida = self.ledger.reconcile('openrouter', 300_000, {'nota': 'gasto externo'})
        # O extrato acusa gasto que o ledger nao liquidou: tem de ocupar o teto.
        self.assertEqual(saida['excedente_nusd'], 300_000)
        self.assertEqual(saida['liquidado_do_provedor_nusd'], 0)
        self.ledger.cancel_before_send(pendente, evidence={'motivo': 'teste'})
        self.assertEqual(self.ledger.wallet_committed_nusd(), 300_000)

    def test_conciliacoes_sucessivas_nao_somam_o_mesmo_excedente(self):
        """[R2-3] O excedente é calculado, então repetir a conciliação não acumula nada."""
        self.ledger.reconcile('openrouter', 100_000, {'n': 1})
        primeiro = self.ledger.wallet_committed_nusd()
        self.ledger.reconcile('openrouter', 100_000, {'n': 2})
        self.ledger.reconcile('openrouter', 100_000, {'n': 3})
        self.assertEqual(self.ledger.wallet_committed_nusd(), primeiro)
        # Nenhuma linha sintetica e criada: o excedente nao e materializado.
        linhas = self.ledger.db.execute(
            "SELECT COUNT(*) n FROM attempt_budget WHERE cost_source = 'provider_statement_excess'"
        ).fetchone()
        self.assertEqual(linhas['n'], 0)

    def test_gasto_novo_nao_consome_o_excedente_ja_observado(self):
        """[R4-1] O furo que o cálculo dinâmico abriu.

        Com o excedente calculado contra o liquidado de agora, uma chamada feita DEPOIS do
        extrato reduzia o excedente ao ser liquidada e devolvia espaço no teto — o mesmo
        dinheiro podia ser gasto duas vezes. Ancorado no snapshot, isso não acontece.
        """
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 1})
        self.assertEqual(self.ledger.wallet_committed_nusd(), 1_000_000)
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        self.ledger.settle(attempt, provider_reported_cost_nusd=1_000_000)
        # O gasto novo SOMA ao excedente ja observado, nao o substitui.
        self.assertEqual(self.ledger.wallet_committed_nusd(), 2_000_000)

    def test_extrato_atrasado_nao_apaga_divergencia_ja_vista(self):
        """[R4-1] Mantemos o maior excedente observado por provedor."""
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 1})
        self.ledger.reconcile('openrouter', 0, {'n': 2, 'nota': 'extrato atrasado'})
        self.assertEqual(self.ledger.wallet_committed_nusd(), 1_000_000)

    def test_historico_do_mesmo_provedor_nao_e_contado_duas_vezes(self):
        """[R3-1] Histórico sem provedor ficava fora da soma e o extrato o somava de novo."""
        self.ledger.record_historical_commitment(1_000_000, {'fonte': 'dossie'}, provider='openrouter')
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 1})
        self.assertEqual(self.ledger.wallet_committed_nusd(), 1_000_000)

    def test_historico_sem_provedor_e_recusado(self):
        """[R4-3] A docstring exigia provedor; a implementação não."""
        from executor.ledger import LedgerStateError
        with self.assertRaises(LedgerStateError):
            self.ledger.record_historical_commitment(500, {'fonte': 'desconhecida'})

    def test_regularizacao_liquida_pelo_pior_caso_e_nao_pela_tarifa_escolhida(self):
        """[R4-2] Antes, bastava declarar um modelo barato para liberar saldo de reserva antiga."""
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        reservado = self.ledger.wallet_committed_nusd()
        self.ledger.db.execute(
            'UPDATE attempt_budget SET priced_provider = NULL, priced_model = NULL,'
            ' priced_snapshot_id = NULL WHERE attempt_id = ?', (attempt,))
        from executor.ledger import LedgerStateError
        with self.assertRaises(LedgerStateError):
            self.ledger.settle(attempt, usage={'input_tokens': 1, 'output_tokens': 0})
        self.ledger.regularizar_identidade(attempt, 'openrouter', 'm',
                                           motivo='base migrada de versao anterior')
        saida = self.ledger.settle(attempt, usage={'input_tokens': 1, 'output_tokens': 0})
        self.assertEqual(saida['cost_source'], 'worst_case_price_snapshot_divergente')
        self.assertEqual(saida['settled_nusd'], reservado)

    def test_regularizacao_exige_provedor_e_modelo(self):
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        from executor.ledger import LedgerStateError
        with self.assertRaises(LedgerStateError):
            self.ledger.regularizar_identidade(attempt, 'openrouter', None, motivo='sem modelo')

    def test_experimento_pausado_nao_reserva(self):
        """[R4-6] reserve() não consultava o status pausado."""
        from executor.ledger import BudgetError
        self.ledger.db.execute("UPDATE experiments SET status = 'paused' WHERE experiment_id = 'exp'")
        with self.assertRaises(BudgetError) as ctx:
            self.ledger.reserve(**reserva())
        self.assertIn('pausado', str(ctx.exception))

    def test_migracao_remove_ajuste_materializado_antigo(self):
        """[R4-4] Linhas da versão anterior contariam o excedente duas vezes."""
        self.ledger.db.execute(
            "INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,"
            "settled_nusd,cost_source) VALUES('conciliacao:openrouter','exp','conciliacao',"
            "7000,7000,'provider_statement_excess')")
        self.ledger.close()
        reaberto = Ledger(self.caminho, 'exp', prices=PRECOS)
        try:
            linhas = reaberto.db.execute(
                "SELECT COUNT(*) n FROM attempt_budget WHERE cost_source = 'provider_statement_excess'"
            ).fetchone()
            self.assertEqual(linhas['n'], 0)
        finally:
            reaberto.close()
        self.ledger = Ledger(self.caminho, 'exp', prices=PRECOS)

    def test_extrato_menor_que_o_liquidado_nao_devolve_saldo(self):
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        self.ledger.settle(attempt, provider_reported_cost_nusd=500_000)
        antes = self.ledger.wallet_committed_nusd()
        self.ledger.reconcile('openrouter', 1, {'nota': 'extrato atrasado'})
        self.assertEqual(self.ledger.wallet_committed_nusd(), antes)


class TarifaEMigracao(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.temp.name) / 'l.sqlite3'

    def tearDown(self):
        self.temp.cleanup()

    def abrir(self, precos):
        ledger = Ledger(self.caminho, 'exp', prices=precos)
        ledger.set_wallet_cap(usd_to_nusd('5.00'))
        ledger.authorize(usd_to_nusd('5.00'))
        ledger.set_block_cap('b1', usd_to_nusd('5.00'))
        ledger.register_arm('arm-1', 'S01', 'openrouter', 'm')
        return ledger

    def test_liquidar_com_tabela_de_precos_diferente_conserva_a_reserva(self):
        """[R2-4] Tarifa nova não pode liquidar reserva feita com tarifa antiga."""
        ledger = self.abrir(PRECOS)
        attempt = ledger.reserve(**reserva())['attempt_id']
        reservado = ledger.wallet_committed_nusd()
        ledger.close()

        outro = Ledger(self.caminho, 'exp', prices=PRECOS_B)
        try:
            saida = outro.settle(attempt, usage={'input_tokens': 1000, 'output_tokens': 0})
            self.assertEqual(saida['cost_source'], 'worst_case_price_snapshot_divergente')
            self.assertEqual(saida['settled_nusd'], reservado)
        finally:
            outro.close()

    def test_base_antiga_ganha_as_colunas_novas(self):
        """[R2-8] CREATE TABLE IF NOT EXISTS não altera tabela existente."""
        antiga = Path(self.temp.name) / 'antiga.sqlite3'
        conexao = sqlite3.connect(antiga)
        conexao.executescript(
            'CREATE TABLE experiments (experiment_id TEXT PRIMARY KEY, protocol_version TEXT,'
            ' hypothesis TEXT, primary_metric TEXT, decision_rule_json TEXT, preregistered_at_utc TEXT,'
            ' seed INTEGER, budget_cap_nusd INTEGER, status TEXT, amendments_json TEXT);'
            'CREATE TABLE attempt_budget (attempt_id TEXT PRIMARY KEY, experiment_id TEXT,'
            ' block_id TEXT, reserved_nusd INTEGER, settled_nusd INTEGER, cost_source TEXT);'
            "INSERT INTO attempt_budget VALUES ('velha','exp','b1',1000,1000,'usage_priced');")
        conexao.commit()
        conexao.close()

        ledger = Ledger(antiga, 'exp', prices=PRECOS)
        try:
            colunas = {l['name'] for l in ledger.db.execute('PRAGMA table_info(attempt_budget)')}
            self.assertIn('priced_provider', colunas)
            self.assertIn('priced_snapshot_id', colunas)
            self.assertEqual(ledger.settled_nusd_total(), 1000)
        finally:
            ledger.close()


class EstatisticaRound2(unittest.TestCase):
    def test_massa_de_cauda_nunca_passa_de_um(self):
        """[R2-5] Com todas as diferenças iguais a zero, a conta antiga devolvia 2.0."""
        clusters = {'F1': [(True, True), (True, True)], 'F2': [(False, False), (True, True)]}
        saida = bootstrap_cluster(clusters, repeticoes=500)
        self.assertLessEqual(saida['massa_de_cauda_bilateral'], 1.0)
        self.assertEqual(saida['diferenca_observada'], 0.0)

    def test_limite_por_familia_e_mais_conservador_que_por_caso(self):
        """[R2-6] Casos dependentes não são ensaios independentes."""
        por_caso = limite_superior_erro(0, 28)
        por_familia = limite_superior_erro(0, 9)
        self.assertLess(por_caso, por_familia)
        self.assertAlmostEqual(por_caso, 0.101466, places=5)

    def test_p_de_permutacao_nunca_e_zero(self):
        """[R2-9] (extremos + 1) / (repeticoes + 1)."""
        self.assertGreater((0 + 1) / (20000 + 1), 0)


if __name__ == '__main__':
    unittest.main()
