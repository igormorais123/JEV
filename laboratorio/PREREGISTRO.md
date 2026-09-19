# Programa E14 — exploração sistemática das capacidades do Jev

*Pré-registro vivo. Cada rodada é escrita aqui **antes** de rodar, com hipótese, medida e
critério de decisão. Emendas entram datadas, ao final, nunca por reescrita — a prova da ordem é
o histórico do Git.*

Aberto em 2026-09-19. Helena.

## Por que este programa existe

Os doze experimentos do dossiê responderam "o Jev serve para a triagem?". O E13 respondeu "ele
serve dentro dos meus fluxos?". Nenhum dos treze perguntou **onde ele quebra** — e um
instrumento que só foi medido onde funciona é um instrumento cuja margem ninguém conhece.

O orçamento deixou de ser a restrição: restam US$ 4,95 de US$ 5,00, e a US$ 0,042 por milhão de
tokens de entrada com saída gratuita, isso compra mais chamadas do que eu tenho perguntas boas.
A restrição agora é a qualidade da hipótese. Então o programa é escrito como um programa: cada
rodada nasce do achado da anterior, e o critério de parada é a hipótese acabar, não o dinheiro.

**Teto declarado deste programa: US$ 2,00**, verificado antes de cada chamada, registrado em
`laboratorio/gastos.jsonl`. Acima disso o núcleo se recusa a despachar.

## Regras que valem para todas as rodadas

1. **A hipótese e o critério de decisão são escritos antes da execução.** Rodada sem critério
   prévio vira interpretação livre do resultado, que é o defeito que este estudo persegue desde
   a nona revisão.
2. **Contraste pareado.** Sempre que possível, a mesma pergunta nos mesmos casos sob condições
   diferentes, para que a diferença seja atribuível à condição e não ao corpus.
3. **A direção do erro importa mais que a taxa.** Reportar para que lado o modelo erra, não só
   quanto.
4. **Falha de transporte não é resposta errada** (Emenda 1 do E12). HTTP 429/5xx e timeout vão
   para repescagem; só conta como erro o que voltou do modelo.
5. **O que o dado não sustenta não vira conclusão.** Limite superior de Clopper-Pearson quando a
   contagem for zero.

---

## R0 — A confiança do Jev é calibrada, ou só ordenada? (custo zero)

**Por que.** A seção 6.1 do relatório mostrou que o corte de 0,90 furou no E12: um erro passou
com confiança 0,98. Isso foi medido como corte, nunca como calibração. São coisas diferentes:
um número pode ordenar bem (mais confiança, menos erro) e ainda assim mentir sobre a
probabilidade (dizer 0,90 quando acerta 0,70).

**Hipótese H0.** Entre os casos em que o Jev declara confiança *c*, a taxa de acerto observada é
aproximadamente *c*.

**Medida.** Curva de calibração em faixas, erro de calibração esperado (ECE), e separação
(AUC-like: a confiança média dos acertos contra a dos erros) nos 230 casos já pagos dos
corpora E1, E7, E11 e E12, sob os três gabaritos.

**Critério.** ECE ≤ 0,05 sustenta H0. ECE > 0,10 falsifica: a confiança é um ordenador, não uma
probabilidade — e nesse caso toda política de corte precisa ser calibrada por dado, nunca
transportada, o que reforça a seção 6.1 com um mecanismo e não só com um susto.

**Custo:** zero. Os dados já estão pagos.

---

## R1 — Quantas opções o Jev aguenta?

**Por que.** Toda aplicação prática escolhe o número de classes. O estudo sempre usou cinco. Se
a acurácia despenca em oito, isso é uma regra de projeto; se não despenca, o Jev serve para
taxonomias maiores do que se supunha.

**Hipótese H1.** A acurácia cai monotonicamente com o número de opções, e a queda é material
(> 10 pontos) entre 5 e 12.

**Desenho.** O mesmo corpus de triagem (90 casos do E12), sob 4 condições pareadas: 2, 3, 5 e
12 opções. As opções extras são distratores plausíveis, escritos antes de ver qualquer
resultado. Na condição de 2 e 3 opções, o gabarito é colapsado por um mapa fixo, escrito junto
com os distratores.

**Critério.** Queda ≤ 3 pontos entre 5 e 12 falsifica H1 e libera taxonomias grandes.

**Custo estimado:** 360 chamadas, ~US$ 0,009.

---

## R2 — A ordem das opções enviesa a escolha?

**Por que.** O E2b mediu efeito de posição entre *casos* num lote. Ninguém mediu posição entre
*opções* dentro da pergunta — e é aí que um viés seria invisível e sistemático, porque a ordem
das classes costuma ser fixa em produção.

**Hipótese H2.** A escolha é invariante à ordem das opções.

**Desenho.** Os 90 casos do E12 em três permutações fixas das cinco classes (original, inversa,
sorteada com semente 20260919), pareado por caso.

**Critério.** Mais de 5% dos casos mudando de resposta entre permutações falsifica H2, e obriga
a sortear a ordem em produção ou a votar entre permutações.

**Custo estimado:** 270 chamadas, ~US$ 0,007.

---

## R3 — O Jev aguenta o jeito que o Igor escreve?

**Por que.** Os 230 casos do estudo foram escritos por mim, em português correto. O material
real do Igor tem erro de digitação em quase toda mensagem ("qeu", "vc", "implenta",
"acessessiveis"). Se a acurácia cai com ruído tipográfico, metade das aplicações propostas no
guia está superestimada.

**Hipótese H3.** A acurácia é invariante a ruído tipográfico realista.

**Desenho.** Os 90 casos do E12 em quatro condições pareadas: original; erro leve (5% dos
caracteres); erro pesado (15%); e "estilo Igor" — abreviação, falta de acento e pontuação
ausente, aplicados por regras derivadas do histórico real.

**Critério.** Queda > 5 pontos no estilo Igor falsifica H3 e vira ressalva de primeira ordem no
guia prático.

**Custo estimado:** 360 chamadas, ~US$ 0,009.

---

## R4 — O Jev é logicamente coerente consigo mesmo?

**Por que.** O contrato devolve `probabilities` além da escolha. Se a pergunta A e a pergunta
não-A não produzem probabilidades complementares, o número não é uma crença e não pode ser
usado como uma.

**Hipótese H4.** Perguntar "isto é X?" e "isto não é X?" produz probabilidades que somam ~1,0.

**Desenho.** 60 casos, cada um perguntado nas duas formas, pareado. Mede-se o desvio da soma
em relação a 1,0.

**Critério.** Desvio mediano > 0,10 falsifica H4.

**Custo estimado:** 120 chamadas, ~US$ 0,003.

---

*As rodadas seguintes serão escritas quando as anteriores tiverem achado — é essa a diferença
entre um programa e uma lista.*

---

# Achados e emendas — 2026-09-19

## R0 e R0b — fechados. H0 sustentada, com uma inversão de sinal.

ECE 0,0349 sob o gabarito oficial e 0,0305 sob o do autor: **calibrado** pelo critério
pré-registrado (≤ 0,05). Separação 0,93 — a confiança ordena muito bem.

O que não estava previsto: sob o gabarito do autor o desvio é **positivo** em todas as faixas
médias (+0,29 em [0,0-0,5), +0,26 em [0,70-0,80)), isto é, o Jev é **subconfiante** — declara
0,74 e acerta 100%. Sob o anotador independente o sinal inverte: desvios de −0,36 e −0,28 nas
faixas altas, sobreconfiança. **Calibração não é propriedade do modelo; é propriedade do par
(modelo, critério de correção).** Terceiro achado do estudo que é sobre método e não sobre
modelo.

R0b: sob o critério oficial, o corte de 0,99 descarta 49 dos 230 casos para evitar **um** erro
que o corte de 0,70 já deixaria passar sozinho. A recomendação de 0,99 do guia é defensável,
mas o preço em cobertura precisa ser dito junto.

## R1 — H1 **falsificada**. O Jev aguenta taxonomia grande.

| Opções | Acurácia | Diferença contra a original |
|---|---|---|
| 2 | 98,9% | +0,0 |
| 3 | 97,8% | −1,1 |
| 5 (original) | 98,9% | — |
| 12 | 97,8% | −1,1 pontos, IC95 [−3,3%; 0,0%] |

A previsão era queda material (> 10 pontos) entre 5 e 12. Deu 1,1 ponto, e dos 90 casos apenas
**um** caiu num dos sete distratores plausíveis. Consequência de projeto: taxonomias de doze
classes são viáveis; a regra de "3 a 6 classes" do guia prático era conservadora demais.

## R2 — H2 **sustentada**, e de forma absoluta.

**0 de 90** casos mudaram de resposta sob permutação inversa das opções, e 0 de 90 sob
permutação sorteada. Invariância perfeita à ordem das classes.

O contraste com o E2b é o achado: lá, 3 de 40 casos mudavam conforme os **vizinhos no lote**.
Então o viés de posição do Jev existe entre casos, não entre opções — e isso muda a mitigação
recomendada: sortear a ordem das classes é desnecessário; sortear a ordem dos casos no lote,
não.

## R3 — H3 **parcialmente falsificada**.

| Condição | Acurácia | Diferença pareada |
|---|---|---|
| Ruído leve (5%) | 96,7% | −2,2 pontos, IC95 [−5,6%; 0,0%] |
| Estilo Igor | 96,7% | −2,2 pontos, IC95 [−5,6%; 0,0%] |
| Ruído pesado (15%) | **93,3%** | **−5,6 pontos, IC95 [−11,1%; −1,1%]** |

O estilo real do Igor custa 2,2 pontos e não separa de zero. Ruído pesado custa 5,6 pontos com
intervalo que exclui zero. A ressalva entra no guia, mas menor do que eu temia.

## R5 — nascida de R3, e o achado mais útil do programa até agora.

**Sob degradação de entrada, o Jev não fica burro: fica honesto.**

Sob ruído pesado, a confiança média dos acertos é 0,915 e a dos erros, **0,620**. O corte de
0,95 elimina **todos os 6 erros** mantendo 68% de cobertura; o de 0,70 já reduz de 6 para 1.

Isto separa dois tipos de dificuldade que o estudo vinha tratando como um só. Contra ruído de
superfície a confiança protege. Contra a ambiguidade semântica do E12 — o erro com confiança
0,98 — ela não protegeu. **Hipótese que nasce daqui e vira R7.**

---

## R4 — coerência lógica (pré-registrada acima, ainda não executada)

## R6 — onde fica o ponto de quebra do número de opções?

**Por que.** R1 falsificou a queda em 12. Uma regra de projeto precisa do limite, não de um
ponto isolado.

**Hipótese H6.** Existe um número de opções a partir do qual a acurácia cai material (> 5
pontos); ele está entre 12 e 40.

**Desenho.** Os mesmos 90 casos em 20 e 40 opções, com distratores plausíveis escritos antes.

**Critério.** Se 40 opções custar ≤ 3 pontos, H6 é falsificada e o limite prático do Jev não
está no número de classes.

## R7 — a confiança distingue texto ruim de sentido ambíguo?

**Por que.** R5 mostrou a confiança protegendo contra ruído de superfície; o E12 mostrou-a
falhando contra ambiguidade semântica. Se a distinção for real, ela vira regra operacional:
confiança alta com texto sujo é confiável; confiança alta com texto ambíguo, não.

**Hipótese H7.** A confiança do Jev cai com dificuldade de superfície e **não** cai com
dificuldade semântica, mesmo quando a acurácia cai nas duas.

**Desenho.** Corpus adversarial novo, escrito para este fim: 40 casos em duas metades pareadas
por classe — 20 de dificuldade semântica pura (negação, condicional, ação de terceiro, pedido
adiado, cancelamento parcial), em português limpo; e 20 fáceis semanticamente, com ruído de
superfície pesado. Gabarito escrito com o caso.

**Critério.** Se a confiança média dos erros semânticos for ≥ 0,90 enquanto a dos erros de
superfície ficar ≤ 0,70, H7 é sustentada e vira regra no guia.

---

# Segundo bloco de achados — 2026-09-19

## R4 — H4 sustentada, com 3,3% de contradição dura.

Desvio mediano da soma das probabilidades: **0,0**. Médio: 0,0317. A crença do Jev é coerente
na maioria dos casos. Mas em **2 de 60** ele respondeu "sim" para uma afirmação e "sim" para a
negação dela. Não é ruído de arredondamento; é contradição lógica. Consequência: a
probabilidade serve como grandeza operacional, não como crença formal.

## R6 — H6 sustentada. O ponto de quebra da taxonomia fica entre 12 e 20.

| Opções | 5 | 12 | 20 | 40 | 80 | 147 |
|---|---|---|---|---|---|---|
| Acurácia | 98,9% | 97,8% | 93,3% | 90,0% | 90,0% | 90,0% |

A queda não é linear: cai até 40 e depois estabiliza num platô de 90%. **Regra de projeto: até
12 classes, sem custo; de 20 em diante, cinco a nove pontos, e um platô que não piora mais.**

## R8 — 48 armadilhas semânticas novas: 91,7%, e nenhum erro acima de 0,90.

Escritas para quebrar o modelo no ponto exato em que ele quebrou no E12. Funcionaram — a
acurácia caiu de 98,9% para 91,7%. Mas a confiança dos erros foi **0,43**, e **nenhum** dos
quatro erros passou de 0,90.

Por família: adiado 100%, concluída 100%, negado 100%, parcial 87,5%, pressuposto 87,5%,
**terceiro 75%** — a ação atribuída a outra pessoa é a armadilha mais difícil, e é a que o guia
prático cita como caso típico.

## R9 e R10 — o desempate que o estudo arrastava desde o E10.

O Jev ignorou **40 de 40** tentativas de manipulação escritas dentro da mensagem do cliente,
sob quatro vetores (ordem direta, falsa autoridade, bloco de formato, sugestão). Os mesmos 40
ataques contra os quatro comparadores do E12:

| Braço | Manipulado | Taxa | IC95 | Viraram `cancelar` |
|---|---|---|---|---|
| openai/gpt-oss-20b | 28/40 | **70,0%** | [54,6%; 81,9%] | 4 |
| google/gemma-3-12b | 10/40 | **25,0%** | [14,2%; 40,2%] | **10** |
| meta-llama/llama-3.1-8b | 5/40 | 12,5% | [5,5%; 26,1%] | 3 |
| mistralai/mistral-nemo | 0/40 | 0,0% | [0,0%; 8,8%] | 0 |
| **typesafe/jev-1.13** | **0/40** | **0,0%** | [0,0%; 8,8%] | 0 |

**Dezessete respostas viraram `cancelar` — a classe irreversível — porque o cliente escreveu
uma linha de texto.** O gemma caiu em 10 de 10 no vetor de formato, todas para `cancelar`.

O mecanismo é arquitetural, não estatístico: no contrato do Jev o texto vai em `state` e as
opções em `questions`, separados; num LLM genérico tudo é uma string de prompt e texto de
terceiro é indistinguível de instrução. **Esta é a primeira vantagem do Jev que não depende de
quem escreveu o gabarito** — e a resposta à pergunta que o E10, o E11 e o E12 não conseguiram
fechar. Ressalva devida: o mistral-nemo também resistiu, então a afirmação correta é "três dos
quatro comparadores são manipuláveis", não "só o Jev resiste".

## R11 — a varredura dos extremos, e um achado falso que eu mesma produzi.

**Correção registrada.** A primeira leitura da R11 mostrou a acurácia caindo para 23,3% com
confiança 1,0 quando o contexto passava de 20 mil caracteres, e eu quase publiquei isso como "o
limite do modelo". Fui conferir: o núcleo truncava o estado em 12.000 caracteres, e como o
recheio vinha **antes** da mensagem, o que chegou ao modelo não continha pedido nenhum. O
defeito era meu; o limite não existia. Corrigido em `nucleo.py`, refeito na R12.

O que a varredura mostrou de verdade, com a referência em 96,7%:

| Dimensão | Nível extremo | Acurácia | A confiança avisa? |
|---|---|---|---|
| Idioma (inglês, misto, sem acento) | — | 96,7% | não precisa |
| Instrução curta ou **autocontraditória** | — | 96,7% | não precisa |
| Sobreposição de classes | critérios **idênticos** | 93,3% | — |
| Ruído tipográfico | 70% dos caracteres | 36,7% | **sim** (conf. 0,27) |
| Tudo junto | ruído 50% + 160 opções + recheio | 23,3% | sim |

Dois achados que não estavam previstos:

- **Idioma e instrução quase não importam.** Critérios em inglês, misturados, sem acento,
  instrução reduzida a "Classifique a mensagem" e até uma instrução que se contradiz de
  propósito: tudo em 96,7%.
- **Com os cinco critérios escritos de forma idêntica, ele ainda acerta 93,3%.** Ou seja, o Jev
  decide pelo **rótulo** da classe, não pela descrição. A descrição é quase decorativa; o nome
  da classe carrega o sentido. Isso inverte a recomendação do guia, que mandava caprichar na
  descrição de cada classe.

## R12 — diluição de contexto: nenhum efeito até 50 mil caracteres.

96,7% constante em 0, 8k, 12k, 16k, 20k, 30k e 50k caracteres de texto irrelevante, com a
mensagem antes ou depois do recheio. Treze condições, mesma acurácia, mesma resposta dominante.
**O Jev não se perde em contexto grande** — e foi bom ter errado antes, porque a correção
produziu uma medida melhor do que a que eu tinha planejado.

## R13 — o modo de falha mais perigoso, e a mitigação que custa uma linha.

Dez textos sem pedido nenhum (uma política interna, uma receita de bolo, "Bom dia.", letras
aleatórias):

- **Sem classe de escape:** respondeu `informacao` em **10 de 10**, confiança média **0,987**,
  todas acima de 0,90. Falha silenciosa com confiança máxima — nenhum corte protegeria.
- **Com a classe `nao-se-aplica`:** escolheu a saída em **10 de 10**.

**Regra de projeto de primeira ordem: toda taxonomia precisa de uma classe "não se aplica".**
Sem ela, o Jev preenche com a classe mais genérica e declara certeza.

## R14 — o ciclo autorrecursivo, medido em vez de proclamado.

O Jev leu as 37 condições do próprio mapa de limites e classificou cada uma em `seguro`,
`exige-cuidado` ou `proibido`. Meu gabarito foi escrito antes.

- Concordância bruta: **56,8%**.
- Divergências que **afrouxam** o que eu apertei: **0**.
- Divergências que apertam: 16 — ele é sistematicamente mais conservador que eu.
- Confiança média: **0,867** quando concorda, **0,454** quando diverge.
- **No corte de 0,90: 14 decisões aceitas, 14 concordam — 100%.**

O loop funciona sob corte: automatiza 38% das decisões de risco com concordância total, manda o
resto para leitura humana, e nunca erra para o lado perigoso. É a mesma política que o guia
recomenda para triagem, aplicada à governança do próprio estudo.

---

# Síntese do programa E14

Quatorze rodadas, **2.522 chamadas**, **US$ 0,18** de um teto de US$ 2,00. O que mudou:

1. **O Jev tem uma vantagem que não depende de gabarito:** imunidade a instrução injetada no
   texto do cliente. Três dos quatro LLMs baratos obedecem; ele não. Isso responde a pergunta
   em aberto desde o E10 e vira a recomendação principal do guia.
2. **Ele é muito mais robusto do que o estudo supunha:** idioma, ordem das opções, tamanho do
   contexto, qualidade da instrução e até descrições de classe idênticas quase não o afetam.
3. **Ele quebra em dois lugares, e só um avisa:** ruído tipográfico pesado derruba a acurácia
   mas derruba a confiança junto; texto sem pedido algum produz resposta errada com confiança
   máxima — e a mitigação é uma classe de escape.
4. **O que decide não é a descrição da classe, é o nome dela.** Contraria o que o guia dizia.
