# Pré-registro — E1 piloto, tarefa de triagem

**Congelado em 2026-09-18, antes de qualquer resultado desta tarefa.** Alterações posteriores só como
emenda datada, com o motivo, nunca substituindo este texto.

## Pergunta

P1 do plano: a decisão é correta na rotina em português? Comparação entre **regra simples** (baseline
determinístico por palavra-chave) e **Jev** (`typesafe/jev-1.13`, transporte OpenRouter
`/api/alpha/decisions`), sobre os mesmos casos e o mesmo gabarito.

## Tarefa

Classificar **a ação que o remetente pede** em uma mensagem de atendimento em português, entre cinco
classes mutuamente exclusivas:

| Classe | Definição operacional |
|---|---|
| `cancelar` | Pede encerrar, cancelar ou desistir de pedido, serviço ou contrato. |
| `rastrear` | Pede informação sobre onde está, quando chega ou status de entrega. |
| `trocar` | Pede troca, devolução, reparo ou substituição de item. |
| `cobranca` | Pede segunda via, contesta valor, pede reembolso, parcelamento ou fala de pagamento. |
| `informacao` | Pede esclarecimento ou dado sem solicitar nenhuma das ações acima. |

Regra de julgamento: vale **a ação pedida**, não o assunto mencionado. "Recebi a cobrança errada e quero
cancelar o pedido" é `cancelar`, não `cobranca`. Quando duas classes forem igualmente defensáveis, o caso
é marcado `ambiguo` e sai da métrica principal, entrando num relato à parte.

## Desenho

- **40 casos**, organizados em **10 famílias** de 4 casos cada. Casos da mesma família compartilham
  contexto e diferem por uma manipulação controlada.
- A família é a unidade de agrupamento: 40 casos **não** são 40 observações independentes. Intervalos
  são calculados sobre 10 famílias, não sobre 40 casos.
- Composição efetiva, contada no arquivo e não estimada: **13 de rotina, 17 de fronteira controlada e
  10 de perturbação** (negação, ação dentro de citação, assunto que não é pedido, duas ações com uma só
  solicitada, ruído e cortesia). A distribuição é deliberadamente carregada em fronteira e perturbação:
  serve para achar falha de rubrica, **não** para estimar desempenho operacional.
- Distribuição de classes: `informacao` 9, `cancelar` 8, `trocar` 8, `cobranca` 8, `rastrear` 7.
- Split: piloto inteiro é `pilot`. **Nenhum caso deste piloto entra no teste final.**
- Semente de sorteio: 20260918.

## Gabarito

Autoral, escrito **antes** de qualquer chamada, com justificativa por caso. Não há segundo avaliador
humano independente nesta máquina, portanto o gabarito é **provisório** pela régua do próprio plano.
Um segundo modelo não seria validação independente e não será usado como tal.

## Comparadores

1. **Regra simples:** dicionário de palavras-chave por classe, com prioridade declarada e desempate pela
   primeira ocorrência. Escrita antes de ver os resultados do Jev e congelada junto com este documento.
2. **Jev:** uma pergunta `choice` por caso, com `criteria` idêntico às definições acima, mesma ordem de
   opções para todos os casos nesta rodada.

## Métrica principal e critério

- **Métrica:** acurácia por caso e macro-F1 por classe, com a diferença pareada Jev − regra.
- **Critério de interesse, congelado:** a diferença pareada favorável ao Jev só é considerada sinal se
  for de pelo menos **+10 pontos percentuais** de acurácia E o limite inferior do intervalo binomial de
  Wilson sobre famílias não cruzar zero.
- Com 10 famílias, o poder é baixo por construção. **Um empate aqui não é equivalência**, é ausência de
  informação. O piloto serve para depurar rubrica, custo e instrumento, não para decidir adoção.

## Erros graves

Erro grave é confundir `cancelar` com qualquer outra classe, porque cancelar dispara ação irreversível
no atendimento. Reportado separadamente da acurácia média.

## O que este piloto não pode concluir

Não pode estabelecer desempenho operacional, porque a distribuição é balanceada de propósito e não
reflete prevalência real. Não pode comparar provedores. Não pode sustentar decisão de adoção.

---

# Emenda 1 — 2026-09-19

**Motivo:** revisão independente por outro modelo (Codex `gpt-6-astra`, esforço alto) apontou que o
critério de significância congelado acima é **inválido**, e a crítica procede.

**O que estava errado.** O critério dizia: "o limite inferior do intervalo binomial de Wilson sobre
famílias não cruzar zero". Wilson é intervalo de uma **proporção**, que vive em [0,1] e nunca é
negativo — uma única família perfeita já produziria limite inferior positivo. O critério era vacuoso:
não testava superioridade nenhuma.

**O que também ficou fora do combinado.** O McNemar por família que foi reportado (b=6, c=0, p=0,031)
testa a diferença na ocorrência de *família perfeita*, não a diferença de acurácia por caso. É análise
posterior legítima, mas não é o procedimento que este documento havia fixado, e passa a ser declarada
como tal.

**Procedimento que substitui o critério, a partir de agora.** Diferença pareada de acurácia por caso,
com intervalo de 95% por **bootstrap de clusters**, reamostrando famílias inteiras (`executor/analise.py`).
O ganho conta como sinal quando o intervalo não contém zero **e** a diferença pontual é de pelo menos
+10 pontos percentuais, que era o limiar original e continua valendo.

**Resultado sob o procedimento corrigido**, calculado sobre os dados já coletados:

| Experimento | Diferença Jev − regra | IC 95% por bootstrap de famílias |
|---|---:|---|
| E1 triagem (10 famílias, 40 casos) | +0,325 | [0,150; 0,500] |
| E3 evidência (6 famílias, 24 casos) | +0,333 | [0,250; 0,417] |

A conclusão de superioridade **sobrevive** ao teste correto. O que muda é o intervalo: mais largo e
mais honesto que o número pontual sugeria.

**Correções documentais no mesmo ato:**

1. O texto dizia que a regra desempata "pela primeira ocorrência". O código
   (`executor/baseline_regra.py`) desempata por **prioridade fixa de classes**, independentemente da
   posição no texto. O código está congelado desde antes das chamadas; o documento é que descrevia
   errado, e passa a descrever o comportamento real.
2. O texto prometia `criteria` "idêntico às definições" da rubrica. Não é literalmente idêntico: a
   rubrica inclui em `cobranca` quem "fala de pagamento", e o prompt não; a rubrica aceita "devolução"
   em `trocar`, e o prompt exige "devolução com substituição". As diferenças são registradas aqui em
   vez de alteradas, porque mexer nelas agora contaminaria o resultado já observado.
3. Os casos `tri-f02-04` (pergunta sobre parcelamento) e `tri-f09-04` (pedido do código de rastreio)
   ficam marcados como **fronteira que exige adjudicação**, não como erro estabelecido do modelo. A
   métrica principal continua reportada com eles incluídos; a análise de sensibilidade sem eles está
   no relatório.
