"""Testes do despacho com transporte simulado. Nenhuma chamada de rede e nenhum custo."""
import tempfile
import unittest
from pathlib import Path

from executor import runner
from executor.ledger import Ledger
from executor.pricing import usd_to_nusd

PRICES = {
    'schema_version': 1,
    'snapshot_id': 'fixture-prices',
    'models': {
        'openrouter:typesafe/jev-1.13': {
            'input_nusd_per_million_tokens': 42_000_000,
            'output_nusd_per_million_tokens': 0,
            'context_length': 32_000,
        },
    },
}
MODEL = 'typesafe/jev-1.13'
PROVIDER = 'openrouter'
QUESTIONS = [{'id': 'q1', 'question': 'Cobranca ou entrega?', 'options': ['cobranca', 'entrega']}]


def dispatch_args(**overrides):
    args = dict(arm_id='arm-1', block_id='b1', provider=PROVIDER, model=MODEL,
                state='Mensagem de teste.', questions=QUESTIONS,
                request_path='runs/req.jsonl', runtime_manifest_path='runs/manifest.json',
                api_key='chave-de-teste')
    args.update(overrides)
    return args


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.temp.name) / 'ledger.sqlite3', 'exp-runner', prices=PRICES)
        self.ledger.authorize(usd_to_nusd('5.00'))
        self.ledger.set_block_cap('b1', usd_to_nusd('0.25'))
        self.ledger.register_arm('arm-1', 'S01', PROVIDER, MODEL)
        self.sent = []

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def transport(self, status, body):
        def send(url, headers, payload, timeout):
            self.sent.append({'url': url, 'payload': payload, 'headers': headers})
            return status, body
        return send

    def test_sucesso_liquida_pelo_usage(self):
        body = {'id': 'req-1', 'model': 'typesafe/jev-1.13-20260917',
                'decisions': [{'choice': 'cobranca', 'confidence': 0.91}],
                'usage': {'input_tokens': 100, 'output_tokens': 0}}
        result = runner.dispatch(self.ledger, transport=self.transport(200, body), **dispatch_args())
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['cost_source'], 'usage_priced')
        # 100 tokens a 42.000.000 nusd por milhao = 4.200 nusd (US$ 0,0000042).
        self.assertEqual(result['settled_nusd'], 4_200)
        self.assertEqual(self.sent[0]['url'], runner.DECISIONS_URL)
        self.assertEqual(self.sent[0]['payload']['model'], MODEL)

    def test_escolha_fora_das_opcoes_e_resposta_invalida(self):
        body = {'decisions': [{'choice': 'outra-coisa'}], 'usage': {'input_tokens': 50, 'output_tokens': 0}}
        result = runner.dispatch(self.ledger, transport=self.transport(200, body), **dispatch_args())
        self.assertEqual(result['status'], 'invalid_response')
        row = self.ledger.db.execute('SELECT status FROM attempts WHERE attempt_id = ?',
                                     (result['attempt_id'],)).fetchone()
        self.assertEqual(row['status'], 'invalid_response')

    def test_quantidade_de_decisoes_diferente_reprova(self):
        body = {'decisions': [], 'usage': {'input_tokens': 10, 'output_tokens': 0}}
        result = runner.dispatch(self.ledger, transport=self.transport(200, body), **dispatch_args())
        self.assertEqual(result['status'], 'invalid_response')

    def test_erro_http_liquida_e_registra(self):
        result = runner.dispatch(self.ledger, transport=self.transport(429, {'error': 'rate limited'}),
                                 **dispatch_args())
        self.assertEqual(result['status'], 'http_error')
        self.assertEqual(result['http_status'], 429)
        self.assertGreater(result['settled_nusd'], 0)

    def test_timeout_conserva_reserva_e_nao_liquida(self):
        def send(url, headers, payload, timeout):
            raise runner.TransportTimeout('tempo esgotado')
        result = runner.dispatch(self.ledger, transport=send, **dispatch_args())
        self.assertEqual(result['status'], 'timeout')
        self.assertEqual(self.ledger.committed_nusd(), result['reserved_nusd'])
        self.assertEqual(self.ledger.open_attempts()[0]['status'], 'timeout')

    def test_sem_reserva_nao_ha_envio(self):
        self.ledger.set_block_cap('b1', 1)
        from executor.ledger import BudgetError
        with self.assertRaises(BudgetError):
            runner.dispatch(self.ledger, transport=self.transport(200, {}), **dispatch_args())
        self.assertEqual(self.sent, [])

    def test_resposta_sem_usage_fica_no_pior_caso(self):
        body = {'decisions': [{'choice': 'cobranca'}]}
        result = runner.dispatch(self.ledger, transport=self.transport(200, body), **dispatch_args())
        self.assertEqual(result['cost_source'], 'worst_case_no_usage')
        self.assertEqual(result['settled_nusd'], self.ledger.committed_nusd())

    def test_dry_run_nao_reserva_nem_envia(self):
        payload = runner.payload_for(MODEL, 'Mensagem de teste.', QUESTIONS)
        preview = runner.dry_run(self.ledger, PROVIDER, MODEL, payload)
        self.assertTrue(preview['fits'])
        self.assertGreater(preview['worst_case_nusd'], 0)
        self.assertEqual(self.ledger.committed_nusd(), 0)
        self.assertEqual(self.sent, [])

    def test_chave_nao_aparece_no_registro(self):
        body = {'decisions': [{'choice': 'cobranca'}], 'usage': {'input_tokens': 10, 'output_tokens': 0}}
        runner.dispatch(self.ledger, transport=self.transport(200, body), **dispatch_args())
        dump = ' '.join(str(r) for r in self.ledger.db.execute('SELECT * FROM attempts').fetchall())
        dump += ' '.join(str(r) for r in self.ledger.db.execute('SELECT * FROM budget_events').fetchall())
        self.assertNotIn('chave-de-teste', dump)

    def test_canarios_tem_gabarito_e_opcoes_coerentes(self):
        for canary in runner.CANARIES:
            options = canary['questions'][0]['options']
            self.assertIn(canary['expected'], options)


if __name__ == '__main__':
    unittest.main()
