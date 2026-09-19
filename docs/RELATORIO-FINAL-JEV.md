# Jev 1.13 — relatório final de avaliação

**Autoria:** Dra. Helena Strategos, Cientista-Chefe de Inteligência da INTEIA
**Execução:** 18–19 de setembro de 2026
**Sistema avaliado:** Jev 1.13 (`typesafe/jev-1.13` via OpenRouter e `jev-1.13.0` direto)
**Custo total:** US$ 0,035707114 em 1.474 chamadas, de um teto autorizado de US$ 5,00, conciliado contra um extrato de provedor de US$ 0,034640289
**Código, dados e registros:** este repositório, com pré-registros em `planning/` e relatórios
brutos em `runs/`

---

## 1. Recomendação

**O Jev supera quatro LLMs genéricos e baratos nesta tarefa, em corpus novo e pré-registrado,
sob o gabarito adjudicado por um terceiro juiz cego — e não supera nenhum deles de forma
estatisticamente distinguível sob o gabarito do único anotador que não passou pela minha mão. A
replicação com o triplo de famílias e o quádruplo de comparadores não moveu essa divergência, e
é isso que este estudo tem de mais sólido a dizer: o gargalo não é a amostra, é o rótulo.**

Esta é a **sexta** versão da recomendação deste relatório, e vale registrar a sequência porque
ela é o método:

1. *"Use o Jev com corte de confiança em 0,90"* — antes de existir qualquer comparador que não
   fosse uma regra que eu mesma escrevi.
2. *"Não adote"* — quando o E10 comparou o Jev a `meta-llama/llama-3.1-8b-instruct` na partição
   de teste e a diferença não separou de zero.
3. *"Evidência dividida"* — quando o E10b, no piloto, separou.
4. *"O gargalo é o rótulo"* — quando o E11, em corpus novo, deu vantagem clara sob o meu
   gabarito e sinal invertido sob o do anotador independente.
5. *"Vantagem do Jev no gabarito adjudicado"* — quando os 10 desacordos do E11 foram a um
   terceiro juiz cego e ele **confirmou meu gabarito em 10 de 10**.
6. Esta, quando o E12 replicou tudo com 30 famílias novas e **quatro** comparadores de quatro
   fornecedores, o segundo juiz cego confirmou meu gabarito em outros 10 de 10, e a divergência
   entre os gabaritos **continuou exatamente onde estava**.

**O resultado da replicação (E12), nos três gabaritos, contra os quatro comparadores:**

| Gabarito | Jev | llama-3.1-8b | mistral-nemo | gemma-3-12b | gpt-oss-20b | Leitura |
|---|---|---|---|---|---|---|
| Adjudicado (oficial) | 0,9889 | 0,8778 | 0,9111 | 0,8444 | 0,8444 | vantagem em todos |
| Meu, sem adjudicar | 0,9889 | 0,8778 | 0,9111 | 0,8444 | 0,8444 | vantagem em todos |
| Anotador independente | 0,9000 | 0,9000 | 0,8556 | 0,8222 | 0,7111 | **sem evidência** |

As diferenças pareadas, no gabarito oficial, vão de +7,8% (IC95 [3,3%; 13,3%], contra o
mistral-nemo) a +14,4% (IC95 [7,8%; 21,1%] e [6,7%; 22,2%], contra o gemma e o gpt-oss). Sob o
gabarito do anotador independente, a diferença contra o llama-3.1-8b é **exatamente zero**
(IC95 [−6,7%; 6,7%], McNemar p = 1,0000) e o intervalo contém zero também contra o mistral-nemo
e o gemma. A regra de leitura estava congelada antes de existir um único caso: só há vantagem se
o intervalo separar de zero contra **todos**, e a conclusão só é reportada como vantagem se
sobreviver aos três gabaritos. Ela não sobreviveu, e o veredito pré-registrado é
`depende-do-gabarito`.

**O resultado do desempate anterior (E11), que o E12 replica:**

| Gabarito | Jev | llama-3.1-8b | Diferença | IC95 | McNemar |
|---|---|---|---|---|---|
| Adjudicado (oficial) | 1,0000 | 0,8667 | **13,3%** | [5,0%; 21,7%] | p = 0,0078 |
| Meu, sem adjudicar | 1,0000 | 0,8667 | 13,3% | [5,0%; 21,7%] | p = 0,0078 |
| Anotador independente | 0,8333 | 0,8667 | −3,3% | [−10,0%; 3,3%] | p = 0,6875 |

**Por que a quarta versão estava errada, e quem mostrou isso.** A décima quarta rodada de
revisão adversarial apontou que eu havia enterrado um resultado pré-registrado usando como ouro
um modelo de 7B cujas discordâncias seguem um padrão conhecido: classificar pelo **vocabulário
presente** na mensagem em vez do ato de fala pedido — que é exatamente o modo de falhar da regra
congelada que o Jev supera desde o E1. E apontou que o E8 tinha um procedimento para isso, o
terceiro juiz cego, e que o E11 havia parado antes dele. Os dois pontos procedem. Escrevi a
emenda com a regra de leitura **antes** de rodar o juiz, declarando que se ele confirmasse meu
gabarito a conclusão mudaria contra a que eu acabara de publicar. Ele confirmou
10 de 10, sem nenhum caso em que declarasse
ambiguidade ou propusesse terceira leitura.

**O que isto autoriza afirmar:** neste corpus, com esta rubrica e contra este comparador, o Jev
é melhor, e a diferença é grande o bastante para sobreviver ao agrupamento por família. No erro
grave (`cancelar` indevido) **o Jev não cometeu nenhum sob nenhum dos três gabaritos**; o
comparador cometeu um sob dois deles e nenhum sob o terceiro — o detalhe está na seção 3.10, e
ele é menos favorável do que a versão anterior desta frase dizia.

**O que isto não autoriza:** que a rubrica meça o que diz medir. Os três anotadores deste estudo
— eu, o anotador independente e o terceiro juiz — produzem rótulos, e dois deles são modelos de
linguagem enquanto o terceiro sou eu, que escrevi o corpus. Concordância entre modelos sobre uma
rubrica que eu redigi mede reprodutibilidade, não validade. Enquanto duas pessoas do atendimento
real não anotarem os mesmos casos e medirem kappa entre si antes de olhar qualquer modelo, toda
conclusão deste relatório repousa sobre um rótulo não validado. É o item 3 da seção 10, custa
tempo de gente e não custa orçamento.

*(Registro de método: nenhuma das cinco versões foi apagada, e três delas contrariaram o que eu
tinha acabado de publicar. A quarta foi corrigida por uma crítica externa que eu poderia ter
ignorado — ela dizia que meu rigor tinha virado o seu contrário, e estava certa.)*

---

### 1.1 A política de corte, que continua válida no que ela mede

O restante desta seção descreve a política de aceitação estudada no E9. **Ela não é uma
recomendação de adoção, e não deve ser lida como uma.** O corte de 0,90 nunca foi
pré-registrado: foi lido nos erros do piloto e depois avaliado sobre os mesmos erros, o que a
seção 8 já registra ao dizer que `confidence` foi validado como ordenador e não como
probabilidade. Ela está aqui porque mede uma coisa real — quanto do volume um corte cobre e ao
custo de quê —, e essa medida é útil para desenhar o piloto em sombra do item 4 da seção 10.
Usá-la como política operacional exigiria pré-registrar o corte num corpus que ele não tenha
visto.

A política concreta que os dados sustentam: aceitar automaticamente as decisões com confiança
≥ 0,90 e encaminhar o restante para uma pessoa. Na partição de confirmação — os 40 casos que não
guiaram o desenho, que é a leitura que vale para decidir — essa política aceita **87,5%** sem
nenhum erro observado entre os aceitos; na união dos 80 casos, aceita 80%, também sem erro
observado. Os erros do modelo — quatro no gabarito do autor, três no oficial — têm todos confiança abaixo
de 0,90.

**A base é pequena e o número precisa ser lido assim:** são 3 erros em 80 casos no gabarito
oficial (4, no do autor). "Nenhum erro
entre os aceitos" descreve o que foi observado, não uma garantia; a seção 6 traz o limite
superior que sobra depois de respeitar o agrupamento por família. Sob os parâmetros da seção 7 —
declarados, nunca cronometrados — e **na mesma partição de confirmação**, a política leva o custo
por decisão de US$ 0.400 para
US$ 0.050. Na união dos 80 casos, onde a cobertura cai para
80%, o mesmo corte custa US$ 0.080. Citar a cobertura de uma
partição com o preço da outra descreveria uma política que não existe.

**O que impede a recomendação de ir além disso:** o modelo não é determinístico. O mesmo caso,
sozinho e repetido cinco vezes, pode mudar de resposta. Um sistema que decide sozinho precisa
responder igual à mesma pergunta, e este não responde.

**Acurácia do modelo nestes 80 casos: entre 0,8875 e
0,9625, conforme o gabarito adotado** — 0,8875
sob o gabarito do anotador independente, 0,95 sob o meu, e
0,9625 sob o adjudicado, que é o oficial **porque foi declarado antes**, não porque é o mais
alto. Reportar só o número mais alto seria escolher o gabarito depois de ver o resultado, e é
por isso que o painel exibe a faixa.

*(Correção registrada na décima terceira rodada: até aqui esta frase chamava o adjudicado de "o
mais defensável dos três". A revisão adversarial apontou que essa é exatamente a manobra que o
resto do documento condena — o adjudicado dá o teto da faixa, e dois dos três anotadores que o
produziram passaram pela minha mão. O único gabarito que não passou é o do anotador
independente, que dá o piso, 0,8875. Nenhum dos três é "o mais defensável"; o que existe é a
faixa.)*

*(Correção registrada: até a décima primeira rodada de revisão, este parágrafo dizia "entre
0,8875 e 0,9750". O 0,9750 não é gabarito nenhum destes 80 casos — é a acurácia do E7 isolado,
que tem 40. Misturar denominadores é o mesmo vício que eu vinha corrigindo no painel, e ele
estava aqui.)*

**Confiança: 0,35.** Este número deixou de ser
um julgamento meu e passou a ser uma conta com as penalidades declaradas, partindo de 1,0:

- a política se apoia em 40 casos, menos de cem (-0,20)
- 1 caso(s) mudam de resposta entre repetições idênticas (-0,10)
- o gabarito foi adjudicado por modelos, não por pessoas do domínio (-0,10)
- corpus construído pelo avaliador, não colhido de uso real (-0,10)
- zero erro observado entre os aceitos, mas o limite superior de 95% por família é 25,9% (-0,10)
- o comparador econômico foi vencido no gabarito adjudicado, mas os três anotadores que produziram esse gabarito são modelos de linguagem (-0,05)

Os dois últimos descontos entraram na décima terceira rodada, cobrados pela revisão
adversarial: o teto de erro já estava escrito na seção 6 e não era descontado, e o braço do LLM
econômico não existia. Depois que ele passou a existir e empatou, o desconto por ausência de
comparador (-0,10) virou desconto por comparador que não separou de zero (-0,20). A nota caiu de
0,5 para 0,2 sem que nenhum dado do Jev piorasse: o que mudou foi o que se sabe sobre a
alternativa. A conta
está em `executor/placar.py:confianca_calculada`, e é para ser contestada: se alguém achar que
um desconto está errado, o lugar de discutir é o código, não a minha impressão.

---

## 2. Achado principal

**A confiança que o modelo reporta é informativa, e essa é a descoberta com mais valor
operacional do estudo.**

Não era óbvio. `confidence` é um número que o modelo emite sobre a própria resposta; nada
garante que corresponda a probabilidade de acerto. Mas nos dois corpora, todos os erros
ficaram concentrados abaixo de 0,90, e nenhum caso aceito acima desse corte estava errado.
É isso que torna viável uma política de triagem com revisão seletiva, em vez de revisão total.

A ressalva é grande e vai na seção 8: zero erro entre os aceitos não é taxa de erro zero.
Respeitando o agrupamento por família, o limite superior do erro ainda chega a 25,9%.

**E há uma ressalva maior, descoberta depois, na seção 6.1:** isso valeu nos dois primeiros
corpora e **não se repetiu no terceiro**. No corpus novo do E12, o único erro do modelo veio com
confiança 0,98 — acima de qualquer corte que este relatório vinha recomendando. A confiança
continua informativa; ela não é garantia, e o corte precisa ser recalibrado em cada material
novo.

---

## 3. Evidência

### 3.1 Comparação contra comparadores congelados

Os três primeiros resultados abaixo usam o **gabarito do autor**, como pré-registrado. O
gabarito oficial do estudo, depois da adjudicação da seção 3.6.1, está na seção 3.6 e move os
números para cima; mantenho os dois porque trocar de gabarito depois de ver o resultado é
exatamente o que um pré-registro existe para impedir.

| Experimento | Jev | Comparador | Diferença pareada (IC95, bootstrap de famílias) |
|---|---|---|---|
| **E1** triagem, piloto (40 casos, 10 famílias) | 0,925 | regra de palavras-chave 0,600 | **+0,325** [0,150; 0,500] |
| **E3** suporte por evidência (24 casos, 6 famílias) | 0,958 | regra ingênua 0,625 | **+0,333** [0,250; 0,417] |
| **E7** triagem, confirmação (40 casos, 10 famílias) | 0,975 | mesma regra congelada 0,325 | **+0,650** [0,525; 0,775] |

O E7 é o experimento que mais importa: 40 casos escritos **depois** de o sistema estar
congelado, pré-registrados, projetados para armadilhas que o piloto não cobria. A vantagem não
encolheu fora do piloto — que era o risco real de um estudo desenhado pelo próprio avaliador.

**Ressalva registrada em emenda ao pré-registro, antes de aparecer em qualquer resumo:** a
vantagem cresceu porque o comparador piorou, não porque o Jev melhorou. O Jev foi de 0,925 para
0,975 (dois casos); a regra caiu de 0,600 para 0,325, porque escrevi famílias inteiras contra
casamento de palavras-chave. A comparação honesta entre corpora é a do Jev consigo mesmo.

### 3.1.1 O mesmo resultado sob os três gabaritos

Existem três gabaritos para estes casos, e eles não dão o mesmo número. Apresentar um só, sem
dizer qual, foi o defeito que a décima segunda rodada de revisão encontrou no painel.

| Conjunto | Anotador independente | Meu gabarito | Adjudicado | Casos em disputa |
|---|---|---|---|---|
| E1 piloto (40 casos) | 0,875 | 0,925 | 0,925 | 4 |
| E7 confirmação (40 casos) | 0,9 | 0,975 | 1 | 5 |
| Os 80 juntos | 0,8875 | 0,95 | 0,9625 | 9 |

O gabarito do anotador independente é o mais severo dos três, e ele **não** é o menos defensável:
é o único que não passou pela minha mão. Ele erra de formas próprias — em 6 das 9 divergências
viu ação onde o enunciado pedia informação — mas citar só os outros dois seria escolher o
gabarito depois de ver o resultado. O painel exibe a faixa completa em cada cartão.

### 3.2 Ressalvas e exceções (E4)

Oito consultas, cinco candidatos cada, com ressalvas críticas plantadas. Perder uma ressalva no
topo significa que a exceção não chega a quem decide.

| Ordenação | Ressalvas no topo-3 | nDCG@5 |
|---|---|---|
| **Jev** | **8/8** | **0,9958** |
| BM25 | 5/8 | 0,9205 |
| Ordem de chegada | 4/8 | 0,7359 |

O corpus foi embaralhado com semente fixa antes da execução, porque na primeira versão ele
estava em ordem decrescente de relevância e a "ordem de chegada" ganhava de graça.

### 3.3 Formato, lote e posição (E2, E2b)

Desenho fatorial 2×2×2 (lote × ordem das opções × distração), 8 condições sobre os mesmos 40
casos, ordem de execução embaralhada. Acurácia entre 0,925 e 0,950; **McNemar p = 1,000 em
todos os contrastes** — nenhuma condição se separa das outras. O lote de 8 reduz o custo por
decisão em 32% a 43%.

O E2 sugeriu que as posições 4 e 8 do lote eram piores. O E2b desconfundiu: com a ordem dos
casos fixa, posição e caso eram a mesma variável. Embaralhando em 5 permutações (200
observações), o efeito de posição desaparece: **permutação p = 0,403**. O que sobra é outro
achado, que virou o E6.

### 3.4 Estabilidade (E2b, E6)

- **No lote:** 3 casos em 40 mudam de resposta conforme os vizinhos do lote.
- **Isolado:** com uma pergunta por chamada, repetida 5 vezes, **1 caso em 40** ainda muda de
  resposta entre repetições idênticas — e é um dos três.

Conclusão: parte da instabilidade é do próprio modelo, não do agrupamento. Voto majoritário de
cinco chamadas leva a acurácia de 0,925 a 0,950: **um caso a mais, a cinco vezes o custo.**

### 3.5 Transporte (E5)

OpenRouter contra o endpoint TypeSafe direto, mesmos 40 casos, chamadas intercaladas para que
uma deriva do serviço não caísse sobre um só braço.

| | Concordância | Acurácia | Latência p50 | Custo por decisão |
|---|---|---|---|---|
| OpenRouter | \- | 0,925 | 396 ms | 22,167 nusd |
| TypeSafe direto | **40/40 (100%)** | 0,925 | 755 ms | 24,804 nusd |

Decisão idêntica em todos os casos. O direto é ~2× mais lento e ~12% mais caro, porque cobra
tokens de saída que o OpenRouter não cobra. **Não há motivo técnico para trocar de transporte.**

### 3.6 Qualidade do gabarito (E8)

A limitação mais séria de todo o estudo era ter um anotador só. Um anotador independente e cego
(`qwen2.5-7b` local, custo zero, outro fornecedor e outra arquitetura) classificou os 80 casos
vendo apenas as instruções e os critérios — sem o gabarito e sem a resposta do Jev.

- **Kappa de Cohen: 0,859.** Concordância bruta 88,8%, 9 divergências em 80.
- Dos **4 erros do Jev** sob o meu gabarito, o anotador independente **confirma o meu gabarito
  em 2** (`tri-f06-02`, `tri-f09-04` — erros claros do modelo) e **fica do lado do Jev em 2**
  (`tri-f02-04`, `cnf-g05-02`). Nas outras 7 divergências foi o anotador que caiu na armadilha,
  com o Jev do lado do gabarito.
- **Sob o gabarito do outro anotador, o Jev faz 0,8875, não 0,95.** A acurácia depende de qual
  gabarito se adota, e é exatamente essa fragilidade que o experimento veio expor.

**Um dado lateral que vale registrar:** o anotador independente tinha a opção de marcar um caso
como ambíguo, e marcou 6. Apenas 2 desses 6 estavam de fato entre os 9 em que ele divergiu de
mim. A autopercepção de ambiguidade praticamente não previu a divergência real — o que é mais um
motivo para não usar "o modelo disse que estava em dúvida" como filtro de qualidade.

### 3.6.1 Adjudicação cega dos 9 casos em disputa

A sétima rodada de revisão apontou, com razão, que sem adjudicação o E8 não fechava nada: dois
anotadores que discordam não produzem verdade, produzem uma disputa. Os 9 casos foram então
submetidos a um **terceiro juiz** (`gpt-5.6-sol-high`, outro fornecedor ainda), que recebeu só a
mensagem e as duas leituras **em ordem sorteada**, sem saber qual veio de quem.

| | Resultado |
|---|---|
| Casos em que o terceiro juiz confirma o gabarito do autor | **8 de 9** |
| Casos em que confirma o anotador local | 1 de 9 (`cnf-g05-02`) |
| Casos em que propôs uma terceira leitura | 0 |

**Este resultado corrige a leitura anterior deste relatório, e corrige-a contra o modelo.** Eu
havia registrado que em 2 dos 4 erros "o suspeito é o meu gabarito". A adjudicação diz outra
coisa: em `tri-f02-04` o terceiro juiz ficou comigo, e o Jev errou mesmo. Só `cnf-g05-02` — o
caso que eu já havia declarado contestável antes de ver qualquer um destes resultados — mudou de
lado, e mudou contra mim.

**Sob o gabarito adjudicado, o Jev faz 0,9625 (77/80)**, com três
erros: `tri-f02-04`, `tri-f06-02` e `tri-f09-04` — **todos do corpus piloto**. No conjunto de confirmação, que é a
partição de teste, o gabarito adjudicado deixa o modelo **sem erro nenhum**, porque o único erro
que havia lá (`cnf-g05-02`) foi justamente o caso que mudou de lado. Isso não deve ser lido como
"40/40 no teste": é um resultado de 40 casos em que o único erro virou disputa e a disputa foi
decidida por um terceiro modelo. O número que eu levaria a uma reunião é o de 80 casos, 0,9625.

A faixa honesta de acurácia nestes 80 casos é **0,8875 a 0,9625**: 0,8875 sob o gabarito do
anotador independente, 0,9500 sob o meu, 0,9625 sob o adjudicado.

**O limite desta adjudicação, dito antes que alguém o use contra o resultado:** o terceiro juiz
é um modelo de linguagem grande, como o Jev. Modelos grandes treinados em dados parecidos tendem
a compartilhar a mesma convenção sobre o que é "a ação pedida" — a concordância de 8 em 9 pode
estar medindo essa convenção compartilhada, e não a verdade do domínio. O desenho controla o que
dá para controlar (ordem sorteada, juiz cego à autoria, nenhum acesso ao repositório), mas não
controla isso. Uma adjudicação com três pessoas do atendimento real poderia chegar a outro lugar,
e continua sendo o item 2 da seção 10.

**Ressalva que não pode ser omitida:** um modelo de 7B não é anotador humano, e o E8 **não é a
adjudicação de gabarito** que o estudo precisa. Ele recebeu a minha rubrica e reproduziu a minha
rubrica; kappa alto aqui mede reprodutibilidade, não validade do constructo. O padrão das
divergências mostra viés claro — em 6 das 9 ele viu ação onde eu li pedido de informação, que é
precisamente a armadilha que as instruções mandam evitar. E os 71 casos de "consenso" são os
casos em que os dois concordam, ou seja, os fáceis: a acurácia de 0,9718 ali **não é uma medida
melhor, é uma medida sobre um subconjunto mais fácil**, e não corrige nada. Os 9 casos em disputa **foram adjudicados** (seção 3.6.1), mas por um terceiro
modelo, não por uma pessoa. **O anotador humano continua pendente**, e o que a adjudicação
mostra é que a rubrica é reproduzível entre juízes independentes — não que ela seja a definição
certa do problema.

---

### 3.7 Erro grave: `cancelar` indevido

O pré-registro do E1 define, desde 18 de setembro, que **erro grave é confundir `cancelar` com
qualquer outra classe, porque cancelar dispara ação irreversível no atendimento**, e manda
reportá-lo *separadamente da acurácia média*. Até a décima terceira rodada de revisão ele nunca
foi reportado. A cobrança procede e é séria: acurácia média trata todos os erros como iguais, e
a métrica que o próprio protocolo classificou como irreversível ficou fora do relatório inteiro.

| Conjunto | Gabarito | Indevido | Perdido | Teto por família | Regra congelada |
|---|---|---|---|---|---|
| piloto (E1) | anotador local | **0** | 2 | 25,9% | 3 |
| piloto (E1) | autor | **0** | 1 | 25,9% | 4 |
| piloto (E1) | oficial | **0** | 1 | 25,9% | 4 |
| confirmação (E7) | anotador local | **0** | 1 | 25,9% | 5 |
| confirmação (E7) | autor | **0** | 0 | 25,9% | 6 |
| confirmação (E7) | oficial | **0** | 0 | 25,9% | 6 |
| desempate (E11) | anotador local | **0** | 5 | 13,9% | 20 |
| desempate (E11) | autor e oficial | **0** | 0 | 13,9% | 20 |
| replicação (E12) | anotador local | **0** | 3 | 9,5% | 30 |
| replicação (E12) | autor e oficial | **0** | 0 | 9,5% | 30 |

**O Jev não cometeu nenhum erro grave nos 230 casos classificados do estudo, sob nenhum dos três
gabaritos.** A regra congelada comete 10 nos 80 casos em que existe comparação com ela. Este é o
resultado mais favorável ao modelo em todo o estudo, e é exatamente por isso que o teto vai na
mesma tabela: zero erro observado só permite afirmar que a taxa por família está **abaixo de
25,9% com 95% de confiança** nos conjuntos de 10 famílias, e abaixo de 9,5% no corpus de 30
famílias do E12 — que é o mais apertado que este estudo conseguiu, e ainda assim é um em cada
dez.

Os quatro comparadores econômicos do E12, no mesmo corpus e no gabarito oficial, cometem erro
grave: llama-3.1-8b, 2 falsos `cancelar` e 2 perdidos; gemma-3-12b, 2 e 1; gpt-oss-20b, 1 e 2. O
mistral-nemo, como o Jev, não comete nenhum — e custa um quarto do preço dele.

*(Correção registrada: até a décima sexta rodada de revisão este parágrafo dizia que o
gpt-oss-20b perdia 5 `cancelar`. Eram 5 antes de eu corrigir o defeito que apagava nove
respostas já pagas daquele braço, descrito em 9.1, e o número ficou no texto depois de o dado
mudar. É o mesmo erro que este relatório persegue desde a nona rodada: número velho numa caixa
nova — desta vez cometido por mim, no parágrafo em que eu comparava erro grave entre modelos.)* Zero observado não é zero verdadeiro, e um teto de um quarto por família não é uma
garantia operacional. O que este número autoriza dizer é que o erro irreversível não apareceu
onde a regra congelada o comete dez vezes; o que ele não autoriza é prometer que não aparecerá.

O sentido oposto — `cancelar` que o modelo deixa passar — aparece em 1 a 5 casos conforme o
gabarito e o corpus; no E12, sob o gabarito do anotador independente, o próprio Jev perde 3. Custa atraso, não destruição, e por isso está na tabela mas fora da definição de erro
grave.

---

### 3.8 O braço do LLM econômico (E10)

O estudo comparou o Jev contra uma regra congelada em todos os experimentos anteriores, e a
regra perde feio em toda parte: 60,0% no piloto, 32,5% na confirmação, 10 erros graves contra
zero. Nada disso responde à pergunta que o plano fez primeiro: *vale um LLM especializado aqui,
ou qualquer classificador de linguagem resolve?*

`meta-llama/llama-3.1-8b-instruct` recebeu **exatamente as mesmas instruções e os mesmos
critérios congelados do E1** — sem exemplos, sem ajuste de prompt, sem nenhuma iteração contra
estes casos — nos 40 casos da partição de confirmação, com `temperature` 0 e `max_tokens` 64.
Custo total: US$ 0,000358.

| | Autor | Oficial | Anotador independente | Erro grave |
|---|---|---|---|---|
| Jev 1,13 | 0,9750 | 1,0000 | 0,9000 | 0 |
| llama-3.1-8b | 0,9000 | 0,9250 | 0,8500 | 0 |
| Regra congelada | 0,3250 | — | — | 6 |

Diferença pareada **7,5%**, IC95
**[0,0%; 15,0%]** sobre 10 famílias. O intervalo
toca zero no limite inferior. Discordâncias: 3 casos, todos a favor
do Jev — `cnf-g03-01`, `cnf-g05-04`, `cnf-g07-01` —, o que dá McNemar exato bilateral **p = 0,25**.

Três detalhes de método que impedem este resultado de ser lido como favorável a quem eu quisesse:

1. **O Jev não foi reexecutado.** As respostas dele vêm do E7, dos mesmos 40 casos. Reexecutar
   daria ao Jev uma segunda amostragem que o comparador não teve — e, como o E6 mostrou, este
   modelo não é determinístico.
2. **Resposta fora do contrato contaria como erro**, nunca seria reexecutada nem descartada.
   Isso estava no pré-registro justamente porque descartar resposta malformada do comparador e
   não do Jev é uma das formas mais comuns de fraudar este tipo de comparação. Não foi preciso:
   as 40 respostas vieram em JSON válido, com classe dentro das cinco.
3. **O comparador não é o anotador do E8.** Usar o `qwen2.5:7b` aqui faria do anotador juiz de
   si mesmo. Ainda assim, sob o gabarito daquele anotador — o mais severo dos três — o
   comparador faz 0.8500 e o Jev 0.9000.

**O que isto não diz:** que nenhum LLM econômico resolve a tarefa (testou-se um), que os dois
são equivalentes (o poder é baixo), ou que o Jev é dispensável em produção (o corpus continua
sendo escrito por mim). O que diz é uma coisa só, e basta para mudar a recomendação: **este
estudo não mostrou que o Jev é necessário.**

---

### 3.9 O mesmo comparador no piloto (E10b), e o que ele fez com a conclusão

O intervalo do E10 encostou em zero no limite inferior. Com 10 famílias, é o caso em que mais
poder muda a leitura — e havia 10 famílias disponíveis, a US$ 0,0004. Rodei, sob a Emenda 1 do
pré-registro, escrita antes da execução.

| Conjunto (famílias) | Jev | llama-3.1-8b | Diferença | IC95 |
|---|---|---|---|---|
| Confirmação, teste (10) | 0,9750 | 0,9000 | 7,5% | [0,0%; 15,0%] — não separa |
| Piloto (10) | 0,9250 | 0,7250 | 20,0% | [10,0%; 30,0%] — separa |
| Os 80, 20 famílias | 0,9500 | 0,8125 | 13,8% | [7,5%; 20,0%] — separa |

A assimetria é grande e merece ser dita: o comparador cai de 90,0% na confirmação para
72.5% no piloto, enquanto o Jev cai de 97,5% para
92.5%. O corpus piloto é mais duro **para o comparador**, não para
os dois igualmente.

**A premissa da minha própria emenda não sobreviveu à conferência.** A emenda dizia que o piloto
havia guiado o desenho do prompt do Jev e que por isso o resultado ali deveria ser lido como
secundário. Fui ao histórico: as instruções e os critérios entraram uma única vez, no commit
`9f6d13b` de 18/09, junto com o corpus piloto, e nunca foram alterados; o corpus piloto também
não mudou depois de rodar. Não houve iteração de prompt contra resultados. Registrei isso como
nota de verificação no próprio pré-registro, em vez de reescrever a emenda.

O que continua valendo contra a leitura ampliada é outra coisa, e é suficiente: **eu escolhi
rodar o piloto depois de ver o resultado primário.** Uma análise decidida depois de ver o
resultado que ela vai corrigir não pode ser apresentada como se tivesse sido planejada antes —
ainda que a conta esteja certa, e ela está.

Por isso o relatório não elege nenhum dos dois lados. A partição que existe para decidir não
separa; a leitura com o dobro das famílias separa; e a segunda foi escolhida depois da primeira.
Esta era a conclusão antes da adjudicação dos 10 desacordos. A seção 3.11 conta o que aconteceu
com ela.

---

### 3.10 O desempate (E11): o que ele mediu, e o que quase me fez concluir errado

O E10 não separou de zero na partição de teste; o E10b, decidido depois, separou no piloto. Os
dois defeitos eram claros: poder baixo e uma análise escolhida depois de ver a outra. O E11
existe para resolver os dois — e resolveu, só que a resposta não foi a que a pergunta esperava.

**O que foi congelado antes de qualquer dado existir:** as 20 famílias de fenômeno linguístico,
listadas nominalmente no pré-registro; a métrica primária; o bootstrap por família; e as três
leituras possíveis do intervalo, com o que cada uma obrigaria a escrever aqui. Só então os 60
casos foram escritos, três por família, com o gabarito fixado junto com o caso.

**Duas correções antes da primeira chamada,** pela mesma disciplina do E7: `dsp-d12-02` tinha
gabarito `trocar` num pedido condicional, e a rubrica que os dois modelos recebem diz que ação
condicional não é ação pedida — o caso mediria a contradição, não o modelo; `dsp-d09-02` ficava
entre `rastrear` e `informacao`, e um caso que dois gabaritos defendem não mede nada.

**Um incidente, declarado:** a primeira execução completou as 120 chamadas, liquidou
US$ 0,001923295 e então a análise quebrou com `KeyError: 'kind'` — um campo que só existe nos
corpora antigos. **Os dados se perderam inteiros**, porque nada era gravado em disco: o
`request_path` que o executor registra no livro-caixa é só um rótulo. O custo permanece no
livro-caixa, como tem de permanecer, e o experimento passou a gravar cada resposta assim que ela
chega. Entre as duas execuções não mudou corpus, gabarito nem prompt — só o código de
persistência.

**O resultado, nos dois gabaritos:**

| Gabarito | Jev | llama-3.1-8b | Diferença | IC95 |
|---|---|---|---|---|
| Meu | 1,0000 | 0,8667 | 13,3% | [5,0%; 21,7%] |
| Anotador independente | 0,8333 | 0,8667 | −3,3% | [−10,0%; 3,3%] |

Sob o meu gabarito, só o Jev acerta em 8 casos e só o comparador em nenhum (McNemar exato
p = 0,0078). Sob o do anotador independente, 2 contra 4 (p = 0,6875).

Erro grave (`cancelar` indevido), recontado sob os três gabaritos porque a décima quinta rodada
de revisão mostrou que a afirmação anterior era falsa:

| Gabarito | Jev | llama-3.1-8b |
|---|---|---|
| Meu e adjudicado | 0 | 1 (`dsp-d03-01`) |
| Anotador independente | 0 | **0** |

Até esta rodada, esta seção dizia que o erro grave era *"a única métrica do E11 em que a
diferença não depende do gabarito"*. **Não é.** O único falso-`cancelar` do comparador é
justamente `dsp-d03-01`, que está entre os 10 casos em disputa: o anotador independente leu
`cancelar` ali, e sob o gabarito dele o comparador acerta e o erro grave some. A frase antiga
usava como âncora um caso que o próprio parágrafo seguinte declara contestado. O que se sustenta
é mais modesto e continua valendo: **o Jev não cometeu erro grave sob nenhum dos três
gabaritos**, e o comparador cometeu sob dois deles.

Uma ressalva de contabilidade, da mesma rodada: o campo `erros_graves_cancelar` gravado nos
relatórios soma `cancelar` indevido **e** `cancelar` perdido, e por isso marca 2 para o
comparador onde a prosa diz 1. Os dois números estão certos em definições diferentes, e a
definição que o pré-registro do E1 chamou de irreversível é só a primeira. O bloco
`erro_grave` do relatório traz as duas listas separadas, nominalmente.

**Os 10 casos em que o anotador independente discorda de mim:**
`dsp-d01-02`, `dsp-d03-01`, `dsp-d06-03`, `dsp-d09-01`, `dsp-d10-03`,
`dsp-d11-01`, `dsp-d12-01`, `dsp-d16-01`, `dsp-d16-02` e `dsp-d18-01`.
Em **todos** eles o Jev responde o que eu responderia. Há duas leituras
para isso, e eu não tenho como escolher entre elas com o que este estudo mediu:

1. O Jev segue a rubrica escrita melhor do que um modelo de 7B segue, e o anotador é que erra —
   o padrão das discordâncias dele é o mesmo dos corpora anteriores, puxar para ação onde o
   enunciado pede informação.
2. Eu escrevi 60 casos que casam com a leitura do Jev, sem perceber, porque conheço as respostas
   dele desde o E1.

A segunda não é paranoia: é exatamente o que um corpus escrito pelo avaliador permite, e foi ela
que sustentou a quarta recomendação deste relatório. **A seção 3.11 mostra por que ela não
sobreviveu**: os 10 casos foram a um terceiro juiz cego, que confirmou meu gabarito em todos.

---

### 3.11 Os 10 desacordos do desempate foram a um terceiro juiz, e ele não hesitou

A primeira leitura deste experimento dizia que a vantagem do Jev "dependia de quem escreveu o
gabarito", porque sob o gabarito do anotador independente o sinal invertia. A décima quarta
rodada de revisão mostrou o defeito dessa leitura: o anotador independente é um modelo de 7B, e
as 10 discordâncias dele seguem **um padrão só** — ele lê o vocabulário
presente na mensagem, não o ato de fala pedido. Em `dsp-d01-02` ("Será que eu deveria cancelar?
Antes de decidir, me explica como funciona a multa") ele marcou `cancelar`; em `dsp-d18-01`
("Por enquanto não cancela nada, só me manda o valor da multa") marcou `cobranca`. É o mesmo
modo de falhar da regra congelada que o Jev supera desde o E1.

Sob a Emenda 2 do pré-registro, escrita antes da execução e com a regra de leitura declarada, os
10 casos foram ao mesmo procedimento do E8b: terceiro juiz de outro fornecedor
(`gpt-5.6-sol-high`), cego a quem escreveu cada leitura, com as duas em ordem sorteada por
semente fixa, e sem ver resposta de modelo nenhum.

| Decisão do terceiro juiz | Casos |
|---|---|
| Confirmam o meu gabarito | **10 de 10** |
| Confirmam o anotador independente | 0 |
| Propuseram terceira leitura | 0 |
| Declararam ambiguidade | 0 |

Dez de dez, sem nenhuma ambiguidade declarada. A inversão de sinal era o anotador, não o
gabarito — e a emenda dizia, antes de eu saber disso, que nesse caso a leitura primária
pré-registrada voltaria a valer. Voltou.

**Uma ressalva sobre o McNemar,** apontada na mesma revisão e procedente: ele trata os 60 casos
como independentes, e eles não são — são 3 por família. O p = 0,0078 é **secundário** e está
otimista. A métrica primária, que é o bootstrap por família, respeita o agrupamento, e é ela que
sustenta a conclusão.

**E uma que não procede:** a revisão questionou `dsp-d16-03` ("Meu cancelamento já foi
processado? Se ainda não, processa agora"), com gabarito `cancelar`, numa família chamada
"pedido de confirmação, não pedido de ação". Não é contradição, é o controle da família: dois
casos dela são `informacao` e o terceiro tem pedido explícito de execução. Famílias com caso de
contraste são o desenho de todos os corpora deste estudo, e sem elas a família mediria só a
classe, não o fenômeno.

---

### 3.12 A replicação (E12): mais famílias, mais comparadores, mesma divergência

O item 1 do próximo movimento deste relatório pedia repetir o E10 *"em amostra maior, com pelo
menos 30 famílias, e com dois ou três LLMs econômicos em vez de um"*. Foi feito, e é o
experimento mais caro em chamadas de todo o estudo: 90 casos novos em 30 famílias declaradas
antes de o primeiro caso existir, cinco braços na mesma lista e na mesma ordem, 529 tentativas
registradas no livro-caixa.

**O que este experimento tinha de diferente.** O E11 comparou o Jev contra **um** modelo de 8B
de **um** fornecedor. Vencer um modelo não é vencer a classe "LLM genérico e barato": os quatro
comparadores do E12 são de quatro fornecedores (Meta, Mistral, Google e OpenAI de pesos
abertos), e a regra de leitura exige que o intervalo separe de zero contra **todos** para que
haja vantagem. É um teste de interseção-união, conservador por construção, e ele foi escrito
assim de propósito — basta um comparador barato empatar para que a conclusão não seja favorável
ao sistema avaliado.

**O resultado, no gabarito oficial:** o Jev acerta 0,9889 e supera os quatro, de +7,8% a +14,4%,
com todos os IC95 acima de zero e McNemar exato entre p = 0,0156 e p = 0,0002. Os 10 casos em
que eu e o anotador independente discordamos foram a um terceiro juiz cego, de outro fornecedor,
com as leituras em ordem sorteada — e ele confirmou meu gabarito em 10 de 10, sem declarar
ambiguidade em nenhum.

**O resultado sob o gabarito do anotador independente:** contra o llama-3.1-8b a diferença é
**0,0000**, IC95 [−6,7%; 6,7%], McNemar p = 1,0000. Contra o mistral-nemo e o gemma o intervalo
encosta em zero pelo lado de baixo. Só contra o gpt-oss-20b a vantagem sobrevive.

**Por que isso importa mais do que o número favorável.** O E11 já tinha encontrado essa
divergência, e a explicação natural era falta de poder: 20 famílias, um comparador, intervalos
largos. O E12 triplicou as famílias e quadruplicou os comparadores. Se a divergência fosse ruído
amostral, ela teria encolhido. Ela não encolheu — ficou no mesmo lugar. **A conclusão deste
estudo sobre o Jev depende de quem escreveu o gabarito, e mais medição não resolve isso.**

**Custo por mil classificações, do livro-caixa e não de estimativa:** mistral-nemo US$ 0,005638;
llama-3.1-8b US$ 0,007520; gemma-3-12b US$ 0,014744; Jev US$ 0,022524; gpt-oss-20b US$ 0,092679.
O Jev é o quarto mais caro dos cinco. Se a pergunta operacional for *"qual o classificador mais
barato que passa no critério de erro grave"*, o mistral-nemo custa um quarto do Jev, não comete
nenhum `cancelar` indevido nos 90 casos e, sob o gabarito independente, não é distinguível dele.

**Erro grave, no gabarito oficial:** o Jev não comete nenhum `falso-cancelar` nem perde nenhum
`cancelar`. O mistral-nemo também não. O llama-3.1-8b comete 2 e perde 2; o gemma comete 2 e
perde 1; o gpt-oss-20b comete 1 e perde 5. Zero observado não é zero verdadeiro: com 30
famílias, o limite superior de 95% do Jev ainda é 4,4%.

**Três emendas, todas escritas durante a execução e antes de olhar qualquer acurácia:**

1. **Falha de transporte não é resposta errada.** O provedor devolveu HTTP 429 em 46 chamadas do
   gemma. Contá-las como erro de classificação atribuiria ao comparador uma falha que é da fila
   do provedor. Elas foram repetidas em até três tentativas; 8 seguiram sem resposta e contam
   como erro dele, com o número publicado.
2. **Cobertura mínima de um braço.** Um braço com menos de 90% de respostas válidas é reportado
   como incompleto e sai da leitura primária. O critério foi escrito antes de calcular a
   acurácia do braço que motivou a dúvida, justamente para que manter ou tirar não fosse escolha
   pós-hoc. Ao fim, gemma ficou em 91,1% e gpt-oss em 90,0%: nenhum saiu.
3. **Teto de saída é parâmetro de transporte.** Com os 64 tokens de saída herdados do E10, o
   gpt-oss-20b devolvia conteúdo vazio — ele gasta saída com raciocínio antes de responder. O
   teto subiu para 256, o braço foi reexecutado desde o primeiro caso, e as 9 chamadas feitas sob
   o teto insuficiente foram anuladas **da análise, não do livro-caixa**, onde seguem pagas e
   registradas.

A terceira emenda corrigia um erro que favorecia o sistema avaliado, e é por isso que ela foi
escrita antes: sem ela, o gpt-oss apareceria com acurácia perto de zero e a "vantagem do Jev"
sobre ele seria um artefato da minha configuração.

**Como auditar essa cronologia sem acreditar em mim.** As três emendas foram commitadas com a
execução em curso, ou seja, quando já existiam respostas parciais no disco — o Git prova a
ordem dos commits, não o que eu tinha visto. O que torna a afirmação verificável é o bruto:
`runs/e12-replicacao/respostas.jsonl` é gravado caso a caso, na ordem, e vai versionado desde a
décima sexta rodada de revisão, que cobrou justamente isso. Cruzando o horário de cada linha do
bruto com o horário de cada commit de emenda, qualquer pessoa recalcula exatamente qual era o
estado dos dados quando cada regra foi escrita — inclusive para me contradizer.

---

## 4. Mecanismo: por que funciona

A vantagem sobre as regras não vem de vocabulário maior. Vem de resolver três coisas que o
casamento de palavras não resolve, e que as famílias do corpus isolam uma a uma:

1. **Quem realiza a ação.** "Minha esposa cancelou o pedido dela; o meu não chegou" contém
   "cancelou" e não é um pedido de cancelamento.
2. **O estatuto da ação.** Ação negada ("não quero cancelar nada"), condicional ("se não chegar
   até sexta, vou querer cancelar") ou já concluída ("já cancelei pelo site") não é a ação pedida.
3. **A palavra contra o pedido.** "Solicito o estorno do aparelho com defeito: mandem um novo"
   usa o léxico financeiro para pedir uma troca.

A regra congelada acerta a família 1 do piloto quase inteira e desaba nas famílias G06 e G07 do
conjunto de confirmação. É essa diferença que o número +0,650 do E7 está medindo.

---

## 5. Contra-hipóteses testadas

### Contra-hipótese 1: o corpus foi desenhado para o sistema ganhar
**Argumento:** escrevi os casos conhecendo o Jev e a regra. Um corpus assim mede o autor.
**Teste executado:** E7, com 40 casos novos, pré-registrados, com o sistema já congelado.
**Resultado:** a vantagem não encolheu. Mas registrei que ela cresceu por piora do comparador,
não por melhora do Jev. **Parcialmente refutada, com ressalva permanente.**

### Contra-hipótese 2: o gabarito está errado onde o Jev "erra"
**Argumento:** um anotador só define a verdade que ele mesmo vai avaliar.
**Teste executado:** E8, anotador independente e cego.
**Teste executado:** E8 mais a adjudicação cega dos 9 casos em disputa por um terceiro juiz.
**Resultado: refutada, e refutada contra o modelo.** O terceiro juiz confirmou o meu gabarito em
8 dos 9 casos. Sob o gabarito adjudicado o Jev faz 0,9625, com três erros reais — não dois. A
hipótese de que "o gabarito é que está errado onde o modelo erra" só se sustentou em um caso, o
mesmo que eu já havia declarado contestável antes de ter qualquer resultado.

### Contra-hipótese 3: o ganho é do formato, não do modelo
**Argumento:** talvez lote, ordem das opções ou distração expliquem os resultados.
**Teste executado:** E2 fatorial completo, mais E2b para desconfundir posição.
**Resultado:** nenhuma condição se separa (McNemar p = 1,000). **Refutada.**

### Contra-hipótese 4: o resultado depende do provedor
**Teste executado:** E5, dois transportes intercalados.
**Resultado:** 40/40 de concordância. **Refutada.**

### Contra-hipótese 5: a acurácia cai numa distribuição de classes realista
**Argumento:** os corpora são quase balanceados; um canal real não é.
**Teste executado:** E9, reponderação da matriz de confusão sob quatro distribuições, no
gabarito oficial.
**Resultado:** acurácia esperada entre 0,9502 e
0,9724 — varia pouco, porque nenhuma classe é fraca. **Refutada dentro da suposição de que a dificuldade dentro de cada classe é a mesma do
corpus**, que é uma suposição grande e não testada.

---

## 6. Calibração

Medida na partição de teste (conjunto de confirmação), que é a leitura honesta:

| Corte | Aceitos | Cobertura | Erros observados | Limite superior de erro (por família) |
|---|---|---|---|---|
| **0,90** | **35/40** | **87,5%** | **0** | **25,9%** |
| 0,95 | 34/40 | 85,0% | 0 | 25,9% |
| 0,99 | 28/40 | 70,0% | 0 | 25,9% |

O limite do corte 0,90 — **o que a seção 1 recomenda** — não estava calculado até a décima
segunda rodada de revisão apontar a lacuna: o painel vendia um corte cujo número desconfortável
ninguém tinha computado. Ele é **25,9% por família** e 8,2% por caso, sobre 10 famílias e 35
casos aceitos.

**Zero erro observado não é taxa de erro zero.** Os aceitos vêm de um número pequeno de
famílias, e famílias são a unidade de dependência. O limite por caso (Clopper-Pearson, 35 ensaios no corte 0,90) daria um número bem menor, e seria enganoso: trataria casos da mesma família como
observações independentes, o que eles não são.

### 6.1 A calibração não se transportou para o corpus novo

O corte de 0,90 foi calibrado no piloto e na confirmação, e nos dois **todos** os erros ficaram
abaixo dele. O E12 trouxe 90 casos novos, e ali isso deixou de valer:

| Corte | Aceitos (E12) | Cobertura | Erros entre os aceitos | Limite superior por família |
|---|---|---|---|---|
| 0,90 | 86/90 | 95,6% | **1** | 14,9% |
| 0,95 | 81/90 | 90,0% | **1** | 14,9% |
| **0,99** | **74/90** | **82,2%** | **0** | **9,8%** |

O erro é `rep-p30-03`: *"Posso pedir a segunda via por aqui? Antes de pedir, me confirma se ela
vem com o mesmo vencimento da original."* O gabarito é `informacao` — o remetente adia
explicitamente o pedido — e o modelo respondeu `cobranca` **com confiança 0,98**. O anotador
independente leu como `cobranca` também, e o terceiro juiz cego confirmou o gabarito; ou seja, é
um caso difícil, não um caso mal escrito.

**Consequência para a recomendação, e ela é desfavorável ao que este relatório vinha dizendo:**
a afirmação "todos os erros ficam abaixo de 0,90" era verdadeira nos dois primeiros corpora e é
falsa no terceiro. Um corte calibrado num conjunto **não se transporta** para outro. A
recomendação operacional passa a ser o corte de 0,99, que é o único que zera o erro nos três
corpora, e mesmo ele exige recalibração no material real de quem for aplicar — com revisão
humana obrigatória da classe `cancelar` em qualquer corte.

A seção 1.1 e o achado principal (seção 2) devem ser lidos com esta ressalva: a confiança
reportada é informativa, e continua sendo o recurso mais útil do modelo, mas ela não é uma
garantia.

---

## 7. Custo e operação

**Medido:** 1.474 chamadas, US$ 0,035707114 no total, contra um extrato de provedor de
US$ 0,034640289 — a diferença é o arredondamento para cima que o executor aplica em toda
conversão. Custo por decisão individual ~US$ 0,000024. Latência mediana 396 ms no OpenRouter.

O E12 sozinho responde por 529 dessas chamadas e US$ 0,013088340, e foi ele que expôs o defeito
descrito na seção 9: liquidar uma requisição recusada por limite de taxa pelo pior caso fazia o
livro-caixa declarar US$ 0,499 de gasto que o provedor nunca cobrou.

**Declarado, não medido:** 2 minutos por revisão humana, US$ 12,00 por hora. Nenhum cronômetro
foi usado; trocar esses parâmetros muda toda a tabela abaixo.

A tabela abaixo usa a **união dos 80 casos**, que é a leitura conservadora: a partição de
confirmação sozinha dá cobertura maior no mesmo corte (87,5% contra 80,0%) e, por isso mesmo,
custo menor (US$ 0.050 contra
US$ 0.080). **Cobertura e custo têm de ser lidos sempre na
mesma partição** — foi essa mistura que a décima rodada de revisão encontrou no painel.

| Política | Cobertura automática | Erros entre aceitos | Custo por decisão | Economia |
|---|---|---|---|---|
| Revisar tudo | 0% | — | US$ 0,400 | — |
| Corte 0,99 | 66,25% | 0 | US$ 0,135 | 66,2% |
| Corte 0,95 | 77,5% | 0 | US$ 0,090 | 77,5% |
| **Corte 0,90** | **80,0%** | **0** | **US$ 0,080** | **80,0%** |
| Aceitar tudo | 100% | 3 | US$ 0,000022 | 100% |

A linha "aceitar tudo" é o que a automação total custaria e o que ela erraria. A diferença entre
ela e o corte 0,90 é o preço de não errar: **US$ 0,08 por decisão nesta tabela, que é a união**.
Na partição de confirmação, que é a leitura da seção 1, esse preço é US$ 0,05. Os dois números
são da mesma política em bases diferentes, e nenhum dos dois deve ser citado sozinho.

---

## 8. Limites — o que este estudo não autoriza afirmar

1. **Não é um teste em dados reais.** Os 80 casos de triagem e os 24 de evidência foram
   construídos por mim. Nenhum veio de um canal de atendimento em produção.
2. **Nenhum anotador humano além de mim.** O E8 mitigou com um anotador independente e o E8b
   com um terceiro juiz, mas os três são modelos de linguagem. O kappa de 0,8420 sobre os 230 casos anotados mede que a
   rubrica é **reprodutível por um LLM**, não que ela seja válida. Os 3 erros que
   restam no gabarito adjudicado (tri-f02-04, tri-f06-02, tri-f09-04) passaram pela adjudicação cega, mas a
   adjudicação foi feita por máquina. A validade do constructo continua aberta, e é o item 2 da
   seção 10.

   *(Até a décima terceira rodada este item dizia "dois dos quatro erros do Jev podem ser erro
   meu" — número anterior à adjudicação, e afirmação que a seção 3.6.1 já havia substituído. Os
   dois textos conviveram por treze revisões, cada um dizendo uma coisa sobre o ponto que decide
   se o modelo erra ou se o rótulo erra.)*
3. **Amostra pequena.** 10 famílias por corpus. O bootstrap respeita o agrupamento, e por isso
   os intervalos são largos — o que é honesto, não um defeito.
4. **O modelo não é determinístico.** Confirmado com o caso isolado e repetido.
5. **Tempo humano não foi cronometrado.** A tabela da seção 7 é uma conta de sensibilidade, não
   uma medição de fluxo real. Isso era a pergunta P5 do plano e continua aberta.
6. **`confidence` não foi validado como probabilidade.** Foi validado como *ordenador*: separa
   bem o que está certo do que está errado nestes 80 casos. Não é a mesma coisa.
7. **Todos os anotadores deste estudo são modelos de linguagem, ou sou eu.** O gabarito do
   autor é meu; o anotador independente é `qwen2.5:7b`; os terceiros juízes são
   `gpt-5.6-sol-high`. A adjudicação cega resolve disputas *dentro* da rubrica, e resolveu:
   18 dos 19 casos em disputa no estudo inteiro foram para o meu gabarito. O que ela não pode
   resolver é se a rubrica corresponde ao que uma pessoa do atendimento faria. Esta é a
   limitação de que todas as outras derivam.
8. **Os dois braços não usam o mesmo protocolo.** O Jev responde pelo endpoint de decisões do
   provedor, com o campo `questions` nativo; o comparador responde por `chat/completions`, com
   JSON forçado, `max_tokens` 64 e `temperature` 0. O texto da rubrica é idêntico, a interface
   não é, e nenhuma ablação cruzada foi feita (o comparador no endpoint de decisões, ou o Jev
   pelo chat). Parte da diferença medida pode ser de formato, e este estudo não separa as duas
   coisas.
9. **A vantagem medida é sobre um corpus de armadilhas, não sobre uma amostra de trabalho.**
   As 20 famílias do E11 são a instrução congelada fatiada em fenômenos: ação de terceiro,
   negada, condicional, já concluída, irônica, truncada. Um canal real não chega com 20
   fenômenos linguísticos × 3 casos, balanceados e escritos para punir casamento lexical. Os
   13,3 pontos percentuais de diferença medem **densidade de armadilha**, e o 60/60 do Jev é teto
   de escala, não façanha. O mesmo vale, e a seção 3.1 já registra, para a folga contra as
   regras congeladas: famílias inteiras foram desenhadas contra elas.
10. **Um único LLM econômico foi testado como comparador.** O E10 usou
   `meta-llama/llama-3.1-8b-instruct`. Um empate com ele não é empate com a categoria, e uma
   vantagem sobre ele também não seria vantagem sobre a categoria. O que o E10 estabelece é que
   **um** modelo barato foi vencido neste corpus, e não que a categoria toda perca.
11. **Nenhuma conclusão sobre os outros 14 sistemas do plano.** A rodada simples offline dos 15
   sistemas mostrou 5 suítes passando, 7 falhando e 3 sem como rodar. Isso é estado de
   repositório, não evidência de comportamento.

---

## 9. Controle financeiro e integridade do processo

O controle de gastos foi tratado como código crítico e passou por **dezesseis rodadas de revisão
independente**, todas conduzidas por modelos de outros fornecedores (gpt-6-astra via Codex e
Grok 4.6 via Cursor); os defeitos abaixo vão até a décima terceira, e as rodadas seguintes não
encontraram defeito financeiro novo — a décima sexta apontou, com razão, o **limite da
evidência** da retificação do 429, que está declarado em 9.1. O décimo sexto e mais caro deles não veio de revisão
nenhuma: veio da execução do E12, e está descrito no fim desta seção. As quatro primeiras
encontraram
mais de 20 defeitos de prioridade 1, e — como o protocolo da casa prevê — as correções de cada
rodada criaram defeitos novos, apanhados na rodada seguinte. Os mais graves:

- O teto era aplicado por experimento, então abrir um experimento novo abria um teto novo.
- Divergência entre o extrato do provedor e o registro local não ocupava o teto.
- Reserva e liquidação podiam usar modelos diferentes, liberando saldo inexistente.
- Respostas ausentes sumiam das métricas e inflavam a acurácia.
- O critério de significância do pré-registro original era vacuoso (intervalo de Wilson sobre
  uma proporção nunca cruza zero); foi substituído por bootstrap de famílias, em emenda.
- `CREATE TABLE IF NOT EXISTS` não adiciona coluna a tabela existente: o banco de produção
  ficou sem as colunas de uma correção enquanto a suíte passava, porque a suíte usava bancos
  novos. Só uma verificação no estado real pegou isso.
- A migração apagava o ajuste de conciliação antes de ancorar o valor, o que devolveria ao
  teto dinheiro que o provedor já havia cobrado.

A sexta rodada, feita já sobre o painel pronto, encontrou o defeito mais instrutivo de todos:
**`authorize()` desfazia a pausa por estouro de teto.** Todo runner chama `authorize()` no
arranque e, como a função era um `INSERT OR REPLACE` com status fixo em `running`, bastava
relançar o script para apagar a única trava que impede gasto novo depois do teto — e apagar
junto as emendas registradas. A trava criada na quinta rodada não valia nada no caminho real;
valia só nos testes, que a exercitavam por outro caminho.

A mesma rodada apontou que o painel havia começado a contar meia verdade: o cartão do E8 citava
os dois casos em que o anotador independente apoia o Jev e omitia os dois em que ele confirma o
gabarito. Corrigido no código e na seção 3.6, e é a razão de a confiança da seção 1 ter caído de
0,75 para 0,60. O texto do veredito do painel passou a ser calculado a partir dos números, em
vez de prosa fixa: um texto com números escritos à mão continua afirmando o mesmo depois que os
dados mudam.

A sétima rodada revisou as correções da sexta e encontrou o que o protocolo desta casa sempre
encontra: um defeito novo, criado pela própria correção. O `authorize()` corrigido deixou de
apagar a pausa, mas continuava reescrevendo o teto do experimento — e como todo runner o chama
com US$ 5,00 no arranque, **uma emenda que baixasse o teto para US$ 1,00 seria desfeita pelo
próximo `python -m executor.run_e*`**, sem registro. Agora `authorize` só reduz; ampliar exige
`ampliar_teto_do_experimento(motivo, evidência)` e nunca passa do teto da carteira.

A mesma rodada cobrou a adjudicação dos 9 casos em disputa do E8, e a cobrança estava certa:
dois anotadores que discordam não produzem verdade. A adjudicação foi feita (seção 3.6.1) e
**mudou o resultado contra o modelo**, não a favor.

**Conciliação de encerramento contra o extrato do provedor:** o ledger registra
US$ 0,017182296 para o OpenRouter; o provedor cobrou US$ 0,017095092. O ledger está **acima** do
extrato em US$ 0,000087, e a diferença é explicada: são as chamadas que voltaram HTTP 400 na
fase de sondagem do contrato, provisionadas aqui e não cobradas lá. Nenhum excedente a absorver,
nenhum gasto sem identidade de provedor. Somando o TypeSafe direto (US$ 0,000992166), o total
comprometido era US$ 0,022618774 naquele momento; depois do E12 e da retificação descrita em
9.1, ele é US$ 0,035707114, contra um extrato de US$ 0,034640289.

A oitava rodada não encontrou defeito financeiro novo — o teto passou a ser, nas palavras do
revisor, "o pedaço mais honesto do repositório". Encontrou coisa pior no painel: depois de
adjudicar o gabarito, **o placar passou a se contradizer**. O veredito citava 87,5% em 40 casos
da confirmação e o cartão ao lado citava 80% em 80 casos da união; um cartão do E8 dizia 3 erros
e o outro dizia 4; e as pendências continuavam pedindo a adjudicação que o painel acabara de
anunciar. Três gabaritos circulavam ao mesmo tempo e cada parte usava o que tinha à mão.

A correção não foi cosmética: `executor/gabarito.py` passou a definir **um** gabarito oficial
(o do autor, com os casos em disputa substituídos pela adjudicação), o E9 passou a consumi-lo,
cada cartão declara qual gabarito está por trás do seu número, e `politica_de_referencia()`
devolve uma leitura só — sem cair silenciosamente na união quando a partição falta. O teste
`test_coerencia_placar.py` roda o painel contra os relatórios reais e falha se veredito e cartão
divergirem.

A nona rodada não achou defeito financeiro — e achou, de novo, o painel falando duas línguas.
O cartão do E7 estampava 97,5% (gabarito do autor) e narrava, na linha de baixo, que no gabarito
oficial não havia erro nenhum; a nota de confiança justificava o corte de 0,90 com 80 casos da
união enquanto o veredito, ao lado, falava de 40 casos da confirmação. A correção da oitava tinha
unificado o par que a revisão apontou com o dedo, e só ele.

Agora `executor/gabarito.py` recalcula cada conjunto **sob os dois gabaritos, na mesma conta**, e
o cartão mostra a **faixa** — 97,5% a 100,0% no E7 — em vez do melhor dos dois. Com um número só,
o olho pega o mais alto e a ressalva vira letra miúda. A nota de confiança passou a citar a mesma
base da política que recomenda, e o título do veredito usa a mesma função de política do resto do
painel.

A décima rodada não achou defeito financeiro e achou uma promessa impossível no painel: o
veredito oferecia a **cobertura da partição de confirmação (87,5%) com o custo da união
(US$ 0,080)**. Custo por decisão depende da fração que vai para revisão humana, que é justamente
o que a cobertura mede; as duas coisas têm de sair da mesma partição. Ou 87,5% a US$ 0,050, ou
80% a US$ 0,080. O meio-termo era o número preferido de cada coluna.

Corrigido: `politica_de_referencia()` passou a devolver também a política de revisar tudo da
mesma partição, o veredito usa as duas, e um teste quebra se o custo da união aparecer ao lado da
cobertura da confirmação. Na mesma rodada, o cartão do E8 deixou de estampar 96,2% — o mais alto
dos três gabaritos — e passou a mostrar a faixa 88,8% a 96,2%, como o E7 já fazia.

A décima primeira e a décima segunda rodadas não acharam defeito financeiro; acharam o painel
mostrando **dois gabaritos onde existem três**. O gabarito do anotador independente é o mais
severo — no piloto dá 87,5% contra 92,5% do autor, e na confirmação 90,0% contra 97,5% — e
ficava de fora dos cartões que se lê primeiro. O rótulo que deveria denunciar isso perguntava a
coisa errada: se a adjudicação mudou algum caso, e não se os anotadores discordaram. Com essa
pergunta, o piloto aparecia como unânime tendo quatro casos em disputa dentro dele.

A décima terceira rodada trocou de método: em vez de reler o código, **mutou os dados** e
perguntou quais cartões se mexiam. Zerando as nove divergências do anotador independente dentro
de `runs/e8-anotador/relatorio.json`, os cartões do E1 e do E7 acompanharam e o do E8 ficou
parado. Ele não recalculava nada — lia dois agregados gravados dentro do próprio relatório no
momento em que aquele experimento rodou. Era o defeito da nona rodada, número velho em caixa
nova, sobrevivendo justamente no cartão que fala de gabarito. A correção criou
`gabarito.desempenho_do_estudo()`, que soma E1 e E7 sob os três gabaritos na hora da leitura, e
o teste de mutação virou teste permanente.

A auditoria de mutação foi então aplicada a todos os relatórios, e achou um **segundo** cartão
cego: o E3 lia o bloco `jev` gravado no alto de `runs/e3-evidencia/relatorio.json` em vez de
contar os casos. Os dois números batem hoje — 23 acertos em 24 — e é justamente por isso que
nenhum teste de coerência podia pegá-lo: um número congelado parece correto enquanto ninguém
mexe nos dados. Trocados cinco acertos por erros, o cartão continuava estampando 95,8%. Hoje ele
recalcula e a auditoria de mutação virou teste permanente sobre todos os relatórios que têm
lista de casos.

A mesma rodada achou um defeito que nenhum teste do painel podia achar, porque não estava no
painel: **`output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf` e `output/pdf/RELATORIO-FINAL-JEV.pdf`
eram o mesmo arquivo**, byte a byte, e já tinham sido versionados assim. O gerador do relatório
chamava a função que monta o PDF do plano e copiava o resultado; aquela função gravava sempre no
caminho do plano e montava sempre a capa do plano. Cada build do relatório destruía o plano, e o
relatório que foi entregue abria anunciando *"ensaios dos sistemas ainda pendentes"* — depois de
todos os ensaios terminados. Capa e destino passaram a ser do chamador, o relatório ganhou capa
própria com números vindos do placar, e dois testes novos exigem que cada PDF abra no documento
que o nome dele promete.

A mesma décima terceira rodada cobrou quatro coisas que eu podia verificar e uma que eu podia
executar. As quatro: o pré-registro do E1 mandava reportar erro grave separado da acurácia
média, e isso nunca tinha sido feito (seção 3.7); o `runs/ledger.sqlite3` é ignorado pelo Git, e
sem ele o custo publicado era uma citação que ninguém de fora podia conferir (agora
`runs/extrato-ledger.json` vai versionado); o `.gitignore` tinha `runs/` puro, e como o Git não
desce em diretório excluído **nenhuma** das exceções abaixo dele valia; e o README dizia "nove
rodadas" enquanto este documento dizia treze.

A quinta foi a que importou. O revisor apontou que o único comparador do estudo era uma regra
congelada que eu mesma escrevi, e que a pergunta P1 do plano seguia sem metade da resposta.
Executei o E10 (seção 3.8), com regra de decisão congelada antes da primeira chamada. O
resultado contrariou a recomendação que este documento vinha fazendo desde a primeira versão, e
a recomendação mudou. Custou US$ 0,000358, e as treze revisões adversariais feitas até ali não
o teriam encontrado, porque nenhuma delas estava olhando para fora do que já havia sido medido.

O E10 e o E10b abriram uma divisão que nenhum dos dois podia fechar, e o E11 foi escrito para
fechá-la: corpus novo, 20 famílias declaradas antes do primeiro caso, regra de decisão congelada
antes de existir dado. Ele fechou, mas não onde eu esperava. A vantagem do Jev sobre o
comparador barato é nítida sob o meu gabarito e some sob o do anotador independente — mesma
execução, mesmas respostas, mesmos 60 casos.

Três defeitos apareceram no caminho e estão corrigidos: a primeira execução do E11 perdeu 120
chamadas pagas porque nada era persistido; `titulo_do_veredito` tinha virado impura e passou a
responder pelo repositório em vez de responder pelos dados que recebia; e o run de tentativas
órfãs se substituía a cada publicação, apagando as próprias órfãs e desfazendo em silêncio a
reconciliação de custo que a oitava rodada tinha estabelecido.

A décima quarta rodada foi a mais útil de todas, e foi a que me corrigiu contra mim mesma. Ela
mostrou que eu havia enterrado um resultado pré-registrado usando como ouro um modelo de 7B cujo
modo de errar é justamente o que o sistema avaliado supera; que o procedimento para resolver
isso já existia no próprio estudo, o terceiro juiz cego do E8b, e que o E11 tinha parado antes
dele. Rodei, sob emenda com a regra escrita antes, e o juiz confirmou meu gabarito em 10 de 10.
A recomendação mudou pela quinta vez.

A mesma rodada achou três números velhos que conviviam com os novos no texto canônico — 625
chamadas e US$ 0,018174462 na seção 7, na seção 9 e no README — e um kappa publicado que era
anterior à ampliação do E8. O teste que existia exigia que o número certo aparecesse; não exigia
que o errado sumisse. Agora exige.

A décima quinta rodada não encontrou defeito financeiro, e encontrou o documento ainda
argumentando a recomendação anterior enquanto a seção 1 publicava a nova: a 3.10 se intitulava
*"por que ele não desempatou"* e fechava dizendo que o relatório *"não fecha a favor de
ninguém"*. Achou também uma afirmação que eu havia acabado de escrever e que era falsa — a de
que o erro grave seria a métrica que não depende do gabarito. O único falso-`cancelar` do
comparador está entre os 10 casos em disputa, e sob o gabarito do anotador independente ele
desaparece. Reconto agora sob os três, e o que sobra é mais modesto.

### 9.1 O defeito que quinze revisões adversariais não acharam, e que a execução achou

Nenhuma execução anterior deste estudo havia levado HTTP 429. O E12 levou 76.

A regra do executor é liquidar pelo pior caso reservado quando não há `usage` confiável na
resposta — e ela é correta: na dúvida, o teto sofre. Uma requisição recusada por limite de taxa
não tem `usage`, então cada uma das 76 entrou no livro-caixa por US$ 0,0066. Somaram
**US$ 0,499**: mais de vinte vezes o gasto de todo o estudo até aquele momento, e 10% do teto
autorizado inteiro, por chamadas em que **nenhum token foi processado**.

O extrato da chave mostrava US$ 0,0346 de uso acumulado. As 76 foram retificadas para zero pelo
mecanismo que já existia para isso (`retificar_liquidacao`, que só aceita corrigir liquidação
conservadora e exige motivo e evidência), com o extrato como evidência, e a regra foi corrigida
na origem: **HTTP 429 liquida zero**, porque o provedor recusa antes de gerar. A exceção vale
só para o 429 — em 5xx e em timeout a geração pode ter acontecido, e ali o conservador continua
certo.

**O que essa evidência prova, e o que ela não prova.** O extrato da chave é **agregado**: ele
diz quanto o provedor cobrou no total, não quanto cobrou em cada tentativa. Uma requisição
recusada com 429 não recebe identificador de geração, então não há recibo por tentativa a
conferir. O que sustenta a retificação é a conta agregada, e ela é conservadora nos dois
sentidos: depois de zerar as 76, o ledger ainda liquida US$ 0,035707114 contra os
US$ 0,034640289 do extrato — continua **acima** do que o provedor cobrou. Se alguma daquelas
chamadas tivesse sido cobrada, a diferença de US$ 0,001 já a absorveria. Essa é a garantia que
existe; um recibo por tentativa não existe, e este parágrafo está aqui para que ninguém leia
mais do que há.

Não era um erro de arredondamento: era o executor financeiro inventando meio dólar de gasto que
nunca existiu. Como a política é conservadora, ele errava para o lado seguro do teto e para o
lado errado da verdade — e teria bloqueado orçamento real de trabalho futuro.

Outros três defeitos apareceram na mesma execução e estão corrigidos, todos com teste:

- O interpretador de resposta do comparador assumia objeto JSON. Um modelo devolveu uma **lista**
  e a execução inteira caiu com `AttributeError`, depois de 361 chamadas pagas. Resposta fora do
  contrato é erro do comparador; agora ela vira erro, e não exceção.
- A marca que anula da análise as chamadas feitas sob teto de saída insuficiente viajava junto no
  registro da reexecução e apagava também a **resposta nova**. Nove chamadas já pagas do
  gpt-oss-20b sumiram da análise sem que nada acusasse — e sumiram justamente inflando a
  vantagem do Jev sobre aquele braço, de +14,4% para +24,4%. Corrigido, o número voltou a +14,4%.
- O custo publicado no painel e no relatório do E12 vinha do valor que cada caso guardou no
  instante da chamada, e não do livro-caixa. Depois da retificação, os dois divergiam em
  US$ 0,052 — os dois números de custo no mesmo painel que a oitava rodada já havia proibido.
  Agora ambos leem `attempt_budget`.

A décima sexta rodada revisou o E12 inteiro e não derrubou a conclusão central. Encontrou três
coisas, todas corrigidas e agora travadas por teste: as adjudicações do E11 e do E12 não iam no
Git, e o relatório se apoia nelas para dizer "o terceiro juiz confirmou meu gabarito em 10 de
10"; o número de `cancelar` perdidos do gpt-oss-20b no texto era anterior à correção de 9.1; e o
README dizia "empata exatamente com o mais barato" onde o dado diz "não separa de zero", ainda
por cima atribuindo o empate ao braço errado. As três são a mesma família de defeito que este
relatório persegue desde a nona rodada, e duas delas eu cometi ao escrever sobre o experimento
que acabara de corrigir esse mesmo tipo de erro.

Estado final: **1.474 tentativas, nenhuma reserva pendente sem liquidação, US$ 0,035707114 de
US$ 5,00, conciliado contra um extrato de US$ 0,034640289, e 176 testes automatizados passando.**
A chave da API nunca foi versionada, impressa em log ou copiada para documentação.

---

## 9.2 O E13: aplicar o Jev aos fluxos de trabalho desta casa

Os doze experimentos anteriores mediram o Jev em corpora construídos para medi-lo. O E13 é
diferente: ele o coloca dentro do fluxo real de trabalho do Claude Code e do Codex, com o
material que o Igor de fato escreveu, para responder a uma pergunta de economia — o Jev, que
custa US$ 0,042 por milhão de tokens de entrada e nada na saída, consegue poupar trabalho de
modelos milhares de vezes mais caros?

A amostra saiu de 8.801 pedidos distintos do histórico e de 1.990 comandos de shell realmente
executados. Os gabaritos foram anotados antes de cada execução, com o mesmo viés de autor que o
E8 e o E11 mediram. Custo: US$ 0,0104 em 455 chamadas.

**O roteamento de esforço não funciona, e o motivo não é a formulação da pergunta.** Quatro
formulações foram testadas, da mais abstrata à mais concreta, e nenhuma produziu cobertura útil:

| Formulação | Acurácia | Cobertura útil |
|---|---|---|
| Quatro classes de esforço | 51,7% | 0% |
| "O pedido diz onde mexer?" | 66,7% | 0% |
| "Quantos minutos leva?" | 70,0% | 0% |
| A mesma, com o contexto da conversa anterior | 71,8% | 0% |

Cobertura útil é a fração de pedidos mandados para o caminho barato com confiança acima do
corte. Quando o Jev diz "simples", diz com confiança de no máximo 0,73 — não existe ponto de
operação. Uma terceira pergunta explicou a razão: **54 dos 60 pedidos reais são continuações**
("continue", "verifique e corrija então", "piorou tudo"), e a informação que decidiria não está
escrita na mensagem. Dar a conversa anterior ao modelo moveu 2,6 pontos e nenhuma cobertura.

Este é o terceiro achado do estudo sobre o *método* e não sobre o modelo, e o mais caro de
descobrir tarde: **a pergunta certa pode não ter resposta no texto disponível.** Nenhuma
melhoria de classificador resolve isso.

**O guarda de comando irreversível funciona, e não serve aqui.** Em 60 comandos executados, o
Jev somado à regra por palavra libera 14 dos 30 alarmes falsos sem soltar nenhum dos 4 comandos
irreversíveis reais, e nos quatro ele nunca passou do corte de confiança. O resultado é bom e
inútil nesta máquina, que roda em `acceptEdits` com `Bash(*)` liberado: não há confirmação para
poupar. Fica medido para o dia em que o modo de permissão mudar.

**O que funciona é o que o E1 já dizia: dizer sobre o que é a mensagem.** A linha de base não é
hipotética — são os oito `hookify.suggest-skill-*` que já rodavam por `regex_match` a cada
prompt. Com corte de confiança 0,90, nos mesmos 60 pedidos:

| | Temas reais encontrados (de 23) | Sugestões à toa (em 37 sem tema) |
|---|---|---|
| **Jev** | **9** | **0** |
| Os regex de hoje | 5 | 1 |

Quase o dobro da cobertura sem nenhum disparo falso, e o erro do Jev é por omissão: 10 dos 13
erros foram deixar de sugerir, não sugerir errado. O corte é 0,90 e não o 0,99 da seção 6.1
porque a assimetria é outra — aqui uma sugestão perdida custa uma skill não carregada, e uma
sugestão errada custa três linhas de contexto. O corte foi calibrado neste dado, e não
transportado do E12, que é precisamente o que a seção 6.1 manda fazer.

Está instalado como hook `UserPromptSubmit` nos dois clientes, em modo ativo, verificado de
ponta a ponta numa sessão real. Falha para o lado aberto, mascara credencial antes de qualquer
envio, e o custo por chamada é verificado contra o teto antes de ela sair. O pacote, a medição
e as instruções de remoção estão em `integracao/`.

**A conclusão para a pergunta de economia é negativa e vale registrá-la assim:** o Jev não
consegue decidir quanto esforço um pedido merece, porque essa informação não está no pedido. Ele
consegue dizer do que o pedido trata, e é só isso que foi instalado.

---

## 10. Próximo movimento

1. ~~**Repetir o E10 em amostra maior**, com pelo menos 30 famílias, e com dois ou três LLMs
   econômicos em vez de um.~~ **Feito: é o E12, seção 3.12.** 30 famílias, quatro comparadores,
   US$ 0,013. O resultado fecha a pergunta que este item fazia e abre outra: sob o gabarito
   adjudicado o Jev vence os quatro; sob o gabarito independente ele empata com o mais barato
   deles. Mais medição não separa essas duas leituras, porque a diferença entre elas não é de
   amostra.
2. **Coletar 200 mensagens reais de um canal de atendimento**, com a distribuição de classes que
   o canal tem — responsável: Igor; critério: corpus anonimizado disponível em `data/corpus/`.
   **Este é agora o item que bloqueia todos os outros**: enquanto o rótulo for meu, cada
   experimento novo só acrescenta precisão a uma medida cuja referência não foi validada.
3. **Anotar com dois humanos independentes** e medir kappa entre eles antes de olhar o modelo —
   critério: kappa humano-humano ≥ 0,80; abaixo disso, o problema é a definição das classes,
   não o modelo.
4. **Rodar a política do corte 0,90 em sombra** sobre esse corpus real, sem efeito em produção,
   medindo cobertura e erro entre aceitos — critério: erro entre aceitos ≤ 1% com cobertura
   ≥ 70%.
5. **Cronometrar o fluxo humano** durante a sombra, para fechar a pergunta P5 com dado medido em
   vez de parâmetro declarado.
6. **Só então** decidir se a política sobe para produção, e com qual corte.

O item 1 está fechado. Os itens 2 e 3 dependem de gente, não de orçamento, e são o caminho
crítico. Restam US$ 4,96 do teto autorizado, o que cobre com folga toda a fase de sombra — e a
folga não é o que falta.

---

*O estudo que eu queria ter feito é o que começa no item 2. O que está aqui é o que dá para
saber sem dados reais — e o principal valor dele é ter descoberto, antes de gastar, exatamente
onde o modelo quebra: no mesmo caso, perguntado duas vezes. O E12 acrescentou o segundo achado
dessa natureza, e ele é sobre o método e não sobre o modelo: quando a conclusão depende de quem
escreveu o gabarito, triplicar a amostra não a torna menos dependente — só mais precisa dentro
de cada gabarito.*

**— Helena.** Café preto, sem açúcar.
