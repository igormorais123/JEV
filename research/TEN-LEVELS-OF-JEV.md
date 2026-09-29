# 10 Levels of Jev — contribuições à arquitetura

- Fonte: [10 Levels of Jev For Agentic Engineers](https://www.youtube.com/watch?v=_U-O5lYhJ7Q), IndyDevDan.
- Publicação e consulta: 28/09/2026. Duração: 35min17s.
- Código associado: [disler/ten-levels-of-jev](https://github.com/disler/ten-levels-of-jev/tree/777adaf47d37ae0553220d35b2f15b3a3a063305), revisão `777adaf47d37ae0553220d35b2f15b3a3a063305`.
- Material atualizado: [Arquitetura do JEV](../docs/ARQUITETURA-DO-JEV-REVISAO.md), páginas 8–10, 12–13, 17–18.

## Seleção das contribuições

| Nível e momento | Técnica | Destino no material |
|---|---|---|
| 1 · [00:57](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=57s) | Decisão binária sobre estado delimitado | Já coberta nos princípios e na triagem; sem novo fluxo |
| 2 · [03:18](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=198s) | Opções declaradas e perguntas independentes na mesma chamada | Classificação já coberta; agrupamento explicitado no contexto |
| 3 · [06:20](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=380s) | Pontuação por dimensão, combinação em código | Incorporada à triagem: escalas normalizadas e precedência das regras críticas |
| 4 · [08:50](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=530s) | Encaminhamento conforme confiança | Já coberto; os cortes da demonstração não viraram parâmetros do JEV |
| 5 · [12:11](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=731s) | Roteamento de modelo, agente e fluxo | Já coberto nas políticas 2 e 3; sem ampliação |
| 6 · [14:31](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=871s) | Verificação no ponto de chamada da ferramenta | Precisão adicionada ao ciclo de execução; classificação não concede permissão |
| 7 · [17:34](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=1054s) | Compactação guiada por uso de contexto e mudança do trabalho | Nova ramificação no ciclo existente; resumo conferido, estado e fontes preservados |
| 8 · [20:02](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=1202s) | Perguntar sobre arquivo antes de carregá-lo no agente | Explicitado no fluxo de contexto; leitura original antes de citar ou editar |
| 9 · [23:39](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=1419s) | Mesmas perguntas em vários arquivos, com paralelismo | Incorporado ao contexto: escopo, limite do lote, reserva e registro dos itens não analisados |
| 10 · [29:28](https://www.youtube.com/watch?v=_U-O5lYhJ7Q&t=1768s) | Agente formula perguntas ao Jev e classifica falhas | Incorporado à orquestração e avaliação; diagnóstico separado da prova por testes |

## Conferência no código associado

Os caminhos abaixo pertencem a `apps/ten-levels/src/levels/`, na revisão indicada.

- [level03/ticket-priority.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level03/ticket-priority.ts) e [normalize.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level03/normalize.ts): perguntas separadas, normalização e soma ponderada. A arquitetura reaproveita a separação, com critérios próprios; não copia os pesos nem usa a média para compensar uma condição crítica.
- [level07/should-compact.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level07/should-compact.ts) e [pick-cut-point.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level07/pick-cut-point.ts): mudança de tarefa, fim de etapa, dependência do histórico e operação em andamento. O código combina esses sinais com a ocupação; a indicação de corte vira instrução para o agente produzir o resumo. Os limites de 6k/10k/14k são definidos para a demonstração.
- [level08/read-state.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level08/read-state.ts), [level09/ask-files.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level09/ask-files.ts) e [prune.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level09/prune.ts): leitura fora do contexto principal, paralelismo limitado, resultados por caminho e lista de exclusões. Para o JEV, o lote também precisa de seleção prévia dos arquivos permitidos e reserva monetária compartilhada.
- [level10/ask.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level10/ask.ts), [assemble.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level10/assemble.ts) e [tool-description.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level10/tool-description.ts): o agente fornece perguntas e referências, o código monta o estado. A técnica foi aproveitada para classificações e investigação; resultado numérico de teste continua sendo extraído em código.
- [level06/bash-gate.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level06/bash-gate.ts) e [write-gate.ts](https://github.com/disler/ten-levels-of-jev/blob/777adaf47d37ae0553220d35b2f15b3a3a063305/apps/ten-levels/src/levels/level06/write-gate.ts): parecer antes de comandos e escrita. A classificação semântica permanece subordinada às permissões e às regras determinísticas do JEV.

## Conteúdo excluído da edição

- Comparações de preços, multiplicadores de economia e tempos das demonstrações: não medem o trabalho completo no JEV.
- Cortes fixos de confiança, limites de contexto e quantidades de arquivos: dependem da tarefa, do transporte e da avaliação local.
- Alegações de bloqueio infalível de comandos ou de injeção: conflitam com as falhas já documentadas no estudo local.
- Chamar a probabilidade ou a confiança do modelo de “intervalo de confiança”: não corresponde ao significado estatístico do termo.
- Recrutamento, patrocínio, análise de ideias, jogos, interfaces e divulgação comercial: não acrescentam uma política necessária a esta arquitetura.
- Repetição de decisões binárias, saídas tipadas, roteamento e comparação A/B: os fluxos existentes já contêm esses princípios.

## Registro da análise

Leitura integral da transcrição automática em inglês (1.088 segmentos), descrição e capítulos do vídeo; conferência estática dos doze arquivos acima e da extensão de compactação. A extração usou a biblioteca local `youtube_transcript_api`; o serviço DeepAPI não tinha configuração disponível. Transcrição e cópias de inspeção estão em `tmp/video-jev-20260928/`, fora do acervo versionado.

SHA-256 da transcrição JSON: `cacc48662a9699cbc95607ae09a1637458dff1fd791bdecd251307f714df1f13`.

O código externo foi consultado como fonte. As demonstrações e os testes desse repositório não foram executados nesta revisão. As contribuições foram incorporadas ao documento de arquitetura; os resultados experimentais locais anteriores permanecem identificados por suas datas e fontes.
