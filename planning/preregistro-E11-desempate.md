# Pré-registro E11 — o desempate entre o Jev e o LLM econômico

**Registrado em 19 de setembro de 2026, antes de escrever uma única linha do corpus novo e antes
de qualquer chamada a qualquer modelo.**

## Por que este experimento existe

O E10 comparou o Jev contra `meta-llama/llama-3.1-8b-instruct` na partição de confirmação e a
diferença não separou de zero. O E10b, decidido **depois** de ver esse resultado, rodou o mesmo
comparador no piloto e a diferença separou — e separou também nas 20 famílias somadas.

A evidência ficou dividida, e a divisão tem dois defeitos que nenhum dos dois experimentos pode
consertar sozinho:

1. **Poder.** Dez famílias por partição. O intervalo primário encostou em zero; com essa
   amostra, "não separa" diz pouco.
2. **Pós-hoc.** A análise que separa de zero foi escolhida depois de ver a que não separava.
   Ainda que a conta esteja correta — e está —, uma análise escolhida assim não pode ser
   apresentada como se tivesse sido planejada antes.

Este experimento existe para resolver os dois de uma vez: **corpus novo, mais famílias, regra de
decisão congelada antes de existir qualquer dado.**

## Hipótese

**H0:** o Jev e um LLM genérico e barato acertam igualmente esta tarefa.

**H1:** o Jev acerta mais.

Como no E10, **H0 é a hipótese que ameaça a utilidade do Jev**, e é ela que este experimento
tenta preservar.

## Desenho

- **Corpus:** 60 casos novos em **20 famílias** de fenômeno linguístico, 3 casos por família,
  em `data/corpus/triagem-desempate.jsonl`. Nenhum caso reaproveitado do piloto ou da
  confirmação; nenhuma família repetida daqueles dois corpora.
- **Quem escreve:** eu, o que continua sendo o limite central deste estudo e está declarado na
  seção 8 do relatório. O que este corpus resolve é poder e pós-hoc, **não** validade externa.
- **Ordem de construção, congelada aqui:** as 20 famílias são declaradas **neste documento,
  antes** de qualquer caso ser escrito; os 60 casos são escritos a partir delas; o gabarito é
  fixado junto com o caso; só então qualquer modelo é chamado.
- **Braços:** `typesafe/jev-1.13` e `meta-llama/llama-3.1-8b-instruct`, com **as mesmas
  instruções e critérios congelados do E1**, sem exemplos e sem qualquer ajuste de prompt.
- **Ordem de execução:** os dois braços rodam sobre a mesma lista, na mesma ordem. Nenhum dos
  dois é reexecutado.

## As 20 famílias, declaradas antes de escrever os casos

| # | Família | Fenômeno |
|---|---|---|
| D01 | intenção-em-pergunta-retórica | a ação aparece dentro de pergunta retórica, não como pedido |
| D02 | ação-em-citação-de-atendente | o remetente cita o que o atendente disse que faria |
| D03 | ameaça-hipotética | ação prometida como ameaça condicional futura |
| D04 | pedido-em-pós-escrito | a ação real aparece depois de um assunto que não é ação |
| D05 | duas-ações-uma-descartada | o remetente cogita duas e descarta uma explicitamente |
| D06 | ação-por-terceiro-autorizado | alguém pede em nome de outra pessoa |
| D07 | correção-de-pedido-anterior | o remetente desdiz um pedido que fez antes |
| D08 | vocabulário-de-outra-classe | palavras típicas de uma classe, ação de outra |
| D09 | ação-já-em-andamento | o processo já começou e o remetente só relata |
| D10 | pedido-implícito-por-queixa | queixa que constitui pedido sem verbo de pedido |
| D11 | número-e-prazo-como-distração | dados numéricos que puxam para cobrança sem sê-lo |
| D12 | pedido-encadeado | ação B condicionada ao resultado da ação A |
| D13 | negação-dupla | duas negações que resultam em pedido afirmativo |
| D14 | ironia-e-sarcasmo | pedido real embrulhado em ironia |
| D15 | mensagem-truncada-com-pedido-claro | texto cortado, mas com a ação inequívoca |
| D16 | pedido-de-confirmação-de-ação | pergunta se a ação foi feita, não pede que se faça |
| D17 | mistura-de-canais | menciona ter pedido em outro canal e o que quer agora |
| D18 | pedido-adiado-pelo-remetente | pede explicitamente para não agir agora |
| D19 | reformulação-sinônima | a ação nomeada por sinônimo incomum |
| D20 | quantificador-parcial | a ação vale para parte do pedido, não para tudo |

## Métrica primária e regra de decisão, congeladas antes de existir dado

- **Primária:** diferença pareada de acurácia (Jev − comparador) sobre os 60 casos, com
  bootstrap de 20 000 reamostragens **por família**, e IC95 de percentil.
- **Secundária, declarada aqui e não depois:** McNemar exato bilateral sobre as discordâncias; e
  o erro grave (`cancelar` indevido) de cada braço, reportado separadamente como manda o
  pré-registro do E1.

A leitura, decidida agora:

1. **IC95 inteiramente acima de zero** → há evidência de que o Jev supera um LLM econômico nesta
   tarefa. A seção 1 do relatório volta a recomendar o Jev, com os limites da seção 8 intactos.
2. **IC95 contendo zero** → não há evidência de vantagem. A recomendação passa a ser: usar o
   classificador mais barato que passe no critério de erro grave, porque o estudo não mostrou
   que o especializado é necessário.
3. **IC95 inteiramente abaixo de zero** → o comparador barato é melhor, e a recomendação é ele.

Em qualquer dos três casos, **este resultado é o primário e substitui a leitura dividida atual**,
porque é o único dos três conjuntos cuja análise foi decidida antes de existir o dado.

O que **não** acontece em nenhum caso: escolher entre este conjunto e os anteriores depois de
ver o número. Os três vão para o relatório, com os três intervalos.

## Orçamento

Dois braços × 60 casos = 120 chamadas.

- Jev: reserva do pior caso publicado, 32.000 tokens de entrada a US$ 0,042/M =
  US$ 0,001344 por chamada; saída a custo zero. 60 chamadas: **US$ 0,08064**.
- llama-3.1-8b: 131.072 tokens a US$ 0,05/M mais 64 de saída a US$ 0,08/M =
  US$ 0,00655872 por chamada. 60 chamadas: **US$ 0,3935232**.

Pior caso total: **US$ 0,4741632**. Teto do bloco fixado em **US$ 0,60**. Gasto acumulado antes
deste experimento: US$ 0,018876461 de US$ 5,00; mesmo no pior caso integral, o estudo termina
abaixo de **US$ 0,50**.

## O que este experimento continua não podendo concluir

Que o resultado vale para um canal real — o corpus é meu. Que vale para a categoria "LLM barato"
— testa um modelo. Que a rubrica é válida — isso depende de anotadores humanos, e segue aberto.

---

# Nota de construção — 2026-09-19, antes de qualquer chamada

Os 60 casos foram escritos a partir das 20 famílias declaradas acima, nessa ordem. Ao reler o
conjunto contra a **rubrica congelada do E1** — que é a mesma que os dois modelos vão receber —
dois casos tinham gabarito que contrariava a própria rubrica, e foram reescritos **antes de
qualquer chamada**:

- **`dsp-d12-02`** pedia *"se a peça estiver em estoque, manda uma nova"* com gabarito `trocar`.
  A rubrica diz que ação **condicional não é a ação pedida**. O gabarito brigava com a instrução
  que o modelo recebe, e o caso mediria a contradição, não o modelo. Reescrito para pedido
  imperativo, com a condicional recaindo sobre o aviso.
- **`dsp-d09-02`** perguntava quando o motoboy passaria para a coleta, com gabarito `rastrear`.
  O caso ficava entre `rastrear` (status logístico) e `informacao` (prazo de procedimento), e um
  caso que dois gabaritos defendem não mede nada. Reescrito para status de entrega de um pedido
  mantido.

Os dois trazem `revisado_antes_de_executar: true` no corpus. É a mesma disciplina aplicada no E7,
quando `cnf-g05-01` e `cnf-g10-04` foram reescritos antes da primeira chamada: corrigir gabarito
depois de ver a resposta do modelo é fraude; antes, é higiene.

Distribuição das classes nos 60 casos: `cancelar` 14, `informacao` 13, `rastrear` 11,
`cobranca` 11, `trocar` 11. Balanceada de propósito, o que **não** reflete prevalência real —
mesma limitação dos corpora anteriores, tratada no E9.

---

# Nota de incidente — 2026-09-19, primeira execução perdida

A primeira execução do E11 completou **as 120 chamadas** e liquidou **US$ 0,001923295** no
livro-caixa. Em seguida a análise quebrou com `KeyError: 'kind'` — a função `resumo()` do E1
exigia um campo que só existe nos corpora piloto e de evidência, e que este corpus não tem.

**Os dados se perderam inteiros**, porque nada havia sido gravado em disco: o `request_path` que
o `dispatch` registra no livro-caixa é apenas um rótulo, e ninguém escreve aquele arquivo. Cento
e vinte chamadas pagas existiam só na memória do processo.

O que foi corrigido antes de repetir:

1. `kind` passou a ser opcional em `resumo()`.
2. O E11 grava cada caso em `runs/e11-desempate/respostas.jsonl` **assim que a resposta chega**,
   e ganhou `--so-analisar`, que refaz a análise a partir desse bruto sem nenhuma chamada.

**O que eu vi da execução perdida, declarado:** as últimas sete linhas do log do braço barato,
mostrando acertos em `dsp-d18-03`, `dsp-d19-01`, `dsp-d19-02`, `dsp-d19-03`, `dsp-d20-01`,
`dsp-d20-02` e `dsp-d20-03`. Nenhum número agregado, nenhum intervalo, nenhuma acurácia. Não
alterei o corpus, nem um gabarito, nem o prompt entre as duas execuções — o único diff é o
código de persistência e o campo opcional.

A execução que vale é a segunda, e o custo da primeira **permanece no livro-caixa**, como tem de
permanecer: dinheiro gasto não se apaga porque o resultado se perdeu. Total do experimento passa
a incluir as duas.

---

# Emenda 2 — 2026-09-19, antes de rodar o terceiro juiz nos 10 desacordos

**Motivo.** A décima quarta rodada de revisão adversarial fez duas críticas que procedem, e as
duas são sobre este pré-registro.

**A primeira:** a regra congelada aqui produziu a leitura `vantagem-do-jev`, e o relatório
publicou outra coisa. Isso foi feito **em prosa**, sem emenda, e é exatamente o que este
documento existe para impedir. A análise por gabarito — rodar o anotador independente nos 60
casos e recalcular a diferença sob o gabarito dele — **não estava pré-registrada**. Ela foi
decidida depois de ver que o Jev acertara 60 de 60. Está declarada aqui, agora, pelo que é:
análise complementar, pós-hoc, motivada pelo resultado.

**A segunda, e mais séria:** o anotador independente é `qwen2.5:7b-instruct`, e a rubrica deste
estudo diz que vale a ação pedida, não o assunto mencionado. O revisor mostrou que as
divergências dele seguem um padrão — classificar pelo vocabulário presente na mensagem — que é
justamente o modo de falhar da regra congelada que o Jev supera desde o E1. Tratar esse anotador
como se fosse um humano do domínio, e com ele inverter o sinal de um resultado pré-registrado,
pode ser o oposto de rigor. **No E8 esse mesmo conflito foi resolvido por um terceiro juiz cego,
que devolveu 8 dos 9 casos ao gabarito do autor — e o E11 parou antes dessa etapa.**

**O que vai ser feito, declarado antes de qualquer chamada:** os 10 casos em que os dois
anotadores divergem no corpus do desempate vão ao mesmo procedimento do E8b — terceiro juiz de
outro fornecedor, cego a quem escreveu cada leitura, com as leituras em **ordem sorteada** e a
mesma rubrica que os dois receberam.

**A regra de leitura, congelada agora:**

1. Se o terceiro juiz confirmar **o gabarito do autor na maioria** dos 10, o gabarito oficial do
   E11 passa a ser o adjudicado, como já é nos outros dois corpora, e a **leitura primária
   pré-registrada volta a valer**: há evidência de que o Jev supera um LLM econômico neste
   corpus. A conclusão publicada muda, e muda contra mim.
2. Se confirmar **o anotador independente na maioria**, a inversão do sinal se sustenta com um
   juiz a mais, e a conclusão atual fica mais forte, não mais fraca.
3. Se ficar **dividido ou declarar ambiguidade na maioria**, os casos são ambíguos por natureza,
   e a conclusão é sobre a rubrica: ela não separa o que diz separar.

Em qualquer dos três casos, os três números — autor, anotador independente e adjudicado — vão
para o relatório e para o painel, como manda a política desde a décima segunda rodada. O que a
adjudicação decide é **qual é o oficial**, não qual aparece.

**O que não muda:** o corpus, os gabaritos originais, as respostas dos dois modelos. Nada é
reexecutado. O terceiro juiz vê apenas mensagem e duas leituras, sem saber de onde vieram e sem
ver nenhuma resposta de modelo.
