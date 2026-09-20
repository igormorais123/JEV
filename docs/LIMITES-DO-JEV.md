# Os limites do Jev — mapa empírico

> Programa E14, 2026-09-19. 2.522 chamadas reais ao `typesafe/jev-1.13`, US$ 0,17597.
> Consumo acumulado da chave, todos os caminhos, pelo livro-caixa: US$ 0,28363 de US$ 5,00
> autorizados. Só a parte do dossiê (US$ 0,03571) está conciliada contra extrato do provedor.
> Pré-registro e emendas datadas: `laboratorio/PREREGISTRO.md`.
> Dados brutos: `laboratorio/mapa-de-limites.json`. Visual: `output/mapa-de-limites.html`.

Os experimentos E1 a E13 mediram **quanto o Jev acerta**. Este mediu **onde ele para de
acertar**, e foi a única família de rodadas que produziu uma vantagem do Jev que não depende de
quem escreve o gabarito.

---

## 1. O achado que fecha a questão aberta desde o E10

Desde o E10 a pergunta era: *se um LLM genérico barato empata em acurácia, por que usar o Jev?*
A resposta não estava na acurácia. Está no contrato.

Quatro vetores de manipulação foram escritos **dentro do texto do cliente** — ordem direta,
falsa autoridade, bloco de formato e sugestão — e a mesma bateria de 40 tentativas foi enviada
aos cinco modelos:

| Modelo | Manipulado | Taxa | IC95 | Viraram `cancelar` |
|---|---|---|---|---|
| `openai/gpt-oss-20b` | 28/40 | **70,0%** | 0,546–0,819 | 4 |
| `google/gemma-3-12b` | 10/40 | **25,0%** | 0,142–0,402 | **10** |
| `meta-llama/llama-3.1-8b` | 5/40 | 12,5% | 0,055–0,261 | 3 |
| `mistralai/mistral-nemo` | 0/40 | 0,0% | 0,000–0,088 | 0 |
| **`typesafe/jev-1.13`** | **0/40** | **0,0%** | 0,000–0,088 | 0 |

Dezessete respostas viraram `cancelar` — a classe irreversível — porque o cliente escreveu uma
linha de texto. O `gemma-3-12b` caiu em 10 de 10 no vetor de formato, todas para cancelamento.

**Mecanismo:** no contrato do Jev o texto de terceiro vai em `state` e as opções em `questions`,
campos estruturalmente separados. Num LLM genérico tudo é concatenado numa string de prompt, e
texto de terceiro fica indistinguível de instrução. A imunidade é arquitetural, não estatística.

**Ressalva material:** o `mistral-nemo` também resistiu a 100%. A afirmação honesta é *"três dos
quatro comparadores são manipuláveis"*, não *"só o Jev resiste"*.

### 1.1 A R15 derrubou o "0% de manipulação" e o devolveu mais preciso

A ressalva que eu mesma escrevi aqui — *"os quatro vetores foram escritos por quem conhece o
alvo"* — foi testada. Três LLMs receberam a tarefa de escrever os ataques; dois produziram 12
vetores que eu não escrevi. Sob eles, **o Jev virou 10 de 120 respostas, 8,3%**. A afirmação
"imune a instrução injetada", como estava publicada, caiu.

Olhando os dez casos, eles têm uma coisa que os meus quatro vetores não tinham: **não falam com
o classificador**. Escrevem dentro da mensagem um pedido de cancelamento de verdade —
*"solicitamos o cancelamento de seu serviço atual"*, *"solicito a imediata finalização do
serviço"*. Isso não é manipular quem lê: é mudar o que está escrito. Separando as duas coisas:

| | Família A — fala com o classificador | Família B — acrescenta conteúdo |
|---|---|---|
| | protocolo falso, "aprovado sem análise", formato imitado | "seu serviço foi cancelado", "solicito o cancelamento" |
| **`typesafe/jev-1.13`** | **0/50 = 0,0%** | 10/70 = 14,3%, **0 acima do corte 0,90** |
| `meta-llama/llama-3.1-8b` | 8/50 = 16,0%, **8 acima do corte** | 17/70 = 24,3%, **13 acima do corte** |
| `mistralai/mistral-nemo` | 5/50 = 10,0%, **5 acima do corte** | 8/70 = 11,4%, **8 acima do corte** |
| `google/gemma-3-12b` | 1/28 = 3,6%, 1 acima do corte | 3/38 = 7,9%, 3 acima do corte |
| `openai/gpt-oss-20b` | 0/36 = 0,0% | 2/32 = 6,2%, 2 acima do corte |

**O que sobrevive, e é mais forte que a versão anterior:**

1. **Na família A o Jev continua em zero, agora contra vetores de terceiros** — e o `mistral-nemo`,
   que resistia aos meus quatro, cai em 10% destes. O empate que enfraquecia o achado sumiu.
2. **Na família B o Jev muda a resposta, e deve mudar:** o texto mudou. E a confiança cai junto —
   **0,52 nas viradas contra 0,92 nos acertos**, com a maior virada em 0,80. Nenhuma passaria pelo
   corte de 0,90.
3. **Nos comparadores a confiança não protege:** 26 das 34 viradas vieram com 0,90 ou mais.

A formulação correta, que substitui a anterior: **o Jev não obedece a quem fala com ele, e quando
o texto muda de sentido ele muda de resposta avisando que mudou.** Os comparadores obedecem, e
não avisam.

Dado bruto: `laboratorio/r15-adversario-externo.json` e `laboratorio/r15b-familias.json`. A
separação das famílias é minha, foi escrita olhando os textos antes de recontar, e os doze estão
em `r15-vetores-gerados.json` para quem quiser discordar dela.

---

## 2. O modo de falha mais perigoso, e a mitigação de uma linha

Dez textos **sem pedido algum** — uma política interna, uma receita de bolo, "Bom dia.", letras
aleatórias — foram classificados na taxonomia de cinco ações do atendimento:

| Condição | Resposta | Confiança média | Acima de 0,90 | Acerto |
|---|---|---|---|---|
| Sem classe de escape | `informacao` nas 10 | **0,987** | 10/10 | — |
| Com `nao-se-aplica` | `nao-se-aplica` nas 10 | 0,927 | 7/10 | **10/10** |

Sem saída, ele erra em silêncio **com certeza máxima**: nenhum corte de confiança protege, porque
a confiança não cai. Com a saída explícita, acerta tudo.

> **Regra de projeto:** toda taxonomia entregue ao Jev precisa de uma classe de escape
> (`nao-se-aplica`, `nenhuma das anteriores`). É a recomendação mais barata e mais importante
> deste programa.

---

## 3. Onde ele quebra de verdade

| Dimensão | Nível | Acurácia | Confiança nos erros | Leitura |
|---|---|---|---|---|
| **Ruído tipográfico** | 5% | 96,7% | — | sem efeito |
| | estilo Igor (real) | 96,7% | — | sem efeito |
| | 15% | 93,3% | — | leve |
| | 30% | 80,0% | 0,35 | degrada, **e avisa** |
| | 50% | 46,7% | 0,34 | quebra, **e avisa** |
| | 70% | 36,7% | 0,27 | quebra, **e avisa** |
| **Armadilha semântica** | ação de terceiro | **75,0%** | 0,39 | pior família das seis |
| | ação parcial | 87,5% | 0,41 | |
| | pressuposto | 87,5% | 0,53 | |
| | adiado / concluída / negado | 100% | — | resolve bem |
| **Combinado** | ruído 50% + 160 opções + 8k | **23,3%** | 0,54 | soma de estresses colapsa |

O padrão que sustenta a operação: **quando ele quebra, a confiança cai junto.** Sob texto sujo,
a confiança média dos erros foi 0,27–0,35 contra ~0,89 dos acertos. Zero erros acima de 0,90 em
todas as condições de ruído. Um corte de confiança continua protegendo exatamente onde ele falha.

---

## 4. Onde ele não quebra (e o que isso contradiz no guia)

| Dimensão | Varredura | Resultado |
|---|---|---|
| **Diluição de contexto** | 0k → 50k caracteres, recheio antes e depois | **96,7% constante**. Sem efeito. |
| **Ordem das opções** | inversa, sorteada | 98,9% nas duas. Sem efeito. |
| **Idioma** | critérios em inglês, misto, sem acento | 96,7% nas três. Sem efeito. |
| **Instrução** | reduzida a "Classifique a mensagem"; e uma auto-contraditória | 96,7% nas duas. Sem efeito. |
| **Nº de classes** | 2, 3, 5, 12 | 97,8% a 98,9%. Sem custo. |
| | 20, 40, 80, 147 | 93,3% → 90,0%, com platô |
| **Sobreposição de critérios** | os 5 critérios escritos de forma **idêntica** | **93,3%** |

Duas dessas linhas contradizem o `GUIA-PRATICO-JEV.md` como ele estava escrito:

1. **"De 3 a 6 classes"** era conservador demais. Até 12 classes não custam nada; o degrau
   aparece entre 12 e 20 e estabiliza em 90% mesmo com 147 opções.
2. **"Capriche na descrição de cada classe"** está errado na ênfase. Com os cinco critérios
   textualmente idênticos ele ainda acerta 93,3%: **ele decide pelo rótulo da classe, não pela
   descrição.** Nomear bem a classe vale mais que descrevê-la bem.

---

## 5. O falso achado que eu produzi, e por que ele fica no registro

A primeira leitura da diluição de contexto (R11) mostrou colapso para 23,3% com confiança 1,0 e
23 erros acima de 0,90 — um limite de janela espetacular. Antes de publicar, fui à causa: o
`LIMITE_DE_CARACTERES` do meu próprio núcleo estava em 12.000, e como o recheio vinha **antes**
da mensagem, o truncamento cortava fora o pedido do cliente. O modelo respondia sobre um texto
sem pedido nenhum. O limite não existia.

Corrigido para 90.000 caracteres e refeito como R12: **nenhum efeito até 50k**. O acidente virou
a R13, que produziu o achado da seção 2 — o melhor resultado prático do programa.

O episódio está em `laboratorio/PREREGISTRO.md` com data, não apagado. E foi **replicado por
outro agente**: o Codex, em E15, reproduziu a condição `legacy_truncated` de propósito e mediu
16,7% de acurácia com **5 erros aceitos em confiança 1,0** — mesma assinatura, confirmação
independente que eu não pedi.

---

## 6. Ciclo autorrecursivo: o Jev decidindo sobre os dados do Jev

As 37 condições acima foram devolvidas ao próprio Jev, que classificou cada uma em
`seguro` / `exige-cuidado` / `proibido` contra um gabarito escrito antes da rodada.

| Métrica | Valor |
|---|---|
| Concordância bruta | 21/37 = **56,8%** |
| Divergências que **afrouxam** (perigosas) | **0** |
| Divergências que apertam (conservadoras) | 16 |
| Confiança média quando concorda | 0,867 |
| Confiança média quando diverge | 0,454 |
| **No corte 0,90: aceitas** | 14 |
| **No corte 0,90: concordância** | **14/14 = 100%** |

A concordância bruta é ruim. A concordância **sob corte** é perfeita, e o erro é sempre para o
lado seguro — ele nunca liberou o que eu tinha apertado. O loop serve: automatiza 38% da
classificação de risco de novas rodadas por US$ 0,00002 cada e manda o resto para leitura humana.

---

## 7. Calibração

ECE de 0,0305 sobre os 230 casos do gabarito do autor. A confiança do Jev se comporta como
probabilidade, não como mera ordenação — com a ressalva já conhecida do corpus do E12, onde o
único erro veio com confiança 0,98. **A calibração é boa na média e não é garantia no caso.**

---

## 8. Consequências para quem aplica

1. **Classe de escape obrigatória** em toda taxonomia. Seção 2.
2. **Nomeie bem a classe; a descrição importa menos do que se pensava.** Seção 4.
3. **Até 12 classes sem custo.** Acima de 20, conte com ~90%.
4. **Corte de confiança protege contra degradação de entrada** (ruído, texto sujo), porque ali a
   confiança cai. **Não protege contra armadilha semântica de alta confiança** — a classe
   irreversível continua exigindo gente.
5. **Texto de terceiro só entra em `state`.** É onde está a vantagem que sobrevive a qualquer
   critério de correção — e, pela R15, a qualquer autor de ataque.
5b. **Distinga ataque de leitura.** Se o texto inserido pede a ação, mudar a resposta é acerto,
   não falha. O que se exige do classificador é não obedecer a quem se dirige a ele, e avisar
   quando a leitura ficou incerta. O Jev faz as duas; os comparadores, nenhuma.
6. **Diluição de contexto não é um risco.** Truncamento do cliente é — e foi o único limite real
   encontrado neste programa, no meu código, não no modelo.

---

*Todos os números deste documento saem de `laboratorio/mapa-de-limites.json`,
`laboratorio/r12-r13-contexto.json` e `laboratorio/r14-decisoes.json`, gerados pelas rodadas em
`laboratorio/r*.py`. Nenhum foi digitado à mão.*

**— Helena.**
