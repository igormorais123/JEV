"""Gera o PDF do relatório final, reaproveitando a identidade visual do plano.

O gerador de PDF já existe em `build_deliverables.py` e produz o plano científico. Aqui só
trocamos a origem (o relatório final) e o destino, para que os dois documentos saiam com a
mesma tipografia, o mesmo sumário e o mesmo rodapé.

Uso:
    python planning/build_relatorio_pdf.py
"""
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGEM = ROOT / 'docs' / 'RELATORIO-FINAL-JEV.md'
DESTINO = ROOT / 'output' / 'pdf' / 'RELATORIO-FINAL-JEV.pdf'


def main():
    modulo = runpy.run_path(str(ROOT / 'planning' / 'build_deliverables.py'))
    build_pdf = modulo['build_pdf']
    # build_pdf grava no caminho do plano; renomeamos depois para não duplicar o gerador.
    gerado = Path(build_pdf(ORIGEM.read_text(encoding='utf-8')))
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_bytes(gerado.read_bytes())
    print(f'PDF do relatório final: {DESTINO.relative_to(ROOT)} '
          f'({DESTINO.stat().st_size / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
