"""HTTP 429 não custa nada, e o livro-caixa tem de saber disso.

[E12] O executor liquida pelo pior caso quando não há `usage` confiável, e isso é correto: na
dúvida, o teto sofre. Mas uma requisição recusada por limite de taxa nunca chegou a gerar token
nenhum — não há dúvida a sofrer. Durante o E12, 76 chamadas recusadas com 429 entraram no
livro-caixa como US$ 0,499, mais de vinte vezes o gasto real de todo o estudo até ali; o extrato
da chave mostrava US$ 0,0346. Treze rodadas de revisão do controle financeiro não pegaram isso
porque nenhuma execução anterior tinha levado 429.

O que este teste trava:
1. 429 sem usage liquida **zero**, com origem própria e auditável.
2. 5xx e timeout continuam no pior caso — ali a geração pode ter acontecido.
3. Custo reportado pelo provedor continua tendo precedência sobre tudo.
"""
import tempfile
import unittest
from pathlib import Path

from executor.ledger import Ledger
from executor.pricing import usd_to_nusd


class LiquidacaoDeRequisicaoRecusada(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'ledger.sqlite3'
        self.ledger = Ledger(self.db, 'exp-teste-429')
        self.ledger.__enter__()
        self.ledger.set_wallet_cap(usd_to_nusd('5.00'))
        self.ledger.authorize(usd_to_nusd('5.00'), hypothesis='h', metric='m')
        self.ledger.set_block_cap('bloco', usd_to_nusd('1.00'))
        self.ledger.register_arm('arm', 'S01', 'openrouter', 'meta-llama/llama-3.1-8b-instruct',
                                 endpoint='/api/v1/chat/completions')

    def tearDown(self):
        self.ledger.__exit__(None, None, None)
        self.tmp.cleanup()

    def reservar(self):
        reserva = self.ledger.reserve(
            arm_id='arm', block_id='bloco', provider='openrouter',
            model='meta-llama/llama-3.1-8b-instruct', max_input_tokens=1000,
            max_output_tokens=64, payload_sha256='a' * 64, request_path='r.json',
            runtime_manifest_path='r.json', evidence_level='live_component')
        self.ledger.mark_sent(reserva['attempt_id'])
        return reserva

    def test_429_liquida_zero(self):
        reserva = self.reservar()
        saida = self.ledger.settle(reserva['attempt_id'], status='http_error', http_status=429)
        self.assertEqual(saida['settled_nusd'], 0)
        self.assertEqual(saida['cost_source'], 'rejeitado_sem_geracao')

    def test_5xx_e_timeout_continuam_no_pior_caso(self):
        for codigo in (500, 502, None):
            with self.subTest(http_status=codigo):
                reserva = self.reservar()
                saida = self.ledger.settle(reserva['attempt_id'], status='http_error',
                                           http_status=codigo)
                self.assertEqual(saida['settled_nusd'], reserva['reserved_nusd'])
                self.assertEqual(saida['cost_source'], 'worst_case_no_usage')

    def test_custo_reportado_pelo_provedor_tem_precedencia(self):
        reserva = self.reservar()
        saida = self.ledger.settle(reserva['attempt_id'], status='http_error', http_status=429,
                                   provider_reported_cost_nusd=1234)
        self.assertEqual(saida['settled_nusd'], 1234)
        self.assertEqual(saida['cost_source'], 'provider_reported')

    def test_reserva_de_429_nao_segue_comprometida(self):
        reserva = self.reservar()
        self.ledger.settle(reserva['attempt_id'], status='http_error', http_status=429)
        self.assertEqual(self.ledger.wallet_committed_nusd(), 0)


if __name__ == '__main__':
    unittest.main()
