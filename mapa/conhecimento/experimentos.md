# Experimentos

Os experimentos pré-registrados do estudo (E1–E16). Cada um liga pré-registro, executor, adjudicação, testes e resultados.

← [MAPA.md](../../MAPA.md) · [Rodadas do laboratório](../../mapa/conhecimento/rodadas.md) · [Hipóteses](../../mapa/conhecimento/hipoteses.md) · [Perguntas estratégicas](../../mapa/conhecimento/perguntas.md) · [Sistemas avaliados](../../mapa/conhecimento/sistemas.md) · [Revisões adversariais](../../mapa/conhecimento/revisoes.md) · [Temas](../../mapa/conhecimento/temas.md) · [Testes](../../mapa/conhecimento/testes.md) · [Lacunas e ideias](../../mapa/conhecimento/lacunas.md)

**18** itens: [E1](../../mapa/conhecimento/experimentos.md#e1) [E2](../../mapa/conhecimento/experimentos.md#e2) [E2b](../../mapa/conhecimento/experimentos.md#e2b) [E3](../../mapa/conhecimento/experimentos.md#e3) [E4](../../mapa/conhecimento/experimentos.md#e4) [E5](../../mapa/conhecimento/experimentos.md#e5) [E6](../../mapa/conhecimento/experimentos.md#e6) [E7](../../mapa/conhecimento/experimentos.md#e7) [E8](../../mapa/conhecimento/experimentos.md#e8) [E9](../../mapa/conhecimento/experimentos.md#e9) [E10](../../mapa/conhecimento/experimentos.md#e10) [E10b](../../mapa/conhecimento/experimentos.md#e10b) [E11](../../mapa/conhecimento/experimentos.md#e11) [E12](../../mapa/conhecimento/experimentos.md#e12) [E13](../../mapa/conhecimento/experimentos.md#e13) [E14](../../mapa/conhecimento/experimentos.md#e14) [E15](../../mapa/conhecimento/experimentos.md#e15) [E16](../../mapa/conhecimento/experimentos.md#e16)

| id | título | executa | pré-registro | resultados | outras peças |
|---|---|---|---|---:|---|
| [E1](../../mapa/conhecimento/experimentos.md#e1) | Piloto, tarefa de triagem: Jev contra regra simples, no corpus pré-registrado. | [run_e1_triagem.py](../../executor/run_e1_triagem.py) | [preregistro-E1-triagem.md](../../planning/preregistro-E1-triagem.md#L1) | 1 |  |
| [E2](../../mapa/conhecimento/experimentos.md#e2) | Fatorial 2x2x2 separando lote, ordem das opções e distração. | [run_e2_fatorial.py](../../executor/run_e2_fatorial.py) |  | 1 |  |
| [E2b](../../mapa/conhecimento/experimentos.md#e2b) | Desconfunde posição no lote e identidade do caso. | [run_e2b_posicao.py](../../executor/run_e2b_posicao.py) |  | 1 |  |
| [E3](../../mapa/conhecimento/experimentos.md#e3) | Relação afirmação/evidência em três classes, com o contraste que mais custa caro. | [run_e3_evidencia.py](../../executor/run_e3_evidencia.py) |  | 1 |  |
| [E4](../../mapa/conhecimento/experimentos.md#e4) | (pergunta P2): a seleção de fontes preserva as ressalvas necessárias? | [run_e4_ressalvas.py](../../executor/run_e4_ressalvas.py) |  | 1 |  |
| [E5](../../mapa/conhecimento/experimentos.md#e5) | (pergunta P6): OpenRouter contra TypeSafe direto, nos mesmos casos. | [run_e5_provedores.py](../../executor/run_e5_provedores.py) |  | 1 |  |
| [E6](../../mapa/conhecimento/experimentos.md#e6) | O mesmo caso, sozinho, repetido. Separa instabilidade do modelo de efeito do lote. | [run_e6_repetibilidade.py](../../executor/run_e6_repetibilidade.py) |  | 1 |  |
| [E7](../../mapa/conhecimento/experimentos.md#e7) | Conjunto de confirmação da triagem, em casos que não guiaram o desenho. | [run_e7_confirmacao.py](../../executor/run_e7_confirmacao.py) | [preregistro-E7-confirmacao.md](../../planning/preregistro-E7-confirmacao.md#L1) | 1 |  |
| [E8](../../mapa/conhecimento/experimentos.md#e8) | Segundo anotador independente e cego sobre o gabarito dos 80 casos. | [run_e8_anotador.py](../../executor/run_e8_anotador.py) |  | 6 |  |
| [E9](../../mapa/conhecimento/experimentos.md#e9) | O que acontece com o desempenho quando a distribuição de classes não é a do corpus. | [run_e9_prevalencia.py](../../executor/run_e9_prevalencia.py) |  | 1 |  |
| [E10](../../mapa/conhecimento/experimentos.md#e10) | O braço do LLM econômico, que faltava desde o plano original. | [run_e10_llm_economico.py](../../executor/run_e10_llm_economico.py) | [preregistro-E10-llm-economico.md](../../planning/preregistro-E10-llm-economico.md#L1) | 1 |  |
| [E10b](../../mapa/conhecimento/experimentos.md#e10b) | O mesmo comparador econômico nas 10 famílias do piloto, para dobrar o poder. | [run_e10b_piloto.py](../../executor/run_e10b_piloto.py) |  | 1 |  |
| [E11](../../mapa/conhecimento/experimentos.md#e11) | O desempate entre o Jev e o LLM econômico, em corpus novo e pré-registrado. | [run_e11_desempate.py](../../executor/run_e11_desempate.py) | [preregistro-E11-desempate.md](../../planning/preregistro-E11-desempate.md#L1) | 7 | adjudica: [adjudicar_e11.py](../../executor/adjudicar_e11.py) |
| [E12](../../mapa/conhecimento/experimentos.md#e12) | A replicação do desempate com 30 famílias novas e quatro comparadores econômicos. | [run_e12_replicacao.py](../../executor/run_e12_replicacao.py) | [preregistro-E12-replicacao.md](../../planning/preregistro-E12-replicacao.md#L1) | 7 | adjudica: [adjudicar_e12.py](../../executor/adjudicar_e12.py), testa: [test_calibracao_e12.py](../../executor/tests/test_calibracao_e12.py), testa: [test_e12_replicacao.py](../../executor/tests/test_e12_replicacao.py) |
| [E13](../../mapa/conhecimento/experimentos.md#e13) | Integração com tráfego real do Igor: amostragem, gabaritos e relatórios agregados (integra |  |  | 0 | define: [README.md](../../integracao/README.md) |
| [E14](../../mapa/conhecimento/experimentos.md#e14) | Programa de rodadas do laboratório, R0 a R27 (laboratorio/). |  | [PREREGISTRO.md](../../laboratorio/PREREGISTRO.md#L1) | 0 |  |
| [E15](../../mapa/conhecimento/experimentos.md#e15) | Preregistered real-call evaluation; public code excerpts and labelled synthetic cases. | [run_e15.py](../../executor/run_e15.py) | [preregistro-E15-implantacao.md](../../planning/preregistro-E15-implantacao.md#L1) | 0 | emenda: [emenda-E15-01.md](../../planning/emenda-E15-01.md) |
| [E16](../../mapa/conhecimento/experimentos.md#e16) | Real repository retrieval experiment with a frozen lexical comparator. | [run_e16.py](../../executor/run_e16.py) | [preregistro-E16-recuperacao.md](../../planning/preregistro-E16-recuperacao.md#L1) | 0 |  |

## Itens

<a id="e1"></a>

### E1 — Piloto, tarefa de triagem: Jev contra regra simples, no corpus pré-registrado.

- **emendas:** Emenda 1 — 2026-09-19
- **onde está:** executa [executor/run_e1_triagem.py](../../executor/run_e1_triagem.py); pré-registra [planning/preregistro-E1-triagem.md:1](../../planning/preregistro-E1-triagem.md#L1); resultado [runs/e1-triagem/relatorio.json](../../runs/e1-triagem/relatorio.json)
- **sustenta:** [R0](../../mapa/conhecimento/rodadas.md#r0)
- **tema:** [T17 · corpus, desempate, pré](../../mapa/conhecimento/temas.md#t17)
- **semelhantes (julgados pelo Jev):** [E11](../../mapa/conhecimento/experimentos.md#e11) (complementar, 0.34), [executor/baseline_regra.py](../../executor/baseline_regra.py) (mesmo assunto, 0.29), [Q069](../../mapa/conhecimento/perguntas.md#q069) (mesmo assunto, 0.28), [laboratorio/r4_r7_limites.py](../../laboratorio/r4_r7_limites.py) (complementar, 0.26), [Q061](../../mapa/conhecimento/perguntas.md#q061) (mesmo assunto, 0.26)
- **mencionado em 40 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (15×), [lab/data/execution.json](../../lab/data/execution.json) (13×), [lab/index.html](../../lab/index.html) (13×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (13×), [executor/placar.py](../../executor/placar.py) (7×), [planning/preregistro-E7-confirmacao.md](../../planning/preregistro-E7-confirmacao.md) (7×), [executor/publicar_experimentos.py](../../executor/publicar_experimentos.py) (5×), [planning/preregistro-E10-llm-economico.md](../../planning/preregistro-E10-llm-economico.md) (5×), [planning/preregistro-E11-desempate.md](../../planning/preregistro-E11-desempate.md) (5×), [docs/RELATORIO-EXECUCAO-JEV-HELENA.md](../../docs/RELATORIO-EXECUCAO-JEV-HELENA.md) (4×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (3×), [executor/erro_grave.py](../../executor/erro_grave.py) (3×) … e mais 28

<a id="e2"></a>

### E2 — Fatorial 2x2x2 separando lote, ordem das opções e distração.

- **onde está:** executa [executor/run_e2_fatorial.py](../../executor/run_e2_fatorial.py); resultado [runs/e2-fatorial/relatorio.json](../../runs/e2-fatorial/relatorio.json)
- **tema:** [T06 · opções, ordem, pontos](../../mapa/conhecimento/temas.md#t06)
- **semelhantes (julgados pelo Jev):** [H021](../../mapa/conhecimento/hipoteses.md#h021) (complementar, 0.25), [R2](../../mapa/conhecimento/rodadas.md#r2) (complementar, 0.24), [H088](../../mapa/conhecimento/hipoteses.md#h088) (complementar, 0.24), [H006](../../mapa/conhecimento/hipoteses.md#h006) (complementar, 0.24)
- **mencionado em 11 arquivos:** [docs/RELATORIO-EXECUCAO-JEV-HELENA.md](../../docs/RELATORIO-EXECUCAO-JEV-HELENA.md) (4×), [lab/data/execution.json](../../lab/data/execution.json) (4×), [lab/index.html](../../lab/index.html) (4×), [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (3×), [executor/placar.py](../../executor/placar.py) (2×), [executor/publicar_experimentos.py](../../executor/publicar_experimentos.py) (2×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (2×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [docs/PLANO-CIENTIFICO-JEV-HELENA.md](../../docs/PLANO-CIENTIFICO-JEV-HELENA.md) (1×), [executor/run_e2b_posicao.py](../../executor/run_e2b_posicao.py) (1×), [planning/protocolo.md](../../planning/protocolo.md) (1×)

<a id="e2b"></a>

### E2b — Desconfunde posição no lote e identidade do caso.

- **onde está:** executa [executor/run_e2b_posicao.py](../../executor/run_e2b_posicao.py); resultado [runs/e2b-posicao/relatorio.json](../../runs/e2b-posicao/relatorio.json)
- **sustenta:** [R2](../../mapa/conhecimento/rodadas.md#r2)
- **semelhantes (julgados pelo Jev):** [Q028](../../mapa/conhecimento/perguntas.md#q028) (mesmo assunto, 0.24), [E6](../../mapa/conhecimento/experimentos.md#e6) (complementar, 0.23)
- **mencionado em 10 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (4×), [lab/data/execution.json](../../lab/data/execution.json) (4×), [lab/index.html](../../lab/index.html) (4×), [docs/RELATORIO-EXECUCAO-JEV-HELENA.md](../../docs/RELATORIO-EXECUCAO-JEV-HELENA.md) (3×), [executor/placar.py](../../executor/placar.py) (2×), [laboratorio/PREREGISTRO.md](../../laboratorio/PREREGISTRO.md) (2×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (2×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [executor/publicar_experimentos.py](../../executor/publicar_experimentos.py) (1×), [executor/run_e6_repetibilidade.py](../../executor/run_e6_repetibilidade.py) (1×)

<a id="e3"></a>

### E3 — Relação afirmação/evidência em três classes, com o contraste que mais custa caro.

- **onde está:** executa [executor/run_e3_evidencia.py](../../executor/run_e3_evidencia.py); resultado [runs/e3-evidencia/relatorio.json](../../runs/e3-evidencia/relatorio.json)
- **semelhantes (julgados pelo Jev):** [laboratorio/gerar_dossie.py](../../laboratorio/gerar_dossie.py) (complementar, 0.31)
- **mencionado em 16 arquivos:** [docs/RELATORIO-EXECUCAO-JEV-HELENA.md](../../docs/RELATORIO-EXECUCAO-JEV-HELENA.md) (3×), [executor/placar.py](../../executor/placar.py) (3×), [lab/data/execution.json](../../lab/data/execution.json) (3×), [lab/index.html](../../lab/index.html) (3×), [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (2×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (2×), [docs/CAMADAS-CLAUDE-CODE.md](../../docs/CAMADAS-CLAUDE-CODE.md) (1×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [docs/PLANO-CIENTIFICO-JEV-HELENA.md](../../docs/PLANO-CIENTIFICO-JEV-HELENA.md) (1×), [executor/gabarito.py](../../executor/gabarito.py) (1×), [integracao/README.md](../../integracao/README.md) (1×), [integracao/avaliacao/variantes.py](../../integracao/avaliacao/variantes.py) (1×) … e mais 4

<a id="e4"></a>

### E4 — (pergunta P2): a seleção de fontes preserva as ressalvas necessárias?

- **onde está:** executa [executor/run_e4_ressalvas.py](../../executor/run_e4_ressalvas.py); resultado [runs/e4-ressalvas/relatorio.json](../../runs/e4-ressalvas/relatorio.json)
- **tema:** [T07 · importa, contexto, caracteres](../../mapa/conhecimento/temas.md#t07)
- **semelhantes (julgados pelo Jev):** [H055](../../mapa/conhecimento/hipoteses.md#h055) (complementar, 0.23), [H056](../../mapa/conhecimento/hipoteses.md#h056) (complementar, 0.22), [integracao/camadas/verificar.py](../../integracao/camadas/verificar.py) (complementar, 0.21), [H060](../../mapa/conhecimento/hipoteses.md#h060) (complementar, 0.20)
- **mencionado em 11 arquivos:** [docs/RELATORIO-EXECUCAO-JEV-HELENA.md](../../docs/RELATORIO-EXECUCAO-JEV-HELENA.md) (4×), [executor/publicar_experimentos.py](../../executor/publicar_experimentos.py) (4×), [docs/PLANO-CIENTIFICO-JEV-HELENA.md](../../docs/PLANO-CIENTIFICO-JEV-HELENA.md) (3×), [lab/data/execution.json](../../lab/data/execution.json) (3×), [lab/index.html](../../lab/index.html) (3×), [planning/protocolo.md](../../planning/protocolo.md) (3×), [executor/placar.py](../../executor/placar.py) (2×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (2×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (1×), [executor/tests/test_coerencia_placar.py](../../executor/tests/test_coerencia_placar.py) (1×)

<a id="e5"></a>

### E5 — (pergunta P6): OpenRouter contra TypeSafe direto, nos mesmos casos.

- **onde está:** executa [executor/run_e5_provedores.py](../../executor/run_e5_provedores.py); resultado [runs/e5-provedores/relatorio.json](../../runs/e5-provedores/relatorio.json)
- **mencionado em 13 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (2×), [executor/placar.py](../../executor/placar.py) (2×), [lab/data/execution.json](../../lab/data/execution.json) (2×), [lab/index.html](../../lab/index.html) (2×), [README.md](../../README.md) (1×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [docs/PLANO-CIENTIFICO-JEV-HELENA.md](../../docs/PLANO-CIENTIFICO-JEV-HELENA.md) (1×), [docs/RELATORIO-EXECUCAO-JEV-HELENA.md](../../docs/RELATORIO-EXECUCAO-JEV-HELENA.md) (1×), [executor/credenciais.py](../../executor/credenciais.py) (1×), [executor/publicar_experimentos.py](../../executor/publicar_experimentos.py) (1×), [hermes/jev_hermes/nucleo.py](../../hermes/jev_hermes/nucleo.py) (1×), [integracao/README.md](../../integracao/README.md) (1×) … e mais 1

<a id="e6"></a>

### E6 — O mesmo caso, sozinho, repetido. Separa instabilidade do modelo de efeito do lote.

- **onde está:** executa [executor/run_e6_repetibilidade.py](../../executor/run_e6_repetibilidade.py); resultado [runs/e6-repetibilidade/relatorio.json](../../runs/e6-repetibilidade/relatorio.json)
- **sustenta:** [Q029](../../mapa/conhecimento/perguntas.md#q029)
- **semelhantes (julgados pelo Jev):** [E2b](../../mapa/conhecimento/experimentos.md#e2b) (complementar, 0.23)
- **mencionado em 9 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (3×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (2×), [executor/placar.py](../../executor/placar.py) (2×), [lab/data/execution.json](../../lab/data/execution.json) (2×), [lab/index.html](../../lab/index.html) (2×), [docs/CEM-PERGUNTAS-ESTRATEGICAS.md](../../docs/CEM-PERGUNTAS-ESTRATEGICAS.md) (1×), [laboratorio/q100/respostas.py](../../laboratorio/q100/respostas.py) (1×), [laboratorio/r24_votacao.py](../../laboratorio/r24_votacao.py) (1×), [planning/preregistro-E12-replicacao.md](../../planning/preregistro-E12-replicacao.md) (1×)

<a id="e7"></a>

### E7 — Conjunto de confirmação da triagem, em casos que não guiaram o desenho.

- **onde está:** executa [executor/run_e7_confirmacao.py](../../executor/run_e7_confirmacao.py); pré-registra [planning/preregistro-E7-confirmacao.md:1](../../planning/preregistro-E7-confirmacao.md#L1); resultado [runs/e7-confirmacao/relatorio.json](../../runs/e7-confirmacao/relatorio.json)
- **sustenta:** [R0](../../mapa/conhecimento/rodadas.md#r0)
- **mencionado em 20 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (16×), [lab/data/execution.json](../../lab/data/execution.json) (10×), [lab/index.html](../../lab/index.html) (10×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (7×), [executor/placar.py](../../executor/placar.py) (5×), [executor/run_e10_llm_economico.py](../../executor/run_e10_llm_economico.py) (2×), [executor/run_e9_prevalencia.py](../../executor/run_e9_prevalencia.py) (2×), [executor/tests/test_coerencia_placar.py](../../executor/tests/test_coerencia_placar.py) (2×), [laboratorio/r0_calibracao.py](../../laboratorio/r0_calibracao.py) (2×), [planning/preregistro-E10-llm-economico.md](../../planning/preregistro-E10-llm-economico.md) (2×), [README.md](../../README.md) (1×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×) … e mais 8

<a id="e8"></a>

### E8 — Segundo anotador independente e cego sobre o gabarito dos 80 casos.

- **onde está:** executa [executor/run_e8_anotador.py](../../executor/run_e8_anotador.py); resultado [runs/e8-anotador/adjudicacao-bruta.jsonl](../../runs/e8-anotador/adjudicacao-bruta.jsonl); resultado [runs/e8-anotador/adjudicacao-mapa.json](../../runs/e8-anotador/adjudicacao-mapa.json); resultado [runs/e8-anotador/adjudicacao.json](../../runs/e8-anotador/adjudicacao.json); resultado [runs/e8-anotador/casos-cegos.json](../../runs/e8-anotador/casos-cegos.json); resultado [runs/e8-anotador/prompt-adjudicacao.txt](../../runs/e8-anotador/prompt-adjudicacao.txt); resultado [runs/e8-anotador/relatorio.json](../../runs/e8-anotador/relatorio.json)
- **sustenta:** [Q067](../../mapa/conhecimento/perguntas.md#q067)
- **tema:** [T18 · anotador, independente, justificativa](../../mapa/conhecimento/temas.md#t18)
- **semelhantes (julgados pelo Jev):** [Q004](../../mapa/conhecimento/perguntas.md#q004) (mesmo assunto, 0.31), [H033](../../mapa/conhecimento/hipoteses.md#h033) (complementar, 0.26), [H024](../../mapa/conhecimento/hipoteses.md#h024) (complementar, 0.25)
- **mencionado em 20 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (15×), [lab/data/execution.json](../../lab/data/execution.json) (11×), [lab/index.html](../../lab/index.html) (11×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (11×), [executor/tests/test_coerencia_placar.py](../../executor/tests/test_coerencia_placar.py) (10×), [executor/placar.py](../../executor/placar.py) (6×), [executor/gabarito.py](../../executor/gabarito.py) (5×), [docs/CEM-PERGUNTAS-ESTRATEGICAS.md](../../docs/CEM-PERGUNTAS-ESTRATEGICAS.md) (1×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [executor/run_e12_replicacao.py](../../executor/run_e12_replicacao.py) (1×), [executor/tests/test_achados_revisao16.py](../../executor/tests/test_achados_revisao16.py) (1×), [executor/tests/test_achados_revisao4.py](../../executor/tests/test_achados_revisao4.py) (1×) … e mais 8

<a id="e9"></a>

### E9 — O que acontece com o desempenho quando a distribuição de classes não é a do corpus.

- **onde está:** executa [executor/run_e9_prevalencia.py](../../executor/run_e9_prevalencia.py); resultado [runs/e9-prevalencia/relatorio.json](../../runs/e9-prevalencia/relatorio.json)
- **sustenta:** [Q030](../../mapa/conhecimento/perguntas.md#q030)
- **tema:** [T17 · corpus, desempate, pré](../../mapa/conhecimento/temas.md#t17)
- **semelhantes (julgados pelo Jev):** [E11](../../mapa/conhecimento/experimentos.md#e11) (complementar, 0.28), [H027](../../mapa/conhecimento/hipoteses.md#h027) (complementar, 0.23)
- **mencionado em 13 arquivos:** [executor/placar.py](../../executor/placar.py) (4×), [lab/data/execution.json](../../lab/data/execution.json) (4×), [lab/index.html](../../lab/index.html) (4×), [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (3×), [README.md](../../README.md) (1×), [docs/CEM-PERGUNTAS-ESTRATEGICAS.md](../../docs/CEM-PERGUNTAS-ESTRATEGICAS.md) (1×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [docs/RELATORIO-EXECUCAO-JEV-HELENA.md](../../docs/RELATORIO-EXECUCAO-JEV-HELENA.md) (1×), [executor/tests/test_achados_revisao4.py](../../executor/tests/test_achados_revisao4.py) (1×), [executor/tests/test_coerencia_placar.py](../../executor/tests/test_coerencia_placar.py) (1×), [laboratorio/q100/respostas.py](../../laboratorio/q100/respostas.py) (1×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (1×) … e mais 1

<a id="e10"></a>

### E10 — O braço do LLM econômico, que faltava desde o plano original.

- **emendas:** Emenda 1 — 2026-09-19, depois do resultado primário e antes da execução do E10b
- **onde está:** executa [executor/run_e10_llm_economico.py](../../executor/run_e10_llm_economico.py); pré-registra [planning/preregistro-E10-llm-economico.md:1](../../planning/preregistro-E10-llm-economico.md#L1); resultado [runs/e10-llm-economico/relatorio.json](../../runs/e10-llm-economico/relatorio.json)
- **sustenta:** [R9](../../mapa/conhecimento/rodadas.md#r9), [R10](../../mapa/conhecimento/rodadas.md#r10), [R14](../../mapa/conhecimento/rodadas.md#r14), [Q004](../../mapa/conhecimento/perguntas.md#q004), [Q064](../../mapa/conhecimento/perguntas.md#q064)
- **tema:** [T17 · corpus, desempate, pré](../../mapa/conhecimento/temas.md#t17)
- **semelhantes (julgados pelo Jev):** [E11](../../mapa/conhecimento/experimentos.md#e11) (complementar, 0.24)
- **mencionado em 21 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (11×), [executor/placar.py](../../executor/placar.py) (7×), [planning/preregistro-E12-replicacao.md](../../planning/preregistro-E12-replicacao.md) (6×), [executor/run_e10b_piloto.py](../../executor/run_e10b_piloto.py) (4×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (4×), [lab/data/execution.json](../../lab/data/execution.json) (3×), [lab/index.html](../../lab/index.html) (3×), [laboratorio/PREREGISTRO.md](../../laboratorio/PREREGISTRO.md) (3×), [docs/CEM-PERGUNTAS-ESTRATEGICAS.md](../../docs/CEM-PERGUNTAS-ESTRATEGICAS.md) (2×), [docs/LIMITES-DO-JEV.md](../../docs/LIMITES-DO-JEV.md) (2×), [executor/tests/test_coerencia_placar.py](../../executor/tests/test_coerencia_placar.py) (2×), [laboratorio/q100/respostas.py](../../laboratorio/q100/respostas.py) (2×) … e mais 9

<a id="e10b"></a>

### E10b — O mesmo comparador econômico nas 10 famílias do piloto, para dobrar o poder.

- **onde está:** executa [executor/run_e10b_piloto.py](../../executor/run_e10b_piloto.py); resultado [runs/e10b-piloto/relatorio.json](../../runs/e10b-piloto/relatorio.json)
- **semelhantes (julgados pelo Jev):** [E12](../../mapa/conhecimento/experimentos.md#e12) (mesmo assunto, 0.34), [integracao/avaliacao/rodar.py](../../integracao/avaliacao/rodar.py) (complementar, 0.23), [R20](../../mapa/conhecimento/rodadas.md#r20) (complementar, 0.22)
- **mencionado em 10 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (4×), [executor/placar.py](../../executor/placar.py) (3×), [lab/data/execution.json](../../lab/data/execution.json) (3×), [lab/index.html](../../lab/index.html) (3×), [planning/preregistro-E10-llm-economico.md](../../planning/preregistro-E10-llm-economico.md) (3×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [executor/publicar_experimentos.py](../../executor/publicar_experimentos.py) (1×), [executor/run_e11_desempate.py](../../executor/run_e11_desempate.py) (1×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (1×), [planning/preregistro-E11-desempate.md](../../planning/preregistro-E11-desempate.md) (1×)

<a id="e11"></a>

### E11 — O desempate entre o Jev e o LLM econômico, em corpus novo e pré-registrado.

- **emendas:** Emenda 2 — 2026-09-19, antes de rodar o terceiro juiz nos 10 desacordos
- **onde está:** adjudica [executor/adjudicar_e11.py](../../executor/adjudicar_e11.py); executa [executor/run_e11_desempate.py](../../executor/run_e11_desempate.py); pré-registra [planning/preregistro-E11-desempate.md:1](../../planning/preregistro-E11-desempate.md#L1); resultado [runs/e11-desempate/adjudicacao-bruta.jsonl](../../runs/e11-desempate/adjudicacao-bruta.jsonl); resultado [runs/e11-desempate/adjudicacao-mapa.json](../../runs/e11-desempate/adjudicacao-mapa.json); resultado [runs/e11-desempate/adjudicacao.json](../../runs/e11-desempate/adjudicacao.json); resultado [runs/e11-desempate/casos-cegos.json](../../runs/e11-desempate/casos-cegos.json); resultado [runs/e11-desempate/prompt-adjudicacao.txt](../../runs/e11-desempate/prompt-adjudicacao.txt); resultado [runs/e11-desempate/relatorio.json](../../runs/e11-desempate/relatorio.json); resultado [runs/e11-desempate/respostas.jsonl](../../runs/e11-desempate/respostas.jsonl)
- **sustenta:** [R0](../../mapa/conhecimento/rodadas.md#r0), [R9](../../mapa/conhecimento/rodadas.md#r9), [R10](../../mapa/conhecimento/rodadas.md#r10), [R26](../../mapa/conhecimento/rodadas.md#r26), [Q004](../../mapa/conhecimento/perguntas.md#q004), [Q064](../../mapa/conhecimento/perguntas.md#q064)
- **tema:** [T17 · corpus, desempate, pré](../../mapa/conhecimento/temas.md#t17)
- **semelhantes (julgados pelo Jev):** [E1](../../mapa/conhecimento/experimentos.md#e1) (complementar, 0.34), [planning/preregistro-E10-llm-economico.md](../../planning/preregistro-E10-llm-economico.md) (complementar, 0.30), [E9](../../mapa/conhecimento/experimentos.md#e9) (complementar, 0.28), [E12](../../mapa/conhecimento/experimentos.md#e12) (mesmo assunto, 0.25), [E10](../../mapa/conhecimento/experimentos.md#e10) (complementar, 0.24), [hermes/plugin/jev-camadas/__init__.py](../../hermes/plugin/jev-camadas/__init__.py) (complementar, 0.21)
- **mencionado em 30 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (17×), [executor/placar.py](../../executor/placar.py) (11×), [executor/tests/test_coerencia_placar.py](../../executor/tests/test_coerencia_placar.py) (8×), [lab/data/execution.json](../../lab/data/execution.json) (6×), [lab/index.html](../../lab/index.html) (6×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (6×), [planning/preregistro-E12-replicacao.md](../../planning/preregistro-E12-replicacao.md) (6×), [laboratorio/PREREGISTRO.md](../../laboratorio/PREREGISTRO.md) (3×), [docs/CEM-PERGUNTAS-ESTRATEGICAS.md](../../docs/CEM-PERGUNTAS-ESTRATEGICAS.md) (2×), [executor/run_e12_replicacao.py](../../executor/run_e12_replicacao.py) (2×), [laboratorio/q100/respostas.py](../../laboratorio/q100/respostas.py) (2×), [laboratorio/r0_calibracao.py](../../laboratorio/r0_calibracao.py) (2×) … e mais 18

<a id="e12"></a>

### E12 — A replicação do desempate com 30 famílias novas e quatro comparadores econômicos.

- **onde está:** adjudica [executor/adjudicar_e12.py](../../executor/adjudicar_e12.py); executa [executor/run_e12_replicacao.py](../../executor/run_e12_replicacao.py); testa [executor/tests/test_calibracao_e12.py](../../executor/tests/test_calibracao_e12.py); testa [executor/tests/test_e12_replicacao.py](../../executor/tests/test_e12_replicacao.py); pré-registra [planning/preregistro-E12-replicacao.md:1](../../planning/preregistro-E12-replicacao.md#L1); resultado [runs/e12-replicacao/adjudicacao-mapa.json](../../runs/e12-replicacao/adjudicacao-mapa.json); resultado [runs/e12-replicacao/adjudicacao.json](../../runs/e12-replicacao/adjudicacao.json); resultado [runs/e12-replicacao/anuladas-emenda-3.json](../../runs/e12-replicacao/anuladas-emenda-3.json); resultado [runs/e12-replicacao/casos-cegos.json](../../runs/e12-replicacao/casos-cegos.json); resultado [runs/e12-replicacao/prompt-adjudicacao.txt](../../runs/e12-replicacao/prompt-adjudicacao.txt); resultado [runs/e12-replicacao/relatorio.json](../../runs/e12-replicacao/relatorio.json); resultado [runs/e12-replicacao/respostas.jsonl](../../runs/e12-replicacao/respostas.jsonl)
- **sustenta:** [R0](../../mapa/conhecimento/rodadas.md#r0), [R1](../../mapa/conhecimento/rodadas.md#r1), [R2](../../mapa/conhecimento/rodadas.md#r2), [R3](../../mapa/conhecimento/rodadas.md#r3), [R5](../../mapa/conhecimento/rodadas.md#r5), [R7](../../mapa/conhecimento/rodadas.md#r7), [R8](../../mapa/conhecimento/rodadas.md#r8), [R9](../../mapa/conhecimento/rodadas.md#r9), [R10](../../mapa/conhecimento/rodadas.md#r10), [Q004](../../mapa/conhecimento/perguntas.md#q004), [Q064](../../mapa/conhecimento/perguntas.md#q064), [Q078](../../mapa/conhecimento/perguntas.md#q078)
- **semelhantes (julgados pelo Jev):** [E10b](../../mapa/conhecimento/experimentos.md#e10b) (mesmo assunto, 0.34), [executor/run_e10b_piloto.py](../../executor/run_e10b_piloto.py) (mesmo assunto, 0.28), [E11](../../mapa/conhecimento/experimentos.md#e11) (mesmo assunto, 0.25), [integracao/avaliacao/rodar.py](../../integracao/avaliacao/rodar.py) (complementar, 0.24)
- **mencionado em 37 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (24×), [executor/tests/test_achados_revisao16.py](../../executor/tests/test_achados_revisao16.py) (11×), [laboratorio/PREREGISTRO.md](../../laboratorio/PREREGISTRO.md) (11×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (9×), [executor/placar.py](../../executor/placar.py) (5×), [README.md](../../README.md) (4×), [docs/CEM-PERGUNTAS-ESTRATEGICAS.md](../../docs/CEM-PERGUNTAS-ESTRATEGICAS.md) (4×), [laboratorio/q100/respostas.py](../../laboratorio/q100/respostas.py) (4×), [executor/prices.json](../../executor/prices.json) (3×), [laboratorio/r0_calibracao.py](../../laboratorio/r0_calibracao.py) (3×), [output/mapa-de-limites.html](../../output/mapa-de-limites.html) (3×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (2×) … e mais 25

<a id="e13"></a>

### E13 — Integração com tráfego real do Igor: amostragem, gabaritos e relatórios agregados (integracao/avaliacao/).

- **onde está:** define [integracao/README.md](../../integracao/README.md)
- **tema:** [T15 · integração, método, atual](../../mapa/conhecimento/temas.md#t15)
- **semelhantes (julgados pelo Jev):** [integracao/avaliacao/rodar.py](../../integracao/avaliacao/rodar.py) (complementar, 0.25), [Q005](../../mapa/conhecimento/perguntas.md#q005) (complementar, 0.21), [AGENTS.md](../../AGENTS.md) (complementar, 0.21)
- **mencionado em 7 arquivos:** [docs/RELATORIO-FINAL-JEV.md](../../docs/RELATORIO-FINAL-JEV.md) (2×), [docs/CAMADAS-CLAUDE-CODE.md](../../docs/CAMADAS-CLAUDE-CODE.md) (1×), [docs/LIMITES-DO-JEV.md](../../docs/LIMITES-DO-JEV.md) (1×), [hermes/jev_hermes/camadas.py](../../hermes/jev_hermes/camadas.py) (1×), [integracao/camadas/medir.py](../../integracao/camadas/medir.py) (1×), [laboratorio/PREREGISTRO.md](../../laboratorio/PREREGISTRO.md) (1×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (1×)

<a id="e14"></a>

### E14 — Programa de rodadas do laboratório, R0 a R27 (laboratorio/).

- **onde está:** pré-registra [laboratorio/PREREGISTRO.md:1](../../laboratorio/PREREGISTRO.md#L1)
- **sustenta:** [R14](../../mapa/conhecimento/rodadas.md#r14), [R15b](../../mapa/conhecimento/rodadas.md#r15b), [R16](../../mapa/conhecimento/rodadas.md#r16)
- **mencionado em 11 arquivos:** [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (10×), [README.md](../../README.md) (3×), [laboratorio/gerar_mapa_visual.py](../../laboratorio/gerar_mapa_visual.py) (3×), [laboratorio/mapa-de-limites.json](../../laboratorio/mapa-de-limites.json) (2×), [laboratorio/r21-prosa.json](../../laboratorio/r21-prosa.json) (2×), [output/mapa-de-limites.html](../../output/mapa-de-limites.html) (2×), [docs/LIMITES-DO-JEV.md](../../docs/LIMITES-DO-JEV.md) (1×), [executor/tests/test_coerencia_placar.py](../../executor/tests/test_coerencia_placar.py) (1×), [hermes/skill/jev/SKILL.md](../../hermes/skill/jev/SKILL.md) (1×), [laboratorio/nucleo.py](../../laboratorio/nucleo.py) (1×), [laboratorio/r15_adversario_externo.py](../../laboratorio/r15_adversario_externo.py) (1×)

<a id="e15"></a>

### E15 — Preregistered real-call evaluation; public code excerpts and labelled synthetic cases.

- **onde está:** executa [executor/run_e15.py](../../executor/run_e15.py); emenda [planning/emenda-E15-01.md:1](../../planning/emenda-E15-01.md#L1); pré-registra [planning/preregistro-E15-implantacao.md:1](../../planning/preregistro-E15-implantacao.md#L1)
- **sustenta:** [R14](../../mapa/conhecimento/rodadas.md#r14)
- **mencionado em 8 arquivos:** [planning/preregistro-E16-recuperacao.md](../../planning/preregistro-E16-recuperacao.md) (5×), [laboratorio/PREREGISTRO.md](../../laboratorio/PREREGISTRO.md) (4×), [AGENTS.md](../../AGENTS.md) (1×), [README.md](../../README.md) (1×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (1×), [docs/LIMITES-DO-JEV.md](../../docs/LIMITES-DO-JEV.md) (1×), [executor/smoke_mcp.py](../../executor/smoke_mcp.py) (1×), [laboratorio/retratacoes.json](../../laboratorio/retratacoes.json) (1×)

<a id="e16"></a>

### E16 — Real repository retrieval experiment with a frozen lexical comparator.

- **onde está:** executa [executor/run_e16.py](../../executor/run_e16.py); pré-registra [planning/preregistro-E16-recuperacao.md:1](../../planning/preregistro-E16-recuperacao.md#L1)
- **sustenta:** [R14](../../mapa/conhecimento/rodadas.md#r14), [R17](../../mapa/conhecimento/rodadas.md#r17)
- **mencionado em 7 arquivos:** [laboratorio/PREREGISTRO.md](../../laboratorio/PREREGISTRO.md) (3×), [docs/CAMADAS-CLAUDE-CODE.md](../../docs/CAMADAS-CLAUDE-CODE.md) (2×), [docs/GUIA-PRATICO-JEV.md](../../docs/GUIA-PRATICO-JEV.md) (2×), [integracao/camadas/medir.py](../../integracao/camadas/medir.py) (2×), [hermes/jev_hermes/camadas.py](../../hermes/jev_hermes/camadas.py) (1×), [integracao/camadas/busca.py](../../integracao/camadas/busca.py) (1×), [laboratorio/r17_economia_de_contexto.py](../../laboratorio/r17_economia_de_contexto.py) (1×)
