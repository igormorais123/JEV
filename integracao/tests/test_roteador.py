"""O classificador tem de falhar para o lado aberto e calar quando não tem confiança.

Todo este arquivo roda offline, com transporte falso: o caminho inteiro do hook é exercitado
sem rede e sem custo, como no resto do estudo.

A versão anterior deste arquivo testava uma política de roteamento de esforço que a medição em
material real derrubou (cobertura útil de 0%). Os testes dela saíram junto com ela: teste que
protege código morto dá falsa sensação de cobertura.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from jev_router import politica, roteador  # noqa: E402


def resposta(tema, confianca, risco='seguro', custo=0.00001):
    def transporte(url, cabecalhos, corpo, timeout):
        return 200, {'answers': {
            'tema': {'type': 'choice', 'choice': tema, 'confidence': confianca},
            'risco': {'type': 'choice', 'choice': risco, 'confidence': 0.9}},
            'usage': {'cost': custo}}
    return transporte


def quebrado(status=500, corpo=None):
    def transporte(url, cabecalhos, corpo_enviado, timeout):
        return status, corpo or {}
    return transporte


class PoliticaDeSugestao(unittest.TestCase):

    def test_so_sugere_acima_do_corte(self):
        abaixo = politica.decidir({'tema': {'choice': 'juridico', 'confidence': 0.85},
                                   'risco': {'choice': 'seguro'}})
        self.assertFalse(abaixo['sugere'])
        self.assertIn('abaixo do corte', abaixo['motivo'])

        acima = politica.decidir({'tema': {'choice': 'juridico', 'confidence': 0.95},
                                  'risco': {'choice': 'seguro'}})
        self.assertTrue(acima['sugere'])
        self.assertIn('/ash', acima['skills'])

    def test_sem_tema_nao_sugere_nada(self):
        """Em 37 dos 60 pedidos reais não havia tema: o silêncio é o caso comum."""
        d = politica.decidir({'tema': {'choice': 'nenhum', 'confidence': 1.0},
                              'risco': {'choice': 'seguro'}})
        self.assertFalse(d['sugere'])
        self.assertEqual(politica.texto_para_o_agente(d, 'ativo'), '')

    def test_risco_irreversivel_avisa_mas_nao_decide(self):
        d = politica.decidir({'tema': {'choice': 'nenhum', 'confidence': 1.0},
                              'risco': {'choice': 'irreversivel'}})
        self.assertIn('não se desfaz', d['aviso'])
        self.assertIn('Confirme o alvo', politica.texto_para_o_agente(d, 'ativo'))

    def test_tema_fora_do_contrato_nao_vira_sugestao(self):
        d = politica.decidir({'tema': {'choice': 'inventado', 'confidence': 1.0}, 'risco': {}})
        self.assertFalse(d['sugere'])

    def test_o_corte_publicado_e_o_que_o_dado_sustenta(self):
        """Se alguém mudar o corte, tem de mudar a medição junto."""
        resultado = RAIZ / 'avaliacao' / 'skills-resultado.json'
        if not resultado.exists():
            self.skipTest('a avaliação ainda não rodou')
        gabarito = json.loads((RAIZ / 'avaliacao' / 'gabarito-skills.json')
                              .read_text(encoding='utf-8'))['gabarito']
        linhas = json.loads(resultado.read_text(encoding='utf-8'))['linhas']
        falsos = [l['id'] for l in linhas
                  if l['jev'] not in (None, 'nenhum')
                  and (l['confianca'] or 0) >= politica.CORTE_DO_TEMA
                  and gabarito[l['id']]['tema'] == 'nenhum']
        self.assertEqual(falsos, [],
                         'no corte publicado o Jev não pode sugerir skill onde não há tema')


class FalhaParaOLadoAberto(unittest.TestCase):

    def setUp(self):
        self.tmp = mock.patch.object(roteador, 'DECISOES', RAIZ / 'tests' / '.decisoes-teste.jsonl')
        self.tmp.start()
        self.addCleanup(self.tmp.stop)
        self.addCleanup(lambda: (RAIZ / 'tests' / '.decisoes-teste.jsonl').unlink(missing_ok=True))
        self.pedidos = RAIZ / 'tests' / '.pedidos-teste.jsonl'
        self.tmp2 = mock.patch.object(roteador, 'PEDIDOS', self.pedidos)
        self.tmp2.start()
        self.addCleanup(self.tmp2.stop)
        self.addCleanup(lambda: self.pedidos.unlink(missing_ok=True))

    def test_pedido_curto_nao_gasta_chamada(self):
        def nunca(*a, **k):
            raise AssertionError('não podia ter chamado a rede')
        self.assertIsNone(roteador.classificar('ok', transporte=nunca, usar_cache=False))

    def test_erro_http_devolve_none(self):
        with mock.patch.object(roteador.cliente, 'chave', return_value='x'):
            self.assertIsNone(roteador.classificar(
                'Preciso entender por que o teste de calibração falhou no corpus novo',
                transporte=quebrado(), usar_cache=False))

    def test_sem_chave_devolve_none_sem_enviar(self):
        with mock.patch.object(roteador.cliente, 'chave', return_value=None):
            def nunca(*a, **k):
                raise AssertionError('enviou sem chave')
            self.assertIsNone(roteador.classificar(
                'Preciso entender por que o teste de calibração falhou', transporte=nunca,
                usar_cache=False))

    def test_teto_estourado_impede_o_envio(self):
        with mock.patch.object(roteador.cliente.orcamento, 'pode_gastar',
                               return_value=(False, 'teto')):
            def nunca(*a, **k):
                raise AssertionError('enviou fora do teto')
            self.assertIsNone(roteador.classificar(
                'Preciso entender por que o teste de calibração falhou', transporte=nunca,
                usar_cache=False))

    def test_decisao_e_registrada(self):
        with mock.patch.object(roteador.cliente, 'chave', return_value='x'), \
             mock.patch.object(roteador.cliente.orcamento, 'registrar', return_value=None):
            d = roteador.classificar('Redija a contestação do processo da vara de família',
                                     transporte=resposta('juridico', 0.97), usar_cache=False)
        self.assertTrue(d['sugere'])
        linhas = (RAIZ / 'tests' / '.decisoes-teste.jsonl').read_text(encoding='utf-8').splitlines()
        self.assertEqual(json.loads(linhas[-1])['tema'], 'juridico')

    def test_o_pedido_fica_recuperavel_e_redigido(self):
        """Sem isto, auditar a decisão depois é impossível.

        As 28 primeiras decisões de produção guardaram só o SHA-256 do pedido. Ao tentar medir
        se elas foram certas, o recasamento do hash contra o transcript recuperou 1 caso de 28:
        o registro existia, mas não sustentava nenhuma conclusão. Agora o texto fica em
        `estado/pedidos.jsonl`, que o .gitignore exclui -- e passa pela mesma redação que
        protege qualquer envio, porque um arquivo local também vaza em backup.
        """
        pedido = ('Redija a contestação do processo da vara de família; a chave é '
                  'sk-proj-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        with mock.patch.object(roteador.cliente, 'chave', return_value='x'),              mock.patch.object(roteador.cliente.orcamento, 'registrar', return_value=None):
            decisao = roteador.classificar(pedido, transporte=resposta('juridico', 0.97),
                                           usar_cache=False)
        guardado = json.loads(self.pedidos.read_text(encoding='utf-8').splitlines()[-1])
        self.assertEqual(guardado['pedido_sha256'], decisao['pedido_sha256'])
        self.assertIn('vara de família', guardado['pedido'])
        self.assertNotIn('sk-proj-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', guardado['pedido'])

    def test_guardar_o_pedido_nunca_derruba_a_decisao(self):
        with mock.patch.object(roteador, 'PEDIDOS', Path('/caminho/que/nao/existe/x.jsonl')),              mock.patch.object(roteador.cliente, 'chave', return_value='x'),              mock.patch.object(roteador.cliente.orcamento, 'registrar', return_value=None):
            decisao = roteador.classificar('Redija a contestação do processo da vara de família',
                                           transporte=resposta('juridico', 0.97),
                                           usar_cache=False)
        self.assertTrue(decisao['sugere'])


class Hook(unittest.TestCase):
    """O hook precisa sair em silêncio e com código 0 quando não tem o que dizer."""

    def rodar(self, entrada, ambiente=None):
        import os
        import subprocess
        env = dict(os.environ)
        env.update(ambiente or {})
        return subprocess.run([sys.executable, str(RAIZ / 'hooks' / 'jev_prompt_router.py')],
                              input=json.dumps(entrada), capture_output=True, text=True, env=env)

    def test_entrada_invalida_sai_limpo(self):
        import subprocess
        r = subprocess.run([sys.executable, str(RAIZ / 'hooks' / 'jev_prompt_router.py')],
                           input='isto não é json', capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), '')

    def test_pedido_curto_sai_limpo_sem_rede(self):
        r = self.rodar({'prompt': 'ok', 'cwd': '.', 'session_id': 's1'})
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), '')

    def test_em_sombra_nao_injeta_contexto(self):
        r = self.rodar({'prompt': 'ok', 'session_id': 's1'}, {'JEV_ROUTER_MODO': 'sombra'})
        self.assertEqual(r.stdout.strip(), '')

    def test_a_nota_sai_em_utf8_com_acento_intacto(self):
        """O console do Windows entrega cp1252 e corrompia o acento no caminho até o modelo.

        O teste roda o hook de verdade, sem rede: a resposta é semeada no cache pela mesma
        impressão que o roteador calcula.
        """
        import os
        import subprocess
        pedido = 'Redija a contestação do processo da vara de família com os prazos'
        estado = ('Diretório de trabalho: C:/x' + '\n\n'
                  + 'Pedido do usuário:' + '\n' + pedido)
        marca = roteador.impressao(estado)
        roteador.para_o_cache(marca, {
            'tema': {'type': 'choice', 'choice': 'juridico', 'confidence': 1.0},
            'risco': {'type': 'choice', 'choice': 'seguro', 'confidence': 1.0}})
        self.addCleanup(lambda: (roteador.CACHE / f'{marca}.json').unlink(missing_ok=True))

        env = dict(os.environ)
        env.pop('PYTHONIOENCODING', None)
        env['JEV_ROUTER_MODO'] = 'ativo'
        r = subprocess.run([sys.executable, str(RAIZ / 'hooks' / 'jev_prompt_router.py')],
                           input=json.dumps({'prompt': pedido, 'cwd': 'C:/x',
                                             'session_id': 'enc'}).encode('utf-8'),
                           capture_output=True, env=env)
        # Decodificado como UTF-8 puro: se o hook escrevesse pelo console, isto quebraria.
        nota = json.loads(r.stdout.decode('utf-8'))['hookSpecificOutput']['additionalContext']
        self.assertIn('confiança', nota)
        self.assertIn('jurisprudência', nota)


if __name__ == '__main__':
    unittest.main()
