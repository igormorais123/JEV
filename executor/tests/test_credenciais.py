"""As chaves do Jev são achadas na ordem certa, o provedor preferido é o declarado, e nenhum
valor de chave vaza em erro, log ou diagnóstico."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from executor import credenciais  # noqa: E402

FALSA_TS = 'ts-chave-de-teste-0000000000000000'
FALSA_OR = 'or-chave-de-teste-0000000000000000'


class Credenciais(unittest.TestCase):

    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.env = Path(self.pasta.name) / '.env'
        self.cofre = Path(self.pasta.name) / 'jev.env'
        self.arquivos = (self.env, self.cofre)
        self.limpo = mock.patch.dict(os.environ, {}, clear=False)
        self.limpo.start()
        for nome in ('TYPESAFE_API_KEY', 'OPENROUTER_API_KEY', 'JEV_PROVEDOR'):
            os.environ.pop(nome, None)

    def tearDown(self):
        self.limpo.stop()
        self.pasta.cleanup()

    def test_ordem_ambiente_projeto_cofre(self):
        self.cofre.write_text(f'TYPESAFE_API_KEY={FALSA_TS}\n', encoding='utf-8')
        self.assertEqual(credenciais.valor('TYPESAFE_API_KEY', self.arquivos), (FALSA_TS, 'jev.env'))
        self.env.write_text('TYPESAFE_API_KEY=do-projeto-000000000000000000\n', encoding='utf-8')
        self.assertEqual(credenciais.valor('TYPESAFE_API_KEY', self.arquivos)[1], '.env')
        os.environ['TYPESAFE_API_KEY'] = 'do-ambiente-00000000000000000000'
        self.assertEqual(credenciais.valor('TYPESAFE_API_KEY', self.arquivos)[1], 'ambiente')

    def test_provedor_preferido_e_o_declarado_com_chave(self):
        self.cofre.write_text(f'JEV_PROVEDOR=typesafe\nTYPESAFE_API_KEY={FALSA_TS}\n'
                              f'OPENROUTER_API_KEY={FALSA_OR}\n', encoding='utf-8')
        self.assertEqual(credenciais.provedor(self.arquivos), 'typesafe')
        self.cofre.write_text(f'JEV_PROVEDOR=typesafe\nOPENROUTER_API_KEY={FALSA_OR}\n', encoding='utf-8')
        self.assertEqual(credenciais.provedor(self.arquivos), 'openrouter',
                         'preferência sem chave cai para quem tem chave')
        self.cofre.write_text(f'TYPESAFE_API_KEY={FALSA_TS}\nOPENROUTER_API_KEY={FALSA_OR}\n', encoding='utf-8')
        self.assertEqual(credenciais.provedor(self.arquivos), 'typesafe', 'sem preferência, typesafe primeiro')

    def test_erro_e_diagnostico_nunca_carregam_o_valor(self):
        self.cofre.write_text(f'TYPESAFE_API_KEY={FALSA_TS}\n', encoding='utf-8')
        with self.assertRaises(RuntimeError) as ctx:
            credenciais.chave('openrouter', self.arquivos)
        self.assertNotIn(FALSA_TS, str(ctx.exception))
        situacao = str(credenciais.situacao(self.arquivos))
        self.assertNotIn(FALSA_TS, situacao)
        self.assertIn('jev.env', situacao)

    def test_o_cofre_real_existe_e_nao_esta_em_repositorio(self):
        self.assertTrue(credenciais.COFRE.exists(), 'o cofre ~/.secrets/jev.env precisa existir nesta máquina')
        self.assertNotIn('.claude', str(credenciais.COFRE))
        self.assertEqual(credenciais.provedor(), 'typesafe')

    def test_url_por_provedor(self):
        from executor.runner import url_for
        self.assertTrue(url_for('typesafe').startswith('https://api.typesafe.ai/'))
        self.assertTrue(url_for('openrouter').startswith('https://openrouter.ai/'))
        self.assertTrue(url_for('desconhecido').startswith('https://openrouter.ai/'))


if __name__ == '__main__':
    unittest.main()
