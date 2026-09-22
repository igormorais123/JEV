# O Jev em camadas no Claude Code — medição

*Página gerada por `integracao/camadas/medir.py --gravar`; não edite à mão. Os números saem
de `integracao/estado/camadas.jsonl`, `decisoes.jsonl` e `gastos.jsonl`, e cada linha desses
arquivos é uma decisão de verdade tomada numa sessão desta máquina, nos dois modos. Sessões
de teste de ponta a ponta (`smoke-*`) ficam fora.*

Registros: **200** (2026-09-20T20:44:33 a 2026-09-22T03:26:29).
Última rotina automática: 2026-09-22T03:26:34 (so-medir, ok).

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
| tokens que deixaram de entrar no contexto (estimados, 4 caracteres por token) | **37.418** |
| o que isso vale ao preço declarado de US$ 15/M de entrada (parâmetro, não preço lido) | US$ 0,5613 |
| chamadas ao Jev pelas camadas | 504 |
| custo do Jev, todas as camadas e o roteador | **US$ 0,042378** |

## Leitura (`Read`, e `cat` dentro de comando do shell)

| | valor |
|---|---|
| leituras vistas pelos hooks | 106 |
| por via: `Read` | 67 vistas, 4 estreitadas, 28.292 tokens evitados |
| por via: shell (`cat`, `sed -n`, `head` em comando só de leitura) | 39 vistas, 1 estreitadas, 8.387 tokens evitados |
| com pedido vigente na sessão | 106 |
| classificados (arquivo grande, com pedido) | 19 |
| estreitados | 5 (em modo ativo: 5) |
| linhas evitadas | 1.936 |
| tokens evitados (estimados) | **36.679** |
| releitura do mesmo arquivo em até 10 leituras (arrependimento) | **2 de 5** |
| linhas relidas nessas voltas (o que fez falta) | 164 de 1.936 evitadas (mais 1 volta(s) de tamanho não registrado) |
| blocos por classe | complementar: 69, essencial: 109, incerto: 1, irrelevante: 32 |
| blocos que uma regra "irrelevante ≥ 0,99" descartaria | 0 |
| latência mediana / p90 do hook | 3.476 ms / 4.035 ms |
| custo | US$ 0,013239 em 211 chamadas |

Por que não estreitou: read ja delimitado: 55, tipo de arquivo fora da camada: 17, arquivo pequeno: 15, metade ou mais dos blocos e essencial; arquivo inteiro interessa: 13, economia pequena demais para valer o intervalo: 1.

## Busca (`Grep`, `Glob` e listagens externas)

| | valor |
|---|---|
| listagens vistas | 8 (Glob: 1, Grep: 6, WebSearch: 1) |
| classificados (6 ou mais arquivos, com pedido) | 4 |
| com sugestão | 3 (em modo ativo: 3) |
| arquivos postos em "leia primeiro" | 28 |
| desses, lidos pelo agente nas 8 leituras seguintes | **0 de 28** |
| arquivos marcados irrelevantes com ≥ 0,99 | 0 |
| latência mediana | 4.091 ms |
| custo | US$ 0,001245 em 51 chamadas |

Por que não sugeriu: poucos itens: 4, nada a ordenar: nenhum essencial nem descartável: 1.

## Sentinela (conteúdo externo)

| | valor |
|---|---|
| conteúdos vistos | 14 |
| inspecionados (partes de 3.500 caracteres) | 10 (29 partes) |
| acusados | **2** |
| por ferramenta | WebFetch: 7, prompt/pasted_content: 3 |
| acusados por ferramenta | prompt/pasted_content: 2 |
| latência mediana | 1.335 ms |
| custo | US$ 0,001313 em 29 chamadas |

Uma acusação não é bloqueio: o conteúdo continua no contexto com um aviso. A R23 mede 2,4% de
alarme falso em texto limpo e 7 de 24 em texto legítimo com palavra-gatilho; a taxa aqui só
vira medida de acerto quando alguém revisar as acusações.

## Saída de comando (`Bash`, `PowerShell`)

| | valor |
|---|---|
| saídas longas com marca de erro | 68 |
| classificadas | 68 |
| com causa apontada (confiança ≥ 0,90) | **3** |
| partes por classe | causa: 6, consequencia: 4, incerto: 1, normal: 193 |
| latência mediana | 1.340 ms |
| custo | US$ 0,009603 em 204 chamadas |

Aplicação não medida no estudo: a parte apontada só vira acerto quando alguém conferir contra
a causa real. Por que não apontou: nenhuma parte com causa acima do corte: 65.

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
| decisões do roteador de tema em produção | 185 (sugeriu skill em 93; 88 do cache) |
| latência mediana sem cache | 935 ms |
| custo do roteador | US$ 0,003158 |
| guarda de comando (sombra) | 439 chamadas, US$ 0,013274 |

## O que esta página não prova

- Tokens evitados são estimativa por caracteres; o tokenizador do modelo caro conta diferente.
- Uma leitura estreitada sem releitura não prova que a janela bastou: prova que o agente não
  voltou. A medida de acerto exige revisar as janelas contra o que o agente de fato usou.
- A concordância da busca mede se a sugestão foi seguida, e o agente que a segue pode estar
  seguindo o próprio Grep.
- O valor em dólares depende do preço declarado no parâmetro; troque-o e a linha muda.
