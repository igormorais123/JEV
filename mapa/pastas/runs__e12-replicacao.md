# runs/e12-replicacao/

Resultados do experimento E12 (replicacao): relatório agregado e, quando houve, adjudicação cega e respostas brutas.

← [MAPA.md](../../MAPA.md) · pasta acima: [runs](../../mapa/pastas/runs.md) · abrir a pasta: [runs/e12-replicacao/](../../runs/e12-replicacao)

**Outras peças do E12:** [`executor/adjudicar_e12.py`](../../executor/adjudicar_e12.py) · [`executor/run_e12_replicacao.py`](../../executor/run_e12_replicacao.py) · [`executor/tests/test_calibracao_e12.py`](../../executor/tests/test_calibracao_e12.py) · [`executor/tests/test_e12_replicacao.py`](../../executor/tests/test_e12_replicacao.py) · [`planning/preregistro-E12-replicacao.md`](../../planning/preregistro-E12-replicacao.md)

## Arquivos

| arquivo | tipo | tamanho | descrição |
|---|---|---:|---|
| [adjudicacao-mapa.json](../../runs/e12-replicacao/adjudicacao-mapa.json) | dado | 62 l. | Objeto com 10 chaves: rep-p05-01, rep-p05-02, rep-p06-01, rep-p09-01, rep-p10-01, rep-p10-02, rep-p17-01, rep-p22-01, rep-p23-01, rep-p30-03 |
| [adjudicacao.json](../../runs/e12-replicacao/adjudicacao.json) | dado | 104 l. | Objeto com 6 chaves: at, terceiro_juiz, preregistro, corpus, casos, placar |
| [anuladas-emenda-3.json](../../runs/e12-replicacao/anuladas-emenda-3.json) | dado | 65 l. | Objeto com 8 chaves: at, emenda, motivo, braco, teto_antigo, teto_novo, chamadas_anuladas_da_analise, observacao |
| [casos-cegos.json](../../runs/e12-replicacao/casos-cegos.json) | dado | 62 l. | Lista de 10 itens (case_id, text, A, B) |
| [prompt-adjudicacao.txt](../../runs/e12-replicacao/prompt-adjudicacao.txt) | texto | 68 l. | Voce e o terceiro juiz de um estudo de anotacao. Dois anotadores independentes classificaram as mesmas mensagens de atendimento ao cliente e divergiram em 10 c… |
| [relatorio.json](../../runs/e12-replicacao/relatorio.json) | dado | 4614 l. | Objeto com 23 chaves: at, preregistro, corpus, modelo, comparadores, casos_programados, familias, resumo, gabaritos_disponiveis, cobertura_dos_bracos, bracos_n… |
| [respostas.jsonl](../../runs/e12-replicacao/respostas.jsonl) | dado | 536 l. | 536 registros JSONL (campos: case_id, family, gold, text, rationale, revisado_antes_de_executar, jev, jev_confidence, jev_status, jev_attempt_id) |

## Ligações e conteúdo de cada arquivo

### adjudicacao-mapa.json

- **papel nos estudos** — resultado [E12](../../mapa/conhecimento/experimentos.md#e12)

### adjudicacao.json

- **usa** — citação: [`data/corpus/triagem-replicacao.jsonl`](../../data/corpus/triagem-replicacao.jsonl), [`planning/preregistro-E12-replicacao.md`](../../planning/preregistro-E12-replicacao.md)
- **papel nos estudos** — resultado [E12](../../mapa/conhecimento/experimentos.md#e12)

### anuladas-emenda-3.json

- **usa** — citação: [`planning/preregistro-E12-replicacao.md`](../../planning/preregistro-E12-replicacao.md)
- **papel nos estudos** — resultado [E12](../../mapa/conhecimento/experimentos.md#e12)

### casos-cegos.json

- **papel nos estudos** — resultado [E12](../../mapa/conhecimento/experimentos.md#e12)

### prompt-adjudicacao.txt

- **é usado por** — citação: [`executor/adjudicar_e12.py`](../../executor/adjudicar_e12.py)
- **papel nos estudos** — resultado [E12](../../mapa/conhecimento/experimentos.md#e12)

### relatorio.json

- **usa** — citação: [`data/corpus/triagem-replicacao.jsonl`](../../data/corpus/triagem-replicacao.jsonl), [`planning/preregistro-E12-replicacao.md`](../../planning/preregistro-E12-replicacao.md)
- **é usado por** — citação: [`executor/erro_grave.py`](../../executor/erro_grave.py), [`executor/placar.py`](../../executor/placar.py), [`executor/run_e8_anotador.py`](../../executor/run_e8_anotador.py), [`laboratorio/r0_calibracao.py`](../../laboratorio/r0_calibracao.py), [`planning/build_guia_pdf.py`](../../planning/build_guia_pdf.py), [`planning/build_relatorio_pdf.py`](../../planning/build_relatorio_pdf.py)
- **papel nos estudos** — resultado [E12](../../mapa/conhecimento/experimentos.md#e12)

### respostas.jsonl

- **é usado por** — citação: [`docs/RELATORIO-FINAL-JEV.md`](../../docs/RELATORIO-FINAL-JEV.md), [`executor/run_e12_replicacao.py`](../../executor/run_e12_replicacao.py), [`executor/tests/test_achados_revisao16.py`](../../executor/tests/test_achados_revisao16.py), [`laboratorio/r21-prosa.json`](../../laboratorio/r21-prosa.json)
- **papel nos estudos** — resultado [E12](../../mapa/conhecimento/experimentos.md#e12)
