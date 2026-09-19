# Pré-registro E12 — a replicação do desempate com mais famílias e mais comparadores

**Registrado em 19 de setembro de 2026, antes de escrever uma única linha do corpus novo, antes
de qualquer chamada a qualquer modelo e antes de qualquer resultado ser observado.**

## Por que este experimento existe

É o item 1 da seção 10 do relatório final, escrito quando o estudo fechou: *repetir o E10 em
amostra maior, com pelo menos 30 famílias, e com dois ou três LLMs econômicos em vez de um.*

O E11 respondeu à pergunta com 20 famílias e **um** comparador, e a resposta se partiu em duas:
sob o meu gabarito e sob o gabarito oficial (adjudicado por terceiro juiz cego) o Jev separa de
zero; sob o gabarito do anotador independente, não separa. Duas fragilidades sobraram, e são
elas que este experimento ataca:

1. **Um comparador só.** `meta-llama/llama-3.1-8b-instruct` é um modelo de 8B de um fornecedor
   só. Vencer um modelo não é vencer a classe "LLM genérico e barato". Se o Jev perde a
   vantagem contra qualquer comparador barato razoável, a recomendação de adotá-lo cai.
2. **Vinte famílias.** O IC95 do E11 sob o gabarito do anotador chegou a [-0,10; 0,033]: um
   intervalo que contém zero e é largo o bastante para não dizer quase nada.

## Hipótese

**H0:** o Jev e um LLM genérico e barato acertam igualmente esta tarefa.

**H1:** o Jev acerta mais que **todos** os comparadores econômicos testados.

Como no E10 e no E11, **H0 é a hipótese que ameaça a utilidade do Jev**, e é ela que este
experimento tenta preservar. A regra de leitura abaixo é deliberadamente hostil ao Jev: basta um
comparador barato empatar com ele para que a conclusão não seja "vantagem".

## Desenho

- **Corpus:** 90 casos novos em **30 famílias** de fenômeno linguístico, 3 casos por família, em
  `data/corpus/triagem-replicacao.jsonl`. Nenhum caso reaproveitado do piloto, da confirmação ou
  do desempate; nenhuma família repetida daqueles três corpora.
- **Quem escreve:** eu. Continua sendo o limite central do estudo, declarado na seção 8 do
  relatório final. O que este corpus resolve é **poder** e **generalidade do comparador**, não
  validade externa. Nenhum corpus que eu escreva resolve validade externa.
- **Ordem de construção, congelada aqui:** as 30 famílias são declaradas **neste documento,
  antes** de qualquer caso ser escrito; os 90 casos são escritos a partir delas; o gabarito é
  fixado junto com o caso; só então qualquer modelo é chamado. Este arquivo é commitado antes de
  o corpus existir, e o histórico do Git é a prova da ordem.
- **Braços:** `typesafe/jev-1.13` contra **quatro** comparadores econômicos, todos com **as
  mesmas instruções e critérios congelados do E1**, sem exemplos e sem qualquer ajuste de prompt:

  | Braço | Modelo | Fornecedor | Por que está aqui |
  |---|---|---|---|
  | C1 | `meta-llama/llama-3.1-8b-instruct` | Meta | âncora: é o comparador do E10 e do E11, e sem ele não dá para ligar este resultado àqueles |
  | C2 | `mistralai/mistral-nemo` | Mistral | o mais barato dos quatro; outra família de pesos |
  | C3 | `google/gemma-3-12b-it` | Google | outro fornecedor, outro tamanho |
  | C4 | `openai/gpt-oss-20b` | OpenAI (pesos abertos) | o maior dos quatro, ainda dentro da faixa econômica |

- **Critério de entrada de um comparador:** preço publicado na API do provedor, `response_format`
  entre os parâmetros suportados e limite de saída declarável. Os quatro satisfazem os três, e os
  preços vão para `executor/prices.json` **antes** da primeira chamada.
- **Teto de saída:** 64 tokens por chamada em todos os comparadores, como no E10, o que torna a
  reserva financeira verificável.
- **Ordem de execução:** todos os braços rodam sobre a mesma lista, na mesma ordem. Nenhum braço
  é reexecutado. Resposta malformada é **erro**, nunca descarte — vale para o Jev e para os
  quatro comparadores igualmente.

## As 30 famílias, declaradas antes de escrever os casos

| # | Família | Fenômeno |
|---|---|---|
| P01 | pedido-por-eufemismo | a ação é pedida sem o verbo dela, por rodeio |
| P02 | condicional-ja-satisfeita | a condição é declarada e o próprio texto diz que ela já ocorreu |
| P03 | acao-em-lista-numerada | vários itens numerados, só um contém pedido de ação |
| P04 | mensagem-encaminhada | corpo encaminhado de terceiro, com o pedido do remetente no topo |
| P05 | pergunta-sobre-procedimento | pergunta como se faz a ação, sem pedir que a façam |
| P06 | pedido-retirado-na-mesma-frase | o remetente pede e desdiz dentro da mesma frase |
| P07 | duas-classes-no-mesmo-verbo | um verbo só que cabe em duas classes, resolvido pelo complemento |
| P08 | prazo-como-assunto | o prazo é o tema da mensagem, não o que se pede |
| P09 | acao-atribuida-ao-sistema | o sistema teria agido sozinho; o remetente relata |
| P10 | pedido-de-terceiro-recusado | alguém quer a ação e o remetente diz que não quer |
| P11 | negacao-com-excecao | nega a ação em geral e a pede para um item específico |
| P12 | comparacao-entre-opcoes | pede que expliquem a diferença entre duas ações possíveis |
| P13 | anexo-mencionado | cita um anexo; o pedido está no texto, não no anexo |
| P14 | saudacao-longa-e-pedido-curto | muita cortesia e uma oração final que carrega o pedido |
| P15 | erro-de-digitacao-no-verbo-chave | o verbo que decide a classe vem escrito errado |
| P16 | pedido-repetido-de-atendimento-anterior | o remetente reitera um pedido que já fez antes |
| P17 | acao-em-hipotese-de-terceiro | terceiro pode vir a agir; nada é pedido |
| P18 | valor-cobrado-a-mais | contestação de valor, que não é o mesmo que pedir segunda via |
| P19 | garantia-vencida | pede reparo declarando que a garantia acabou |
| P20 | endereco-errado-na-entrega | endereço errado, que pode virar rastreio, troca ou informação |
| P21 | cancelamento-parcial | cancela um item e mantém o resto do pedido |
| P22 | duplicidade-de-cobranca | a mesma compra cobrada duas vezes |
| P23 | urgencia-sem-verbo-de-acao | a urgência é o sinal; o pedido não tem verbo próprio |
| P24 | mudanca-de-assunto-no-meio | começa num assunto e o pedido real aparece no outro |
| P25 | remetente-em-terceira-pessoa | o remetente fala de si na terceira pessoa |
| P26 | citacao-de-politica-da-empresa | cita a política da empresa e pede algo à luz dela |
| P27 | perguntas-encadeadas | várias perguntas seguidas, com uma só ação pedida |
| P28 | canal-errado | diz ter pedido por outro canal e refaz, ou não, o pedido aqui |
| P29 | pedido-de-nota-fiscal | documento fiscal, que é cobrança e não informação |
| P30 | licenca-de-cortesia | pergunta se pode pedir e, na sequência, pede |

As classes são as cinco congeladas no E1: `cancelar`, `rastrear`, `trocar`, `cobranca`,
`informacao`. Cada família recebe três casos com gabaritos escolhidos para não deixar nenhuma
família com uma classe só.

## Regra de decisão, congelada antes de existir qualquer dado

**Medida primária:** diferença pareada de acurácia entre o Jev e **cada** comparador, com IC95
por bootstrap de 20.000 repetições reamostrando **famílias inteiras** (`bootstrap_cluster`), como
no E1, no E10 e no E11.

**Leitura, aplicada sobre o gabarito oficial** (o do autor com os casos em disputa substituídos
pela adjudicação cega do terceiro juiz):

- `vantagem-do-jev` — os IC95 de **todos os quatro** comparadores estão inteiramente acima de
  zero. Só então há evidência de que o Jev supera a classe "LLM genérico e barato".
- `vantagem-do-comparador` — o IC95 de **algum** comparador está inteiramente abaixo de zero.
- `sem-evidencia-de-vantagem` — qualquer outro caso, incluindo o caso em que três comparadores
  separam e um não. A recomendação passa a ser o classificador mais barato que passe no critério
  de erro grave.

Exigir que **todos** separem é um teste de interseção-união: ele é conservador por construção e
não precisa de correção de multiplicidade, porque a multiplicidade aqui trabalha contra a
conclusão favorável ao Jev, não a favor dela.

**Teste de robustez ao gabarito, também congelado aqui:** a mesma leitura é repetida sob os três
gabaritos — o do autor, o oficial e o do anotador independente. A conclusão só é reportada como
`vantagem-do-jev` se ela sobreviver aos três. Se os gabaritos discordarem, o resultado reportado
é `depende-do-gabarito`, e é assim que ele vai para o painel e para o relatório. Esta cláusula
existe porque foi exatamente aqui que o E11 quase publicou uma conclusão que o gabarito seguinte
desmentia.

**Medida secundária, pré-registrada e reportada separadamente da acurácia:** erro grave, nas duas
direções — `falso-cancelar` (o braço diz `cancelar` e o gabarito não é `cancelar`) e
`cancelar-perdido` (o gabarito é `cancelar` e o braço não diz). Reportado por braço, com limite
superior de Clopper-Pearson, porque não observar erro não é ter erro zero.

**Medida terciária:** custo observado por 1.000 classificações em cada braço, tirado do
livro-caixa e não de estimativa. É o número que responde "qual o mais barato que passa".

**McNemar exato bilateral** entre o Jev e cada comparador, como medida de discordância pareada,
reportado junto e sem substituir o intervalo.

## O que este experimento não decide

- **Validade externa.** O corpus continua sendo meu. 90 casos escritos por quem conhece o modelo
  avaliado não viram 90 mensagens reais de um canal de atendimento.
- **Adoção.** Mesmo com `vantagem-do-jev` nos três gabaritos, os itens 2 a 6 da seção 10 do
  relatório final continuam de pé, e o corte de produção continua dependendo de dado real.
- **Determinismo.** O E6 mostrou que o Jev muda de resposta no mesmo caso perguntado duas vezes.
  Este experimento roda cada braço uma vez, como os anteriores, e herda esse limite.

## Orçamento

Teto do bloco: **US$ 0,80**, dentro dos US$ 4,98 que restam do teto de US$ 5,00 autorizado em
18/09/2026. A reserva é atômica e feita antes de cada chamada, pelo pior caso publicado do
modelo; o custo observado esperado é de ordem de centésimos de centavo. São 90 casos × 5 braços
= **450 chamadas**.

Se o teto do bloco for atingido, a execução para e o experimento é reportado incompleto, com os
casos que faltaram nomeados. Nenhum braço é excluído da análise por ter custado mais.

---

## Emenda 1 — falha de transporte não é resposta errada

**Escrita em 19 de setembro de 2026, durante a execução, com o braço `c3` ainda rodando e antes
de qualquer análise do resultado dele.**

O corpo do pré-registro diz que "resposta malformada é erro, nunca descarte", e essa cláusula
continua valendo integralmente. Durante a execução apareceu um caso que ela não cobre: o
provedor devolveu **HTTP 429** (limite de taxa) em parte das chamadas do `c3`. Isso não é uma
resposta malformada do modelo — é uma chamada que o modelo nunca chegou a responder. Contá-la
como erro de classificação atribuiria ao comparador uma falha que é do transporte, e produziria
uma vantagem do Jev que não foi medida em lugar nenhum.

**Regra, congelada aqui antes de olhar o resultado:**

1. Uma tentativa que termine em **erro de transporte** — HTTP 429, HTTP 5xx ou timeout — é
   repetida, com espaçamento entre chamadas, até **três** tentativas por caso.
2. Uma tentativa que termine em **resposta malformada** (JSON inválido, classe fora do
   contrato) **não** é repetida: ela é erro do comparador, como sempre foi.
3. Se após as três tentativas o caso continuar sem resposta, ele entra na análise como ausência
   e **conta como erro** daquele braço, e o relatório publica quantos casos ficaram assim, por
   braço.
4. O número de repetições e o custo delas entram no livro-caixa como qualquer outra chamada.
   Nenhuma tentativa é apagada.

Esta emenda vale igualmente para os cinco braços, e não só para aquele em que o problema
apareceu.

## Emenda 2 — cobertura mínima de um braço

**Escrita em 19 de setembro de 2026, com o braço `c3` ainda em execução, antes da repescagem da
Emenda 1 e antes de calcular qualquer acurácia dele.**

A Emenda 1 resolve o caso em que algumas chamadas morrem no transporte. Ela não resolve o caso
em que o provedor limita tanto um modelo que o braço inteiro fica sem dado: no `c3` quase metade
das chamadas voltou 429, e três repescagens podem não bastar.

Um braço assim não mede o modelo, mede a fila do provedor. Mantê-lo na leitura primária
atribuiria ao comparador uma derrota de infraestrutura; tirá-lo depois de ver a acurácia dele
seria escolher o resultado. Então o critério vai escrito antes:

1. **Cobertura** de um braço é a proporção de casos com resposta válida ao fim da repescagem.
2. Braço com cobertura **≥ 90%** entra na leitura primária normalmente; os casos sem resposta
   contam como erro dele, conforme a Emenda 1.
3. Braço com cobertura **< 90%** é reportado como **incompleto por limite de taxa do provedor**.
   Ele sai da leitura primária — que passa a exigir separação contra todos os comparadores
   completos — e permanece no relatório com a acurácia que teve, a cobertura e o motivo, para
   que ninguém precise acreditar em mim sobre o que ele teria feito.
4. Um braço incompleto **nunca** é substituído por outro modelo escolhido depois. A lista de
   comparadores está congelada no corpo do pré-registro.
5. O relatório e o painel dizem quantos braços entraram na leitura e quantos ficaram de fora.

Este critério vale para os quatro comparadores igualmente, e valeria contra o Jev se fosse o
braço dele a falhar.
