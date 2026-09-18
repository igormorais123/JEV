# Instruções do projeto JEV

- A chave OpenRouter está somente no arquivo local `.env`, ignorado pelo Git. Nunca exibir, registrar em logs, copiar para documentação ou versionar a chave.
- O orçamento TOTAL acumulado autorizado para testes OpenRouter é de US$ 5,00, não por execução. Não ultrapassar esse valor.
- Antes de chamadas pagas, implementar controle persistente de gastos e verificar preços e custo máximo previsto por chamada, incluindo limites de tokens. Interromper antes de esgotar o saldo; se não for possível garantir o teto, não executar chamadas pagas.
- A variável OPENROUTER_TEST_BUDGET_USD documenta o teto; sozinha não aplica um limite no provedor.
