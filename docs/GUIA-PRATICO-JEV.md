# Como aplicar o Jev — guia de uso

*Documento de aplicação. Todos os números vêm dos experimentos E1 a E12 e do livro-caixa; nenhum
é estimativa. O método completo está em `docs/RELATORIO-FINAL-JEV.md`.*

---

## 1. Para que serve, em uma frase

O Jev lê um texto e responde **uma pergunta fechada sobre ele**, devolvendo a resposta já
classificada, com um número de confiança junto. Ele não escreve, não resume e não conversa: ele
decide entre opções que você define.

É isso que ele faz bem, e é aí que ele deve ser aplicado: **onde existe uma decisão repetitiva,
com opções conhecidas, que hoje alguém toma lendo texto**.

---

## 2. As três aplicações testadas, com o ganho medido

### Aplicação 1 — Triagem: "o que esta pessoa está pedindo?"

Entra uma mensagem, sai uma classe: `cancelar`, `rastrear`, `trocar`, `cobranca`, `informacao`
(as classes são suas, estas foram as do teste).

**Acerto: 92,5% no piloto, 97,5% no conjunto de confirmação, 98,9% no corpus novo.** O método
por palavra-chave, no mesmo teste: 60,0%, 32,5%. Não é uma melhora incremental — é outra
categoria de resultado.

Onde aplicar: fila de atendimento, caixa de entrada de e-mail, WhatsApp comercial, protocolo de
demandas internas. Qualquer lugar onde alguém hoje lê para encaminhar.

### Aplicação 2 — Verificação: "o que este texto afirma se sustenta no documento?"

Entra uma afirmação mais a evidência, sai se a evidência suporta a afirmação.

**Acerto: 95,8%, contra 62,5% da regra simples.**

Onde aplicar: conferência de citação antes de protocolar peça, checagem de número em relatório
contra a fonte, revisão de contrato contra o que a proposta prometia. É a aplicação mais
diretamente útil no trabalho jurídico.

### Aplicação 3 — Ordenação: "qual trecho muda a resposta?"

Entra uma pergunta mais um conjunto de trechos, sai a ordem de relevância.

**Achou as 8 de 8 ressalvas e colocou no top-3.** O BM25, que é o método de busca padrão, achou
5 de 8. A ordem original do documento, 4 de 8.

Onde aplicar: achar a exceção escondida no meio do contrato, a cláusula que inverte a regra
geral, o parágrafo que ressalva o artigo anterior. **É onde ele mais se destaca sobre o que se
usa hoje**, e é a aplicação menos óbvia das três.

---

## 3. Onde ele brilha: o tipo de texto que derruba os outros métodos

O ganho do Jev não aparece em mensagem fácil — aparece exatamente onde o vocabulário engana.
Estes são casos reais do teste, em que o Jev acertou e um LLM genérico e barato errou:

**"Como faço para cancelar pelo aplicativo? Não quero que vocês cancelem nada agora, só quero
saber o caminho."** — a palavra "cancelar" aparece duas vezes e o pedido é de informação.
Jev: *informação*. LLM barato: *cancelar*.

**"Minha esposa quer cancelar o plano. Eu não quero; só me explica o que muda."** — a ação é de
terceiro e foi recusada por quem escreve. Jev: *informação*. LLM barato: *cancelar*.

**"Quero devolver o produto e receber o dinheiro de volta. Não quero outro no lugar."** —
"devolver" cabe em duas classes, e quem decide é o complemento. Jev: *cobrança*. LLM barato:
*trocar*.

**"Meu irmão disse para deixar como está, mas quem paga a conta sou eu: cancela."** — o pedido
real vem depois de uma opinião contrária. Jev: *cancelar*. LLM barato: *cobrança*.

**"Do pedido 8891, cancela só o item da caneca. O resto mantém."** — cancelamento parcial
continua sendo cancelamento. Jev: *cancelar*. LLM barato: *trocar*.

O padrão é sempre o mesmo: **a ação está negada, citada, condicional, adiada ou parcial.** É o
texto que uma pessoa apressada também erra. Se o seu material tem muito disso — e texto de
cliente e texto jurídico têm —, é aí que o investimento se paga.

---

## 4. Como aplicar, passo a passo

**Passo 1 — Escreva as opções antes de qualquer teste.** De 3 a 6 classes, cada uma com uma
frase dizendo o que entra nela. As classes ruins são as que se sobrepõem; se você hesita entre
duas ao classificar à mão, o modelo também vai hesitar — e o problema é da definição, não dele.

**Passo 2 — Separe a classe perigosa.** Em toda aplicação existe uma opção cujo erro não tem
volta (aqui foi `cancelar`). Essa classe **nunca** vai para o automático, qualquer que seja a
confiança. Trate-a como fila prioritária de revisão humana.

**Passo 3 — Rode em sombra por duas semanas.** O modelo responde, ninguém age pela resposta
dele, e no fim se compara com o que a equipe decidiu. É barato: mil decisões custam **US$ 0,02**.

**Passo 4 — Escolha o corte pelo seu dado, não pelo deste estudo.** Veja a seção 5: o corte que
funcionou em dois corpora falhou no terceiro. O corte tem de ser calibrado no material real.

**Passo 5 — Só então automatize o que passa do corte**, mantendo revisão humana do resto e da
classe perigosa. E volte a medir de tempos em tempos: o modelo não é determinístico.

---

## 5. O cuidado mais importante: a confiança é útil, mas não é garantia

Este é o ponto que mais muda a aplicação prática, e ele vem do experimento mais recente.

Nos dois primeiros corpora, **todos** os erros do Jev ficaram abaixo de 0,90 de confiança.
Aceitar automaticamente o que passava de 0,90 resolvia 87,5% das mensagens **sem nenhum erro
entre as aceitas**. Era a política recomendada.

No corpus novo, com 90 casos, isso não se repetiu: o único erro do modelo veio com **confiança
0,98**. Ele disse "cobrança" onde a resposta era "informação", na mensagem *"Posso pedir a
segunda via por aqui? Antes de pedir, me confirma se ela vem com o mesmo vencimento."* — o
pedido estava adiado, e ele leu como já feito.

| Corte de confiança | Resolve sozinho | Erros entre os aceitos |
|---|---|---|
| 0,90 | 95,6% | **1** |
| 0,95 | 90,0% | **1** |
| 0,99 | 82,2% | 0 |

**O que isso significa na prática:** a confiança continua sendo informativa — 82% das mensagens
passam de 0,99 e nenhuma delas estava errada. Mas ela **não é uma garantia**, e um corte
calibrado num conjunto não se transporta para outro. Aplique com corte alto (0,99), revisão da
classe perigosa, e recalibre no seu próprio material antes de subir o volume.

---

## 6. Quanto custa e quanto economiza

| Item | Valor medido |
|---|---|
| Mil decisões do Jev | **US$ 0,022** |
| Mil decisões do LLM genérico mais barato testado | US$ 0,006 |
| Revisar tudo com gente (2 min a US$ 12/h, **parâmetro declarado, não cronometrado**) | US$ 0,40 por decisão |
| Com corte de confiança e revisão só do resto | US$ 0,05 por decisão |
| Toda a avaliação, 1.474 chamadas reais | US$ 0,0357 |

A conta que decide **não é a do modelo** — é a do tempo de pessoa. O custo por decisão do Jev é
de dois centésimos de centavo; o da revisão humana é vinte mil vezes maior. Por isso o passo 3
acima inclui cronometrar a revisão: se ela leva 30 segundos e não 2 minutos, a economia real é
um quarto da que está nesta tabela, e ninguém mediu isso ainda.

---

## 7. Os cuidados, em ordem de risco

**1. Não automatize a classe irreversível.** Em 230 casos o Jev não errou nenhum `cancelar` — e
ainda assim a estatística só garante que a taxa por família de casos está abaixo de 9,5%. Um em
cada dez é muito quando o erro cancela o contrato de um cliente.

**2. Recalibre o corte no seu material.** Seção 5. Foi o achado que mudou esta recomendação.

**3. A mesma pergunta pode ter resposta diferente.** Repetindo 40 casos cinco vezes, 1 caso
mudou de resposta. Para decisão que não tem volta: pergunte três vezes e vá pela maioria, ou
mande para revisão.

**4. O teste foi feito com casos construídos, não com material real.** Nenhuma das 230 mensagens
veio de um canal de produção. Elas medem discriminação de linguagem, não a bagunça do mundo
real — e essa é a razão do passo 3 da seção 4.

**5. A vantagem sobre um LLM genérico e barato não está provada.** Contra o método simples de
hoje, a vantagem é enorme e sólida. Contra quatro LLMs baratos, ela existe sob o critério de
correção desta casa e desaparece sob o critério de um anotador independente. Se o seu caso de
uso tolera 88% a 91% de acerto, um modelo genérico barato pode bastar — e custa um quarto.

**6. A acurácia depende da mistura de assuntos.** Nas quatro distribuições simuladas, a acurácia
esperada vai de 95,0% a 97,2%. Um canal dominado por rastreio não se comporta como um dominado
por cobrança.

---

## 8. Os 15 sistemas do ecossistema: por onde começar

O plano previa avaliar 15 repositórios que usam o Jev. O que foi executado mede **o estado do
código de cada um** — a suíte de testes deles — e não o comportamento com o modelo.

| Estado | Sistemas |
|---|---|
| Suíte passa (5) | Jev Search, Jev Ultrafast, jevcal, Jev Rerank Bench, Every |
| Suíte falha (7) | Jev CLI, Janus, pi-warden, System One Adapter, HEIST//ONE, SemIf/OpenJev, pi-model-router |
| Não rodou (3) | Jev Review, should-ai-kill-us-all, Jeeves |

**Leitura prática:** comece pelos cinco que passam — neles o esforço vai para a aplicação, não
para consertar o repositório. O System One Adapter é o mais caro da lista (108 falhas e 64
erros). Passar na própria suíte não diz que o componente é bom; diz que ele está inteiro.

---

## 9. Placar final: todos os testes, o resultado e a consequência

Doze experimentos, 1.474 chamadas reais, US$ 0,0357. Esta é a lista inteira — o que cada um
perguntou, o que respondeu e o que isso muda na hora de aplicar.

| # | O que foi testado | Resultado | Consequência prática |
|---|---|---|---|
| E1 | Triagem, corpus piloto: Jev contra regra por palavra-chave | **92,5%** contra 60,0% | O método simples de hoje não é páreo. Aplicar vale a pena. |
| E2 | O formato do pedido muda a resposta? (lote, ordem, texto irrelevante junto) | 92,5% a 95,0% nas 8 condições, sem diferença significativa | **Pode mandar de 8 em 8** para baratear, e ruído no texto não atrapalha. |
| E2b | O lugar da mensagem no lote influencia? | Efeito de posição some ao embaralhar (p = 0,40); **3 de 40 casos** mudam conforme os vizinhos | Lote é seguro na média, mas um caso limítrofe pode virar. Não use lote para a classe perigosa. |
| E3 | Uma afirmação se sustenta na evidência anexada? | **95,8%** contra 62,5% | Aplicação recomendada: conferência de citação e de número contra a fonte. |
| E4 | Achar o trecho que muda a resposta | **8 de 8 ressalvas no top-3**; BM25 acha 5 | Aplicação recomendada: achar a exceção escondida em contrato ou norma. |
| E5 | O resultado muda conforme o caminho de acesso? | 40 de 40 casos iguais nos dois; o acesso direto é 2× mais lento e mais caro | Use o caminho mais barato. Trocar de fornecedor de acesso não muda a resposta. |
| E6 | Perguntando 5 vezes a mesma coisa, responde igual? | **1 caso de 40 oscila**; votar em 3 chamadas estabiliza | Para decisão sem volta, pergunte 3 vezes e vá pela maioria. |
| E7 | Triagem em conjunto separado, que nunca guiou nada | **97,5%** contra 32,5% | O resultado do E1 não foi sorte nem ajuste ao teste. |
| E8 | Um anotador independente concorda com o nosso critério? | Concordância 87,4%, kappa 0,84; **29 divergências em 230 casos** | O critério de correção é reprodutível, mas não é unânime — e as divergências são casos reais de ambiguidade. |
| E9 | E se a mistura de assuntos do canal for outra? | Acurácia esperada entre **95,0% e 97,2%** | Estime pelo seu canal: mais rastreio ou mais cobrança muda o número. |
| E10 / E10b | Um LLM genérico e barato faz o mesmo? | Empata no conjunto de teste; o Jev ganha no piloto | Primeira vez que a necessidade do Jev ficou em dúvida. |
| E11 | Desempate: corpus novo, 20 famílias | Jev ganha sob o nosso critério; **empata sob o do anotador independente** | A dúvida não era de amostra pequena. |
| E12 | Replicação: 30 famílias novas, **4** LLMs baratos | Jev **98,9%**, os outros de 84,4% a 91,1% sob o nosso critério; **sem vantagem** sob o critério independente | Triplicar o teste não resolveu: o que decide é quem escreve o gabarito. |
| — | Erro grave (`cancelar` indevido), todos os corpora | **0 em 230 casos**, sob os três critérios; a regra simples comete 10 em 80 | O erro que dói não apareceu — mas a estatística só garante abaixo de 9,5% por família. |
| — | A confiança avisa quando ele erra? | Funcionou em 2 corpora; **falhou no 3º** (erro com confiança 0,98) | Use corte 0,99 e recalibre no seu material. É o cuidado nº 2. |

**As três consequências que resumem tudo:**

1. **Aplicar vale a pena onde o método atual é regra simples ou busca por palavra.** O ganho é
   grande, replicado três vezes e sobrevive a mudança de formato, de ordem e de fornecedor de
   acesso.
2. **O que não se provou é que precise ser o Jev.** Contra LLMs genéricos baratos, a vantagem
   depende de quem escreveu o gabarito — e eles custam um quarto do preço.
3. **Nada disso autoriza automatizar sem rede.** A confiança falha, o modelo oscila, e a classe
   irreversível continua exigindo gente.

---

## 10. O que decidir hoje

| Pergunta | Resposta |
|---|---|
| Onde aplicar primeiro? | Verificação de afirmação contra evidência, e ordenação para achar ressalva. São as duas em que a vantagem sobre o método atual é maior e o risco é menor. |
| E a triagem de atendimento? | Vale, mas com corte alto e revisão da classe perigosa — e ela é a aplicação em que o LLM barato mais se aproxima. |
| Dá para automatizar? | Só acima de 0,99 de confiança, nunca na classe irreversível, e depois de recalibrar no seu material. |
| Quanto custa experimentar? | Praticamente nada: mil decisões por dois centavos. O custo do piloto é o tempo de quem compara os resultados. |
| Qual o maior risco? | Automatizar sobre um critério de correção que ninguém de fora validou. |
| O que destrava tudo? | 200 mensagens reais e duas pessoas anotando os mesmos casos. Não é dinheiro — sobram US$ 4,96 do teto. É acesso a dado real e tempo de gente. |

---

*Cada número deste documento sai dos arquivos em `runs/`, do livro-caixa em
`runs/ledger.sqlite3` e do painel em `lab/`. O relatório final traz o experimento de origem de
cada afirmação.*

**— Helena.**
