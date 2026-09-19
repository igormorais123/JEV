"""Cada PDF entregue tem de conter o documento que o nome dele promete.

[R13] `output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf` e `output/pdf/RELATORIO-FINAL-JEV.pdf`
estavam byte a byte idênticos, e assim foram versionados por três commits: quem abrisse o plano
científico leria o relatório final. O defeito não aparece em teste nenhum do painel porque não
está no painel — está no que sai do repositório para a mão de quem lê.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDFS = {
    'output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf': 'PLANO v1.0',
    'output/pdf/RELATORIO-FINAL-JEV.pdf': 'RELATÓRIO FINAL',
}


def primeira_pagina(caminho):
    from pypdf import PdfReader
    return PdfReader(str(caminho)).pages[0].extract_text() or ''


@unittest.skipUnless(all((ROOT / p).exists() for p in PDFS), 'PDFs ainda não gerados')
class EntregaveisNaoSeConfundem(unittest.TestCase):

    def test_cada_pdf_abre_no_documento_que_promete(self):
        for relativo, titulo in PDFS.items():
            with self.subTest(pdf=relativo):
                texto = primeira_pagina(ROOT / relativo)
                self.assertIn(titulo, texto,
                              f'{relativo} não começa pelo documento que o nome anuncia')

    def test_os_dois_pdfs_sao_documentos_diferentes(self):
        conteudos = {p: (ROOT / p).read_bytes() for p in PDFS}
        valores = list(conteudos.values())
        self.assertNotEqual(valores[0], valores[1],
                            'os dois entregáveis são o mesmo arquivo com nomes diferentes')


if __name__ == '__main__':
    unittest.main()


class GeradorDePdfAceitaOsCabecalhosDoRelatorio(unittest.TestCase):
    """[E11] Um `#### ` no markdown travava o build do PDF para sempre.

    O parser conhecia `##` e `###`. Um cabeçalho de nível 4 não casava com nenhum ramo, caía no
    fluxo de texto como parágrafo comum, e a partir daí o layout do reportlab entrava em laço: o
    comando não terminava, sem erro e sem saída. Achar isso exigiu bissecionar o markdown inteiro
    linha a linha. O teste roda o gerador sobre um documento mínimo com os quatro níveis.
    """

    def test_build_termina_com_cabecalho_de_nivel_quatro(self):
        import runpy
        import tempfile
        raiz = ROOT / 'planning' / 'build_deliverables.py'
        if not raiz.exists():
            self.skipTest('gerador ausente')
        modulo = runpy.run_path(str(raiz))
        destino = Path(tempfile.mkdtemp()) / 'teste.pdf'
        capa = dict(modulo['CAPA_DO_PLANO'])
        capa['destino'] = str(destino.relative_to(destino.anchor))
        markdown = ('# Título\n\n## Seção\n\nTexto.\n\n### Subseção\n\nTexto.\n\n'
                    '#### Nível quatro\n\nTexto que vem depois do nível quatro.\n')
        try:
            modulo['build_pdf'](markdown, {**capa, 'destino': 'output/pdf/_teste-niveis.pdf'})
        finally:
            alvo = ROOT / 'output' / 'pdf' / '_teste-niveis.pdf'
            if alvo.exists():
                alvo.unlink()
