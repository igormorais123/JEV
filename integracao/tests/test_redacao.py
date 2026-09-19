"""Nenhuma credencial pode atravessar a fronteira desta máquina dentro de um pedido.

O teste mais duro é o último: ele pega as chaves que de fato existem no `settings.json` desta
máquina, monta um pedido como o Igor escreveria, e exige que nenhuma delas sobreviva à redação.
Nada é impresso: o que se afirma é ausência.
"""
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from jev_router import redacao  # noqa: E402

SETTINGS = Path.home() / '.claude' / 'settings.json'


class Formas(unittest.TestCase):

    def test_mascara_os_prefixos_conhecidos(self):
        amostras = ['sk-proj-abcdefghijklmnop1234567890', 'ghp_abcdefghijklmnopqrstuvwxyz012345',
                    'AIzaSyB0123456789abcdefghijklmnopqrs', 'pplx-0123456789abcdefghij',
                    'apify_api_0123456789abcdefghij']
        for amostra in amostras:
            with self.subTest(amostra=amostra[:6]):
                limpo, n = redacao.limpar(f'usa esta chave {amostra} no script')
                self.assertNotIn(amostra, limpo)
                self.assertGreaterEqual(n, 1)

    def test_mascara_atribuicao_em_env(self):
        limpo, n = redacao.limpar('OPENROUTER_API_KEY=abcdef1234567890xyz')
        self.assertNotIn('abcdef1234567890xyz', limpo)
        self.assertIn('[segredo]', limpo)

    def test_mascara_credencial_em_url(self):
        limpo, _ = redacao.limpar('clona de https://usuario:senhaforte@github.com/x/y.git')
        self.assertNotIn('senhaforte', limpo)

    def test_texto_comum_passa_intacto(self):
        pedido = ('Corrija o teste de calibração em executor/tests/test_calibracao_e12.py, '
                  'que está com o regex errado na linha 64.')
        limpo, n = redacao.limpar(pedido)
        self.assertEqual(limpo, pedido)
        self.assertEqual(n, 0)


@unittest.skipUnless(SETTINGS.exists(), 'sem settings.json nesta máquina')
class ContraAsChavesQueExistemAqui(unittest.TestCase):

    def segredos(self):
        """Os valores que são de fato credencial.

        Nem tudo que se chama `..._KEY` guarda uma: `INTEIA_SECRETS_FILE` e
        `GOOGLE_SERVICE_ACCOUNT_KEY` guardam o caminho do arquivo onde a credencial está. Um
        caminho não é segredo e mascará-lo só tiraria contexto útil do classificador.
        """
        ambiente = json.loads(SETTINGS.read_text(encoding='utf-8')).get('env', {})
        return [v for k, v in ambiente.items()
                if isinstance(v, str) and len(v) >= 20
                and any(p in k.upper() for p in ('KEY', 'TOKEN', 'SECRET'))
                and not any(marca in v for marca in (':\\', '://', '@', ' '))]

    def test_nenhuma_chave_real_sobrevive_a_redacao(self):
        segredos = self.segredos()
        self.assertGreater(len(segredos), 3, 'o teste só vale se houver chaves para testar')
        for segredo in segredos:
            pedido = f'roda o script passando a credencial {segredo} e me diz o que volta'
            limpo, _ = redacao.limpar(pedido)
            # A asserção é sobre ausência; o valor nunca é impresso nem na falha.
            self.assertNotIn(segredo, limpo,
                             'uma credencial desta máquina sobreviveu à redação')


if __name__ == '__main__':
    unittest.main()
