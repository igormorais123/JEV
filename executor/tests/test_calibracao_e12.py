"""A calibração publicada tem de ser a do dado, inclusive quando o dado desmente a recomendação.

O corte de 0,90 foi calibrado no piloto e na confirmação, onde todos os erros do modelo ficaram
abaixo dele. No corpus novo do E12 isso não se repetiu: o único erro veio com confiança 0,98.
Enquanto nada checava isso, o relatório podia continuar recomendando um corte que o experimento
mais recente já tinha furado — exatamente o padrão de defeito que este estudo persegue desde a
nona rodada, número velho numa caixa nova.

Este teste recalcula a calibração do E12 dos casos brutos e exige que o documento diga o que ela
diz.
"""
import json
import re
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E12 = ROOT / 'runs' / 'e12-replicacao' / 'relatorio.json'
RELATORIO = ROOT / 'docs' / 'RELATORIO-FINAL-JEV.md'
GUIA = ROOT / 'docs' / 'GUIA-PRATICO-JEV.md'


def calibracao(casos, corte, gold):
    aceitos = [c for c in casos if (c.get('jev_confidence') or 0) >= corte]
    erros = [c['case_id'] for c in aceitos if c.get('jev') != gold[c['case_id']]]
    familias = defaultdict(list)
    for c in aceitos:
        familias[c['family']].append(c.get('jev') == gold[c['case_id']])
    return {'aceitos': len(aceitos), 'erros': erros,
            'familias_com_erro': sum(1 for v in familias.values() if not all(v))}


@unittest.skipUnless(E12.exists(), 'o E12 ainda não rodou')
class CalibracaoDoCorpusNovo(unittest.TestCase):

    def setUp(self):
        self.dados = json.loads(E12.read_text(encoding='utf-8'))
        self.casos = self.dados['casos']
        oficial = self.dados['por_gabarito'].get('oficial') or self.dados['por_gabarito']['autor']
        self.gold = {c['case_id']: c['gold'] for c in self.casos}
        self.tem_oficial = 'oficial' in self.dados['por_gabarito']
        self.oficial = oficial

    def test_o_corte_de_090_deixa_passar_erro_neste_corpus(self):
        """Se um dia isto falhar, é porque o dado mudou — e o texto precisa mudar junto."""
        resultado = calibracao(self.casos, 0.90, self.gold)
        self.assertEqual(len(resultado['erros']), 1,
                         'a seção 6.1 afirma que o corte 0,90 deixa passar exatamente 1 erro')
        self.assertIn('rep-p30-03', resultado['erros'])

    def test_o_corte_recomendado_zera_o_erro(self):
        resultado = calibracao(self.casos, 0.99, self.gold)
        self.assertEqual(resultado['erros'], [],
                         'o corte recomendado tem de ser o que zera o erro no corpus novo')

    def test_o_erro_veio_acima_do_corte_antigo(self):
        erro = next(c for c in self.casos if c['case_id'] == 'rep-p30-03')
        self.assertGreater(erro['jev_confidence'], 0.90,
                           'o achado da seção 6.1 é que o erro passou do corte antigo')

    def test_a_tabela_do_relatorio_bate_com_o_recalculo(self):
        texto = RELATORIO.read_text(encoding='utf-8')
        for corte, padrao in ((0.90, r'\| 0,90 \| (\d+)/90 \| [\d,%*]+ \| \*\*(\d+)\*\*'),
                              (0.99, r'\| \*\*0,99\*\* \| \*\*(\d+)/90\*\* \| [\d,%*]+ \| \*\*(\d+)\*\*')):
            achado = re.search(padrao, texto)
            with self.subTest(corte=corte):
                self.assertIsNotNone(achado, f'a linha do corte {corte} sumiu da seção 6.1')
                resultado = calibracao(self.casos, corte, self.gold)
                self.assertEqual(int(achado.group(1)), resultado['aceitos'])
                self.assertEqual(int(achado.group(2)), len(resultado['erros']))

    @unittest.skipUnless(GUIA.exists(), 'o guia prático ainda não existe')
    def test_o_guia_nao_recomenda_um_corte_que_deixa_passar_erro(self):
        texto = GUIA.read_text(encoding='utf-8')
        zera = next(corte for corte in (0.90, 0.95, 0.99)
                    if not calibracao(self.casos, corte, self.gold)['erros'])
        rotulo = f'{zera:.2f}'.replace('.', ',')
        self.assertIn(rotulo, texto,
                      'o guia precisa citar o corte que de fato zera o erro no corpus novo')


if __name__ == '__main__':
    unittest.main()
