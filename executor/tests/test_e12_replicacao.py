"""O que o E12 promete no pré-registro tem de valer no código, e não só no texto.

Três coisas são travadas aqui:

1. **O corpus é o que o pré-registro diz que é** — 90 casos, 30 famílias novas, três casos por
   família, nenhuma família e nenhum texto repetidos dos corpora anteriores. Um corpus que
   reaproveitasse famílias do piloto ou do desempate mediria de novo o que já foi medido.
2. **A leitura é interseção-união** — só há `vantagem-do-jev` quando TODOS os comparadores
   separam de zero. É a cláusula que torna a regra hostil ao Jev, e é a primeira que a pressa
   de publicar um resultado bom tenderia a afrouxar.
3. **Gabarito ausente não é gabarito que concorda** — sem segundo anotador sobre este corpus, ou
   com divergência ainda não adjudicada, o bloco `oficial` não existe. Enquanto essa condição
   não era checada, `adjudicado()` devolvia o gold do autor para casos que ninguém adjudicou.
"""
import json
import unittest
from pathlib import Path

from executor import run_e12_replicacao as e12

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-replicacao.jsonl'
CLASSES = {'cancelar', 'rastrear', 'trocar', 'cobranca', 'informacao'}
OUTROS = ('triagem-piloto.jsonl', 'triagem-confirmacao.jsonl', 'triagem-desempate.jsonl',
          'evidencia-piloto.jsonl', 'ressalvas-piloto.jsonl')


def carregar(nome):
    alvo = ROOT / 'data' / 'corpus' / nome
    return [json.loads(l) for l in alvo.read_text(encoding='utf-8').splitlines() if l.strip()]


class CorpusDaReplicacao(unittest.TestCase):

    def setUp(self):
        self.casos = carregar('triagem-replicacao.jsonl')

    def test_tamanho_declarado_no_preregistro(self):
        self.assertEqual(len(self.casos), 90)
        familias = {c['family'] for c in self.casos}
        self.assertEqual(len(familias), 30)
        for familia in familias:
            with self.subTest(familia=familia):
                self.assertEqual(sum(1 for c in self.casos if c['family'] == familia), 3)

    def test_nenhuma_familia_com_uma_classe_so(self):
        for familia in {c['family'] for c in self.casos}:
            classes = {c['gold'] for c in self.casos if c['family'] == familia}
            with self.subTest(familia=familia):
                self.assertGreater(len(classes), 1,
                                   'família com classe única não testa discriminação')

    def test_classes_e_identificadores_validos(self):
        ids = [c['case_id'] for c in self.casos]
        self.assertEqual(len(set(ids)), len(ids))
        for caso in self.casos:
            with self.subTest(caso=caso['case_id']):
                self.assertIn(caso['gold'], CLASSES)
                self.assertTrue(caso['text'].strip())
                self.assertTrue(caso['rationale'].strip())

    def test_nada_reaproveitado_dos_corpora_anteriores(self):
        textos, familias = set(), set()
        for nome in OUTROS:
            for caso in carregar(nome):
                textos.add(caso.get('text'))
                familias.add(caso.get('family'))
        self.assertEqual([c['case_id'] for c in self.casos if c['text'] in textos], [])
        self.assertEqual(sorted({c['family'] for c in self.casos} & familias), [])


class LeituraCongelada(unittest.TestCase):
    """A regra do pré-registro, exercitada com dados fabricados."""

    @staticmethod
    def comparacao(inferior, superior):
        return {'pareada': {'ic95': [inferior, superior]},
                'separa_de_zero': inferior > 0, 'separa_contra_o_jev': superior < 0}

    def test_vantagem_exige_todos_os_comparadores(self):
        todos = {'c%d' % i: self.comparacao(0.05, 0.2) for i in range(1, 5)}
        self.assertEqual(e12.leitura(todos)[0], 'vantagem-do-jev')

    def test_um_empate_derruba_a_vantagem(self):
        quase = {'c%d' % i: self.comparacao(0.05, 0.2) for i in range(1, 4)}
        quase['c4'] = self.comparacao(-0.02, 0.18)
        chave, frase = e12.leitura(quase)
        self.assertEqual(chave, 'sem-evidencia-de-vantagem')
        self.assertIn('c4', frase)

    def test_comparador_melhor_tem_precedencia(self):
        misto = {'c1': self.comparacao(0.05, 0.2), 'c2': self.comparacao(-0.3, -0.1),
                 'c3': self.comparacao(0.05, 0.2), 'c4': self.comparacao(0.05, 0.2)}
        chave, frase = e12.leitura(misto)
        self.assertEqual(chave, 'vantagem-do-comparador')
        self.assertIn('c2', frase)

    def test_intervalo_que_encosta_em_zero_nao_separa(self):
        encostado = {'c%d' % i: self.comparacao(0.0, 0.2) for i in range(1, 5)}
        self.assertEqual(e12.leitura(encostado)[0], 'sem-evidencia-de-vantagem')


class GabaritoAusenteNaoConcorda(unittest.TestCase):

    def test_sem_segundo_anotador_nao_ha_gabarito_oficial(self):
        casos = [{'case_id': 'x-1', 'family': 'F', 'gold': 'cancelar'}]
        original = e12.do_anotador_local
        try:
            e12.do_anotador_local = lambda: {}
            mapas, procedencia = e12.gabaritos(casos)
        finally:
            e12.do_anotador_local = original
        self.assertEqual(sorted(mapas), ['autor'])
        self.assertFalse(procedencia['corpus_tem_segundo_anotador'])

    def test_divergencia_sem_adjudicacao_nao_produz_oficial(self):
        import tempfile
        casos = [{'case_id': 'x-1', 'family': 'F', 'gold': 'cancelar'}]
        original, saida = e12.do_anotador_local, e12.OUT
        # A adjudicacao do E12 ja existe no repositorio; este teste e sobre o estado em que ela
        # ainda NAO existe, entao o diretorio do experimento aponta para um vazio.
        with tempfile.TemporaryDirectory() as pasta:
            try:
                e12.do_anotador_local = lambda: {'x-1': 'informacao'}
                e12.OUT = Path(pasta)
                mapas, procedencia = e12.gabaritos(casos)
            finally:
                e12.do_anotador_local, e12.OUT = original, saida
        self.assertNotIn('oficial', mapas)
        self.assertEqual(procedencia['casos_em_que_os_anotadores_divergem'], ['x-1'])


class CoberturaEAnulacao(unittest.TestCase):
    """As duas emendas que nasceram durante a execução, travadas contra regressão."""

    def test_braco_abaixo_do_minimo_sai_da_leitura(self):
        casos = [{'case_id': 'x-%d' % i, 'family': 'F', 'gold': 'cancelar',
                  'c1': 'cancelar', 'c2': 'cancelar', 'c3': 'cancelar',
                  'c4': 'cancelar' if i < 8 else None} for i in range(10)]
        cobertura = e12.cobertura_dos_bracos(casos)
        self.assertTrue(cobertura['c1']['entra_na_leitura'])
        self.assertEqual(cobertura['c4']['cobertura'], 0.8)
        self.assertFalse(cobertura['c4']['entra_na_leitura'])

    def test_limite_exato_de_noventa_por_cento_entra(self):
        casos = [{'case_id': 'x-%d' % i, 'family': 'F', 'gold': 'cancelar',
                  'c1': 'cancelar', 'c2': 'cancelar', 'c3': 'cancelar',
                  'c4': 'cancelar' if i < 9 else None} for i in range(10)]
        self.assertTrue(e12.cobertura_dos_bracos(casos)['c4']['entra_na_leitura'])

    def test_resposta_nova_prevalece_sobre_anulacao_na_mesma_linha(self):
        """A anulação vale para o que veio antes dela, nunca para a reexecução.

        A primeira versão apagava a resposta da reexecução porque a marca viajava junto no
        registro: nove chamadas já pagas do c4 sumiram da análise sem que nada acusasse.
        """
        import json as _json
        import tempfile
        with tempfile.TemporaryDirectory() as pasta:
            bruto = Path(pasta) / 'respostas.jsonl'
            linhas = [
                {'case_id': 'x-1', 'c4': 'cancelar', 'c4_attempt_id': 'velha'},
                {'case_id': 'x-1', 'c4_anulado_pela_emenda_3': 'velha'},
                {'case_id': 'x-1', 'c4': 'trocar', 'c4_attempt_id': 'nova',
                 'c4_anulado_pela_emenda_3': 'velha'},
            ]
            bruto.write_text(''.join(_json.dumps(l) + chr(10) for l in linhas), encoding='utf-8')
            original = e12.BRUTO
            try:
                e12.BRUTO = bruto
                recuperado = {c['case_id']: c for c in e12.recuperar()}
            finally:
                e12.BRUTO = original
        self.assertEqual(recuperado['x-1']['c4'], 'trocar')
        self.assertEqual(recuperado['x-1']['c4_attempt_id'], 'nova')

    def test_anulacao_sozinha_apaga_a_resposta_anterior(self):
        import json as _json
        import tempfile
        with tempfile.TemporaryDirectory() as pasta:
            bruto = Path(pasta) / 'respostas.jsonl'
            linhas = [{'case_id': 'x-1', 'c4': 'cancelar', 'c4_attempt_id': 'velha'},
                      {'case_id': 'x-1', 'c4_anulado_pela_emenda_3': 'velha'}]
            bruto.write_text(''.join(_json.dumps(l) + chr(10) for l in linhas), encoding='utf-8')
            original = e12.BRUTO
            try:
                e12.BRUTO = bruto
                recuperado = {c['case_id']: c for c in e12.recuperar()}
            finally:
                e12.BRUTO = original
        self.assertIsNone(recuperado['x-1'].get('c4'))
        self.assertIsNone(recuperado['x-1'].get('c4_attempt_id'))


class FalhaDeTransporte(unittest.TestCase):

    def test_o_que_e_repetido_e_o_que_nao_e(self):
        for erro in ('http 429: rate limit', 'http 502: bad gateway', 'Timeout ao ler'):
            with self.subTest(erro=erro):
                self.assertTrue(e12.falha_de_transporte(erro))
        for erro in ('json invalido: {', 'classe fora do contrato: None',
                     'json fora do contrato (list): [1]', None, ''):
            with self.subTest(erro=erro):
                self.assertFalse(e12.falha_de_transporte(erro))


if __name__ == '__main__':
    unittest.main()
