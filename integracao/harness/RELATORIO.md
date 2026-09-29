# Instalação e avaliação local dos 16 sistemas

Data: 21/09/2026. Windows ARM64, Node 24.16, Python 3.14; ambientes Python dos projetos usam 3.13 x64. Revisões exatas em `resultados.json`. Logs em `runs/harness-20260921/`.

**Atualização da implementação:** a central HTML está em http://127.0.0.1:8767, com operações reais, histórico e diagnóstico financeiro. O perfil TypeSafe autorizado separadamente, de US$ 0,03, passou a estar disponível e foi respeitado pela ponte. O CLI acertou **7/7 casos sintéticos** com inferência real; o formulário também realizou uma classificação real de log, com recibo. Isso valida esses caminhos de integração, não a qualidade dos demais sistemas. Na instalação inicial não houve chamadas pagas por ausência da carteira histórica; ela não foi recriada.

| Sistema | Para que serve, em termos simples | Resultado observado nesta rodada | Decisão para o Codex |
|---|---|---|---|
| Jev CLI | Classifica texto, extrai campos e verifica afirmações pelo terminal. | 180 testes passaram; 4 falharam por caminhos/permissões Windows. Build e tipagem passaram. Corrigido erro real de data/fuso; integração CLI→ponte exercitada com resposta simulada. | Manter instalado; candidato direto a apoio. 7/7 casos sintéticos reais corretos; qualidade em produção ainda pendente. |
| Every | Examina funções do código e pede julgamentos estruturados. | 78 passaram, 2 ignorados; extração real de duas funções sintéticas conferida. | Manter para escopos pequenos; launcher compartilhado validado em duas funções sintéticas (2/2). Falta medir falsos positivos em código real autorizado. |
| Jev Review | Produz uma revisão automatizada de alterações. | Tipagem e `check` passaram, incluindo 17 verificações de dependências e sintaxe do dashboard. Não é uma avaliação de detecção de bugs. | Manter experimental; launcher pronto. Falta revisão real comparada a defeitos conhecidos. |
| Janus | Compara quando encaminhar uma tarefa para modelos diferentes. | 38 testes passaram. Replay banking77: 80,2% de acerto, +1,4 ponto e −53% de custo frente às referências do relatório. WOS: 52,8%, mesma qualidade e +47% de custo. | Útil para estudar roteamento. Não ativar roteamento genérico: WOS recomendou DO NOT ROUTE. Dados históricos, não novas chamadas. |
| jevcal | Ajuda a escolher limites de confiança e custo antes de adotar uma decisão automática. | 24 testes passaram; demo gerou relatório com 400 linhas sintéticas. | Manter como instrumento de avaliação. A demo não prova qualidade do Jev. |
| Jev Rerank Bench | Mede se reordenar documentos melhora a seleção de contexto. | 9 testes passaram; dependências instaladas. | Manter para medir o harness. Falta executar avaliação real com corpus e relevâncias congelados. |
| Jev Search | Busca na web e organiza resultados. | 68 testes passaram; rotas geradas e build passou usando Node x64. | Instalação pronta para desenvolvimento; busca efetiva pendente de Search1API e integração financeira do cliente de inferência. |
| Jev Ultrafast | Agente para operar páginas no navegador. | 31 testes passaram. Navegação autônoma com modelo real não executada. | Manter experimental. Falta integrar seus provedores à carteira e comparar tarefas reais com o navegador já disponível no Codex. |
| System One Adapter Python | Adapta sistemas/modelos para uma interface comum de decisões. | 198 testes passaram, 31 falharam após permitir loopback nos testes; falhas restantes envolvem fixtures/cassettes e autenticação simulada. | Ambiente instalado, adoção pendente. Não considerar conector validado de ponta a ponta. |
| OpenJev / SemIf | Explora decisões locais sem chamar uma API a cada julgamento. | 15 testes e 69 verificações de alegações publicadas passaram. PyTorch está em CPU; CUDA indisponível. | Manter para pesquisa. Pesos e desempenho de inferência local nesta máquina não foram validados. |
| Pi Model Router | Seleciona modelos dentro do agente Pi. | 58 testes e tipagem passaram após corrigir caminho Windows. | Funciona como extensão do Pi; não é extensão nativa do Codex. Não controla esforço/modelo deste harness. |
| Pi Warden | Analisa e controla operações do agente Pi. | 206 testes passaram, 4 falharam em pressupostos de caminhos/permissões; build e tipagem passaram. | Não ativar como guardião do Codex: a ligação com suas permissões não existe aqui. |
| Jev Studio | Interface visual para montar e observar experiências com Jev. | 177 verificações dos seis scripts passaram individualmente. Interface abriu; conexão e contrato com jogo funcionaram. Inferência foi bloqueada pela carteira ausente. | Manter como laboratório visual, não como evidência de ganho do Codex. |
| HEIST ONE | Jogo que demonstra decisões de agentes. | 6 testes, tipagem e build passaram. Jogo abriu e avançou em modo SCRIPTED. | Instalado como demonstração; não acrescenta uma função operacional ao Codex. |
| Jeeves | Bot com integrações de comunidades, como Discord/Twitch. | Build Rust x64 passou; 100 testes passaram e 24 foram ignorados porque exigem PostgreSQL. | Binário pronto; serviço não configurado. Não há integração direta com Codex; banco e contas ainda necessários para uso como bot. |
| Should AI Kill Us All | Demonstra classificação de notícias em uma aplicação web. | 2 verificações próprias do Worker passaram, usando RSS/cache simulados. Sem avaliação real da classificação. | Manter como exemplo de implementação; não é uma ferramenta geral de apoio ao Codex. |

## O que foi efetivamente integrado

Na continuação com a central HTML, o **Every também foi exercitado com inferência real**: em duas funções sintéticas pré-registradas, atribuiu 0,97 à função que remove espaços e 0,04 à função de soma (2/2 classificações corretas no corte 0,5). Corrigido um defeito do launcher: trocar a variável global da URL não alterava o argumento padrão já capturado pelo Python. O wrapper agora injeta explicitamente o endpoint da ponte e limita tentativas. O primeiro ensaio recebeu 401 usando apenas token efêmero, sem decisão paga; a chamada corrigida passou pela carteira compartilhada. O recibo está em `resultados.json`.

O painel gerencia as 16 entradas, executa suas suítes locais e oferece operações adicionais para CLI, Every, Janus e jevcal. A bancada usa `jev_assist` para log, evidência e contexto. As aplicações externas que exigem contas, banco, pesos ou adaptações permanecem com essas dependências explícitas; não estão sendo anunciadas como 16 integrações nativas completas.

MCP `jev-harness` registrado no Codex, com catálogo dos resultados e cinco operações locais limitadas: dois replays Janus, demo jevcal e ajuda CLI/Every. O protocolo foi testado em subprocesso. Uma nova sessão do Codex é necessária para carregar a configuração.

CLI, Every, Review e Studio têm launchers destinados ao transporte compartilhado existente; CLI e Every foram verificados com inferência real nesta continuação, Review e Studio ainda precisam dessa validação completa. A ponte usa token efêmero, loopback, limite de oito requisições e a subcota `tools`; não entrega a chave real aos aplicativos. A suíte ampliada tem 11 testes aprovados, incluindo painel, cancelamento, ponte, CLI, Every e MCP. Isso comprova o encaminhamento e os bloqueios, não a qualidade das respostas. O limite pode interromper varreduras extensas; confira os erros.

As ferramentas de classificação/ordenação do MCP `jev` existente continuam sendo a integração operacional principal. Este trabalho não redefine permissões, modelo ou esforço do Codex. Ter os 16 repositórios instalados não torna 16 ferramentas nativas disponíveis ao agente.

## Correções e instalação reproduzível

- CLI: preservação correta de datas ISO sem deslocamento de fuso. Patch em `patches/jev-cli-windows.patch`.
- Pi Model Router: conversão de URL de arquivo para caminho Windows. Patch em `patches/pi-model-router-windows.patch`.
- Studio: incluído `alvo` ausente nos seis arquivos de trabalho dos jogos, apontando para o servidor local de porta 8100.
- Search: Node oficial x64 em `tmp/harness/node-v24.16.0-win-x64/`, pnpm 10.8, instalação congelada, geração de rotas e build. O runtime workerd ARM não funcionou.
- Jeeves: Rust stable x64 e ambiente MSVC x64. Scripts de build/teste em `tmp/harness/`; binário em `research/sources/Jeeves/target/x86_64-pc-windows-msvc/debug/jeeves.exe`. O Docker não apresentou engine disponível e PostgreSQL não foi iniciado.

Os ambientes e clones estão em `research/sources/`, ignorados pelo Git. Os patches estão preservados nesta integração; nenhuma publicação foi feita. Logs registram também tentativas que falharam; os números da tabela são os resultados finais explicitamente descritos, não a soma das tentativas.

## Dúvidas ainda abertas para uma decisão definitiva

1. Verificar saldo e validade de preços do perfil ativo antes de qualquer inferência. O teste `avaliar_ao_vivo.py` passou nos sete casos sintéticos do CLI; não valida sozinho os demais sistemas.
2. Medir CLI, Every e Review contra respostas/defeitos conhecidos, incluindo falsos positivos, custo e tempo. Ainda não há prova nova de economia de contexto ou tempo do Codex.
3. Avaliar reordenação com documentos reais autorizados; reproduzir Janus/jevcal em dados da tarefa antes de escolher limites.
4. Search e Ultrafast precisam de configuração e adaptação financeira adicionais. O adapter precisa resolver as 31 falhas antes de ser tratado como base confiável.
5. Testar pesos locais do SemIf e tempo em CPU se essa linha continuar relevante. Jogos, notícias e bot só justificam uso efetivo para suas próprias finalidades, não por serem do mesmo ecossistema.

Comandos de uso e remoção estão em `README.md`. A recomendação de manter ferramentas é provisória onde ainda falta inferência real; não declarar esta rodada como aprovação completa dos 16 sistemas.
