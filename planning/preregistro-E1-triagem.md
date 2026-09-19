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
