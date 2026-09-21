# runs/e8-anotador/

Resultados do experimento E8 (anotador): relatório agregado e, quando houve, adjudicação cega e respostas brutas.

← [MAPA.md](../../MAPA.md) · pasta acima: [runs](../../mapa/pastas/runs.md) · abrir a pasta: [runs/e8-anotador/](../../runs/e8-anotador)

**Outras peças do E8:** [`executor/run_e8_anotador.py`](../../executor/run_e8_anotador.py)

## Arquivos

| arquivo | tipo | tamanho | descrição |
|---|---|---:|---|
| [adjudicacao-bruta.jsonl](../../runs/e8-anotador/adjudicacao-bruta.jsonl) | dado | 9 l. | 9 registros JSONL (campos: case_id, escolha, classe, motivo) |
| [adjudicacao-mapa.json](../../runs/e8-anotador/adjudicacao-mapa.json) | dado | 65 l. | Objeto com 9 chaves: tri-f02-04, tri-f04-01, tri-f07-04, tri-f10-03, cnf-g02-03, cnf-g03-01, cnf-g03-02, cnf-g04-02, cnf-g05-02 |
| [adjudicacao.json](../../runs/e8-anotador/adjudicacao.json) | dado | 123 l. | Objeto com 8 chaves: at, terceiro_juiz, desenho, casos, placar, gabarito_adjudicado, acuracia_sob_gabarito_do_autor, acuracia_sob_gabarito_do_modelo_local |
| [casos-cegos.json](../../runs/e8-anotador/casos-cegos.json) | dado | 402 l. | Lista de 80 itens (case_id, conjunto, text) |
| [prompt-adjudicacao.txt](../../runs/e8-anotador/prompt-adjudicacao.txt) | texto | 64 l. | Voce e o terceiro juiz de um estudo de anotacao. Dois anotadores independentes classificaram as mesmas mensagens de atendimento ao cliente e divergiram em 9 ca… |
| [relatorio.json](../../runs/e8-anotador/relatorio.json) | dado | 2148 l. | Objeto com 14 chaves: at, anotador_independente, natureza, casos, respostas_validas, concordancia_bruta, kappa_cohen, n_divergencias, divergencias, acuracia_je… |

## Ligações e conteúdo de cada arquivo

### adjudicacao-bruta.jsonl

- **papel nos estudos** — resultado [E8](../../mapa/conhecimento/experimentos.md#e8)

### adjudicacao-mapa.json

- **papel nos estudos** — resultado [E8](../../mapa/conhecimento/experimentos.md#e8)

### adjudicacao.json

- **é usado por** — citação: [`executor/tests/test_coerencia_placar.py`](../../executor/tests/test_coerencia_placar.py)
- **papel nos estudos** — resultado [E8](../../mapa/conhecimento/experimentos.md#e8)

### casos-cegos.json

- **papel nos estudos** — resultado [E8](../../mapa/conhecimento/experimentos.md#e8)

### prompt-adjudicacao.txt

- **papel nos estudos** — resultado [E8](../../mapa/conhecimento/experimentos.md#e8)

### relatorio.json

- **é usado por** — citação: [`docs/RELATORIO-FINAL-JEV.md`](../../docs/RELATORIO-FINAL-JEV.md), [`laboratorio/r21-prosa.json`](../../laboratorio/r21-prosa.json)
- **papel nos estudos** — resultado [E8](../../mapa/conhecimento/experimentos.md#e8)
