"""Regressão dos achados da revisão independente (Codex gpt-6-astra, 2026-09-19).

Cada teste reproduz um defeito que o revisor apontou. Todos falhavam antes da correção.
"""
import tempfile
import unittest
from pathlib import Path

from executor import runner
from executor.ledger import Ledger, LedgerStateError
from executor.pricing import PricingError, worst_case_nusd
from executor.run_e1_triagem import resumo
from executor.pricing import usd_to_nusd

PRECOS = {
    'schema_version': 1,
    'snapshot_id': 'fixture',
    'models': {
        'openrouter:caro': {'input_nusd_per_million_tokens': 42_000_000,
                            'output_nusd_per_million_tokens': 0,
                            'context_length': 32_000, 'max_completion_tokens': 28_800},
        'openrouter:barato': {'input_nusd_per_million_tokens': 1_000,
                              'output_nusd_per_million_tokens': 0,
                              'context_length': 32_000, 'max_completion_tokens': 28_800},
        'openrouter:sem-teto-de-saida': {'input_nusd_per_million_tokens': 42_000_000,
                                         'output_nusd_per_million_tokens': 1_000_000,
                                         'context_length': 32_000},
    },
}


def reserva(**over):
    args = dict(arm_id='arm-1', block_id='b1', provider='openrouter', model='caro',
                max_input_tokens=1000, max_output_tokens=100, payload_sha256='0' * 64,
                request_path='r.jsonl', runtime_manifest_path='m.json')
    args.update(over)
    return args


class AchadosP1(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = Ledger(Path(self.temp.name) / 'l.sqlite3', 'exp', prices=PRECOS)
        self.ledger.set_wallet_cap(usd_to_nusd('5.00'))
        self.ledger.authorize(usd_to_nusd('5.00'))
        self.ledger.set_block_cap('b1', usd_to_nusd('1.00'))
        self.ledger.register_arm('arm-1', 'S01', 'openrouter', 'barato')

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    # P1-3: reserva e liquidação podem usar modelos diferentes
    def test_liquidacao_recusa_modelo_diferente_do_reservado(self):
        attempt = self.ledger.reserve(**reserva(model='caro'))['attempt_id']
        with self.assertRaises(LedgerStateError) as ctx:
            self.ledger.settle(attempt, model='barato', usage={'input_tokens': 10, 'output_tokens': 0})
        self.assertIn('difere do reservado', str(ctx.exception))

    def test_liquidacao_sem_model_usa_o_reservado_e_nao_o_do_braco(self):
        """O braço está cadastrado como 'barato'; a reserva foi de 'caro'."""
        attempt = self.ledger.reserve(**reserva(model='caro'))['attempt_id']
        saida = self.ledger.settle(attempt, usage={'input_tokens': 1_000_000, 'output_tokens': 0})
        self.assertEqual(saida['settled_nusd'], 42_000_000)  # tarifa do caro, não a do barato

    def test_liquidacao_recusa_provedor_diferente(self):
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        with self.assertRaises(LedgerStateError):
            self.ledger.settle(attempt, provider='outro', usage={'input_tokens': 1, 'output_tokens': 0})

    # P1-2: divergência do extrato não ocupava o teto
    def test_extrato_acima_do_ledger_ocupa_o_teto(self):
        antes = self.ledger.wallet_committed_nusd()
        saida = self.ledger.reconcile('openrouter', antes + 50_000, {'nota': 'extrato maior'})
        self.assertEqual(saida['excedente_absorvido_nusd'], 50_000)
        self.assertEqual(self.ledger.wallet_committed_nusd(), antes + 50_000)

    def test_extrato_abaixo_do_ledger_nao_devolve_saldo(self):
        attempt = self.ledger.reserve(**reserva())['attempt_id']
        self.ledger.settle(attempt, usage={'input_tokens': 100, 'output_tokens': 0})
        antes = self.ledger.wallet_committed_nusd()
        self.ledger.reconcile('openrouter', 1, {'nota': 'extrato atrasado'})
        self.assertEqual(self.ledger.wallet_committed_nusd(), antes)

    # P1-1: teto declarado sem garantia do endpoint
    def test_dispatch_nao_aceita_teto_declarado_pelo_cliente(self):
        import inspect
        parametros = inspect.signature(runner.dispatch).parameters
        self.assertNotIn('input_token_cap', parametros)
        self.assertNotIn('max_output_tokens', parametros)

    def test_sem_max_completion_tokens_nao_reserva(self):
        with self.assertRaises(PricingError):
            runner.reservation_output_tokens(PRECOS, 'openrouter', 'sem-teto-de-saida')

    # P2-11: taxa por requisição inválida
    def test_taxa_negativa_nao_precifica(self):
        precos = {'schema_version': 1, 'snapshot_id': 'x', 'models': {
            'openrouter:ruim': {'input_nusd_per_million_tokens': 1_000_000,
                                'output_nusd_per_million_tokens': 0,
                                'request_surcharge_nusd': -5000}}}
        with self.assertRaises(PricingError):
            worst_case_nusd(precos, 'openrouter', 'ruim', 10, 1)


class AchadoP1Metricas(unittest.TestCase):
    """P1-4: resposta ausente sumia da acurácia e inflava família perfeita."""

    def casos(self):
        return [
            {'case_id': 'a1', 'family': 'F1', 'kind': 'rotina', 'text': 'x', 'gold': 'cancelar',
             'jev': 'cancelar'},
            {'case_id': 'a2', 'family': 'F1', 'kind': 'rotina', 'text': 'y', 'gold': 'trocar',
             'jev': None},  # timeout, erro HTTP ou resposta inválida
        ]

    def test_ausencia_conta_como_falha_da_familia(self):
        d = resumo('jev', self.casos())
        self.assertEqual(d['casos_programados'], 2)
        self.assertEqual(d['respostas_validas'], 1)
        self.assertEqual(d['cobertura'], 0.5)
        self.assertEqual(d['familias_sem_erro'], 0)
        self.assertEqual(d['sem_resposta'], ['a2'])

    def test_acuracia_condicional_e_sobre_programados_sao_distintas(self):
        d = resumo('jev', self.casos())
        self.assertEqual(d['acuracia'], 1.0)
        self.assertEqual(d['acuracia_sobre_programados'], 0.5)


if __name__ == '__main__':
    unittest.main()
