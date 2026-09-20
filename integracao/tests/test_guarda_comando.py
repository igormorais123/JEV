"""O guarda de comando: o que ele pode fazer, e sobretudo o que ele não pode.

Todos os testes são offline. O transporte é injetado, e o único teste que toca disco escreve no
diretório de testes.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / 'hooks'))

import jev_guarda_comando as guarda  # noqa: E402


def resposta(efeito, confianca):
    def transporte(url, cabecalhos, dados, timeout):
        return 200, {'answers': {'efeito': {'type': 'choice', 'choice': efeito,
                                            'confidence': confianca}},
                     'usage': {'cost': 0.00002}}
    return transporte


def quebrado(status=500):
    def transporte(url, cabecalhos, dados, timeout):
        return status, {}
    return transporte


class SoOlhaOQueARegraBarrou(unittest.TestCase):
    """A segunda camada não pode virar primeira camada por acidente.

    Se este teste cair, o hook passa a opinar sobre comando que ninguém barrou, e um 'allow' dele
    deixaria de ser "não precisa confirmar" para virar "pode executar" -- que é exatamente o
    desenho que a R16 mediu como inseguro.
    """

    def test_comando_que_a_regra_nao_marca_nao_gasta_chamada(self):
        def nunca(*a, **k):
            raise AssertionError('chamou a rede para comando que a regra não barrou')
        libera, detalhe = guarda.avaliar('git status --short', transporte=nunca)
        self.assertIsNone(libera)
        self.assertIn('nao barrou', detalhe['motivo'])

    def test_comando_marcado_pela_regra_e_avaliado(self):
        libera, detalhe = guarda.avaliar('npm test && git push origin main',
                                         transporte=resposta('apenas-le', 0.99))
        self.assertTrue(libera)
        self.assertEqual(detalhe['efeito'], 'apenas-le')


class NuncaLiberaOQueEGrave(unittest.TestCase):

    def test_efeito_grave_nao_libera_nem_com_confianca_maxima(self):
        for efeito in ('sai-da-maquina', 'apaga-sem-volta'):
            with self.subTest(efeito=efeito):
                libera, _ = guarda.avaliar('rm -rf build && deploy',
                                           transporte=resposta(efeito, 1.0))
                self.assertFalse(libera)

    def test_abaixo_do_corte_nao_libera(self):
        libera, detalhe = guarda.avaliar('git push origin main',
                                         transporte=resposta('apenas-le', guarda.CORTE - 0.01))
        self.assertFalse(libera)
        self.assertIn('abaixo do corte', detalhe['motivo'])

    def test_falha_de_rede_nao_libera(self):
        libera, _ = guarda.avaliar('git push origin main', transporte=quebrado())
        self.assertFalse(libera)

    def test_resposta_fora_do_contrato_nao_libera(self):
        def fora(url, cabecalhos, dados, timeout):
            return 200, {'answers': {'outra': {'choice': 'apenas-le'}}}
        self.assertFalse(guarda.avaliar('git push origin main', transporte=fora)[0])


class Hook(unittest.TestCase):

    def setUp(self):
        self.registro = RAIZ / 'tests' / '.guarda-teste.jsonl'
        patch = mock.patch.object(guarda, 'REGISTRO', self.registro)
        patch.start()
        self.addCleanup(patch.stop)
        self.addCleanup(lambda: self.registro.unlink(missing_ok=True))

    def rodar(self, evento, modo='ativo', **kwargs):
        with mock.patch.object(sys, 'stdin', mock.MagicMock()), \
             mock.patch.object(guarda.json, 'load', return_value=evento), \
             mock.patch.dict('os.environ', {'JEV_GUARDA_MODO': modo}), \
             mock.patch.object(guarda, 'avaliar', **kwargs) as avaliar:
            saida = mock.MagicMock()
            with mock.patch.object(sys, 'stdout', saida):
                codigo = guarda.main()
            escrito = b''.join(c.args[0] for c in saida.buffer.write.call_args_list)
        return codigo, escrito, avaliar

    def test_ferramenta_de_outro_tipo_e_ignorada(self):
        codigo, escrito, avaliar = self.rodar(
            {'tool_name': 'Read', 'tool_input': {'file_path': 'x'}},
            return_value=(True, {'efeito': 'apenas-le', 'confianca': 1.0}))
        self.assertEqual(codigo, 0)
        self.assertEqual(escrito, b'')
        avaliar.assert_not_called()

    def test_em_sombra_nao_escreve_nada_na_saida(self):
        codigo, escrito, _ = self.rodar(
            {'tool_name': 'Bash', 'tool_input': {'command': 'git push origin main'}},
            modo='sombra',
            return_value=(True, {'efeito': 'apenas-le', 'confianca': 0.99, 'motivo': 'ok'}))
        self.assertEqual(codigo, 0)
        self.assertEqual(escrito, b'')
        self.assertIn('"modo": "sombra"', self.registro.read_text(encoding='utf-8'))

    def test_em_ativo_a_liberacao_sai_em_utf8_com_acento_intacto(self):
        codigo, escrito, _ = self.rodar(
            {'tool_name': 'Bash', 'tool_input': {'command': 'git push origin main'}},
            return_value=(True, {'efeito': 'apenas-le', 'confianca': 0.99, 'motivo': 'ok'}))
        self.assertEqual(codigo, 0)
        bloco = json.loads(escrito.decode('utf-8'))['hookSpecificOutput']
        self.assertEqual(bloco['permissionDecision'], 'allow')
        self.assertIn('confiança', bloco['permissionDecisionReason'])

    def test_excecao_no_meio_nao_derruba_a_sessao(self):
        codigo, escrito, _ = self.rodar(
            {'tool_name': 'Bash', 'tool_input': {'command': 'git push origin main'}},
            side_effect=RuntimeError('boom'))
        self.assertEqual(codigo, 0)
        self.assertEqual(escrito, b'')

    def test_nao_libera_nunca_devolve_allow(self):
        codigo, escrito, _ = self.rodar(
            {'tool_name': 'Bash', 'tool_input': {'command': 'rm -rf /'}},
            return_value=(False, {'efeito': 'apaga-sem-volta', 'confianca': 1.0,
                                  'motivo': 'grave'}))
        self.assertEqual(escrito, b'')

    def test_o_comando_nao_vai_para_o_registro_em_claro(self):
        self.rodar({'tool_name': 'Bash',
                    'tool_input': {'command': 'git push https://user:segredo@host/repo'}},
                   return_value=(True, {'efeito': 'apenas-le', 'confianca': 0.99, 'motivo': 'ok'}))
        self.assertNotIn('segredo', self.registro.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
