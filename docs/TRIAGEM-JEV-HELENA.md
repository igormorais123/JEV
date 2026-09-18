# JEV — triagem de projetos e agenda de experimentos

> Atualização de escopo: o pedido posterior exige uma rodada simples de todos os sistemas. O [plano científico completo](PLANO-CIENTIFICO-JEV-HELENA.md) prevalece sobre as prioridades de exclusão/adiamento deste estudo inicial.

**Helena Strategos Inteia · perspectiva de cientista-chefe · 18/09/2026**  
**Status:** estudo documental e inspeção estática concluídos para os 18 repositórios indicados, além do cookbook oficial. Nenhum sistema instalado ou executado; nenhuma inferência paga. **Gasto OpenRouter nesta pesquisa: US$ 0.**

## 1. Decisão recomendada

**Não vale testar os 15 sistemas como 15 projetos independentes.** A lista reúne aplicações, ferramentas de medição, infraestrutura de comparação e demonstrações. A melhor primeira rodada combina **Jev CLI + um corpus próprio em português + avaliação reaproveitável**. Depois, testa o ganho de ordenação de fontes. Roteamento, revisão de código e fiscalização de agentes entram conforme o resultado dessas duas frentes.

Minha pergunta central é: **em qual decisão concreta o Jev reduz custo, demora ou trabalho humano sem aumentar o erro que nos importa?** Classificar corretamente o tipo de tarefa não demonstra que se escolheu o melhor modelo para executá-la. Produzir uma probabilidade não demonstra calibração. Um exemplo funcionando não mede confiabilidade.

**Prioridades propostas, não resultados experimentais:**

| Destino | Projetos | Decisão |
|---|---|---|
| Primeiro experimento | Jev CLI | Melhor entrada: várias decisões delimitadas e transporte OpenRouter já implementado |
| Avaliação compartilhada | Janus, jevcal, System One Adapter | Usar como instrumentos; evitar três infraestruturas e três coletas independentes |
| Segunda frente | Jev Rerank Bench + núcleo do Jev Search | Primeiro medir ordenação sobre candidatos congelados; depois avaliar busca completa |
| Rodada condicional | Every, pi-model-router, pi-warden, Jev Review | Cada um precisa demonstrar ganho incremental sobre ferramenta ou rotina já disponível |
| Adiar integração completa | Jev Ultrafast, Jeeves | Mais dependências e causas de falha; começar por decisões isoladas se a frente for escolhida |
| Referência de pesquisa | HEIST//ONE, SemIf | Úteis para arquitetura/soberania local; não prioritários para decidir adoção via OpenRouter |
| Eliminar da bateria de qualidade | should-ai-kill-us-all | Perguntas centrais sem alvo empírico verificável; guardar somente a arquitetura de monitoramento |
| Consulta, sem experimento próprio | Dois catálogos awesome, skills e cookbook oficiais | São fontes e exemplos, não competidores |

“Adiar” não significa que o projeto é ruim. Significa que o teste compra pouca informação adicional agora ou exige uma condição ainda ausente. A única exclusão metodológica forte é usar o veredito do projeto de notícias como medida de previsão real.

## 2. Achado que altera a ordem: OpenRouter é uma condição técnica

A página do provedor lista **`typesafe/jev-1.13`**, com **US$ 0,042 por milhão de tokens de entrada e saída gratuita**, na consulta de 18/09. Isso é preço publicado, não medição de cobrança da nossa conta. [Fonte: OpenRouter](https://openrouter.ai/typesafe/jev-1.13/).

O Jev CLI implementa `POST https://openrouter.ai/api/alpha/decisions`, enviando `model`, `state` e `questions`; valida as respostas tipadas e possui seleção explícita de provedor. Portanto, existe um caminho implementado para nossa chave, **ainda sem teste autenticado nesta pesquisa**. [Código consultado](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/src/provider.ts).

Há uma divergência documental: o CLI diz que o OpenRouter não possui alias `latest`, enquanto o catálogo atual lista `~typesafe/jev-latest`. Para o experimento, fixar `typesafe/jev-1.13` e registrar a versão devolvida evita depender dessa divergência. Não inferir, a partir da página genérica de compatibilidade OpenAI, que o Jev usa o endpoint comum de chat.

| Componente | Situação encontrada | Implicação para iniciar |
|---|---|---|
| Jev CLI | Provedor OpenRouter Decisions no código | Candidato ao primeiro teste de contrato |
| Jev Search, pi-model-router, Every, Jev Ultrafast | Cliente Jev aponta para TypeSafe | Adaptar transporte antes de usar nossa chave |
| Janus | Provedor Jev usa SDK TypeSafe; há provedores LLM separados | Reaproveitar resultados/replay ou criar integração de decisões |
| jevcal | Jev usa `/v1/systemone`; opção OpenRouter existente usa chat para LLM | Suporte a LLM OpenRouter não prova suporte a Jev Decisions |
| System One Adapter | Provedor OpenAI aceita `base_url` e chave customizados | Serve ao comparador generativo; não é o cliente nativo Jev |
| pi-warden | Integração `pi-typesafe` e credencial TypeSafe | Verificar/adaptar essa dependência; exige ambiente Pi |
| Jev Review, HEIST//ONE | SDK oficial TypeSafe | Integração adicional para o endpoint de decisões |
| Jeeves | Cliente Rust TypeSafe, Gemini e plataformas de chat | Não é uma aplicação utilizável apenas com a chave disponível |
| should-ai-kill-us-all | Endpoint TypeSafe configurável | Alterar URL não dispensa revisar identificador do modelo e contrato |
| SemIf | Modelos locais | Não usa nossa chave e não reproduz o Jev |

A TypeSafe documenta inglês como língua de melhor desempenho e distingue o limite total da requisição do limite de estado mais pergunta. O OpenRouter apresenta contexto de 32K. **Não transferir automaticamente limites de lote nem resultados em inglês para o transporte e corpus que usaremos.** [Modelos TypeSafe](https://docs.typesafe.ai/models).

## 3. Critério da triagem

Comparei utilidade para os usos sugeridos, existência de um resultado verificável, contribuição única, dependências, compatibilidade da credencial e evidência publicada. Não usei estrelas como medida de qualidade nem atribuí notas numéricas sem observações.

- **Fato documental:** comportamento descrito e/ou trecho de implementação inspecionado.
- **Resultado do autor:** experimento publicado no próprio projeto, não reproduzido aqui.
- **Hipótese de teste:** ganho possível, ainda por medir em nossos dados.
- **Recomendação:** julgamento de prioridade derivado dessas informações.

Foram lidos READMEs, configurações, clientes e arquivos centrais selecionados. Não foi feita auditoria integral, avaliação de manutenção dos autores ou certificação das suítes. A presença de testes é um sinal de estrutura, não prova de que passaram. Os hashes consultados e a estrutura de entrada estão no [catálogo de fontes](../research/FONTES.md).

## 4. Fichas dos sistemas

### 01 · Jev CLI — testar primeiro

[Repositório](https://github.com/Nasrallah-AL/jev-cli) · Node.js 20.12+ · MIT.

**Função e estrutura:** comandos para classificação, suporte de alegações, busca/ordenação, comparação e roteamento. Começar por `docs/classify.md`, `verify.md`, `route.md`, `batch.md` e `src/provider.ts`. O modo `--dry-run` permite examinar a requisição sem inferência. `verify` julga a evidência fornecida; não pesquisa a verdade externamente.

**Perguntas:** separa apoio, contradição e ausência de informação em português? Mantém o resultado com negação, datas, valores e paráfrases? Identifica quando nenhuma classe cabe? Lote e chamada individual concordam? Resposta incompleta termina em erro detectável?

**Teste proposto:** 120 itens de classificação e 90 pares alegação–evidência rotulados, comparados com regras simples e um LLM de referência. Separar erros por classe e falsos apoios. Incluir casos sem resposta e trocar ordem das opções.

**Decisão:** continuar se houver vantagem de custo/tempo com qualidade aceitável no conjunto reservado. Abandonar um uso específico se os erros confiantes persistirem após uma revisão das perguntas. O CLI é a bancada; não precisa ser o formato final do produto.

### 02 · Jev Search — testar o núcleo, depois o aplicativo

[Repositório](https://github.com/superagents-lab/jev-search) · Node.js 22.12+, pnpm, TanStack/React, Cloudflare · MIT.

**Função:** escolhe fontes, período e candidatos de consulta; Search1API recupera; Jev pontua títulos/trechos; código une e ordena resultados. Ler `src/lib/typesafe.ts`, `pipeline.ts`, `search1api.ts`, `rank.ts`, `merge.ts` e `test/`. Exige Search1API além do Jev.

**Perguntas:** o ganho vem da busca ou da reordenação? Fontes oficiais sobem quando a pergunta as exige? Textos recentes mas irrelevantes superam documentos corretos? Datas desconhecidas e fontes indisponíveis ficam visíveis? Duplicatas ocupam os primeiros lugares?

**Teste:** 30 consultas e 20 candidatos congelados por consulta; comparar ordenação original, BM25 e Jev. Medir nDCG@10, Recall@5, documentos oficiais relevantes no topo e perdas por filtro. Só depois testar consultas ao vivo, mantendo a mesma janela de coleta entre variantes.

**Decisão:** prioridade alta para curadoria; adiar interface/deploy e Search1API até demonstrar ganho no núcleo. Jev CLI já cobre um teste mínimo de reranking, mas não substitui o fluxo de busca completo.

### 03 · Janus — manter como instrumento de decisão

[Repositório](https://github.com/FirasSX914/Janus) · Python, NumPy, provedores opcionais · MIT.

**Função:** mede a política de manter uma decisão no modelo primário ou recorrer ao fallback. Ler `RESEARCH.md`, `results/`, `src/janus/measure.py`, `sweep.py` e `providers/`. Com logs sem rótulo, mede concordância, não acerto.

**Perguntas:** o fallback corrige precisamente os erros do Jev? Quanto custa a cascata completa? Há um limiar que melhora o compromisso qualidade/custo em dados não usados na escolha? Quando a resposta correta é não rotear?

**Teste:** reutilizar as mesmas decisões rotuladas do CLI; comparar sempre Jev, sempre fallback e cascata. Escolher o limiar na calibração e avaliar em reserva intocada: o fluxo `measure.py` inspecionado faz varredura e escolha sobre as linhas medidas, exigindo essa separação no nosso protocolo.

**Decisão:** alta prioridade metodológica. Os resultados publicados diferem entre conjuntos; não copiar limiares. Não abrir uma segunda coleta se os dados necessários já foram registrados no primeiro experimento.

### 04 · pi-warden — promissor, condicionado ao ganho sobre regras

[Repositório](https://github.com/DevMortimer/pi-warden) · Pi/TypeScript e `pi-typesafe`.

**Função:** combina padrões locais e julgamentos para ações, regras, repetição e alegações de conclusão. Ler `docs/guards.md`, `src/guard.ts`, `done.ts`, `stuck.ts` e `eval/reports/`. Muitas verificações orientam o agente; não bloqueiam. O autor relata ganhos concentrados em algumas dimensões e ausência de ganho mensurável em outras.

**Perguntas:** identifica “testes passaram” quando nenhum teste passou? Distingue comando citado de comando executado? Respeita o escopo autorizado? Quanto interrompe trabalho correto? O que Jev acrescenta ao detector determinístico?

**Teste:** reprodução offline de 60 eventos rotulados — 20 violações, 20 ações legítimas, 20 alegações de conclusão — com saídas de ferramentas preservadas. Comparar regras, Jev e combinação; medir detecção, falsos bloqueios, avisos inúteis e latência.

**Decisão:** não instalar em toda a operação nesta rodada. Só avançar se reduzir erro residual com poucos falsos bloqueios. Integração ao Pi é trabalho distinto de aproveitamento em Hermes/Codex.

### 05 · Jev Ultrafast — adiar até validar decisões básicas

[Repositório](https://github.com/browser-use/jev-ultrafast) · Python/uv, Chrome, Browser Harness, modelo textual.

**Função:** Jev seleciona operação/alvo entre elementos observados; o modelo textual preenche texto. Ler `jev_ultrafast/agent.py`, `model.py`, `snapshot.js`, `examples/` e `docs/performance.md`. OpenRouter aparece no auxiliar de texto; o Jev permanece no endpoint TypeSafe.

**Perguntas:** detecta campo/alvo desatualizado? Sabe parar sem declarar sucesso falso? Funciona com rótulos portugueses e mensagens de validação? Quanto custa por tarefa concluída, incluindo novas tentativas? Um script estável seria melhor?

**Teste futuro:** cinco tarefas locais com formulário, dropdown, busca, erro e mudança de DOM, três repetições por variante; comparar script e agente convencional. Verificador independente lê o estado final. O MVP declara limitações em frames, shadow roots, canvas e uploads.

**Decisão:** referência útil para portais, mas inadequada como primeiro teste do modelo. As medições publicadas de poucas tarefas não fundamentam confiabilidade em portais heterogêneos.

### 06 · jevcal — aproveitar calibração, evitar duplicação

[Repositório](https://github.com/abhixhek/jevcal) · Python 3.10+ · MIT.

**Função:** perguntas por configuração, coleta, compilação de limiares, relatório e detecção de regressão. Ler `src/jevcal/compile.py`, `metrics.py`, `check.py`, `providers/` e `examples/`. A demonstração usa simulador.

**Perguntas:** a confiança separa erros/acertos em cada pergunta? Uma exigência de urgência derruba a cobertura do lote inteiro? O limiar funciona fora da amostra de ajuste? Uma mudança de versão é detectada? O intervalo inferior de precisão sustenta a meta?

**Teste:** alimentar predições reais já coletadas, comparar alvo por pergunta e política única. Medir precisão entre aceitos, cobertura, Brier/ECE e composição da escalada; conferir os denominadores. Não usar rótulos automáticos como verdade sem revisão.

**Decisão:** manter como complemento do Janus para múltiplas perguntas e regressão. Para uma única classificação, escolher apenas um deles como executor principal. Otimização de perguntas precisa de uma reserva final adicional: consultar repetidamente a validação também ajusta o sistema a ela.

### 07 · Jev Rerank Bench — estudar antes de pagar por busca

[Repositório](https://github.com/anessbelbati/jev-rerank-bench) · Python/uv, datasets, respostas salvas.

**Função:** comparação de estratégias de ordenação, custos e sensibilidade. Ler `results/summary.md`, `cache/`, `rerankers/jev.py`, `eval.py`, `significance.py` e `candidates/`. Os autores disponibilizam respostas para reavaliação sem novas chamadas.

**Perguntas:** a rubrica supera relevância binária nos nossos documentos? A ordem dos candidatos altera o resultado? O sistema rejeita a lista quando nenhum documento responde? O ganho persiste em português? A seleção inicial já perdeu a resposta?

**Teste:** compartilhar as 30 consultas do Jev Search. Incluir versões sem resposta e ordem invertida. Medir recall da recuperação separadamente da qualidade de reordenação; não excluir silenciosamente consultas sem documento relevante.

**Decisão:** prioridade alta como protocolo. Não reproduzir todos os modelos/datasets. Os resultados publicados não estabelecem vencedor universal; pesos por conjunto e por consulta podem mudar a leitura. Evidência externa orienta o desenho, não substitui nossa avaliação.

### 08 · System One Adapter — manter como comparador

[Repositório oficial](https://github.com/typesafe-ai/system-one-adapter-python) · Python, SDKs opcionais · MIT.

**Função:** expõe decisões tipadas usando LLMs generativos. Ler `src/system_one_adapter/providers/openai.py`, demais provedores e `tests/`. Aceita endpoint OpenAI compatível; contabiliza tentativas e registra diagnósticos de estrutura.

**Perguntas:** a vantagem vem do Jev ou de decompor bem a tarefa? JSON inválido e correções eliminam a economia do LLM? Probabilidades declaradas pelo LLM calibram? Escolha discreta basta para o nosso uso?

**Teste:** mesmas entradas, opções e rótulos do CLI, com um LLM acessível pelo OpenRouter; medir qualidade, custo total com tentativas, latência e falhas de esquema. Comparar probabilidades e modo discreto sem tratá-los como instrumentos idênticos.

**Decisão:** instrumento necessário para uma comparação útil, mas não aplicação autônoma. Não confundir normalização de números com calibração empírica nem este adaptador com transporte nativo de Jev Decisions.

### 09 · Jev Review — segunda escolha para código

[Repositório](https://github.com/devagrawal09/jev-review) · Node.js 24+, Git, SDK TypeSafe · MIT.

**Função:** revisão por etapas de diff ou código completo: sinal de risco, evidência, mecanismo, severidade e encaminhamento. Ler `src/review/`, `src/domain/`, `src/adapters/` e `scripts/check-dependencies.ts`. O painel é local; não há integração de compilador/analisadores no escopo documentado.

**Perguntas:** aponta região que demonstra o defeito? Diferencia suspeita de erro reproduzível? Regride ao receber contexto de teste? Severidade corresponde ao efeito observado? As etapas acumulam falsos positivos ou custo?

**Teste:** 20 diffs pequenos — 10 com defeitos documentados/reproduzíveis e 10 corretos — comparados com linter/testes e revisão generativa. Medir precisão por achado, defeitos omitidos e minutos para confirmar cada alerta.

**Decisão:** adiar atrás de Every para uma pergunta comportamental estreita. Não é redundância total: revisão de mudança e busca por função têm unidades diferentes. Eliminar da implantação se o custo de confirmar alertas superar o trabalho poupado.

### 10 · Every — bom candidato a terceiro experimento

[Repositório](https://github.com/sufianetaouil/every) · Python/tree-sitter · MIT.

**Função:** pergunta sim/não aplicada a funções extraídas; adiciona vizinhança conforme a questão e ranqueia resultados. Ler `every/extract.py`, `classify.py`, `judge.py`, `cache.py` e `examples/recorded/`. O código de funções é enviado ao provedor. O selftest publicado é pequeno e autoral.

**Perguntas:** encontra “captura erro e ignora” além do que `rg`/AST encontra? Distingue recuperação válida de erro engolido? Mudança de modelo invalida cache? Questões entre arquivos assumem explicitamente cobertura parcial?

**Teste:** 60 funções rotuladas, metade com comportamento buscado, incluindo negativos difíceis, duas linguagens e exemplos que dependem de chamadores. Comparar `rg`, uma regra AST e Jev; medir precisão nos dez primeiros, recall e tempo de inspeção.

**Decisão:** manter pelo resultado verificável e escopo pequeno. Só adaptar o transporte se a pergunta que queremos responder realmente escapa de regras sintáticas. Não executar uma varredura inteira como ensaio inicial.

### 11 · HEIST//ONE — referência, sem orçamento inicial

[Repositório](https://github.com/AbdelStark/heist-one) · Node.js 22.13+, pnpm, servidor e navegador · MIT.

**Função:** jogo com observação limitada por guarda, propostas Jev e validação determinística. Ler `SPEC.md`, `packages/game/`, `apps/` e `docs/LIVE-JEV-VERIFICATION.md`. Possui adaptador programado sem credenciais e rastros de uma execução ao vivo.

**Perguntas:** o agente usa somente o que observou? Respostas atrasadas são descartadas? Fallback mantém a simulação operando? O Jev acrescenta variedade/coerência que regras não entregam?

**Teste futuro:** cenários e sementes fixos, mesmas observações, comparar adaptador programado e Jev; medir ações inválidas, atrasos descartados, coerência e custo por minuto.

**Decisão:** guardar a separação observação → proposta → validação → ação como referência para simulações. Não mede comportamento humano nem capacidade geral do modelo. Reabrir se existir um produto de simulação definido; não gastar para assistir outra demonstração.

### 12 · SemIf, anteriormente OpenJev — trilha local separada

[URL fornecida](https://github.com/TheoLeeCJ/openjev) · Python/CUDA ou demonstração WebGPU · MIT no código; pesos têm licenças próprias.

**Função:** reproduz o padrão de decisões tipadas com modelos abertos, lendo escores de opções. Ler `examples/`, `benchmarks/`, `docs/REPRODUCE.md`, `results/raw/` e `webgpu-demo/`. Não é o modelo Jev nem sua reprodução de treinamento.

**Perguntas:** atende ao corpus português em hardware disponível? A quantização altera as decisões? O desempenho inclui download/carregamento? Reuso de estado modifica respostas? A economia de API compensa memória, energia e manutenção?

**Teste futuro:** exatamente o corpus do CLI, revisão fixa dos pesos, CPU/GPU e precisão numérica registrados. Comparar partida fria e operação aquecida; não comparar número BF16 nativo com experiência quantizada de navegador como se fossem iguais.

**Decisão:** adiar até haver requisito de execução local. O README distingue resultados locais de registros Jev publicados por terceiros; não demonstra equivalência entre os modelos. Sem aluguel de GPU nesta rodada de US$ 5.

### 13 · pi-model-router — testar a política antes da extensão

[Repositório](https://github.com/redrossa/pi-model-router) · Pi, Node.js 20+.

**Função:** classifica a mensagem com contexto recente e mapeia categoria para lista priorizada de modelos disponíveis. Ler `src/jev.ts`, `router.ts`, `context.ts`, `extension.ts` e `config/default-criteria.json`. O cliente observado usa TypeSafe e `jev-latest`; retorna ao modelo anterior ao fim do turno conforme a lógica da extensão.

**Perguntas:** classificar “coding” identifica quem resolverá melhor? Tarefas mistas e “sim, faça” são encaminhadas corretamente? Histórico truncado perde intenção? Indisponibilidade de um modelo leva a fallback adequado? O custo do turno completo cai?

**Teste:** 40 tarefas classificadas e 10 conversas curtas; primeiro verificar o destino escolhido sem executar modelos. Depois comparar desempenho real dos candidatos apenas numa subamostra viável.

**Decisão:** útil para ergonomia, ainda sem demonstração de escolha ótima. Janus decide sobre escalada por confiança; este projeto escolhe por categoria. São complementares, não equivalentes. Não atribuir economia a um acerto de categoria.

### 14 · should-ai-kill-us-all — retirar como benchmark

[Repositório](https://github.com/hellogumbo/should-ai-kill-us-all) · Cloudflare Pages/KV · CC0.

**Função:** agrega manchetes selecionadas, faz perguntas de veredito/risco e mostra pedido e resposta. Ler `functions/api/verdict.js`. Há cache e contenção de chamadas; atualização por requisição/cache não deve ser confundida automaticamente com agendamento garantido a cada dez minutos. O código consultado inclui quatro perguntas, apesar de um trecho do README dizer três.

**Perguntas aproveitáveis:** as fontes estão disponíveis? Notícias repetidas ou antigas inflam o indicador? Trocar fontes inverte o resultado? O custo e a frescura ficam visíveis?

**Por que eliminar:** “a IA deve matar a humanidade?” não possui rótulo observável de acerto; a estimativa de sobrevivência não ganha validade pela saída numérica. O conjunto selecionado de notícias também impede interpretá-la como amostra representativa do mundo.

**Reaproveitamento:** monitor factual de eventos, com categorias auditáveis, links, datas, deduplicação e alarmes. Isso seria outro experimento, compartilhando o protocolo do Jev Search. Manter a referência, retirar o veredito da bateria de qualidade.

### 15 · Jeeves — separar classificador e produto de moderação

[Repositório](https://github.com/Infrawrench/Jeeves) · Rust/Tokio/Twilight/SQLx/QuickJS, PostgreSQL, Gemini, Discord/Twitch.

**Função:** transforma regras em linguagem natural em avaliações de mensagens/histórico e ações. O escopo atual inclui Twitch, além de Discord. Ler `src/typesafe/client.rs`, `add_action/`, `message_actions/`, `moderation/`, `gemini.rs` e `twitch/`. Gemini também trata imagens e regras computacionais; o resultado não é atribuível só ao Jev.

**Perguntas:** distingue ironia, citação e infração em português? Uma mensagem antiga leva a punir o autor atual? Contagens e janelas temporais são corretas? Regras concorrentes se contradizem? Funciona em canais separados?

**Teste futuro:** 100 mensagens sintéticas/consentidas com contexto e regra explícita, incluindo negativos difíceis; medir violações perdidas e falsos positivos. Exercitar contagem/tempo com código determinístico. Registrar apenas propostas de ação na avaliação inicial.

**Decisão:** adiar o bot completo. Se moderação virar prioridade, usar primeiro o CLI para medir a parte semântica; banco, OAuth e ações reais não ajudam a responder se o classificador presta.

## 5. Achados de código que precisam entrar no desenho dos testes

Estes são achados de inspeção estática, não falhas reproduzidas em execução:

| Achado | Consequência prática | Evidência na revisão consultada |
|---|---|---|
| O CLI devolve tokens e substitui uso ausente por zero; seu retorno normalizado não preserva um campo de custo monetário | Não usar esse zero como evidência de chamada gratuita; orçamento precisa reconciliar a resposta/cobrança original | [provider.ts](https://github.com/Nasrallah-AL/jev-cli/blob/02ca80177aaef0b30a897959207f99df1e0c8446/src/provider.ts) |
| Janus mede, varre limiares e escolhe a política sobre as mesmas linhas recebidas | Acrescentar validação em conjunto reservado, sem escolher novamente o limiar nele | [measure.py](https://github.com/FirasSX914/Janus/blob/9cb66c488cf884e5997356a0de45f75aa3148774/src/janus/measure.py) |
| jevcal usa `HOLDOUT_SLACK = 0.02`; o status `ok` não é uma garantia literal de atingir a meta na reserva | Conferir contagens e precisão observadas, além do status. Seu modelo de custo também inclui valores presumidos de fallback | [compile.py](https://github.com/abhixhek/jevcal/blob/ae8f3144d69c9cb0e5e0a2c17f70b9d14714cb9f/src/jevcal/compile.py) |
| A chave de cache de Every combina pergunta normalizada, modo e texto; não inclui versão do modelo | Separar/desativar cache entre versões e variantes do experimento para não reutilizar escore antigo | [cache.py](https://github.com/sufianetaouil/every/blob/aaa72d582a831420dfd23a788e3bc948c798c248/every/cache.py) |

Isso reforça a escolha de um protocolo comum: ferramentas de avaliação também contêm pressupostos que precisam ser examinados.

## 6. Referências que não precisam virar novas frentes

| Referência | Aproveitar | Pergunta de leitura |
|---|---|---|
| [Awesome Jev by TypeSafe](https://github.com/Anil-matcha/awesome-jev-by-typesafe) | Mapa de usos, exemplos e ligações para documentação | O uso possui código e evidência ou só descrição? |
| [Awesome TypeSafe](https://github.com/AbdelStark/awesome-typesafe) | Segunda taxonomia e descoberta complementar | A entrada acrescenta função à nossa lista ou apenas outra implementação? |
| [Skills oficiais](https://github.com/typesafe-ai/skills) | Decomposição em perguntas e referência de contrato; `skills/typesafe-ai/SKILL.md` como material estudado | O que deve ser pergunta ao modelo e o que continua cálculo/regra? |
| [Parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions) | Perguntas independentes sobre estado compartilhado | O lote preserva qualidade e respeita os limites do transporte? |

Manter um catálogo consolidado. A inclusão em dois awesome não constitui duas validações independentes. Skills não foram instaladas; o cookbook não foi executado.

## 7. Onde há redundância real

| Grupo | Parte compartilhada | Parte distinta | Como evitar gastar duas vezes |
|---|---|---|---|
| CLI / Search / Rerank Bench | Relevância e ordenação | Ferramenta genérica / produto / metodologia | Uma coleção de consultas, candidatos e julgamentos alimenta os três |
| Janus / jevcal | Confiança, cobertura e escalada | Política entre modelos / metas por pergunta e regressão | Uma coleta; análises diferentes dos mesmos registros |
| Janus / pi-model-router | Encaminhamento | Correção por fallback / categoria e disponibilidade | Separar acerto do rótulo de sucesso da tarefa final |
| Every / Review / warden | Julgamentos sobre código/ações | Busca por função / revisão de mudança / fiscalização durante execução | Só testar todos quando as três unidades de trabalho forem necessárias |
| CLI / Jeeves | Classificação semântica de mensagens | Infraestrutura e regras do produto de moderação | Medir rótulos antes de configurar o bot |
| Ultrafast / HEIST | Decisão seguida de executor validado | DOM real / mundo simulado | Reutilizar princípios; métricas de sucesso são distintas |
| SemIf / Adapter / Jev | Contrato de decisão | Modelo local / geração adaptada / decisão nativa | Mesmas entradas e rótulos, custos e latências contabilizados separadamente |

## 8. Perguntas científicas que decidem adoção

1. **Validade:** qual erro queremos reduzir e quem define a resposta correta antes de ver o modelo?
2. **Ganho incremental:** Jev supera regra/AST/BM25 ou apenas uma comparação fraca?
3. **Calibração:** entre decisões aceitas, qual taxa real de acerto, em quantos casos e com que incerteza?
4. **Robustez:** paráfrase, negação, ordem de opções/candidatos, extensão do texto e português mudam o resultado?
5. **Generalização:** funciona em documentos e tarefas que não orientaram perguntas nem limiares?
6. **Operação:** o custo inclui falhas, retries, fallback, busca e revisão humana? Qual a latência p95?
7. **Abstenção:** reconhece falta de resposta e ausência de evidência? Como o software trata saída incompleta?
8. **Causalidade:** ao retirar Jev e conservar o resto, o sistema piora de maneira útil e repetível?

### Protocolo mínimo proposto

**Congelar antes das chamadas:** tarefa, exemplos, rótulos, rubrica, versões, critérios de sucesso e orçamento por lote. Rótulo humano deve vir antes da predição; conflitos ficam marcados e adjudicados. Casos gerados artificialmente servem para falhas controladas; a decisão de adoção precisa incluir exemplos representativos do trabalho real.

**Separar desenvolvimento, calibração e teste:** divisão inicial 40% / 30% / 30%, agrupada por documento, conversa ou origem para impedir vazamento entre paráfrases. Com poucos itens por classe, ampliar a amostra ou assumir resultado exploratório. O teste final permanece intocado; revisão posterior abre uma nova versão do experimento. Os tamanhos das fichas são pilotos: não garantem suporte para estimar limiares. jevcal exige por padrão ao menos 30 aceitos no ajuste; subdividir um piloto pequeno pode legitimamente resultar em nenhum limiar elegível.

**Comparadores:** regra determinística aplicável; Jev; um LLM fixo; cascata quando a tarefa justificar. Para busca, conservar o mesmo conjunto de candidatos. Para agentes, conservar objetivo e verificador de resultado. Executar variantes em ordem alternada quando a latência for medida.

**Critérios iniciais de avanço — metas de engenharia propostas, não fatos sobre Jev:**

| Uso | Medida principal | Sinal para ampliar o teste | Sinal para interromper/reformular |
|---|---|---|---|
| Classificação | Macro-F1 e erros por classe | Até 2 pontos percentuais de perda ante LLM, com pelo menos 30% de redução de custo ou latência | Perda concentrada em classe importante ou economia ausente |
| Apoio de alegação | Falso apoio, precisão dos aceitos e cobertura | Nenhum falso apoio nos casos críticos do piloto; cobertura útil | Fonte silenciosa/contraditória aceita como apoio com alta confiança |
| Reranking | nDCG@10 + recall da recuperação | Ganho pareado frente à ordem original sem perder fontes essenciais | Ganho desaparece fora da amostra ou em casos sem resposta |
| Fiscalização | Detecção residual e falsos bloqueios | Ganho além das regras, falso bloqueio até 5% no piloto | Interrompe ações legítimas sem reduzir violações |
| Código | Precisão entre primeiros achados e tempo de confirmação | Encontrar defeitos confirmados que a referência perdeu | Maior trabalho para eliminar suspeitas do que para revisar diretamente |
| Roteamento | Qualidade final, custo e latência do turno | Mantém qualidade no teste reservado e reduz custo total | Só acerta categoria, mas escolhe modelo pior ou mais caro |

Reportar contagens, diferenças pareadas e intervalos quando o tamanho permitir. “Zero erros em dez exemplos” é só observação do piloto; não valida precisão de 99%. ECE em amostra pequena é instável. Brier faz sentido para probabilidades com rótulos compatíveis; uma nota ordinal de severidade não deve ser tratada automaticamente como probabilidade.

### Ordem executável quando passarmos aos testes

1. **Contrato e custo:** poucas entradas triviais via Jev CLI/OpenRouter; verificar tipos, opções, versão, uso e cobrança. Não executar antes do controle global de orçamento.
2. **Decisões básicas:** classificação e alegação–evidência; LLM comparador; registrar todas as saídas para reaproveitamento.
3. **Calibração:** Janus/jevcal sobre os registros. Aceitar “não rotear” como resultado legítimo.
4. **Busca:** candidatos congelados; rubrica, relevância binária e ordem original. Só depois Search1API ao vivo.
5. **Escolher uma aplicação:** Every, roteador ou warden conforme utilidade e saldo. Não distribuir o orçamento restante entre todas.

## 9. Orçamento de até US$ 5

**Esta fase consumiu US$ 0 da chave.** O orçamento é cumulativo entre projetos, execuções e tentativas. Não foi criado controle executável nem alterado limite da conta: nesta entrega existe o plano para implementá-lo antes da primeira inferência.

| Reserva proposta | Teto |
|---|---:|
| Verificação de contrato/cobrança | US$ 0,10 |
| Classificação e apoio de alegações, incluindo comparador | US$ 1,20 |
| Reranking e perturbações | US$ 0,90 |
| Comparação entre modelos/cascata, reutilizando coleta | US$ 0,80 |
| Uma aplicação condicional | US$ 0,50 |
| Margem não programada para variação/retentativas | US$ 1,50 |
| **Total máximo** | **US$ 5,00** |

Esses são envelopes de alocação, não previsão de gasto. **Planejar somente US$ 3,50 de chamadas; preservar US$ 1,50 de margem.** Search1API, Gemini direto, GPU e hospedagem não estão financiados por essa chave nem autorizados como despesas adicionais. O custo total de um fluxo não pode ser omitido porque sai de outro provedor.

Antes de inferir, o executor precisa de registro persistente único com gasto confirmado e reservado, limite por requisição e por repetição, versão/preço fixados e parada automática. Toda requisição em andamento reserva seu custo máximo; timeout não significa gratuidade. Se o endpoint não fornecer informação suficiente para limitar e reconciliar a cobrança, parar antes de continuar. `OPENROUTER_TEST_BUDGET_USD` sozinho não limita a API.

Exemplo apenas aritmético: 1.000 chamadas com 2.000 tokens de entrada cada, à tarifa publicada de US$ 0,042/M, dariam US$ 0,084 para Jev. O número não inclui perguntas maiores, fallbacks ou outras APIs e não define tamanho autorizado de lote. Estimar sobre a requisição completa e a cobrança efetiva.

## 10. Estrutura para começar

Já disponíveis nesta pasta:

```text
JEV/
  docs/TRIAGEM-JEV-HELENA.md       decisão, fichas e protocolo
  research/FONTES.md              links de arquivos nas revisões consultadas
  research/sources-manifest.json  URLs, hashes, data e estrutura dos 18 repos
  research/collect_sources.py     registro do procedimento de coleta
  research/sources/              cópias locais, ignoradas pelo Git
  AGENTS.md                      instruções e orçamento cumulativo
  .env                           credencial local; não integra a pesquisa
```

Estrutura proposta para a etapa posterior, **ainda não implementada**:

```text
experiments/
  protocol/        rubricas, critérios e configuração por versão
  datasets/        itens, procedência, rótulos e partições congeladas
  predictions/     respostas brutas, modelo, tokens, custo e duração
  budget/          registro cumulativo e reservas de chamadas
  reports/         métricas, falhas e decisão de continuar/descartar
```

Campos mínimos de um item: `id`, tarefa, idioma, origem, texto/estado, pergunta, opções, rótulo, justificativa do rótulo e grupo de partição. Campos de execução: hash de entrada/pergunta, commit, modelo solicitado/devolvido, provedor, tentativa, resposta completa, erro, latência, tokens e custo confirmado/estimado. Sem a credencial em qualquer desses registros.

**Informações ainda necessárias para execução:** um primeiro corpus do trabalho real; definição das classes e erros mais caros; modelo comparador com preço verificado; confirmação técnica do contrato/custo no OpenRouter. Pi, Search1API, Gemini e hardware local só precisam ser resolvidos se a aplicação correspondente avançar.

## 11. Contra-hipóteses e decisão final de Helena

**O que pode refutar minha prioridade:**

- **Regras bastam.** Se AST/BM25/expressões simples atingirem o objetivo com menos trabalho, a melhor decisão pode ser não usar Jev naquele fluxo.
- **Português muda a conclusão.** Um modelo excelente em exemplos ingleses pode errar fronteiras semânticas do nosso corpus. A prioridade cai se a adaptação de perguntas não resolver.
- **A integração consome a vantagem.** Latência de proxy, manutenção de adaptadores e confirmação humana podem custar mais que os tokens poupados. Medir o fluxo completo pode inverter a escolha.

**Cenários de trabalho, sem probabilidades inventadas:** no favorável, Jev vira componente barato para algumas decisões recorrentes; no intermediário, fica restrito a triagem/ordenação com revisão; no desfavorável, regras ou um LLM existente resolvem melhor e o estudo evita instalar aplicações desnecessárias.

**Confiança:** alta na distinção entre funções e nas incompatibilidades observadas nos clientes; média na prioridade de utilidade, pois o corpus real ainda não foi escolhido; desempenho local ainda desconhecido. Não existe base para atribuir uma probabilidade numérica de adoção.

**Recomendação concreta:** começar posteriormente com o Jev CLI e uma avaliação compartilhada, acrescentar reranking e só então escolher uma aplicação. Manter as demais como referência, preservando o direito de concluir “não vale usar” quando o ganho não aparecer.

— **Helena Strategos Inteia**  
*Cientista-Chefe de Inteligência — dados antes de opinião.*
