# jev-gateway: o Jev escolhendo a ferramenta de cada turno do Codex e do Claude Code

Instalado em 2026-09-22 a partir do vídeo "Como usar JEV no Codex e Claude Code (e gastar menos tokens)" (Vini, AI Coders Academy, https://youtu.be/rtWCFKg7XEs) e do repositório https://github.com/vinilana/jev-gateway (v0.4.1, MIT, projeto independente, não é da TypeSafe). Esta página diz o que o sistema faz, o que medi aqui, como ficou ligado ao nosso livro-caixa e quando vale usar.

## 1. O que ele faz

É um proxy local (Node, Hono) entre o agente de código e a API do modelo. Em cada requisição que carrega ferramentas, ele monta um `state` com a conversa e pergunta ao Jev, numa chamada só: qual ferramenta é a próxima (`choice` entre todas as ferramentas mais `no_tool_needed`), se alguma ferramenta é mesmo necessária (`noul`, como contraprova) e, para ferramentas cujos argumentos são todos fechados (enum, booleano, constante), o valor de cada argumento. Listas com mais de 120 ferramentas (o Claude Code manda 130 a 280) passam por duas chamadas: uma ranqueia por grupos, a outra decide entre os 3 melhores de cada grupo. É a mesma ideia da nossa seção "ordenar candidatos numa chamada" da `docs/ESSENCIA-DO-JEV.md`, aplicada a ferramentas.

A resposta vira um modo, que sai no cabeçalho `x-jev-gateway-mode`:

| modo | quando | efeito |
|---|---|---|
| `direct` | ferramenta e todos os argumentos com certeza | o gateway monta a chamada da ferramenta; o LLM nem é chamado |
| `forced` | ferramenta com certeza, argumentos abertos | `tool_choice` fixado nela; o LLM só preenche os argumentos |
| `hint` | certeza, mas `tool_choice` não pode mudar (Anthropic com thinking ligado, ou conversa com cache) | um `<system-reminder>` de uma linha é anexado ao fim do último bloco do usuário sugerindo a ferramenta; o modelo pode ignorar |
| `none` | certeza de que não precisa de ferramenta | `tool_choice: none` |
| `passthrough` | confiança abaixo de 0,7, as duas perguntas discordam, Jev falhou, sem ferramentas, ou o cliente já escolheu | requisição intocada; `x-jev-gateway-reason` diz por quê |

O Claude Code roda com thinking e cache, então recebe só `hint`. O Codex recebe `forced`/`none`/`direct`. Se o Jev cai, demora mais de 4 s ou a chave falha, tudo passa direto: o gateway nunca faz uma requisição falhar. Ele escuta só em `127.0.0.1` e não altera `~/.claude` nem `~/.codex`: só as sessões abertas por `jev-claude` e `jev-codex` passam por ele.

## 2. O que o autor mediu (benchmark dele, 120 sessões, 5 por célula)

Medianas com roteamento ligado, comparadas ao mesmo modelo sem roteamento. Tarefas: corrigir cinco bugs num motor de xadrez; acrescentar notação algébrica a ele. Fonte: README do `jev-gateway-bench`, 2026-09-18/19.

| modelo | corrigir bugs: saída / entrada / tempo | nova funcionalidade: saída / entrada / tempo |
|---|---:|---:|
| GPT-6 Astra (Codex) | −57% / −7% / −39% | 0% / +2% / +8% |
| GPT-5.6 Sol (Codex) | −57% / −40% / −36% | −9% / −39% / −16% |
| GPT-5.6 Luna (Codex) | −12% / −10% / +10% | −14% / −51% / −14% (mas resolveu 3 de 5, contra 5 de 5 sem) |
| Fable 5.1 (Claude Code) | −13% / −19% / +6% | −24% / −27% / −26% |
| Opus 5 (Claude Code) | −7% / −22% / +2% | +22% / +61% / +83% |
| Sonnet 5 (Claude Code) | −41% / −48% / −25% | +9% / +16% / +37% |

O que o próprio autor destaca: em depuração todos os modelos gastaram menos; em criar funcionalidade é cara ou coroa, e Opus 5 e Sonnet 5 ficaram claramente piores porque um `hint` que não cabe custa um desvio em vez de ser ignorado de graça. Cinco rodadas por célula é pouco; 80 a 96% dos tokens de entrada vêm do cache, então uma economia de entrada vale menos dinheiro do que a mesma economia em saída. O Jev custou entre meio centavo e dez centavos por cinco rodadas. Uma rodada foi descartada porque o agente achou o diretório de outra rodada e copiou.

## 3. O que medi aqui (2026-09-22, uma tarefa de uma linha em cada agente)

Tarefa: "use a ferramenta para contar os arquivos .py em `laboratorio/` e responda só o número" (resposta certa: 57). Ambiente real do Igor: Claude Code com 133 ferramentas (MCPs e plugins ligados), Codex com 13.

| | Claude Code (Fable 5.1) | Codex (GPT-6 Astra) |
|---|---|---|
| turno 1 | `hint` Glob, Jev 0,98, 2.016 ms, 20.055 tokens; LLM 5,7 s, 111.875 de entrada (cache 0), 153 de saída | `forced` exec, Jev 0,94, 1.117 ms, 4.097 tokens; LLM 5,2 s, 28.444 de entrada, 55 de saída |
| turno 2 | `passthrough` (Jev disse `no_tool_needed` a 0,99; com thinking não força `none`), 2.311 ms, 21.866 tokens; LLM 5,9 s, 113.197 (cache 111.873), 3 de saída | `none`, Jev 1,00, 974 ms, 4.225 tokens; LLM 4,1 s, 28.524 (cache 28.288), 5 de saída |
| resposta | 57 | 57 |
| custo do Jev (piso, só entrada) | US$ 0,00176 nos dois turnos | US$ 0,00035 nos dois turnos |

Leitura: o Jev acertou a ferramenta nos quatro turnos. No Claude Code o preço é uma chamada de ~20 mil tokens (a lista de 133 ferramentas com descrições vai inteira) e mais ~2 s por turno, cerca de 35% em cima dos ~5,8 s do modelo; no Codex, ~4 mil tokens e ~1 s. A US$ 0,042 por milhão de tokens (tabela da TypeSafe em `executor/prices.json`), um turno do Claude Code custa ~US$ 0,0008 e um do Codex ~US$ 0,0002. Cem turnos por dia no Claude Code dão ~US$ 0,08. O cache do prompt continuou funcionando nos dois (turno 2 com quase toda a entrada em cache), como o autor promete para o `hint`.

Nada disso mede economia: dois turnos não têm comparação sem roteamento. A comparação certa é o `--routing off` do próprio gateway (modo linha de base, que continua contando tokens) em tarefas parecidas, ou o `jev-gateway-bench` com `--agent claude --model claude-fable-5-1 --user-tools`.

## 4. Como ficou instalado neste PC

- `npm install -g jev-gateway` (Node 24). Chave: a TypeSafe do cofre, copiada para `~/.jev-gateway/.env` (permissão 0600 no autor; no Windows, arquivo do usuário). `JEV_PROVIDER=typesafe`.
- Portas: Claude Code 8789; Codex **8793** (`JEV_CODEX_PORT` no mesmo `.env`), porque 8790 e 8792 estavam ocupadas por `python -m http.server` antigos (um deles em `0.0.0.0`, que capturava as chamadas do painel). Antes de escolher porta, `netstat -ano | findstr LISTEN`.
- Ajustes nossos no `.env`, pelo que o estudo mediu: `JEV_MIN_CONFIDENCE=0.90` (o padrão 0,7 é folgado demais para `forced`, que age; 0,90 é o nosso corte de "usar") e `JEV_DIRECT_CALLS=false` (nunca responder sem o LLM: uma chamada montada errada pelo gateway passa sem ninguém olhar; as ferramentas de código são abertas e não perdem nada). Conferido em `/router/decide`: o exemplo das luzes, que saía `direct`, passou a sair `forced`.
- **Windows:** o lançador chama `spawn("claude")` sem shell, e o Node só encontra `.exe` no PATH; `claude` e `codex` estão instalados como `.cmd`. Os wrappers `~/bin/jev-claude.cmd` e `~/bin/jev-codex.cmd` (a pasta `~/bin` vem antes do npm no PATH) põem a pasta dos executáveis nativos no PATH e delegam ao lançador original. Sem eles: `could not run claude: spawn claude ENOENT`.
- Codex: o lançador detecta o login ChatGPT em `~/.codex/auth.json` e encaminha para `chatgpt.com/backend-api/codex`; os perfis `omniroute` do `config.toml` não são afetados (o gateway injeta `-c model_provider="jev-gateway"` só na sessão lançada).

Comandos: `jev-claude` e `jev-codex` no lugar de `claude` e `codex`; `--dashboard` (página em `localhost:8789/dashboard`, atualiza a cada 2 s, mostra só metadados), `--routing off|on`, `--status`, `--logs`, `--start`, `--stop`, `--setup`. Log por cliente em `~/.jev-gateway/<cliente>.log`, uma linha JSON por requisição.

## 5. Como ficou ligado ao nosso livro-caixa

O gateway tem chave e transporte próprios: é, por definição, um transporte pago fora de `executor/shared.py`. Para a carteira única de `runs/ledger.sqlite3` continuar dizendo a verdade, `integracao/gateway/conciliar.py`:

1. lê as linhas novas dos logs (`event: route` com `jev.inputTokens`), guardando por cliente quantas linhas já leu e a assinatura da primeira linha (arquivo recriado recomeça do zero);
2. precifica cada chamada com o mesmo `executor/pricing.py` do estudo (tabela `typesafe:jev-1.13.0`) e anexa a `integracao/gastos.jsonl`, que o livro-caixa já importa (`shared.import_legacy`, idempotente por digest de linha). O gateway não registra os tokens de saída do Jev, então o valor gravado é um **piso**, declarado no campo `custo_fonte`;
3. importa no ledger e imprime a carteira. Se o disponível cair abaixo de US$ 0,25, roda `jev-claude --routing off` e `jev-codex --routing off`: os gateways continuam medindo, mas param de chamar o Jev.

Roda sozinho no `SessionEnd` do Claude Code (`integracao/camadas/rotina.py --so-medir`, passo `gateway`) e na rotina diária completa. `python integracao/gateway/conciliar.py --relatorio` mostra, por cliente e por dia, turnos, modos, taxa em que o Jev decidiu, latência mediana, tokens e o piso de custo. Testes em `integracao/tests/test_gateway_conciliar.py`.

## 6. Quando usar, e o que vigiar

- **Vale para depuração e para sessões com muitas ferramentas.** É onde o benchmark do autor ganhou em todos os modelos, e onde o próprio README recomenda para o Claude Code ("melhores escolhas de ferramenta em listas grandes, não menor custo ou latência").
- **Meça antes de deixar ligado em tudo.** `--routing off` numa tarefa parecida e o painel "Token use" lado a lado. Em criar funcionalidade com Opus 5 ou Sonnet 5, o benchmark diz para não usar.
- **Latência:** +2 s por turno no Claude Code com 133 ferramentas. Em sessões longas de edição, é perceptível.
- **Privacidade:** a conversa inteira (até 60 mil caracteres, mensagens cortadas a 4 mil) vai à TypeSafe a cada turno, como já vai pelos nossos hooks de leitura. Imagens viram marcador.
- **Segurança local:** um gateway aberto pelo lançador não tem chave própria; qualquer processo desta máquina pode usá-lo para chamar o Jev com a nossa chave (`/router/decide`) e para falar com o provedor usando a credencial que o cliente enviar. Só escuta em `127.0.0.1`.
- **O corte de 0,7 na confiança** é o padrão do autor; aqui está em 0,90. Pela nossa fórmula (`confiança = (K·p − 1)/(K − 1)`), com 120 opções 0,7 equivale a p ≈ 0,70 e 0,90 a p ≈ 0,90; com 13 opções, 0,72 e 0,91. O corte mais alto roteia menos turnos (o benchmark do autor foi com 0,7); se o painel mostrar quase tudo em `passthrough` por "low confidence", é o preço dessa escolha, não defeito.
- **Painel:** `jev-claude --dashboard`. A página de um gateway tenta ler os outros nas portas padrão e nas passadas em `?peers=`; um gateway em porta não padrão só aparece na própria página (`localhost:8793/dashboard`) por bloqueio de CORS entre origens.
- **O `hint` é um `<system-reminder>` anexado ao turno do usuário.** Nossa sentinela não o vê (ela olha o que as ferramentas leem), e o texto é fixo ("A tool-routing model suggests the "X" tool is the most relevant next step. Ignore this if it does not fit"). Vale saber que ele existe ao ler transcrições.

## 7. O que o repositório dele tem que já usamos ou podemos usar

- `POST /router/decide`: pede uma decisão sem chamar nenhum LLM. Serve para testar roteamento de ferramentas de um MCP nosso com um `curl`.
- `scripts/mock-jev.mjs`: um Jev falso local para rodar um agente de ponta a ponta sem chave.
- `jev-gateway-bench`: o corredor de benchmark (workspace limpo por rodada, gateway próprio por porta, verificador oculto, auditoria de cópia entre rodadas). É o melhor desenho de benchmark de agente que vi no ecossistema do Jev; a ideia de "custo por tarefa resolvida, contando as falhas" é a métrica certa.
- A pergunta `needs_tool` (noul) como contraprova da `choice`, com passagem direta quando discordam: é a nossa "concordância entre duas perguntas" (Essência, 2.3), implementada por outra pessoa sem nos conhecer.
