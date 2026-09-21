# Instruções do projeto JEV

- Para achar qualquer arquivo, função ou relação entre partes do projeto, comece por `MAPA.md` (índice, grafos, experimentos e testes; símbolos em `mapa/simbolos.md`, grafo em `mapa/grafo.json`). Depois de criar, mover ou apagar arquivos, regenere com `python mapa/gerar_mapa.py --verificar`.
- A chave OpenRouter está somente no arquivo local `.env`, ignorado pelo Git. Nunca exibir, registrar em logs, copiar para documentação ou versionar a chave.
- O orçamento TOTAL acumulado autorizado para testes OpenRouter é de US$ 5,00, não por execução. Não ultrapassar esse valor.
- Antes de chamadas pagas, implementar controle persistente de gastos e verificar preços e custo máximo previsto por chamada, incluindo limites de tokens. Interromper antes de esgotar o saldo; se não for possível garantir o teto, não executar chamadas pagas.
- A variável OPENROUTER_TEST_BUDGET_USD documenta o teto; sozinha não aplica um limite no provedor.

## Integração assistida medida

- No Claude Code, os hooks de leitura, busca e sentinela (`integracao/camadas/`) já
  filtram o que entra no contexto; para vários arquivos candidatos, use a skill `/jev-ler`
  (`integracao/camadas/ler.py`). Medição em `docs/CAMADAS-CLAUDE-CODE.md`.
- Para usar JEV antes de carregar arquivos no contexto, siga `integracao/USO-CODEX.md`
  e `integracao/ler_contexto.py`. Priorize busca local; preserve referências de todos
  os candidatos; use dois trechos para fonte única e três para resposta repartida ou
  estrutura desconhecida. Confiança baixa não aborta; falha técnica ou sentinela alerta devolve tudo.

- Laboratório e hook usam `executor/shared.py` e a carteira existente em `runs/ledger.sqlite3`.
  Não criar transporte pago paralelo nem estimar teto financeiro por caracteres.
- Ferramentas `jev_assist` e `jev_rank_context` são auxiliares para classificação fechada
  e ordenação de trechos. Preservar todos os IDs/fontes; nunca delegar autorização ou
  escolha de esforço/modelo ao JEV. Não exportar material privado sem autorização.
- Em avaliação, registrar hipóteses antes das chamadas, congelar corpus/rubricas e
  separar texto sintético, fonte real, tráfego de produção e simulação de transporte.
- E15/E16 autorizam apenas apoio à leitura. Evidência sobre código é experimental.
  Economia do Astra permanece não medida. `jev_record_review` registra revisão posterior
  identificando humano, assistente ou verificação determinística.
