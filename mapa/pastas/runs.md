# runs/

Resultados dos experimentos: um diretório por experimento com `relatorio.json` agregado; extrato do livro-caixa e erro grave. O banco `ledger.sqlite3` não é versionado.

← [MAPA.md](../../MAPA.md) · pasta acima: [raiz](../../mapa/pastas/_raiz.md) · abrir a pasta: [runs/](../../runs)

## Subpastas

| subpasta | arquivos | finalidade |
|---|---:|---|
| [canaries/](../../mapa/pastas/runs__canaries.md) | 1 | Resumo dos canários de comportamento (verificação de que o modelo servido não mudou). |
| [e1-triagem/](../../mapa/pastas/runs__e1-triagem.md) | 1 | Resultados do experimento E1 (triagem): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e10-llm-economico/](../../mapa/pastas/runs__e10-llm-economico.md) | 1 | Resultados do experimento E10 (llm economico): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e10b-piloto/](../../mapa/pastas/runs__e10b-piloto.md) | 1 | Resultados do experimento E10b (piloto): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e11-desempate/](../../mapa/pastas/runs__e11-desempate.md) | 7 | Resultados do experimento E11 (desempate): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e12-replicacao/](../../mapa/pastas/runs__e12-replicacao.md) | 7 | Resultados do experimento E12 (replicacao): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e2-fatorial/](../../mapa/pastas/runs__e2-fatorial.md) | 1 | Resultados do experimento E2 (fatorial): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e2b-posicao/](../../mapa/pastas/runs__e2b-posicao.md) | 1 | Resultados do experimento E2b (posicao): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e3-evidencia/](../../mapa/pastas/runs__e3-evidencia.md) | 1 | Resultados do experimento E3 (evidencia): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e4-ressalvas/](../../mapa/pastas/runs__e4-ressalvas.md) | 1 | Resultados do experimento E4 (ressalvas): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e5-provedores/](../../mapa/pastas/runs__e5-provedores.md) | 1 | Resultados do experimento E5 (provedores): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e6-repetibilidade/](../../mapa/pastas/runs__e6-repetibilidade.md) | 1 | Resultados do experimento E6 (repetibilidade): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e7-confirmacao/](../../mapa/pastas/runs__e7-confirmacao.md) | 1 | Resultados do experimento E7 (confirmacao): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e8-anotador/](../../mapa/pastas/runs__e8-anotador.md) | 6 | Resultados do experimento E8 (anotador): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |
| [e9-prevalencia/](../../mapa/pastas/runs__e9-prevalencia.md) | 1 | Resultados do experimento E9 (prevalencia): relatório agregado e, quando houve, adjudicação cega e respostas brutas. |

## Arquivos

| arquivo | tipo | tamanho | descrição |
|---|---|---:|---|
| [analise-pareada.json](../../runs/analise-pareada.json) | dado | 116 l. | Objeto com 9 chaves: e1_triagem, e3_evidencia, e2b_posicao, calibracao_0.9, calibracao_0.95, calibracao_0.99, calibracao_confirmacao_0.9, calibracao_confirmaca… |
| [caixa-conciliado.json](../../runs/caixa-conciliado.json) | dado | 88 l. | Objeto com 5 chaves: chamadas, usd, por_experimento, em, corte_utc |
| [erro-grave.json](../../runs/erro-grave.json) | dado | 319 l. | Objeto com 2 chaves: definicao, por_conjunto |
| [extrato-ledger.json](../../runs/extrato-ledger.json) | dado | 19174 l. | Objeto com 9 chaves: gerado_em, banco, sha256_do_banco, tentativas, comprometido_nusd, comprometido_usd, reservas_pendentes_sem_liquidacao, colunas_omitidas, l… |

## Ligações e conteúdo de cada arquivo

### analise-pareada.json

- **é usado por** — citação: [`executor/analise.py`](../../executor/analise.py), [`executor/placar.py`](../../executor/placar.py)

### caixa-conciliado.json

- **é usado por** — citação: [`integracao/camadas/rotina.py`](../../integracao/camadas/rotina.py), [`laboratorio/caixa.py`](../../laboratorio/caixa.py), [`laboratorio/conciliar_caixa.py`](../../laboratorio/conciliar_caixa.py)

### erro-grave.json

- **é usado por** — citação: [`executor/erro_grave.py`](../../executor/erro_grave.py), [`executor/placar.py`](../../executor/placar.py)
- **menciona 4 conceitos** — [E1](../../mapa/conhecimento/experimentos.md#e1) (2×), [E7](../../mapa/conhecimento/experimentos.md#e7) (1×), [E11](../../mapa/conhecimento/experimentos.md#e11) (1×), [E12](../../mapa/conhecimento/experimentos.md#e12) (1×)

### extrato-ledger.json

- **é usado por** — citação: [`README.md`](../../README.md), [`docs/RELATORIO-FINAL-JEV.md`](../../docs/RELATORIO-FINAL-JEV.md), [`executor/exportar_extrato.py`](../../executor/exportar_extrato.py), [`executor/tests/test_coerencia_placar.py`](../../executor/tests/test_coerencia_placar.py), [`integracao/camadas/rotina.py`](../../integracao/camadas/rotina.py)
