# JEV no Codex e no Claude Code

Instalação nesta máquina em 21/09/2026:

- Skill oficial `typesafe-ai`, de https://github.com/typesafe-ai/skills,
  em `~/.codex/skills/typesafe-ai` e `~/.claude/skills/typesafe-ai`.
- Skill de uso cotidiano `jev-assist`, nos mesmos diretórios de skills. Sua fonte
  está em `integracao/skills/jev-assist/SKILL.md`; na cópia instalada, `__JEV_ROOT__`
  é substituído pelo caminho absoluto deste checkout.
- Servidor MCP `jev`, global nos dois aplicativos, usando `integracao/jev_mcp.py`.
- Instruções de uso proativo acrescentadas aos arquivos globais de cada agente;
  conteúdo anterior preservado com backup datado.

As skills ficam disponíveis a partir do próximo turno. Reabra a sessão se o aplicativo
ainda não listar as ferramentas MCP. A skill `typesafe-ai` é a oficial; `jev-assist`
é a adaptação local para aproveitar a carteira e as evidências do projeto.
O hook local `jev_workflow.py` está instalado em `UserPromptSubmit` no Codex e Claude Code.
Ele ativa o procedimento de seleção nos pedidos substantivos, sem enviar o prompt ao
provedor e sem ler transcripts. O agente forma candidatos reais e uma subtarefa adequada
para `jev_route`, aplica a escolha compatível e continua o trabalho. Não há interceptação
de todas as leituras nem execução automática de ferramentas escolhidas pelo classificador.

Instalar novamente: `python integracao/instalar_workflow.py`. Remover apenas esse hook:
`python integracao/instalar_workflow.py --remove`. Outros hooks são preservados com backup.
Em sessões já abertas, iniciar uma nova sessão para carregar a nova configuração de hooks/MCP.

Teste do processo de hook: JSON `UserPromptSubmit` válido, sem prompt privado na saída.
O diagnóstico `codex debug prompt-input` não executou o hook; portanto não foi tratado
como prova de acionamento automático dentro de uma sessão nativa. Esse acionamento deve
ser observado na próxima tarefa após recarregar a configuração. CLI e MCP foram testados
diretamente, com chamadas TypeSafe reais e uso das ferramentas recomendadas pelo agente.

Na revisão real, JEV sugeriu `code-review`, cuja exigência de referência de commits não
cabia no trabalho: o agente leu a skill e rejeitou sua aplicação. Na conferência da API,
indicou `web__run` e absteve-se da skill por confiança 0,77; o agente abriu a documentação
oficial e seguiu com a skill TypeSafe já aplicável. Esses casos não contam como sucesso
automático de skill. Descrições completas e validação das pré-condições são necessárias.

Referências: [hooks do Codex](https://developers.openai.com/pt-BR/docs/hooks) e
[contrato TypeSafe](https://docs.typesafe.ai/api).

## O que delegar

### Seletores de ferramentas e skills

As ferramentas `jev_select_tool` e `jev_select_skill` recebem a tarefa e até dez
candidatos reais (`id`, `description`). Retornam `selected_id`, confiança, motivo,
todos os IDs e recibo financeiro. Só recomendam; não executam ferramentas nem carregam
skills automaticamente. As instruções globais do Codex/Claude e a skill `jev-assist`
orientam seu uso proativo entre alternativas plausíveis.

Uma escolha explícita do usuário é preservada por `required_id`, sem inferência.
Ausência de candidato adequado, confiança abaixo de 0,80 ou resposta inválida resulta
em abstenção. O corte é provisório, não calibrado. O agente confere disponibilidade,
lê a skill indicada e aplica todas as instruções obrigatórias.

Validação inicial: 15 testes direcionados passaram. Duas chamadas reais acertaram
a ferramenta de pesquisa web (808 ms) e a skill PDF (733 ms), entre três alternativas
cada. São testes simples com gabarito prévio, não uma avaliação ampla de roteamento.
Artefatos locais: `runs/typesafe-selectors-20260921/`. Custo adicional por tokens/tarifa:
US$ 0,000052164; acumulado da carteira separada: US$ 0,000231210 de US$ 0,03.

| Trabalho | Ferramenta | Papel do assistente principal |
|---|---|---|
| Tema, intenção, tipo de documento, etiquetas e critérios fechados | `jev_judge` | Definir classes e contexto, conferir casos ambíguos |
| Julgar duplicidade entre pares candidatos | `jev_judge` | Encontrar candidatos localmente; não apagar automaticamente |
| Ordenar trechos e resultados de busca | `jev_rank_context` | Manter todas as fontes recuperáveis e ler as ressalvas |
| Triar logs por tipo de falha | `jev_assist`, tarefa `log` | Diagnosticar causa, corrigir e testar |
| Conferir afirmação versus fonte fornecida | `jev_assist`, tarefa `evidence` | Confirmar na fonte; conferir atualidade e origem |
| Avaliar relevância de um trecho | `jev_assist`, tarefa `context` | Ampliar a leitura quando faltar contexto |
| Diagnóstico de instalação e medições | `jev_status`, `jev_metrics` | Separar disponibilidade de gasto e de economia comprovada |

`jev_judge` aceita até oito perguntas independentes sobre o mesmo estado em uma
requisição, todas com a opção `incerto`. É apoio semântico, não geração de texto.
Categorias novas não herdam automaticamente as taxas de acerto dos experimentos anteriores.

Busca exata, contas, comparação de datas e validação de formatos continuam em código.
Autorização, execução, publicação, escolha de modelo/esforço e síntese ficam com o agente.
Use JEV quando volume ou contexto justificarem a chamada adicional; não há garantia de
economia para uma pergunta pequena já resolvida pelo assistente.

## Estado financeiro desta instalação

**Atualização após autorização de Igor em 21/09/2026:** foi autorizado um orçamento NOVO
separado de US$ 0,03 na TypeSafe. O perfil local `integracao/runtime.local.json` seleciona
a carteira `runs/typesafe-smoke-20260921/ledger.sqlite3`, com esse mesmo teto acumulado.
Não substitui nem reinicia a carteira histórica ausente. O perfil vale para todas as
chamadas padrão do transporte compartilhado nesta máquina, sem transportar segredos.

As nove chamadas reais realizadas até esta atualização produziram dez decisões corretas
em casos sintéticos (oito individuais e duas perguntas no mesmo estado), custando
US$ 0,000179046 por tokens e tarifa. Saldo: US$ 0,029820954. O piloto está no painel como
`typesafe-local-smoke-20260921`, com orçamento separado dos US$ 5 antigos. Para o saldo
operacional atualizado, executar `python integracao/usar.py --status` ou `jev_status`.

O perfil rejeita carteira ausente, teto acima do autorizado e preço verificado há mais
de 24 horas. Revalidar a documentação oficial antes de atualizar a data/tarifa em
`runs/typesafe-smoke-20260921/precos.json`; saída atualmente gratuita. Não basta mudar
a data para ignorar a conferência. O saldo não autoriza renovação automática do teto.

### Diagnóstico inicial, antes da autorização separada

O diagnóstico local encontrou a chave OpenRouter no `.env`, sem exibir seu valor.
Não encontrou chave TypeSafe nem `runs/ledger.sqlite3`. Nenhuma inferência foi realizada
para esta instalação. As chamadas pagas param antes de consultar credenciais ou rede
se o livro-caixa não existe. A integração não cria uma carteira nova com US$ 5.

Para ativar o uso pago, recuperar do outro PC um backup consistente e atualizado do
SQLite pela API de backup, após parar os consumidores. Copiar só o arquivo principal
enquanto há escrita em WAL pode perder lançamentos. Manter apenas um PC como executor
da carteira, ou implantar uma coordenação central antes de gastar simultaneamente.
O JSON de extrato versionado não substitui o livro-caixa completo atualizado.

Todas as chamadas passam por `executor/shared.py`, com reserva atômica, liquidação,
teto global de US$ 5 e subcota existente `tools` de US$ 0,20. Não aumentar cotas nem
contornar bloqueio via SDK ou cliente paralelo. O OpenRouter consulta os preços públicos
no fluxo compartilhado; uma futura troca para TypeSafe exige conferir tarifa e credencial.

## Conferir e usar sem MCP carregado

```powershell
python integracao/usar.py --status
claude mcp get jev
codex mcp get jev
```

O CLI também aceita `--request pedido.json`, com objeto `name` e `arguments` conforme
o catálogo MCP. Não incluir chave no arquivo. Os exemplos estão na skill `jev-assist`.

Validação desta mudança: 20 testes direcionados passaram, incluindo handshake stdio,
catálogo, conservação de IDs, lote de perguntas em chamada única, rejeição de rubricas
inválidas e bloqueio sem rede/credencial quando não existe carteira. Claude Code confirmou
conexão ao servidor. Testes de inferência real aguardam o livro-caixa.

Suíte ampliada: 259 testes e 211 subtestes passaram, quatro foram pulados e dois
dependentes do cofre/chaves reais do outro PC foram explicitamente excluídos.
A primeira execução também revelou a ausência da pasta operacional `integracao/estado`,
criada localmente antes da repetição. Não foram criadas credenciais fictícias para passar testes.

Após ativar o perfil local: 32 testes direcionados passaram (transporte, MCP, perfil,
rubricas e servidor do painel), incluindo bloqueio de tarifa antiga e aumento indevido
do teto. Navegação no painel conferiu execução publicada e orçamento separado, sem erros JS.


## Fonte para comparação de modelos

Por orientação de Igor em 21/09/2026, Artificial Analysis passa a ser fonte preferencial
para recomendações de modelos: https://artificialanalysis.ai/. Consultar evidências
recentes de múltiplos benchmarks pertinentes à tarefa, a metodologia e a configuração
exata avaliada. Cruzar com documentação dos fornecedores e avaliação local representativa.

Separar qualidade, custo por tarefa, latência total e confiabilidade. Não usar apenas o
ranking geral, não contar o índice e seus componentes como evidências independentes e
não confundir custo API com assinatura Codex. Critérios/pesos devem refletir o trabalho;
explicar limitações, incerteza e sensibilidade da recomendação a esses pesos.

A preferência está nas instruções globais do Codex e Claude Code. Não altera modelos,
esforço ou autorizações financeiras; os seletores JEV continuam sendo de ferramentas/skills.
