# O Jev em camadas no Claude Code — medição

*Página gerada por `integracao/camadas/medir.py --gravar`; não edite à mão. Os números saem
de `integracao/estado/camadas.jsonl`, `decisoes.jsonl` e `gastos.jsonl`, e cada linha desses
arquivos é uma decisão de verdade tomada numa sessão desta máquina, nos dois modos. Sessões
de teste de ponta a ponta (`smoke-*`) ficam fora.*

Registros: **3** (2026-09-20T20:44:33 a 2026-09-20T22:29:37).

## As camadas, e o que cada uma faz com o contexto do modelo caro

| camada | ponto do fluxo | o que decide | base no estudo |
|---|---|---|---|
| tema (roteador) | `UserPromptSubmit` | sobre o que é o pedido; sugere a skill | E1, E13: 9 de 23 temas, 0 falsos |
| leitura | `PreToolUse` em `Read` | que janela do arquivo entra | E16, R18, R20, R26: top-3 mantém a resposta, corta 74% |
| busca | `PostToolUse` em `Grep` | por qual arquivo começar | E16: 8 de 8 essenciais no topo |
| sentinela | `PostToolUse` em conteúdo externo | se o texto tenta dar ordens | R23, R27: 95% de detecção, 2,4% de alarme falso |
| guarda (sombra) | `PreToolUse` em `Bash` | se o comando barrado pode passar | R16: 72% → 30% de interrupção, 0 de 12 liberados |
| ler (skill `/jev-ler`) | quando o agente chama | quais blocos de vários arquivos entram | R18, R20, R26: k = 3 |

## O total

| | valor |
|---|---|
| tokens que deixaram de entrar no contexto (estimados, 4 caracteres por token) | **8.269** |
| o que isso vale ao preço declarado de US$ 15/M de entrada (parâmetro, não preço lido) | US$ 0,124 |
| chamadas ao Jev pelas camadas | 17 |
| custo do Jev, todas as camadas e o roteador | **US$ 0,002129** |

## Leitura (`Read`)

| | valor |
|---|---|
| Reads vistos pelo hook | 2 |
| com pedido vigente na sessão | 2 |
| classificados (arquivo grande, com pedido) | 1 |
| estreitados | 1 (em modo ativo: 1) |
| linhas evitadas | 604 |
| tokens evitados (estimados) | **8.269** |
| releitura do mesmo arquivo em até 10 leituras (arrependimento) | **1 de 1** |
| linhas relidas nessas voltas (o que fez falta) | 0 de 604 evitadas (mais 1 volta(s) de tamanho não registrado) |
| blocos por classe | complementar: 7, essencial: 4, incerto: 1, irrelevante: 2 |
| blocos que uma regra "irrelevante ≥ 0,99" descartaria | 0 |
| latência mediana / p90 do hook | 3.035 ms / 3.035 ms |
| custo | US$ 0,00073 em 14 chamadas |

Por que não estreitou: read ja delimitado: 1.

## Busca (`Grep`)

| | valor |
|---|---|
| Greps vistos | 0 |
| classificados (6 ou mais arquivos, com pedido) | 0 |
| com sugestão | 0 (em modo ativo: 0) |
| arquivos postos em "leia primeiro" | 0 |
| desses, lidos pelo agente nas 8 leituras seguintes | **—** |
| arquivos marcados irrelevantes com ≥ 0,99 | 0 |
| latência mediana | — ms |
| custo | US$ 0 em 0 chamadas |

Por que não sugeriu: —.

## Sentinela (conteúdo externo)

| | valor |
|---|---|
| conteúdos vistos | 0 |
| inspecionados (partes de 3.500 caracteres) | 0 (0 partes) |
| acusados | **0** |
| por ferramenta | — |
| acusados por ferramenta | — |
| latência mediana | — ms |
| custo | US$ 0 em 0 chamadas |

Uma acusação não é bloqueio: o conteúdo continua no contexto com um aviso. A R23 mede 2,4% de
alarme falso em texto limpo e 7 de 24 em texto legítimo com palavra-gatilho; a taxa aqui só
vira medida de acerto quando alguém revisar as acusações.

## Leitura seletiva pela skill (`/jev-ler`)

| | valor |
|---|---|
| usos | 1 (com seleção: 1) |
| blocos classificados / devolvidos | 3 / 3 |
| caracteres nos candidatos / devolvidos | 12.973 / 12.973 |
| tokens evitados (estimados) | **0** |
| custo | US$ 0,000181 em 3 chamadas |

## Tema e guarda (as camadas anteriores)

| | valor |
|---|---|
| decisões do roteador de tema em produção | 94 (sugeriu skill em 67; 61 do cache) |
| latência mediana sem cache | 622 ms |
| custo do roteador | US$ 0,000963 |
| guarda de comando (sombra) | 10 chamadas, US$ 0,000255 |

## O que esta página não prova

- Tokens evitados são estimativa por caracteres; o tokenizador do modelo caro conta diferente.
- Uma leitura estreitada sem releitura não prova que a janela bastou: prova que o agente não
  voltou. A medida de acerto exige revisar as janelas contra o que o agente de fato usou.
- A concordância da busca mede se a sugestão foi seguida, e o agente que a segue pode estar
  seguindo o próprio Grep.
- O valor em dólares depende do preço declarado no parâmetro; troque-o e a linha muda.
