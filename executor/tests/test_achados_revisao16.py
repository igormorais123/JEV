"""O que a décima sexta rodada de revisão adversarial encontrou, travado contra regressão.

A rodada revisou o E12 e não derrubou a conclusão central, mas achou três coisas que os testes
existentes deixavam passar:

1. **Só o E8 tinha a adjudicação versionada.** As do E11 e do E12 ficavam fora do Git por causa
   do `runs/**`, e o relatório se apoia nelas para afirmar "o terceiro juiz confirmou meu
   gabarito em 10 de 10". Quem clonasse o repositório não conseguia conferir a afirmação que
   mais sustenta a recomendação.
2. **Um número de erro grave no relatório era anterior a uma correção de dados.** O texto dizia
   que o gpt-oss-20b perdia 5 `cancelar`; eram 5 antes de eu corrigir o defeito que apagava nove
   respostas já pagas daquele braço. Depois da correção são 2, e o texto não acompanhou. É o
   mesmo padrão que a nona rodada batizou: número velho numa caixa nova.
3. **O README trocava "não separa de zero" por "empata exatamente com o mais barato"** — e ainda
   atribuía o empate ao braço errado: o empate exato é contra o llama-3.1-8b, que não é o mais
   barato dos quatro.
"""
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELATORIO = ROOT / 'docs' / 'RELATORIO-FINAL-JEV.md'
README = ROOT / 'README.md'
E12 = ROOT / 'runs' / 'e12-replicacao' / 'relatorio.json'


def versionados():
    saida = subprocess.run(['git', 'ls-files', 'runs/'], cwd=ROOT, capture_output=True,
                           text=True, check=False)
    return set(saida.stdout.split())


@unittest.skipUnless((ROOT / '.git').exists(), 'fora de um repositório Git')
class EvidenciaCitadaEstaVersionada(unittest.TestCase):

    def test_toda_adjudicacao_citada_pode_ser_conferida_por_quem_clona(self):
        arquivos = versionados()
        for adjudicacao in ROOT.glob('runs/*/adjudicacao.json'):
            relativo = adjudicacao.relative_to(ROOT).as_posix()
            with self.subTest(arquivo=relativo):
                self.assertIn(relativo, arquivos,
                              'o relatório cita esta adjudicação e ela não vai no Git')

    def test_o_bruto_que_prova_a_cronologia_das_emendas_esta_versionado(self):
        arquivos = versionados()
        bruto = 'runs/e12-replicacao/respostas.jsonl'
        if not (ROOT / bruto).exists():
            self.skipTest('o E12 ainda não rodou')
        self.assertIn(bruto, arquivos,
                      'sem o bruto versionado, "a emenda foi escrita antes" não é auditável')


@unittest.skipUnless(E12.exists(), 'o E12 ainda não rodou')
class NumeroDeErroGraveNoTextoVemDoDado(unittest.TestCase):
    """O relatório compara erro grave entre os braços; os números têm de sair do JSON."""

    def setUp(self):
        self.dados = json.loads(E12.read_text(encoding='utf-8'))
        self.texto = RELATORIO.read_text(encoding='utf-8')
        self.oficial = (self.dados['por_gabarito'].get('oficial')
                        or self.dados['por_gabarito']['autor'])['erro_grave']

    def test_a_frase_de_comparacao_bate_com_o_relatorio_json(self):
        padrao = (r'llama-3\.1-8b, (\d+) falsos? `cancelar` e (\d+) perdidos?; '
                  r'gemma-3-12b, (\d+) e (\d+); gpt-oss-20b, (\d+) e (\d+)')
        achado = re.search(padrao, self.texto)
        self.assertIsNotNone(achado, 'a frase de erro grave do E12 sumiu ou mudou de forma')
        esperado = []
        for chave in ('c1', 'c3', 'c4'):
            bloco = self.oficial[chave]
            esperado += [len(bloco['falso_cancelar']), len(bloco['cancelar_perdido'])]
        self.assertEqual([int(n) for n in achado.groups()], esperado)

    def test_quem_o_texto_diz_que_nao_comete_erro_grave_de_fato_nao_comete(self):
        for chave in ('jev', 'c2'):
            with self.subTest(braco=chave):
                self.assertEqual(self.oficial[chave]['falso_cancelar'], [])
                self.assertEqual(self.oficial[chave]['cancelar_perdido'], [])


@unittest.skipUnless(E12.exists(), 'o E12 ainda não rodou')
class ReadmeNaoExageraOResultado(unittest.TestCase):

    def setUp(self):
        self.dados = json.loads(E12.read_text(encoding='utf-8'))
        self.readme = README.read_text(encoding='utf-8')

    def test_o_readme_nao_chama_de_empate_o_que_o_dado_nao_mede(self):
        """"Empatar" e "não separar de zero" não são a mesma afirmação.

        A segunda é o que o intervalo diz; a primeira é mais forte e o estudo não a sustenta,
        porque não observar diferença não é observar ausência de diferença.
        """
        outro = self.dados['por_gabarito'].get('anotador local')
        if not outro:
            self.skipTest('sem o gabarito do anotador independente')
        exatos = [c for c, v in outro['comparacoes'].items()
                  if v['pareada']['diferenca_observada'] == 0.0]
        if 'empata exatamente' in self.readme:
            self.assertTrue(exatos, 'o README fala em empate exato e nenhum braço empatou')
            mais_barato = min(self.dados['custo'],
                              key=lambda c: self.dados['custo'][c]['custo_por_mil_classificacoes_usd']
                              if c != 'jev' and self.dados['custo'].get(c) else float('inf'))
            self.assertIn(mais_barato, exatos,
                          'o README atribui o empate exato ao braço mais barato, e não foi ele')

    def test_o_readme_cita_o_veredito_que_o_experimento_produziu(self):
        if self.dados['veredito'] == 'depende-do-gabarito':
            self.assertIn('não separa de zero contra nenhum deles', self.readme)


if __name__ == '__main__':
    unittest.main()
