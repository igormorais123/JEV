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
