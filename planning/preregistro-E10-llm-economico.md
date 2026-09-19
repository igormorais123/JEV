# Pré-registro E10 — o braço do LLM econômico

**Registrado em 19 de setembro de 2026, antes de qualquer chamada paga a este modelo.**

## Por que este experimento existe

O plano científico abriu com a pergunta P1: *vale um LLM especializado aqui, ou qualquer
classificador de linguagem resolve?* O estudo respondeu metade dela. Comparou o Jev contra uma
**regra congelada escrita por mim** e mostrou vantagem larga e replicada. Nunca comparou o Jev
contra outro modelo de linguagem barato no mesmo contrato.

A décima terceira rodada de revisão adversarial (Grok 4.6 via Cursor) apontou isso como o
defeito central do desenho, e o apontamento procede: um comparador que eu mesmo escrevi e
congelei é o comparador mais fácil de vencer que existe. Enquanto o único braço de comparação
for esse, a recomendação "use o Jev" não se distingue de "use qualquer coisa melhor que uma
lista de palavras-chave".

## Hipótese

**H0:** um LLM genérico e barato, com a mesma rubrica e o mesmo corpus, acerta tanto quanto o
Jev na triagem.

**H1:** o Jev acerta mais.

Note que **H0 é a hipótese que ameaça a recomendação deste relatório**, e é ela que este
experimento tenta preservar, não derrubar. Se H0 sobreviver, a seção 1 do relatório final tem de
ser reescrita.

## Desenho

- **Corpus:** os 40 casos do conjunto de confirmação (`data/corpus/triagem-confirmacao.jsonl`),
  que é a partição de teste. O piloto não entra: ele guiou o desenho do prompt do Jev e usá-lo
  aqui favoreceria o Jev.
- **Comparador:** `meta-llama/llama-3.1-8b-instruct` via OpenRouter. Escolhido por ser
  econômico, de porte comparável ao anotador do E8 e **diferente dele** — usar o `qwen2.5:7b`
  faria do anotador juiz de si mesmo.
- **Mesma tarefa:** as mesmas cinco classes, os mesmos critérios e as mesmas instruções que o
  Jev recebeu no E1 e no E7, sem exemplos e sem ajuste. Nenhum prompt foi afinado contra estes
  40 casos: o prompt é o que o E1 congelou.
- **Métrica primária:** acurácia sobre casos programados, sob os três gabaritos (autor, anotador
  independente e adjudicado), reportada como faixa, como todo o resto do painel.
- **Métrica pareada:** McNemar exato sobre os casos em que os dois discordam, mais o bootstrap
  de famílias, igual ao E1 e ao E7.
- **Erro grave:** `cancelar` indevido, reportado separadamente, como manda o pré-registro do E1.

## Regra de decisão, congelada antes de olhar

1. Se o intervalo de 95% da diferença pareada (bootstrap de famílias) **contiver zero**, o
   resultado é **ausência de evidência de vantagem**, não equivalência — com 10 famílias o poder
   é baixo por construção, e um empate aqui não prova empate.
2. Se contiver zero, a seção 1 do relatório final muda de "use o Jev" para **"não há evidência
   de que o Jev supere um LLM econômico nesta tarefa"**, e o desconto de confiança por ausência
   de comparador é substituído por um desconto por comparador que empatou.
3. Se o limite inferior ficar acima de zero, a vantagem do Jev passa a ter um comparador que não
   fui eu que escrevi, e o desconto de 0,10 da nota de confiança é retirado.
4. Qualquer resposta que não respeite o contrato (classe fora das cinco, JSON inválido) conta
   como **erro**, não é reexecutada e não é descartada. Descartar resposta malformada do
   comparador e não do Jev seria fraudar a comparação.

## Orçamento

A regra desta casa é reservar o **pior caso publicado**, não o payload estimado, porque o
provedor acrescenta tokens que o cliente não vê. Para este modelo o contexto publicado é de
131.072 tokens de entrada, a US$ 0,05/M: **US$ 0,0065536 por chamada só de entrada**.

A saída é diferente: o endpoint de chat aceita `max_tokens`, e um teto que o servidor respeita é
um teto verificável. Fixo **`max_tokens` = 64**, o que basta para a resposta pedida (uma classe
e uma confiança) e custa US$ 0,00000512 por chamada.

Pior caso por chamada: **US$ 0,00655872**. Nas 40: **US$ 0,2623488**. Teto do bloco fixado em
**US$ 0,30**, com reserva atômica antes de cada chamada. O gasto real será uma fração disso — o
prompt tem centenas de tokens, não 131 mil — mas o que a carteira bloqueia é o pior caso.

Gasto acumulado do estudo antes deste experimento: US$ 0,018174462 de US$ 5,00. Mesmo no pior
caso integral, o estudo termina abaixo de US$ 0,29.

*(Este parágrafo foi corrigido antes da primeira chamada. A versão escrita minutos antes
declarava um pior caso de US$ 0,000108 por chamada, calculado sobre 2000 tokens de entrada que
eu estimara do payload — exatamente a estimativa que o executor financeiro foi construído para
recusar. Nenhuma chamada havia sido feita quando a correção entrou.)*

## O que este experimento não pode concluir

Não pode dizer que *nenhum* LLM econômico resolve a tarefa: testa um. Não pode dizer que o Jev é
melhor em produção: o corpus continua sendo escrito por mim. E não resolve a validade do
constructo, que depende de anotadores humanos e segue como item 2 da seção 10.
