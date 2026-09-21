# integracao/jev_router/

Roteador de prompts: política, orçamento, redação de credenciais, cliente do provedor e CLI.

← [MAPA.md](../../MAPA.md) · pasta acima: [integracao](../../mapa/pastas/integracao.md) · abrir a pasta: [integracao/jev_router/](../../integracao/jev_router)

## Arquivos

| arquivo | tipo | tamanho | descrição |
|---|---|---:|---|
| [__init__.py](../../integracao/jev_router/__init__.py) | código | 1 l. | Roteador de trabalho baseado no Jev: classifica o pedido antes de gastar modelo caro. |
| [cli.py](../../integracao/jev_router/cli.py) | código | 50 l. | Linha de comando do roteador, para quem não tem hook: Codex, scripts, ou o próprio agente. |
| [cliente.py](../../integracao/jev_router/cliente.py) | código | 107 l. | Chamada ao endpoint de decisões do Jev, no formato que um hook pode usar. |
| [orcamento.py](../../integracao/jev_router/orcamento.py) | código | 90 l. | Controle persistente de gasto do roteador, separado do livro-caixa dos experimentos. |
| [politica.py](../../integracao/jev_router/politica.py) | código | 118 l. | O que o Jev decide nos fluxos do Claude Code e do Codex, e o que ele não decide. |
| [redacao.py](../../integracao/jev_router/redacao.py) | código | 53 l. | Mascara segredo antes de o pedido sair desta máquina. |
| [roteador.py](../../integracao/jev_router/roteador.py) | código | 127 l. | Orquestra a classificação: cache, chamada ao Jev, política e registro da decisão. |

## Grafo de imports e links

Nós em negrito são desta pasta; setas cheias são imports, tracejadas são links de documento.

```mermaid
flowchart LR
  n_executor___init___py["executor/__init__.py"]
  n_executor_assist_py["executor/assist.py"]
  n_executor_credenciais_py["executor/credenciais.py"]
  n_executor_ledger_py["executor/ledger.py"]
  n_executor_pricing_py["executor/pricing.py"]
  n_executor_shared_py["executor/shared.py"]
  n_integracao_avaliacao_com_contexto_py["integracao/avaliacao/com_contexto.py"]
  n_integracao_avaliacao_comandos_py["integracao/avaliacao/comandos.py"]
  n_integracao_avaliacao_rodar_py["integracao/avaliacao/rodar.py"]
  n_integracao_avaliacao_skills_py["integracao/avaliacao/skills.py"]
  n_integracao_avaliacao_variantes_py["integracao/avaliacao/variantes.py"]
  n_integracao_camadas_nucleo_py["integracao/camadas/nucleo.py"]
  n_integracao_hooks_jev_guarda_comando_py["integracao/hooks/jev_guarda_comando.py"]
  n_integracao_hooks_jev_prompt_router_py["integracao/hooks/jev_prompt_router.py"]
  n_integracao_jev_mcp_py["integracao/jev_mcp.py"]
  n_integracao_jev_router___init___py["<b>__init__.py</b>"]
  n_integracao_jev_router_cli_py["<b>cli.py</b>"]
  n_integracao_jev_router_cliente_py["<b>cliente.py</b>"]
  n_integracao_jev_router_orcamento_py["<b>orcamento.py</b>"]
  n_integracao_jev_router_politica_py["<b>politica.py</b>"]
  n_integracao_jev_router_redacao_py["<b>redacao.py</b>"]
  n_integracao_jev_router_roteador_py["<b>roteador.py</b>"]
  n_integracao_tests_test_camadas_py["integracao/tests/test_camadas.py"]
  n_integracao_tests_test_redacao_py["integracao/tests/test_redacao.py"]
  n_integracao_tests_test_roteador_py["integracao/tests/test_roteador.py"]
  n_laboratorio_nucleo_py["laboratorio/nucleo.py"]
  n_laboratorio_r31_r37_segunda_leva_py["laboratorio/r31_r37_segunda_leva.py"]
  n_executor_assist_py --> n_integracao_jev_router_redacao_py
  n_integracao_avaliacao_com_contexto_py --> n_integracao_jev_router___init___py
  n_integracao_avaliacao_com_contexto_py --> n_integracao_jev_router_cliente_py
  n_integracao_avaliacao_comandos_py --> n_integracao_jev_router___init___py
  n_integracao_avaliacao_comandos_py --> n_integracao_jev_router_cliente_py
  n_integracao_avaliacao_rodar_py --> n_integracao_jev_router___init___py
  n_integracao_avaliacao_rodar_py --> n_integracao_jev_router_politica_py
  n_integracao_avaliacao_rodar_py --> n_integracao_jev_router_roteador_py
  n_integracao_avaliacao_skills_py --> n_integracao_jev_router___init___py
  n_integracao_avaliacao_skills_py --> n_integracao_jev_router_cliente_py
  n_integracao_avaliacao_variantes_py --> n_integracao_jev_router___init___py
  n_integracao_avaliacao_variantes_py --> n_integracao_jev_router_cliente_py
  n_integracao_camadas_nucleo_py --> n_integracao_jev_router___init___py
  n_integracao_camadas_nucleo_py --> n_integracao_jev_router_cliente_py
  n_integracao_camadas_nucleo_py --> n_integracao_jev_router_redacao_py
  n_integracao_hooks_jev_guarda_comando_py --> n_integracao_jev_router___init___py
  n_integracao_hooks_jev_guarda_comando_py --> n_integracao_jev_router_cliente_py
  n_integracao_hooks_jev_prompt_router_py --> n_integracao_jev_router___init___py
  n_integracao_hooks_jev_prompt_router_py --> n_integracao_jev_router_politica_py
  n_integracao_hooks_jev_prompt_router_py --> n_integracao_jev_router_redacao_py
  n_integracao_hooks_jev_prompt_router_py --> n_integracao_jev_router_roteador_py
  n_integracao_jev_mcp_py --> n_integracao_jev_router_redacao_py
  n_integracao_jev_router_cli_py --> n_integracao_jev_router_orcamento_py
  n_integracao_jev_router_cli_py --> n_integracao_jev_router_politica_py
  n_integracao_jev_router_cli_py --> n_integracao_jev_router_roteador_py
  n_integracao_jev_router_cliente_py --> n_executor___init___py
  n_integracao_jev_router_cliente_py --> n_executor_credenciais_py
  n_integracao_jev_router_cliente_py --> n_executor_ledger_py
  n_integracao_jev_router_cliente_py --> n_executor_pricing_py
  n_integracao_jev_router_cliente_py --> n_executor_shared_py
  n_integracao_jev_router_cliente_py --> n_integracao_jev_router_orcamento_py
  n_integracao_jev_router_cliente_py --> n_integracao_jev_router_redacao_py
  n_integracao_jev_router_roteador_py --> n_integracao_jev_router_cliente_py
  n_integracao_jev_router_roteador_py --> n_integracao_jev_router_politica_py
  n_integracao_jev_router_roteador_py --> n_integracao_jev_router_redacao_py
  n_integracao_tests_test_camadas_py --> n_integracao_jev_router___init___py
  n_integracao_tests_test_camadas_py --> n_integracao_jev_router_orcamento_py
  n_integracao_tests_test_redacao_py --> n_integracao_jev_router___init___py
  n_integracao_tests_test_redacao_py --> n_integracao_jev_router_redacao_py
  n_integracao_tests_test_roteador_py --> n_integracao_jev_router___init___py
  n_integracao_tests_test_roteador_py --> n_integracao_jev_router_politica_py
  n_integracao_tests_test_roteador_py --> n_integracao_jev_router_roteador_py
  n_laboratorio_nucleo_py --> n_integracao_jev_router_redacao_py
  n_laboratorio_r31_r37_segunda_leva_py --> n_integracao_jev_router_redacao_py
```

## Ligações e conteúdo de cada arquivo

### __init__.py

- **é usado por** — import: [`integracao/avaliacao/com_contexto.py`](../../integracao/avaliacao/com_contexto.py), [`integracao/avaliacao/comandos.py`](../../integracao/avaliacao/comandos.py), [`integracao/avaliacao/rodar.py`](../../integracao/avaliacao/rodar.py), [`integracao/avaliacao/skills.py`](../../integracao/avaliacao/skills.py), [`integracao/avaliacao/variantes.py`](../../integracao/avaliacao/variantes.py), [`integracao/camadas/nucleo.py`](../../integracao/camadas/nucleo.py), [`integracao/hooks/jev_guarda_comando.py`](../../integracao/hooks/jev_guarda_comando.py), [`integracao/hooks/jev_prompt_router.py`](../../integracao/hooks/jev_prompt_router.py), [`integracao/tests/test_camadas.py`](../../integracao/tests/test_camadas.py), [`integracao/tests/test_redacao.py`](../../integracao/tests/test_redacao.py), [`integracao/tests/test_roteador.py`](../../integracao/tests/test_roteador.py)
- **parecidos (julgados pelo Jev)** — [`integracao/avaliacao/auditar_producao.py`](../../integracao/avaliacao/auditar_producao.py) (complementar, 0.29), [`integracao/jev_router/orcamento.py`](../../integracao/jev_router/orcamento.py) (complementar, 0.23)

### cli.py

- **usa** — import: [`integracao/jev_router/orcamento.py`](../../integracao/jev_router/orcamento.py), [`integracao/jev_router/politica.py`](../../integracao/jev_router/politica.py), [`integracao/jev_router/roteador.py`](../../integracao/jev_router/roteador.py)
- **é usado por** — citação: [`integracao/README.md`](../../integracao/README.md), [`laboratorio/r18-perguntas.json`](../../laboratorio/r18-perguntas.json), [`laboratorio/r38-dois-trechos-em-lista-bruto.json`](../../laboratorio/r38-dois-trechos-em-lista-bruto.json), [`laboratorio/r38-dois-trechos-em-lista.json`](../../laboratorio/r38-dois-trechos-em-lista.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json), [`laboratorio/r44-candidato-envenenado-bruto.json`](../../laboratorio/r44-candidato-envenenado-bruto.json), [`laboratorio/r44-candidato-envenenado.json`](../../laboratorio/r44-candidato-envenenado.json)
- **chama de outros arquivos** — [`orcamento.custo_maximo_por_chamada_usd`](../../integracao/jev_router/orcamento.py#L34), [`orcamento.situacao`](../../integracao/jev_router/orcamento.py#L55), [`politica.texto_para_o_agente`](../../integracao/jev_router/politica.py#L109), [`roteador.classificar`](../../integracao/jev_router/roteador.py#L81)
- **parecidos (julgados pelo Jev)** — [`integracao/avaliacao/auditar_producao.py`](../../integracao/avaliacao/auditar_producao.py) (complementar, 0.29), [`integracao/instalar.py`](../../integracao/instalar.py) (complementar, 0.21), [`integracao/camadas/saida.py`](../../integracao/camadas/saida.py) (complementar, 0.20)
- **conteúdo** — [main](../../integracao/jev_router/cli.py#L18) (l. 18)

### cliente.py

- **usa** — import: [`executor/__init__.py`](../../executor/__init__.py), [`executor/credenciais.py`](../../executor/credenciais.py), [`executor/ledger.py`](../../executor/ledger.py), [`executor/pricing.py`](../../executor/pricing.py), [`executor/shared.py`](../../executor/shared.py), [`integracao/jev_router/orcamento.py`](../../integracao/jev_router/orcamento.py), [`integracao/jev_router/redacao.py`](../../integracao/jev_router/redacao.py); citação: [`executor/runner.py`](../../executor/runner.py)
- **é usado por** — import: [`integracao/avaliacao/com_contexto.py`](../../integracao/avaliacao/com_contexto.py), [`integracao/avaliacao/comandos.py`](../../integracao/avaliacao/comandos.py), [`integracao/avaliacao/skills.py`](../../integracao/avaliacao/skills.py), [`integracao/avaliacao/variantes.py`](../../integracao/avaliacao/variantes.py), [`integracao/camadas/nucleo.py`](../../integracao/camadas/nucleo.py), [`integracao/hooks/jev_guarda_comando.py`](../../integracao/hooks/jev_guarda_comando.py), [`integracao/jev_router/roteador.py`](../../integracao/jev_router/roteador.py); citação: [`laboratorio/r17-economia-de-contexto.json`](../../laboratorio/r17-economia-de-contexto.json), [`laboratorio/r18-escala.json`](../../laboratorio/r18-escala.json), [`laboratorio/r18-perguntas.json`](../../laboratorio/r18-perguntas.json), [`laboratorio/r20-k-adaptativo.json`](../../laboratorio/r20-k-adaptativo.json), [`laboratorio/r20-perguntas.json`](../../laboratorio/r20-perguntas.json), [`laboratorio/r38-dois-trechos-em-lista-bruto.json`](../../laboratorio/r38-dois-trechos-em-lista-bruto.json), [`laboratorio/r38-dois-trechos-em-lista.json`](../../laboratorio/r38-dois-trechos-em-lista.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json), [`laboratorio/r43-tamanho-da-lista-bruto.json`](../../laboratorio/r43-tamanho-da-lista-bruto.json), [`laboratorio/r43-tamanho-da-lista.json`](../../laboratorio/r43-tamanho-da-lista.json), [`laboratorio/r44-candidato-envenenado-bruto.json`](../../laboratorio/r44-candidato-envenenado-bruto.json), [`laboratorio/r44-candidato-envenenado.json`](../../laboratorio/r44-candidato-envenenado.json), [`laboratorio/r45-lista-nas-duas-ordens-bruto.json`](../../laboratorio/r45-lista-nas-duas-ordens-bruto.json), [`laboratorio/r45-lista-nas-duas-ordens.json`](../../laboratorio/r45-lista-nas-duas-ordens.json)
- **chama de outros arquivos** — [`credenciais.chave`](../../executor/credenciais.py#L71), [`credenciais.provedor`](../../executor/credenciais.py#L59), [`ledger.Ledger`](../../executor/ledger.py#L32), [`pricing.load_prices`](../../executor/pricing.py#L18), [`pricing.usd_to_nusd`](../../executor/pricing.py#L74), [`shared.ask`](../../executor/shared.py#L125), [`orcamento.pode_gastar`](../../integracao/jev_router/orcamento.py#L70), [`orcamento.registrar`](../../integracao/jev_router/orcamento.py#L81), [`redacao.limpar`](../../integracao/jev_router/redacao.py#L43)
- **parecidos (julgados pelo Jev)** — [`executor/run_e5_provedores.py`](../../executor/run_e5_provedores.py) (complementar, 0.22), [`hermes/jev_hermes/nucleo.py`](../../hermes/jev_hermes/nucleo.py) (complementar, 0.21)
- **conteúdo** — [chave](../../integracao/jev_router/cliente.py#L29) (l. 29), [transporte_http](../../integracao/jev_router/cliente.py#L41) (l. 41), [perguntar](../../integracao/jev_router/cliente.py#L57) (l. 57; usado em 7)

### orcamento.py

- **usa** — citação: [`executor/ledger.py`](../../executor/ledger.py), [`executor/prices.json`](../../executor/prices.json)
- **é usado por** — import: [`integracao/jev_router/cli.py`](../../integracao/jev_router/cli.py), [`integracao/jev_router/cliente.py`](../../integracao/jev_router/cliente.py), [`integracao/tests/test_camadas.py`](../../integracao/tests/test_camadas.py); citação: [`integracao/camadas/verificar.py`](../../integracao/camadas/verificar.py), [`laboratorio/r17-economia-de-contexto.json`](../../laboratorio/r17-economia-de-contexto.json), [`laboratorio/r17_economia_de_contexto.py`](../../laboratorio/r17_economia_de_contexto.py), [`laboratorio/r18-escala.json`](../../laboratorio/r18-escala.json), [`laboratorio/r18-perguntas.json`](../../laboratorio/r18-perguntas.json), [`laboratorio/r20-k-adaptativo.json`](../../laboratorio/r20-k-adaptativo.json), [`laboratorio/r20-perguntas.json`](../../laboratorio/r20-perguntas.json), [`laboratorio/r38-dois-trechos-em-lista-bruto.json`](../../laboratorio/r38-dois-trechos-em-lista-bruto.json), [`laboratorio/r38-dois-trechos-em-lista.json`](../../laboratorio/r38-dois-trechos-em-lista.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json), [`laboratorio/r44-candidato-envenenado-bruto.json`](../../laboratorio/r44-candidato-envenenado-bruto.json), [`laboratorio/r44-candidato-envenenado.json`](../../laboratorio/r44-candidato-envenenado.json)
- **parecidos (julgados pelo Jev)** — [`laboratorio/conciliar_caixa.py`](../../laboratorio/conciliar_caixa.py) (complementar, 0.30), [`integracao/jev_router/__init__.py`](../../integracao/jev_router/__init__.py) (complementar, 0.23), [`executor/exportar_extrato.py`](../../executor/exportar_extrato.py) (complementar, 0.21)
- **conteúdo** — [custo_maximo_por_chamada_usd](../../integracao/jev_router/orcamento.py#L34) (l. 34; usado em 2), [_linhas](../../integracao/jev_router/orcamento.py#L40) (l. 40), [situacao](../../integracao/jev_router/orcamento.py#L55) (l. 55; usado em 1), [pode_gastar](../../integracao/jev_router/orcamento.py#L70) (l. 70; usado em 2), [registrar](../../integracao/jev_router/orcamento.py#L81) (l. 81; usado em 1)

### politica.py

- **é usado por** — import: [`integracao/avaliacao/rodar.py`](../../integracao/avaliacao/rodar.py), [`integracao/hooks/jev_prompt_router.py`](../../integracao/hooks/jev_prompt_router.py), [`integracao/jev_router/cli.py`](../../integracao/jev_router/cli.py), [`integracao/jev_router/roteador.py`](../../integracao/jev_router/roteador.py), [`integracao/tests/test_roteador.py`](../../integracao/tests/test_roteador.py); citação: [`laboratorio/r17-economia-de-contexto.json`](../../laboratorio/r17-economia-de-contexto.json), [`laboratorio/r17_economia_de_contexto.py`](../../laboratorio/r17_economia_de_contexto.py), [`laboratorio/r18-escala.json`](../../laboratorio/r18-escala.json), [`laboratorio/r18-perguntas.json`](../../laboratorio/r18-perguntas.json), [`laboratorio/r20-k-adaptativo.json`](../../laboratorio/r20-k-adaptativo.json), [`laboratorio/r20-perguntas.json`](../../laboratorio/r20-perguntas.json), [`laboratorio/r38-dois-trechos-em-lista-bruto.json`](../../laboratorio/r38-dois-trechos-em-lista-bruto.json), [`laboratorio/r38-dois-trechos-em-lista.json`](../../laboratorio/r38-dois-trechos-em-lista.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json), [`laboratorio/r43-tamanho-da-lista-bruto.json`](../../laboratorio/r43-tamanho-da-lista-bruto.json), [`laboratorio/r43-tamanho-da-lista.json`](../../laboratorio/r43-tamanho-da-lista.json), [`laboratorio/r44-candidato-envenenado-bruto.json`](../../laboratorio/r44-candidato-envenenado-bruto.json), [`laboratorio/r44-candidato-envenenado.json`](../../laboratorio/r44-candidato-envenenado.json), [`laboratorio/r45-lista-nas-duas-ordens-bruto.json`](../../laboratorio/r45-lista-nas-duas-ordens-bruto.json), [`laboratorio/r45-lista-nas-duas-ordens.json`](../../laboratorio/r45-lista-nas-duas-ordens.json)
- **parecidos (julgados pelo Jev)** — [`integracao/README.md`](../../integracao/README.md) (complementar, 0.34), [`laboratorio/q100/registro.py`](../../laboratorio/q100/registro.py) (complementar, 0.26), [`integracao/instalar.py`](../../integracao/instalar.py) (complementar, 0.26), [`integracao/avaliacao/amostrar.py`](../../integracao/avaliacao/amostrar.py) (complementar, 0.25), [`integracao/avaliacao/amostrar_com_contexto.py`](../../integracao/avaliacao/amostrar_com_contexto.py) (complementar, 0.21)
- **conteúdo** — [decidir](../../integracao/jev_router/politica.py#L84) (l. 84; usado em 2), [texto_para_o_agente](../../integracao/jev_router/politica.py#L109) (l. 109; usado em 3)

### redacao.py

- **é usado por** — import: [`executor/assist.py`](../../executor/assist.py), [`integracao/camadas/nucleo.py`](../../integracao/camadas/nucleo.py), [`integracao/hooks/jev_prompt_router.py`](../../integracao/hooks/jev_prompt_router.py), [`integracao/jev_mcp.py`](../../integracao/jev_mcp.py), [`integracao/jev_router/cliente.py`](../../integracao/jev_router/cliente.py), [`integracao/jev_router/roteador.py`](../../integracao/jev_router/roteador.py), [`integracao/tests/test_redacao.py`](../../integracao/tests/test_redacao.py), [`laboratorio/nucleo.py`](../../laboratorio/nucleo.py), [`laboratorio/r31_r37_segunda_leva.py`](../../laboratorio/r31_r37_segunda_leva.py); citação: [`integracao/README.md`](../../integracao/README.md), [`laboratorio/r17-economia-de-contexto.json`](../../laboratorio/r17-economia-de-contexto.json), [`laboratorio/r17_economia_de_contexto.py`](../../laboratorio/r17_economia_de_contexto.py), [`laboratorio/r20-k-adaptativo.json`](../../laboratorio/r20-k-adaptativo.json), [`laboratorio/r20-perguntas.json`](../../laboratorio/r20-perguntas.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json)
- **parecidos (julgados pelo Jev)** — [`executor/credenciais.py`](../../executor/credenciais.py) (complementar, 0.21)
- **conteúdo** — [limpar](../../integracao/jev_router/redacao.py#L43) (l. 43; usado em 9)

### roteador.py

- **usa** — import: [`integracao/jev_router/cliente.py`](../../integracao/jev_router/cliente.py), [`integracao/jev_router/politica.py`](../../integracao/jev_router/politica.py), [`integracao/jev_router/redacao.py`](../../integracao/jev_router/redacao.py); citação: [`.gitignore`](../../.gitignore)
- **é usado por** — import: [`integracao/avaliacao/rodar.py`](../../integracao/avaliacao/rodar.py), [`integracao/hooks/jev_prompt_router.py`](../../integracao/hooks/jev_prompt_router.py), [`integracao/jev_router/cli.py`](../../integracao/jev_router/cli.py), [`integracao/tests/test_roteador.py`](../../integracao/tests/test_roteador.py); citação: [`laboratorio/r17-economia-de-contexto.json`](../../laboratorio/r17-economia-de-contexto.json), [`laboratorio/r17_economia_de_contexto.py`](../../laboratorio/r17_economia_de_contexto.py), [`laboratorio/r18-escala.json`](../../laboratorio/r18-escala.json), [`laboratorio/r18-perguntas.json`](../../laboratorio/r18-perguntas.json), [`laboratorio/r20-k-adaptativo.json`](../../laboratorio/r20-k-adaptativo.json), [`laboratorio/r20-perguntas.json`](../../laboratorio/r20-perguntas.json), [`laboratorio/r38-dois-trechos-em-lista-bruto.json`](../../laboratorio/r38-dois-trechos-em-lista-bruto.json), [`laboratorio/r38-dois-trechos-em-lista.json`](../../laboratorio/r38-dois-trechos-em-lista.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json), [`laboratorio/r43-tamanho-da-lista-bruto.json`](../../laboratorio/r43-tamanho-da-lista-bruto.json), [`laboratorio/r43-tamanho-da-lista.json`](../../laboratorio/r43-tamanho-da-lista.json), [`laboratorio/r44-candidato-envenenado-bruto.json`](../../laboratorio/r44-candidato-envenenado-bruto.json), [`laboratorio/r44-candidato-envenenado.json`](../../laboratorio/r44-candidato-envenenado.json), [`laboratorio/r45-lista-nas-duas-ordens-bruto.json`](../../laboratorio/r45-lista-nas-duas-ordens-bruto.json), [`laboratorio/r45-lista-nas-duas-ordens.json`](../../laboratorio/r45-lista-nas-duas-ordens.json)
- **chama de outros arquivos** — [`cliente.perguntar`](../../integracao/jev_router/cliente.py#L57), [`politica.decidir`](../../integracao/jev_router/politica.py#L84), [`redacao.limpar`](../../integracao/jev_router/redacao.py#L43)
- **parecidos (julgados pelo Jev)** — [`hermes/jev_hermes/nucleo.py`](../../hermes/jev_hermes/nucleo.py) (complementar, 0.43), [`integracao/camadas/nucleo.py`](../../integracao/camadas/nucleo.py) (complementar, 0.26)
- **conteúdo** — [impressao](../../integracao/jev_router/roteador.py#L30) (l. 30; usado em 1), [do_cache](../../integracao/jev_router/roteador.py#L37) (l. 37), [para_o_cache](../../integracao/jev_router/roteador.py#L47) (l. 47; usado em 1), [guardar_pedido](../../integracao/jev_router/roteador.py#L56) (l. 56), [registrar](../../integracao/jev_router/roteador.py#L73) (l. 73), [classificar](../../integracao/jev_router/roteador.py#L81) (l. 81; usado em 3)
