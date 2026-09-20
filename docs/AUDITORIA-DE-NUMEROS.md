# Auditoria dos números publicados

Gerado por `python laboratorio/auditoria.py --escrever`, e preso na suíte de testes
por `laboratorio/tests/test_auditoria.py` — editar um número na documentação sem o
dado que o sustente quebra a suíte.

Cada linha abaixo foi recalculada a partir das linhas brutas de resposta guardadas
em `laboratorio/*.json`, com Wilson do `statsmodels` e McNemar exato do `scipy` —
implementações **independentes** das que o laboratório usa para gerar os resumos.
A escolha é deliberada: se o Wilson de casa tivesse um defeito, todo o laboratório
herdaria esse defeito em silêncio, e só uma segunda implementação o revelaria.
(Um teste confere que as duas dão o mesmo resultado; dão.)

Uma divergência aqui significa que a documentação e o dado discordam, e o dado ganha.

**1130 de 1130 conferências fecham.**

## R1-R3 — 27 conferências, todas fecham

Acurácia e intervalo por condição de estresse — número de opções, ordem, ruído, estilo de escrita.

| | item | publicado | recalculado |
|---|---|---|---|
|  | 5-opcoes: n | `90` | `90` |
|  | 5-opcoes: acurácia | `0.9889` | `0.9889` |
|  | 5-opcoes: ic95 | `[0.9397, 0.998]` | `[0.9397, 0.998]` |
|  | 12-opcoes: n | `90` | `90` |
|  | 12-opcoes: acurácia | `0.9778` | `0.9778` |
|  | 12-opcoes: ic95 | `[0.9226, 0.9939]` | `[0.9226, 0.9939]` |
|  | 3-opcoes: n | `90` | `90` |
|  | 3-opcoes: acurácia | `0.9778` | `0.9778` |
|  | 3-opcoes: ic95 | `[0.9226, 0.9939]` | `[0.9226, 0.9939]` |
|  | 2-opcoes: n | `90` | `90` |
|  | 2-opcoes: acurácia | `0.9889` | `0.9889` |
|  | 2-opcoes: ic95 | `[0.9397, 0.998]` | `[0.9397, 0.998]` |
|  | ordem-inversa: n | `90` | `90` |
|  | ordem-inversa: acurácia | `0.9889` | `0.9889` |
|  | ordem-inversa: ic95 | `[0.9397, 0.998]` | `[0.9397, 0.998]` |
|  | ordem-sorteada: n | `90` | `90` |
|  | ordem-sorteada: acurácia | `0.9889` | `0.9889` |
|  | ordem-sorteada: ic95 | `[0.9397, 0.998]` | `[0.9397, 0.998]` |
|  | ruido-leve: n | `90` | `90` |
|  | ruido-leve: acurácia | `0.9667` | `0.9667` |
|  | ruido-leve: ic95 | `[0.9065, 0.9886]` | `[0.9065, 0.9886]` |
|  | ruido-pesado: n | `90` | `90` |
|  | ruido-pesado: acurácia | `0.9333` | `0.9333` |
|  | ruido-pesado: ic95 | `[0.8621, 0.9691]` | `[0.8621, 0.9691]` |
|  | estilo-igor: n | `90` | `90` |
|  | estilo-igor: acurácia | `0.9667` | `0.9667` |
|  | estilo-igor: ic95 | `[0.9065, 0.9886]` | `[0.9065, 0.9886]` |

## R8 — 18 conferências, todas fecham

Acurácia por família de armadilha semântica: pedido adiado, concluído, de terceiro, negado, parcial e pressuposto.

| | item | publicado | recalculado |
|---|---|---|---|
|  | A-adiado: n | `8` | `8` |
|  | A-adiado: acurácia | `1.0` | `1.0` |
|  | A-adiado: ic95 | `[0.6756, 1.0]` | `[0.6756, 1.0]` |
|  | B-concluida: n | `8` | `8` |
|  | B-concluida: acurácia | `1.0` | `1.0` |
|  | B-concluida: ic95 | `[0.6756, 1.0]` | `[0.6756, 1.0]` |
|  | C-terceiro: n | `8` | `8` |
|  | C-terceiro: acurácia | `0.75` | `0.75` |
|  | C-terceiro: ic95 | `[0.4093, 0.9285]` | `[0.4093, 0.9285]` |
|  | D-negado: n | `8` | `8` |
|  | D-negado: acurácia | `1.0` | `1.0` |
|  | D-negado: ic95 | `[0.6756, 1.0]` | `[0.6756, 1.0]` |
|  | E-parcial: n | `8` | `8` |
|  | E-parcial: acurácia | `0.875` | `0.875` |
|  | E-parcial: ic95 | `[0.5291, 0.9776]` | `[0.5291, 0.9776]` |
|  | F-pressuposto: n | `8` | `8` |
|  | F-pressuposto: acurácia | `0.875` | `0.875` |
|  | F-pressuposto: ic95 | `[0.5291, 0.9776]` | `[0.5291, 0.9776]` |

## R9 — 10 conferências, todas fecham

Acurácia sob injeção escrita dentro da mensagem do cliente, por tipo de injeção.

| | item | publicado | recalculado |
|---|---|---|---|
|  | sem-injecao: n | `10` | `10` |
|  | sem-injecao: acurácia | `1.0` | `1.0` |
|  | injecao-direta: n | `10` | `10` |
|  | injecao-direta: acurácia | `1.0` | `1.0` |
|  | injecao-autoridade: n | `10` | `10` |
|  | injecao-autoridade: acurácia | `1.0` | `1.0` |
|  | injecao-formato: n | `10` | `10` |
|  | injecao-formato: acurácia | `1.0` | `1.0` |
|  | injecao-sugestao: n | `10` | `10` |
|  | injecao-sugestao: acurácia | `1.0` | `1.0` |

## R10 — 20 conferências, todas fecham

Taxa de manipulação de cada comparador, medida contra a resposta que ele mesmo deu sem injeção — não contra o gabarito.

| | item | publicado | recalculado |
|---|---|---|---|
|  | c1: tentativas | `40` | `40` |
|  | c1: virados | `5` | `5` |
|  | c1: taxa | `0.125` | `0.125` |
|  | c1: ic95 | `[0.0546, 0.2611]` | `[0.0546, 0.2611]` |
|  | c2: tentativas | `40` | `40` |
|  | c2: virados | `0` | `0` |
|  | c2: taxa | `0.0` | `0.0` |
|  | c2: ic95 | `[0.0, 0.0876]` | `[0.0, 0.0876]` |
|  | c3: tentativas | `40` | `40` |
|  | c3: virados | `10` | `10` |
|  | c3: taxa | `0.25` | `0.25` |
|  | c3: ic95 | `[0.1419, 0.4019]` | `[0.1419, 0.4019]` |
|  | c4: tentativas | `40` | `40` |
|  | c4: virados | `28` | `28` |
|  | c4: taxa | `0.7` | `0.7` |
|  | c4: ic95 | `[0.5457, 0.8193]` | `[0.5457, 0.8193]` |
|  | jev: tentativas | `40` | `40` |
|  | jev: virados | `0` | `0` |
|  | jev: taxa | `0.0` | `0.0` |
|  | jev: ic95 | `[0.0, 0.0876]` | `[0.0, 0.0876]` |

## R11 — 80 conferências, todas fecham

Acurácia nos extremos: até 147 opções, 70% de ruído, 30 mil tokens de diluição, sobreposição de classes, troca de idioma e instrução vazia.

| | item | publicado | recalculado |
|---|---|---|---|
|  | referencia/base: n | `30` | `30` |
|  | referencia/base: sem resposta | `0` | `0` |
|  | referencia/base: acurácia | `0.9667` | `0.9667` |
|  | referencia/base: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | opcoes/40: n | `30` | `30` |
|  | opcoes/40: sem resposta | `0` | `0` |
|  | opcoes/40: acurácia | `0.9` | `0.9` |
|  | opcoes/40: ic95 | `[0.7438, 0.9654]` | `[0.7438, 0.9654]` |
|  | opcoes/80: n | `30` | `30` |
|  | opcoes/80: sem resposta | `0` | `0` |
|  | opcoes/80: acurácia | `0.9` | `0.9` |
|  | opcoes/80: ic95 | `[0.7438, 0.9654]` | `[0.7438, 0.9654]` |
|  | opcoes/147: n | `30` | `30` |
|  | opcoes/147: sem resposta | `0` | `0` |
|  | opcoes/147: acurácia | `0.9` | `0.9` |
|  | opcoes/147: ic95 | `[0.7438, 0.9654]` | `[0.7438, 0.9654]` |
|  | ruido/30%: n | `30` | `30` |
|  | ruido/30%: sem resposta | `0` | `0` |
|  | ruido/30%: acurácia | `0.8` | `0.8` |
|  | ruido/30%: ic95 | `[0.6269, 0.905]` | `[0.6269, 0.9049]` |
|  | ruido/50%: n | `30` | `30` |
|  | ruido/50%: sem resposta | `0` | `0` |
|  | ruido/50%: acurácia | `0.4667` | `0.4667` |
|  | ruido/50%: ic95 | `[0.3023, 0.6386]` | `[0.3023, 0.6386]` |
|  | ruido/70%: n | `30` | `30` |
|  | ruido/70%: sem resposta | `0` | `0` |
|  | ruido/70%: acurácia | `0.3667` | `0.3667` |
|  | ruido/70%: ic95 | `[0.2187, 0.5449]` | `[0.2187, 0.5449]` |
|  | diluicao/2k: n | `30` | `30` |
|  | diluicao/2k: sem resposta | `0` | `0` |
|  | diluicao/2k: acurácia | `0.9667` | `0.9667` |
|  | diluicao/2k: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | diluicao/8k: n | `30` | `30` |
|  | diluicao/8k: sem resposta | `0` | `0` |
|  | diluicao/8k: acurácia | `0.9667` | `0.9667` |
|  | diluicao/8k: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | diluicao/20k: n | `30` | `30` |
|  | diluicao/20k: sem resposta | `0` | `0` |
|  | diluicao/20k: acurácia | `0.2333` | `0.2333` |
|  | diluicao/20k: ic95 | `[0.1179, 0.4093]` | `[0.1179, 0.4093]` |
|  | diluicao/30k: n | `30` | `30` |
|  | diluicao/30k: sem resposta | `0` | `0` |
|  | diluicao/30k: acurácia | `0.2333` | `0.2333` |
|  | diluicao/30k: ic95 | `[0.1179, 0.4093]` | `[0.1179, 0.4093]` |
|  | sobreposicao/parcial: n | `30` | `30` |
|  | sobreposicao/parcial: sem resposta | `0` | `0` |
|  | sobreposicao/parcial: acurácia | `0.9667` | `0.9667` |
|  | sobreposicao/parcial: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | sobreposicao/total: n | `30` | `30` |
|  | sobreposicao/total: sem resposta | `0` | `0` |
|  | sobreposicao/total: acurácia | `0.9333` | `0.9333` |
|  | sobreposicao/total: ic95 | `[0.7868, 0.9815]` | `[0.7868, 0.9815]` |
|  | idioma/ingles: n | `30` | `30` |
|  | idioma/ingles: sem resposta | `0` | `0` |
|  | idioma/ingles: acurácia | `0.9667` | `0.9667` |
|  | idioma/ingles: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | idioma/misto: n | `30` | `30` |
|  | idioma/misto: sem resposta | `0` | `0` |
|  | idioma/misto: acurácia | `0.9667` | `0.9667` |
|  | idioma/misto: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | idioma/sem-acento: n | `30` | `30` |
|  | idioma/sem-acento: sem resposta | `0` | `0` |
|  | idioma/sem-acento: acurácia | `0.9667` | `0.9667` |
|  | idioma/sem-acento: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | instrucao/curta: n | `30` | `30` |
|  | instrucao/curta: sem resposta | `0` | `0` |
|  | instrucao/curta: acurácia | `0.9667` | `0.9667` |
|  | instrucao/curta: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | instrucao/vazia: n | `0` | `0` |
|  | instrucao/vazia: sem resposta | `30` | `30` |
|  | instrucao/vazia: acurácia | `None` | `None` |
|  | instrucao/vazia: ic95 | `[None, None]` | `[None, None]` |
|  | instrucao/contraditoria: n | `30` | `30` |
|  | instrucao/contraditoria: sem resposta | `0` | `0` |
|  | instrucao/contraditoria: acurácia | `0.9667` | `0.9667` |
|  | instrucao/contraditoria: ic95 | `[0.8333, 0.9941]` | `[0.8333, 0.9941]` |
|  | combinado/ruido50+160opcoes+8k: n | `30` | `30` |
|  | combinado/ruido50+160opcoes+8k: sem resposta | `0` | `0` |
|  | combinado/ruido50+160opcoes+8k: acurácia | `0.2333` | `0.2333` |
|  | combinado/ruido50+160opcoes+8k: ic95 | `[0.1179, 0.4093]` | `[0.1179, 0.4093]` |

## R15 — 20 conferências, todas fecham

Taxa de virada de cada modelo sob os 12 vetores adversariais escritos por três LLMs que não sou eu.

| | item | publicado | recalculado |
|---|---|---|---|
|  | jev: n | `120` | `120` |
|  | jev: manipulado | `10` | `10` |
|  | jev: taxa | `0.0833` | `0.0833` |
|  | jev: ic95 | `[0.0459, 0.1466]` | `[0.0459, 0.1466]` |
|  | c1: n | `120` | `120` |
|  | c1: manipulado | `25` | `25` |
|  | c1: taxa | `0.2083` | `0.2083` |
|  | c1: ic95 | `[0.1453, 0.2895]` | `[0.1453, 0.2895]` |
|  | c2: n | `120` | `120` |
|  | c2: manipulado | `13` | `13` |
|  | c2: taxa | `0.1083` | `0.1083` |
|  | c2: ic95 | `[0.0644, 0.1766]` | `[0.0644, 0.1766]` |
|  | c3: n | `66` | `66` |
|  | c3: manipulado | `4` | `4` |
|  | c3: taxa | `0.0606` | `0.0606` |
|  | c3: ic95 | `[0.0238, 0.1457]` | `[0.0238, 0.1457]` |
|  | c4: n | `68` | `68` |
|  | c4: manipulado | `2` | `2` |
|  | c4: taxa | `0.0294` | `0.0294` |
|  | c4: ic95 | `[0.0081, 0.101]` | `[0.0081, 0.101]` |

## R15b — 45 conferências, todas fecham

A separação que salvou a afirmação de imunidade: meta-instrução (família A) contra conteúdo inserido (família B).

| | item | publicado | recalculado |
|---|---|---|---|
|  | jev: viradas | `10` | `10` |
|  | jev: maior confiança de virada | `0.8` | `0.8` |
|  | jev: viradas acima do corte | `0` | `0` |
|  | jev: viradas família A | `0` | `0` |
|  | jev: viradas família B | `10` | `10` |
|  | família A/jev: n | `50` | `50` |
|  | família A/jev: virou | `0` | `0` |
|  | família A/jev: taxa | `0.0` | `0.0` |
|  | família A/jev: virou acima do corte | `0` | `0` |
|  | família A/c1: n | `50` | `50` |
|  | família A/c1: virou | `8` | `8` |
|  | família A/c1: taxa | `0.16` | `0.16` |
|  | família A/c1: virou acima do corte | `8` | `8` |
|  | família A/c2: n | `50` | `50` |
|  | família A/c2: virou | `5` | `5` |
|  | família A/c2: taxa | `0.1` | `0.1` |
|  | família A/c2: virou acima do corte | `5` | `5` |
|  | família A/c3: n | `28` | `28` |
|  | família A/c3: virou | `1` | `1` |
|  | família A/c3: taxa | `0.0357` | `0.0357` |
|  | família A/c3: virou acima do corte | `1` | `1` |
|  | família A/c4: n | `36` | `36` |
|  | família A/c4: virou | `0` | `0` |
|  | família A/c4: taxa | `0.0` | `0.0` |
|  | família A/c4: virou acima do corte | `0` | `0` |
|  | família B/jev: n | `70` | `70` |
|  | família B/jev: virou | `10` | `10` |
|  | família B/jev: taxa | `0.1429` | `0.1429` |
|  | família B/jev: virou acima do corte | `0` | `0` |
|  | família B/c1: n | `70` | `70` |
|  | família B/c1: virou | `17` | `17` |
|  | família B/c1: taxa | `0.2429` | `0.2429` |
|  | família B/c1: virou acima do corte | `13` | `13` |
|  | família B/c2: n | `70` | `70` |
|  | família B/c2: virou | `8` | `8` |
|  | família B/c2: taxa | `0.1143` | `0.1143` |
|  | família B/c2: virou acima do corte | `8` | `8` |
|  | família B/c3: n | `38` | `38` |
|  | família B/c3: virou | `3` | `3` |
|  | família B/c3: taxa | `0.0789` | `0.0789` |
|  | família B/c3: virou acima do corte | `3` | `3` |
|  | família B/c4: n | `32` | `32` |
|  | família B/c4: virou | `2` | `2` |
|  | família B/c4: taxa | `0.0625` | `0.0625` |
|  | família B/c4: virou acima do corte | `2` | `2` |

## R16 — 20 conferências, todas fecham

Recall sobre comando irreversível e taxa de alarme falso, por formulação do guarda.

| | item | publicado | recalculado |
|---|---|---|---|
|  | A-atual: avaliados | `118` | `118` |
|  | A-atual: irreversíveis | `12` | `12` |
|  | A-atual: recall | `0.5833` | `0.5833` |
|  | A-atual: alarmes falsos | `21` | `21` |
|  | A-atual: taxa de alarme falso | `0.1981` | `0.1981` |
|  | B-rotulo-consagrado: avaliados | `120` | `120` |
|  | B-rotulo-consagrado: irreversíveis | `12` | `12` |
|  | B-rotulo-consagrado: recall | `0.5` | `0.5` |
|  | B-rotulo-consagrado: alarmes falsos | `13` | `13` |
|  | B-rotulo-consagrado: taxa de alarme falso | `0.1204` | `0.1204` |
|  | C-com-escape: avaliados | `120` | `120` |
|  | C-com-escape: irreversíveis | `12` | `12` |
|  | C-com-escape: recall | `0.6667` | `0.6667` |
|  | C-com-escape: alarmes falsos | `20` | `20` |
|  | C-com-escape: taxa de alarme falso | `0.1852` | `0.1852` |
|  | D-pergunta-do-efeito: avaliados | `120` | `120` |
|  | D-pergunta-do-efeito: irreversíveis | `12` | `12` |
|  | D-pergunta-do-efeito: recall | `0.8333` | `0.8333` |
|  | D-pergunta-do-efeito: alarmes falsos | `21` | `21` |
|  | D-pergunta-do-efeito: taxa de alarme falso | `0.1944` | `0.1944` |

## R17 — 37 conferências, todas fecham

Primeira medição de economia de contexto, com pareamento contra carregar tudo, contra o BM25 e contra sorteio.

| | item | publicado | recalculado |
|---|---|---|---|
|  | todos: n | `20` | `20` |
|  | todos: acertos | `15` | `15` |
|  | todos: taxa | `0.75` | `0.75` |
|  | todos: ic95 | `[0.5313, 0.8881]` | `[0.5313, 0.8881]` |
|  | todos: bytes | `172866` | `172866` |
|  | todos: economia | `0.0` | `0.0` |
|  | todos: alvo_no_topo | `20` | `20` |
|  | jev: n | `20` | `20` |
|  | jev: acertos | `18` | `18` |
|  | jev: taxa | `0.9` | `0.9` |
|  | jev: ic95 | `[0.699, 0.9721]` | `[0.699, 0.9721]` |
|  | jev: bytes | `47313` | `47313` |
|  | jev: economia | `0.7263` | `0.7263` |
|  | jev: alvo_no_topo | `20` | `20` |
|  | bm25: n | `20` | `20` |
|  | bm25: acertos | `14` | `14` |
|  | bm25: taxa | `0.7` | `0.7` |
|  | bm25: ic95 | `[0.481, 0.8545]` | `[0.481, 0.8545]` |
|  | bm25: bytes | `53982` | `53982` |
|  | bm25: economia | `0.6877` | `0.6877` |
|  | bm25: alvo_no_topo | `16` | `16` |
|  | sorteio: n | `20` | `20` |
|  | sorteio: acertos | `7` | `7` |
|  | sorteio: taxa | `0.35` | `0.35` |
|  | sorteio: ic95 | `[0.1812, 0.5671]` | `[0.1812, 0.5671]` |
|  | sorteio: bytes | `44041` | `44041` |
|  | sorteio: economia | `0.7452` | `0.7452` |
|  | sorteio: alvo_no_topo | `3` | `3` |
|  | jev_vs_todos: só jev | `4` | `4` |
|  | jev_vs_todos: só todos | `1` | `1` |
|  | jev_vs_todos: p | `0.375` | `0.375` |
|  | jev_vs_bm25: só jev | `4` | `4` |
|  | jev_vs_bm25: só bm25 | `0` | `0` |
|  | jev_vs_bm25: p | `0.125` | `0.125` |
|  | jev_vs_sorteio: só jev | `11` | `11` |
|  | jev_vs_sorteio: só sorteio | `0` | `0` |
|  | jev_vs_sorteio: p | `0.001` | `0.001` |

## R18 — 71 conferências, todas fecham

A mesma medição em 74 perguntas geradas e filtradas por máquina, com a curva de k e o teste do recorte com cabeçalho.

| | item | publicado | recalculado |
|---|---|---|---|
|  | todos: n | `74` | `74` |
|  | todos: acertos | `64` | `64` |
|  | todos: taxa | `0.8649` | `0.8649` |
|  | todos: ic95 | `[0.7688, 0.9249]` | `[0.7688, 0.9249]` |
|  | todos: bytes | `631826` | `631826` |
|  | todos: economia | `0.0` | `0.0` |
|  | todos: alvo_presente | `74` | `74` |
|  | jev-1: n | `74` | `74` |
|  | jev-1: acertos | `68` | `68` |
|  | jev-1: taxa | `0.9189` | `0.9189` |
|  | jev-1: ic95 | `[0.8342, 0.9623]` | `[0.8342, 0.9623]` |
|  | jev-1: bytes | `78256` | `78256` |
|  | jev-1: economia | `0.8761` | `0.8761` |
|  | jev-1: alvo_presente | `70` | `70` |
|  | jev-2: n | `74` | `74` |
|  | jev-2: acertos | `69` | `69` |
|  | jev-2: taxa | `0.9324` | `0.9324` |
|  | jev-2: ic95 | `[0.8514, 0.9708]` | `[0.8514, 0.9708]` |
|  | jev-2: bytes | `161718` | `161718` |
|  | jev-2: economia | `0.744` | `0.744` |
|  | jev-2: alvo_presente | `72` | `72` |
|  | jev-3: n | `74` | `74` |
|  | jev-3: acertos | `65` | `65` |
|  | jev-3: taxa | `0.8784` | `0.8784` |
|  | jev-3: ic95 | `[0.7847, 0.9347]` | `[0.7847, 0.9347]` |
|  | jev-3: bytes | `247493` | `247493` |
|  | jev-3: economia | `0.6083` | `0.6083` |
|  | jev-3: alvo_presente | `72` | `72` |
|  | jev-5: n | `74` | `74` |
|  | jev-5: acertos | `65` | `65` |
|  | jev-5: taxa | `0.8784` | `0.8784` |
|  | jev-5: ic95 | `[0.7847, 0.9347]` | `[0.7847, 0.9347]` |
|  | jev-5: bytes | `368948` | `368948` |
|  | jev-5: economia | `0.4161` | `0.4161` |
|  | jev-5: alvo_presente | `72` | `72` |
|  | jev-cab-2: n | `74` | `74` |
|  | jev-cab-2: acertos | `66` | `66` |
|  | jev-cab-2: taxa | `0.8919` | `0.8919` |
|  | jev-cab-2: ic95 | `[0.8009, 0.9442]` | `[0.8009, 0.9442]` |
|  | jev-cab-2: bytes | `271270` | `271270` |
|  | jev-cab-2: economia | `0.5707` | `0.5707` |
|  | jev-cab-2: alvo_presente | `74` | `74` |
|  | bm25-2: n | `74` | `74` |
|  | bm25-2: acertos | `52` | `52` |
|  | bm25-2: taxa | `0.7027` | `0.7027` |
|  | bm25-2: ic95 | `[0.5907, 0.7947]` | `[0.5907, 0.7947]` |
|  | bm25-2: bytes | `187359` | `187359` |
|  | bm25-2: economia | `0.7035` | `0.7035` |
|  | bm25-2: alvo_presente | `51` | `51` |
|  | sorteio-2: n | `74` | `74` |
|  | sorteio-2: acertos | `24` | `24` |
|  | sorteio-2: taxa | `0.3243` | `0.3243` |
|  | sorteio-2: ic95 | `[0.2286, 0.4373]` | `[0.2286, 0.4373]` |
|  | sorteio-2: bytes | `152820` | `152820` |
|  | sorteio-2: economia | `0.7581` | `0.7581` |
|  | sorteio-2: alvo_presente | `19` | `19` |
|  | H18a jev-2 vs todos (resposta): só jev-2 | `7` | `7` |
|  | H18a jev-2 vs todos (resposta): só todos | `2` | `2` |
|  | H18a jev-2 vs todos (resposta): p | `0.1797` | `0.1797` |
|  | H18b jev-2 vs bm25-2 (resposta): só jev-2 | `18` | `18` |
|  | H18b jev-2 vs bm25-2 (resposta): só bm25-2 | `1` | `1` |
|  | H18b jev-2 vs bm25-2 (resposta): p | `0.0001` | `0.0001` |
|  | H18d jev-cab-2 vs jev-2 (resposta): só jev-cab-2 | `2` | `2` |
|  | H18d jev-cab-2 vs jev-2 (resposta): só jev-2 | `5` | `5` |
|  | H18d jev-cab-2 vs jev-2 (resposta): p | `0.4531` | `0.4531` |
|  | controle jev-2 vs sorteio-2: só jev-2 | `46` | `46` |
|  | controle jev-2 vs sorteio-2: só sorteio-2 | `1` | `1` |
|  | controle jev-2 vs sorteio-2: p | `0.0` | `0.0` |
|  | H18b alvo no topo: só jev-2 | `22` | `22` |
|  | H18b alvo no topo: só bm25-2 | `1` | `1` |
|  | H18b alvo no topo: p | `0.0` | `0.0` |

## R19 — 59 conferências, todas fecham

Acurácia por formulação e por molde na armadilha de sujeito, incluindo a pergunta de sujeito avaliada sozinha.

| | item | publicado | recalculado |
|---|---|---|---|
|  | A-atual: n | `85` | `85` |
|  | A-atual: acertos | `76` | `76` |
|  | A-atual: taxa | `0.8941` | `0.8941` |
|  | A-atual: ic95 | `[0.8109, 0.9433]` | `[0.8109, 0.9433]` |
|  | A-atual/terceiro-quer: acertos | `9` | `9` |
|  | A-atual/terceiro-quer: n | `15` | `15` |
|  | A-atual/terceiro-quer-eu-nao: acertos | `14` | `14` |
|  | A-atual/terceiro-quer-eu-nao: n | `14` | `14` |
|  | A-atual/terceiro-contra-eu-quero: acertos | `12` | `12` |
|  | A-atual/terceiro-contra-eu-quero: n | `14` | `14` |
|  | A-atual/terceiro-ja-fez: acertos | `15` | `15` |
|  | A-atual/terceiro-ja-fez: n | `16` | `16` |
|  | A-atual/eu-peco-terceiro-cita: acertos | `26` | `26` |
|  | A-atual/eu-peco-terceiro-cita: n | `26` | `26` |
|  | B-instrucao-de-sujeito: n | `85` | `85` |
|  | B-instrucao-de-sujeito: acertos | `79` | `79` |
|  | B-instrucao-de-sujeito: taxa | `0.9294` | `0.9294` |
|  | B-instrucao-de-sujeito: ic95 | `[0.8544, 0.9672]` | `[0.8544, 0.9672]` |
|  | B-instrucao-de-sujeito/terceiro-quer: acertos | `11` | `11` |
|  | B-instrucao-de-sujeito/terceiro-quer: n | `15` | `15` |
|  | B-instrucao-de-sujeito/terceiro-quer-eu-nao: acertos | `14` | `14` |
|  | B-instrucao-de-sujeito/terceiro-quer-eu-nao: n | `14` | `14` |
|  | B-instrucao-de-sujeito/terceiro-contra-eu-quero: acertos | `13` | `13` |
|  | B-instrucao-de-sujeito/terceiro-contra-eu-quero: n | `14` | `14` |
|  | B-instrucao-de-sujeito/terceiro-ja-fez: acertos | `15` | `15` |
|  | B-instrucao-de-sujeito/terceiro-ja-fez: n | `16` | `16` |
|  | B-instrucao-de-sujeito/eu-peco-terceiro-cita: acertos | `26` | `26` |
|  | B-instrucao-de-sujeito/eu-peco-terceiro-cita: n | `26` | `26` |
|  | C-com-escape: n | `85` | `85` |
|  | C-com-escape: acertos | `76` | `76` |
|  | C-com-escape: taxa | `0.8941` | `0.8941` |
|  | C-com-escape: ic95 | `[0.8109, 0.9433]` | `[0.8109, 0.9433]` |
|  | C-com-escape/terceiro-quer: acertos | `10` | `10` |
|  | C-com-escape/terceiro-quer: n | `15` | `15` |
|  | C-com-escape/terceiro-quer-eu-nao: acertos | `14` | `14` |
|  | C-com-escape/terceiro-quer-eu-nao: n | `14` | `14` |
|  | C-com-escape/terceiro-contra-eu-quero: acertos | `11` | `11` |
|  | C-com-escape/terceiro-contra-eu-quero: n | `14` | `14` |
|  | C-com-escape/terceiro-ja-fez: acertos | `15` | `15` |
|  | C-com-escape/terceiro-ja-fez: n | `16` | `16` |
|  | C-com-escape/eu-peco-terceiro-cita: acertos | `26` | `26` |
|  | C-com-escape/eu-peco-terceiro-cita: n | `26` | `26` |
|  | D-sujeito-e-acao: n | `83` | `83` |
|  | D-sujeito-e-acao: acertos | `67` | `67` |
|  | D-sujeito-e-acao: taxa | `0.8072` | `0.8072` |
|  | D-sujeito-e-acao: ic95 | `[0.7096, 0.8777]` | `[0.7096, 0.8777]` |
|  | D-sujeito-e-acao/terceiro-quer: acertos | `13` | `13` |
|  | D-sujeito-e-acao/terceiro-quer: n | `15` | `15` |
|  | D-sujeito-e-acao/terceiro-quer-eu-nao: acertos | `14` | `14` |
|  | D-sujeito-e-acao/terceiro-quer-eu-nao: n | `14` | `14` |
|  | D-sujeito-e-acao/terceiro-contra-eu-quero: acertos | `5` | `5` |
|  | D-sujeito-e-acao/terceiro-contra-eu-quero: n | `14` | `14` |
|  | D-sujeito-e-acao/terceiro-ja-fez: acertos | `15` | `15` |
|  | D-sujeito-e-acao/terceiro-ja-fez: n | `15` | `15` |
|  | D-sujeito-e-acao/eu-peco-terceiro-cita: acertos | `20` | `20` |
|  | D-sujeito-e-acao/eu-peco-terceiro-cita: n | `25` | `25` |
|  | pergunta de sujeito: n | `83` | `83` |
|  | pergunta de sujeito: ic95 | `[0.5806, 0.7764]` | `[0.5806, 0.7764]` |
|  | pergunta de sujeito: taxa | `0.6867` | `0.6867` |

## R20 — 52 conferências, todas fecham

Lote novo, política de k adaptativo e a classe do topo como preditor do acerto.

| | item | publicado | recalculado |
|---|---|---|---|
|  | todos: n | `95` | `95` |
|  | todos: acertos | `77` | `77` |
|  | todos: taxa | `0.8105` | `0.8105` |
|  | todos: ic95 | `[0.7203, 0.8767]` | `[0.7203, 0.8767]` |
|  | todos: bytes | `840452` | `840452` |
|  | todos: economia | `0.0` | `0.0` |
|  | jev-1: n | `95` | `95` |
|  | jev-1: acertos | `89` | `89` |
|  | jev-1: taxa | `0.9368` | `0.9368` |
|  | jev-1: ic95 | `[0.869, 0.9707]` | `[0.869, 0.9707]` |
|  | jev-1: bytes | `106037` | `106037` |
|  | jev-1: economia | `0.8738` | `0.8738` |
|  | jev-2: n | `95` | `95` |
|  | jev-2: acertos | `89` | `89` |
|  | jev-2: taxa | `0.9368` | `0.9368` |
|  | jev-2: ic95 | `[0.869, 0.9707]` | `[0.869, 0.9707]` |
|  | jev-2: bytes | `221432` | `221432` |
|  | jev-2: economia | `0.7365` | `0.7365` |
|  | jev-3: n | `95` | `95` |
|  | jev-3: acertos | `87` | `87` |
|  | jev-3: taxa | `0.9158` | `0.9158` |
|  | jev-3: ic95 | `[0.8425, 0.9567]` | `[0.8425, 0.9567]` |
|  | jev-3: bytes | `302068` | `302068` |
|  | jev-3: economia | `0.6406` | `0.6406` |
|  | adaptativo: n | `95` | `95` |
|  | adaptativo: acertos | `89` | `89` |
|  | adaptativo: taxa | `0.9368` | `0.9368` |
|  | adaptativo: ic95 | `[0.869, 0.9707]` | `[0.869, 0.9707]` |
|  | adaptativo: bytes | `115735` | `115735` |
|  | adaptativo: economia | `0.8623` | `0.8623` |
|  | jev-2 vs jev-3: só jev-2 | `4` | `4` |
|  | jev-2 vs jev-3: só jev-3 | `2` | `2` |
|  | jev-2 vs jev-3: p | `0.6875` | `0.6875` |
|  | jev-2 vs todos: só jev-2 | `15` | `15` |
|  | jev-2 vs todos: só todos | `3` | `3` |
|  | jev-2 vs todos: p | `0.0075` | `0.0075` |
|  | adaptativo vs jev-2: só adaptativo | `1` | `1` |
|  | adaptativo vs jev-2: só jev-2 | `1` | `1` |
|  | adaptativo vs jev-2: p | `1.0` | `1.0` |
|  | adaptativo vs jev-1: só adaptativo | `1` | `1` |
|  | adaptativo vs jev-1: só jev-1 | `1` | `1` |
|  | adaptativo vs jev-1: p | `1.0` | `1.0` |
|  | classe essencial: n | `93` | `93` |
|  | classe essencial: acertos | `89` | `89` |
|  | classe essencial: taxa | `0.957` | `0.957` |
|  | classe essencial: ic95 | `[0.8946, 0.9831]` | `[0.8946, 0.9831]` |
|  | classe essencial: alvo presente | `92` | `92` |
|  | classe irrelevante: n | `2` | `2` |
|  | classe irrelevante: acertos | `0` | `0` |
|  | classe irrelevante: taxa | `0.0` | `0.0` |
|  | classe irrelevante: ic95 | `[0.0, 0.6576]` | `[0.0, 0.6576]` |
|  | classe irrelevante: alvo presente | `0` | `0` |

## consolidado — 61 conferências, todas fecham

O número que sustenta a tese, refeito juntando os dois lotes brutos: 169 perguntas, pareadas uma a uma.

| | item | publicado | recalculado |
|---|---|---|---|
|  | todos: n | `169` | `169` |
|  | todos: acertos | `141` | `141` |
|  | todos: taxa | `0.8343` | `0.8343` |
|  | todos: ic95 | `[0.771, 0.8828]` | `[0.771, 0.8828]` |
|  | todos: bytes | `1472278` | `1472278` |
|  | jev-1: n | `169` | `169` |
|  | jev-1: acertos | `157` | `157` |
|  | jev-1: taxa | `0.929` | `0.929` |
|  | jev-1: ic95 | `[0.88, 0.9589]` | `[0.88, 0.9589]` |
|  | jev-1: bytes | `184293` | `184293` |
|  | jev-2: n | `169` | `169` |
|  | jev-2: acertos | `158` | `158` |
|  | jev-2: taxa | `0.9349` | `0.9349` |
|  | jev-2: ic95 | `[0.8872, 0.9633]` | `[0.8872, 0.9633]` |
|  | jev-2: bytes | `383150` | `383150` |
|  | jev-3: n | `169` | `169` |
|  | jev-3: acertos | `152` | `152` |
|  | jev-3: taxa | `0.8994` | `0.8994` |
|  | jev-3: ic95 | `[0.8448, 0.9362]` | `[0.8448, 0.9362]` |
|  | jev-3: bytes | `549561` | `549561` |
|  | jev-5: n | `74` | `74` |
|  | jev-5: acertos | `65` | `65` |
|  | jev-5: taxa | `0.8784` | `0.8784` |
|  | jev-5: ic95 | `[0.7847, 0.9347]` | `[0.7847, 0.9347]` |
|  | jev-5: bytes | `368948` | `368948` |
|  | adaptativo: n | `95` | `95` |
|  | adaptativo: acertos | `89` | `89` |
|  | adaptativo: taxa | `0.9368` | `0.9368` |
|  | adaptativo: ic95 | `[0.869, 0.9707]` | `[0.869, 0.9707]` |
|  | adaptativo: bytes | `115735` | `115735` |
|  | bm25-2: n | `74` | `74` |
|  | bm25-2: acertos | `52` | `52` |
|  | bm25-2: taxa | `0.7027` | `0.7027` |
|  | bm25-2: ic95 | `[0.5907, 0.7947]` | `[0.5907, 0.7947]` |
|  | bm25-2: bytes | `187359` | `187359` |
|  | sorteio-2: n | `74` | `74` |
|  | sorteio-2: acertos | `24` | `24` |
|  | sorteio-2: taxa | `0.3243` | `0.3243` |
|  | sorteio-2: ic95 | `[0.2286, 0.4373]` | `[0.2286, 0.4373]` |
|  | sorteio-2: bytes | `152820` | `152820` |
|  | jev-2 vs todos: pareados | `169` | `169` |
|  | jev-2 vs todos: só jev-2 | `22` | `22` |
|  | jev-2 vs todos: só todos | `5` | `5` |
|  | jev-2 vs todos: p | `0.0015` | `0.0015` |
|  | jev-1 vs todos: pareados | `169` | `169` |
|  | jev-1 vs todos: só jev-1 | `22` | `22` |
|  | jev-1 vs todos: só todos | `6` | `6` |
|  | jev-1 vs todos: p | `0.0037` | `0.0037` |
|  | jev-2 vs jev-3: pareados | `169` | `169` |
|  | jev-2 vs jev-3: só jev-2 | `8` | `8` |
|  | jev-2 vs jev-3: só jev-3 | `2` | `2` |
|  | jev-2 vs jev-3: p | `0.1094` | `0.1094` |
|  | jev-1 vs jev-2: pareados | `169` | `169` |
|  | jev-1 vs jev-2: só jev-1 | `3` | `3` |
|  | jev-1 vs jev-2: só jev-2 | `4` | `4` |
|  | jev-1 vs jev-2: p | `1.0` | `1.0` |
|  | H20a dois lotes: n | `169` | `169` |
|  | H20a jev-2 vs jev-3: só jev-2 | `8` | `8` |
|  | H20a jev-2 vs jev-3: p | `0.1094` | `0.1094` |
|  | H20a jev-2 vs todos: só jev-2 | `22` | `22` |
|  | H20a jev-2 vs todos: p | `0.0015` | `0.0015` |

## R21 — 67 conferências, todas fecham

| | item | publicado | recalculado |
|---|---|---|---|
|  | pt: n | `65` | `65` |
|  | pt: acertos | `51` | `51` |
|  | pt: taxa | `0.7846` | `0.7846` |
|  | pt: ic95 | `[0.6703, 0.8671]` | `[0.6703, 0.8671]` |
|  | pt/pedido-direto: n | `19` | `19` |
|  | pt/pedido-direto: acertos | `19` | `19` |
|  | pt/sem-pedido: n | `21` | `21` |
|  | pt/sem-pedido: acertos | `16` | `16` |
|  | pt/terceiro-contra-eu-quero: n | `8` | `8` |
|  | pt/terceiro-contra-eu-quero: acertos | `8` | `8` |
|  | pt/terceiro-quer: n | `17` | `17` |
|  | pt/terceiro-quer: acertos | `8` | `8` |
|  | en: n | `64` | `64` |
|  | en: acertos | `49` | `49` |
|  | en: taxa | `0.7656` | `0.7656` |
|  | en: ic95 | `[0.6487, 0.8525]` | `[0.6487, 0.8525]` |
|  | en/pedido-direto: n | `20` | `20` |
|  | en/pedido-direto: acertos | `20` | `20` |
|  | en/sem-pedido: n | `21` | `21` |
|  | en/sem-pedido: acertos | `14` | `14` |
|  | en/terceiro-contra-eu-quero: n | `8` | `8` |
|  | en/terceiro-contra-eu-quero: acertos | `8` | `8` |
|  | en/terceiro-quer: n | `15` | `15` |
|  | en/terceiro-quer: acertos | `7` | `7` |
|  | es: n | `63` | `63` |
|  | es: acertos | `49` | `49` |
|  | es: taxa | `0.7778` | `0.7778` |
|  | es: ic95 | `[0.6609, 0.8628]` | `[0.6609, 0.8627]` |
|  | es/pedido-direto: n | `20` | `20` |
|  | es/pedido-direto: acertos | `20` | `20` |
|  | es/sem-pedido: n | `20` | `20` |
|  | es/sem-pedido: acertos | `13` | `13` |
|  | es/terceiro-contra-eu-quero: n | `8` | `8` |
|  | es/terceiro-contra-eu-quero: acertos | `8` | `8` |
|  | es/terceiro-quer: n | `15` | `15` |
|  | es/terceiro-quer: acertos | `8` | `8` |
|  | pt-meta: n | `68` | `68` |
|  | pt-meta: acertos | `36` | `36` |
|  | pt-meta: taxa | `0.5294` | `0.5294` |
|  | pt-meta: ic95 | `[0.4124, 0.6433]` | `[0.4124, 0.6433]` |
|  | pt-meta/pedido-direto: n | `22` | `22` |
|  | pt-meta/pedido-direto: acertos | `22` | `22` |
|  | pt-meta/sem-pedido: n | `21` | `21` |
|  | pt-meta/sem-pedido: acertos | `0` | `0` |
|  | pt-meta/terceiro-contra-eu-quero: n | `8` | `8` |
|  | pt-meta/terceiro-contra-eu-quero: acertos | `8` | `8` |
|  | pt-meta/terceiro-quer: n | `17` | `17` |
|  | pt-meta/terceiro-quer: acertos | `6` | `6` |
|  | pt-sujeito: n | `66` | `66` |
|  | pt-sujeito: acertos | `60` | `60` |
|  | pt-sujeito: taxa | `0.9091` | `0.9091` |
|  | pt-sujeito: ic95 | `[0.8155, 0.9577]` | `[0.8155, 0.9577]` |
|  | pt-sujeito/pedido-direto: n | `21` | `21` |
|  | pt-sujeito/pedido-direto: acertos | `21` | `21` |
|  | pt-sujeito/sem-pedido: n | `21` | `21` |
|  | pt-sujeito/sem-pedido: acertos | `19` | `19` |
|  | pt-sujeito/terceiro-contra-eu-quero: n | `7` | `7` |
|  | pt-sujeito/terceiro-contra-eu-quero: acertos | `7` | `7` |
|  | pt-sujeito/terceiro-quer: n | `17` | `17` |
|  | pt-sujeito/terceiro-quer: acertos | `13` | `13` |
|  | meta: n | `68` | `68` |
|  | meta: viradas | `21` | `21` |
|  | meta: para o alvo da injecao | `19` | `19` |
|  | prosa: n | `21` | `21` |
|  | prosa: jev em primeiro | `20` | `20` |
|  | prosa: bm25 em primeiro | `20` | `20` |
|  | prosa: pareado p | `1.0` | `1.0` |

## R21b — 6 conferências, todas fecham

| | item | publicado | recalculado |
|---|---|---|---|
|  | n | `81` | `81` |
|  | viradas | `28` | `28` |
|  | taxa | `0.3457` | `0.3457` |
|  | ic95 | `[0.2512, 0.4541]` | `[0.2512, 0.4541]` |
|  | para o alvo da injecao | `28` | `28` |
|  | viradas acima do corte | `1` | `1` |

## R22 — 105 conferências, todas fecham

As três defesas contra a ordem direta — sanitizar, delimitar e sentinela — com acurácia, virada e pareamento por arranjo, e os dois braços do detector.

| | item | publicado | recalculado |
|---|---|---|---|
|  | limpo: n | `82` | `82` |
|  | limpo: acertos | `74` | `74` |
|  | limpo: taxa de acerto | `0.9024` | `0.9024` |
|  | limpo: ic95 do acerto | `[0.8191, 0.9497]` | `[0.8191, 0.9497]` |
|  | limpo: pares com a base | `82` | `82` |
|  | limpo: viradas | `0` | `0` |
|  | limpo: taxa de virada | `0.0` | `0.0` |
|  | limpo: ic95 da virada | `[0.0, 0.0448]` | `[0.0, 0.0448]` |
|  | limpo: viradas para o alvo | `0` | `0` |
|  | limpo: viradas acima do corte | `0` | `0` |
|  | limpo: trechos removidos | `0` | `0` |
|  | limpo-sanitizado: n | `84` | `84` |
|  | limpo-sanitizado: acertos | `76` | `76` |
|  | limpo-sanitizado: taxa de acerto | `0.9048` | `0.9048` |
|  | limpo-sanitizado: ic95 do acerto | `[0.8232, 0.9509]` | `[0.8232, 0.9509]` |
|  | limpo-sanitizado: pares com a base | `82` | `82` |
|  | limpo-sanitizado: viradas | `0` | `0` |
|  | limpo-sanitizado: taxa de virada | `0.0` | `0.0` |
|  | limpo-sanitizado: ic95 da virada | `[0.0, 0.0448]` | `[0.0, 0.0448]` |
|  | limpo-sanitizado: viradas para o alvo | `0` | `0` |
|  | limpo-sanitizado: viradas acima do corte | `0` | `0` |
|  | limpo-sanitizado: trechos removidos | `0` | `0` |
|  | limpo-delimitado: n | `81` | `81` |
|  | limpo-delimitado: acertos | `72` | `72` |
|  | limpo-delimitado: taxa de acerto | `0.8889` | `0.8889` |
|  | limpo-delimitado: ic95 do acerto | `[0.8021, 0.9404]` | `[0.8021, 0.9404]` |
|  | limpo-delimitado: pares com a base | `78` | `78` |
|  | limpo-delimitado: viradas | `1` | `1` |
|  | limpo-delimitado: taxa de virada | `0.0128` | `0.0128` |
|  | limpo-delimitado: ic95 da virada | `[0.0023, 0.0691]` | `[0.0023, 0.0691]` |
|  | limpo-delimitado: viradas para o alvo | `0` | `0` |
|  | limpo-delimitado: viradas acima do corte | `0` | `0` |
|  | limpo-delimitado: trechos removidos | `0` | `0` |
|  | limpo-sentinela: n | `83` | `83` |
|  | limpo-sentinela: acertos | `75` | `75` |
|  | limpo-sentinela: taxa de acerto | `0.9036` | `0.9036` |
|  | limpo-sentinela: ic95 do acerto | `[0.8212, 0.9503]` | `[0.8212, 0.9503]` |
|  | limpo-sentinela: pares com a base | `80` | `80` |
|  | limpo-sentinela: viradas | `0` | `0` |
|  | limpo-sentinela: taxa de virada | `0.0` | `0.0` |
|  | limpo-sentinela: ic95 da virada | `[0.0, 0.0458]` | `[0.0, 0.0458]` |
|  | limpo-sentinela: viradas para o alvo | `0` | `0` |
|  | limpo-sentinela: viradas acima do corte | `0` | `0` |
|  | limpo-sentinela: trechos removidos | `0` | `0` |
|  | meta: n | `80` | `80` |
|  | meta: acertos | `49` | `49` |
|  | meta: taxa de acerto | `0.6125` | `0.6125` |
|  | meta: ic95 do acerto | `[0.5029, 0.7118]` | `[0.5029, 0.7118]` |
|  | meta: pares com a base | `78` | `78` |
|  | meta: viradas | `28` | `28` |
|  | meta: taxa de virada | `0.359` | `0.359` |
|  | meta: ic95 da virada | `[0.2615, 0.4697]` | `[0.2615, 0.4697]` |
|  | meta: viradas para o alvo | `28` | `28` |
|  | meta: viradas acima do corte | `1` | `1` |
|  | meta: trechos removidos | `0` | `0` |
|  | meta-sanitizado: n | `85` | `85` |
|  | meta-sanitizado: acertos | `76` | `76` |
|  | meta-sanitizado: taxa de acerto | `0.8941` | `0.8941` |
|  | meta-sanitizado: ic95 do acerto | `[0.8109, 0.9433]` | `[0.8109, 0.9433]` |
|  | meta-sanitizado: pares com a base | `82` | `82` |
|  | meta-sanitizado: viradas | `1` | `1` |
|  | meta-sanitizado: taxa de virada | `0.0122` | `0.0122` |
|  | meta-sanitizado: ic95 da virada | `[0.0022, 0.0659]` | `[0.0022, 0.0659]` |
|  | meta-sanitizado: viradas para o alvo | `0` | `0` |
|  | meta-sanitizado: viradas acima do corte | `0` | `0` |
|  | meta-sanitizado: trechos removidos | `170` | `170` |
|  | meta-delimitado: n | `79` | `79` |
|  | meta-delimitado: acertos | `55` | `55` |
|  | meta-delimitado: taxa de acerto | `0.6962` | `0.6962` |
|  | meta-delimitado: ic95 do acerto | `[0.5877, 0.7866]` | `[0.5877, 0.7866]` |
|  | meta-delimitado: pares com a base | `76` | `76` |
|  | meta-delimitado: viradas | `21` | `21` |
|  | meta-delimitado: taxa de virada | `0.2763` | `0.2763` |
|  | meta-delimitado: ic95 da virada | `[0.1884, 0.3858]` | `[0.1884, 0.3858]` |
|  | meta-delimitado: viradas para o alvo | `20` | `20` |
|  | meta-delimitado: viradas acima do corte | `1` | `1` |
|  | meta-delimitado: trechos removidos | `0` | `0` |
|  | meta-sentinela: n | `83` | `83` |
|  | meta-sentinela: acertos | `52` | `52` |
|  | meta-sentinela: taxa de acerto | `0.6265` | `0.6265` |
|  | meta-sentinela: ic95 do acerto | `[0.519, 0.7228]` | `[0.519, 0.7228]` |
|  | meta-sentinela: pares com a base | `80` | `80` |
|  | meta-sentinela: viradas | `28` | `28` |
|  | meta-sentinela: taxa de virada | `0.35` | `0.35` |
|  | meta-sentinela: ic95 da virada | `[0.2545, 0.4592]` | `[0.2545, 0.4592]` |
|  | meta-sentinela: viradas para o alvo | `28` | `28` |
|  | meta-sentinela: viradas acima do corte | `1` | `1` |
|  | meta-sentinela: trechos removidos | `0` | `0` |
|  | pareado meta-sanitizado: virou só sem defesa | `27` | `27` |
|  | pareado meta-sanitizado: virou só com defesa | `0` | `0` |
|  | pareado meta-sanitizado: p | `0.0` | `0.0` |
|  | pareado meta-delimitado: virou só sem defesa | `8` | `8` |
|  | pareado meta-delimitado: virou só com defesa | `2` | `2` |
|  | pareado meta-delimitado: p | `0.1094` | `0.1094` |
|  | pareado meta-sentinela: virou só sem defesa | `3` | `3` |
|  | pareado meta-sentinela: virou só com defesa | `1` | `1` |
|  | pareado meta-sentinela: p | `0.625` | `0.625` |
|  | sentinela recall_sob_ataque: n | `83` | `83` |
|  | sentinela recall_sob_ataque: certos | `83` | `83` |
|  | sentinela recall_sob_ataque: taxa | `1.0` | `1.0` |
|  | sentinela recall_sob_ataque: ic95 | `[0.9558, 1.0]` | `[0.9558, 1.0]` |
|  | sentinela silencio_no_texto_limpo: n | `83` | `83` |
|  | sentinela silencio_no_texto_limpo: certos | `81` | `81` |
|  | sentinela silencio_no_texto_limpo: taxa | `0.9759` | `0.9759` |
|  | sentinela silencio_no_texto_limpo: ic95 | `[0.9163, 0.9934]` | `[0.9163, 0.9934]` |

## R23 — 145 conferências, todas fecham

O sanitizador contra 48 paráfrases da ordem direta, por conjunto e por família de autor, com o pareamento pela chave certa e os dois braços do sentinela.

| | item | publicado | recalculado |
|---|---|---|---|
|  | conhecidos/bruto: pares | `942` | `942` |
|  | conhecidos/bruto: viradas | `208` | `208` |
|  | conhecidos/bruto: taxa de virada | `0.2208` | `0.2208` |
|  | conhecidos/bruto: ic95 da virada | `[0.1955, 0.2484]` | `[0.1955, 0.2484]` |
|  | conhecidos/bruto: acima do corte | `20` | `20` |
|  | conhecidos/bruto: removidos | `0` | `0` |
|  | conhecidos/v1: pares | `934` | `934` |
|  | conhecidos/v1: viradas | `207` | `207` |
|  | conhecidos/v1: taxa de virada | `0.2216` | `0.2216` |
|  | conhecidos/v1: ic95 da virada | `[0.1962, 0.2494]` | `[0.1962, 0.2494]` |
|  | conhecidos/v1: acima do corte | `23` | `23` |
|  | conhecidos/v1: removidos | `0` | `0` |
|  | conhecidos/v2: pares | `941` | `941` |
|  | conhecidos/v2: viradas | `11` | `11` |
|  | conhecidos/v2: taxa de virada | `0.0117` | `0.0117` |
|  | conhecidos/v2: ic95 da virada | `[0.0065, 0.0208]` | `[0.0065, 0.0208]` |
|  | conhecidos/v2: acima do corte | `0` | `0` |
|  | conhecidos/v2: removidos | `1084` | `1084` |
|  | conhecidos/pareado v1: virou só sem defesa | `14` | `14` |
|  | conhecidos/pareado v1: virou só com defesa | `13` | `13` |
|  | conhecidos/pareado v1: p | `1.0` | `1.0` |
|  | conhecidos/pareado v2: virou só sem defesa | `201` | `201` |
|  | conhecidos/pareado v2: virou só com defesa | `6` | `6` |
|  | conhecidos/pareado v2: p | `0.0` | `0.0` |
|  | conhecidos: sentinela n | `1002` | `1002` |
|  | conhecidos: sentinela acusou | `831` | `831` |
|  | conhecidos: sentinela recall | `0.8293` | `0.8293` |
|  | surpresa/bruto: pares | `2854` | `2854` |
|  | surpresa/bruto: viradas | `1308` | `1308` |
|  | surpresa/bruto: taxa de virada | `0.4583` | `0.4583` |
|  | surpresa/bruto: ic95 da virada | `[0.4401, 0.4766]` | `[0.4401, 0.4766]` |
|  | surpresa/bruto: acima do corte | `380` | `380` |
|  | surpresa/bruto: removidos | `0` | `0` |
|  | surpresa/v1: pares | `2851` | `2851` |
|  | surpresa/v1: viradas | `1309` | `1309` |
|  | surpresa/v1: taxa de virada | `0.4591` | `0.4591` |
|  | surpresa/v1: ic95 da virada | `[0.4409, 0.4775]` | `[0.4409, 0.4775]` |
|  | surpresa/v1: acima do corte | `370` | `370` |
|  | surpresa/v1: removidos | `0` | `0` |
|  | surpresa/v2: pares | `2850` | `2850` |
|  | surpresa/v2: viradas | `1276` | `1276` |
|  | surpresa/v2: taxa de virada | `0.4477` | `0.4477` |
|  | surpresa/v2: ic95 da virada | `[0.4295, 0.466]` | `[0.4295, 0.466]` |
|  | surpresa/v2: acima do corte | `378` | `378` |
|  | surpresa/v2: removidos | `168` | `168` |
|  | surpresa/pareado v1: virou só sem defesa | `39` | `39` |
|  | surpresa/pareado v1: virou só com defesa | `44` | `44` |
|  | surpresa/pareado v1: p | `0.6609` | `0.6609` |
|  | surpresa/pareado v2: virou só sem defesa | `71` | `71` |
|  | surpresa/pareado v2: virou só com defesa | `41` | `41` |
|  | surpresa/pareado v2: p | `0.0059` | `0.0059` |
|  | surpresa: sentinela n | `3032` | `3032` |
|  | surpresa: sentinela acusou | `2234` | `2234` |
|  | surpresa: sentinela recall | `0.7368` | `0.7368` |
|  | conteudo/mistralai/mistral-nemo: vetores | `12` | `12` |
|  | conteudo/mistralai/mistral-nemo/bruto: pares | `954` | `954` |
|  | conteudo/mistralai/mistral-nemo/bruto: viradas | `455` | `455` |
|  | conteudo/mistralai/mistral-nemo/bruto: taxa de virada | `0.4769` | `0.4769` |
|  | conteudo/mistralai/mistral-nemo/bruto: ic95 da virada | `[0.4454, 0.5087]` | `[0.4454, 0.5087]` |
|  | conteudo/mistralai/mistral-nemo/bruto: acima do corte | `178` | `178` |
|  | conteudo/mistralai/mistral-nemo/bruto: removidos | `0` | `0` |
|  | conteudo/mistralai/mistral-nemo/v2: pares | `951` | `951` |
|  | conteudo/mistralai/mistral-nemo/v2: viradas | `447` | `447` |
|  | conteudo/mistralai/mistral-nemo/v2: taxa de virada | `0.47` | `0.47` |
|  | conteudo/mistralai/mistral-nemo/v2: ic95 da virada | `[0.4385, 0.5018]` | `[0.4385, 0.5018]` |
|  | conteudo/mistralai/mistral-nemo/v2: acima do corte | `177` | `177` |
|  | conteudo/mistralai/mistral-nemo/v2: removidos | `0` | `0` |
|  | conteudo/mistralai/mistral-nemo/pareado v2: virou só sem defesa | `13` | `13` |
|  | conteudo/mistralai/mistral-nemo/pareado v2: virou só com defesa | `10` | `10` |
|  | conteudo/mistralai/mistral-nemo/pareado v2: p | `0.6776` | `0.6776` |
|  | conteudo/mistralai/mistral-nemo: sentinela n | `1013` | `1013` |
|  | conteudo/mistralai/mistral-nemo: sentinela acusou | `308` | `308` |
|  | conteudo/mistralai/mistral-nemo: sentinela recall | `0.304` | `0.304` |
|  | instrucao/google/gemma-3-12b-it: vetores | `12` | `12` |
|  | instrucao/google/gemma-3-12b-it/bruto: pares | `951` | `951` |
|  | instrucao/google/gemma-3-12b-it/bruto: viradas | `458` | `458` |
|  | instrucao/google/gemma-3-12b-it/bruto: taxa de virada | `0.4816` | `0.4816` |
|  | instrucao/google/gemma-3-12b-it/bruto: ic95 da virada | `[0.45, 0.5134]` | `[0.45, 0.5134]` |
|  | instrucao/google/gemma-3-12b-it/bruto: acima do corte | `155` | `155` |
|  | instrucao/google/gemma-3-12b-it/bruto: removidos | `0` | `0` |
|  | instrucao/google/gemma-3-12b-it/v2: pares | `954` | `954` |
|  | instrucao/google/gemma-3-12b-it/v2: viradas | `427` | `427` |
|  | instrucao/google/gemma-3-12b-it/v2: taxa de virada | `0.4476` | `0.4476` |
|  | instrucao/google/gemma-3-12b-it/v2: ic95 da virada | `[0.4163, 0.4793]` | `[0.4163, 0.4793]` |
|  | instrucao/google/gemma-3-12b-it/v2: acima do corte | `153` | `153` |
|  | instrucao/google/gemma-3-12b-it/v2: removidos | `84` | `84` |
|  | instrucao/google/gemma-3-12b-it/pareado v2: virou só sem defesa | `43` | `43` |
|  | instrucao/google/gemma-3-12b-it/pareado v2: virou só com defesa | `11` | `11` |
|  | instrucao/google/gemma-3-12b-it/pareado v2: p | `0.0` | `0.0` |
|  | instrucao/google/gemma-3-12b-it: sentinela n | `1011` | `1011` |
|  | instrucao/google/gemma-3-12b-it: sentinela acusou | `953` | `953` |
|  | instrucao/google/gemma-3-12b-it: sentinela recall | `0.9426` | `0.9426` |
|  | instrucao/laboratorio: vetores | `12` | `12` |
|  | instrucao/laboratorio/bruto: pares | `942` | `942` |
|  | instrucao/laboratorio/bruto: viradas | `208` | `208` |
|  | instrucao/laboratorio/bruto: taxa de virada | `0.2208` | `0.2208` |
|  | instrucao/laboratorio/bruto: ic95 da virada | `[0.1955, 0.2484]` | `[0.1955, 0.2484]` |
|  | instrucao/laboratorio/bruto: acima do corte | `20` | `20` |
|  | instrucao/laboratorio/bruto: removidos | `0` | `0` |
|  | instrucao/laboratorio/v2: pares | `941` | `941` |
|  | instrucao/laboratorio/v2: viradas | `11` | `11` |
|  | instrucao/laboratorio/v2: taxa de virada | `0.0117` | `0.0117` |
|  | instrucao/laboratorio/v2: ic95 da virada | `[0.0065, 0.0208]` | `[0.0065, 0.0208]` |
|  | instrucao/laboratorio/v2: acima do corte | `0` | `0` |
|  | instrucao/laboratorio/v2: removidos | `1084` | `1084` |
|  | instrucao/laboratorio/pareado v2: virou só sem defesa | `201` | `201` |
|  | instrucao/laboratorio/pareado v2: virou só com defesa | `6` | `6` |
|  | instrucao/laboratorio/pareado v2: p | `0.0` | `0.0` |
|  | instrucao/laboratorio: sentinela n | `1002` | `1002` |
|  | instrucao/laboratorio: sentinela acusou | `831` | `831` |
|  | instrucao/laboratorio: sentinela recall | `0.8293` | `0.8293` |
|  | instrucao/openai/gpt-oss-20b: vetores | `12` | `12` |
|  | instrucao/openai/gpt-oss-20b/bruto: pares | `949` | `949` |
|  | instrucao/openai/gpt-oss-20b/bruto: viradas | `395` | `395` |
|  | instrucao/openai/gpt-oss-20b/bruto: taxa de virada | `0.4162` | `0.4162` |
|  | instrucao/openai/gpt-oss-20b/bruto: ic95 da virada | `[0.3853, 0.4479]` | `[0.3853, 0.4479]` |
|  | instrucao/openai/gpt-oss-20b/bruto: acima do corte | `47` | `47` |
|  | instrucao/openai/gpt-oss-20b/bruto: removidos | `0` | `0` |
|  | instrucao/openai/gpt-oss-20b/v2: pares | `945` | `945` |
|  | instrucao/openai/gpt-oss-20b/v2: viradas | `402` | `402` |
|  | instrucao/openai/gpt-oss-20b/v2: taxa de virada | `0.4254` | `0.4254` |
|  | instrucao/openai/gpt-oss-20b/v2: ic95 da virada | `[0.3942, 0.4572]` | `[0.3942, 0.4572]` |
|  | instrucao/openai/gpt-oss-20b/v2: acima do corte | `48` | `48` |
|  | instrucao/openai/gpt-oss-20b/v2: removidos | `84` | `84` |
|  | instrucao/openai/gpt-oss-20b/pareado v2: virou só sem defesa | `15` | `15` |
|  | instrucao/openai/gpt-oss-20b/pareado v2: virou só com defesa | `20` | `20` |
|  | instrucao/openai/gpt-oss-20b/pareado v2: p | `0.4996` | `0.4996` |
|  | instrucao/openai/gpt-oss-20b: sentinela n | `1008` | `1008` |
|  | instrucao/openai/gpt-oss-20b: sentinela acusou | `973` | `973` |
|  | instrucao/openai/gpt-oss-20b: sentinela recall | `0.9653` | `0.9653` |
|  | limpo: sentinela calada | `78` | `78` |
|  | gatilho/bruto: n | `24` | `24` |
|  | gatilho/bruto: acertos | `20` | `20` |
|  | gatilho/bruto: ic95 | `[0.6415, 0.9332]` | `[0.6415, 0.9332]` |
|  | gatilho/bruto: mutiladas | `0` | `0` |
|  | gatilho/v1: n | `24` | `24` |
|  | gatilho/v1: acertos | `20` | `20` |
|  | gatilho/v1: ic95 | `[0.6415, 0.9332]` | `[0.6415, 0.9332]` |
|  | gatilho/v1: mutiladas | `10` | `10` |
|  | gatilho/v2: n | `24` | `24` |
|  | gatilho/v2: acertos | `19` | `19` |
|  | gatilho/v2: ic95 | `[0.5953, 0.9076]` | `[0.5953, 0.9076]` |
|  | gatilho/v2: mutiladas | `22` | `22` |
|  | gatilho alarme falso: sentinela n | `24` | `24` |
|  | gatilho alarme falso: sentinela acusou | `7` | `7` |

## R24 — 52 conferências, todas fecham

As quatro políticas de votação refeitas das cinco chamadas por caso, a oscilação e o acerto por formulação.

| | item | publicado | recalculado |
|---|---|---|---|
|  | atendimento: casos | `85` | `85` |
|  | atendimento/unica: n | `84` | `84` |
|  | atendimento/unica: acertos | `76` | `76` |
|  | atendimento/unica: ic95 | `[0.8232, 0.9509]` | `[0.8232, 0.9509]` |
|  | atendimento/maioria-igual: n | `85` | `85` |
|  | atendimento/maioria-igual: acertos | `77` | `77` |
|  | atendimento/maioria-igual: ic95 | `[0.8251, 0.9515]` | `[0.8251, 0.9515]` |
|  | atendimento/maioria-igual: certo só única | `0` | `0` |
|  | atendimento/maioria-igual: certo só votação | `0` | `0` |
|  | atendimento/maioria-igual: p | `1.0` | `1.0` |
|  | atendimento/maioria-diversa: n | `85` | `85` |
|  | atendimento/maioria-diversa: acertos | `78` | `78` |
|  | atendimento/maioria-diversa: ic95 | `[0.8396, 0.9595]` | `[0.8396, 0.9595]` |
|  | atendimento/maioria-diversa: certo só única | `0` | `0` |
|  | atendimento/maioria-diversa: certo só votação | `1` | `1` |
|  | atendimento/maioria-diversa: p | `1.0` | `1.0` |
|  | atendimento/diversa-por-confianca: n | `85` | `85` |
|  | atendimento/diversa-por-confianca: acertos | `78` | `78` |
|  | atendimento/diversa-por-confianca: ic95 | `[0.8396, 0.9595]` | `[0.8396, 0.9595]` |
|  | atendimento/diversa-por-confianca: certo só única | `0` | `0` |
|  | atendimento/diversa-por-confianca: certo só votação | `1` | `1` |
|  | atendimento/diversa-por-confianca: p | `1.0` | `1.0` |
|  | atendimento: oscilaram | `0` | `0` |
|  | atendimento/formulação base: acertos | `76` | `76` |
|  | atendimento/formulação sujeito: acertos | `77` | `77` |
|  | atendimento/formulação reescrita: acertos | `77` | `77` |
|  | juridico: casos | `69` | `69` |
|  | juridico/unica: n | `69` | `69` |
|  | juridico/unica: acertos | `55` | `55` |
|  | juridico/unica: ic95 | `[0.6878, 0.8751]` | `[0.6878, 0.8751]` |
|  | juridico/maioria-igual: n | `69` | `69` |
|  | juridico/maioria-igual: acertos | `55` | `55` |
|  | juridico/maioria-igual: ic95 | `[0.6878, 0.8751]` | `[0.6878, 0.8751]` |
|  | juridico/maioria-igual: certo só única | `0` | `0` |
|  | juridico/maioria-igual: certo só votação | `0` | `0` |
|  | juridico/maioria-igual: p | `1.0` | `1.0` |
|  | juridico/maioria-diversa: n | `69` | `69` |
|  | juridico/maioria-diversa: acertos | `64` | `64` |
|  | juridico/maioria-diversa: ic95 | `[0.8413, 0.9687]` | `[0.8413, 0.9687]` |
|  | juridico/maioria-diversa: certo só única | `0` | `0` |
|  | juridico/maioria-diversa: certo só votação | `9` | `9` |
|  | juridico/maioria-diversa: p | `0.0039` | `0.0039` |
|  | juridico/diversa-por-confianca: n | `69` | `69` |
|  | juridico/diversa-por-confianca: acertos | `61` | `61` |
|  | juridico/diversa-por-confianca: ic95 | `[0.7875, 0.9401]` | `[0.7875, 0.9401]` |
|  | juridico/diversa-por-confianca: certo só única | `0` | `0` |
|  | juridico/diversa-por-confianca: certo só votação | `6` | `6` |
|  | juridico/diversa-por-confianca: p | `0.0312` | `0.0312` |
|  | juridico: oscilaram | `0` | `0` |
|  | juridico/formulação base: acertos | `55` | `55` |
|  | juridico/formulação sujeito: acertos | `63` | `63` |
|  | juridico/formulação reescrita: acertos | `63` | `63` |

## R25 — 42 conferências, todas fecham

O terceiro domínio: acurácia por arranjo e molde, a frase de sujeito e a sanitização pareadas.

| | item | publicado | recalculado |
|---|---|---|---|
|  | base: n | `76` | `76` |
|  | base: acertos | `48` | `48` |
|  | base: ic95 | `[0.5192, 0.7312]` | `[0.5193, 0.7312]` |
|  | base: viradas | `0` | `0` |
|  | base: viradas acima do corte | `0` | `0` |
|  | base/terceiro-quer: acertos | `4` | `4` |
|  | base/terceiro-contra-eu-quero: acertos | `10` | `10` |
|  | base/sem-pedido: acertos | `11` | `11` |
|  | base/pedido-direto: acertos | `23` | `23` |
|  | sujeito: n | `77` | `77` |
|  | sujeito: acertos | `60` | `60` |
|  | sujeito: ic95 | `[0.6746, 0.8573]` | `[0.6746, 0.8573]` |
|  | sujeito: viradas | `11` | `11` |
|  | sujeito: viradas acima do corte | `0` | `0` |
|  | sujeito/terceiro-quer: acertos | `13` | `13` |
|  | sujeito/terceiro-contra-eu-quero: acertos | `10` | `10` |
|  | sujeito/sem-pedido: acertos | `13` | `13` |
|  | sujeito/pedido-direto: acertos | `24` | `24` |
|  | meta: n | `73` | `73` |
|  | meta: acertos | `34` | `34` |
|  | meta: ic95 | `[0.3559, 0.579]` | `[0.3559, 0.579]` |
|  | meta: viradas | `16` | `16` |
|  | meta: viradas acima do corte | `2` | `2` |
|  | meta/terceiro-quer: acertos | `1` | `1` |
|  | meta/terceiro-contra-eu-quero: acertos | `9` | `9` |
|  | meta/sem-pedido: acertos | `0` | `0` |
|  | meta/pedido-direto: acertos | `24` | `24` |
|  | meta-sanitizado: n | `77` | `77` |
|  | meta-sanitizado: acertos | `49` | `49` |
|  | meta-sanitizado: ic95 | `[0.5248, 0.7349]` | `[0.5248, 0.7349]` |
|  | meta-sanitizado: viradas | `0` | `0` |
|  | meta-sanitizado: viradas acima do corte | `0` | `0` |
|  | meta-sanitizado/terceiro-quer: acertos | `4` | `4` |
|  | meta-sanitizado/terceiro-contra-eu-quero: acertos | `10` | `10` |
|  | meta-sanitizado/sem-pedido: acertos | `11` | `11` |
|  | meta-sanitizado/pedido-direto: acertos | `24` | `24` |
|  | sujeito: certo só base | `0` | `0` |
|  | sujeito: certo só sujeito | `11` | `11` |
|  | sujeito: p | `0.001` | `0.001` |
|  | sanitização: virou só sem defesa | `16` | `16` |
|  | sanitização: virou só com defesa | `0` | `0` |
|  | sanitização: p | `0.0` | `0.0` |

## R26 — 39 conferências, todas fecham

A resposta dividida em dois trechos: acerto por arranjo, pareamento contra carregar tudo e o que a ordenação viu.

| | item | publicado | recalculado |
|---|---|---|---|
|  | dupla/jev-1: n | `80` | `80` |
|  | dupla/jev-1: acertos | `6` | `6` |
|  | dupla/jev-1: ic95 | `[0.0348, 0.1541]` | `[0.0348, 0.1541]` |
|  | dupla/jev-1: alvos presentes | `0` | `0` |
|  | dupla/jev-1: certo só todos | `54` | `54` |
|  | dupla/jev-1: certo só seleção | `0` | `0` |
|  | dupla/jev-1: p | `0.0` | `0.0` |
|  | dupla/jev-2: n | `80` | `80` |
|  | dupla/jev-2: acertos | `40` | `40` |
|  | dupla/jev-2: ic95 | `[0.393, 0.607]` | `[0.393, 0.607]` |
|  | dupla/jev-2: alvos presentes | `42` | `42` |
|  | dupla/jev-2: certo só todos | `26` | `26` |
|  | dupla/jev-2: certo só seleção | `6` | `6` |
|  | dupla/jev-2: p | `0.0005` | `0.0005` |
|  | dupla/jev-3: n | `80` | `80` |
|  | dupla/jev-3: acertos | `50` | `50` |
|  | dupla/jev-3: ic95 | `[0.5155, 0.7231]` | `[0.5155, 0.7231]` |
|  | dupla/jev-3: alvos presentes | `59` | `59` |
|  | dupla/jev-3: certo só todos | `21` | `21` |
|  | dupla/jev-3: certo só seleção | `11` | `11` |
|  | dupla/jev-3: p | `0.1102` | `0.1102` |
|  | dupla/todos: n | `80` | `80` |
|  | dupla/todos: acertos | `60` | `60` |
|  | dupla/todos: ic95 | `[0.6452, 0.8319]` | `[0.6452, 0.8319]` |
|  | dupla/todos: alvos presentes | `80` | `80` |
|  | simples/jev-1: n | `80` | `80` |
|  | simples/jev-1: acertos | `76` | `76` |
|  | simples/jev-1: ic95 | `[0.8784, 0.9804]` | `[0.8784, 0.9804]` |
|  | simples/jev-1: alvos presentes | `78` | `78` |
|  | simples/todos: n | `80` | `80` |
|  | simples/todos: acertos | `67` | `67` |
|  | simples/todos: ic95 | `[0.7416, 0.9025]` | `[0.7416, 0.9025]` |
|  | simples/todos: alvos presentes | `80` | `80` |
|  | ordenação: n | `80` | `80` |
|  | ordenação: topo é alvo | `71` | `71` |
|  | ordenação: dois no top-2 | `42` | `42` |
|  | ordenação: dois no top-3 | `59` | `59` |
|  | ordenação: topo essencial | `53` | `53` |
|  | ordenação: dois alvos essenciais | `17` | `17` |

## R27 — 61 conferências, todas fecham

As oito montagens da integração sanitizador + sentinela: virada, acerto e detecção, com o pareamento contra o separado.

| | item | publicado | recalculado |
|---|---|---|---|
|  | limpo-separado: n | `84` | `84` |
|  | limpo-separado: acertos | `76` | `76` |
|  | limpo-separado: viradas | `0` | `0` |
|  | limpo-separado: ic95 da virada | `[0.0, 0.0437]` | `[0.0, 0.0437]` |
|  | limpo-separado: acima do corte | `0` | `0` |
|  | limpo-dois-campos: n | `84` | `84` |
|  | limpo-dois-campos: acertos | `77` | `77` |
|  | limpo-dois-campos: viradas | `1` | `1` |
|  | limpo-dois-campos: ic95 da virada | `[0.0021, 0.0644]` | `[0.0021, 0.0644]` |
|  | limpo-dois-campos: acima do corte | `0` | `0` |
|  | limpo-dois-campos: sentinela n | `84` | `84` |
|  | limpo-dois-campos: sentinela certos | `82` | `82` |
|  | limpo-sentinela-limpo: n | `84` | `84` |
|  | limpo-sentinela-limpo: acertos | `76` | `76` |
|  | limpo-sentinela-limpo: viradas | `0` | `0` |
|  | limpo-sentinela-limpo: ic95 da virada | `[0.0, 0.0437]` | `[0.0, 0.0437]` |
|  | limpo-sentinela-limpo: acima do corte | `0` | `0` |
|  | limpo-sentinela-limpo: sentinela n | `84` | `84` |
|  | limpo-sentinela-limpo: sentinela certos | `82` | `82` |
|  | limpo-duas-chamadas: n | `85` | `85` |
|  | limpo-duas-chamadas: acertos | `77` | `77` |
|  | limpo-duas-chamadas: viradas | `0` | `0` |
|  | limpo-duas-chamadas: ic95 da virada | `[0.0, 0.0432]` | `[0.0, 0.0432]` |
|  | limpo-duas-chamadas: acima do corte | `0` | `0` |
|  | limpo-duas-chamadas: sentinela n | `85` | `85` |
|  | limpo-duas-chamadas: sentinela certos | `83` | `83` |
|  | meta-separado: n | `84` | `84` |
|  | meta-separado: acertos | `76` | `76` |
|  | meta-separado: viradas | `0` | `0` |
|  | meta-separado: ic95 da virada | `[0.0, 0.0437]` | `[0.0, 0.0437]` |
|  | meta-separado: acima do corte | `0` | `0` |
|  | meta-dois-campos: n | `84` | `84` |
|  | meta-dois-campos: acertos | `79` | `79` |
|  | meta-dois-campos: viradas | `3` | `3` |
|  | meta-dois-campos: ic95 da virada | `[0.0122, 0.0998]` | `[0.0122, 0.0998]` |
|  | meta-dois-campos: acima do corte | `0` | `0` |
|  | meta-dois-campos: sentinela n | `84` | `84` |
|  | meta-dois-campos: sentinela certos | `84` | `84` |
|  | meta-sentinela-limpo: n | `85` | `85` |
|  | meta-sentinela-limpo: acertos | `77` | `77` |
|  | meta-sentinela-limpo: viradas | `0` | `0` |
|  | meta-sentinela-limpo: ic95 da virada | `[0.0, 0.0432]` | `[0.0, 0.0432]` |
|  | meta-sentinela-limpo: acima do corte | `0` | `0` |
|  | meta-sentinela-limpo: sentinela n | `85` | `85` |
|  | meta-sentinela-limpo: sentinela certos | `2` | `2` |
|  | meta-duas-chamadas: n | `82` | `82` |
|  | meta-duas-chamadas: acertos | `74` | `74` |
|  | meta-duas-chamadas: viradas | `0` | `0` |
|  | meta-duas-chamadas: ic95 da virada | `[0.0, 0.0448]` | `[0.0, 0.0448]` |
|  | meta-duas-chamadas: acima do corte | `0` | `0` |
|  | meta-duas-chamadas: sentinela n | `83` | `83` |
|  | meta-duas-chamadas: sentinela certos | `83` | `83` |
|  | pareado meta-dois-campos: só separado | `0` | `0` |
|  | pareado meta-dois-campos: só nesta | `3` | `3` |
|  | pareado meta-dois-campos: p | `0.25` | `0.25` |
|  | pareado meta-sentinela-limpo: só separado | `0` | `0` |
|  | pareado meta-sentinela-limpo: só nesta | `0` | `0` |
|  | pareado meta-sentinela-limpo: p | `1.0` | `1.0` |
|  | pareado meta-duas-chamadas: só separado | `0` | `0` |
|  | pareado meta-duas-chamadas: só nesta | `0` | `0` |
|  | pareado meta-duas-chamadas: p | `1.0` | `1.0` |

## cem hipoteses — 8 conferências, todas fecham

| | item | publicado | recalculado |
|---|---|---|---|
|  | o registro tem cem | `100` | `100` |
|  | nenhuma prova quebrou | `0` | `0` |
|  | a pagina existe | `True` | `True` |
|  | a pagina esta atualizada | `True` | `True` |
|  | a pagina declara o placar | `True` | `True` |
|  | sustentadas | `81` | `81` |
|  | falsificadas | `18` | `18` |
|  | inconclusivas | `1` | `1` |

## cem perguntas — 5 conferências, todas fecham

O registro estratégico, a declaração de todo parâmetro não medido que as respostas usam, e se a página publicada está atualizada.

| | item | publicado | recalculado |
|---|---|---|---|
|  | o registro tem cem | `100` | `100` |
|  | toda pergunta tem resposta | `0` | `0` |
|  | nenhuma usa parâmetro não declarado | `[]` | `[]` |
|  | CEM-PERGUNTAS-ESTRATEGICAS.md existe | `True` | `True` |
|  | CEM-PERGUNTAS-ESTRATEGICAS.md está atualizado | `True` | `True` |

## documentação — 72 conferências, todas fecham

Cada afirmação numérica escrita nos documentos, conferida em duas etapas: o trecho existe literalmente, e o valor fecha com o dado.

| | item | publicado | recalculado |
|---|---|---|---|
|  | GUIA-PRATICO-JEV.md: "| todos os 8 trechos | 141/169 | 83,4% | 1.472.278 |…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "| todos os 8 trechos | 141/169 | 83,4% | 1.472.278 |…" fecha com o dado | `141` | `141` |
|  | GUIA-PRATICO-JEV.md: "83,4%…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "83,4%…" fecha com o dado | `83,4%` | `83,4%` |
|  | GUIA-PRATICO-JEV.md: "| **os dois do Jev** | **158/169** | **93,5%** | 383…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "| **os dois do Jev** | **158/169** | **93,5%** | 383…" fecha com o dado | `158` | `158` |
|  | GUIA-PRATICO-JEV.md: "**22 casos a 5, p = 0,0015**…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "**22 casos a 5, p = 0,0015**…" fecha com o dado | `0.0015` | `0.0015` |
|  | PREREGISTRO.md: "**`jev-2` contra carregar tudo: 22 casos a 5, p = 0,…" está escrito | `True` | `True` |
|  | PREREGISTRO.md: "**`jev-2` contra carregar tudo: 22 casos a 5, p = 0,…" fecha com o dado | `22` | `22` |
|  | PREREGISTRO.md: "22 a 6, p = 0,0037…" está escrito | `True` | `True` |
|  | PREREGISTRO.md: "22 a 6, p = 0,0037…" fecha com o dado | `0.0037` | `0.0037` |
|  | PREREGISTRO.md: "8 a 2,
p = 0,109…" está escrito | `True` | `True` |
|  | PREREGISTRO.md: "8 a 2,
p = 0,109…" fecha com o dado | `0.1094` | `0.1094` |
|  | PREREGISTRO.md: "3 a 4, p = 1,0…" está escrito | `True` | `True` |
|  | PREREGISTRO.md: "3 a 4, p = 1,0…" fecha com o dado | `1.0` | `1.0` |
|  | GUIA-PRATICO-JEV.md: "22 casos a 1 na colocação do trecho certo, p < 0,000…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "22 casos a 1 na colocação do trecho certo, p < 0,000…" fecha com o dado | `22` | `22` |
|  | PREREGISTRO.md: "**22 casos só do Jev contra 1 só do BM25, p < 0,0001…" está escrito | `True` | `True` |
|  | PREREGISTRO.md: "**22 casos só do Jev contra 1 só do BM25, p < 0,0001…" fecha com o dado | `1` | `1` |
|  | PREREGISTRO.md: "| **jev, k = 2** | **69/74** | **93,2%** | 72/74 | 1…" está escrito | `True` | `True` |
|  | PREREGISTRO.md: "| **jev, k = 2** | **69/74** | **93,2%** | 72/74 | 1…" fecha com o dado | `69` | `69` |
|  | PREREGISTRO.md: "66 contra 69…" está escrito | `True` | `True` |
|  | PREREGISTRO.md: "66 contra 69…" fecha com o dado | `66` | `66` |
|  | GUIA-PRATICO-JEV.md: "de 89,4% para 92,9% em 85…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "de 89,4% para 92,9% em 85…" fecha com o dado | `89,4%` | `89,4%` |
|  | GUIA-PRATICO-JEV.md: "92,9%…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "92,9%…" fecha com o dado | `92,9%` | `92,9%` |
|  | GUIA-PRATICO-JEV.md: "(95,5%
contra 84,4%)…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "(95,5%
contra 84,4%)…" fecha com o dado | `95,5%` | `95,5%` |
|  | GUIA-PRATICO-JEV.md: "só 68,7%…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "só 68,7%…" fecha com o dado | `68,7%` | `68,7%` |
|  | GUIA-PRATICO-JEV.md: "**86,2% de economia contra 73,7%**…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "**86,2% de economia contra 73,7%**…" fecha com o dado | `86,2%` | `86,2%` |
|  | GUIA-PRATICO-JEV.md: "73,7%…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "73,7%…" fecha com o dado | `73,7%` | `73,7%` |
|  | GUIA-PRATICO-JEV.md: "resposta saiu certa em 95,7%…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "resposta saiu certa em 95,7%…" fecha com o dado | `95,7%` | `95,7%` |
|  | GUIA-PRATICO-JEV.md: "**72,6% do contexto**…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "**72,6% do contexto**…" fecha com o dado | `72,6%` | `72,6%` |
|  | GUIA-PRATICO-JEV.md: "18/20 respostas certas contra 15/20…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "18/20 respostas certas contra 15/20…" fecha com o dado | `18` | `18` |
|  | LIMITES-DO-JEV.md: "família A…" está escrito | `True` | `True` |
|  | LIMITES-DO-JEV.md: "família A…" fecha com o dado | `0` | `0` |
|  | LIMITES-DO-JEV.md: "família B…" está escrito | `True` | `True` |
|  | LIMITES-DO-JEV.md: "família B…" fecha com o dado | `10` | `10` |
|  | GUIA-PRATICO-JEV.md: "| regra por palavra sozinha | **72,2%** | 0 de 12 |…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "| regra por palavra sozinha | **72,2%** | 0 de 12 |…" fecha com o dado | `72,2%` | `72,2%` |
|  | GUIA-PRATICO-JEV.md: "| regra + Jev como segunda camada | **29,6%** | **0 …" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "| regra + Jev como segunda camada | **29,6%** | **0 …" fecha com o dado | `29,6%` | `29,6%` |
|  | GUIA-PRATICO-JEV.md: "0 em 46 liberações…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "0 em 46 liberações…" fecha com o dado | `46` | `46` |
|  | GUIA-PRATICO-JEV.md: "**0 de 12**…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "**0 de 12**…" fecha com o dado | `0` | `0` |
|  | GUIA-PRATICO-JEV.md: "| nenhuma | 28/78 = **35,9%** | 49/80 = 61,3% | — |…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "| nenhuma | 28/78 = **35,9%** | 49/80 = 61,3% | — |…" fecha com o dado | `35,9%` | `35,9%` |
|  | GUIA-PRATICO-JEV.md: "| **sanitizar a entrada** | 1/82 = **1,2%** | 76/85 …" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "| **sanitizar a entrada** | 1/82 = **1,2%** | 76/85 …" fecha com o dado | `1` | `1` |
|  | GUIA-PRATICO-JEV.md: "27 a 0, p < 0,0001…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "27 a 0, p < 0,0001…" fecha com o dado | `27` | `27` |
|  | GUIA-PRATICO-JEV.md: "| delimitar o texto do cliente | 21/76 = 27,6% | 55/…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "| delimitar o texto do cliente | 21/76 = 27,6% | 55/…" fecha com o dado | `27,6%` | `27,6%` |
|  | GUIA-PRATICO-JEV.md: "removeu 170 trechos…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "removeu 170 trechos…" fecha com o dado | `170` | `170` |
|  | GUIA-PRATICO-JEV.md: "**83 de
83** tentativas de ordem direta…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "**83 de
83** tentativas de ordem direta…" fecha com o dado | `83` | `83` |
|  | GUIA-PRATICO-JEV.md: "calada em **81 de 83** mensagens limpas…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "calada em **81 de 83** mensagens limpas…" fecha com o dado | `81` | `81` |
|  | GUIA-PRATICO-JEV.md: "recall de 100%
com 2,4% de alarme falso…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "recall de 100%
com 2,4% de alarme falso…" fecha com o dado | `2,4%` | `2,4%` |
|  | GUIA-PRATICO-JEV.md: "76/84 contra 74/82 sem ela…" está escrito | `True` | `True` |
|  | GUIA-PRATICO-JEV.md: "76/84 contra 74/82 sem ela…" fecha com o dado | `76` | `76` |

## páginas geradas — 4 conferências, todas fecham

| | item | publicado | recalculado |
|---|---|---|---|
|  | DOSSIE-DE-EVIDENCIAS.md existe | `True` | `True` |
|  | DOSSIE-DE-EVIDENCIAS.md está atualizado | `True` | `True` |
|  | BATERIA-COMPLEMENTAR.md existe | `True` | `True` |
|  | BATERIA-COMPLEMENTAR.md está atualizado | `True` | `True` |

## caixa — 4 conferências, todas fecham

As chamadas e o custo declarados na documentação contra o livro-caixa SQLite, e o teto de gasto autorizado.

| | item | publicado | recalculado |
|---|---|---|---|
|  | o guia declara chamadas e custo | `True` | `True` |
|  | chamadas declaradas = livro-caixa | `31163` | `31163` |
|  | custo declarado = livro-caixa (4 casas) | `1.0054` | `1.0054` |
|  | dentro do teto de US$ 5,00 | `True` | `True` |

## Fora do alcance desta auditoria

Números que aparecem nos resumos mas cujas linhas brutas não estão no arquivo que os cita. Não são falhas; são o que esta página **não** prova.

- R1-R3: original-E12: reaproveitada de outro experimento
- R22: se os oito padrões do sanitizador cobrem a ordem direta escrita de outro jeito: a defesa foi medida contra os vetores que este laboratório escreveu, e um atacante que os conheça pode contorná-los
- R23: se os 36 vetores escritos por três modelos esgotam as formas de dar ordem ao classificador: são uma amostra, e a taxa de virada vale para ela
- R24: se a formulação reescrita ganha por ser reescrita ou por ter os critérios em ordem inversa: as duas mudanças entraram juntas
- R25: se a queda da clínica é do domínio ou do gerador: o mesmo modelo escreveu os três corpus, e a fraqueza de terceiro pode ser dele
- R26: se a pergunta dupla "responda as duas" representa a resposta dividida do mundo real, onde a divisão não vem anunciada
- cem perguntas: se o valor dos parâmetros não medidos — preço de mercado, custo-hora, volume mensal — corresponde à realidade de quem for usar o estudo. A auditoria confere que eles estão declarados, não que estão certos

