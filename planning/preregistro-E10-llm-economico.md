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

---

# Emenda 1 — 2026-09-19, depois do resultado primário e antes da execução do E10b

**Motivo:** o resultado primário deu diferença pareada de +7,50% com IC95 [0,00%; 15,00%] sobre
10 famílias. O intervalo toca zero exatamente no limite inferior, e com 10 famílias o poder é
baixo por construção — coisa que este mesmo pré-registro já declarava. Um intervalo que encosta
em zero é o caso em que mais poder muda a leitura, e não usar as 10 famílias do piloto que estão
disponíveis, e custam US$ 0,0004, seria escolher a ignorância.

**O que muda:** o comparador roda também nos 40 casos do piloto (E1), somando 80 casos e 20
famílias.

**O que não muda:** o **resultado primário continua sendo o da partição de confirmação**, com o
número já publicado. A análise sobre as 20 famílias é **secundária e declarada como tal**,
porque tem um viés conhecido: o piloto guiou o desenho do prompt do Jev, e o comparador recebe
esse mesmo prompt sem nunca ter visto aqueles casos. O viés, portanto, **favorece o Jev**.

**Consequência disso para a leitura:** se o intervalo secundário **continuar contendo zero**, a
conclusão de ausência de evidência fica mais forte, porque sobreviveu a um teste enviesado a
favor do Jev e com o dobro das famílias. Se o intervalo secundário **separar de zero**, isso
**não** restabelece a recomendação: seria uma vantagem medida na partição que desenhou o prompt,
que é exatamente a leitura que o estudo inteiro recusa. Nesse caso a conclusão permanece a do
resultado primário, e a discrepância entra no relatório como o que ela é — o piloto favorecendo
quem foi desenhado nele.

Esta emenda foi escrita **antes** de qualquer chamada do E10b.

---

# Nota de verificação — 2026-09-19, depois de executar o E10b

A Emenda 1 declarou um viés: *"o piloto guiou o desenho do prompt do Jev"*, e por isso mandou
tratar o resultado das 20 famílias como secundário e incapaz de restabelecer a recomendação.

**Fui conferir no histórico e a premissa não se sustenta.** As instruções e os critérios entraram
no repositório uma única vez, no commit `9f6d13b` (18/09/2026), junto com o corpus piloto, e
**nunca foram alterados depois** — o único commit posterior a tocar o arquivo (`b493035`) não
mexeu no prompt. O corpus piloto também não mudou depois de rodar. Não houve, portanto, nenhuma
iteração de prompt contra os resultados do piloto.

Isso enfraquece o viés declarado, mas não o elimina, e sobra um viés menor que continua real: a
rubrica e o corpus piloto foram escritos **juntos**, então a rubrica "casa" com aquele corpus por
construção. Os dois modelos recebem a mesma rubrica, e o comparador nunca viu nenhum dos dois
corpora.

**Consequência para a leitura, escrita agora que os dois resultados estão na mesa e declarada
como pós-hoc:** a evidência está dividida, e dizer isso é mais fiel do que escolher um dos lados.

- Partição de teste (confirmação, 10 famílias): diferença +7,50%, IC95 [0,00%; 15,00%] — **não
  separa de zero**.
- Piloto (10 famílias): +20,00%, IC95 [10,00%; 30,00%] — separa.
- Os 80 casos, 20 famílias: +13,75%, IC95 [7,50%; 20,00%] — separa.

A recomendação final do estudo **não** volta a ser "use o Jev", porque a partição que existe para
decidir não sustenta isso sozinha e porque a decisão de olhar o piloto foi tomada depois de ver o
resultado primário. Também não é "os dois empatam", porque em 20 famílias eles não empatam. É a
terceira, que é a que os dados aguentam: **a evidência não é suficiente para decidir, e o
desempate custa US$ 0,0004 por conjunto de 40 casos.**

Registro o que não vou fazer: não vou eleger, agora, a leitura das 20 famílias como principal só
porque ela é a que favorece a conclusão que eu já tinha publicado antes do E10.
