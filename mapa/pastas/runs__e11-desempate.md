# runs/e11-desempate/

Resultados do experimento E11 (desempate): relatório agregado e, quando houve, adjudicação cega e respostas brutas.

← [MAPA.md](../../MAPA.md) · pasta acima: [runs](../../mapa/pastas/runs.md) · abrir a pasta: [runs/e11-desempate/](../../runs/e11-desempate)

**Outras peças do E11:** [`executor/adjudicar_e11.py`](../../executor/adjudicar_e11.py) · [`executor/run_e11_desempate.py`](../../executor/run_e11_desempate.py) · [`planning/preregistro-E11-desempate.md`](../../planning/preregistro-E11-desempate.md)

## Arquivos

| arquivo | tipo | tamanho | descrição |
|---|---|---:|---|
| [adjudicacao-bruta.jsonl](../../runs/e11-desempate/adjudicacao-bruta.jsonl) | dado | 10 l. | 10 registros JSONL (campos: case_id, escolha, classe, motivo) |
| [adjudicacao-mapa.json](../../runs/e11-desempate/adjudicacao-mapa.json) | dado | 62 l. | Objeto com 10 chaves: dsp-d01-02, dsp-d03-01, dsp-d06-03, dsp-d09-01, dsp-d10-03, dsp-d11-01, dsp-d12-01, dsp-d16-01, dsp-d16-02, dsp-d18-01 |
| [adjudicacao.json](../../runs/e11-desempate/adjudicacao.json) | dado | 104 l. | Objeto com 6 chaves: at, terceiro_juiz, preregistro, corpus, casos, placar |
| [casos-cegos.json](../../runs/e11-desempate/casos-cegos.json) | dado | 62 l. | Lista de 10 itens (case_id, text, A, B) |
| [prompt-adjudicacao.txt](../../runs/e11-desempate/prompt-adjudicacao.txt) | texto | 68 l. | Voce e o terceiro juiz de um estudo de anotacao. Dois anotadores independentes classificaram as mesmas mensagens de atendimento ao cliente e divergiram em 10 c… |
| [relatorio.json](../../runs/e11-desempate/relatorio.json) | dado | 1512 l. | Objeto com 23 chaves: at, preregistro, corpus, modelo, comparador, jev, llm, pareada, so_jev_acerta, so_llm_acerta, mcnemar_discordancias, mcnemar_p_exato |
| [respostas.jsonl](../../runs/e11-desempate/respostas.jsonl) | dado | 120 l. | 120 registros JSONL (campos: case_id, family, gold, text, rationale, revisado_antes_de_executar, jev, jev_confidence, jev_status, jev_attempt_id) |

## Ligações e conteúdo de cada arquivo

### adjudicacao-bruta.jsonl

- **papel nos estudos** — resultado [E11](../../mapa/conhecimento/experimentos.md#e11)

### adjudicacao-mapa.json

- **papel nos estudos** — resultado [E11](../../mapa/conhecimento/experimentos.md#e11)

### adjudicacao.json

- **usa** — citação: [`data/corpus/triagem-desempate.jsonl`](../../data/corpus/triagem-desempate.jsonl), [`planning/preregistro-E11-desempate.md`](../../planning/preregistro-E11-desempate.md)
- **é usado por** — citação: [`runs/e11-desempate/relatorio.json`](../../runs/e11-desempate/relatorio.json)
- **papel nos estudos** — resultado [E11](../../mapa/conhecimento/experimentos.md#e11)

### casos-cegos.json

- **papel nos estudos** — resultado [E11](../../mapa/conhecimento/experimentos.md#e11)

### prompt-adjudicacao.txt

- **é usado por** — citação: [`executor/adjudicar_e11.py`](../../executor/adjudicar_e11.py)
- **papel nos estudos** — resultado [E11](../../mapa/conhecimento/experimentos.md#e11)

### relatorio.json

- **usa** — citação: [`planning/preregistro-E11-desempate.md`](../../planning/preregistro-E11-desempate.md), [`runs/e11-desempate/adjudicacao.json`](../../runs/e11-desempate/adjudicacao.json)
- **é usado por** — citação: [`executor/erro_grave.py`](../../executor/erro_grave.py), [`executor/placar.py`](../../executor/placar.py), [`executor/run_e8_anotador.py`](../../executor/run_e8_anotador.py), [`executor/tests/test_coerencia_placar.py`](../../executor/tests/test_coerencia_placar.py), [`laboratorio/r0_calibracao.py`](../../laboratorio/r0_calibracao.py), [`planning/build_guia_pdf.py`](../../planning/build_guia_pdf.py), [`planning/build_relatorio_pdf.py`](../../planning/build_relatorio_pdf.py)
- **papel nos estudos** — resultado [E11](../../mapa/conhecimento/experimentos.md#e11)

### respostas.jsonl

- **é usado por** — citação: [`executor/run_e11_desempate.py`](../../executor/run_e11_desempate.py), [`planning/preregistro-E11-desempate.md`](../../planning/preregistro-E11-desempate.md)
- **papel nos estudos** — resultado [E11](../../mapa/conhecimento/experimentos.md#e11)
