# Pré-registro E7 — conjunto de confirmação da triagem

**Registrado em:** 2026-09-19, antes de qualquer chamada paga sobre este corpus.
**Corpus:** `data/corpus/triagem-confirmacao.jsonl` (40 casos, 10 famílias, 5 classes).
**Sistema sob teste:** Jev 1.13 via OpenRouter, contrato `choice`, instruções e critérios
**idênticos** aos do E1 (`executor/run_e1_triagem.py`, constantes `INSTRUCOES` e `CRITERIOS`).
Nada no prompt foi ajustado para este corpus.

## Por que este experimento existe

O E1 mostrou o Jev em 0,925 contra 0,600 da regra congelada. Mas o corpus do E1 é o mesmo que
usei para entender o contrato da API e calibrar o que perguntar. Um resultado forte nele mede,
em parte, o quanto o corpus foi desenhado para o sistema. O E7 responde outra pergunta:

> A vantagem se mantém em casos que nunca influenciaram o desenho?

## Hipótese

**H1:** a acurácia do Jev no conjunto de confirmação fica acima da acurácia da regra congelada,
com intervalo de confiança de 95% da diferença pareada que não contém zero.

**H0:** a diferença é compatível com zero.

## Desenho

- 40 casos novos, escritos para armadilhas que o E1 não cobria: gíria e erro de digitação,
  ação de terceiro, condicional não realizada, duas intenções com uma dominante, ação já
  concluída, negação explícita, vocabulário trocado (a palavra sugere uma classe e o pedido é
  outra), mensagem longa com ruído, pedido implícito e educado, ambiguidade resolvida na
  última frase.
- 10 famílias de 4 casos. **A família é a unidade de análise**: casos da mesma família
  compartilham a armadilha e não são independentes.
- Comparador: a mesma regra de palavras-chave congelada do E1 (`executor/baseline_regra.py`),
  sem nenhuma alteração. Ela não foi ajustada a este corpus, e é esperado que vá mal nas
  famílias G07 e G06 — esse é exatamente o ponto: medir quanto vale entender o pedido em vez
  de casar palavras.
- Chamadas individuais, uma pergunta por chamada, sem lote.
- Uma única passada por caso. Não haverá repetição nem voto majoritário.

## Critério de decisão, fixado antes

1. Diferença pareada Jev − regra, com intervalo de 95% por **bootstrap de famílias**
   (20.000 reamostragens, famílias sorteadas com reposição), o mesmo procedimento da Emenda 1
   do E1. A vantagem é considerada sustentada se o intervalo não contiver zero.
2. **Critério de replicação, o que de fato me interessa:** a diferença observada no E7 cai
   dentro do intervalo de 95% estimado no E1 ([0,150; 0,500])? Se cair, a vantagem replica.
   Se ficar abaixo de 0,150, houve otimismo no piloto e a recomendação muda.
3. Resposta ausente, inválida ou com erro de transporte conta como **erro** do Jev, e o caso
   entra no denominador. Não vou reportar acurácia condicional sem reportar a cobertura junto.

## O que este experimento NÃO resolve

- O corpus continua sendo autoral e de um só anotador: eu. Um segundo anotador cego é
  necessário para que o gabarito deixe de ser uma opinião bem documentada.
- Os casos são construídos, não colhidos de atendimento real, e a distribuição de classes é
  quase balanceada, o que não é a distribuição de um canal de verdade.
- Dois gabaritos foram reescritos antes da execução (`cnf-g05-01` e `cnf-g10-04`) porque
  roçavam em duas classes ao mesmo tempo. Um gabarito ambíguo não testa o modelo, testa o
  redator. A troca está registrada aqui e ocorreu **antes** de qualquer chamada.

## Orçamento

40 chamadas individuais, pior caso reservado US$ 0,001344 por chamada, teto do bloco
US$ 0,25. O teto global da carteira continua sendo US$ 5,00.

---

## Emenda 1 — 2026-09-19, depois da execução

Registrada depois de ver os resultados e declarada como tal.

**1. O critério 2 estava mal especificado.** Escrevi "a diferença cai dentro do intervalo do
piloto?" como se fosse um teste de duas caudas, mas o risco que eu queria cobrir é de uma cauda
só: um piloto otimista, com a vantagem encolhendo fora dele. A diferença observada foi **+0,650**,
acima do intervalo [0,150; 0,500]. Ler isso como "não replica" seria trocar um resultado por um
rótulo. O relatório passa a registrar os dois lados separados: `abaixo_do_ic_do_piloto` (que
ameaçaria a conclusão) e `dentro_do_ic_do_piloto`.

**2. A vantagem cresceu porque o comparador piorou, não porque o Jev melhorou.**
Jev: 0,925 no piloto → **0,975** na confirmação. Regra congelada: 0,600 → **0,325**. As famílias
G06 (negação explícita) e G07 (vocabulário trocado) foram escritas exatamente contra o casamento
de palavras-chave, e a regra não tem como acertá-las. Isso é informativo sobre o limite da regra,
não é evidência adicional sobre o Jev. A comparação honesta entre corpora é a do Jev consigo
mesmo: 0,925 contra 0,975, diferença de dois casos.

**3. O único erro do Jev tem gabarito contestável.** Em `cnf-g05-02` ("Devolvi o produto na
agência e tenho o comprovante. Preciso saber quando o novo será enviado."), meu gabarito é
`trocar` e o Jev respondeu `rastrear`. O pedido literal é sobre o envio de um item — o que é
rastreio — dentro de um processo de troca já em curso. Mantenho o gabarito e a contagem como
estão, e registro aqui que um segundo anotador poderia decidir diferente. Se decidisse, a
acurácia do Jev neste corpus seria 40/40, o que reforça a necessidade do segundo anotador em
vez de resolver a dúvida a meu favor.
