"""Regressão dos achados da QUINTA rodada de revisão independente (2026-09-19).

A quarta rodada fechou o furo do excedente dinâmico ancorando-o no snapshot. Ao fazer isso,
criou três problemas novos: a migração apagava o compromisso antigo sem ancorar o valor em
lugar nenhum, a âncora não tinha caminho de volta, e a pausa por estouro não tinha retomada.
Cada teste aqui reproduz um deles. Todos falhavam antes da correção.
"""
import tempfile
import unittest
from pathlib import Path

from executor.ledger import Ledger, LedgerStateError
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


class Round5(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.temp.name) / 'l.sqlite3'
        self.ledger = Ledger(self.caminho, 'exp', prices=PRECOS)
        self.ledger.set_wallet_cap(usd_to_nusd('5.00'))
        self.ledger.authorize(usd_to_nusd('5.00'))
        self.ledger.set_block_cap('b1', usd_to_nusd('5.00'))
        self.ledger.register_arm('arm-1', 'S01', 'openrouter', 'm')

    def tearDown(self):
        try:
            self.ledger.close()
        except Exception:
            pass
        self.temp.cleanup()

    def reabrir(self, prices=PRECOS):
        self.ledger.close()
        self.ledger = Ledger(self.caminho, 'exp', prices=prices)
        return self.ledger

    # ---- R5-1: migração apagava compromisso sem preservar o valor ----
    def test_migracao_preserva_o_excedente_da_versao_anterior(self):
        """Sem âncora, apagar a linha devolvia ao teto dinheiro que o provedor já cobrou."""
        self.ledger.db.execute(
            "INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,"
            "settled_nusd,cost_source) VALUES('conciliacao:openrouter','exp','conciliacao',"
            "7000,7000,'provider_statement_excess')")
        antes = self.ledger.wallet_committed_nusd()
        self.assertEqual(antes, 7000)
        reaberto = self.reabrir()
        self.assertEqual(
            reaberto.db.execute("SELECT COUNT(*) n FROM attempt_budget"
                                " WHERE cost_source = 'provider_statement_excess'").fetchone()['n'], 0)
        self.assertEqual(reaberto.excedente_de_extrato_nusd(), 7000)
        self.assertEqual(reaberto.wallet_committed_nusd(), antes)

    def test_migracao_ancora_no_snapshot_existente_do_provedor(self):
        self.ledger.reconcile('openrouter', 0, {'n': 1})
        self.ledger.db.execute(
            "INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,"
            "settled_nusd,cost_source) VALUES('conciliacao:openrouter','exp','conciliacao',"
            "7000,7000,'provider_statement_excess')")
        reaberto = self.reabrir()
        linhas = reaberto.db.execute(
            'SELECT COUNT(*) n FROM provider_snapshots WHERE provider = ?', ('openrouter',)).fetchone()
        self.assertEqual(linhas['n'], 1)  # ancorou no snapshot que já existia, não criou outro
        self.assertEqual(reaberto.excedente_de_extrato_nusd(), 7000)

    def test_migracao_e_uma_transacao_so(self):
        """Se a ancoragem falhar, nada é apagado."""
        self.ledger.db.execute(
            "INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,"
            "settled_nusd,cost_source) VALUES('conciliacao:openrouter','exp','conciliacao',"
            "7000,7000,'provider_statement_excess')")
        self.ledger.close()
        original = Ledger._migrar_ajuste_materializado

        def explode(self):
            original(self)
            raise RuntimeError('falha no meio da migracao')

        Ledger._migrar_ajuste_materializado = explode
        try:
            with self.assertRaises(RuntimeError):
                Ledger(self.caminho, 'exp', prices=PRECOS)
        finally:
            Ledger._migrar_ajuste_materializado = original
        self.ledger = Ledger(self.caminho, 'exp', prices=PRECOS)
        self.assertEqual(self.ledger.excedente_de_extrato_nusd(), 7000)
        self.assertEqual(self.ledger.wallet_committed_nusd(), 7000)

    # ---- R5-2: âncora sem caminho de volta ----
    def test_excedente_ancorado_pode_ser_baixado_com_evidencia(self):
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 1})
        self.assertEqual(self.ledger.wallet_committed_nusd(), 1_000_000)
        saida = self.ledger.baixar_excedente(
            'openrouter', 1_000_000, motivo='gasto identificado e registrado como tentativa',
            evidence={'attempt_id': 'a-1', 'extrato': 'fatura 2026-09'})
        self.assertEqual(saida['excedente_restante_nusd'], 0)
        self.assertEqual(self.ledger.wallet_committed_nusd(), 0)

    def test_baixa_nao_passa_do_excedente_ancorado(self):
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 1})
        with self.assertRaises(LedgerStateError):
            self.ledger.baixar_excedente('openrouter', 1_000_001, motivo='x', evidence={'e': 1})
        self.assertEqual(self.ledger.wallet_committed_nusd(), 1_000_000)

    def test_baixa_exige_motivo_e_evidencia(self):
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 1})
        with self.assertRaises(LedgerStateError):
            self.ledger.baixar_excedente('openrouter', 10, motivo='', evidence={'e': 1})
        with self.assertRaises(LedgerStateError):
            self.ledger.baixar_excedente('openrouter', 10, motivo='ok', evidence={})

    def test_baixa_sobrevive_a_extrato_novo(self):
        """Um extrato posterior não pode ressuscitar o excedente já baixado."""
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 1})
        self.ledger.baixar_excedente('openrouter', 1_000_000, motivo='identificado',
                                     evidence={'attempt_id': 'a-1'})
        self.ledger.reconcile('openrouter', 1_000_000, {'n': 2})
        self.assertEqual(self.ledger.excedente_de_extrato_nusd(), 0)

    # ---- R5-3: pausa sem retomada auditável ----
    def test_experimento_pausado_pode_retomar_quando_volta_ao_teto(self):
        self.ledger.db.execute("UPDATE experiments SET status = 'paused' WHERE experiment_id = 'exp'")
        from executor.ledger import BudgetError
        with self.assertRaises(BudgetError):
            self.ledger.reserve(**reserva())
        self.ledger.retomar_experimento(motivo='teto recomposto apos conciliacao',
                                        evidence={'extrato': 'fatura 2026-09'})
        self.assertTrue(self.ledger.reserve(**reserva())['attempt_id'])

    def test_retomada_negada_enquanto_o_teto_estiver_estourado(self):
        self.ledger.reconcile('openrouter', usd_to_nusd('9.00'), {'n': 1})
        self.ledger.db.execute("UPDATE experiments SET status = 'paused' WHERE experiment_id = 'exp'")
        with self.assertRaises(LedgerStateError):
            self.ledger.retomar_experimento(motivo='quero continuar', evidence={'e': 1})

    def test_retomada_exige_motivo_e_evidencia(self):
        self.ledger.db.execute("UPDATE experiments SET status = 'paused' WHERE experiment_id = 'exp'")
        with self.assertRaises(LedgerStateError):
            self.ledger.retomar_experimento(motivo='', evidence={'e': 1})

    # ---- R4-5: liquidação conservadora irreversível ----
    def test_liquidacao_conservadora_pode_ser_retificada_com_evidencia(self):
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        reaberto = self.reabrir(PRECOS_B)  # tabela de precos diferente da reserva
        saida = reaberto.settle(attempt, usage={'input_tokens': 1, 'output_tokens': 0})
        self.assertEqual(saida['cost_source'], 'worst_case_price_snapshot_divergente')
        retificado = reaberto.retificar_liquidacao(
            attempt, 3, motivo='extrato do provedor mostrou o custo real',
            evidence={'fatura': '2026-09', 'linha': 12})
        self.assertEqual(retificado['settled_anterior_nusd'], saida['settled_nusd'])
        self.assertEqual(reaberto.settled_nusd_total('openrouter'), 3)

    def test_liquidacao_reportada_pelo_provedor_nao_e_retificavel(self):
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        self.ledger.settle(attempt, provider_reported_cost_nusd=50)
        with self.assertRaises(LedgerStateError):
            self.ledger.retificar_liquidacao(attempt, 1, motivo='quero baixar',
                                             evidence={'e': 1})

    def test_retificacao_nao_pode_estourar_o_teto(self):
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        reaberto = self.reabrir(PRECOS_B)
        reaberto.settle(attempt, usage={'input_tokens': 1, 'output_tokens': 0})
        with self.assertRaises(LedgerStateError):
            reaberto.retificar_liquidacao(attempt, usd_to_nusd('9.00'), motivo='custo real',
                                          evidence={'fatura': 'x'})


if __name__ == '__main__':
    unittest.main()
