# output/pdf/

PDFs finais: guia prático, plano científico e relatório final.

← [MAPA.md](../../MAPA.md) · pasta acima: [output](../../mapa/pastas/output.md) · abrir a pasta: [output/pdf/](../../output/pdf)

## Arquivos

| arquivo | tipo | tamanho | descrição |
|---|---|---:|---|
| [GUIA-PRATICO-JEV.pdf](../../output/pdf/GUIA-PRATICO-JEV.pdf) | pdf | 89 KB | PDF gerado (binário) |
| [PLANO-CIENTIFICO-JEV-HELENA.pdf](../../output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf) | pdf | 144 KB | PDF gerado (binário) |
| [RELATORIO-FINAL-JEV.pdf](../../output/pdf/RELATORIO-FINAL-JEV.pdf) | pdf | 144 KB | PDF gerado (binário) |
| [_teste.pdf](../../output/pdf/_teste.pdf) | pdf | 99 KB | PDF gerado (binário) |

## Grafo de imports e links

Nós em negrito são desta pasta; setas cheias são imports, tracejadas são links de documento.

```mermaid
flowchart LR
  n_README_md["README.md"]
  n_output_pdf_PLANO_CIENTIFICO_JEV_HELENA_pdf["<b>PLANO-CIENTIFICO-JEV-HELENA.pdf</b>"]
  n_README_md -.-> n_output_pdf_PLANO_CIENTIFICO_JEV_HELENA_pdf
```

## Ligações e conteúdo de cada arquivo

### GUIA-PRATICO-JEV.pdf

- **é usado por** — citação: [`planning/build_guia_pdf.py`](../../planning/build_guia_pdf.py)

### PLANO-CIENTIFICO-JEV-HELENA.pdf

- **é usado por** — link: [`README.md`](../../README.md); citação: [`docs/RELATORIO-FINAL-JEV.md`](../../docs/RELATORIO-FINAL-JEV.md), [`executor/tests/test_entregaveis.py`](../../executor/tests/test_entregaveis.py), [`lab/dashboard.js`](../../lab/dashboard.js), [`lab/index.html`](../../lab/index.html), [`lab/server.py`](../../lab/server.py), [`lab/template.html`](../../lab/template.html), [`laboratorio/r21-prosa.json`](../../laboratorio/r21-prosa.json), [`planning/build_deliverables.py`](../../planning/build_deliverables.py)

### RELATORIO-FINAL-JEV.pdf

- **é usado por** — citação: [`docs/RELATORIO-FINAL-JEV.md`](../../docs/RELATORIO-FINAL-JEV.md), [`executor/tests/test_entregaveis.py`](../../executor/tests/test_entregaveis.py), [`laboratorio/r21-prosa.json`](../../laboratorio/r21-prosa.json), [`planning/build_relatorio_pdf.py`](../../planning/build_relatorio_pdf.py)
