# Relatório de execução — programa de avaliação Jev

**Helena Strategos · 18 e 19 de setembro de 2026 · primeira rodada com inferência real**


> **Documento histórico.** Escrito depois do E4 e antes do E5 ao E9, da adjudicação do gabarito
> e de cinco rodadas de revisão independente. Os números aqui — 305 chamadas, acurácias sob o
> gabarito do autor, calibração do piloto — foram superados. O documento vale como registro do
> que se sabia naquele momento, não como conclusão.
>
> **A conclusão está em [`RELATORIO-FINAL-JEV.md`](RELATORIO-FINAL-JEV.md).** Onde os dois
> divergirem, vale o final.

**Status:** etapas 1 a 4 do plano executadas, mais os experimentos E1, E2, E2b, E3 e E4. 305 chamadas
reais, **US$ 0,010950** gastos de um teto de US$ 5,00 de gasto novo. Conciliação com o extrato do
provedor fechada sem divergência inexplicada. Todos os resultados abaixo passaram por **duas rodadas** de
revisão independente de outro modelo (Codex `gpt-6-astra`), que encontraram dezenove defeitos além do que
a execução já havia revelado. A seção 5 lista o que essas revisões derrubaram.

---

## 1. Recomendação

**Uso consultivo do Jev na triagem de mensagens e na relação afirmação/evidência, com corte de confiança
em 0,95 e revisão humana do resto.** Não é recomendação de adoção plena: o gabarito ainda é autoral e
provisório, e nenhum teste mediu o fluxo de trabalho completo.

O que sustenta: em duas tarefas independentes, com comparador determinístico congelado antes das
chamadas, o Jev entregou ganho grande, consistente e barato — e a confiança que ele devolve separa
acerto de erro bem o bastante para desenhar um encaminhamento.

O que impede ir além: 64 casos autorais, um único avaliador, nenhuma medição de tempo humano poupado.

---

## 2. Achado principal

**A confiança do Jev é informativa, e isso vale mais que a acurácia média.** A confiança média nos erros
foi 0,513 contra 0,926 nos acertos; na segunda tarefa, o único erro saiu com confidence 0,36.

Isso muda o desenho operacional: em vez de perguntar "o modelo é bom o suficiente para decidir sozinho?",
a pergunta vira "quanto da fila ele resolve e quanto sobra para a pessoa?". Com corte em 0,95, **28 dos 40
casos são aceitos (70% de cobertura) e nenhum deles está errado**.

**Não observar erro não é taxa de erro zero.** Duas rodadas de revisão independente derrubaram a versão
anterior desta seção, que falava em "360 decisões" e "zero erro". As 360 são 40 casos repetidos nove vezes,
e o modelo se mostrou determinístico para entrada idêntica: o N honesto é 40. Sobre 28 aceitos com zero
erros observados, o limite superior de 95% para a taxa de erro é **10,1% se os casos forem independentes**
— e eles não são. Os 28 aceitos vêm de apenas 9 famílias; respeitando o agrupamento, o limite honesto é
**28,3%**. O sinal de calibração continua valendo; a promessa de perfeição, não, e nem o número bonito.

---

## 3. Evidência

### 3.1 E1 — triagem, 40 casos em 10 famílias

Pré-registro congelado em `planning/preregistro-E1-triagem.md` antes de qualquer chamada. Critério
declarado: ganho só conta como sinal se for de pelo menos +10 pontos percentuais.

| Braço | Acurácia | Macro-F1 | Famílias sem erro | Erros graves de cancelamento |
|---|---:|---:|---:|---:|
| Regra simples congelada | 0,600 | 0,554 | 1/10 | 4 |
| Jev 1.13 | **0,925** | **0,928** | **7/10** | **1** |

Diferença pareada **+32,5 pontos**, mais de três vezes o critério, com **IC 95% de [0,150; 0,500]** por
bootstrap de famílias (20.000 reamostragens de clusters inteiros). O intervalo não contém zero.

O critério que este pré-registro havia congelado era inválido e foi emendado em 2026-09-19: ele pedia que
"o limite inferior do intervalo de Wilson sobre famílias não cruzasse zero", mas Wilson é intervalo de
proporção e nunca é negativo — uma única família perfeita já o satisfaria. O procedimento acima o
substitui. O McNemar por família reportado antes (b=6, c=0, p=0,031) testa a ocorrência de *família
perfeita*, não a diferença de acurácia, e passa a constar como análise posterior. A conclusão sobrevive ao
teste correto; o que muda é a largura do intervalo.

### 3.2 E2 — fatorial 2×2×2, 320 decisões

Mesmos 40 casos, oito condições cruzando lote, ordem das opções e contexto de distração, com ordem de
execução embaralhada por semente 20260918. O ensaio histórico mudava esses três fatores ao mesmo tempo e
ainda rodava individual antes; aqui cada um varia sozinho.

| Fator | Efeito na acurácia | Efeito no custo |
|---|---|---|
| Lote de 8 contra individual | não detectado (p=1,000 nas 4 células) | **−35,9% a −39,9% por decisão** |
| Ordem das opções invertida | não detectado | nenhum |
| Contexto de distração | não detectado | **+11,4% individual, +18,9% em lote** |

36 dos 40 casos acertam nas oito condições e nenhum erra em todas. A economia do lote é real e menor que
os ~47% do dossiê histórico. O denominador é a decisão **solicitada**: todas as 320 voltaram válidas, então
aqui ele coincide com decisão obtida; com falhas ou retries, os números mudariam.

"Não detectado" é o máximo que estes dados permitem. Demonstrar ausência de perda relevante exigiria uma
margem de não inferioridade declarada antes, e isso não foi feito.

### 3.2.1 E2b — desconfundindo posição e caso

No E2 a ordem dos casos dentro do lote era fixa, então "a posição 4 erra mais" e "o caso que cai na posição
4 é difícil" eram a mesma afirmação. O E2b repetiu o lote em cinco permutações (200 observações) e o padrão
**desapareceu**: amplitude observada de 0,12 entre posições, com p=0,403 em teste de permutação que usa o
caso como unidade. O qui-quadrado que eu havia calculado antes tratava as 200 observações como
independentes, o que era errado.

**Achado novo, e este muda operação:** três dos quarenta casos mudam de resposta conforme os **vizinhos** do
lote, embora o modelo seja determinístico para entrada idêntica. O caso `tri-f09-03` oscilou entre
`informacao`, `rastrear` e `trocar` dependendo da companhia. Quem precisa de reprodutibilidade por caso —
auditoria, contestação, revisão — deve usar o modo individual e pagar os 36% a 40% a mais. A atribuição
específica à composição do lote ainda mistura composição e posição; separar as duas exige um desenho
próprio.

### 3.3 E3 — relação afirmação/evidência, 24 casos em 6 famílias contrastivas

Três classes: suportado, contradito, não informado. As famílias atacam exatamente os contrastes que o
plano apontou como perigosos.

| Braço | Acurácia | Macro-F1 | Famílias sem erro | Erro grave de "não decide" |
|---|---:|---:|---:|---:|
| Regra ingênua congelada | 0,625 | 0,652 | 0/6 | 8 |
| Jev 1.13 | **0,958** | **0,960** | **5/6** | **1** |

O ganho está onde importa: agendado não é pago, proposto não é aprovado, citado não é endossado, ausente
não é negativo. A regra errou oito desses; o Jev, um — e com confiança 0,36. Diferença pareada de +0,333,
com IC 95% de [0,250; 0,417] por bootstrap de famílias.

### 3.4 Custo e latência medidos

- **US$ 0,0000222 por decisão** individual; **US$ 0,0000133** em lote de 8.
- Latência p50 de 420 ms e p95 de 603 ms por chamada individual.
- Tarifa conferida na fonte: US$ 0,000000042 por token de entrada, saída não cobrada. O `usage.cost`
  devolvido bate exatamente com a tarifa publicada.

### 3.5 Rodada simples dos 15 sistemas, camada offline

Suítes rodadas no ambiente que cada repositório declara, com as variáveis `OPENAI_*` e `ANTHROPIC_*` da
máquina removidas — elas estavam redirecionando clientes para um roteador local e teriam contaminado tudo.

| Resultado | Sistemas |
|---|---|
| Suíte passa integralmente | S02 Jev Search (80), S05 Ultrafast (31), S06 jevcal (24), S07 Rerank Bench (9), S10 Every (78) |
| Suíte falha | S01 CLI (13 de 208), S03 Janus (não coleta), S04 pi-warden, S08 Adapter (108 falhas, 64 erros), S11 HEIST (1 de 7), S12 OpenJev (4 de 15), S13 pi-model-router |
| Bloqueado | S09 Jev Review e S14 painel de manchetes (sem script de teste), S15 Jeeves (cargo ausente) |

Três achados de engenharia, não de modelo:

1. **S08 e S03 não declaram as próprias dependências de teste.** O Adapter importa `httpx` e `anthropic`
   sem declará-los no grupo dev; o Janus importa `pyyaml` sem declará-lo. Com o suplemento, o Janus passa
   38/38. O Adapter continua falhando: seus cassetes de rede cobrem só um módulo, e 172 testes morrem em
   "Network is disabled".
2. **S12 não roda no Windows:** quatro testes leem arquivo sem declarar encoding e quebram no cp1252.
3. **Instalar não é testar.** S09 e S14 não têm suíte alguma; não recebem nota de qualidade.

### 3.6 E4 — preservação de ressalvas na seleção de fontes (pergunta P2)

Oito consultas, cinco candidatos cada, com relevância graduada e marcação de qual trecho contém a
**ressalva necessária** — aquele que limita a regra geral e sem o qual a resposta final fica errada,
ainda que a regra geral esteja presente.

| Braço | nDCG@5 | Ressalvas no top-3 | Trechos essenciais no top-3 |
|---|---:|---:|---:|
| Ordem de chegada | 0,736 | 4/8 | 7 |
| BM25 | 0,921 | 5/8 | 13 |
| Jev (tipo `score`) | **0,996** | **8/8** | **16 de 16** |

O BM25 acerta a relevância geral e ainda assim perde três ressalvas: ele encontra o trecho que fala do
assunto, não o que limita a regra. Essa é exatamente a falha que o plano apontou como perigosa em
pesquisa jurídica, e é onde o ganho do Jev aparece.

Um erro de desenho foi corrigido **antes** de gastar: eu havia escrito o corpus com os candidatos em ordem
decrescente de relevância, o que dava ao braço "ordem de chegada" um nDCG de 0,99 e um teto impossível de
superar. A ordem de apresentação passou a ser embaralhada por consulta, com semente 20260918.

---

## 4. Mecanismo

A tarefa é de decisão tipada sobre texto curto, com opções fechadas e critérios escritos. É exatamente o
formato em que um classificador especializado tem vantagem estrutural sobre palavra-chave: a regra vê
tokens, o modelo vê a relação entre a ação pedida e o assunto mencionado. Os erros da regra confirmam o
mecanismo — ela confunde o assunto com o pedido em 16 dos 40 casos, e confunde ausência com negação em 8
dos 24 do E3.

O custo é baixo porque a saída é uma escolha, não texto: a tarifa de saída é zero e a entrada é minúscula.
Por isso o lote economiza — ele amortiza as instruções repetidas, não a decisão.

---

## 5. Revisão independente e o que ela derrubou

Todo o material — executor, desenho, corpora e relatório — foi submetido a outro modelo
(Codex `gpt-6-astra`, esforço alto), com instrução de procurar defeito e sem espaço para elogio. A
primeira tentativa foi honesta ao falhar: o sandbox bloqueou a leitura dos arquivos e o revisor
**recusou-se a afirmar que não havia defeito**, em vez de fingir uma revisão. Na segunda, com o código
entregue no próprio prompt, vieram **cinco achados P1**. Verifiquei cada um contra o código: todos
procedem. Todos foram corrigidos, com teste de regressão que reproduz o defeito
(`executor/tests/test_achados_revisao.py`).

| # | Achado | Consequência real | Correção |
|---|---|---|---|
| P1-1 | O teto declarado na reserva não era imposto ao que era enviado; `max_completion_tokens` ausente virava silenciosamente 1 token | Bastaria declarar 1 token para reservar quase nada e enviar 32 mil | O cliente não declara mais teto; reserva usa o contexto publicado, e sem máximo verificável não despacha |
| P1-2 | Divergência do extrato do provedor virava só um evento, sem ocupar o teto | Extrato à frente do ledger autorizaria gasto contra saldo inexistente | Excedente não registrado passa a consumir a carteira |
| P1-3 | A reserva precificava um modelo e a liquidação podia usar outro | Reservar caro e liquidar barato liberaria saldo que não existe | Identidade de preço é gravada na reserva; liquidar com outra é recusado |
| P1-4 | Resposta ausente sumia da acurácia e inflava "família sem erro" | Braço com falhas pareceria melhor do que é, e o pareamento quebrava | Relatório traz cobertura, acurácia condicional e acurácia sobre os casos programados |
| P1-5 | O critério de significância congelado era vacuoso | Wilson de proporção nunca cruza zero: o critério não testava nada | Emenda datada e bootstrap de clusters por família |

O P1-5 é o mais sério, porque atinge a conclusão e não o código. A emenda está em
`planning/preregistro-E1-triagem.md`, e o resultado **sobrevive** ao teste correto: a diferença de +32,5
pontos tem IC 95% de [0,150; 0,500].

### 5.1 Segunda rodada: a correção criou defeitos novos

O protocolo da casa diz que o primeiro round de correções costuma introduzir regressões. Submeti as
correções ao mesmo revisor, com instrução explícita de procurar regressão. Vieram **mais sete P1**.

| # | Achado da segunda rodada | Por que importa |
|---|---|---|
| R2-1 | A conciliação comparava o extrato com o total **comprometido**, que inclui reservas ainda não gastas | Extrato e reserva são grandezas diferentes: com uma reserva pendente grande, divergência real ficava escondida |
| R2-2 | A absorção do excedente lia o saldo **fora** da transação | Duas conexões poderiam absorver o mesmo excedente duas vezes |
| R2-3 | Conciliação e registro histórico podiam duplicar o mesmo gasto | Ordem de importação mudava o total comprometido |
| R2-4 | A liquidação usava a tabela de preços **atual**, não a da reserva | Trocar a tabela por uma mais barata liquidaria a reserva antiga por menos e liberaria saldo |
| R2-5 | `p_bootstrap_bilateral` podia devolver **2,0** | Com todas as diferenças iguais, a conta passava de 1; e nunca foi p-valor calibrado, é massa de cauda |
| R2-6 | O limite de erro tratava 28 casos como 28 ensaios independentes | Eles vêm de 9 famílias; o limite honesto é 28,3%, não 10,1% |
| R2-7 | A cobertura excluía do denominador os casos sem confidence | Mesmo mecanismo do P1-4, em outra métrica |

E um alerta que, ao ser verificado, era pior do que P2: **`CREATE TABLE IF NOT EXISTS` não adiciona coluna
a tabela existente.** O banco de produção, com 305 tentativas, estava sem as colunas de identidade de
preço criadas na primeira rodada — os testes passavam porque usam bancos novos. Havia uma correção que só
funcionava em laboratório. Migração implementada com `ALTER TABLE`, base migrada, identidade das 305
tentativas antigas preenchida pela evidência da reserva.

Todos os sete corrigidos, com regressão em `executor/tests/test_achados_revisao2.py`.

### 5.2 Terceira rodada: a correção da correção

Terceira submissão, agora perguntando por regressões das correções da segunda. Mais **três P1** e quatro
P2, e a raiz de três deles era a mesma decisão minha: eu havia **materializado** o ajuste de conciliação
como uma linha no ledger.

- Um gasto histórico do mesmo provedor ficava fora da soma filtrada, e o extrato o somava de novo.
- Quando a tentativa correspondente era enfim liquidada, o ajuste só encolhia na conciliação *seguinte*;
  no intervalo, a carteira contava o mesmo dinheiro duas vezes e podia negar uma chamada legítima.
- A migração criava as colunas de identidade vazias, e o `settle` passava a rejeitar para sempre qualquer
  tentativa antiga que ainda estivesse pendente — inclusive um timeout que recebesse resposta tardia.

A correção foi estrutural: **o excedente do extrato deixou de ser linha e passou a ser cálculo**. Ele agora
acompanha o estado sozinho, encolhe no instante em que a cobrança vira tentativa registrada, e não colide
com o histórico. Junto, o gasto histórico passou a exigir o provedor, e foi criada uma regularização
auditada de identidade para tentativas herdadas de base antiga.

Dos P2: o `round(..., 4)` estava trazendo de volta o p igual a zero que a correção anterior tinha
eliminado (1/20001 arredonda para 0,0), e o limite de erro por família foi reapresentado pelo que ele de
fato mede — a probabilidade de uma família conter um caso aceito errado — e não como um limite
conservador do risco por caso, que seria outro evento.

Total: **20 defeitos encontrados**, sendo 1 pela execução, 5 na primeira revisão, 7 na segunda e 7 na
terceira. Nenhum foi encontrado lendo o código na primeira escrita.

Dos alertas P2, três mudaram o texto deste relatório: "efeito inexistente" virou "não detectamos efeito";
"zero erro" virou "zero erros observados, com limite superior de 10,1%"; e a divergência entre a rubrica
escrita e o prompt efetivamente enviado passou a constar na emenda em vez de ser apresentada como
equivalência.

Dois alertas continuam **abertos e não corrigidos**, por escolha: o comparador é reconhecidamente simples
e o corpus concentra justamente as dificuldades que ele não trata, e as dez famílias são categorias
autorais de fenômenos, não amostra da rotina. Os dois entram como contra-hipóteses abaixo, porque não se
resolvem com código — só com dados novos.

---

## 6. Contra-hipóteses

### Contra-hipótese 1: o gabarito é meu, e eu escrevi os casos

**Argumento:** eu redigi o corpus e o gabarito. Se minha intuição de rotulagem coincide com o viés do
modelo, a acurácia mede concordância, não correção. Dois dos casos instáveis são ambiguidade da minha
rubrica, não erro do modelo: "Vocês parcelam em quantas vezes?" e "Me manda o código de rastreio".
**Teste observável:** um segundo avaliador humano, cego às saídas, rotula os mesmos 64 casos até
2026-10-15; calcular Cohen kappa e refazer a métrica sobre o gabarito adjudicado.
**Gatilho de reversão:** se o kappa ficar abaixo de 0,75 ou a acurácia do Jev cair abaixo de 0,85 no
gabarito adjudicado, a recomendação volta para "inconclusivo" e o corpus é refeito antes de qualquer
decisão de adoção.

### Contra-hipótese 2: a regra simples foi construída fraca

**Argumento:** eu escrevi o comparador. Um dicionário melhor, com prioridade diferente, poderia fechar boa
parte dos 32 pontos. A regra erra principalmente por confundir assunto com ação — um engenheiro com uma
tarde poderia mitigar isso.
**Teste observável:** pedir a um terceiro que escreva a melhor regra que conseguir, sem ver os resultados
do Jev, e rodá-la no mesmo corpus até 2026-10-15.
**Gatilho de reversão:** se a regra de terceiro passar de 0,85, o ganho do Jev deixa de justificar a
dependência externa na triagem, e o uso fica restrito à tarefa de evidência.

### Contra-hipótese 3: 64 casos não sustentam nada

**Argumento:** o poder é baixo por construção. O intervalo de Wilson sobre as 10 famílias do E1 vai de
0,397 a 0,892 — largo o suficiente para caber quase qualquer verdade. A distribuição é balanceada de
propósito e não reflete prevalência real, então a acurácia observada não prevê desempenho operacional.
**Teste observável:** coletar 280 casos reais desidentificados por tarefa, em janela consecutiva, e medir
no estrato natural até 2026-11-30.
**Gatilho de reversão:** se no estrato natural a acurácia cair abaixo de 0,85 ou a cobertura com erro zero
cair abaixo de 50%, o corte de confiança precisa ser recalibrado antes de qualquer uso.

### Contra-hipótese 4: a repetibilidade mata o valor das repetições

**Argumento:** E1 e a condição base do E2 concordaram em 40 de 40 casos. O modelo é determinístico neste
corpus, então as 360 decisões do pool de calibração são 40 decisões repetidas nove vezes. O intervalo de
confiança do risco-cobertura é bem mais largo do que 360 sugere.
**Teste observável:** já observado. **Consequência aplicada:** o relatório trata o pool como N=40 para
inferência e usa as repetições apenas como verificação de estabilidade.

---

## 7. Calibração de confiança

| Afirmação | Confiança | Por quê |
|---|---:|---|
| O Jev supera a regra simples nestes corpora | **0,95** | Ganho grande em dois desenhos, com IC de bootstrap por família que não contém zero |
| O Jev preserva ressalvas melhor que BM25 neste corpus | **0,80** | 8/8 contra 5/8, mas são só oito consultas autorais |
| A confiança do modelo é informativa | **0,75** | Separação forte, mas o N honesto é 40 e o limite superior de erro acima de 0,95 é 28,3% respeitando as famílias |
| O lote economiza de 35% a 40% sem dano | **0,70** | Economia medida direto; "sem dano" é ausência de evidência, com poder baixo |
| O ganho se mantém em dados reais não balanceados | **0,45** | Nenhum caso real foi testado; é extrapolação |
| O Jev reduz tempo humano no fluxo completo | **0,20** | Nada foi medido sobre fluxo de trabalho |

Confiança não é probabilidade do evento: é o quanto eu apostaria na conclusão dado o que foi medido.

---

## 8. Cenários

**Base (mais provável):** o ganho se confirma em dados reais com alguma erosão, a acurácia cai para a faixa
de 0,85 a 0,92 no estrato natural, o corte de confiança precisa subir, e o uso consultivo se estabiliza
resolvendo metade da fila sem revisão. *Sinal:* queda concentrada em casos de fronteira, não em rotina.

**Otimista:** o desempenho se mantém acima de 0,92 no estrato natural e a calibração aguenta, permitindo
automação real da faixa de alta confiança. *Sinal:* zero erro acima de 0,95 persistir em 280 casos reais.

**Pessimista:** o ganho era das minhas frases, não da tarefa; no texto real, cheio de ruído, abreviação e
gíria regional, a acurácia cai abaixo de 0,80 e a confiança deixa de separar. *Sinal:* erros aparecendo
com confidence alta — é esse o indicador que mata a recomendação, não a acurácia média.

---

## 9. Próximo movimento

1. **Rotular os 64 casos com um segundo avaliador humano cego** — responsável: Igor ou quem ele designar;
   até 2026-10-15; feito quando houver Cohen kappa calculado e gabarito adjudicado gravado.
2. **Coletar 280 casos reais desidentificados de triagem**, em janela consecutiva, sem selecionar os
   difíceis — responsável: Helena com Efesto; até 2026-11-30; feito quando o corpus estiver versionado com
   origem, data e estrato declarados.
3. **Medir o fluxo completo com e sem o componente** (P5), cronometrando minutos humanos por tarefa
   concluída — responsável: Efesto; até 2026-11-30; feito quando houver 20 tarefas pareadas com tempo real
   registrado.
4. **Corrigir a identificação do efeito de posição no lote**, embaralhando a ordem dos casos dentro do
   lote com semente registrada — responsável: Efesto; até 2026-10-10; feito quando posição e caso
   deixarem de ser colineares.
5. **Reduzir o limite da chave no painel do provedor** de US$ 50 para o valor autorizado — responsável:
   Igor, porque exige acesso à conta; até 2026-09-30; feito quando o extrato mostrar o novo limite.
6. **Encomendar uma segunda regra a um terceiro**, desenvolvida em dados separados e congelada antes do
   teste, para saber se o ganho sobrevive a um comparador bem-feito — responsável: Helena com Efesto; até
   2026-10-20; feito quando a regra de terceiro rodar no mesmo corpus sem ter visto as saídas do Jev.
7. **Separar composição do lote de posição no lote**, com desenho em que a vizinhança varia e a posição
   fica fixa — responsável: Efesto; até 2026-10-20; feito quando os três casos instáveis tiverem causa
   atribuída.

---

## 10. O que este relatório não estabelece

Não mede desempenho em dados reais. Não mede tempo humano poupado. Não compara provedores: P6 continua
sem execução, porque não há conta TypeSafe direta nesta máquina. Não julga 14 dos 15 sistemas além da
camada offline — instalar e rodar suíte não é inferência real do componente, e só o S01 teve inferência.

P2 passou a ter resposta preliminar no E4, sobre oito consultas autorais. Isso é um piloto, não um
benchmark de busca.

O controle financeiro e a análise acumularam **vinte** defeitos encontrados durante a própria execução:
um ao rodar (o teto aplicado por experimento) e dezenove em três rodadas de revisão independente, sendo
que cada rodada encontrou defeitos criados pelas correções da rodada anterior.
Todos corrigidos, todos com teste de regressão. O gasto real nunca chegou perto do limite — US$ 0,010950
de US$ 5,00 — mas um controle financeiro que só funciona porque o gasto é pequeno não é um controle
financeiro.

Nenhum dos vinte foi encontrado lendo o código na primeira escrita. Apareceram ao executar de verdade, ou
quando outro modelo olhou com instrução de achar problema. O mais instrutivo: uma das correções da
primeira rodada **só funcionava nos testes**, porque `CREATE TABLE IF NOT EXISTS` não migra tabela
existente e os testes usavam bancos novos. A suíte estava verde e a produção, quebrada.

---

*A parte mais honesta deste relatório é a seção 9. Todo mundo sabe escrever o que mediu; poucos escrevem
o que continuaram sem saber depois de gastar o orçamento. — Helena*
