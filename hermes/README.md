# O Jev no Hermes da VPS

Implantado em 21/09/2026. Fonte versionada aqui; cópia viva na VPS (`ssh hermes`). Regra de
fundo, do estudo: o Jev decide, não escreve; o ganho em dinheiro aparece quando ele decide
**antes** da etapa cara — o que entra no contexto, se o modelo principal precisa acordar.

## Onde está cada peça

| peça | na VPS | o que faz |
|---|---|---|
| núcleo | `/root/.hermes/integrations/jev/jev_hermes/nucleo.py` | chaves, OpenRouter com reserva na TypeSafe, redação de credenciais, cache de 3 dias, teto, registro sem conteúdo |
| chaves | `/root/.hermes/integrations/jev/jev.env` (0600) | `OPENROUTER_API_KEY`, `TYPESAFE_API_KEY` copiadas do cofre do PC; tetos |
| camadas | `/root/.hermes/plugins/jev-camadas/` + `jev_hermes/camadas.py` | tema/risco do pedido, recorte de `read_file`, ordem de busca, sentinela em conteúdo externo, causa de erro no terminal |
| ferramenta | `/root/.hermes/plugins/jev-advisor/` (v3) | `jev_advisor` para o modelo, com modo `lote` (até 60 textos) |
| porteiros | `/root/.hermes/scripts/jev_gate_*.py` | decidem se o job de cron acorda o modelo principal |
| rotinas | `/root/.hermes/scripts/jev_rotina_*.py` | jobs sem modelo principal: caixa vigiada, agenda, saúde do coletor, medição |
| skill | `/root/.hermes/skills/jev/SKILL.md` | quando e como delegar ao Jev |
| contrato | `/root/HERMES.md`, linha "Sistema 1 é do Jev" | Jev por padrão em toda decisão fechada |
| medição | `jev_hermes/medir.py` → `estado/RELATORIO.md` | recalculada dos registros, diária |

## Jobs de cron com o Jev

| job | antes | agora |
|---|---|---|
| ARCANO — e-mails de Fábio (30 min) | Sol acordava 48×/dia, prompt ~71 KB; 43 de 50 em `[SILENT]` | código compara IDs com o estado; só acorda com e-mail novo, já com triagem do Jev |
| Monitor Fábio — WhatsApp (3×/dia) | 49 de 50 em silêncio | painel + cursor por código, conversa nova pelo Jev (dorme só com social ≥ 0,99) |
| Revisão diária de e-mail | Sol listava e abria cabeçalhos | Jev tria; dorme se tudo for descartável; acorda com a lista pronta |
| Radar de IA (diário) | Sol lia todo candidato | Jev lê contra as missões; tudo trivial → descarte pelo helper, sem Sol |
| Watchdog urgente Fábio | 22 palavras-chave | Jev decide relevância; palavras só se o Jev falhar |
| Caixa vigiada (novo, 30 min, 7–22h) | — | alerta imediato de e-mail que pede ação, cliente, jurídico, financeiro |
| Agenda do dia (novo, 7h) | — | compromissos de hoje com marca de preparo |
| Saúde do coletor WhatsApp (novo, 8h) | — | avisa coletor parado ou deslogado (regra, sem Jev) |
| Medição diária (novo, local) e economia semanal (novo, seg. 8h05) | — | relatório e resumo |

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

## Testes

`python -m pytest hermes/tests -q` — offline, transporte simulado, nenhuma chamada paga.
