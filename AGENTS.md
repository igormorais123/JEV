# Instruções do projeto JEV

- A chave OpenRouter está somente no arquivo local `.env`, ignorado pelo Git. Nunca exibir, registrar em logs, copiar para documentação ou versionar a chave.
- O orçamento TOTAL acumulado autorizado para testes OpenRouter é de US$ 5,00, não por execução. Não ultrapassar esse valor.
- Antes de chamadas pagas, implementar controle persistente de gastos e verificar preços e custo máximo previsto por chamada, incluindo limites de tokens. Interromper antes de esgotar o saldo; se não for possível garantir o teto, não executar chamadas pagas.
- A variável OPENROUTER_TEST_BUDGET_USD documenta o teto; sozinha não aplica um limite no provedor.

## Integração assistida medida

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
