---
name: jev-assist
description: Use JEV proactively to support Codex/Astra and Claude Code with repeated semantic classification, document tagging, intent, relevance ranking, duplicate candidates, log triage and claim-to-source checks. Prefer it for bounded judgments over many candidates or before loading large context. Uses the existing shared budget; falls back to the host assistant when unavailable.
---

# JEV como auxiliar cotidiano

O usuário pediu uso amplo do JEV quando reduzir trabalho repetitivo. Considere esta skill
proativamente; não espere o usuário mencionar JEV. Escolha subtarefas que tenham classes
explícitas e contexto suficiente. Para uma decisão trivial já evidente, responda diretamente;
para busca literal, cálculo, datas, validação de JSON e regras exatas, use código/rg.

## Ferramentas

O servidor MCP `jev` oferece:

- `jev_route`: entrada integrada; recebe `task`, `tools` e `skills`, sugere ambos em até
  duas chamadas. Listas usam `{id,description}`. Aceita `required_tool_id` e
  `required_skill_id`. Após consultar, aplique a seleção ao trabalho, não pare na recomendação.

- `jev_select_tool`: seleciona a próxima ferramenta entre alternativas realmente disponíveis.
- `jev_select_skill`: seleciona a próxima skill entre alternativas presentes no catálogo da sessão.

- `jev_status`: diagnóstico local sem custo. Consulte antes do primeiro uso na sessão.
- `jev_judge`: categorias próprias, até oito perguntas independentes sobre o mesmo estado
  em uma chamada. Use para tema/intenção, tipo de documento, etiquetas, triagem de solicitações,
  critérios de qualidade e seleção entre valores previamente extraídos. Vários rótulos que
  possam coexistir exigem perguntas separadas, não uma escolha exclusiva.
- `jev_assist`: rubricas prontas `log`, `evidence`, `context`.
- `jev_rank_context`: até oito candidatos; conserva todos os IDs, apenas ordena.
- `jev_metrics`: registros locais, sem inferência. Economia do Astra ainda não medida.
- `jev_record_review`: registra revisão posterior de tentativa existente, identificando se
  foi humana, do assistente ou determinística. Não apresentar revisão própria como independente.

Se o MCP ainda não foi carregado, use o Python local com `__JEV_ROOT__/integracao/usar.py`:

```powershell
python "__JEV_ROOT__/integracao/usar.py" --status
python "__JEV_ROOT__/integracao/usar.py" --request pedido.json
```

Formato de `pedido.json` (sem credenciais):

```json
{"name":"jev_judge","arguments":{"state":"O pacote não pôde ser importado.","questions":[{"id":"tema","instructions":"Classifique o assunto explicitamente descrito em state.","choices":{"software":"Falha de software ou biblioteca.","outro":"Outro assunto identificável.","incerto":"Não há informação suficiente."}}]}}
```

## Fluxo

### Seleção de ferramentas e skills solicitada pelo usuário

Use os dois seletores proativamente quando houver alternativas plausíveis para a tarefa.
O hook local `jev_workflow.py` ativa esse fluxo na entrada de pedidos substantivos,
sem enviar o prompt. Prefira `jev_route` para resolver as duas escolhas juntas. Preserve
nas descrições as pré-condições das skills; copie a descrição oficial, sem transformá-la
em uma capacidade genérica. Se a skill indicada exigir um contexto que não existe,
registre a inadequação e continue pelo procedimento normal, sem forçar sua aplicação.
Passe `task` com o próximo passo, objetivo e restrições, e `candidates` com `id` e
`description` de até dez candidatos. Ferramentas vêm do catálogo real da sessão (ou de
busca de ferramentas); skills vêm da lista disponível ao agente. Não invente capacidades,
não considere arquivo instalado como prova de ferramenta carregada e não leia todas as
skills para formar o catálogo: use primeiro as descrições já disponíveis.

Para um catálogo grande, faça uma pré-seleção local por finalidade, mantendo alternativas
plausíveis; declare ao usuário quando uma recomendação se limita a essa pré-seleção.
Nunca exclua uma skill explicitamente solicitada. Use `required_id` para preservar seleção
explícita sem inferência. Não use o JEV para escolher se deve consultar o próprio seletor.

`selected_id` é sugestão entre os IDs recebidos, não execução automática. Confirme que
a ferramenta continua disponível e que sua entrada/efeito cabe na tarefa; para skills,
leia o SKILL.md escolhido e aplique suas instruções. O seletor não elimina outras skills
obrigatórias em tarefas compostas. Depois de concluir um passo, selecione novamente apenas
se o próximo objetivo ou candidatos mudarem. Evite consultar de novo para a mesma decisão.

Resultado nulo, baixa confiança, falha ou saldo insuficiente: o agente escolhe pelo fluxo
normal. Corte inicial de 0,80 é provisório, sem calibração para este roteamento; confiança
não prova acerto. Não delegar permissões, modelo ou esforço. Não criar hooks fictícios:
no Codex, esta ativação acontece pelas instruções e pelas ferramentas MCP/CLI.

Exemplo de pedido ao CLI (também corresponde aos argumentos da ferramenta MCP):

```json
{"name":"jev_select_skill","arguments":{"task":"Extrair uma tabela de PDF local","candidates":[{"id":"pdf","description":"Extrair e conferir documentos PDF"},{"id":"frontend-design","description":"Criar interfaces web"}]}}
```

1. Ache candidatos localmente com `rg`, metadados ou parsers; não envie a conversa inteira.
2. Preserve ID, arquivo, linha e fonte. Envie apenas conteúdo necessário cujo uso no provedor
   esteja autorizado. Não ler/enviar `.env`, credenciais, arquivos de autenticação ou dados
   privados de outro projeto por causa desta configuração global. Redação automática não
   garante anonimização; confira o material antes do envio.
3. Pergunte uma propriedade por questão. Defina critérios sem sobreposição, inclua `incerto`.
   IDs organizam a saída; a instrução deve nomear o item/campo a avaliar. Não referencie
   uma posição distante de array sem identificar claramente o alvo.
4. Reúna perguntas independentes que realmente compartilham contexto. Evite lotes enormes.
5. Leia o recibo: erro/timeout/ausência de carteira/preço invalida o uso. Continue normalmente
   com Astra/Claude, sem repetir automaticamente e sem inventar classificação.
6. Use o julgamento como apoio. Confiança alta não é verdade comprovada. Em seleção de fontes,
   mantenha todos os candidatos recuperáveis, leia ressalvas e amplie a leitura se necessário.
   Fonte única: pelo menos dois trechos; resposta distribuída: pelo menos três quando disponíveis.
7. Verifique amostras/erros contra as fontes; registre tempo total, custo e releituras quando
   avaliar economia. Não assumir que inserir uma chamada torna uma tarefa simples mais rápida.

## Limites operacionais

Use somente o transporte `executor/shared.py` por essas ferramentas. O perfil local
`integracao/runtime.local.json` usa a carteira TypeSafe separada autorizada em 21/09/2026,
com teto TOTAL de US$ 0,03, incluindo os testes já realizados. `jev_status` informa saldo,
reserva máxima por chamada e prontidão. O preço precisa ser revalidado após 24 horas.
Sem perfil local, vale a carteira histórica existente e seus limites; não criar saldo novo.
Nunca contornar bloqueio com outro cliente ou aumentar teto. A skill oficial `typesafe-ai`
serve para desenho e documentação; exemplos de API devem passar pelo transporte financeiro.
Não copiar carteiras para gastar simultaneamente nos dois PCs: usar uma máquina executora
ou coordenação central. Esse saldo pequeno não é autorização de uso pago ilimitado.

JEV não decide autorização, permissões, execução de comandos, publicação, modelo/esforço do
assistente ou conclusão de tarefa. Não gera redação nem substitui análise causal e raciocínio
de múltiplas etapas. Sugestão de injeção é apenas sinal; as regras do agente continuam válidas.
Aplicações novas e classificações sobre código são experimentais até terem avaliação própria.
