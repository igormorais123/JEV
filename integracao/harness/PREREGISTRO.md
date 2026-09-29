# Instalação e avaliação no Codex — 21/09/2026

Pedido: instalar e exercitar os 16 sistemas citados para decidir sua utilidade no harness do Codex.

Antes das chamadas: registrar revisão de cada fonte, instalação isolada, testes offline e uso de componente separadamente. Teste sintético não será descrito como produção. Os gabaritos são do assistente, não humanos independentes.

Hipóteses: (H1) ferramentas de classificação, evidência e busca são acessíveis pelo MCP; (H2) testes antigos podem falhar por ambiente, não por qualidade do modelo; (H3) extensões Pi e aplicações de jogo/moderação não são plugins nativos Codex; (H4) a integração deve negar envio quando a carteira histórica ou preços não puderem ser verificados.

Critérios: instalação comprovada por comando executável; integração por initialize/tools/list/tools/call no processo MCP; qualidade por casos com resposta esperada congelada antes do envio; indisponibilidade externa registrada, sem substituir por resposta simulada. Resultados de simuladores explicitamente identificados.

Nenhuma chave será entregue aos repositórios externos. Chamadas reais passam exclusivamente por executor/shared.py e carteira em runs/ledger.sqlite3; teto TOTAL US$ 5. A ausência do banco exige reconciliação prévia dos gastos e não autoriza abrir uma carteira zerada. Modelos/esforço/permissões permanecem sob controle do Codex e do usuário.

Aplicações web serão locais. Não conectar Discord/Twitch, publicar resultados ou executar moderação em contas reais. Código de exemplo sintético e código público são o corpus inicial. A instalação não autoriza exportação de arquivos privados.
# Complemento: painel e Every, 21/09/2026

Antes da chamada ao Every: `fixtures/exemplo.py` contém somente duas funções sintéticas. Pergunta congelada: "Does this function strip whitespace from a string?". Esperado: `normalize` sim, `add` não. Usar `--no-cache --yes --json --above 0.5`, no transporte compartilhado. Este teste verifica integração e separação de um positivo/negativo simples; não mede detecção de bugs de produção. No painel, o log sintético ModuleNotFoundError deve ser classificado como dependência. Resultados e recibos preservados no histórico local.

## Camada para agentes

Antes do ensaio da API v1: submeter o mesmo pedido lógico duas vezes com a mesma chave deve retornar um único job, sem segunda inferência. Fixture: AFIRMAÇÃO "O pagamento foi realizado."; FONTE "O pagamento foi agendado para amanhã, mas ainda não foi executado.". Esperado: `contradito`. A execução real usa a carteira compartilhada ativa. Repetição idempotente não é experimento de estabilidade do modelo. Os demais testes usam servidor temporário, subprocessos locais ou inferência explicitamente simulada.
