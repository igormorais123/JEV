"""O placar não pode se contradizer.

A oitava rodada de revisão encontrou o painel publicando dois números para a mesma decisão: o
veredito citava 87,5% em 40 casos da confirmação e o cartão do E9, no mesmo JSON, citava 80% em
80 casos da união. Os dois estavam certos e os dois eram a mesma recomendação.

Este teste roda `montar()` contra os relatórios REAIS do repositório — não contra dicionários
fabricados — e exige que o painel escolha uma leitura e a use inteira.
"""
import json
import re
import unittest
from pathlib import Path

from executor import placar

ROOT = Path(__file__).resolve().parents[2]


def tem_relatorios():
    return all((ROOT / 'runs' / nome / 'relatorio.json').exists()
               for nome in ('e7-confirmacao', 'e9-prevalencia', 'e8-anotador'))


@unittest.skipUnless(tem_relatorios(), 'requer os relatórios de execução')
class CoerenciaDoPlacar(unittest.TestCase):
    def setUp(self):
        self.bloco = placar.montar()
        self.cartoes = {c['chave']: c for c in self.bloco['cartoes']}

    def numeros(self, texto):
        return set(re.findall(r'\d+[.,]?\d*', texto))

    def test_veredito_e_cartao_e9_citam_a_mesma_cobertura(self):
        veredito = self.bloco['veredito']['texto']
        cartao = self.cartoes['e9']['leitura']
        e9 = json.loads((ROOT / 'runs/e9-prevalencia/relatorio.json').read_text(encoding='utf-8'))
        politica = placar.politica_de_referencia(e9)
        self.assertIsNotNone(politica, 'sem partição de confirmação não há política de referência')
        cobertura = f"{politica['cobertura'] * 100:.1f}"
        self.assertIn(cobertura, veredito)
        self.assertIn(cobertura, cartao)
        self.assertIn(str(politica['casos']), veredito)
        self.assertIn(str(politica['casos']), cartao)

    def test_politica_de_referencia_nao_cai_para_a_uniao(self):
        """Sem a partição, o painel tem de ficar em silêncio, não trocar o número."""
        e9 = {'politicas_de_aceitacao': [{'corte': 0.90, 'cobertura': 0.8, 'casos': 80,
                                          'erros_entre_aceitos': 0}]}
        self.assertIsNone(placar.politica_de_referencia(e9))

    def test_cartao_do_gabarito_adjudicado_declara_o_gabarito(self):
        cartao = self.cartoes.get('e8')
        self.assertIsNotNone(cartao, 'o cartão do gabarito adjudicado sumiu')
        self.assertIn('oficial', cartao['comparacao'].lower())

    def test_cartao_de_concordancia_diz_que_usa_o_gabarito_do_autor(self):
        cartao = self.cartoes['e8b']
        self.assertIn('GABARITO DO AUTOR', cartao['leitura'])

    def test_erros_da_nota_de_confianca_batem_com_o_gabarito_oficial(self):
        adj = json.loads((ROOT / 'runs/e8-anotador/adjudicacao.json').read_text(encoding='utf-8'))
        erros = len(adj['gabarito_adjudicado']['erros'])
        self.assertIn(f'{erros} erros', self.bloco['veredito']['confianca_nota'])

    def test_pendencias_nao_pedem_o_que_ja_foi_feito(self):
        texto = ' '.join(self.bloco['pendencias']).lower()
        self.assertNotIn('adjudicação dos casos', texto)
        self.assertIn('pessoas do atendimento real', texto)

    def test_e9_usa_o_gabarito_oficial(self):
        e9 = json.loads((ROOT / 'runs/e9-prevalencia/relatorio.json').read_text(encoding='utf-8'))
        self.assertTrue(e9['procedencia_do_gabarito']['adjudicado'])
        adj = json.loads((ROOT / 'runs/e8-anotador/adjudicacao.json').read_text(encoding='utf-8'))
        erros_oficiais = len(adj['gabarito_adjudicado']['erros'])
        tudo = next(p for p in e9['politicas_de_aceitacao'] if p['corte'] == 0.0)
        self.assertEqual(tudo['erros_entre_aceitos'], erros_oficiais)


class GabaritoOficial(unittest.TestCase):
    def test_adjudicacao_substitui_apenas_o_que_mudou(self):
        from executor import gabarito
        autor = gabarito.do_autor()
        oficial, procedencia = gabarito.adjudicado()
        if not procedencia['adjudicado']:
            self.skipTest('sem adjudicação no repositório')
        mudados = {c['case_id'] for c in procedencia['casos_substituidos']}
        for case_id, entrada in oficial.items():
            if case_id not in mudados:
                self.assertEqual(entrada['gold'], autor[case_id]['gold'], case_id)

    def test_rotulo_distingue_com_e_sem_adjudicacao(self):
        from executor import gabarito
        self.assertIn('sem adjudicação', gabarito.rotulo({'adjudicado': False}))
        self.assertIn('adjudicado', gabarito.rotulo({'adjudicado': True, 'casos_substituidos': []}))


if __name__ == '__main__':
    unittest.main()


@unittest.skipUnless(tem_relatorios(), 'requer os relatórios de execução')
class PainelPublicadoEhReproduzivel(unittest.TestCase):
    """O que está no ar tem que ser o que os relatórios produzem.

    Sem isto, uma edição manual em `lab/data/execution.json` passaria despercebida, e o painel
    poderia afirmar algo que nenhum experimento sustenta.
    """

    def test_bloco_publicado_bate_com_o_gerado(self):
        publicado = json.loads(
            (ROOT / 'lab/data/execution.json').read_text(encoding='utf-8')).get('decision')
        self.assertIsNotNone(publicado, 'o painel está sem placar de decisão')
        gerado = placar.montar()
        for campo in ('veredito', 'cartoes', 'pendencias', 'orcamento'):
            self.assertEqual(publicado[campo], gerado[campo],
                             f'{campo} publicado difere do que os relatórios geram')

    def test_custo_somado_no_painel_fecha_com_o_ledger(self):
        import sqlite3
        estado = json.loads((ROOT / 'lab/data/execution.json').read_text(encoding='utf-8'))
        do_painel = sum(a['cost_usd'] or 0 for r in estado['runs'] for a in r['attempts'])
        caminho = ROOT / 'runs' / 'ledger.sqlite3'
        if not caminho.exists():
            self.skipTest('sem ledger')
        db = sqlite3.connect(str(caminho))
        try:
            total = db.execute(
                'SELECT COALESCE(SUM(CASE WHEN settled_nusd IS NULL THEN reserved_nusd'
                ' ELSE settled_nusd END),0) FROM attempt_budget').fetchone()[0]
        finally:
            db.close()
        self.assertAlmostEqual(do_painel, total / 1e9, places=9)
