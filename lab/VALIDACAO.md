# Verificação da interface — 18/09/2026

## Concluído

- Oito testes automatizados do servidor: persistência/revisão, conflito concorrente, reconciliação de custo desconhecido, preservação de arquivo corrompido, bloqueio de arquivos privados, origem/host, valores inválidos/duplicação de custos e preservação das evidências existentes.
- Navegador Chrome: navegação entre áreas, 15 sistemas, filtro de família, abertura de fichas, paginação e seis decisões históricas incorretas.
- Acompanhamento salvo e recuperado após recarga em contexto isolado; importação de um pacote sintético de teste, reconhecimento de duplicata, rejeição de custo negativo, exportação de backup e consulta do registro completo.
- Cálculo conferido em fixture isolada: acurácia 2/3, macro-F1 2/3, precisão 1, recall 1/2; mediana 200 ms e p95 900 ms para tempos 100/200/900.
- Wilson: 16/16 produz limite inferior 0,8063923195; histórico individual 8/8 mostra 67,6% a 100%. Intervalo desativado para decisões agrupadas na mesma tentativa.
- Sem dados: acurácia indefinida, não zero. Valores ausentes não foram preenchidos como resultados.
- Inspeção visual em desktop e viewport móvel de 390 px; sem transbordamento horizontal nas telas conferidas e sem erros JavaScript.
- Os dados sintéticos de QA ficaram em um contexto descartável do navegador e em diretório temporário, sem entrar no arquivo do projeto.

O estado entregue permanece com **zero execuções novas**. As 96 decisões do Hermes continuam na base histórica separada. Nenhuma API de inferência foi chamada para construir ou testar a interface.

## Ajuste de foco

Terminal inicial com 30 rodadas planejadas e registro de atividade. Resultados e métricas abrem nos novos testes e mantêm uma aba de histórico de referência acessível. Dados anteriores preservados.
