# Jev 1.13 — relatório final de avaliação

**Autoria:** Dra. Helena Strategos, Cientista-Chefe de Inteligência da INTEIA
**Execução:** 18–19 de setembro de 2026
**Sistema avaliado:** Jev 1.13 (`typesafe/jev-1.13` via OpenRouter e `jev-1.13.0` direto)
**Custo total:** US$ 0,022618774 em 945 chamadas, de um teto autorizado de US$ 5,00
**Código, dados e registros:** este repositório, com pré-registros em `planning/` e relatórios
brutos em `runs/`

---

## 1. Recomendação

**Não decida sobre o Jev com base neste estudo — e o motivo não é o modelo, é o gabarito. A
vantagem do Jev sobre um LLM genérico e barato aparece sob o gabarito que eu escrevi e desaparece
sob o único gabarito que não passou pela minha mão.**

O estudo terminou no experimento que existia para desempatar, e o desempate desempatou para os
dois lados. Corpus novo, 60 casos, 20 famílias declaradas no pré-registro antes de o primeiro
caso ser escrito, dois braços na mesma lista e na mesma ordem:

| Gabarito | Jev | llama-3.1-8b | Diferença pareada | IC95 | McNemar |
|---|---|---|---|---|---|
| Meu (o do corpus) | 1.0000 | 0.8667 | **13,3%** | [5,0%; 21,7%] | p = 0.0078 |
| Anotador independente | 0.8333 | 0.8667 | **-3,3%** | [-10,0%; 3,3%] | p = 0.6875 |

Pela regra congelada no pré-registro do E11, que olhava o gabarito do corpus, a leitura seria
*"há evidência de que o Jev supera um LLM econômico"*. Eu não vou parar aí, por dois motivos que
não são preferência minha.

**O primeiro é que o Jev acertou 60 de 60.** Acerto perfeito no único conjunto que só eu revisei
não é uma vitória, é um alarme. Foi por isso que rodei o anotador independente também nesses 60
casos — depois do resultado, e com o resultado já à vista. Ele discorda de mim em 10 deles, e em
todos os 10 o Jev concorda comigo.

**O segundo é que a política deste estudo, desde a décima segunda rodada de revisão, é nunca
apresentar um gabarito sozinho.** Aplicá-la aqui e não lá seria escolher a regra conforme o
resultado.

Sob o gabarito independente o sinal **inverte**: o comparador barato fica numericamente à frente,
com o intervalo contendo zero. Os dois números são da mesma execução, das mesmas respostas, dos
mesmos 60 casos. O que muda entre uma linha e outra da tabela é **quem escreveu o rótulo**.

É essa a conclusão do estudo, e ela não é sobre o Jev: **o gargalo não é a comparação entre os
modelos, é a validade do rótulo.** Nenhuma execução adicional resolve isso — não há corpus meu,
por maior que seja, que responda a uma pergunta cujo obstáculo é eu ter escrito o gabarito. O que
falta são dois anotadores humanos do domínio, medindo kappa entre si antes de olhar qualquer
modelo. É o item 3 da seção 10, custa tempo de gente e não custa orçamento nenhum.

*(Registro de método: a recomendação deste relatório mudou três vezes em um dia. Era "use o Jev
com corte em 0,90"; virou "não adote" quando o E10 não separou de zero; virou "evidência
dividida" quando o E10b separou; e é esta agora, quando o E11 mostrou que a divisão tem nome.
Cada mudança está datada e nenhuma versão anterior foi apagada. Um relatório que não muda quando
o dado muda não é um relatório estável — é um relatório que parou de ler os dados.)*

Esta recomendação substitui a anterior, que era "use o Jev como classificador consultivo com
corte de confiança em 0,90". A mudança não veio de opinião: veio dos experimentos E10 e E10b,
executados em 19 de setembro, **depois** de o relatório estar escrito e depois de treze rodadas
de revisão.

Até o E10, o único comparador deste estudo era uma **regra congelada escrita por mim** — o
comparador mais fácil de vencer que existe. A décima terceira rodada de revisão adversarial
apontou que a pergunta P1 do plano original (*vale um LLM especializado aqui, ou qualquer
classificador de linguagem resolve?*) seguia com metade da resposta. O braço foi então executado
com regra de decisão congelada antes da primeira chamada
(`planning/preregistro-E10-llm-economico.md`).

| | Acurácia (autor) | Acurácia (oficial) | Acurácia (anotador independente) |
|---|---|---|---|
| Jev 1.13 | 0.9750 | 1.0000 | 0.9000 |
| `meta-llama/llama-3.1-8b-instruct` | 0.9000 | 0.9250 | 0.8500 |

A diferença pareada é de **7,5%**, com IC95
**[0,0%; 15,0%]** por reamostragem de famílias — e esse intervalo
**contém zero**. Os dois modelos discordam em 3 casos
(cnf-g03-01, cnf-g05-04, cnf-g07-01), todos a favor do Jev, o que no McNemar exato dá
**p = 0,25**. Nenhuma das 40 respostas do comparador saiu fora do contrato.

Pela regra que eu mesma congelei antes de olhar: isto é **ausência de evidência de vantagem**, e
não equivalência. Com 10 famílias o poder é baixo por construção, e um empate aqui não prova
empate. O que cai não é o desempenho do Jev — ele continua acertando mais em números absolutos,
e nos três gabaritos. O que cai é a afirmação de que **ele é necessário**. Um modelo de 8B que
custa uma fração do preço chega perto o suficiente para que esta amostra não os separe.

**E então o E10b virou o resultado para o outro lado.** Com o intervalo primário encostando em
zero, dobrei o poder: o mesmo comparador nas 10 famílias do piloto, sob emenda escrita antes da
execução. Ali o Jev faz 0.9250 contra 0.7250 do
comparador — diferença **20,0%**, IC95
[10,0%; 30,0%], que **separa** de zero. Nas
20 famílias das duas partições juntas: **13,8%**,
IC95 [7,5%; 20,0%], que também separa.

A emenda mandava tratar isso como secundário porque *"o piloto guiou o desenho do prompt do
Jev"*. **Fui conferir no histórico do repositório e essa premissa não se sustenta:** as
instruções entraram uma única vez, no commit `9f6d13b` de 18/09, junto com o corpus piloto, e
nunca mais mudaram. Não houve iteração de prompt. Sobra um viés menor e real — a rubrica e o
corpus piloto foram escritos juntos, então a rubrica casa com aquele corpus por construção —, e
sobra o fato decisivo: **a decisão de olhar o piloto foi tomada depois de eu ver o resultado
primário.**

Por isso a recomendação não volta a ser "use o Jev". Escolher agora a leitura de 20 famílias,
que é justamente a que devolve a conclusão que eu já tinha publicado, seria escolher o resultado
depois de vê-lo — o vício que este relatório passa dez seções condenando. E também não é "os
dois empatam", porque em 20 famílias eles não empatam. É a terceira leitura, que é a única que
os dados aguentam: **a evidência não basta para decidir.**

**O que fazer com isso:** rodar os dois lado a lado num corpus novo, pré-registrado, com pelo
menos 30 famílias, colhido de uso real. É o desempate, e custa quase nada: as 80 chamadas do E10
e do E10b custaram US$ 0,000702 somadas.

*(Registro de método: este resultado poderia ter ficado fora do relatório. O E10 não estava no
plano original, foi sugerido por um revisor adversarial, contraria a conclusão que eu já havia
publicado e me custou reescrever a recomendação que treze rodadas de revisão tinham poupado.
Executá-lo e publicá-lo é o único motivo pelo qual as outras conclusões deste documento merecem
algum crédito.)*

---

### 1.1 A política de corte, que continua válida no que ela mede

O restante desta seção descreve a política de aceitação estudada no E9. Ela **não** é mais a
recomendação do estudo — a recomendação é a de cima —, mas o que ela mede continua valendo, e é
o que se deve usar caso a decisão de adotar o Jev seja tomada por outros motivos que não este
estudo.

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

**Confiança: 0,25.** Este número deixou de ser
um julgamento meu e passou a ser uma conta com as penalidades declaradas, partindo de 1,0:

- a política se apoia em 40 casos, menos de cem (-0,20)
- 1 caso(s) mudam de resposta entre repetições idênticas (-0,10)
- o gabarito foi adjudicado por modelos, não por pessoas do domínio (-0,10)
- corpus construído pelo avaliador, não colhido de uso real (-0,10)
- zero erro observado entre os aceitos, mas o limite superior de 95% por família é 25,9% (-0,10)
- no corpus de desempate a vantagem do Jev sobre o LLM econômico separa de zero sob o gabarito do autor e não separa sob o do anotador independente (-0,15)

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
| OpenRouter | \- | 0,925 | 396 ms | 22.167 nusd |
| TypeSafe direto | **40/40 (100%)** | 0,925 | 755 ms | 24.804 nusd |

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

| Conjunto | Gabarito | `cancelar` indevido | `cancelar` perdido | Teto do erro grave (por família) | Regra congelada |
|---|---|---|---|---|---|
| piloto (E1) | anotador local | **0** | 2 | 25,9% | 3 |
| piloto (E1) | autor | **0** | 1 | 25,9% | 4 |
| piloto (E1) | oficial | **0** | 1 | 25,9% | 4 |
| confirmação (E7) | anotador local | **0** | 1 | 25,9% | 5 |
| confirmação (E7) | autor | **0** | 0 | 25,9% | 6 |
| confirmação (E7) | oficial | **0** | 0 | 25,9% | 6 |

**O Jev não cometeu nenhum erro grave nos 80 casos, sob nenhum dos três gabaritos.** A regra
congelada comete 10. Este é o resultado mais favorável ao modelo em todo o estudo, e é
exatamente por isso que o teto vai na mesma tabela: com 10 famílias por conjunto, zero erro
observado só permite afirmar que a taxa por família está **abaixo de 25,9% com 95% de
confiança**. Zero observado não é zero verdadeiro, e um teto de um quarto por família não é uma
garantia operacional. O que este número autoriza dizer é que o erro irreversível não apareceu
onde a regra congelada o comete dez vezes; o que ele não autoriza é prometer que não aparecerá.

O sentido oposto — `cancelar` que o modelo deixa passar — aparece em 1 ou 2 casos conforme o
gabarito. Custa atraso, não destruição, e por isso está na tabela mas fora da definição de erro
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
| Jev 1.13 | 0.9750 | 1.0000 | 0.9000 | 0 |
| llama-3.1-8b | 0.9000 | 0.9250 | 0.8500 | 0 |
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

| Conjunto | Famílias | Jev | llama-3.1-8b | Diferença | IC95 | Separa de zero? |
|---|---|---|---|---|---|---|
| Confirmação (teste) | 10 | 0,9750 | 0,9000 | 7,5% | [0,0%; 15,0%] | **não** |
| Piloto | 10 | 0.9250 | 0.7250 | 20,0% | [10,0%; 30,0%] | sim |
| Os 80, 20 famílias | 20 | 0,9500 | 0,8125 | 13,8% | [7,5%; 20,0%] | sim |

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
A conclusão honesta é a que ficou na seção 1: **a evidência não basta para decidir**, e o
desempate é um corpus novo com pelo menos 30 famílias, pré-registrado antes de qualquer chamada.

---

### 3.10 O desempate (E11), e por que ele não desempatou

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

| Gabarito | Jev | llama-3.1-8b | Diferença | IC95 | Só o Jev acerta | Só o comparador | McNemar |
|---|---|---|---|---|---|---|---|
| Meu | 1.0000 | 0.8667 | 13,3% | [5,0%; 21,7%] | 8 | 0 | p = 0.0078 |
| Anotador independente | 0.8333 | 0.8667 | -3,3% | [-10,0%; 3,3%] | 2 | 4 | p = 0.6875 |

Erro grave (`cancelar` indevido): **Jev 0, comparador 1**. É a única métrica do E11 em que a
diferença não depende do gabarito, e é a métrica que o pré-registro do E1 chamou de
irreversível.

**Os 10 casos em que o anotador independente discorda de mim:**
`dsp-d01-02`, `dsp-d03-01`, `dsp-d06-03`, `dsp-d09-01`, `dsp-d10-03`, `dsp-d11-01`, `dsp-d12-01`, `dsp-d16-01`, `dsp-d16-02`, `dsp-d18-01`. Em **todos** eles o Jev responde o que eu responderia. Há duas leituras
para isso, e eu não tenho como escolher entre elas com o que este estudo mediu:

1. O Jev segue a rubrica escrita melhor do que um modelo de 7B segue, e o anotador é que erra —
   o padrão das discordâncias dele é o mesmo dos corpora anteriores, puxar para ação onde o
   enunciado pede informação.
2. Eu escrevi 60 casos que casam com a leitura do Jev, sem perceber, porque conheço as respostas
   dele desde o E1.

A segunda não é paranoia: é exatamente o que um corpus escrito pelo avaliador permite. E é por
isso que o relatório não fecha a favor de ninguém.

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

---

## 7. Custo e operação

**Medido:** 625 chamadas, US$ 0,018174462 no total. Custo por decisão individual ~US$ 0,000022.
Latência mediana 396 ms no OpenRouter.

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
   com um terceiro juiz, mas os três são modelos de linguagem. O kappa de 0,8593 mede que a
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
7. **O gabarito é meu em todos os corpora, inclusive no do desempate.** Esta é a limitação de
   que todas as outras derivam, e o E11 a tornou mensurável em vez de apenas declarada: a
   conclusão sobre a necessidade do Jev **muda de sinal** conforme o gabarito adotado.
8. **Um único LLM econômico foi testado como comparador.** O E10 usou
   `meta-llama/llama-3.1-8b-instruct`. Um empate com ele não é empate com a categoria, e uma
   vantagem sobre ele também não seria vantagem sobre a categoria. O que o E10 estabelece é que
   **um** modelo barato chega perto o bastante para esta amostra não separar os dois.
9. **Nenhuma conclusão sobre os outros 14 sistemas do plano.** A rodada simples offline dos 15
   sistemas mostrou 5 suítes passando, 7 falhando e 3 sem como rodar. Isso é estado de
   repositório, não evidência de comportamento.

---

## 9. Controle financeiro e integridade do processo

O controle de gastos foi tratado como código crítico e passou por **treze rodadas de revisão
independente**, todas conduzidas por modelos de outros fornecedores (gpt-6-astra via Codex e
Grok 4.6 via Cursor). As quatro primeiras encontraram
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
comprometido é US$ 0,018174462.

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
a recomendação mudou. Custou US$ 0,000358 e treze rodadas de revisão não o teriam encontrado,
porque nenhuma delas estava olhando para fora do que já havia sido medido.

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

Estado final: **945 tentativas, nenhuma reserva pendente sem liquidação, US$ 0,022618774 de
US$ 5,00, 144 testes automatizados passando.** A chave da API nunca foi versionada, impressa em
log ou copiada para documentação.

---

## 10. Próximo movimento

1. **Repetir o E10 em amostra maior**, com pelo menos 30 famílias, e com dois ou três LLMs
   econômicos em vez de um — critério: o IC95 da diferença pareada separar de zero, ou não
   separar com poder suficiente para que "não separa" signifique alguma coisa. É o movimento
   mais barato da lista (as 40 chamadas custaram US$ 0,000358) e o que mais muda a decisão: se o
   empate se confirmar, a discussão deixa de ser "qual modelo" e passa a ser "qual o mais
   barato que passa".
2. **Coletar 200 mensagens reais de um canal de atendimento**, com a distribuição de classes que
   o canal tem — responsável: Igor; critério: corpus anonimizado disponível em `data/corpus/`.
3. **Anotar com dois humanos independentes** e medir kappa entre eles antes de olhar o modelo —
   critério: kappa humano-humano ≥ 0,80; abaixo disso, o problema é a definição das classes,
   não o modelo.
4. **Rodar a política do corte 0,90 em sombra** sobre esse corpus real, sem efeito em produção,
   medindo cobertura e erro entre aceitos — critério: erro entre aceitos ≤ 1% com cobertura
   ≥ 70%.
5. **Cronometrar o fluxo humano** durante a sombra, para fechar a pergunta P5 com dado medido em
   vez de parâmetro declarado.
6. **Só então** decidir se a política sobe para produção, e com qual corte.

Os itens 2 e 3 dependem de gente, não de orçamento; o item 1 depende só de orçamento, e de muito pouco. Restam US$ 4,98 do teto autorizado, o que
cobre com folga toda a fase de sombra.

---

*O estudo que eu queria ter feito é o que começa no item 1. O que está aqui é o que dá para
saber sem dados reais — e o principal valor dele é ter descoberto, antes de gastar, exatamente
onde o modelo quebra: no mesmo caso, perguntado duas vezes.*

**— Helena.** Café preto, sem açúcar.
