"""Testes offline do controle financeiro: concorrencia, reinicio, timeout, usage ausente e arredondamento.

Nenhum teste faz chamada de rede. O executor precisa passar aqui antes de qualquer chamada paga.
"""
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from executor.ledger import BudgetError, Ledger, LedgerStateError
from executor.pricing import PricingError, observed_nusd, usd_to_nusd, worst_case_nusd

PRICES = {
    'schema_version': 1,
    'snapshot_id': 'fixture-prices',
    'captured_at_utc': '2026-09-18T00:00:00Z',
    'models': {
        # 1 nusd/token de entrada e 3 nusd/token de saida, em preco por milhao.
        'openrouter:typesafe/jev-1.13': {
            'input_nusd_per_million_tokens': 1_000_000,
            'output_nusd_per_million_tokens': 3_000_000,
        },
        # Preco que nao divide exato por milhao, para checar arredondamento.
        'openrouter:odd-price': {
            'input_nusd_per_million_tokens': 1,
            'output_nusd_per_million_tokens': 1,
            'request_surcharge_nusd': 7,
        },
    },
}
MODEL = 'typesafe/jev-1.13'
PROVIDER = 'openrouter'


def reserve_args(**overrides):
    args = dict(arm_id='arm-1', block_id='b1', provider=PROVIDER, model=MODEL,
                max_input_tokens=1000, max_output_tokens=100,
                payload_sha256='0' * 64, request_path='requests/x.jsonl',
                runtime_manifest_path='manifests/x.json')
    args.update(overrides)
    return args


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'ledger.sqlite3'
        self.ledger = self.open_ledger()
        self.ledger.authorize(usd_to_nusd('1.00'))
        self.ledger.set_block_cap('b1', usd_to_nusd('0.25'))
        self.ledger.register_arm('arm-1', 'S01', PROVIDER, MODEL)

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def open_ledger(self):
        return Ledger(self.path, 'exp-test', prices=PRICES)

    # --- precificacao -------------------------------------------------
    def test_pior_caso_usa_teto_de_tokens(self):
        # 1000 * 1 + 100 * 3 nanodolares.
        self.assertEqual(worst_case_nusd(PRICES, PROVIDER, MODEL, 1000, 100), 1300)

    def test_sem_preco_nao_reserva(self):
        with self.assertRaises(PricingError):
            self.ledger.reserve(**reserve_args(model='modelo-sem-preco'))
        self.assertEqual(self.ledger.committed_nusd(), 0)

    def test_sem_teto_de_tokens_nao_reserva(self):
        with self.assertRaises(PricingError):
            self.ledger.reserve(**reserve_args(max_output_tokens=None))
        self.assertEqual(self.ledger.committed_nusd(), 0)

    def test_arredondamento_nunca_subestima(self):
        # 1 nusd por milhao de tokens: qualquer fracao sobe para 1, mais a taxa fixa.
        self.assertEqual(observed_nusd(PRICES, PROVIDER, 'odd-price', 1, 0), 1 + 7)
        self.assertEqual(observed_nusd(PRICES, PROVIDER, 'odd-price', 1_000_001, 0), 2 + 7)
        self.assertEqual(usd_to_nusd('3.002937546'), 3_002_937_546)

    # --- reservas e tetos ---------------------------------------------
    def test_reserva_reduz_saldo_disponivel(self):
        before = self.ledger.available_nusd()
        result = self.ledger.reserve(**reserve_args())
        self.assertEqual(result['reserved_nusd'], 1300)
        self.assertEqual(self.ledger.available_nusd(), before - 1300)

    def test_teto_do_bloco_bloqueia_antes_do_teto_global(self):
        self.ledger.set_block_cap('b1', 2000)
        self.ledger.reserve(**reserve_args())
        with self.assertRaises(BudgetError) as ctx:
            self.ledger.reserve(**reserve_args())
        self.assertIn('Teto do bloco', str(ctx.exception))
        self.assertEqual(self.ledger.committed_nusd(), 1300)

    def test_bloco_sem_teto_registrado_nao_despacha(self):
        with self.assertRaises(BudgetError):
            self.ledger.reserve(**reserve_args(block_id='desconhecido'))

    def test_teto_global_considera_gasto_historico(self):
        self.ledger.record_historical_commitment(usd_to_nusd('0.9999999'), {'fonte': 'dossie'})
        self.ledger.set_block_cap('b1', usd_to_nusd('1.00'))
        with self.assertRaises(BudgetError) as ctx:
            self.ledger.reserve(**reserve_args())
        self.assertIn('Teto global', str(ctx.exception))

    # --- liquidacao ----------------------------------------------------
    def test_usage_valido_liquida_pelo_custo_observado(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.mark_sent(attempt)
        result = self.ledger.settle(attempt, usage={'input_tokens': 500, 'output_tokens': 10})
        self.assertEqual(result['cost_source'], 'usage_priced')
        self.assertEqual(result['settled_nusd'], 530)
        self.assertEqual(self.ledger.committed_nusd(), 530)

    def test_resposta_sem_usage_mantem_o_pior_caso(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.mark_sent(attempt)
        result = self.ledger.settle(attempt, usage={'texto': 'ok'})
        self.assertEqual(result['cost_source'], 'worst_case_no_usage')
        self.assertEqual(result['settled_nusd'], 1300)
        row = self.ledger.db.execute('SELECT known_cost_nusd FROM attempts WHERE attempt_id = ?', (attempt,)).fetchone()
        self.assertIsNone(row['known_cost_nusd'])

    def test_usage_parcial_nao_vira_custo_barato(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        result = self.ledger.settle(attempt, usage={'input_tokens': 500})
        self.assertEqual(result['cost_source'], 'worst_case_no_usage')
        self.assertEqual(result['settled_nusd'], 1300)

    def test_custo_do_provedor_acima_da_reserva_e_registrado(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        result = self.ledger.settle(attempt, provider_reported_cost_nusd=5000)
        self.assertEqual(result['settled_nusd'], 5000)
        event = self.ledger.db.execute(
            "SELECT evidence_json FROM budget_events WHERE attempt_id = ? AND event_type = 'settle'", (attempt,)
        ).fetchone()
        self.assertIn('overrun_nusd', event['evidence_json'])

    def test_estouro_no_settle_pausa_o_experimento(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.settle(attempt, provider_reported_cost_nusd=usd_to_nusd('2.00'))
        status = self.ledger.db.execute('SELECT status FROM experiments WHERE experiment_id = ?', ('exp-test',)).fetchone()
        self.assertEqual(status['status'], 'paused')

    def test_liquidacao_dupla_e_recusada(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.settle(attempt, usage={'input_tokens': 1, 'output_tokens': 1})
        with self.assertRaises(LedgerStateError):
            self.ledger.settle(attempt, usage={'input_tokens': 1, 'output_tokens': 1})

    # --- timeout e retry ------------------------------------------------
    def test_timeout_conserva_a_reserva(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.mark_sent(attempt)
        self.ledger.mark_timeout(attempt)
        self.assertEqual(self.ledger.committed_nusd(), 1300)
        self.assertEqual([a['attempt_id'] for a in self.ledger.open_attempts()], [attempt])

    def test_retry_tem_reserva_propria_e_pai_declarado(self):
        parent = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.mark_timeout(parent)
        child = self.ledger.retry_of(parent, provider=PROVIDER, model=MODEL, max_input_tokens=1000,
                                     max_output_tokens=100, payload_sha256='1' * 64,
                                     request_path='requests/y.jsonl', runtime_manifest_path='manifests/y.json')
        self.assertEqual(self.ledger.committed_nusd(), 2600)
        row = self.ledger.db.execute('SELECT parent_attempt_id FROM attempts WHERE attempt_id = ?',
                                     (child['attempt_id'],)).fetchone()
        self.assertEqual(row['parent_attempt_id'], parent)

    def test_liberacao_so_com_evidencia_de_nao_envio(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        with self.assertRaises(LedgerStateError):
            self.ledger.cancel_before_send(attempt, evidence=None)
        self.ledger.cancel_before_send(attempt, evidence={'motivo': 'validacao de payload falhou antes do envio'})
        self.assertEqual(self.ledger.committed_nusd(), 0)

    def test_nao_libera_reserva_de_tentativa_ja_enviada(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.mark_sent(attempt)
        with self.assertRaises(LedgerStateError):
            self.ledger.cancel_before_send(attempt, evidence={'motivo': 'tentativa tardia'})
        self.assertEqual(self.ledger.committed_nusd(), 1300)

    # --- concorrencia e reinicio -----------------------------------------
    def test_concorrencia_nao_ultrapassa_o_teto(self):
        self.ledger.set_block_cap('b1', 13_000)  # exatamente 10 reservas de 1300
        granted, denied = [], []
        lock = threading.Lock()

        def worker():
            ledger = self.open_ledger()
            try:
                result = ledger.reserve(**reserve_args())
            except (BudgetError, sqlite3.OperationalError) as exc:
                with lock:
                    denied.append(str(exc))
            else:
                with lock:
                    granted.append(result['attempt_id'])
            finally:
                ledger.close()

        threads = [threading.Thread(target=worker) for _ in range(24)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(granted), 10)
        self.assertEqual(len(denied), 14)
        self.assertEqual(self.ledger.committed_nusd(), 13_000)
        self.assertLessEqual(self.ledger.committed_nusd(), self.ledger.cap_nusd())

    def test_reinicio_preserva_reservas_pendentes(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.mark_sent(attempt)
        self.ledger.close()  # simula queda do processo apos o envio

        recovered = self.open_ledger()
        try:
            self.assertEqual(recovered.committed_nusd(), 1300)
            pending = recovered.open_attempts()
            self.assertEqual([(a['attempt_id'], a['status']) for a in pending], [(attempt, 'sent')])
        finally:
            recovered.close()
        self.ledger = self.open_ledger()

    def test_reserva_falha_nao_deixa_tentativa_orfa(self):
        self.ledger.set_block_cap('b1', 1000)
        with self.assertRaises(BudgetError):
            self.ledger.reserve(**reserve_args())
        count = self.ledger.db.execute('SELECT COUNT(*) AS n FROM attempts').fetchone()['n']
        self.assertEqual(count, 0)

    # --- conciliacao -------------------------------------------------------
    def test_conciliacao_usa_delta_e_nao_soma_duas_vezes(self):
        attempt = self.ledger.reserve(**reserve_args())['attempt_id']
        self.ledger.settle(attempt, usage={'input_tokens': 500, 'output_tokens': 10})
        first = self.ledger.reconcile(PROVIDER, 530, {'usage': '0.00000053'})
        self.assertEqual(first['delta_nusd'], 530)
        second = self.ledger.reconcile(PROVIDER, 530, {'usage': '0.00000053'})
        self.assertEqual(second['delta_nusd'], 0)
        self.assertEqual(second['ledger_committed_nusd'], 530)

    def test_snapshot_do_provedor_nao_guarda_credencial(self):
        self.ledger.reconcile(PROVIDER, 100, {'label': 'chave-teste', 'limit': 50}, key_limit_nusd=usd_to_nusd('50'))
        row = self.ledger.db.execute('SELECT sanitized_json FROM provider_snapshots').fetchone()
        self.assertNotIn('sk-', row['sanitized_json'])


if __name__ == '__main__':
    unittest.main()


class RealPriceTableTests(unittest.TestCase):
    """A tabela versionada precisa bater com o preco bruto registrado na fonte."""

    def setUp(self):
        from executor.pricing import load_prices
        self.prices = load_prices()

    def test_tabela_real_carrega_e_confere_com_a_fonte(self):
        for key, entry in self.prices['models'].items():
            provider, model = key.split(':', 1)
            raw_prompt = entry['raw_pricing']['prompt']
            expected = usd_to_nusd(raw_prompt) * 1_000_000
            self.assertEqual(entry['input_nusd_per_million_tokens'], expected)
            self.assertTrue(entry.get('source', '').startswith('https://'))
            # Pior caso de uma chamada com contexto cheio precisa caber no teto de bloco previsto.
            worst = worst_case_nusd(self.prices, provider, model, entry['context_length'], 1)
            self.assertLess(worst, usd_to_nusd('0.25'))
