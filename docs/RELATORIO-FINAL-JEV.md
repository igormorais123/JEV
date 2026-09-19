# Jev 1.13 — relatório final de avaliação

**Autoria:** Dra. Helena Strategos, Cientista-Chefe de Inteligência da INTEIA
**Execução:** 18–19 de setembro de 2026
**Sistema avaliado:** Jev 1.13 (`typesafe/jev-1.13` via OpenRouter e `jev-1.13.0` direto)
**Custo total:** US$ 0,018174462 em 625 chamadas, de um teto autorizado de US$ 5,00
**Código, dados e registros:** este repositório, com pré-registros em `planning/` e relatórios
brutos em `runs/`

---

## 1. Recomendação

**Use o Jev como classificador consultivo com corte de confiança em 0,90 e revisão humana do
que ficar abaixo. Não o use como decisor automático sem revisão.**

A política concreta que os dados sustentam: aceitar automaticamente as decisões com confiança
≥ 0,90 e encaminhar o restante para uma pessoa. Na partição de confirmação — os 40 casos que não
guiaram o desenho, que é a leitura que vale para decidir — essa política aceita **87,5%** sem
nenhum erro observado entre os aceitos; na união dos 80 casos, aceita 80%, também sem erro
observado. Os quatro erros do modelo têm confiança abaixo de 0,90.

**A base é pequena e o número precisa ser lido assim:** são 4 erros em 80 casos. "Nenhum erro
entre os aceitos" descreve o que foi observado, não uma garantia; a seção 6 traz o limite
superior que sobra depois de respeitar o agrupamento por família. Sob os parâmetros da seção 7 —
declarados, nunca cronometrados — a política leva o custo por decisão de US$ 0,400 para
US$ 0,080.

**O que impede a recomendação de ir além disso:** o modelo não é determinístico. O mesmo caso,
sozinho e repetido cinco vezes, pode mudar de resposta. Um sistema que decide sozinho precisa
responder igual à mesma pergunta, e este não responde.

**Confiança: 0,60.** Rebaixada de 0,75 depois da sexta rodada de revisão independente, que
mostrou que o painel havia começado a apresentar duas lacunas conhecidas como se estivessem
fechadas. Alta para a comparação contra os comparadores congelados — é pareada, pré-registrada e
replicou fora do corpus piloto. Baixa para qualquer afirmação operacional: 80 casos construídos
por mim, gabarito de um anotador humano (também eu), e um corte apoiado em 4 erros.

---

## 2. Achado principal

**A confiança que o modelo reporta é informativa, e essa é a descoberta com mais valor
operacional do estudo.**

Não era óbvio. `confidence` é um número que o modelo emite sobre a própria resposta; nada
garante que corresponda a probabilidade de acerto. Mas nos dois corpora, todos os erros
ficaram concentrados abaixo de 0,90, e nenhum caso aceito acima desse corte estava errado.
É isso que torna viável uma política de triagem com revisão seletiva, em vez de revisão total.

A ressalva é grande e vai na seção 8: zero erro em 64 casos aceitos não é taxa de erro zero.
Respeitando o agrupamento por família, o limite superior do erro ainda chega a 25,9%.

---

## 3. Evidência

### 3.1 Comparação contra comparadores congelados

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
- **Sob o gabarito do outro anotador, o Jev faz 0,8875, não 0,95.** Esse número tem de ser dito
  junto com os demais: a acurácia depende de qual gabarito se adota, e é exatamente essa
  fragilidade que o experimento veio expor.
- `cnf-g05-02` é o caso que eu havia declarado contestável **antes** de ver este resultado, na
  emenda do pré-registro do E7. `tri-f02-04` é mais delicado: é o mesmo caso que o E6 mostra
  oscilando entre repetições idênticas. Usar a opinião de um classificador instável para
  impugnar o gabarito seria o inverso de auditoria, e não faço isso aqui — registro que os dois
  juízes divergem de mim e que o caso fica em aberto até adjudicação humana.

**Ressalva que não pode ser omitida:** um modelo de 7B não é anotador humano, e o E8 **não é a
adjudicação de gabarito** que o estudo precisa. Ele recebeu a minha rubrica e reproduziu a minha
rubrica; kappa alto aqui mede reprodutibilidade, não validade do constructo. O padrão das
divergências mostra viés claro — em 6 das 9 ele viu ação onde eu li pedido de informação, que é
precisamente a armadilha que as instruções mandam evitar. E os 71 casos de "consenso" são os
casos em que os dois concordam, ou seja, os fáceis: a acurácia de 0,9718 ali **não é uma medida
melhor, é uma medida sobre um subconjunto mais fácil**, e não corrige nada. **O segundo anotador
humano continua pendente, e nenhum dos 9 casos em disputa foi adjudicado.**

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
**Resultado:** em 2 dos 4 erros, o juiz independente apoiou o Jev. **Confirmada em parte** — e
isso significa que a acurácia real do Jev pode ser mais alta do que a reportada, não mais baixa.

### Contra-hipótese 3: o ganho é do formato, não do modelo
**Argumento:** talvez lote, ordem das opções ou distração expliquem os resultados.
**Teste executado:** E2 fatorial completo, mais E2b para desconfundir posição.
**Resultado:** nenhuma condição se separa (McNemar p = 1,000). **Refutada.**

### Contra-hipótese 4: o resultado depende do provedor
**Teste executado:** E5, dois transportes intercalados.
**Resultado:** 40/40 de concordância. **Refutada.**

### Contra-hipótese 5: a acurácia cai numa distribuição de classes realista
**Argumento:** os corpora são quase balanceados; um canal real não é.
**Teste executado:** E9, reponderação da matriz de confusão sob quatro distribuições.
**Resultado:** acurácia esperada entre 0,943 e 0,969 — varia pouco, porque nenhuma classe é
fraca. **Refutada dentro da suposição de que a dificuldade dentro de cada classe é a mesma do
corpus**, que é uma suposição grande e não testada.

---

## 6. Calibração

Medida na partição de teste (conjunto de confirmação), que é a leitura honesta:

| Corte | Aceitos | Cobertura | Erros observados | Limite superior de erro (por família) |
|---|---|---|---|---|
| 0,90 | 35/40 | 87,5% | 0 | — |
| 0,95 | 34/40 | 85,0% | 0 | 25,9% |
| 0,99 | 28/40 | 70,0% | 0 | 25,9% |

**Zero erro observado não é taxa de erro zero.** Os aceitos vêm de um número pequeno de
famílias, e famílias são a unidade de dependência. O limite por caso (Clopper-Pearson sobre 34
ensaios) daria um número muito menor, e seria enganoso: trataria casos da mesma família como
observações independentes, o que eles não são.

---

## 7. Custo e operação

**Medido:** 625 chamadas, US$ 0,018174462 no total. Custo por decisão individual ~US$ 0,000022.
Latência mediana 396 ms no OpenRouter.

**Declarado, não medido:** 2 minutos por revisão humana, US$ 12,00 por hora. Nenhum cronômetro
foi usado; trocar esses parâmetros muda toda a tabela abaixo.

A tabela abaixo usa a **união dos 80 casos**. A partição de confirmação sozinha dá cobertura
maior no mesmo corte (87,5% contra 80,0%), então a linha do corte 0,90 aqui é a leitura
conservadora, não a otimista.

| Política | Cobertura automática | Erros entre aceitos | Custo por decisão | Economia |
|---|---|---|---|---|
| Revisar tudo | 0% | — | US$ 0,400 | — |
| Corte 0,99 | 66,3% | 0 | US$ 0,135 | 66,2% |
| Corte 0,95 | 77,5% | 0 | US$ 0,090 | 77,5% |
| **Corte 0,90** | **80,0%** | **0** | **US$ 0,080** | **80,0%** |
| Aceitar tudo | 100% | 4 | US$ 0,000022 | 100% |

A linha "aceitar tudo" é o que a automação total custaria e o que ela erraria. A diferença entre
ela e o corte 0,90 é o preço de não errar: US$ 0,08 por decisão.

---

## 8. Limites — o que este estudo não autoriza afirmar

1. **Não é um teste em dados reais.** Os 80 casos de triagem e os 24 de evidência foram
   construídos por mim. Nenhum veio de um canal de atendimento em produção.
2. **Um anotador humano.** O E8 mitigou com um juiz independente, mas um modelo de 7B não
   substitui uma segunda pessoa. Dois dos quatro "erros" do Jev podem ser erro meu.
3. **Amostra pequena.** 10 famílias por corpus. O bootstrap respeita o agrupamento, e por isso
   os intervalos são largos — o que é honesto, não um defeito.
4. **O modelo não é determinístico.** Confirmado com o caso isolado e repetido.
5. **Tempo humano não foi cronometrado.** A tabela da seção 7 é uma conta de sensibilidade, não
   uma medição de fluxo real. Isso era a pergunta P5 do plano e continua aberta.
6. **`confidence` não foi validado como probabilidade.** Foi validado como *ordenador*: separa
   bem o que está certo do que está errado nestes 80 casos. Não é a mesma coisa.
7. **Nenhuma conclusão sobre os outros 14 sistemas do plano.** A rodada simples offline dos 15
   sistemas mostrou 5 suítes passando, 7 falhando e 3 sem como rodar. Isso é estado de
   repositório, não evidência de comportamento.

---

## 9. Controle financeiro e integridade do processo

O controle de gastos foi tratado como código crítico e passou por **sete rodadas de revisão
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

Estado final: **625 tentativas, nenhuma reserva pendente sem liquidação, US$ 0,018174462 de
US$ 5,00, 102 testes automatizados passando.** A chave da API nunca foi versionada, impressa em
log ou copiada para documentação.

---

## 10. Próximo movimento

1. **Coletar 200 mensagens reais de um canal de atendimento**, com a distribuição de classes que
   o canal tem — responsável: Igor; critério: corpus anonimizado disponível em `data/corpus/`.
2. **Anotar com dois humanos independentes** e medir kappa entre eles antes de olhar o modelo —
   critério: kappa humano-humano ≥ 0,80; abaixo disso, o problema é a definição das classes,
   não o modelo.
3. **Rodar a política do corte 0,90 em sombra** sobre esse corpus real, sem efeito em produção,
   medindo cobertura e erro entre aceitos — critério: erro entre aceitos ≤ 1% com cobertura
   ≥ 70%.
4. **Cronometrar o fluxo humano** durante a sombra, para fechar a pergunta P5 com dado medido em
   vez de parâmetro declarado.
5. **Só então** decidir se a política sobe para produção, e com qual corte.

Os itens 1 e 2 dependem de gente, não de orçamento. Restam US$ 4,98 do teto autorizado, o que
cobre com folga toda a fase de sombra.

---

*O estudo que eu queria ter feito é o que começa no item 1. O que está aqui é o que dá para
saber sem dados reais — e o principal valor dele é ter descoberto, antes de gastar, exatamente
onde o modelo quebra: no mesmo caso, perguntado duas vezes.*

**— Helena.** Café preto, sem açúcar.
