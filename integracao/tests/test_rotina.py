"""A rotina automática para no primeiro passo que falha e só commita quando tudo fechou."""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from camadas import rotina  # noqa: E402


class Rotina(unittest.TestCase):

    def setUp(self):
        self.ultima = rotina.ESTADO / '_teste_rotina-ultima.json'
        self.log = rotina.ESTADO / '_teste_rotina.log'
        self.patches = [mock.patch.object(rotina, 'ULTIMA', self.ultima),
                        mock.patch.object(rotina, 'LOG', self.log)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.ultima.unlink(missing_ok=True)
        self.log.unlink(missing_ok=True)

    def test_para_na_auditoria_e_nao_commita(self):
        def falso(nome, comando, tempo=300):
            return (nome != 'auditoria'), f'{nome} rodou'
        with mock.patch.object(rotina, '_rodar', side_effect=falso), \
                mock.patch.object(rotina, '_commit') as commit:
            r = rotina.executar()
        self.assertFalse(r['ok'])
        self.assertEqual(r['parou_em'], 'auditoria')
        commit.assert_not_called()
        self.assertEqual(json.loads(self.ultima.read_text(encoding='utf-8'))['parou_em'], 'auditoria')

    def test_completa_commita_e_so_medir_nao(self):
        with mock.patch.object(rotina, '_rodar', return_value=(True, 'ok')), \
                mock.patch.object(rotina, '_commit', return_value=True) as commit:
            completa = rotina.executar()
            so_medir = rotina.executar(so_medir=True)
        self.assertTrue(completa['commit'])
        self.assertEqual(len(completa['passos']), len(rotina.PASSOS_COMPLETOS))
        self.assertEqual([p['passo'] for p in so_medir['passos']], ['medir'])
        self.assertFalse(so_medir['commit'])
        self.assertEqual(commit.call_count, 1)

    def test_o_commit_nunca_faz_push(self):
        fonte = (RAIZ / 'camadas' / 'rotina.py').read_text(encoding='utf-8')
        self.assertNotIn("'push'", fonte)
        self.assertIn('Nunca faz push', fonte)


if __name__ == '__main__':
    unittest.main()
