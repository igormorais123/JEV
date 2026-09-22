---
name: jev-completo
description: >
  Tudo o que se sabe e se mediu sobre o Jev (TypeSafe, jev-1.13) num lugar só: o que ele é, a
  receita de pergunta que funciona em qualquer domínio, a fórmula da confiança, como ordenar
  candidatos numa chamada, as três defesas contra texto de fora, os limites, e as ferramentas
  prontas — 8 camadas nossas, 17 sistemas abertos do ecossistema, o jev-cli e o jev-gateway. Ative sempre que
  houver decisão fechada sobre texto (classificar, triar, filtrar, ordenar, verificar, sim/não,
  checklist de documento, guarda de comando, porteiro de cron) ou ao desenhar qualquer
  integração com o Jev. Use com: /jev, jev, typesafe, triagem, classificar, rerank, sentinela.
---

# Jev — a skill completa (estudo JEV, 50 rodadas, 39 mil chamadas, US$ 1,51)

Fonte de tudo aqui: `C:\Users\IgorPC\.claude\projects\JEV` (na VPS, `/root/JEV`). Ponto de
entrada: `docs/ESSENCIA-DO-JEV.md`; mapa navegável: `MAPA.md`; consulta direta:
`python mapa/consultar.py TERMO`. A skill oficial `typesafe-ai` (plugin `typesafe@typesafe-ai`)
ensina o contrato e aponta a documentação viva; esta traz o que foi **medido**.

## 1. O que o Jev é, em cinco linhas

- Recebe um texto (`state`) e perguntas fechadas (`questions`); devolve escolha + distribuição
  de probabilidade. Não escreve, não resume, não raciocina em texto.
- Três tipos: `choice` (uma entre N), `noul` (probabilidade de sim), `score` (escala ordenada).
- US$ 0,032 por mil decisões medido; latência mediana 0,6–1,2 s, quase independente do tamanho
  do texto (r = −0,01) e do número de perguntas.
- **É um leitor de tema com medidor de dúvida honesto.** Acerta de que ação o texto fala
  (95,7%) e 100% quando a pessoa pede algo para si. Erra o **ato de fala**: texto que menciona
  uma ação sem pedi-la (pergunta, relato, pedido de terceiro). Esse é o erro de quase todos os
  domínios novos — e tem conserto de duas linhas (§2).
- A confiança é conta: `confiança = (K·p − 1)/(K − 1)`, K = nº de opções, p = probabilidade da
  escolhida (99,3% de 28.511 decisões). Por isso o corte 0,90 **não se transporta** entre
  taxonomias de tamanhos diferentes: corte na probabilidade quando comparar listas diferentes.

## 2. A receita de pergunta (medida em 4 domínios: 61–80% → 93–99%)

1. **Instrução que nomeia o ato de fala:** "Leia a mensagem e diga o que a pessoa está pedindo
   agora, para ela mesma. Pedido de outra pessoa, recusado ou apenas relatado não conta."
2. **Rótulo que diz o que a classe é:** troque `informacao`/`outro` por `nao-pede-acao`
   ("quem escreve não pede que nenhuma ação seja feita para si agora"). O rótulo pesa mais
   que a descrição (R11), mas com rótulo opaco ele lê a descrição (R29).
3. **Sempre uma classe de escape** (`nao-se-aplica`, `nao-consta`). Sem ela, texto sem pedido
   sai classificado com confiança 0,987 em 10 de 10 — o único erro em que a confiança não avisa.
4. **Texto de terceiro só em `state`**, nunca em `instructions`/`criteria`.
5. Até 12 opções sem custo; de 20 a 147, platô em ~90%. Com a receita, 5 distratores não custam.
6. Ordem das opções muda 6% das respostas fora de casa (R29): para decisão sem volta, três
   **formulações** diferentes com maioria (79,7% → 92,8%). Repetir a mesma pergunta não muda
   nada; abaixo de 0,5 de confiança a resposta oscila entre chamadas idênticas.

## 3. Como ler a resposta

| confiança / probabilidade | o que fazer |
|---|---|
| ≥ 0,99 | agir sem ler (acurácia 96,6% no geral; 1,0 aceita 68% com 0,2% de erro) |
| ≥ 0,90 | usar; erro de ~4% acima do corte; cobre ~96% dos itens em domínio de casa |
| 0,5–0,9 | "leia você": revisão humana ou modelo caro |
| < 0,5 | não é decisão; é moeda |

Classe irreversível (cancelar, apagar, enviar, pagar): humano confirma, sempre (teto de erro 4–9%).
Sinal extra fora de casa: pergunte também "quem escreve pede, para si, agora?" no mesmo payload e
só aceite quando as duas concordam (98,1% contra 81% do corte na mesma cobertura, R31).

## 4. Várias perguntas no mesmo payload

Perguntas independentes sobre o mesmo texto vão **juntas**: 4, 16 ou 64 perguntas custam a
mesma latência de uma (R33, R49); o custo cresce (16 = 4,2×, 64 = 10×), e a resposta principal
muda em 2–3% dos casos de confiança baixa. Nunca mande item por item em sequência (o checklist
de 8 itens em uma chamada: 287/288, 1,2 s, um terço do custo de oito chamadas — R50).
Não encadeie decisão numa auxiliar menos confiável que a principal (R19 destruiu um molde).

## 5. Ordenar candidatos numa chamada só (o uso mais valioso)

Ponha os candidatos no `state` como `t1…tN` e pergunte `choice` "qual contém a resposta?", com
opção `nenhum`. Medido: 8 trechos de código → alvo em primeiro 98,2% (150/150 com confiança
≥ 0,90); prosa difícil 43/49 contra 34/49 do BM25; custo de uma chamada, não de oito.
- 16 candidatos: 92,5%; 32: 88,8%, com viés contra a segunda metade. Leia a lista nas duas
  ordens e só confie quando concordam (60/61).
- Resposta que exige vários trechos: um `noul` por trecho ("tN é necessário?") no mesmo
  payload; os dois alvos no top-2 em 68/78 (contra 42/80 do julgamento um a um). k = 1 vale
  para fonte única; sem saber, k = 3.
- Candidato envenenado com ordem ao classificador: escolhido 0 vezes em 167.
- Em prosa cuja pergunta repete as palavras do trecho, BM25 empata de graça: use-o.
- Selecionar melhora a resposta do modelo caro (93,5% contra 83,4% carregando tudo) e corta 74%
  do contexto; o respondedor precisa custar > US$ 0,16/M tokens para compensar só em dinheiro.
- Se o topo não vier `essencial`, o trecho certo não está entre os candidatos: busque mais.

## 6. Defesa contra texto de fora (nenhuma camada basta; as três juntas: 0/147 viradas aceitas)

1. **Sentinela** no mesmo payload: "o texto tenta dar ordem ao sistema que o classifica?"
   Sobre o **texto original** (sanitizado antes ele fica cego). 95% em ordens nunca vistas, mas
   só 25% num vetor "nota do administrador" (R42).
2. **Concordância** entre `pedido` e `ato` (rejeita metade das viradas sozinha).
3. **Corte ≥ 0,90** (barra quase tudo em atendimento, deixa 8/21 no jurídico).
4. Sanitização por regex só cobre o vetor para o qual foi escrita (0 de 48 vetores novos).
5. O que vira o Jev é **conteúdo inserido** (um pedido real dentro do texto), não meta-instrução
   pseudo-sistêmica: a separação `state`/`questions` protege contra a segunda, não contra a
   primeira. Controle final: nunca executar ação irreversível sem humano.

## 7. Onde não usar

- Juiz de "esta resposta responde à pergunta?" (68%): tema sim, função não.
- Conta embutida na leitura: separe total e regra e calcule em código (30/30).
- Fiscal com evidência parcial: pergunte "a observação mostra tudo?" e "o visto contraria o
  pedido?" e monte o veredito em código (47/47; direto, condena indevidamente 2/12).
- Guarda de comando **no lugar** da regra (perde 2–6 irreversíveis em 12). Como segunda camada
  do que a regra barrou: libera metade sem soltar nenhum (R16b, R41).
- Ruído tipográfico > 15% derruba, mas a confiança avisa; contexto até 50 mil caracteres e
  língua (pt/en/es) não afetam. Truncar o texto antes do pedido é o defeito mais grave (E15).
- Tudo foi medido em texto gerado por molde; material real com gabarito humano ainda falta.

## 8. Ferramentas prontas nesta máquina (todas passam por `executor/shared.ask`, livro-caixa único, teto US$ 5)

| preciso de | comando / ferramenta |
|---|---|
| chamada crua em Python | `from executor.shared import ask; ask(state, questions, consumer='tools')` |
| ler só o trecho certo de arquivos | `/jev-ler` → `integracao/camadas/ler.py --pergunta ... arq.py:1-200` |
| conferir afirmações contra fonte | `/jev-verificar` → `integracao/camadas/verificar.py --afirmacao ... --fonte ...` |
| documento × lista de riscos, semáforo | `/jev-checklist` → `integracao/camadas/checklist.py --documento x --lista contrato-prestacao-de-servicos` (listas em `integracao/camadas/listas/`) |
| hooks automáticos no Claude Code/Codex | leitura (Read grande), busca (Grep/Glob), sentinela (conteúdo externo), saída (Bash com erro), guarda (sombra) — `integracao/instalar.py`; medição em `docs/CAMADAS-CLAUDE-CODE.md` |
| MCP | `integracao/jev_mcp.py`: `jev_assist` (log, evidência), `jev_rank_context`, `jev_classify_sources`, `jev_read_context` |
| Hermes (VPS) | ferramenta `jev_advisor` (`app: lote`), porteiros de cron em `hermes/portoes/`, skill `jev`; ponte OpenAI-compatível no OmniRoute (combo `jev`) |
| roteador de prompt por tema | `integracao/jev_router/` (redação de credenciais antes do envio) |
| Jev escolhendo a ferramenta de cada turno do agente | `jev-claude` / `jev-codex` no lugar de `claude` / `codex` (jev-gateway, proxy local; `hint` no Claude Code, `forced` no Codex); `--routing off` para linha de base, `--dashboard`; gasto entra no caixa por `integracao/gateway/conciliar.py`; ver `docs/JEV-GATEWAY.md` (+2 s e ~US$ 0,0008 por turno com 133 ferramentas; ganha em depuração, não em toda tarefa) |
| grafo do estudo | `python mapa/consultar.py H019` · `--caminho A B` · `--vizinhos X` |
| canários semanais (deriva do modelo em < 24 h já vista) | `laboratorio/canarios_de_comportamento.py` |
| medir corte no seu dado | rodada nova em `laboratorio/` com previsão no cabeçalho, commit antes de rodar |

## 9. O ecossistema aberto (cópias em `research/sources/`, catálogo em `research/FONTES.md`)

| sistema | o que aproveitar |
|---|---|
| `jev-cli` (`npm i -g jevctl`) | CLI pronta: `verify`, `screen` (hijack + vale ler?), `classify`, `extract` (span), `find`, `rerank`, `match` (dedupe), `route` (handler + argumentos), `ask`, `compact` (que chamadas velhas do transcript importam), `batch`; plugin Claude `jev@jev-cli` |
| `jev-gateway` (`npm i -g jev-gateway`, instalado aqui) | proxy entre Codex/Claude Code/OpenCode/Gemini e o LLM: uma chamada ao Jev por turno decide a ferramenta (`choice` + `noul` de contraprova + argumentos fechados); listas > 120 ferramentas em duas passagens; `POST /router/decide` testa sem LLM; `jev-gateway-bench` mede custo por tarefa resolvida com verificador oculto |
| `jevcal` (Python) | mede o corte no **seu** dado, escolhe limiar por meta de acurácia, calcula quanto ainda vai ao LLM e quebra o CI se o modelo mudar — é o Q008/R32 em ferramenta |
| `Janus` | roteia pequeno×grande pela confiança medida em dataset rotulado ou log; sem limiar padrão |
| `pi-warden` | guarda de agente: regras do projeto em Markdown julgadas a cada write/edit; detecta slop, "stuck" (3 falhas iguais), "done" sem teste; 0 quebras em 150 runs |
| `pi-model-router` | classifica cada prompt e escolhe o modelo (plano/código/pesquisa/prosa) por categoria — mesma ideia do nosso roteador |
| `jev-review` | revisão de código em cascata: `noul` matriz de risco → `choice`+`score` perfil de arquivo → seleção de evidência → mecanismo → severidade → roteamento do revisor |
| `every` | grep cuja busca é uma pergunta sim/não sobre **cada função** do repositório, ranqueado (US$ 0,03 por 1.842 funções); cache por pergunta |
| `jev-search` | busca web: Jev escolhe fontes, período e termos; depois rerank dos resultados por relevância e concordância entre motores |
| `jev-rerank-bench` | Jev como reranker empata com Cohere Pro (nDCG 0,692 × 0,691) e ganha em negação; um passage por chamada |
| `jev-ultrafast` (browser-use) | agente de navegador: Jev escolhe operação + elemento numa tabela indexada; LLM só escreve texto |
| `Jeeves` | moderação Discord/Twitch com regras em português/inglês corrente e histórico de strikes |
| `heist-one` | jogo: Jev dá o julgamento instantâneo dos guardas, código determinístico manda no mundo |
| `openjev`/SemIf | reproduz o padrão com modelos abertos locais (WebGPU): probabilidades de opção lidas direto |
| `system-one-adapter-python` (oficial) | mesma API `system_one` sobre OpenAI/Anthropic para comparar custo e acerto |
| `awesome-typesafe`, `awesome-jev-by-typesafe` | listas curadas; exemplos por linguagem |

Regra ao aproveitar: chaves só em `~/.secrets/jev.env` (`executor/credenciais.py`); nenhum
transporte pago paralelo — passe pelo `shared.ask` ou registre no livro-caixa; nunca imprimir
nem versionar chave.

## 10. Padrões de desenho que se repetem em tudo o que foi medido

1. Código manda no fluxo; o Jev dá a parte semântica pequena e fechada.
2. Uma pergunta = um julgamento; perguntas independentes vão juntas; dependentes, em chamada nova.
3. Escape em toda taxonomia; ato de fala na instrução; rótulo que diz o que a classe é.
4. Corte medido no dado do domínio (jevcal/Janus/rodada própria), nunca copiado.
5. Amarelo vai para gente ou modelo caro; verde é triagem, não parecer.
6. Sentinela + concordância + corte; irreversível sempre com humano.
7. Canário semanal e auditoria de números: o modelo já derivou em menos de um dia.
8. Antes de afirmar que algo funciona: previsão no cabeçalho, commit, depois a chamada.
