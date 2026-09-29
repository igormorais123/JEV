# O Jev em camadas no Claude Code — medição

*Página gerada por `integracao/camadas/medir.py --gravar`; não edite à mão. Os números saem
de `integracao/estado/camadas.jsonl`, `decisoes.jsonl` e `gastos.jsonl`, e cada linha desses
arquivos é uma decisão de verdade tomada numa sessão desta máquina, nos dois modos. Sessões
de teste de ponta a ponta (`smoke-*`) ficam fora.*

Registros: **1.900** (2026-09-20T20:44:33 a 2026-09-26T22:34:03).
Última rotina automática: 2026-09-26T11:16:15 (so-medir, ok).

## As camadas, e o que cada uma faz com o contexto do modelo caro

| camada | ponto do fluxo | o que decide | base no estudo |
|---|---|---|---|
| tema (roteador) | `UserPromptSubmit` | sobre o que é o pedido; sugere a skill | E1, E13: 9 de 23 temas, 0 falsos |
| leitura | `PreToolUse` em `Read` e em `Bash` com `cat ARQUIVO` | que janela do arquivo entra | E16, R18, R20, R26: top-3 mantém a resposta, corta 74% |
| busca | `PostToolUse` em `Grep`, `Glob`, WebSearch, buscas do Gmail, Drive e Agenda | por qual item começar | E1, E16: triagem 92–99%, 8 de 8 essenciais no topo |
| sentinela | `PostToolUse` em conteúdo externo e no conteúdo colado no prompt | se o texto tenta dar ordens | R23, R27: 95% de detecção, 2,4% de alarme falso |
| saída | `PostToolUse` em `Bash` com erro e 3 mil caracteres ou mais | em que parte da saída está a causa | não medida no estudo; só aponta com confiança ≥ 0,90 |
| verificar (skill `/jev-verificar`) | quando o agente chama | se cada afirmação se sustenta na fonte | E3: 95,8% contra 62,5% |
| guarda (sombra) | `PreToolUse` em `Bash` | se o comando barrado pode passar | R16: 72% → 30% de interrupção, 0 de 12 liberados |
| ler (skill `/jev-ler`) | quando o agente chama | quais blocos de vários arquivos entram | R18, R20, R26: k = 3 |

## O total

| | valor |
|---|---|
| tokens que deixaram de entrar no contexto (estimados, 4 caracteres por token) | **90.671** |
| o que isso vale ao preço declarado de US$ 15/M de entrada (parâmetro, não preço lido) | US$ 1,3601 |
| chamadas ao Jev pelas camadas | 1.320 |
| custo do Jev, todas as camadas e o roteador | **US$ 0,119877** |

## Leitura (`Read`, e `cat` dentro de comando do shell)

| | valor |
|---|---|
| leituras vistas pelos hooks | 1.430 |
| por via: `Read` | 1.175 vistas, 13 estreitadas, 75.922 tokens evitados |
| por via: shell (`cat`, `sed -n`, `head` em comando só de leitura) | 255 vistas, 2 estreitadas, 14.010 tokens evitados |
| com pedido vigente na sessão | 1.418 |
| classificados (arquivo grande, com pedido) | 50 |
| estreitados | 15 (em modo ativo: 15) |
| linhas evitadas | 5.681 |
| tokens evitados (estimados) | **89.932** |
| releitura do mesmo arquivo em até 10 leituras (arrependimento) | **8 de 15** |
| linhas relidas nessas voltas (o que fez falta) | 2.457 de 5.681 evitadas (mais 1 volta(s) de tamanho não registrado) |
| blocos por classe | complementar: 147, essencial: 146, incerto: 2, irrelevante: 136 |
| blocos que uma regra "irrelevante ≥ 0,99" descartaria | 0 |
| latência mediana / p90 do hook | 3.556 ms / 5.761 ms |
| custo | US$ 0,036574 em 456 chamadas |

Por que não estreitou: tipo de arquivo fora da camada: 911, read ja delimitado: 314, arquivo pequeno: 103, falha: BudgetError: 36, metade ou mais dos blocos e essencial; arquivo inteiro interessa: 20, economia pequena demais para valer o intervalo: 13, sem pedido vigente: 12, nao coube em blocos: 2, nao foi possivel ler: 2, falha: http_error: 1, falha: sem tempo: 1.

## Busca (`Grep`, `Glob` e listagens externas)

| | valor |
|---|---|
| listagens vistas | 60 (Glob: 1, Grep: 18, WebSearch: 40, mcp__claude_ai_Gmail__search_threads: 1) |
| classificados (6 ou mais arquivos, com pedido) | 36 |
| com sugestão | 8 (em modo ativo: 8) |
| arquivos postos em "leia primeiro" | 41 |
| desses, lidos pelo agente nas 8 leituras seguintes | **2 de 41** |
| arquivos marcados irrelevantes com ≥ 0,99 | 1 |
| latência mediana | 6.788 ms |
| custo | US$ 0,010062 em 375 chamadas |

Por que não sugeriu: nada a ordenar: nenhum essencial nem descartável: 23, falha: BudgetError: 22, poucos itens: 4, falha: timeout: 2, falha: OperationalError: 1.

## Sentinela (conteúdo externo)

| | valor |
|---|---|
| conteúdos vistos | 302 |
| inspecionados (partes de 3.500 caracteres) | 151 (194 partes) |
| acusados | **12** |
| por ferramenta | WebFetch: 140, mcp__claude_ai_Gmail__get_thread: 2, mcp__claude_ai_Gmail__search_threads: 1, prompt/pasted_content: 8 |
| acusados por ferramenta | WebFetch: 7, mcp__claude_ai_Gmail__get_thread: 1, prompt/pasted_content: 4 |
| latência mediana | 1.079 ms |
| custo | US$ 0,006613 em 194 chamadas |

Uma acusação não é bloqueio: o conteúdo continua no contexto com um aviso. A R23 mede 2,4% de
alarme falso em texto limpo e 7 de 24 em texto legítimo com palavra-gatilho; a taxa aqui só
vira medida de acerto quando alguém revisar as acusações.

## Saída de comando (`Bash`, `PowerShell`)

| | valor |
|---|---|
| saídas longas com marca de erro | 104 |
| classificadas | 100 |
| com causa apontada (confiança ≥ 0,90) | **13** |
| partes por classe | causa: 39, consequencia: 17, incerto: 3, normal: 218 |
| latência mediana | 1.462 ms |
| custo | US$ 0,014181 em 286 chamadas |

Aplicação não medida no estudo: a parte apontada só vira acerto quando alguém conferir contra
a causa real. Por que não apontou: nenhuma parte com causa acima do corte: 86, falha: BudgetError: 4, falha: timeout: 1.

## Verificação pela skill (`/jev-verificar`)

| | valor |
|---|---|
| usos / afirmações | 1 / 3 |
| suportadas (confiança ≥ 0,90) | 1 |
| contraditas | **1** |
| não informadas pela fonte | 0 |
| não verificadas (falha) | 0 |
| custo | US$ 0,000193 em 3 chamadas |

## Leitura seletiva pela skill (`/jev-ler`)

| | valor |
|---|---|
| usos | 2 (com seleção: 2) |
| blocos classificados / devolvidos | 6 / 5 |
| caracteres nos candidatos / devolvidos | 21.553 / 18.594 |
| tokens evitados (estimados) | **739** |
| custo | US$ 0,000353 em 6 chamadas |

## Tema e guarda (as camadas anteriores)

| | valor |
|---|---|
| decisões do roteador de tema em produção | 524 (sugeriu skill em 119; 117 do cache) |
| latência mediana sem cache | 841 ms |
| custo do roteador | US$ 0,012742 |
| guarda de comando (sombra) | 906 chamadas, US$ 0,039159 |

## O que esta página não prova

- Tokens evitados são estimativa por caracteres; o tokenizador do modelo caro conta diferente.
- Uma leitura estreitada sem releitura não prova que a janela bastou: prova que o agente não
  voltou. A medida de acerto exige revisar as janelas contra o que o agente de fato usou.
- A concordância da busca mede se a sugestão foi seguida, e o agente que a segue pode estar
  seguindo o próprio Grep.
- O valor em dólares depende do preço declarado no parâmetro; troque-o e a linha muda.
