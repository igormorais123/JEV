# integracao/

O Jev dentro do fluxo real: roteador de prompts, hooks do Claude Code, servidor MCP, instalador, leitura de contexto para o Codex.

← [MAPA.md](../../MAPA.md) · pasta acima: [raiz](../../mapa/pastas/_raiz.md) · abrir a pasta: [integracao/](../../integracao)

## Subpastas

| subpasta | arquivos | finalidade |
|---|---:|---|
| [avaliacao/](../../mapa/pastas/integracao__avaliacao.md) | 17 | Avaliação da integração com tráfego real do Igor (E13): amostragem, gabaritos e relatórios agregados. O texto original é privado e fica fora do Git. |
| [camadas/](../../mapa/pastas/integracao__camadas.md) | 13 | As camadas que decidem o que entra no contexto do modelo caro: leitura, busca, sentinela, saída, verificação, `ler` (skill /jev-ler), medição e rotina. |
| [hooks/](../../mapa/pastas/integracao__hooks.md) | 7 | Os scripts de hook instalados no Claude Code/Codex; cada um é um invólucro fino sobre uma camada. |
| [jev_router/](../../mapa/pastas/integracao__jev_router.md) | 7 | Roteador de prompts: política, orçamento, redação de credenciais, cliente do provedor e CLI. |
| [skill/](../../mapa/pastas/integracao__skill.md) | 1 |  |
| [tests/](../../mapa/pastas/integracao__tests.md) | 6 | Testes da integração: camadas, guarda de comando, redação, roteador e rotina. |

## Arquivos

| arquivo | tipo | tamanho | descrição |
|---|---|---:|---|
| [README.md](../../integracao/README.md) | doc | 256 l. | O Jev dentro do Claude Code e do Codex — Depois do estudo (31 mil chamadas, 27 rodadas), o Jev foi posto nos pontos do fluxo do |
| [instalar.py](../../integracao/instalar.py) | código | 354 l. | Instala (ou remove) o hook do Jev no Claude Code e no Codex. |
| [jev_mcp.py](../../integracao/jev_mcp.py) | código | 206 l. | Minimal MCP stdio server: no dependencies, no shell execution, no secret in config. |

## Grafo de imports e links

Nós em negrito são desta pasta; setas cheias são imports, tracejadas são links de documento.

```mermaid
flowchart LR
  n_README_md["README.md"]
  n_docs_CAMADAS_CLAUDE_CODE_md["docs/CAMADAS-CLAUDE-CODE.md"]
  n_executor_assist_py["executor/assist.py"]
  n_executor_shared_py["executor/shared.py"]
  n_executor_tests_test_mcp_py["executor/tests/test_mcp.py"]
  n_integracao_README_md["<b>README.md</b>"]
  n_integracao_camadas_busca_py["integracao/camadas/busca.py"]
  n_integracao_camadas_sentinela_py["integracao/camadas/sentinela.py"]
  n_integracao_instalar_py["<b>instalar.py</b>"]
  n_integracao_jev_mcp_py["<b>jev_mcp.py</b>"]
  n_integracao_jev_router_redacao_py["integracao/jev_router/redacao.py"]
  n_README_md -.-> n_integracao_README_md
  n_executor_tests_test_mcp_py --> n_integracao_jev_mcp_py
  n_integracao_README_md -.-> n_docs_CAMADAS_CLAUDE_CODE_md
  n_integracao_instalar_py --> n_integracao_camadas_busca_py
  n_integracao_instalar_py --> n_integracao_camadas_sentinela_py
  n_integracao_jev_mcp_py --> n_executor_assist_py
  n_integracao_jev_mcp_py --> n_executor_shared_py
  n_integracao_jev_mcp_py --> n_integracao_jev_router_redacao_py
```

## Ligações e conteúdo de cada arquivo

### README.md

- **usa** — link: [`docs/CAMADAS-CLAUDE-CODE.md`](../../docs/CAMADAS-CLAUDE-CODE.md); citação: [`.gitignore`](../../.gitignore), [`executor/credenciais.py`](../../executor/credenciais.py), [`executor/ledger.py`](../../executor/ledger.py), [`integracao/camadas/medir.py`](../../integracao/camadas/medir.py), [`integracao/camadas/rotina.py`](../../integracao/camadas/rotina.py), [`integracao/hooks/jev_guarda_comando.py`](../../integracao/hooks/jev_guarda_comando.py), [`integracao/hooks/jev_prompt_router.py`](../../integracao/hooks/jev_prompt_router.py), [`integracao/instalar.py`](../../integracao/instalar.py), [`integracao/jev_router/cli.py`](../../integracao/jev_router/cli.py), [`integracao/jev_router/redacao.py`](../../integracao/jev_router/redacao.py), [`integracao/tests/test_redacao.py`](../../integracao/tests/test_redacao.py), [`laboratorio/PREREGISTRO.md`](../../laboratorio/PREREGISTRO.md)
- **é usado por** — link: [`README.md`](../../README.md)
- **parecidos (julgados pelo Jev)** — [`integracao/jev_router/politica.py`](../../integracao/jev_router/politica.py) (complementar, 0.34)
- **papel nos estudos** — define [E13](../../mapa/conhecimento/experimentos.md#e13)
- **menciona 9 conceitos** — [E1](../../mapa/conhecimento/experimentos.md#e1) (1×), [E3](../../mapa/conhecimento/experimentos.md#e3) (1×), [E5](../../mapa/conhecimento/experimentos.md#e5) (1×), [E8](../../mapa/conhecimento/experimentos.md#e8) (1×), [E11](../../mapa/conhecimento/experimentos.md#e11) (1×), [E12](../../mapa/conhecimento/experimentos.md#e12) (1×), [R16](../../mapa/conhecimento/rodadas.md#r16) (1×), [H038](../../mapa/conhecimento/hipoteses.md#h038) (1×), [Q044](../../mapa/conhecimento/perguntas.md#q044) (1×)
- **conteúdo** — As camadas (2026-09-20): o Jev decide o que entra no contexto do modelo caro (l. 3), O que não funcionou, e por quê (l. 83), O que funciona, e está instalado (l. 145), Como está instalado (l. 166), Garantias de operação (l. 189), Como refazer a medição (l. 204), O que se mediu do roteador em produção (l. 220), Os dois hooks, e como mexer neles (l. 241)

### instalar.py

- **usa** — import: [`integracao/camadas/busca.py`](../../integracao/camadas/busca.py), [`integracao/camadas/sentinela.py`](../../integracao/camadas/sentinela.py); citação: [`docs/CAMADAS-CLAUDE-CODE.md`](../../docs/CAMADAS-CLAUDE-CODE.md), [`integracao/camadas/rotina.py`](../../integracao/camadas/rotina.py), [`integracao/hooks/jev_busca.py`](../../integracao/hooks/jev_busca.py), [`integracao/hooks/jev_guarda_comando.py`](../../integracao/hooks/jev_guarda_comando.py), [`integracao/hooks/jev_leitura.py`](../../integracao/hooks/jev_leitura.py), [`integracao/hooks/jev_leitura_shell.py`](../../integracao/hooks/jev_leitura_shell.py), [`integracao/hooks/jev_prompt_router.py`](../../integracao/hooks/jev_prompt_router.py), [`integracao/hooks/jev_saida.py`](../../integracao/hooks/jev_saida.py), [`integracao/hooks/jev_sentinela.py`](../../integracao/hooks/jev_sentinela.py)
- **é usado por** — citação: [`integracao/README.md`](../../integracao/README.md), [`integracao/skill/jev-completo/SKILL.md`](../../integracao/skill/jev-completo/SKILL.md), [`laboratorio/r17-economia-de-contexto.json`](../../laboratorio/r17-economia-de-contexto.json), [`laboratorio/r18-escala.json`](../../laboratorio/r18-escala.json), [`laboratorio/r18-perguntas.json`](../../laboratorio/r18-perguntas.json), [`laboratorio/r20-k-adaptativo.json`](../../laboratorio/r20-k-adaptativo.json), [`laboratorio/r20-perguntas.json`](../../laboratorio/r20-perguntas.json), [`laboratorio/r38-dois-trechos-em-lista-bruto.json`](../../laboratorio/r38-dois-trechos-em-lista-bruto.json), [`laboratorio/r38-dois-trechos-em-lista.json`](../../laboratorio/r38-dois-trechos-em-lista.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json), [`laboratorio/r43-tamanho-da-lista-bruto.json`](../../laboratorio/r43-tamanho-da-lista-bruto.json), [`laboratorio/r43-tamanho-da-lista.json`](../../laboratorio/r43-tamanho-da-lista.json), [`laboratorio/r44-candidato-envenenado-bruto.json`](../../laboratorio/r44-candidato-envenenado-bruto.json), [`laboratorio/r44-candidato-envenenado.json`](../../laboratorio/r44-candidato-envenenado.json), [`laboratorio/r45-lista-nas-duas-ordens-bruto.json`](../../laboratorio/r45-lista-nas-duas-ordens-bruto.json), [`laboratorio/r45-lista-nas-duas-ordens.json`](../../laboratorio/r45-lista-nas-duas-ordens.json)
- **parecidos (julgados pelo Jev)** — [`integracao/jev_router/politica.py`](../../integracao/jev_router/politica.py) (complementar, 0.26), [`integracao/jev_router/cli.py`](../../integracao/jev_router/cli.py) (complementar, 0.21)
- **menciona 1 conceito** — [R16](../../mapa/conhecimento/rodadas.md#r16) (1×)
- **conteúdo** — [entrada_de](../../integracao/instalar.py#L132) (l. 132), [instalado_em](../../integracao/instalar.py#L146) (l. 146), [instalar_gancho](../../integracao/instalar.py#L155) (l. 155), [desinstalar_gancho](../../integracao/instalar.py#L187) (l. 187), [gravar_modo](../../integracao/instalar.py#L213) (l. 213), [backup](../../integracao/instalar.py#L218) (l. 218), [carregar](../../integracao/instalar.py#L224) (l. 224), [gravar](../../integracao/instalar.py#L228) (l. 228), [ja_instalado](../../integracao/instalar.py#L232) (l. 232), [instalar](../../integracao/instalar.py#L240) (l. 240), [desinstalar](../../integracao/instalar.py#L257) (l. 257), [agendar](../../integracao/instalar.py#L283) (l. 283), [ver](../../integracao/instalar.py#L294) (l. 294), [main](../../integracao/instalar.py#L317) (l. 317)

### jev_mcp.py

- **usa** — import: [`executor/assist.py`](../../executor/assist.py), [`executor/shared.py`](../../executor/shared.py), [`integracao/jev_router/redacao.py`](../../integracao/jev_router/redacao.py)
- **é usado por** — import: [`executor/tests/test_mcp.py`](../../executor/tests/test_mcp.py); citação: [`executor/smoke_mcp.py`](../../executor/smoke_mcp.py), [`integracao/skill/jev-completo/SKILL.md`](../../integracao/skill/jev-completo/SKILL.md), [`laboratorio/r17-economia-de-contexto.json`](../../laboratorio/r17-economia-de-contexto.json), [`laboratorio/r18-escala.json`](../../laboratorio/r18-escala.json), [`laboratorio/r18-perguntas.json`](../../laboratorio/r18-perguntas.json), [`laboratorio/r20-k-adaptativo.json`](../../laboratorio/r20-k-adaptativo.json), [`laboratorio/r20-perguntas.json`](../../laboratorio/r20-perguntas.json), [`laboratorio/r38-dois-trechos-em-lista-bruto.json`](../../laboratorio/r38-dois-trechos-em-lista-bruto.json), [`laboratorio/r38-dois-trechos-em-lista.json`](../../laboratorio/r38-dois-trechos-em-lista.json), [`laboratorio/r39-codigo-numa-chamada-bruto.json`](../../laboratorio/r39-codigo-numa-chamada-bruto.json), [`laboratorio/r39-codigo-numa-chamada.json`](../../laboratorio/r39-codigo-numa-chamada.json), [`laboratorio/r44-candidato-envenenado-bruto.json`](../../laboratorio/r44-candidato-envenenado-bruto.json), [`laboratorio/r44-candidato-envenenado.json`](../../laboratorio/r44-candidato-envenenado.json)
- **chama de outros arquivos** — [`redacao.limpar`](../../integracao/jev_router/redacao.py#L43)
- **parecidos (julgados pelo Jev)** — [`integracao/avaliacao/comandos.py`](../../integracao/avaliacao/comandos.py) (complementar, 0.20)
- **conteúdo** — [metrics](../../integracao/jev_mcp.py#L97) (l. 97), [call](../../integracao/jev_mcp.py#L109) (l. 109; usado em 1), [handle](../../integracao/jev_mcp.py#L166) (l. 166; usado em 1), [main](../../integracao/jev_mcp.py#L193) (l. 193)
