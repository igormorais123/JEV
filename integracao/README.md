# O Jev dentro do Claude Code e do Codex

## As camadas (2026-09-20): o Jev decide o que entra no contexto do modelo caro

Depois do estudo (31 mil chamadas, 27 rodadas), o Jev foi posto nos pontos do fluxo do
Claude Code em que o Fable mais gasta tokens: ler arquivo grande, escolher por onde começar
depois de um Grep, e digerir conteúdo que veio de fora. Cada camada é um hook que falha para o
lado aberto, registra tudo em `estado/camadas.jsonl` e tem uma medida do estudo por trás.

| camada | evento | o que faz | modo |
|---|---|---|---|
| tema | `UserPromptSubmit` | sugere a skill pelo assunto do pedido; grava o pedido vigente da sessão | ativo |
| **leitura** | `PreToolUse` em `Read` | em arquivo com 200 linhas ou mais, classifica blocos de ~60 linhas contra o pedido vigente e limita o `Read` à janela dos blocos essenciais (confiança ≥ 0,90, com um vizinho de cada lado) ou, sem nenhum, dos três do topo; injeta uma nota dizendo o que ficou de fora | ativo |
| **leitura pelo shell** | `PreToolUse` em `Bash` | a mesma política, na porta por onde o texto de fato entra (medido em 2026-09-21: 81% do texto de ferramenta vem do `Bash`, 9% do `Read`): quando o comando é só de leitura (`cat`, `sed -n 'A,Bp'`, `head`, `tail`, `echo`, `cd`, `ls`, `wc`, `pwd`, sem pipe, redirecionamento, variável ou curinga) e um segmento é `cat ARQUIVO` de arquivo grande, ele vira `sed -n 'A,Bp' ARQUIVO` com a janela do Jev; no máximo dois arquivos por comando. Qualquer outro comando fica como veio, porque o hook responde `allow`. Alcance medido por replay: 3,5% do texto do `Bash`; o resto tem pipe, heredoc ou programa | ativo |
| **busca** | `PostToolUse` em `Grep`, `Glob`, WebSearch, buscas do Gmail, Drive e Agenda | com 6 ou mais itens, classifica cada um (arquivo mais as linhas que casaram; ou o registro da listagem) e diz por onde começar; não esconde nada | ativo |
| **sentinela** | `PostToolUse` em WebFetch, WebSearch, página, e-mail, Drive; e blocos `<pasted_content>` do prompt | pergunta se o texto tenta dar ordens ao sistema; avisa, não bloqueia | ativo |
| **saída** | `PostToolUse` em `Bash` e `PowerShell` | em saída com 3 mil caracteres ou mais e uma linha de erro (traceback, `XxxError:`, `FAILED`, `fatal:`, `command not found`; não a palavra solta, que casava com todo arquivo-fonte lido), aponta em que parte está a causa (só com confiança ≥ 0,90; aplicação não medida no estudo) | ativo |
| verificar | skill `/jev-verificar` | afirmações contra a fonte: suportado, contradito, não informado (E3: 95,8%) | sob demanda |
| guarda | `PreToolUse` em `Bash` | segunda camada da regra de comando perigoso | sombra (decisão do Igor pendente) |
| ler | skill `/jev-ler` | o agente passa a pergunta e os arquivos candidatos, ou `--rg PADRAO`; volta só os blocos do topo, com número de linha | sob demanda |

O que o primeiro teste real mudou no desenho: em código, o Jev **quase nunca** diz
`irrelevante` com confiança 0,99 (em 14 blocos de `executor/ledger.py`, zero), então uma
regra de descarte nunca dispararia. A regra passou a ser a da ordenação medida — ficam os
blocos do topo — e um `essencial` fraco (0,45) no início do arquivo mostrou que o top-3 puro
arrasta a janela: a janela nasce dos essenciais fortes. Com isso, o mesmo arquivo de 784
linhas foi lido em 240 (7.400 tokens estimados a menos) por US$ 0,0007 e 3,5 s de espera.

Custo por camada e por chamada: leitura US$ 0,00005 por bloco, busca US$ 0,00002 por
arquivo, sentinela US$ 0,00003 por parte. Teto diário do conjunto: US$ 0,20; acumulado,
US$ 1,00, na mesma carteira de US$ 5,00 do projeto. Latência: 0,6 a 3,5 s por hook no
regime do dia (o provedor muda de regime no meio do dia; ver Q044 e H038).

A medição — tokens evitados, releituras (arrependimento), concordância da busca, acusações
do sentinela, custo — está em [`docs/CAMADAS-CLAUDE-CODE.md`](../docs/CAMADAS-CLAUDE-CODE.md),
gerada por `python integracao/camadas/medir.py --gravar`. Instalação e modos:

```
python integracao/instalar.py --ver
python integracao/instalar.py --instalar --gancho leitura --modo ativo     # ou sombra
python integracao/instalar.py --instalar --gancho leitura-shell --modo ativo   # só no Claude Code
python integracao/instalar.py --instalar --gancho busca --modo ativo
python integracao/instalar.py --instalar --gancho sentinela --modo ativo
python integracao/instalar.py --instalar --gancho saida --modo ativo
python integracao/instalar.py --desinstalar --gancho todos
python integracao/instalar.py --agendar        # tarefa diária do Windows com a rotina completa
```

**Chaves e provedor, para qualquer instância desta máquina.** As chaves vivem no cofre
privado `~/.secrets/jev.env` (fora de qualquer repositório; nunca versionar, exibir ou colar em
prompt), com `TYPESAFE_API_KEY`, `OPENROUTER_API_KEY` e a preferência `JEV_PROVEDOR=typesafe`.
Ordem de leitura em `executor/credenciais.py`: variável de ambiente, `.env` do projeto, o cofre.
`python executor/credenciais.py` mostra de onde cada chave vem, sem nenhum valor. O provedor
preferido é a TypeSafe direto (`api.typesafe.ai`, modelo `jev-1.13.0`): só tem o Jev, menos
superfície. O E5 mediu o preço disso nos mesmos 40 casos: mesma resposta nos 40, latência p50
de 755 ms contra 396 ms pelo OpenRouter, custo 12% maior. A TypeSafe não devolve o valor
cobrado; o livro-caixa precifica pelo uso de tokens com a tarifa publicada (US$ 42 por bilhão
de tokens), e o roteador registra esse valor no controle diário. Para voltar ao OpenRouter:
`JEV_PROVEDOR=openrouter` no ambiente ou no cofre.

**A medição não depende de ninguém lembrar.** Ao fim de cada sessão do Claude Code, o hook
`SessionEnd` regera `docs/CAMADAS-CLAUDE-CODE.md`; uma vez por dia, às 23h30, a tarefa agendada
`JEV-medicao-das-camadas` roda `integracao/camadas/rotina.py` inteira: mede, concilia o
livro-caixa (as chamadas dos hooks entram nele), regera as páginas que citam o caixa, audita e
faz commit local por lista explícita de arquivos — nunca push. Se a auditoria não fechar, a
rotina para sem commitar e o motivo fica em `integracao/estado/rotina.log`.

O que **não** está nas camadas, por medida: roteamento de esforço (cobertura útil 0% em 60
pedidos reais), escolha de modelo, e qualquer decisão de permissão — o Jev não libera nada
sozinho.

---

Uso atual no Codex: [leitura assistida antes do contexto](USO-CODEX.md), com referências
completas, abstenção e carteira compartilhada. As seções históricas abaixo descrevem
medições anteriores; não representam economia de tokens do Astra comprovada.

Este pacote aplica o Jev aos fluxos de trabalho reais desta máquina. Ele foi construído para
responder a uma pergunta de economia — *dá para o Jev, que custa US$ 0,042 por milhão de tokens,
poupar trabalho do Opus e do Fable, que custam milhares de vezes mais?* — e a resposta honesta
tem duas partes.

## O que não funcionou, e por quê

**Roteamento de esforço não funciona neste fluxo de trabalho.** A ideia era classificar cada
pedido como simples ou difícil e, nos simples, evitar subagente e modelo caro. Medido em 60
pedidos reais sorteados do histórico do Claude Code:

| Formulação | Acurácia | Cobertura útil |
|---|---|---|
| Quatro classes de esforço | 51,7% | 0% — 55 dos 60 pedidos viraram `investigacao` |
| Binária, "o pedido diz onde mexer?" | 66,7% | 0% |
| Binária, "quantos minutos leva?" | 70,0% | 0% |
| Binária, **com o contexto da conversa anterior** | 71,8% | 0% |

*Cobertura útil* é a fração de pedidos que o Jev manda para o caminho barato com confiança
acima do corte. Ela é zero em todas as formulações: quando o Jev diz "simples", diz com
confiança de no máximo **0,73**, e não existe corte que economize sem arriscar estragar
trabalho.

A causa apareceu numa terceira pergunta: **54 dos 60 pedidos reais dependem do que foi dito
antes** — "continue", "verifique e corrija então", "piorou tudo". A informação que decidiria não
está no texto do pedido. Dar o contexto anterior ao modelo melhorou 2,6 pontos e não moveu a
cobertura. O gargalo não é a formulação da pergunta; é que a decisão de esforço não está escrita
na mensagem.

**Guarda de comando irreversível: o primeiro desenho estava errado, o segundo funciona.**

A primeira leitura desta seção dizia que o guarda era um bom resultado inútil, porque o Claude
Code aqui roda em `acceptEdits` com `Bash(*)` liberado e não haveria confirmação a poupar. Duas
coisas mudaram isso.

*Primeiro, a medição.* A avaliação inicial usava o Jev **no lugar** da regra, e com 60 comandos
e apenas 4 irreversíveis o recall ficou em 0,75 — inutilizável. Refeita com 120 comandos e 12
irreversíveis (R16), a conclusão se inverteu: sozinho o Jev perde de 2 a 6 dos 12, e mesmo a
melhor formulação com corte de confiança interrompe 41,7% dos comandos benignos. **Substituir a
regra é inseguro.** Usar o Jev *depois* da regra, só para liberar o que ela barrou, é outro
resultado:

| | interrompe comando benigno | irreversíveis liberados |
|---|---|---|
| regra por palavra sozinha | **72,2%** | 0 de 12 |
| regra + Jev como segunda camada | **29,6%** | **0 de 12** |

*Segundo, o fato de que existe fricção.* Enquanto eu testava este hook, o
`~/.agents/hooks/deny-dangerous.ps1` bloqueou **dois comandos meus legítimos** nesta sessão —
um `grep` e uma demonstração — porque o texto continha `rm -rf` e `git push` dentro de aspas.
Não é hipótese: é o alarme falso de 72% acontecendo ao vivo, e ele custa uma volta inteira de
diagnóstico cada vez.

**A ressalva que impede ligar isto hoje.** O guard global **nega**, não pergunta, e um `allow`
deste hook não sobrepõe o `deny` de outro: o comando continua barrado. Então o ganho medido só
se realiza em um destes dois caminhos, e a escolha entre eles é do Igor:

1. o guard global passa a devolver `ask` em vez de `deny`, e este hook responde por ele; ou
2. este hook substitui o `deny-dangerous.ps1`, herdando a mesma regra por palavra que já está
   escrita dentro dele, mais a segunda camada.

Enquanto nenhum dos dois acontecer, o hook fica em **sombra**: registra o que teria liberado,
não muda nada. `python instalar.py --ver` diz o estado.

Detalhe completo em `../laboratorio/PREREGISTRO.md`, seção do programa E17; dados em
`../laboratorio/r16-guarda-de-comando.json` e `r16b-segunda-camada.json`.

## O que funciona, e está instalado

**Dizer sobre o que é a mensagem, para sugerir a skill certa.** É a aplicação que o estudo
mediu desde o E1, e a linha de base não é inventada: são os oito `hookify.suggest-skill-*` que
já rodavam nesta máquina por `regex_match`.

Nos mesmos 60 pedidos reais, com corte de confiança 0,90:

| | Temas reais encontrados (de 23) | Sugestões à toa (em 37 sem tema) |
|---|---|---|
| **Jev** | **9** | **0** |
| Regex de hoje | 5 | 1 |

Quase o dobro da cobertura, sem nenhum disparo falso. E o erro do Jev é por omissão — 10 dos 13
erros foram deixar de sugerir, não sugerir errado —, que é o lado seguro para quem injeta
contexto num modelo caro.

O corte é **0,90**, não o 0,99 do guia prático, porque a assimetria aqui é outra: uma sugestão
perdida custa uma skill não carregada; uma sugestão errada custa três linhas de contexto. O
corte foi calibrado neste dado, que é o cuidado nº 2 do guia.

## Como está instalado

Um hook `UserPromptSubmit` no Claude Code (`~/.claude/settings.json`) e no Codex
(`~/.codex/hooks.json`), em modo **ativo**:

```
python integracao/instalar.py --ver          # estado atual
python integracao/instalar.py --instalar --modo ativo
python integracao/instalar.py --instalar --modo sombra   # classifica e registra, não injeta
python integracao/instalar.py --desinstalar
```

O instalador é idempotente e faz backup datado de cada arquivo antes de tocá-lo. Os oito
`hookify.suggest-skill-*` continuam ligados: a troca por este hook é uma decisão à parte, não
foi feita.

Para quem não tem hook — script, Codex por linha de comando, ou o próprio agente:

```
python -m jev_router.cli "redigir a contestação do processo"
python -m jev_router.cli --situacao          # gasto e teto
```

## Garantias de operação

- **Falha para o lado aberto.** Sem chave, sem rede, fora do teto ou com resposta fora do
  contrato, o hook sai em silêncio com código 0. A sessão segue como seguiria sem ele.
- **Segredo não sai daqui.** `redacao.py` mascara credencial antes do envio, por forma e não
  por lista. O teste `test_redacao.py` roda contra as chaves que de fato existem nesta máquina
  e exige que nenhuma sobreviva — sem imprimir nenhuma, nem na falha.
- **Custo sob teto verificado antes do envio.** US$ 0,000085 por chamada no pior caso, teto de
  US$ 0,05 por dia e US$ 1,00 acumulado, em `gastos.jsonl`. As 455 classificações desta
  construção custaram **US$ 0,0104**.
- **Latência**: 488 ms na primeira vez, 74 ms quando o pedido repete (cache em disco).
- **Acento**: a nota é escrita em bytes UTF-8, não pelo console. Por `print` ela chegava ao
  modelo como "confianÃ§a" — o teste `test_a_nota_sai_em_utf8_com_acento_intacto` roda o hook de
  verdade e trava isso.

## Como refazer a medição

```
python avaliacao/amostrar.py --n 60            # sorteia pedidos reais do histórico
python avaliacao/skills.py --rodar             # Jev contra os regex de hoje
python avaliacao/rodar.py                      # o roteamento de esforço que fracassou
python avaliacao/com_contexto.py               # com e sem o contexto da conversa
python avaliacao/comandos.py --extrair --rodar # o guarda de comando
```

Os gabaritos em `avaliacao/gabarito-*.json` foram anotados **antes** de cada execução, e trazem
o mesmo viés declarado do estudo: quem escreveu os critérios anotou o gabarito. Sob um anotador
independente os números podem ser outros — é exatamente o que o E8, o E11 e o E12 mediram.

---

## O que se mediu do roteador em produção

Primeira leitura do que o hook fez de verdade, não em amostra: **88 decisões reais**, 28 delas
na política de tema atual.

| | |
|---|---|
| latência mediana | **431 ms** |
| latência p90 | 623 ms |
| custo total das 88 | **US$ 0,0022** |
| sugeriu skill | 20 de 28 |
| acerto | **não medido** — ver abaixo |

O hook não atrapalha o fluxo e custa quase nada. Se ele acerta, ainda não se sabe, e a razão é
um defeito de engenharia meu: `decisoes.jsonl` guardava só o SHA-256 do pedido, por privacidade,
e recasar o hash contra o transcript recuperou **1 caso de 28**. Um registro que não permite
medir se a decisão foi certa não serve à finalidade que ele próprio declara.

Corrigido: o pedido passa pela mesma redação de credenciais aplicada antes de qualquer envio e
fica em `estado/pedidos.jsonl`, que o `.gitignore` exclui. A próxima medição terá texto.

## Os dois hooks, e como mexer neles

```
python integracao/instalar.py --ver                                   # estado dos dois
python integracao/instalar.py --instalar --gancho guarda --modo ativo # liga o guarda
python integracao/instalar.py --desinstalar --gancho todos            # tira os dois
```

| hook | evento | o que decide | modo hoje |
|---|---|---|---|
| `jev_prompt_router.py` | `UserPromptSubmit` | tema do pedido, sugere a skill | **ativo** |
| `jev_guarda_comando.py` | `PreToolUse` (Bash, PowerShell) | se o comando barrado pode passar | **sombra** |

Os dois falham para o lado que não atrapalha: sem chave, sem rede, fora do teto ou fora do
contrato, saem em silêncio com código 0 e a sessão segue como seguiria sem eles. O guarda tem
uma diferença: ele falha para o lado **fechado**, ou seja, na dúvida a confirmação acontece.
