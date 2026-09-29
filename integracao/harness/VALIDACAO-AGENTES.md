# Validação da camada de agentes — 21/09/2026

API v1 e MCP v2 implementados sobre o mesmo executor da interface HTML. Contrato descoberto ao vivo: **26 operações em 16 ferramentas e a bancada de julgamentos**. Skill `jev-harness` instalada no diretório de skills do Codex; não depende de recarregar o MCP para usar o CLI.

## Evidência observada

- Bootstrap por CLI iniciou o servidor local sem navegador; histórico anterior preservado.
- Manifesto e status lidos pelo cliente JSON. Status não inclui saídas completas dos jobs.
- Ensaio real pré-registrado via preview → submit → wait → submit idêntico: job `ea9efd2cc27d06a7`, resultado `contradito`, confiança 0,99. A fonte dizia que o pagamento estava agendado, ainda não executado.
- Recibo `edeb60bf-5419-4faf-8ebd-a274c93393bc`: TypeSafe, sucesso, 424 tokens de entrada e 48 de saída, 17.808 nanodólares = **US$ 0,000017808**. O reenvio retornou o mesmo job/recibo; não criou uma segunda execução.
- O ensaio é sintético e valida integração/idempotência, não precisão em produção nem economia do Codex.

## Testes de regressão

A suíte cobre painel, ponte, CLI, Every, MCP e contrato para agentes. Os testes específicos verificam: cinco submissões simultâneas idênticas produzem um job; conflito de chave; reenvio após reinício; preservação da interrupção sem execução automática; preview sem envio; rejeição de comando arbitrário; carteira indisponível; recuperação da mesma inferência mesmo após bloqueio do saldo; ausência de texto bruto no registro idempotente; pausa; cancelamento; logs paginados; consulta de IDs fora dos 60 recentes; envelopes estruturados e guia MCP.

```powershell
python -m unittest integracao.harness.test_agents integracao.harness.test_painel integracao.harness.test_ponte integracao.harness.test_componentes -v
```

Os testes com modelo simulado estão explicitamente isolados. A execução real citada acima foi feita fora dessa suíte, pela carteira compartilhada existente. Persistem avisos de conexões SQLite no diagnóstico financeiro compartilhado; não são falhas de assertions nem novas carteiras.
