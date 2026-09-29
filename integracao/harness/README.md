# Ferramentas Jev no harness do Codex

Instalação e testes: 21/09/2026. Veja `resultados.json` e `RELATORIO.md` nesta pasta.

## Operação por agentes

A entrada principal para agentes é [AGENT-GUIDE.md](AGENT-GUIDE.md). Ela inclui um prompt pronto para delegar a tarefa, contrato HTTP, uso do MCP e recuperação de falhas. A skill `jev-harness` também está disponível como pacote em `skill/jev-harness/`.

```powershell
python integracao/harness/agent_cli.py bootstrap
python integracao/harness/agent_cli.py manifest
python integracao/harness/agent_cli.py status
```

O MCP v2 expõe descoberta, preview, submit idempotente, consulta, espera, logs paginados, cancelamento e configuração. API v1: `http://127.0.0.1:8767/api/v1/manifest`. O agente não precisa abrir o HTML. Todos esses caminhos usam o executor e o histórico do painel; não há cliente pago paralelo. Reinicie a sessão do Codex para recarregar o catálogo MCP; o CLI está disponível imediatamente.

Chaves idempotentes persistem no SQLite junto do hash do pedido e ID do agente. Reenvios idênticos retornam a mesma execução, inclusive depois de reiniciar; pedidos diferentes com a mesma chave falham. Não há retomada automática de inferência interrompida. O texto de entrada não é guardado.

## Central HTML

Abra **http://127.0.0.1:8767**. O painel oferece catálogo das 16 ferramentas, busca, filtros, pausa das operações por ferramenta, execução de testes, replays, demonstração jevcal, avaliação real do CLI, histórico persistente e cancelamento de subprocessos. A área **Usar o JEV** envia logs, evidências e contexto ao transporte compartilhado. Carteira e saldo são consultados ao vivo.

O Every também tem a ação **Analisar código de exemplo**, com duas funções sintéticas. A rodada real separou corretamente `normalize` (0,97) de `add` (0,04), no corte de 0,5.

Para iniciar novamente no Windows:

```powershell
powershell -ExecutionPolicy Bypass -File C:/Users/igorm/projetos/JEV/integracao/harness/abrir-painel.ps1
# Ou, com console e encerramento por Ctrl+C:
python integracao/harness/painel.py
```

Histórico e preferências ficam em `integracao/estado/harness/painel.sqlite3`, ignorado pelo Git. Logs do servidor ficam em `integracao/estado/harness-server*.log`. Uma única instância é permitida por histórico. O painel escuta somente em 127.0.0.1 e aceita somente operações cadastradas; não existe terminal livre nem leitura arbitrária de arquivos. Limite de duas operações simultâneas e seis minutos por subprocesso. Requisições pagas já enviadas precisam concluir a contabilização.

Pausar uma ferramenta desabilita novos acionamentos **neste painel**; não desinstala, não cancela trabalhos ativos e não muda permissões do Codex. A presença das fontes não comprova que toda integração externa esteja configurada. Os cartões mantêm o retrato dos testes; execuções novas aparecem separadamente no histórico.

## O que está disponível

O MCP `jev-harness` foi registrado no Codex. Uma nova sessão carrega:

- `harness_catalog`: resultado e limitações dos 16 sistemas, sem rede.
- `harness_offline`: replay Janus, demonstração simulada jevcal e ajuda de CLI/Every.
- `harness_status`: carteira, catálogo e histórico da central em funcionamento.
- `harness_test`: inicia a suíte de uma ferramenta pela central, respeitando pausas e concorrência.

Para classificações e ordenação de contexto, use o MCP `jev` da integração existente e sua skill `jev-assist`. Este pacote não muda modelo, esforço ou permissões do Codex. Pi Warden e Pi Model Router continuam extensões do Pi, sem fingir integração nativa no Codex.

## Comandos de uso

Execute no repositório JEV. Caminhos de documentos/código devem ser absolutos, pois cada ferramenta roda na própria pasta. Não envie código privado de outros projetos sem autorização.

```powershell
# Ferramentas sem inferência paga
python integracao/harness/usar_ferramenta.py Janus -- measure --task banking77
python integracao/harness/usar_ferramenta.py Janus -- measure --task wos
python integracao/harness/usar_ferramenta.py jevcal -- demo

# Usam exclusivamente a carteira compartilhada; bloqueiam se ela estiver ausente
python integracao/harness/usar_ferramenta.py jev-cli -- classify "O aplicativo fecha ao abrir um arquivo" --labels bug,melhoria,outro --json
python integracao/harness/usar_ferramenta.py jev-cli -- verify "O pagamento foi realizado" --evidence "O pagamento esta apenas agendado" --json
python integracao/harness/usar_ferramenta.py every -- --selftest
python integracao/harness/usar_ferramenta.py jev-review -- C:/caminho/absoluto/do/repositorio-autorizado

# Studio: dois processos locais; a chave real não vai para o aplicativo
python research/sources/jevstudio/game/game_server.py
python integracao/harness/usar_ferramenta.py jevstudio
# Abra http://127.0.0.1:8000/arena.html
```

O launcher dá a cada execução uma ponte local autenticada, com até oito requisições; cada uma passa por `executor/shared.py` e seu perfil financeiro ativo. Em 21/09 está ativo o perfil TypeSafe separado, autorizado anteriormente, com teto acumulado de US$ 0,03. Sem esse perfil, aplicam-se a carteira histórica e seus limites existentes. Esta integração não cria nem amplia carteiras. O recibo do transporte compartilhado é o registro financeiro; estimativas impressas por ferramentas externas não substituem esse recibo. O limite de oito requisições torna varreduras extensas do Every e revisões extensas incompletas: use escopo pequeno e confira erros.

Janus e jevcal só têm operações offline liberadas pelo launcher. Seus clientes pagos originais não passam automaticamente pela carteira. Ultrafast também tem um modelo textual adicional; instalar o pacote não autoriza cobrar por esse caminho externo.

## Estado das chamadas reais

O bloqueio inicial por ausência da carteira histórica foi superado para esta etapa pela configuração externa do perfil TypeSafe autorizado de US$ 0,03. A ponte foi atualizada para respeitar esse perfil. A carteira histórica continua independente; não foi reconstruída nem zerada.

`python integracao/usar.py --status` informa a condição atual. O corpus de integração em `corpus.json` foi congelado antes de chamadas. `python integracao/harness/avaliar_ao_vivo.py` executou sete casos no CLI real: **7/7 corretos**. Saída em `runs/harness-20260921/live.json`. Não repete chamadas com erro. Esse conjunto é um smoke test sintético, não certificação de qualidade dos 16 sistemas. O preço do perfil deve estar dentro da validade de 24 horas; bloqueios são exibidos sem trocar de carteira.

## Reproduzir verificações

```powershell
python -m unittest integracao.harness.test_agents integracao.harness.test_painel integracao.harness.test_ponte integracao.harness.test_componentes -v
node integracao/harness/test_news.mjs
```

`auditar_instalacoes.py` registra instalações e testes por projeto, em `runs/harness-20260921/`. Não entrega credenciais reais aos subprocessos. Houve correções e comandos complementares documentados no relatório: o script inicial sozinho não reproduz todas as correções.

Jev Search usa Node x64 nesta máquina ARM, em `tmp/harness/node-v24.16.0-win-x64/`. Seus 68 testes e build passaram após instalar pnpm 10.8.0 e gerar as rotas. A busca real ainda exige Search1API.

Jeeves exige Rust x64 e o ambiente MSVC x64; a cadeia ARM misturada às bibliotecas x64 falhou. Os comandos usados estão nos logs e scripts em `tmp/harness/`. O banco PostgreSQL e as contas Discord/Twitch não foram configurados.

## Remover somente a integração deste trabalho

```powershell
codex mcp remove jev-harness
```

Isso preserva o MCP `jev`, a carteira e os estudos. Os ambientes dos projetos ficam em `research/sources/`, ignorados pelo Git. As alterações próprias anteriores e simultâneas do usuário foram preservadas; não houve commit nem push.
