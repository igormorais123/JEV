# Relatório de execução — programa de avaliação Jev

**Helena Strategos · 18 de setembro de 2026 · primeira rodada com inferência real**

**Status:** etapas 1 a 4 do plano executadas. 261 chamadas reais, **US$ 0,007638** gastos de um teto de
US$ 5,00 de gasto novo. Conciliação com o extrato do provedor fechada sem divergência inexplicada.

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

**A confiança do Jev é informativa, e isso vale mais que a acurácia média.** Em 360 decisões do piloto de
triagem, nenhuma das 244 com confidence ≥ 0,95 estava errada, enquanto a confiança média nos erros foi
0,513 contra 0,926 nos acertos. Na segunda tarefa, o único erro saiu com confidence 0,36.

Isso muda o desenho operacional: em vez de perguntar "o modelo é bom o suficiente para decidir sozinho?",
a pergunta vira "quanto da fila ele resolve sem erro e quanto sobra para a pessoa?". Com corte em 0,95, a
resposta neste corpus foi **67,8% da fila com zero erro**.

---

## 3. Evidência

### 3.1 E1 — triagem, 40 casos em 10 famílias

Pré-registro congelado em `planning/preregistro-E1-triagem.md` antes de qualquer chamada. Critério
declarado: ganho só conta como sinal se for de pelo menos +10 pontos percentuais.

| Braço | Acurácia | Macro-F1 | Famílias sem erro | Erros graves de cancelamento |
|---|---:|---:|---:|---:|
| Regra simples congelada | 0,600 | 0,554 | 1/10 | 4 |
| Jev 1.13 | **0,925** | **0,928** | **7/10** | **1** |

Diferença pareada **+32,5 pontos**, mais de três vezes o critério. McNemar na unidade correta, a família:
b=6, c=0, p=0,031. No nível de caso, b=15, c=2, p=0,0024 — reportado, mas **não** é a unidade válida,
porque casos da mesma família não são independentes.

### 3.2 E2 — fatorial 2×2×2, 320 decisões

Mesmos 40 casos, oito condições cruzando lote, ordem das opções e contexto de distração, com ordem de
execução embaralhada por semente 20260918. O ensaio histórico mudava esses três fatores ao mesmo tempo e
ainda rodava individual antes; aqui cada um varia sozinho.

| Fator | Efeito na acurácia | Efeito no custo |
|---|---|---|
| Lote de 8 contra individual | nenhum detectável (p=1,000 nas 4 células) | **−35,9% a −39,9% por decisão** |
| Ordem das opções invertida | nenhum detectável | nenhum |
| Contexto de distração | nenhum detectável | **+11,4% individual, +18,9% em lote** |

36 dos 40 casos acertam nas oito condições e nenhum erra em todas. A economia do lote é real e menor que
os ~47% do dossiê histórico.

### 3.3 E3 — relação afirmação/evidência, 24 casos em 6 famílias contrastivas

Três classes: suportado, contradito, não informado. As famílias atacam exatamente os contrastes que o
plano apontou como perigosos.

| Braço | Acurácia | Macro-F1 | Famílias sem erro | Erro grave de "não decide" |
|---|---:|---:|---:|---:|
| Regra ingênua congelada | 0,625 | 0,652 | 0/6 | 8 |
| Jev 1.13 | **0,958** | **0,960** | **5/6** | **1** |

O ganho está onde importa: agendado não é pago, proposto não é aprovado, citado não é endossado, ausente
não é negativo. A regra errou oito desses; o Jev, um — e com confiança 0,36.

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

## 5. Contra-hipóteses

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

## 6. Calibração de confiança

| Afirmação | Confiança | Por quê |
|---|---:|---|
| O Jev supera a regra simples nestes dois corpora | **0,95** | Ganho grande, dois desenhos, McNemar significativo na unidade agrupada |
| A confiança do modelo é informativa | **0,85** | Separação forte, mas medida sobre 64 casos e com determinismo observado |
| O lote economiza de 35% a 40% sem dano | **0,70** | Economia medida direto; "sem dano" é ausência de evidência, com poder baixo |
| O ganho se mantém em dados reais não balanceados | **0,45** | Nenhum caso real foi testado; é extrapolação |
| O Jev reduz tempo humano no fluxo completo | **0,20** | Nada foi medido sobre fluxo de trabalho |

Confiança não é probabilidade do evento: é o quanto eu apostaria na conclusão dado o que foi medido.

---

## 7. Cenários

**Base (mais provável):** o ganho se confirma em dados reais com alguma erosão, a acurácia cai para a faixa
de 0,85 a 0,92 no estrato natural, o corte de confiança precisa subir, e o uso consultivo se estabiliza
resolvendo metade da fila sem revisão. *Sinal:* queda concentrada em casos de fronteira, não em rotina.

**Otimista:** o desempenho se mantém acima de 0,92 no estrato natural e a calibração aguenta, permitindo
automação real da faixa de alta confiança. *Sinal:* zero erro acima de 0,95 persistir em 280 casos reais.

**Pessimista:** o ganho era das minhas frases, não da tarefa; no texto real, cheio de ruído, abreviação e
gíria regional, a acurácia cai abaixo de 0,80 e a confiança deixa de separar. *Sinal:* erros aparecendo
com confidence alta — é esse o indicador que mata a recomendação, não a acurácia média.

---

## 8. Próximo movimento

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

---

## 9. O que este relatório não estabelece

Não mede desempenho em dados reais. Não mede tempo humano poupado. Não compara provedores (P6 não foi
executado). Não avalia busca nem preservação de ressalvas em ranking (P2 não foi executado). Não julga 10
dos 15 sistemas além da camada offline — instalar e rodar suíte não é inferência real do componente.

O controle financeiro tinha um furo conceitual, encontrado durante a própria execução: o teto de US$ 5
estava sendo aplicado por experimento, e cada experimento novo abria um teto novo. Foi corrigido com uma
carteira global e um teste de regressão que reproduz o furo. O gasto real nunca chegou perto do limite,
mas o controle estava errado, e isso precisa constar.

---

*A parte mais honesta deste relatório é a seção 9. Todo mundo sabe escrever o que mediu; poucos escrevem
o que continuaram sem saber depois de gastar o orçamento. — Helena*
