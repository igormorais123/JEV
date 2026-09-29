# O Jev no Hermes da VPS

Implantado em 21/09/2026. Fonte versionada aqui; cópia viva na VPS (`ssh hermes`). Regra de
fundo, do estudo: o Jev decide, não escreve; o ganho em dinheiro aparece quando ele decide
**antes** da etapa cara — o que entra no contexto, se o modelo principal precisa acordar.

## Onde está cada peça

| peça | na VPS | o que faz |
|---|---|---|
| núcleo | `/root/.hermes/integrations/jev/jev_hermes/nucleo.py` | chaves, OpenRouter com reserva na TypeSafe, redação de credenciais, cache de 3 dias, teto, registro sem conteúdo |
| chaves | `/root/.hermes/integrations/jev/jev.env` (0600) | `OPENROUTER_API_KEY`, `TYPESAFE_API_KEY` copiadas do cofre do PC; tetos |
| camadas | `/root/.hermes/plugins/jev-camadas/` + `jev_hermes/camadas.py` | tema/risco do pedido, recorte de `read_file`, ordem de busca, sentinela em conteúdo externo, causa de erro no terminal, recorte de saída longa sem erro do terminal (≥ 16 mil caracteres: fica o essencial ao pedido, com vizinhas, primeira e última parte); desde 22/09 (estudo de 30 dias do `state.db`): seções de `skill_view` (`recortes.skill`), sessões de `session_search` (`recortes.sessoes`), resultado longo de `web_extract`/Apify/`execute_code` (`recortes.resultado`) e a transcrição do YouTube na ponte `youtube-auto-bridge` (`recortes.transcricao`: sem enchimento, com a frente de Igor) |
| ferramenta | `/root/.hermes/plugins/jev-advisor/` (v3) | `jev_advisor` para o modelo, com modo `lote` (até 60 textos) |
| porteiros | `/root/.hermes/scripts/jev_gate_*.py` | decidem se o job de cron acorda o modelo principal |
| rotinas | `/root/.hermes/scripts/jev_rotina_*.py` | jobs sem modelo principal: caixa vigiada, agenda, lembrete de compromisso, saúde do coletor, medição |
| ponte OpenAI | `hermes-jev-ponte.service`, `172.17.0.1:20145` (só a rede Docker) | traduz chat do OmniRoute para decisão do Jev; a chave vem no Bearer. No OmniRoute: nós `jev-openrouter` e `jev-typesafe`, combo `jev` |
| skill | `/root/.hermes/skills/jev/SKILL.md` | quando e como delegar ao Jev |
| contrato | `/root/HERMES.md`, linha "Sistema 1 é do Jev" | Jev por padrão em toda decisão fechada |
| medição | `jev_hermes/medir.py` → `estado/RELATORIO.md` | recalculada dos registros, diária |

## Modelo principal e economia da cota (desde 21/09/2026)

- Conversa com Igor: `gpt-6-sol`, esforço alto (desde 22/09/2026, por pedido de Igor; a guarda
  fixa o modelo e o esforço; entre 21 e 22/09 foi `gpt-6-astra` com esforço baixo, e é desse
  período a medição de cache abaixo), conta Pro (igor@inteia.com.br) primeiro no pool
  `openai-codex`, conta team depois. Guarda: `/root/.hermes/bin/hermes-enforce-stable-model`
  (cópia em `infra/`), que roda antes do gateway e a cada 2 min no stability-guard.
- Fora da cota do Astra, pelo OmniRoute (`providers.omniroute`, chave `OMNIROUTE_API_KEY`):
  reserva `sol` → `luna` → Astra; tarefas auxiliares (compressão, resumo de página, títulos,
  aprovação, curador, MCP...) em `luna`; subagentes (`delegate_task`) e cron sem modelo fixado em `sol`.
- Contexto: compressão com teto absoluto de 100 mil tokens (`compression.threshold_tokens`; o
  Astra tem janela de 1,05 M e comprimiria só em 525 mil) e poda sem modelo de resultados de
  ferramenta velhos acima de 48 mil (`proactive_prune_tokens`).
- Smoke do stability-guard a cada 6 h (era 30 min: ~1 M tokens/dia do Astra).
- `HERMES.md`: regra "Economia da cota do modelo principal" (delegar pesquisa e coleta).
- Camada `tema`: nota `[jev/economia]` quando P(pesquisa)+P(relatório) ≥ 0,70.
- Backup e restauração: `/root/backups/hermes-astra-jev-20260921T041649Z` (config, auth, guardas).

### Onde a economia é real (medido em 22/09/2026)

89% da entrada do Astra vem do cache (153,5 M contra 19,1 M novos em 14 dias, `session_model_usage`),
e o peso fixo por chamada é de 35 ferramentas com 53,9 KB de esquema mais 51,8 KB de system prompt
(`hermes prompt-size`). Daí três regras:

1. **Turno evitado vale muito mais que token de entrada poupado.** Um porteiro de cron que não acorda
   o agente economiza entrada, saída e raciocínio; um recorte de 20 mil tokens de entrada economiza
   janela e latência, e quase nada de cota. `medir.py` mostra os dois separados, nunca somados.
2. **Não mexer no prefixo.** Filtrar o índice de skills ou a lista de ferramentas por turno
   invalidaria o cache e custaria mais do que pouparia. As camadas cortam o texto *antes* de ele
   entrar no histórico, uma vez só; depois disso o prefixo fica estável.
3. **A métrica é custo por tarefa resolvida, contando as falhas** — um recorte que obriga a reler o
   arquivo gastou duas vezes. Por isso as camadas preferem não agir quando estão em dúvida.

## Jobs de cron com o Jev

| job | antes | agora |
|---|---|---|
| ARCANO — e-mails de Fábio (30 min) | Sol acordava 48×/dia, prompt ~71 KB; 43 de 50 em `[SILENT]` | código compara IDs com o estado; só acorda com e-mail novo, já com triagem do Jev |
| Monitor Fábio — WhatsApp (3×/dia) | 49 de 50 em silêncio | painel + cursor por código, conversa nova pelo Jev (dorme só com social ≥ 0,99) |
| Revisão diária de e-mail | Sol listava e abria cabeçalhos | Jev tria; dorme se tudo for descartável; acorda com a lista pronta |
| Radar de IA (diário) | Sol lia todo candidato | Jev lê contra as missões; tudo trivial → descarte pelo helper, sem Sol |
| Watchdog urgente Fábio | 22 palavras-chave | Jev decide relevância; palavras só se o Jev falhar |
| Caixa vigiada (novo, 30 min, 7–22h) | — | alerta imediato de e-mail que pede ação, cliente, jurídico, financeiro |
| Controle de prazos por e-mail (novo, 2/2 h, 7h–21h, `4029ae240122`) | script de julho por regex parou em 02/08 (97 eventos, 92 pendentes) | `jev_hermes/prazos.py`: triagem do Jev, prazo escolhido entre as datas do texto, baixa pela entrega; agenda na véspera 9h; aviso só do que mudou |
| Triagem de anexo recebido (novo, 8h e 15h, `5fa261790001`) | Igor abria o anexo para saber o que era | `jev_hermes/anexos.py`: o Jev diz o tipo pelo nome e pelo assunto; peça processual, decisão judicial e contrato são baixados e auditados pela checklist; avisa só o que acendeu vermelho e alimenta o painel da manhã. Em 14 dias: 27 anexos, 1 baixado, 2 pontos vermelhos, US$ 0,0007 |
| Checklist de documento (sob demanda) | Astra lia o contrato inteiro | `jev_hermes/checklist.py` (porte da R50): uma chamada, semáforo por item; o Astra lê só vermelho e amarelo |
| Tese — parágrafo diário (11h, `8f2260d9fe4a`) | Astra acordava com a skill `research` inteira e procurava sozinho: 9 `web_search`, 21 `web_extract`, 19 `execute_code`; 100 mil tokens por dia | `jev_gate_tese_diaria.py` (perfil `tese-diaria` de `jev_hermes/academico.py`): Crossref e OpenAlex por pilar do dia (2024+), fora da wiki, Jev lê título e resumo contra a tese; o agente acorda com os 5 melhores e confirma só o DOI escolhido |
| Radar temático — IA no setor público (sexta 17h, `452a2e509020`) | Astra buscava 3 artigos sozinho pela skill `research` | o mesmo porteiro acadêmico, perfil `radar-tematico` de `jev_hermes/academico.py`: consultas voltadas a Brasil e América Latina, 8 candidatos no contexto; rodou em 17 s e trouxe 2 artigos latino-americanos entre os 8 |
| Boletim Taguatinga e Celina Leão (7h, `7e5e2b895040`) | Astra descobria as notícias sozinho; 110 mil tokens por edição | `jev_gate_boletim_taguatinga.py`: Google Notícias (RSS, 24 h) das duas pautas; o Jev separa Taguatinga-DF da do Tocantins e fato de ruído; o agente acorda com a lista triada e só abre os links listados |
| Painel da manhã (novo, 7h) | — | agenda + demandas do escritório + pendências do WhatsApp pessoal (quem espera Igor, promessas sem entrega — `jev_hermes/pendencias.py`); o Jev pontua urgência e preparo; uma prioridade e o próximo gesto |
| Lembrete de compromisso (novo, 15 min, 7–21h) | `calendar-check.sh` no crontab do root chamava `claude -p` a cada 2 h (12 por dia) para escrever "sem eventos" num log sem leitor; os briefings matinal e da tarde do mesmo crontab, idem (desligados em 23/09, backup em `/root/backups/jev-lembrete-*`) | `rotinas/jev_rotina_lembrete_compromisso.py`: o código lê o Google Agenda; o Jev diz se o evento é com outras pessoas ou prazo (avisa) ou bloqueio pessoal ≥ 0,90 (cala) e se pede preparo; aviso no WhatsApp ~1 h antes, uma vez por evento. Testado com 11 eventos (compromissos todos avisados, foco e treino calados, ambíguos avisados, injeção ignorada; US$ 0,0002) e com um evento real criado e apagado |
| Sono de memória (diário) | Sol colhia e escolhia entre ~20 candidatos; 33 de 50 sem promover | porteiro roda colheita e snapshot; o Jev classifica; só acorda com P(durável) ≥ 0,30 |
| Saúde do coletor WhatsApp (novo, 8h) | — | avisa coletor parado ou deslogado (regra, sem Jev) |
| Medição diária (novo, local) e economia semanal (novo, seg. 8h05) | — | relatório e resumo |

## O que o estudo de uso mostrou (30 dias de `state.db`, 2026-09-21)

- Por origem, em 90 dias: `cli` 178 M tokens de entrada — 1.515 sessões de 30 dias eram o smoke do
  stability-guard (`Responda exatamente: OK-…`, 25 M tokens no mês), reduzido a 6 h em 21/09; `cron`
  135 M, dos quais o ARCANO sozinho 53 M em 30 dias lendo `arcano-fabio-email-monitor.json` 1.981
  vezes (66 M caracteres) — o porteiro derrubou de 43–49 sessões por dia para 3; `whatsapp` 113 M,
  o uso real de Igor: 85 sessões em 30 dias, a maioria entre 150 e 500 mil tokens, 37 compactações.
- O que Igor pede pelo WhatsApp: links do YouTube, X e Instagram (439 pedidos citam vídeo em 90
  dias), pesquisa e relatório, INTEIA, jurídico (Fábio), doutorado, campanha, memória e grafos.
  Mediana do pedido: 36 caracteres; a sessão longa vem das ferramentas, não do pedido.
- Por ferramenta, no WhatsApp: 77% dos caracteres devolvidos vêm de resultados com 8 mil ou mais.
  `read_file` 5,6 M, `skill_view` 5,4 M (mediana 6,7 mil, p90 18,7 mil; `cofre-sonhos` aberta 106
  vezes), `terminal` 3,2 M, `search_files` 2,3 M, `web_extract` 2,0 M, Apify 1,9 M, `session_search`
  1,8 M em 41 resultados, `execute_code` 1,4 M. Daí as camadas de 22/09.
- Achado de implantação: o gancho do terminal recebe o `task_id` do contêiner, que o Hermes colapsa
  em `default`; o pedido guardado pela sessão nunca era achado (6 de 6 recortes "sem pedido
  vigente"). Agora `pedido_vigente('default')` devolve o último pedido só quando uma única sessão
  falou nos últimos 15 minutos; com duas (cron e WhatsApp), é ambíguo e o recorte não mexe.
- Segundo achado, na primeira noite em produção: numa sessão de subagente o `session_id` que o
  `pre_llm_call` recebe (`sa-0-…`) não é o que o `transform_tool_result` recebe; 13 de 13 buscas
  ficaram "sem pedido vigente" com o pedido guardado sob outro nome. O pedido agora é guardado por
  `session_id`, `task_id` e `turn_id`, e procurado nessa ordem. O plugin só recarrega com reinício
  do gateway; `scripts/jev_reiniciar_ocioso.py` (cópia em `rotinas/`) espera 15 min sem mensagem
  antes de reiniciar, para não derrubar uma conversa de Igor.
- Terceiro achado, medindo as camadas novas contra os resultados grandes reais (12 casos do
  `state.db`, 22/09): a camada de resultado não cortava nada. Duas causas, as duas corrigidas.
  O estado ia com o pedido inteiro (até 3.000 caracteres) e estourava o limite da chamada em 7
  dos 12 — agora vai com os últimos 800, que num prompt de cron são justamente a tarefa. E a
  regra "essencial ≥ 0,90 com vizinhas", que serve à leitura de arquivo, nunca dispara em texto
  da web: das 63 partes classificadas, 50 vieram `essencial` entre 0,50 e 0,67 e nenhuma passou
  de 0,90. Passou a valer a CLASSE: fica toda parte essencial, mais a primeira e a última; sem
  nenhuma essencial, nada é cortado. Depois da correção, 3 dos 12 casos recortam, 51 mil
  caracteres evitados no conjunto; os outros nove param em "economia pequena demais" (quase
  tudo é essencial) ou "nenhuma parte essencial". Custo por resultado grande: 13 chamadas,
  cerca de US$ 0,0007.
- Política das seções de skill: o Jev disse `essencial` a 17 de 22 seções de `cofre-sonhos`, 13
  delas com confiança de 0,38 a 0,77. Vale a mesma regra da leitura: ficam as fortes (≥ 0,90), o
  título e a seção de quando usar; sem forte, as três do topo.

## Os seis fluxos do quadro "5 casos de uso do JEV" (desde 23/09/2026)

Fonte: os diagramas do quadro de aula (`fluxos_jev_mermaid_pt.md`, guia em PDF). Em todos o JEV
ocupa o mesmo lugar — o ponto em que o sistema decide o que acontece em seguida — e a decisão
**muda o fluxo**. Os `jev_workflows` de 22/09 davam só a sugestão (consultivos, nunca agem); os
módulos abaixo fecham cada fluxo com o que acontece depois. Motor comum: `jev_hermes/ciclo.py`.

| fluxo | módulo | o que o código decide | o que o Jev decide | o que acontece depois |
|---|---|---|---|---|
| 1 avaliações | `avaliacao.py` | faltas objetivas lidas da saída de teste e do diff que o harness observou; mesmas faltas duas vezes → pessoa | critérios de aceite contra a evidência (via `workflows.judge`) | aprovado; refazer com as faltas devolvidas ao agente e o modelo um nível acima; ou aviso a Igor |
| 2 agentes | `agentes.py` | guardas: testar só código novo, revisar só o que passou, concluir só com teste + revisão + judge | quem trabalha agora, entre as funções permitidas | o agente escolhido roda (Claude Code); testador é o harness |
| 3 modelos | `modelos.py` | escalada por falha; orçamento (desce de nível ou para) | o tipo de trabalho da subtarefa | `claude -p` com o modelo e o esforço do nível |
| 4 triagem | `triagem.py` + caixa vigiada | cortes 0,90 (age) e 0,50 (confira); idempotência; lembrete único | categoria pelo que o item pede + sentinela, no mesmo pedido | cartão no kanban (incidente, oportunidade com acompanhamento, pendência) e alerta |
| 5 bancada | `bancada.py` | mesmas tarefas, pasta nova, verificador oculto depois, IC95 | — (a comparação é conta) | relatório com as 5 medidas em `estado/bancada/` |
| 6 ciclo | `agenda.py` + plugin `jev-fluxos` | guardas: reservar só com escolha; concluir só com evento lido como `confirmed`; reconfere o horário antes | leitura do pedido, resposta livre de Igor, próxima ação quando há mais de uma | pergunta a Igor com as opções; reserva no Google Agenda sem convidados |

Níveis de modelo (fluxo 3): Haiku é proibido nos projetos de Igor, então pequeno = Sonnet com
esforço baixo, especialista = Opus, fronteira = Fable. Custos do `claude -p` são nominais (a
assinatura Max não cobra por chamada), mas são a medida comparável entre arquiteturas.

Isolamento (`isolamento.py`, com `bwrap`): o código que o agente escreve roda sem ver o resto da
máquina. Os testes que o harness roda não têm rede; o `claude` do agente tem rede (fala com a API)
e a própria configuração, mas /root e /tmp viram diretórios vazios em memória, e só a pasta da
tarefa aceita gravação. Conferido na VPS com um teste que tentava ler `~/.hermes/.env` (bloqueado)
e gravar em /root (a gravação caiu no diretório temporário e sumiu). O sandbox nativo do Claude
Code não roda neste servidor (o seccomp dele falha em `setgroups`), por isso o bwrap por fora.

Critério de conclusão: o juiz só aprova o que o harness observa. Por isso o programador acrescenta
testes que provam o pedido (viram evidência) e relata apenas o que aparece nas mudanças; relato
com verificações feitas à mão é lido como "insuficiente" e vai para uma pessoa, como deve.

Validação de implantação (23/09): 147 testes offline na VPS; ao vivo, o roteador de modelos pôs
"classificar 30 e-mails" no pequeno, "corrigir função" no especialista e "planejar migração" na
fronteira; o ciclo de agenda leu "semana que vem à tarde", achou três horários livres reais e,
com "nenhum desses", ofereceu outros dias (nada reservado; a chamada de reserva foi conferida em
`--dry-run`); a triagem criou e arquivou um cartão de teste em `engenharia-inteia`.
Backup: `/root/backups/jev-fluxos-20260923T062122Z` (e `jev-isolamento-20260923T065006Z`).

Depois, ao vivo: o ciclo de agenda reservou um evento real (segunda 28/09, 8h, sem convidados, com a
marca `jev_ciclo`), leu-o de volta como `confirmed` e o evento de teste foi apagado. A caixa
vigiada nova rodou 10 vezes na manhã de 23/09: 2 alertas, o fluxo 4 classificou cada e-mail novo
e não abriu cartão (nenhum chegou a 0,90), US$ 0,0014 de Jev somado.

Bancada (fluxo 5), 4 tarefas × 2 arquiteturas por rodada, cada rodada corrigindo o que a anterior
mostrou:

| rodada | o que corrigiu | código certo (verificador oculto) | concluiu sem pessoa (esteira / jev) |
|---|---|---|---|
| 4 | comando de teste no contexto do agente | 7/8 | 1/4 / 1/4 |
| 5 | critério serve a pesquisa; relato só do que o diff mostra; tarefa sem ambiguidade | 8/8 | 2/4 / 1/4 |
| 7 | isolamento, limite da assinatura, trilha da avaliação | 8/8 | 2/4 / 2/4 |
| 8 | diff sem `__pycache__`; arquivos citados viram evidência | 8/8 | 2/4 / 3/4 |

(A rodada 6 não mediu nada: o Opus bateu no limite de sessão da assinatura, o que levou à regra do
limite.) Na rodada 8 a arquitetura Jev custou em média US$ 2,03 nominais contra 1,55 da esteira,
por uma volta extra no CPF. Com n = 4 por arquitetura, a comparação é **inconclusiva** (IC95 se
sobrepõem); para separar as arquiteturas são precisas repetições. A refatoração segue pedindo
uma pessoa nas duas: repetido sem cache, o juiz dá 0,79–0,91 ao mesmo diff correto (ruído de
±0,05 em torno de 0,85), a faixa "confira" dos diagramas. O corte de 0,90 fica como está.

## Segurança e falhas

- Todo porteiro falha para **acordar**: se algo quebrar, o job roda como antes.
- Toda camada falha para **não mudar nada**.
- E-mail novo de cliente nunca é vetado pelo Jev; o Jev só anota.
- Credenciais são mascaradas antes de qualquer envio; o registro guarda hash, tamanho, classes e custo, nunca o texto.
- Tetos: US$ 0,50 por dia e US$ 5,00 por mês (`jev.env`). Chegando ao teto, tudo segue sem o Jev.

## O contexto do porteiro também é pago

Primeira execução agendada do boletim com porteiro (22/09, 7h): 86 itens coletados, 24
descartados pelo Jev, 15 no contexto, US$ 0,00077 de Jev. O agente entregou o PDF com 12
eventos e não saiu procurando notícia. Mas o prompt foi de 3.731 para 20.869 caracteres, e o
que se poupou em busca voltou pelo prompt: o dia fechou em 62 mil tokens de entrada, o mesmo
da véspera sem porteiro, com 47 chamadas de ferramenta contra 71 (queda de 34%).

Essa primeira conta somava o dia inteiro, que inclui outro job de cron. Medindo só as sessões
do boletim (`rotinas/jev_comparar_job.py 7e5e2b895040`), a execução com porteiro custou 37 mil
tokens de entrada contra uma média de 123 mil nas cinco anteriores e 21 chamadas de ferramenta
contra 38. A ressalva honesta: a véspera sozinha custou 31 mil, abaixo da execução com
porteiro — a variância entre dias é grande e uma execução não fecha a conta.

A lição vale para todo porteiro que injeta candidatos: o contexto é reenviado a cada volta de
ferramenta. O boletim passou a 15 itens com trecho de 180 caracteres, e o contexto caiu de 18
para 11 mil. Título, fonte, hora e link bastam para escolher o que abrir — o texto inteiro já
foi lido pelo Jev na triagem. A tese ficou como estava, com 5 artigos e resumo de 900
caracteres (contexto de 7,2 mil): o problema é o número de itens, não o tamanho de cada um.

A tese acadêmica rodou às 11h do mesmo dia, já com o contexto enxuto, e é a primeira medida
limpa do ganho. Comparada às 15 execuções anteriores do mesmo job:

| | antes (média de 15) | 22/09 com porteiro |
|---|---|---|
| prompt | 13.516 caracteres | 20.735 |
| tokens de entrada | 82.519 | 35.450 |
| chamadas de ferramenta | 25 | 5 |

O porteiro coletou 32 candidatos no Crossref e no OpenAlex, o Jev aprovou 12 e mandou 5 ao
contexto. O agente abriu dois deles e escreveu a ficha; não fez uma única busca para descobrir
artigo. Os 7,2 mil caracteres a mais de prompt compraram 47 mil tokens de entrada a menos.

O custo de Jev registrado nessa execução foi zero porque as mesmas fichas já haviam sido
classificadas nos testes manuais do dia e vieram do cache. Uma execução fria de 32 candidatos
com duas perguntas custa cerca de US$ 0,003.

## Medir uma implantação nova

Porteiro novo só prova valor na execução agendada, não na manual. `scripts/jev_observar_porteiros.py`
(cópia em `rotinas/`) espera a próxima execução de cada job e escreve em
`estado/primeiras-execucoes.md` a decisão do porteiro, o tamanho do prompt e quantas buscas na web
o agente ainda fez — a medida de o porteiro ter mesmo substituído a descoberta. Suba-o solto do
terminal, senão ele morre com a sessão de SSH:

```sh
systemd-run --unit=jev-observar-porteiros --collect /usr/bin/python3 /root/.hermes/scripts/jev_observar_porteiros.py
```

Passada a primeira execução, `rotinas/jev_comparar_job.py <id do job>` põe lado a lado as
sessões daquele job — prompt, tokens de entrada, ferramentas — e tira a média do antes e do
depois. Medir por dia mistura jobs e engana; medir por job é a conta certa.

O agendador do Hermes usa `America/Sao_Paulo` (`config.yaml`), não UTC: `0 7 * * *` é 10h UTC.

## Operar

```sh
ssh hermes
python3 /root/.hermes/integrations/jev/jev_hermes/nucleo.py          # gasto, tetos, provedores
python3 /root/.hermes/integrations/jev/jev_hermes/medir.py --gravar  # medição
touch /root/.hermes/integrations/jev/DESLIGADO                         # desliga todo uso do Jev, sem reiniciar
rm /root/.hermes/integrations/jev/DESLIGADO                            # religa
```

Rollback completo: `/root/backups/jev-hermes-20260921T030919Z` (config.yaml, jobs.json,
plugin jev-advisor v2, HERMES.md, scripts originais). Para voltar um job ao script antigo:
`hermes cron edit <id> --script <antigo>` (ARCANO e monitor: `--script ""`; radar:
`ai_intelligence_tick.py`; watchdog: `fabio_osorio_urgent_watch.py`).

Do lado do PC, antes de confiar no que este repositório diz:

```sh
python hermes/infra/conferir_sincronia.py          # o que roda na VPS é o que está versionado?
python hermes/infra/conferir_sincronia.py --puxar  # traz as divergências para revisar e versionar
```

Em 22/09/2026 uma camada inteira (a rota de ferramenta) foi escrita direto na VPS e ficou fora do
repositório e sem teste. Quem edita lá pode ter razão; o que não pode é a divergência passar
despercebida. Sai com código 1 quando algo diverge ou não foi publicado.

## Testes

`python -m pytest hermes/tests -q` — offline, transporte simulado, nenhuma chamada paga.
