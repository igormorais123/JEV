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
| rotinas | `/root/.hermes/scripts/jev_rotina_*.py` | jobs sem modelo principal: caixa vigiada, agenda, saúde do coletor, medição |
| ponte OpenAI | `hermes-jev-ponte.service`, `172.17.0.1:20145` (só a rede Docker) | traduz chat do OmniRoute para decisão do Jev; a chave vem no Bearer. No OmniRoute: nós `jev-openrouter` e `jev-typesafe`, combo `jev` |
| skill | `/root/.hermes/skills/jev/SKILL.md` | quando e como delegar ao Jev |
| contrato | `/root/HERMES.md`, linha "Sistema 1 é do Jev" | Jev por padrão em toda decisão fechada |
| medição | `jev_hermes/medir.py` → `estado/RELATORIO.md` | recalculada dos registros, diária |

## Modelo principal e economia da cota (desde 21/09/2026)

- Conversa com Igor: `gpt-6-astra`, esforço baixo, conta Pro (igor@inteia.com.br) primeiro no pool
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
| Checklist de documento (sob demanda) | Astra lia o contrato inteiro | `jev_hermes/checklist.py` (porte da R50): uma chamada, semáforo por item; o Astra lê só vermelho e amarelo |
| Tese — parágrafo diário (11h, `8f2260d9fe4a`) | Astra acordava com a skill `research` inteira e procurava sozinho: 9 `web_search`, 21 `web_extract`, 19 `execute_code`; 100 mil tokens por dia | `jev_gate_tese_diaria.py`: Crossref e OpenAlex por pilar do dia (2024+), fora da wiki, Jev lê título e resumo contra a tese; o agente acorda com os 5 melhores e confirma só o DOI escolhido |
| Boletim Taguatinga e Celina Leão (7h, `7e5e2b895040`) | Astra descobria as notícias sozinho; 110 mil tokens por edição | `jev_gate_boletim_taguatinga.py`: Google Notícias (RSS, 24 h) das duas pautas; o Jev separa Taguatinga-DF da do Tocantins e fato de ruído; o agente acorda com a lista triada e só abre os links listados |
| Painel da manhã (novo, 7h) | — | agenda + demandas do escritório + pendências do WhatsApp pessoal (quem espera Igor, promessas sem entrega — `jev_hermes/pendencias.py`); o Jev pontua urgência e preparo; uma prioridade e o próximo gesto |
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
- Política das seções de skill: o Jev disse `essencial` a 17 de 22 seções de `cofre-sonhos`, 13
  delas com confiança de 0,38 a 0,77. Vale a mesma regra da leitura: ficam as fortes (≥ 0,90), o
  título e a seção de quando usar; sem forte, as três do topo.

## Segurança e falhas

- Todo porteiro falha para **acordar**: se algo quebrar, o job roda como antes.
- Toda camada falha para **não mudar nada**.
- E-mail novo de cliente nunca é vetado pelo Jev; o Jev só anota.
- Credenciais são mascaradas antes de qualquer envio; o registro guarda hash, tamanho, classes e custo, nunca o texto.
- Tetos: US$ 0,50 por dia e US$ 5,00 por mês (`jev.env`). Chegando ao teto, tudo segue sem o Jev.

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
