"""A leitura pelo shell só mexe em comando de leitura pura, e o que ela escreve é leitura.

O hook devolve `allow` junto com o comando novo, e `allow` dispensa a confirmação do usuário:
por isso a maior parte destes testes é sobre o que a camada NÃO toca.
"""
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from camadas import nucleo, shell  # noqa: E402
from tests.test_camadas import arquivo_com_alvo, quebrado, transporte_por_trecho  # noqa: E402


class Gramatica(unittest.TestCase):

    def test_divide_nos_separadores_de_nivel_superior(self):
        segmentos, separadores = shell.dividir('cd x && cat a.py; echo "a && b"')
        self.assertEqual([s.strip() for s in segmentos], ['cd x', 'cat a.py', 'echo "a && b"'])
        self.assertEqual(separadores, ['&&', ';'])

    def test_recusa_tudo_que_nao_entende(self):
        for comando in ('cat a.py | head', 'cat a.py > b.py', 'cat $ARQ', 'cat `ls`', 'cat $(ls)',
                        'cat a.py &', 'cat *.py', "python - <<'FIM'\nprint(1)\nFIM", 'cat a\\ b',
                        'cat "a', '(cat a.py)', 'cat ~/a.py', 'cat a.py;', "sed -n '1,$p' a.py"):
            self.assertIsNone(shell.dividir(comando), comando)

    def test_so_leitura_pura_e_interpretada(self):
        for segmento in ('rm a.py', 'python a.py', 'git status', 'sed -i s/a/b/ a.py',
                         "sed -n '1,5p;w x' a.py", "sed 's/a/b/' a.py", 'X=1 cat a.py', 'cd'):
            self.assertIsNone(shell.interpretar(segmento, Path('.')), segmento)

    def test_intervalos(self):
        self.assertEqual(shell.interpretar("sed -n '300,420p' a.py", Path('.'))['fim'], 420)
        self.assertEqual(shell.interpretar('head -n 50 a.py', Path('.'))['fim'], 50)
        self.assertEqual(shell.interpretar('head -80 a.py', Path('.'))['fim'], 80)
        self.assertEqual(shell.interpretar('cat a.py b.py', Path('.'))['tipo'], 'outro')

    def test_caminho_do_git_bash_vira_caminho_do_windows(self):
        visto = shell.interpretar('cat /c/Users/x/a.py', None)
        self.assertEqual(visto['caminho'].as_posix(), 'C:/Users/x/a.py')
        self.assertIsNone(shell.interpretar('cat /tmp/a.py', Path('.'))['caminho'])
        self.assertIsNone(shell.interpretar('cat a.py', None)['caminho'])


class Reescrita(unittest.TestCase):

    def setUp(self):
        self.arquivo = arquivo_com_alvo(nucleo.ESTADO / '_teste_shell.py')
        self.pedido = 'onde está a função alvo?'
        self.transporte = transporte_por_trecho(
            lambda t: ('essencial', 0.98) if 'def alvo' in t else ('complementar', 0.3))
        self.cwd = str(self.arquivo.parent)

    def tearDown(self):
        self.arquivo.unlink(missing_ok=True)

    def analisar(self, comando, **kw):
        return shell.analisar(comando, kw.pop('pedido', self.pedido), self.cwd,
                              transporte=kw.pop('transporte', self.transporte))

    def test_cat_de_arquivo_grande_vira_sed_com_a_janela(self):
        d = self.analisar('echo === && cat _teste_shell.py; echo fim')
        self.assertEqual(d['acao'], 'reescrever')
        self.assertRegex(d['comando'], r"^echo === && sed -n '\d+,\d+p' _teste_shell.py ; echo fim$")
        saida = subprocess.run(['bash', '-c', d['comando']], cwd=self.cwd, capture_output=True,
                               text=True).stdout
        self.assertIn('def alvo', saida)
        self.assertLess(saida.count('\n'), 300)
        nota = shell.nota_para_o_agente(d)
        self.assertIn('_teste_shell.py tem', nota)
        self.assertIn("sed -n 'A,Bp'", nota)

    def test_cd_muda_o_diretorio_de_resolucao(self):
        d = shell.analisar(f'cd {self.arquivo.parent.as_posix()} && cat _teste_shell.py',
                           self.pedido, str(RAIZ), transporte=self.transporte)
        self.assertEqual(d['acao'], 'reescrever')

    def test_um_segmento_que_nao_e_leitura_trava_o_comando_inteiro(self):
        for comando in ('cat _teste_shell.py && rm -rf x', 'git status; cat _teste_shell.py',
                        'cat _teste_shell.py || echo x'):
            d = self.analisar(comando)
            self.assertEqual(d['acao'], 'nada', comando)
            self.assertEqual(d['leituras'], [], comando)

    def test_intervalo_pedido_fica_e_e_registrado(self):
        d = self.analisar("sed -n '100,180p' _teste_shell.py")
        self.assertEqual(d['acao'], 'nada')
        self.assertEqual(d['leituras'][0]['motivo'], 'read ja delimitado')
        self.assertEqual((d['leituras'][0]['offset'], d['leituras'][0]['limit']), (100, 81))

    def test_head_que_cobre_o_arquivo_inteiro_conta_como_cat(self):
        self.assertEqual(self.analisar('head -n 5000 _teste_shell.py')['acao'], 'reescrever')

    def test_falha_do_jev_e_falta_de_pedido_deixam_o_comando_como_veio(self):
        self.assertEqual(self.analisar('cat _teste_shell.py', transporte=quebrado)['acao'], 'nada')
        self.assertEqual(self.analisar('cat _teste_shell.py', pedido='')['acao'], 'nada')

    def test_no_maximo_dois_arquivos_por_comando(self):
        copias = [self.arquivo.with_name(f'_teste_shell_{i}.py') for i in range(3)]
        try:
            for copia in copias:
                copia.write_text(self.arquivo.read_text(encoding='utf-8'), encoding='utf-8')
            d = self.analisar(' && '.join(f'cat {c.name}' for c in copias))
            self.assertEqual(len(d['estreitados']), 2)
            self.assertEqual(d['comando'].count('sed -n'), 2)
            self.assertIn('cat _teste_shell_2.py', d['comando'])
        finally:
            for copia in copias:
                copia.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
