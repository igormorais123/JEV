# Arquitetura do JEV: fonte editável

Fonte completa do PDF “Arquitetura do JEV” (14 páginas, A4 paisagem): textos de cada página, sistema visual, código SVG dos oito diagramas, gerador dos diagramas, folha de estilo e montador do PDF. Tudo o que o PDF contém está aqui.

## 0. Instruções para quem edita

### 0.1 Onde mexer

| Quero mudar | Onde | Como |
|---|---|---|
| Um texto de página | Parte 2 e, para o PDF, o arquivo `montar.py` (Apêndice D) | Os textos da Parte 2 são os mesmos de `montar.py`; mantenha os dois iguais |
| Palavra, cor ou posição pequena num diagrama | Parte 3, bloco SVG do diagrama | Editar o SVG direto (ver 0.3) |
| Caixa ou seta nova, mudança de fluxo | Apêndice B, `diagramas.py` | Editar a função do diagrama e rodar o montador |
| Cores, fontes, espaçamentos | Apêndice C, `estilo.css`, e constantes de `grade.py` | Manter a paleta da Parte 1 |

### 0.2 Como gerar o PDF

1. Salve os quatro arquivos dos apêndices na mesma pasta: `grade.py`, `diagramas.py`, `estilo.css`, `montar.py`.
2. Instale: Python 3.10 ou superior; `pip install playwright`; `playwright install chromium`; fontes Poppins e Lora.
3. Rode `python3 montar.py`. Saem `arquitetura_jev.html` e `arquitetura_jev.pdf`.

Sem Python, qualquer ferramenta que imprima HTML em A4 paisagem com fundo serve: monte uma `<section class="page">` por página, na ordem da Parte 2, com o CSS do Apêndice C, e cole os SVG da Parte 3 dentro de `<div class="fig">`.

### 0.3 Como ler e editar um SVG daqui

- Unidade: milímetro. O `viewBox` dá a largura e a altura do desenho; o SVG ocupa 100% da caixa onde for colocado e mantém a proporção.
- Cada caixa vem precedida do comentário `<!-- nó ID (tipo) -->`, seguida da forma (`rect` ou, nas condições, `polygon` hexagonal) e de um `text` por linha.
- Cada seta vem precedida de `<!-- seta ORIGEM → DESTINO -->`, é um `path` ortogonal e usa um marcador de ponta definido em `<defs>`. Rótulos de seta são `text` logo após o `path`.
- Texto em negrito: `font-weight="500"` na primeira linha, quando ela está em maiúsculas. Notas: `font-style="italic"`.
- Ao mover uma caixa, mova também as extremidades das setas ligadas a ela. Para mudanças de posição maiores, prefira editar `diagramas.py`: o gerador recalcula as setas.

### 0.4 Regras que o documento segue

- Português do Brasil; voz ativa; frases curtas.
- Sem siglas, exceto o nome JEV.
- Sem legendas explicativas, metadados ou comentários sobre o próprio texto. Cada página traz só título, conteúdo e número.
- Diagramas: condição é hexágono; condições em escada são lidas de cima para baixo; “não” desce, “sim” vai para o lado; a cor da caixa indica o papel, igual em todos os diagramas.
- Tamanho de letra dos diagramas: cerca de 8,6 pontos; o texto de cada caixa precisa caber nela.

## 1. Sistema visual

### 1.1 Página

| Item | Valor |
|---|---|
| Formato | A4 paisagem, 297 × 210 mm, sem margem de impressão |
| Margens internas | 12 mm em cima, 16 mm nas laterais, 14 mm embaixo |
| Fundo | branco com grade de pontos #D9DCEB a cada 5 mm |
| Rodapé | só o número da página, à direita, a 6 mm da base |

### 1.2 Tipografia

| Uso | Fonte | Tamanho |
|---|---|---|
| Título da capa | Poppins 500 | 31 pt |
| Título de página | Poppins 500 | 17 pt |
| Cabeçalho de política: número, nome, pergunta | Poppins 28 pt anil; Poppins 500 17 pt; Lora itálico 13 pt | — |
| Subtítulo de bloco | Poppins 500, anil | 10,5 pt |
| Texto corrido | Lora | 10,6 pt, entrelinha 1,55 |
| Tabelas | Poppins nos rótulos, Lora no conteúdo | 8,8 a 9,8 pt |
| Diagramas | Poppins 400 e 500 | 3,05 mm (cerca de 8,6 pt), entrelinha 3,75 mm |

### 1.3 Cores

| Papel | Cor |
|---|---|
| Texto | #1E2130 |
| Texto secundário | #6A6F84 |
| Acento (números, subtítulos, quadro de produção) | #4B4FC8 |
| Fundo de cartões | #F4F5FB |

### 1.4 Tipos de caixa nos diagramas

| Tipo | Preenchimento | Contorno | Forma | Significado |
|---|---|---|---|---|
| entrada | #FFE8CC | #E8590C | retângulo | o que chega ao sistema |
| cond | #FFF9DB | #E67700 | hexágono | condição verificada |
| decisao | #FFF3BF | #E67700 | hexágono | política do JEV (diagrama de integração) |
| executor | #D0EBFF | #1971C2 | retângulo | agente, modelo ou arquitetura que executa |
| ferramenta | #E5DBFF | #7048E8 | retângulo | ferramenta, bancada, ação externa |
| evidencia | #C3FAE8 | #099268 | retângulo | entrega, observação, validação |
| estado | #DBE4FF | #3B5BDB | retângulo | estado, rótulo, escolha |
| humano | #FFDEEB | #C2255C | retângulo | pessoa, pausa, encaminhamento |
| saida | #D3F9D8 | #2B8A3E | retângulo | resultado final ou destino |
| refazer | #FFE3E3 | #C92A2A | retângulo | falha, encerrar, refazer |
| nota | #F8F9FA | #868E96 tracejado | retângulo, texto itálico | dado de apoio |
| acao | #FFFFFF | #495057 | retângulo | passo de processamento |

### 1.5 Setas

| Estilo | Cor | Uso |
|---|---|---|
| contínua | #4A4F66 | passagem principal |
| contínua ou tracejada | #868E96 | ligação secundária, retorno de resposta, nota |
| tracejada | #C92A2A | volta ao estado ou nova tentativa |
| tracejada | #4B4FC8 | recalibração, nova rodada de medição |
| contínua | #2B8A3E | aprovado, concluir |
| contínua | #C2255C | caminho para uma pessoa |

### 1.6 Grade dos diagramas

Cada diagrama é desenhado numa grade: colunas de 52 a 64 mm, linhas de 18,5 mm, margem de 4 mm. Caixa padrão: largura da coluna menos 10 mm, altura 12,5 mm; caixas com três ou quatro linhas usam altura 1,2 a 1,55 vezes maior. As setas saem do meio de um lado da caixa e seguem trechos horizontais e verticais.

## 2. Conteúdo, página a página

### Página 1: capa

- Título: **Arquitetura do JEV**
- Subtítulo: Um núcleo de decisão e seis políticas: triagem, orquestração de agentes, roteamento de modelos, ciclo de execução, avaliação e comparação.
- Destaque, à direita, em Lora itálico com barra anil à esquerda: *O modelo interpreta texto livre. / O código controla o fluxo.*

### Página 2: Princípios

Seis cartões numerados, em grade de 3 × 2.

1. **Um núcleo, seis políticas.** Toda decisão passa pelo mesmo núcleo, com a mesma ordem de precedência. Cada tipo de decisão é uma política.
2. **Regras antes de modelo.** Cancelamento, conclusão comprovada, limites e regras determinísticas decidem primeiro. O modelo propõe só quando nenhuma regra cobre o estado, e só entre opções permitidas.
3. **Conclusão exige prova.** Cada executor entrega um artefato verificável. A conclusão depende de prova vinda da ferramenta ou dos testes.
4. **Orçamento com reserva.** Parte do limite por tarefa fica reservada para avaliar e responder. O trabalho não consome a reserva.
5. **Efeito externo seguro.** Toda ação com efeito fora do sistema usa chave idempotente. Resposta perdida leva a consulta, nunca a repetição cega.
6. **Autonomia por evidência.** A autonomia cresce por fases e por categoria, conforme a comparação com a linha de base.

### Página 3: Visão geral

Diagrama `p0` (Parte 3), largura total, e três colunas abaixo:

- **Estado persistido.** Fonte única da verdade da tarefa. Toda escrita informa a versão lida; escrita sobre versão desatualizada é recusada e refeita.
- **Núcleo.** Lê o estado, aplica a política da decisão em curso e devolve uma ação permitida ou um encaminhamento. Não executa: quem age são os executores, e o resultado volta ao estado só depois de validado.
- **Registro e bancada.** Cada decisão grava política, opções, escolha, motivo, origem e custo. A bancada, fora da produção, usa esse registro para calibrar os parâmetros.

### Página 4: Núcleo de decisão

Coluna esquerda, **Ordem de precedência**, seis passos numerados:

1. **Cancelamento.** Encerra, mesmo com operação pendente.
2. **Conclusão comprovada.** Prova da ferramenta ou dos testes conclui a tarefa.
3. **Limites.** Voltas, voltas sem progresso, tentativas e saldo. Limite atingido pausa com motivo.
4. **Regras da política.** Decisões determinísticas: baratas, reproduzíveis, auditáveis.
5. **Proposta do modelo.** Saída estruturada, restrita às opções permitidas. Proposta fora da lista é recusada e contada.
6. **Alternativa segura.** A opção de menor risco da política, como coletar evidência ou abster.

Coluna direita, **Regra e modelo por política**:

| Política | Decidido por regra | Modelo |
|---|---|---|
| Triagem | duplicata; alerta crítico | classificar texto livre |
| Orquestração de agentes | máquina de estados com guardas | estado ambíguo |
| Roteamento de modelos | restrições, qualidade mínima, custo, saldo | — |
| Ciclo de execução | reconciliar, concluir, executar, perguntar, buscar | interpretar pedido e resposta do usuário |
| Avaliação | testes, análise estática, escopo, tentativas | rubrica de qualidade |
| Comparação | regra de adoção | — |

### Página 5: Contrato de estado e interfaces

Tabela à esquerda:

| Campo | Função |
|---|---|
| id e versão | correlacionar eventos; recusar escrita sobre versão desatualizada |
| objetivo e critérios de conclusão | o que conta como pronto |
| autonomia | ações executáveis sem pedir aprovação |
| dados, evidências, artefatos | base das decisões e das retomadas |
| pendências | o que falta e por que o sistema continua ou aguarda |
| tentativas, voltas, prazo, saldo | limites de repetição e gasto |
| status e motivo | em andamento, aguardando, concluído, interrompido, encaminhado |
| chave da operação externa | consultar e reconciliar reservas, envios, implantações |
| registro de decisões | política, opções, escolha, motivo, origem, custo |

À direita:

- **Progresso.** Ao fim de cada volta, o núcleo calcula uma impressão dos dados e das pendências. Impressão igual por duas voltas seguidas pausa o ciclo.
- **Espera.** Pergunta ao usuário deixa o estado em “aguardando” e encerra o processo. A resposta chega como evento, é gravada no estado e o ciclo retoma dali, sem repetir a pergunta.
- **Escopo.** O estado guarda fatos, evidências e referências a artefatos. Cada executor recebe só o recorte de que precisa.

Abaixo, quatro interfaces em grade de 2 × 2:

```text
Proponente
propor(politica, opcoes, contexto)
→ { escolha: uma das opcoes, motivo }

Executor
executar(papel, recorte_do_estado)
→ { artefato_do_papel, evidencias }

Ferramenta com efeito externo
executar(parametros, chave) → confirmado | recusado | sem resposta
consultar(chave)            → resultado | nada

Registro de decisão
{ tarefa, versao, politica, opcoes, escolha, motivo, origem, custo, modelo_e_versao, instante }
```

### Páginas 6 a 11: as seis políticas

Cada página tem só um cabeçalho em linha (número anil, nome, pergunta em itálico) e o diagrama ocupando o resto da página.

| Página | Número | Nome | Pergunta | Diagrama |
|---|---|---|---|---|
| 6 | 1 | Triagem | O que chegou, com que urgência e quem assume | `p1` |
| 7 | 2 | Orquestração de agentes | Quem trabalha agora e quando parar | `p2` |
| 8 | 3 | Roteamento de modelos | Quanto de inteligência cada subtarefa merece | `p3` |
| 9 | 4 | Ciclo de execução | Agir sem duplicar, sem adivinhar, sem esperar à toa | `p4` |
| 10 | 5 | Avaliação | O resultado pode seguir? | `p5` |
| 11 | 6 | Comparação | Quando o JEV assume uma categoria | `p6` |

### Página 12: Integração

Cabeçalho: sinal “+”, nome **Integração**, pergunta *Os seis usos num só sistema*. Diagrama `p7`.

### Página 13: Implantação em fases

Quatro cartões lado a lado:

| Fase | Nome | Descrição | Portão |
|---|---|---|---|
| 0 | Linha de base | Bancada com casos reais; processo atual medido com as mesmas medidas; registro de decisões instalado. | medidas estáveis entre repetições; critérios de sucesso aceitos pelos donos do processo. |
| 1 | Modo sombra | O JEV decide em paralelo, sem executar. Decisões comparadas às das pessoas. | triagem na precisão alvo por categoria; nenhuma aprovação com critério obrigatório reprovado. |
| 2 | Autonomia restrita | Ações reversíveis executadas. Ações com efeito externo pedem aprovação. | regra de adoção cumprida na bancada e em amostra de produção da categoria. |
| 3 | Autonomia por categoria | Categorias aprovadas liberadas. Casos rotineiros passam à bateria de regressão. | portão contínuo: regressão perto de 100%; custo e intervenção humana por categoria. Falha grave devolve a categoria à fase anterior. |

Abaixo, **Medidas**:

| Onde | Acompanhar | Tolerância zero |
|---|---|---|
| Núcleo | decisões por origem: guarda, regra, modelo, alternativa; propostas inválidas | — |
| Triagem | precisão e cobertura por categoria; abstenção; tempo até o responsável | incidente classificado como melhoria |
| Orquestração | rodadas por caso; retornos rejeitados; tempo até resolver | conclusão sem artefato validado |
| Roteamento | custo por sucesso por família; escaladas; pausas por saldo | reserva de encerramento consumida |
| Ciclo | voltas por tarefa; reconciliações; tempo em espera | efeito externo duplicado |
| Avaliação | concordância com revisão humana; tentativas por caso | aprovação com critério obrigatório reprovado |

### Página 14: Parâmetros, riscos e base técnica

**Parâmetros**

| Parâmetro | Valor inicial | Recalibrar com |
|---|---|---|
| tentativas de correção | 2 | sucesso na segunda tentativa |
| voltas sem progresso | 2 | pausas resolvidas com uma ação simples |
| voltas por tarefa | 12 | percentil 99 dos casos bem-sucedidos |
| reserva de encerramento | 15% do limite | custo real de avaliar e responder |
| precisão alvo da triagem | 90% | custo de encaminhamento errado por categoria |
| margem de não inferioridade | 2 pontos | perda aceitável para o dono do processo |
| qualidade mínima por família | 0,80 a 0,85 | retrabalho aceitável |

**Riscos e mitigações**

| Risco | Mitigação |
|---|---|
| ação ou categoria inexistente proposta pelo modelo | lista fechada de opções; recusa e contagem |
| ciclo sem fim | limites de voltas, tentativas e progresso |
| orçamento esgotado antes da verificação | reserva de encerramento |
| efeito externo duplicado | chave idempotente e consulta antes de repetir |
| sucesso declarado sem prova | artefato por papel; conclusão comprovada pela ferramenta |
| avaliador por modelo desalinhado | critérios obrigatórios em código; rubrica calibrada |
| comparação enganosa | mesma base com e sem o JEV; conjunto de decisão separado |
| dado sensível no modelo errado | classe de dados como restrição no roteamento |
| atualizações concorrentes | versão no estado |

**Base técnica**, em duas colunas:

- *Building effective agents*. Anthropic, 2024. https://www.anthropic.com/engineering/building-effective-agents
- *Demystifying evals for AI agents*. Anthropic, 2026. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- *FrugalGPT*. Chen, Zaharia e Zou, 2023. https://arxiv.org/abs/2305.05176
- *Making retries safe with idempotent APIs*. Amazon Builders' Library, 2021. https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/

## 3. Diagramas

Cada diagrama tem uma descrição do fluxo, para leitura, e o SVG completo. O SVG abaixo é o mesmo desenho do PDF, com coordenadas arredondadas em duas casas e comentários que identificam cada caixa e cada seta.

### Visão geral (`p0`, página 3)

Tamanho: 268 × 82 mm.

- EVENTOS (normalizados e sem duplicatas) → ESTADO (com versão, limites e saldo do orçamento) → NÚCLEO DO JEV → EXECUTORES (agentes, modelos, ferramentas) → VALIDAR (artefato e resultado).
- MODELO (propõe entre opções) → NÚCLEO, seta cinza tracejada.
- NÚCLEO → PESSOA (abstenção, revisão, aprovação), seta rosa. PESSOA → VALIDAR.
- VALIDAR → ESTADO, seta vermelha tracejada, rótulo “atualiza o estado”.
- NÚCLEO → REGISTRO de decisões → BANCADA fora da produção → NÚCLEO, seta anil tracejada, rótulo “calibra”.

#### SVG `p0`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 268 82.0" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p0-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p0-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p0-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p0-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p0-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p0-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<!-- seta EV → EST -->
<path d="M51.00,31.75 L61.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p0-m-base)"/>
<!-- seta EST → N -->
<path d="M103.00,31.75 L113.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p0-m-base)"/>
<!-- seta N → EXE -->
<path d="M155.00,31.75 L165.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p0-m-base)"/>
<!-- seta EXE → VAL -->
<path d="M207.00,31.75 L217.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p0-m-base)"/>
<!-- seta MOD → N -->
<path d="M134.00,19.50 L134.00,25.50" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p0-m-cinza)"/>
<!-- seta N → PES -->
<path d="M155.00,28.00 L160.00,28.00 L160.00,13.25 L165.00,13.25" fill="none" stroke="#C2255C" stroke-width="0.42" marker-end="url(#p0-m-rosa)"/>
<!-- seta PES → VAL -->
<path d="M207.00,13.25 L238.00,13.25 L238.00,25.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p0-m-base)"/>
<!-- seta VAL → EST -->
<path d="M238.00,38.00 L238.00,73.38 L82.00,73.38 L82.00,39.25" fill="none" stroke="#C92A2A" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p0-m-vermelho)"/>
<text x="160.0" y="72.17" text-anchor="middle" font-size="2.68" fill="#C92A2A">atualiza o estado</text>
<!-- seta N → REG -->
<path d="M123.50,38.00 L123.50,49.55" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p0-m-base)"/>
<!-- seta REG → BAN -->
<path d="M155.00,55.80 L165.00,55.80" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p0-m-base)"/>
<!-- seta BAN → N -->
<path d="M186.00,49.55 L186.00,45.07 L144.50,45.07 L144.50,38.00" fill="none" stroke="#4B4FC8" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p0-m-anil)"/>
<text x="165.25" y="43.87" text-anchor="middle" font-size="2.68" fill="#4B4FC8">calibra</text>
<!-- nó EV (entrada) -->
<rect x="9.0" y="24.25" width="42.0" height="15.0" rx="2.2" fill="#FFE8CC" stroke="#E8590C" stroke-width="0.4"/>
<text x="30.0" y="29.07" text-anchor="middle" font-size="3.05" font-weight="500">EVENTOS</text>
<text x="30.0" y="32.82" text-anchor="middle" font-size="3.05" font-weight="400">normalizados e</text>
<text x="30.0" y="36.57" text-anchor="middle" font-size="3.05" font-weight="400">sem duplicatas</text>
<!-- nó EST (estado) -->
<rect x="61.0" y="24.25" width="42.0" height="15.0" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="82.0" y="29.07" text-anchor="middle" font-size="3.05" font-weight="500">ESTADO</text>
<text x="82.0" y="32.82" text-anchor="middle" font-size="3.05" font-weight="400">com versão, limites</text>
<text x="82.0" y="36.57" text-anchor="middle" font-size="3.05" font-weight="400">e saldo do orçamento</text>
<!-- nó N (decisao) -->
<polygon points="113.0,31.75 117.2,25.5 150.8,25.5 155.0,31.75 150.8,38.0 117.2,38.0" fill="#FFF3BF" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="500">NÚCLEO</text>
<text x="134.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">DO JEV</text>
<!-- nó EXE (executor) -->
<rect x="165.0" y="24.25" width="42.0" height="15.0" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="186.0" y="29.07" text-anchor="middle" font-size="3.05" font-weight="500">EXECUTORES</text>
<text x="186.0" y="32.82" text-anchor="middle" font-size="3.05" font-weight="400">agentes, modelos,</text>
<text x="186.0" y="36.57" text-anchor="middle" font-size="3.05" font-weight="400">ferramentas</text>
<!-- nó VAL (evidencia) -->
<rect x="217.0" y="25.5" width="42.0" height="12.5" rx="2.2" fill="#C3FAE8" stroke="#099268" stroke-width="0.4"/>
<text x="238.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="500">VALIDAR</text>
<text x="238.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">artefato e resultado</text>
<!-- nó MOD (executor) -->
<rect x="113.0" y="7.0" width="42.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="134.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="500">MODELO</text>
<text x="134.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">propõe entre opções</text>
<!-- nó PES (humano) -->
<rect x="165.0" y="5.75" width="42.0" height="15.0" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="186.0" y="10.57" text-anchor="middle" font-size="3.05" font-weight="500">PESSOA</text>
<text x="186.0" y="14.32" text-anchor="middle" font-size="3.05" font-weight="400">abstenção, revisão,</text>
<text x="186.0" y="18.07" text-anchor="middle" font-size="3.05" font-weight="400">aprovação</text>
<!-- nó REG (nota) -->
<rect x="113.0" y="49.55" width="42.0" height="12.5" rx="2.2" fill="#F8F9FA" stroke="#868E96" stroke-width="0.4" stroke-dasharray="3 2"/>
<text x="134.0" y="54.99" text-anchor="middle" font-size="3.05" font-weight="500" font-style="italic">REGISTRO</text>
<text x="134.0" y="58.74" text-anchor="middle" font-size="3.05" font-weight="400" font-style="italic">de decisões</text>
<!-- nó BAN (ferramenta) -->
<rect x="165.0" y="49.55" width="42.0" height="12.5" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="186.0" y="54.99" text-anchor="middle" font-size="3.05" font-weight="500">BANCADA</text>
<text x="186.0" y="58.74" text-anchor="middle" font-size="3.05" font-weight="400">fora da produção</text>
</svg>
```

### 1 Triagem (`p1`, página 6)

Tamanho: 232 × 138 mm.

- ITEM RECEBIDO (e-mail, alerta, portal) → normalizar e registrar o canal.
- Condição 1: mesma assinatura de caso aberto? sim → ANEXAR evidência ao caso aberto.
- Condição 2: alerta crítico do monitoramento? sim → INCIDENTE, tipo decidido por regra.
- não → MODELO propõe o tipo e cita o trecho → condição 3: tipo permitido e pontuação ≥ limiar? A nota “limiar calibrado em casos rotulados” liga-se a ela por seta tracejada.
- Condição 3: sim → TIPO ACEITO; não → ABSTER, triagem humana.
- INCIDENTE, TIPO ACEITO e ABSTER → PRIORIDADE (impacto × urgência) → DESTINO (responsável e prazo).

#### SVG `p1`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 232 137.5" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p1-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p1-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p1-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p1-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p1-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p1-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<!-- seta IT → NRM -->
<path d="M55.00,13.25 L65.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<!-- seta C1 → ANX -->
<path d="M111.00,31.75 L121.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<text x="116.0" y="30.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C1 → C2 -->
<path d="M88.00,38.00 L88.00,44.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<text x="89.4" y="42.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C2 → INC -->
<path d="M111.00,50.25 L121.00,50.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<text x="116.0" y="49.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta NRM → C1 -->
<path d="M88.00,19.50 L88.00,25.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<!-- seta C2 → MOD -->
<path d="M88.00,56.50 L88.00,61.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<text x="89.4" y="59.88" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta MOD → C3 -->
<path d="M88.00,76.25 L88.00,81.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<!-- seta C3 → TIPO -->
<path d="M111.00,87.25 L121.00,87.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<text x="116.0" y="86.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C3 → ABS -->
<path d="M88.00,93.50 L88.00,99.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<text x="89.4" y="97.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta CAL → C3 -->
<path d="M55.00,87.25 L65.00,87.25" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p1-m-cinza)"/>
<!-- seta INC → PRI -->
<path d="M167.00,50.25 L200.00,50.25 L200.00,99.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<!-- seta TIPO → PRI -->
<path d="M167.00,87.25 L200.00,87.25 L200.00,99.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<!-- seta ABS → PRI -->
<path d="M111.00,105.75 L177.00,105.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<!-- seta PRI → DES -->
<path d="M200.00,112.00 L200.00,118.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p1-m-base)"/>
<!-- nó IT (entrada) -->
<rect x="9.0" y="7.0" width="46.0" height="12.5" rx="2.2" fill="#FFE8CC" stroke="#E8590C" stroke-width="0.4"/>
<text x="32.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="500">ITEM RECEBIDO</text>
<text x="32.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">e-mail, alerta, portal</text>
<!-- nó NRM (acao) -->
<rect x="65.0" y="7.0" width="46.0" height="12.5" rx="2.2" fill="#FFFFFF" stroke="#495057" stroke-width="0.4"/>
<text x="88.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="400">normalizar e</text>
<text x="88.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">registrar o canal</text>
<!-- nó ANX (saida) -->
<rect x="121.0" y="25.5" width="46.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="144.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="500">ANEXAR</text>
<text x="144.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">evidência ao caso aberto</text>
<!-- nó INC (estado) -->
<rect x="121.0" y="44.0" width="46.0" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="144.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="500">INCIDENTE</text>
<text x="144.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">tipo decidido por regra</text>
<!-- nó MOD (executor) -->
<rect x="65.0" y="61.25" width="46.0" height="15.0" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="88.0" y="66.07" text-anchor="middle" font-size="3.05" font-weight="500">MODELO</text>
<text x="88.0" y="69.82" text-anchor="middle" font-size="3.05" font-weight="400">propõe o tipo</text>
<text x="88.0" y="73.57" text-anchor="middle" font-size="3.05" font-weight="400">e cita o trecho</text>
<!-- nó TIPO (estado) -->
<rect x="121.0" y="81.0" width="46.0" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="144.0" y="88.32" text-anchor="middle" font-size="3.05" font-weight="500">TIPO ACEITO</text>
<!-- nó ABS (humano) -->
<rect x="65.0" y="99.5" width="46.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="88.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="500">ABSTER</text>
<text x="88.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">triagem humana</text>
<!-- nó CAL (nota) -->
<rect x="9.0" y="81.0" width="46.0" height="12.5" rx="2.2" fill="#F8F9FA" stroke="#868E96" stroke-width="0.4" stroke-dasharray="3 2"/>
<text x="32.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="400" font-style="italic">limiar calibrado em</text>
<text x="32.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400" font-style="italic">casos rotulados</text>
<!-- nó PRI (estado) -->
<rect x="177.0" y="99.5" width="46.0" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="200.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="500">PRIORIDADE</text>
<text x="200.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">impacto × urgência</text>
<!-- nó DES (saida) -->
<rect x="177.0" y="118.0" width="46.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="200.0" y="123.44" text-anchor="middle" font-size="3.05" font-weight="500">DESTINO</text>
<text x="200.0" y="127.19" text-anchor="middle" font-size="3.05" font-weight="400">responsável e prazo</text>
<!-- nó C1 (cond) -->
<polygon points="65.0,31.75 69.2,25.5 106.8,25.5 111.0,31.75 106.8,38.0 69.2,38.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="400">mesma assinatura</text>
<text x="88.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">de caso aberto?</text>
<!-- nó C2 (cond) -->
<polygon points="65.0,50.25 69.2,44.0 106.8,44.0 111.0,50.25 106.8,56.5 69.2,56.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="400">alerta crítico do</text>
<text x="88.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">monitoramento?</text>
<!-- nó C3 (cond) -->
<polygon points="65.0,87.25 69.2,81.0 106.8,81.0 111.0,87.25 106.8,93.5 69.2,93.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="400">tipo permitido e</text>
<text x="88.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">pontuação ≥ limiar?</text>
</svg>
```

### 2 Orquestração de agentes (`p2`, página 7)

Tamanho: 232 × 156 mm.

- CHAMADO (erro 500 na finalização da compra) → ESTADO com versão.
- Condições, nesta ordem: limite de voltas ou sem progresso? → PAUSAR e encaminhar; testes passam e revisão aprovada? → CONCLUIR; hipóteses em conflito? → MODELO propõe o papel, inválido vira pesquisador; causa desconhecida? → PESQUISADOR, evidência da causa; sem correção válida? → PROGRAMADOR, diferenças no código; correção sem verificação? → TESTADOR, relatório de testes; última condição falsa → REVISOR, parecer.
- MODELO e os quatro papéis → VALIDAR ARTEFATO (sem artefato: retorno rejeitado), setas cinza.
- VALIDAR ARTEFATO → ESTADO, seta vermelha tracejada, rótulo “atualiza o estado”.

#### SVG `p2`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 232 156.0" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p2-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p2-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p2-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p2-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p2-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p2-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<!-- seta CH → EST -->
<path d="M55.00,13.25 L65.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<!-- seta G → PAU -->
<path d="M111.00,31.75 L121.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="116.0" y="30.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta G → C0 -->
<path d="M88.00,38.00 L88.00,44.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="89.4" y="42.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C0 → FIM -->
<path d="M111.00,50.25 L121.00,50.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="116.0" y="49.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C0 → C1 -->
<path d="M88.00,56.50 L88.00,62.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="89.4" y="60.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C1 → MOD -->
<path d="M111.00,68.75 L121.00,68.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="116.0" y="67.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C1 → C2 -->
<path d="M88.00,75.00 L88.00,81.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="89.4" y="79.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C2 → PE -->
<path d="M111.00,87.25 L121.00,87.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="116.0" y="86.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C2 → C3 -->
<path d="M88.00,93.50 L88.00,99.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="89.4" y="97.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C3 → PR -->
<path d="M111.00,105.75 L121.00,105.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="116.0" y="104.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C3 → C4 -->
<path d="M88.00,112.00 L88.00,118.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="89.4" y="116.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C4 → TE -->
<path d="M111.00,124.25 L121.00,124.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="116.0" y="123.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta EST → G -->
<path d="M88.00,19.50 L88.00,25.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<!-- seta C4 → RE -->
<path d="M88.00,130.50 L88.00,136.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p2-m-base)"/>
<text x="89.4" y="134.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta MOD → VAL -->
<path d="M167.00,68.75 L172.00,68.75 L172.00,105.75 L177.00,105.75" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p2-m-cinza)"/>
<!-- seta PE → VAL -->
<path d="M167.00,87.25 L172.00,87.25 L172.00,105.75 L177.00,105.75" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p2-m-cinza)"/>
<!-- seta TE → VAL -->
<path d="M167.00,124.25 L172.00,124.25 L172.00,105.75 L177.00,105.75" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p2-m-cinza)"/>
<!-- seta PR → VAL -->
<path d="M167.00,105.75 L177.00,105.75" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p2-m-cinza)"/>
<!-- seta RE → VAL -->
<path d="M111.00,142.75 L172.00,142.75 L172.00,105.75 L177.00,105.75" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p2-m-cinza)"/>
<!-- seta VAL → EST -->
<path d="M200.00,98.25 L200.00,13.25 L111.00,13.25" fill="none" stroke="#C92A2A" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p2-m-vermelho)"/>
<text x="155.5" y="12.05" text-anchor="middle" font-size="2.68" fill="#C92A2A">atualiza o estado</text>
<!-- nó CH (entrada) -->
<rect x="9.0" y="5.75" width="46.0" height="15.0" rx="2.2" fill="#FFE8CC" stroke="#E8590C" stroke-width="0.4"/>
<text x="32.0" y="10.57" text-anchor="middle" font-size="3.05" font-weight="500">CHAMADO</text>
<text x="32.0" y="14.32" text-anchor="middle" font-size="3.05" font-weight="400">erro 500 na finalização</text>
<text x="32.0" y="18.07" text-anchor="middle" font-size="3.05" font-weight="400">da compra</text>
<!-- nó EST (estado) -->
<rect x="65.0" y="7.0" width="46.0" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="88.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="500">ESTADO</text>
<text x="88.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">com versão</text>
<!-- nó PAU (humano) -->
<rect x="121.0" y="25.5" width="46.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="144.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="500">PAUSAR</text>
<text x="144.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">e encaminhar</text>
<!-- nó FIM (saida) -->
<rect x="121.0" y="44.0" width="46.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="144.0" y="51.32" text-anchor="middle" font-size="3.05" font-weight="500">CONCLUIR</text>
<!-- nó MOD (executor) -->
<rect x="121.0" y="62.5" width="46.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="144.0" y="67.94" text-anchor="middle" font-size="3.05" font-weight="400">MODELO propõe o papel</text>
<text x="144.0" y="71.69" text-anchor="middle" font-size="3.05" font-weight="400">inválido: pesquisador</text>
<!-- nó PE (executor) -->
<rect x="121.0" y="81.0" width="46.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="144.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="500">PESQUISADOR</text>
<text x="144.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">evidência da causa</text>
<!-- nó PR (executor) -->
<rect x="121.0" y="99.5" width="46.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="144.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="500">PROGRAMADOR</text>
<text x="144.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">diferenças no código</text>
<!-- nó TE (executor) -->
<rect x="121.0" y="118.0" width="46.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="144.0" y="123.44" text-anchor="middle" font-size="3.05" font-weight="500">TESTADOR</text>
<text x="144.0" y="127.19" text-anchor="middle" font-size="3.05" font-weight="400">relatório de testes</text>
<!-- nó RE (executor) -->
<rect x="65.0" y="136.5" width="46.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="88.0" y="141.94" text-anchor="middle" font-size="3.05" font-weight="500">REVISOR</text>
<text x="88.0" y="145.69" text-anchor="middle" font-size="3.05" font-weight="400">parecer</text>
<!-- nó VAL (evidencia) -->
<rect x="177.0" y="98.25" width="46.0" height="15.0" rx="2.2" fill="#C3FAE8" stroke="#099268" stroke-width="0.4"/>
<text x="200.0" y="103.07" text-anchor="middle" font-size="3.05" font-weight="500">VALIDAR ARTEFATO</text>
<text x="200.0" y="106.82" text-anchor="middle" font-size="3.05" font-weight="400">sem artefato: retorno</text>
<text x="200.0" y="110.57" text-anchor="middle" font-size="3.05" font-weight="400">rejeitado</text>
<!-- nó G (cond) -->
<polygon points="65.0,31.75 69.2,25.5 106.8,25.5 111.0,31.75 106.8,38.0 69.2,38.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="400">limite de voltas ou</text>
<text x="88.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">sem progresso?</text>
<!-- nó C0 (cond) -->
<polygon points="65.0,50.25 69.2,44.0 106.8,44.0 111.0,50.25 106.8,56.5 69.2,56.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="400">testes passam e</text>
<text x="88.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">revisão aprovada?</text>
<!-- nó C1 (cond) -->
<polygon points="65.0,68.75 69.2,62.5 106.8,62.5 111.0,68.75 106.8,75.0 69.2,75.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="67.94" text-anchor="middle" font-size="3.05" font-weight="400">hipóteses em</text>
<text x="88.0" y="71.69" text-anchor="middle" font-size="3.05" font-weight="400">conflito?</text>
<!-- nó C2 (cond) -->
<polygon points="65.0,87.25 69.2,81.0 106.8,81.0 111.0,87.25 106.8,93.5 69.2,93.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="400">causa</text>
<text x="88.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">desconhecida?</text>
<!-- nó C3 (cond) -->
<polygon points="65.0,105.75 69.2,99.5 106.8,99.5 111.0,105.75 106.8,112.0 69.2,112.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="400">sem correção</text>
<text x="88.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">válida?</text>
<!-- nó C4 (cond) -->
<polygon points="65.0,124.25 69.2,118.0 106.8,118.0 111.0,124.25 106.8,130.5 69.2,130.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="88.0" y="123.44" text-anchor="middle" font-size="3.05" font-weight="400">correção sem</text>
<text x="88.0" y="127.19" text-anchor="middle" font-size="3.05" font-weight="400">verificação?</text>
</svg>
```

### 3 Roteamento de modelos (`p3`, página 8)

Tamanho: 232 × 138 mm.

- SUBTAREFA (família, contexto, classe de dados) → excluir modelos que já falharam ou não os superam → excluir por contexto, classe de dados e qualidade mínima. A nota “catálogo medido na bancada” liga-se ao segundo filtro.
- Condição: sobrou algum modelo? não → ENCAMINHAR; sim → condição: algum cabe no saldo sem tocar a reserva? A nota “orçamento com reserva de encerramento” liga-se a ela.
- não → PAUSAR, reserva preservada; sim → ESCOLHER menor custo por sucesso → EXECUTAR o modelo escolhido → condição: resultado verificado?
- sim → ACEITAR; não → REGISTRAR FALHA e custo → volta ao primeiro filtro, seta vermelha tracejada, rótulo “escalada”.

#### SVG `p3`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 232 137.5" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p3-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p3-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p3-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p3-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p3-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p3-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<!-- seta SUB → F1 -->
<path d="M55.00,13.25 L65.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<!-- seta F1 → F2 -->
<path d="M111.00,13.25 L121.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<!-- seta CAT → F2 -->
<path d="M177.00,13.25 L167.00,13.25" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p3-m-cinza)"/>
<!-- seta F2 → C1 -->
<path d="M144.00,20.75 L144.00,25.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<!-- seta C1 → ENC -->
<path d="M167.00,31.75 L177.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<text x="172.0" y="30.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C1 → C2 -->
<path d="M144.00,38.00 L144.00,44.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<text x="145.4" y="42.0" text-anchor="start" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C2 → PAU -->
<path d="M167.00,50.25 L177.00,50.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<text x="172.0" y="49.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C2 → ESC -->
<path d="M144.00,56.50 L144.00,62.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<text x="145.4" y="60.5" text-anchor="start" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta LIV → C2 -->
<path d="M111.00,50.25 L121.00,50.25" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p3-m-cinza)"/>
<!-- seta ESC → EXE -->
<path d="M144.00,75.00 L144.00,81.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<!-- seta EXE → V -->
<path d="M144.00,93.50 L144.00,99.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<!-- seta V → OK -->
<path d="M167.00,105.75 L177.00,105.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<text x="172.0" y="104.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta V → FAL -->
<path d="M121.00,105.75 L111.00,105.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p3-m-base)"/>
<text x="116.0" y="104.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta FAL → F1 -->
<path d="M65.00,105.75 L32.00,105.75 L32.00,22.50 L88.00,22.50 L88.00,20.75" fill="none" stroke="#C92A2A" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p3-m-vermelho)"/>
<text x="30.6" y="65.12" text-anchor="end" font-size="2.68" fill="#C92A2A">escalada</text>
<!-- nó SUB (entrada) -->
<rect x="9.0" y="5.75" width="46.0" height="15.0" rx="2.2" fill="#FFE8CC" stroke="#E8590C" stroke-width="0.4"/>
<text x="32.0" y="10.57" text-anchor="middle" font-size="3.05" font-weight="500">SUBTAREFA</text>
<text x="32.0" y="14.32" text-anchor="middle" font-size="3.05" font-weight="400">família, contexto,</text>
<text x="32.0" y="18.07" text-anchor="middle" font-size="3.05" font-weight="400">classe de dados</text>
<!-- nó F1 (acao) -->
<rect x="65.0" y="5.75" width="46.0" height="15.0" rx="2.2" fill="#FFFFFF" stroke="#495057" stroke-width="0.4"/>
<text x="88.0" y="10.57" text-anchor="middle" font-size="3.05" font-weight="400">excluir modelos que</text>
<text x="88.0" y="14.32" text-anchor="middle" font-size="3.05" font-weight="400">já falharam ou não</text>
<text x="88.0" y="18.07" text-anchor="middle" font-size="3.05" font-weight="400">os superam</text>
<!-- nó F2 (acao) -->
<rect x="121.0" y="5.75" width="46.0" height="15.0" rx="2.2" fill="#FFFFFF" stroke="#495057" stroke-width="0.4"/>
<text x="144.0" y="10.57" text-anchor="middle" font-size="3.05" font-weight="400">excluir por contexto,</text>
<text x="144.0" y="14.32" text-anchor="middle" font-size="3.05" font-weight="400">classe de dados e</text>
<text x="144.0" y="18.07" text-anchor="middle" font-size="3.05" font-weight="400">qualidade mínima</text>
<!-- nó CAT (nota) -->
<rect x="177.0" y="7.0" width="46.0" height="12.5" rx="2.2" fill="#F8F9FA" stroke="#868E96" stroke-width="0.4" stroke-dasharray="3 2"/>
<text x="200.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="400" font-style="italic">catálogo medido</text>
<text x="200.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400" font-style="italic">na bancada</text>
<!-- nó ENC (humano) -->
<rect x="177.0" y="25.5" width="46.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="200.0" y="32.82" text-anchor="middle" font-size="3.05" font-weight="500">ENCAMINHAR</text>
<!-- nó PAU (humano) -->
<rect x="177.0" y="44.0" width="46.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="200.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="500">PAUSAR</text>
<text x="200.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">reserva preservada</text>
<!-- nó LIV (nota) -->
<rect x="65.0" y="44.0" width="46.0" height="12.5" rx="2.2" fill="#F8F9FA" stroke="#868E96" stroke-width="0.4" stroke-dasharray="3 2"/>
<text x="88.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="400" font-style="italic">orçamento com</text>
<text x="88.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400" font-style="italic">reserva de encerramento</text>
<!-- nó ESC (estado) -->
<rect x="121.0" y="62.5" width="46.0" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="144.0" y="67.94" text-anchor="middle" font-size="3.05" font-weight="500">ESCOLHER</text>
<text x="144.0" y="71.69" text-anchor="middle" font-size="3.05" font-weight="400">menor custo por sucesso</text>
<!-- nó EXE (executor) -->
<rect x="121.0" y="81.0" width="46.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="144.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="500">EXECUTAR</text>
<text x="144.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">o modelo escolhido</text>
<!-- nó OK (saida) -->
<rect x="177.0" y="99.5" width="46.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="200.0" y="106.82" text-anchor="middle" font-size="3.05" font-weight="500">ACEITAR</text>
<!-- nó FAL (refazer) -->
<rect x="65.0" y="99.5" width="46.0" height="12.5" rx="2.2" fill="#FFE3E3" stroke="#C92A2A" stroke-width="0.4"/>
<text x="88.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="500">REGISTRAR FALHA</text>
<text x="88.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">e custo</text>
<!-- nó C1 (cond) -->
<polygon points="121.0,31.75 125.2,25.5 162.8,25.5 167.0,31.75 162.8,38.0 125.2,38.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="144.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="400">sobrou algum</text>
<text x="144.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">modelo?</text>
<!-- nó C2 (cond) -->
<polygon points="121.0,50.25 125.2,44.0 162.8,44.0 167.0,50.25 162.8,56.5 125.2,56.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="144.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="400">algum cabe no saldo</text>
<text x="144.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">sem tocar a reserva?</text>
<!-- nó V (cond) -->
<polygon points="121.0,105.75 125.2,99.5 162.8,99.5 167.0,105.75 162.8,112.0 125.2,112.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="144.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="400">resultado</text>
<text x="144.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">verificado?</text>
</svg>
```

### 4 Ciclo de execução (`p4`, página 9)

Tamanho: 268 × 156 mm.

- PEDIDO (“dermatologista, semana que vem, à tarde”) → MODELO interpreta datas e filtros → ESTADO com versão.
- Condições, nesta ordem: cancelado ou limite atingido? → PAUSAR e encaminhar; operação externa sem resposta? → CONSULTAR pela chave; confirmada e igual ao pedido? → CONCLUIR (à esquerda); escolha válida e autorizada? → EXECUTAR com chave idempotente; há opções sem escolha? → PERGUNTAR e aguardar evento; há alternativa permitida? → BUSCAR opções; última condição falsa → ENCAMINHAR.
- CONSULTAR, EXECUTAR, PERGUNTAR e BUSCAR → OBSERVAÇÃO (resultado da ferramenta ou resposta do usuário, lida pelo modelo), setas cinza.
- OBSERVAÇÃO → ESTADO, seta vermelha tracejada, rótulo “atualiza o estado”.

#### SVG `p4`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 268 156.0" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p4-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p4-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p4-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p4-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p4-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p4-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<!-- seta PED → INT -->
<path d="M51.00,13.25 L61.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<!-- seta INT → EST -->
<path d="M103.00,13.25 L113.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<!-- seta G → PAU -->
<path d="M155.00,31.75 L165.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="160.0" y="30.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta G → C1 -->
<path d="M134.00,38.00 L134.00,44.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="135.4" y="42.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C1 → CON -->
<path d="M155.00,50.25 L165.00,50.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="160.0" y="49.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C1 → C2 -->
<path d="M134.00,56.50 L134.00,62.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="135.4" y="60.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C2 → C3 -->
<path d="M134.00,75.00 L134.00,81.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="135.4" y="79.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C3 → EXE -->
<path d="M155.00,87.25 L165.00,87.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="160.0" y="86.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C3 → C4 -->
<path d="M134.00,93.50 L134.00,99.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="135.4" y="97.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C4 → PER -->
<path d="M155.00,105.75 L165.00,105.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="160.0" y="104.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C4 → C5 -->
<path d="M134.00,112.00 L134.00,118.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="135.4" y="116.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C5 → BUS -->
<path d="M155.00,124.25 L165.00,124.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="160.0" y="123.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C2 → FIM -->
<path d="M113.00,68.75 L103.00,68.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="108.0" y="67.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta EST → G -->
<path d="M134.00,19.50 L134.00,25.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<!-- seta C5 → ENC -->
<path d="M134.00,130.50 L134.00,136.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p4-m-base)"/>
<text x="135.4" y="134.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta CON → OBS -->
<path d="M207.00,50.25 L212.00,50.25 L212.00,87.25 L217.00,87.25" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p4-m-cinza)"/>
<!-- seta EXE → OBS -->
<path d="M207.00,87.25 L217.00,87.25" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p4-m-cinza)"/>
<!-- seta PER → OBS -->
<path d="M207.00,105.75 L212.00,105.75 L212.00,87.25 L217.00,87.25" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p4-m-cinza)"/>
<!-- seta BUS → OBS -->
<path d="M207.00,124.25 L212.00,124.25 L212.00,87.25 L217.00,87.25" fill="none" stroke="#868E96" stroke-width="0.42" marker-end="url(#p4-m-cinza)"/>
<!-- seta OBS → EST -->
<path d="M238.00,78.19 L238.00,13.25 L155.00,13.25" fill="none" stroke="#C92A2A" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p4-m-vermelho)"/>
<text x="196.5" y="12.05" text-anchor="middle" font-size="2.68" fill="#C92A2A">atualiza o estado</text>
<!-- nó PED (entrada) -->
<rect x="9.0" y="4.19" width="42.0" height="18.12" rx="2.2" fill="#FFE8CC" stroke="#E8590C" stroke-width="0.4"/>
<text x="30.0" y="8.69" text-anchor="middle" font-size="3.05" font-weight="500">PEDIDO</text>
<text x="30.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="400">“dermatologista,</text>
<text x="30.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">semana que vem,</text>
<text x="30.0" y="19.94" text-anchor="middle" font-size="3.05" font-weight="400">à tarde”</text>
<!-- nó INT (executor) -->
<rect x="61.0" y="5.75" width="42.0" height="15.0" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="82.0" y="10.57" text-anchor="middle" font-size="3.05" font-weight="500">MODELO</text>
<text x="82.0" y="14.32" text-anchor="middle" font-size="3.05" font-weight="400">interpreta datas</text>
<text x="82.0" y="18.07" text-anchor="middle" font-size="3.05" font-weight="400">e filtros</text>
<!-- nó EST (estado) -->
<rect x="113.0" y="7.0" width="42.0" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="134.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="500">ESTADO</text>
<text x="134.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">com versão</text>
<!-- nó PAU (humano) -->
<rect x="165.0" y="25.5" width="42.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="186.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="500">PAUSAR</text>
<text x="186.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">e encaminhar</text>
<!-- nó CON (ferramenta) -->
<rect x="165.0" y="44.0" width="42.0" height="12.5" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="186.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="500">CONSULTAR</text>
<text x="186.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">pela chave</text>
<!-- nó FIM (saida) -->
<rect x="61.0" y="62.5" width="42.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="82.0" y="69.82" text-anchor="middle" font-size="3.05" font-weight="500">CONCLUIR</text>
<!-- nó EXE (ferramenta) -->
<rect x="165.0" y="81.0" width="42.0" height="12.5" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="186.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="500">EXECUTAR</text>
<text x="186.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">com chave idempotente</text>
<!-- nó PER (humano) -->
<rect x="165.0" y="99.5" width="42.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="186.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="500">PERGUNTAR</text>
<text x="186.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">e aguardar evento</text>
<!-- nó BUS (ferramenta) -->
<rect x="165.0" y="118.0" width="42.0" height="12.5" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="186.0" y="123.44" text-anchor="middle" font-size="3.05" font-weight="500">BUSCAR</text>
<text x="186.0" y="127.19" text-anchor="middle" font-size="3.05" font-weight="400">opções</text>
<!-- nó ENC (humano) -->
<rect x="113.0" y="136.5" width="42.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="134.0" y="143.82" text-anchor="middle" font-size="3.05" font-weight="500">ENCAMINHAR</text>
<!-- nó OBS (evidencia) -->
<rect x="217.0" y="78.19" width="42.0" height="18.12" rx="2.2" fill="#C3FAE8" stroke="#099268" stroke-width="0.4"/>
<text x="238.0" y="82.69" text-anchor="middle" font-size="3.05" font-weight="500">OBSERVAÇÃO</text>
<text x="238.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="400">resultado da ferramenta</text>
<text x="238.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">ou resposta do usuário,</text>
<text x="238.0" y="93.94" text-anchor="middle" font-size="3.05" font-weight="400">lida pelo modelo</text>
<!-- nó G (cond) -->
<polygon points="113.0,31.75 117.2,25.5 150.8,25.5 155.0,31.75 150.8,38.0 117.2,38.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="400">cancelado ou</text>
<text x="134.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">limite atingido?</text>
<!-- nó C1 (cond) -->
<polygon points="113.0,50.25 117.2,44.0 150.8,44.0 155.0,50.25 150.8,56.5 117.2,56.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="400">operação externa</text>
<text x="134.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">sem resposta?</text>
<!-- nó C2 (cond) -->
<polygon points="113.0,68.75 117.2,62.5 150.8,62.5 155.0,68.75 150.8,75.0 117.2,75.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="67.94" text-anchor="middle" font-size="3.05" font-weight="400">confirmada e igual</text>
<text x="134.0" y="71.69" text-anchor="middle" font-size="3.05" font-weight="400">ao pedido?</text>
<!-- nó C3 (cond) -->
<polygon points="113.0,87.25 117.2,81.0 150.8,81.0 155.0,87.25 150.8,93.5 117.2,93.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="400">escolha válida</text>
<text x="134.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">e autorizada?</text>
<!-- nó C4 (cond) -->
<polygon points="113.0,105.75 117.2,99.5 150.8,99.5 155.0,105.75 150.8,112.0 117.2,112.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="400">há opções</text>
<text x="134.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">sem escolha?</text>
<!-- nó C5 (cond) -->
<polygon points="113.0,124.25 117.2,118.0 150.8,118.0 155.0,124.25 150.8,130.5 117.2,130.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="123.44" text-anchor="middle" font-size="3.05" font-weight="400">há alternativa</text>
<text x="134.0" y="127.19" text-anchor="middle" font-size="3.05" font-weight="400">permitida?</text>
</svg>
```

### 5 Avaliação (`p5`, página 10)

Tamanho: 200 × 138 mm.

- EXECUTOR implementa → ENTREGA (diferenças, testes, registros) → CAMADA 1: CÓDIGO (testes, análise estática, escopo das mudanças) → CAMADA 2: RUBRICA (aplicada por modelo, calibrada com pessoas).
- Condições, nesta ordem: impossível no escopo? → ENCERRAR com motivo; obrigatórios aprovados e rubrica ≥ mínimo? → APROVADO; evidência ambígua? → REVISÃO HUMANA; falha específica, nova e com tentativas?
- Última condição: sim → REFAZER com a lista do que corrigir (à esquerda); não → REVISÃO HUMANA.
- REFAZER → EXECUTOR, seta vermelha tracejada, rótulo “nova tentativa”.

#### SVG `p5`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 137.5" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p5-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p5-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p5-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p5-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p5-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p5-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<!-- seta AG → ENT -->
<path d="M63.00,13.25 L73.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<!-- seta ENT → L1 -->
<path d="M100.00,20.75 L100.00,24.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<!-- seta L1 → L2 -->
<path d="M100.00,39.25 L100.00,42.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<!-- seta C1 → ENCE -->
<path d="M127.00,68.75 L137.00,68.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="132.0" y="67.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C1 → C2 -->
<path d="M100.00,75.00 L100.00,81.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="101.4" y="79.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C2 → OK -->
<path d="M127.00,87.25 L137.00,87.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="132.0" y="86.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C2 → C3 -->
<path d="M100.00,93.50 L100.00,99.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="101.4" y="97.5" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C3 → REV -->
<path d="M127.00,105.75 L137.00,105.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="132.0" y="104.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta L2 → C1 -->
<path d="M100.00,57.75 L100.00,62.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<!-- seta C3 → C4 -->
<path d="M100.00,112.00 L100.00,118.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="101.4" y="116.0" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C4 → RF -->
<path d="M73.00,124.25 L63.00,124.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="68.0" y="123.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C4 → REV -->
<path d="M127.00,124.25 L164.00,124.25 L164.00,112.00" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p5-m-base)"/>
<text x="145.5" y="123.05" text-anchor="middle" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta RF → AG -->
<path d="M36.00,116.75 L36.00,19.50" fill="none" stroke="#C92A2A" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p5-m-vermelho)"/>
<text x="37.4" y="69.12" text-anchor="start" font-size="2.68" fill="#C92A2A">nova tentativa</text>
<!-- nó AG (executor) -->
<rect x="9.0" y="7.0" width="54.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="36.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="500">EXECUTOR</text>
<text x="36.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">implementa</text>
<!-- nó ENT (evidencia) -->
<rect x="73.0" y="5.75" width="54.0" height="15.0" rx="2.2" fill="#C3FAE8" stroke="#099268" stroke-width="0.4"/>
<text x="100.0" y="10.57" text-anchor="middle" font-size="3.05" font-weight="500">ENTREGA</text>
<text x="100.0" y="14.32" text-anchor="middle" font-size="3.05" font-weight="400">diferenças, testes,</text>
<text x="100.0" y="18.07" text-anchor="middle" font-size="3.05" font-weight="400">registros</text>
<!-- nó L1 (acao) -->
<rect x="73.0" y="24.25" width="54.0" height="15.0" rx="2.2" fill="#FFFFFF" stroke="#495057" stroke-width="0.4"/>
<text x="100.0" y="29.07" text-anchor="middle" font-size="3.05" font-weight="500">CAMADA 1: CÓDIGO</text>
<text x="100.0" y="32.82" text-anchor="middle" font-size="3.05" font-weight="400">testes, análise estática,</text>
<text x="100.0" y="36.57" text-anchor="middle" font-size="3.05" font-weight="400">escopo das mudanças</text>
<!-- nó L2 (acao) -->
<rect x="73.0" y="42.75" width="54.0" height="15.0" rx="2.2" fill="#FFFFFF" stroke="#495057" stroke-width="0.4"/>
<text x="100.0" y="47.57" text-anchor="middle" font-size="3.05" font-weight="500">CAMADA 2: RUBRICA</text>
<text x="100.0" y="51.32" text-anchor="middle" font-size="3.05" font-weight="400">aplicada por modelo,</text>
<text x="100.0" y="55.07" text-anchor="middle" font-size="3.05" font-weight="400">calibrada com pessoas</text>
<!-- nó ENCE (refazer) -->
<rect x="137.0" y="62.5" width="54.0" height="12.5" rx="2.2" fill="#FFE3E3" stroke="#C92A2A" stroke-width="0.4"/>
<text x="164.0" y="67.94" text-anchor="middle" font-size="3.05" font-weight="500">ENCERRAR</text>
<text x="164.0" y="71.69" text-anchor="middle" font-size="3.05" font-weight="400">com motivo</text>
<!-- nó OK (saida) -->
<rect x="137.0" y="81.0" width="54.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="164.0" y="88.32" text-anchor="middle" font-size="3.05" font-weight="500">APROVADO</text>
<!-- nó REV (humano) -->
<rect x="137.0" y="99.5" width="54.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="164.0" y="106.82" text-anchor="middle" font-size="3.05" font-weight="500">REVISÃO HUMANA</text>
<!-- nó RF (refazer) -->
<rect x="9.0" y="116.75" width="54.0" height="15.0" rx="2.2" fill="#FFE3E3" stroke="#C92A2A" stroke-width="0.4"/>
<text x="36.0" y="121.57" text-anchor="middle" font-size="3.05" font-weight="500">REFAZER</text>
<text x="36.0" y="125.32" text-anchor="middle" font-size="3.05" font-weight="400">com a lista do</text>
<text x="36.0" y="129.07" text-anchor="middle" font-size="3.05" font-weight="400">que corrigir</text>
<!-- nó C1 (cond) -->
<polygon points="73.0,68.75 77.2,62.5 122.8,62.5 127.0,68.75 122.8,75.0 77.2,75.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="100.0" y="67.94" text-anchor="middle" font-size="3.05" font-weight="400">impossível</text>
<text x="100.0" y="71.69" text-anchor="middle" font-size="3.05" font-weight="400">no escopo?</text>
<!-- nó C2 (cond) -->
<polygon points="73.0,87.25 77.2,81.0 122.8,81.0 127.0,87.25 122.8,93.5 77.2,93.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="100.0" y="86.44" text-anchor="middle" font-size="3.05" font-weight="400">obrigatórios aprovados</text>
<text x="100.0" y="90.19" text-anchor="middle" font-size="3.05" font-weight="400">e rubrica ≥ mínimo?</text>
<!-- nó C3 (cond) -->
<polygon points="73.0,105.75 77.2,99.5 122.8,99.5 127.0,105.75 122.8,112.0 77.2,112.0" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="100.0" y="104.94" text-anchor="middle" font-size="3.05" font-weight="400">evidência</text>
<text x="100.0" y="108.69" text-anchor="middle" font-size="3.05" font-weight="400">ambígua?</text>
<!-- nó C4 (cond) -->
<polygon points="73.0,124.25 77.2,118.0 122.8,118.0 127.0,124.25 122.8,130.5 77.2,130.5" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="100.0" y="123.44" text-anchor="middle" font-size="3.05" font-weight="400">falha específica,</text>
<text x="100.0" y="127.19" text-anchor="middle" font-size="3.05" font-weight="400">nova e com tentativas?</text>
</svg>
```

### 6 Comparação (`p6`, página 11)

Tamanho: 268 × 138 mm.

- CASOS REAIS (conjunto de ajuste e conjunto de decisão) → BANCADA (ambiente restaurado, várias tentativas) → A (base sem o JEV) e B (mesma base com o JEV) → MEDIR por categoria (sucesso, custo, latência, intervenção) → INTERVALO DE 95% da diferença de sucesso.
- Condições, nesta ordem: todo o intervalo abaixo da margem? → REJEITAR; parte abaixo da margem? → AMPLIAR A AMOSTRA; mais barato por sucesso ou menos intervenção? → ADOTAR na categoria; última condição falsa → AJUSTAR B.
- AJUSTAR B → BANCADA, seta anil tracejada, rótulo “medir de novo”.
- AMPLIAR A AMOSTRA → CASOS REAIS, seta anil tracejada contornando o diagrama, rótulo “mais casos”.

#### SVG `p6`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 268 137.5" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p6-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p6-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p6-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p6-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p6-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p6-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<!-- seta CAS → BAN -->
<path d="M51.00,22.50 L61.00,22.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<!-- seta BAN → A -->
<path d="M103.00,22.50 L108.00,22.50 L108.00,13.25 L113.00,13.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<!-- seta BAN → B -->
<path d="M103.00,22.50 L108.00,22.50 L108.00,31.75 L113.00,31.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<!-- seta A → MED -->
<path d="M155.00,13.25 L160.00,13.25 L160.00,22.50 L165.00,22.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<!-- seta B → MED -->
<path d="M155.00,31.75 L160.00,31.75 L160.00,22.50 L165.00,22.50" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<!-- seta MED → IC -->
<path d="M186.00,32.19 L186.00,39.38" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<!-- seta C1 → REJ -->
<path d="M207.00,64.12 L217.00,64.12" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<text x="212.0" y="62.92" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C1 → C2 -->
<path d="M186.00,70.38 L186.00,76.38" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<text x="187.4" y="74.38" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C2 → AMP -->
<path d="M207.00,82.62 L217.00,82.62" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<text x="212.0" y="81.42" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta C2 → C3 -->
<path d="M186.00,88.88 L186.00,94.88" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<text x="187.4" y="92.88" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta C3 → ADO -->
<path d="M207.00,101.12 L217.00,101.12" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<text x="212.0" y="99.92" text-anchor="middle" font-size="2.68" fill="#4A4F66">sim</text>
<!-- seta IC → C1 -->
<path d="M186.00,51.88 L186.00,57.88" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<!-- seta C3 → AJU -->
<path d="M186.00,107.38 L186.00,113.38" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p6-m-base)"/>
<text x="187.4" y="111.38" text-anchor="start" font-size="2.68" fill="#4A4F66">não</text>
<!-- seta AJU → BAN -->
<path d="M165.00,119.62 L82.00,119.62 L82.00,30.00" fill="none" stroke="#4B4FC8" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p6-m-anil)"/>
<text x="123.5" y="118.42" text-anchor="middle" font-size="2.68" fill="#4B4FC8">medir de novo</text>
<!-- seta AMP → CAS -->
<path d="M259.00,82.62 L262.44,82.62 L262.44,132.57 L30.00,132.57 L30.00,30.00" fill="none" stroke="#4B4FC8" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p6-m-anil)"/>
<text x="146.22" y="135.97" text-anchor="middle" font-size="2.68" fill="#4B4FC8">mais casos</text>
<!-- nó CAS (entrada) -->
<rect x="9.0" y="15.0" width="42.0" height="15.0" rx="2.2" fill="#FFE8CC" stroke="#E8590C" stroke-width="0.4"/>
<text x="30.0" y="19.82" text-anchor="middle" font-size="3.05" font-weight="500">CASOS REAIS</text>
<text x="30.0" y="23.57" text-anchor="middle" font-size="3.05" font-weight="400">conjunto de ajuste e</text>
<text x="30.0" y="27.32" text-anchor="middle" font-size="3.05" font-weight="400">conjunto de decisão</text>
<!-- nó BAN (ferramenta) -->
<rect x="61.0" y="15.0" width="42.0" height="15.0" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="82.0" y="19.82" text-anchor="middle" font-size="3.05" font-weight="500">BANCADA</text>
<text x="82.0" y="23.57" text-anchor="middle" font-size="3.05" font-weight="400">ambiente restaurado,</text>
<text x="82.0" y="27.32" text-anchor="middle" font-size="3.05" font-weight="400">várias tentativas</text>
<!-- nó A (executor) -->
<rect x="113.0" y="7.0" width="42.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="134.0" y="12.44" text-anchor="middle" font-size="3.05" font-weight="400">A</text>
<text x="134.0" y="16.19" text-anchor="middle" font-size="3.05" font-weight="400">base sem o JEV</text>
<!-- nó B (executor) -->
<rect x="113.0" y="25.5" width="42.0" height="12.5" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="134.0" y="30.94" text-anchor="middle" font-size="3.05" font-weight="400">B</text>
<text x="134.0" y="34.69" text-anchor="middle" font-size="3.05" font-weight="400">mesma base com o JEV</text>
<!-- nó MED (evidencia) -->
<rect x="165.0" y="12.81" width="42.0" height="19.38" rx="2.2" fill="#C3FAE8" stroke="#099268" stroke-width="0.4"/>
<text x="186.0" y="17.94" text-anchor="middle" font-size="3.05" font-weight="500">MEDIR</text>
<text x="186.0" y="21.69" text-anchor="middle" font-size="3.05" font-weight="400">por categoria</text>
<text x="186.0" y="25.44" text-anchor="middle" font-size="3.05" font-weight="400">sucesso, custo,</text>
<text x="186.0" y="29.19" text-anchor="middle" font-size="3.05" font-weight="400">latência, intervenção</text>
<!-- nó IC (acao) -->
<rect x="165.0" y="39.38" width="42.0" height="12.5" rx="2.2" fill="#FFFFFF" stroke="#495057" stroke-width="0.4"/>
<text x="186.0" y="44.82" text-anchor="middle" font-size="3.05" font-weight="500">INTERVALO DE 95%</text>
<text x="186.0" y="48.57" text-anchor="middle" font-size="3.05" font-weight="400">da diferença de sucesso</text>
<!-- nó REJ (refazer) -->
<rect x="217.0" y="57.88" width="42.0" height="12.5" rx="2.2" fill="#FFE3E3" stroke="#C92A2A" stroke-width="0.4"/>
<text x="238.0" y="65.19" text-anchor="middle" font-size="3.05" font-weight="500">REJEITAR</text>
<!-- nó AMP (ferramenta) -->
<rect x="217.0" y="76.38" width="42.0" height="12.5" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="238.0" y="81.82" text-anchor="middle" font-size="3.05" font-weight="500">AMPLIAR</text>
<text x="238.0" y="85.57" text-anchor="middle" font-size="3.05" font-weight="400">A AMOSTRA</text>
<!-- nó ADO (saida) -->
<rect x="217.0" y="94.88" width="42.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="238.0" y="100.32" text-anchor="middle" font-size="3.05" font-weight="500">ADOTAR</text>
<text x="238.0" y="104.07" text-anchor="middle" font-size="3.05" font-weight="400">na categoria</text>
<!-- nó AJU (estado) -->
<rect x="165.0" y="113.38" width="42.0" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="186.0" y="120.69" text-anchor="middle" font-size="3.05" font-weight="500">AJUSTAR B</text>
<!-- nó C1 (cond) -->
<polygon points="165.0,64.12 169.2,57.88 202.8,57.88 207.0,64.12 202.8,70.38 169.2,70.38" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="186.0" y="63.32" text-anchor="middle" font-size="3.05" font-weight="400">todo o intervalo</text>
<text x="186.0" y="67.07" text-anchor="middle" font-size="3.05" font-weight="400">abaixo da margem?</text>
<!-- nó C2 (cond) -->
<polygon points="165.0,82.62 169.2,76.38 202.8,76.38 207.0,82.62 202.8,88.88 169.2,88.88" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="186.0" y="81.82" text-anchor="middle" font-size="3.05" font-weight="400">parte abaixo</text>
<text x="186.0" y="85.57" text-anchor="middle" font-size="3.05" font-weight="400">da margem?</text>
<!-- nó C3 (cond) -->
<polygon points="160.8,101.12 165.0,94.88 207.0,94.88 211.2,101.12 207.0,107.38 165.0,107.38" fill="#FFF9DB" stroke="#E67700" stroke-width="0.45"/>
<text x="186.0" y="100.32" text-anchor="middle" font-size="3.05" font-weight="400">mais barato por sucesso</text>
<text x="186.0" y="104.07" text-anchor="middle" font-size="3.05" font-weight="400">ou menos intervenção?</text>
</svg>
```

### Integração (`p7`, página 12)

Tamanho: 268 × 147 mm.

- Quadro tracejado “Produção” contém: 1 TRIAGEM, 2 ORQUESTRAÇÃO, CONCLUÍDO, AGENTES, 3 ROTEAMENTO DE MODELOS, MODELOS, 4 CICLO DE EXECUÇÃO, FERRAMENTAS, 5 AVALIAÇÃO e PESSOA.
- EVENTOS (fora do quadro) → 1 TRIAGEM → 2 ORQUESTRAÇÃO → AGENTES.
- 1 TRIAGEM → PESSOA, seta rosa, rótulo “abster”. 2 ORQUESTRAÇÃO → CONCLUÍDO com prova, seta verde, rótulo “concluir”.
- AGENTES → 3 ROTEAMENTO (“subtarefa”) e volta tracejada (“resposta”); 3 ROTEAMENTO → MODELOS e volta tracejada.
- AGENTES → 4 CICLO DE EXECUÇÃO (“ação externa”); 4 CICLO → FERRAMENTAS e volta tracejada (“observação”).
- AGENTES → 5 AVALIAÇÃO; 5 AVALIAÇÃO → AGENTES, seta vermelha tracejada (refazer).
- 5 AVALIAÇÃO → 2 ORQUESTRAÇÃO, seta verde por baixo, rótulo “aprovado: novo estado”. 5 AVALIAÇÃO → PESSOA, seta rosa por baixo, rótulo “revisão”.
- Fora do quadro: ESTADO, ORÇAMENTO E REGISTRO DE DECISÕES liga-se ao quadro por seta cinza tracejada e → 6 COMPARAÇÃO (“registro”); 6 COMPARAÇÃO → quadro, seta anil tracejada, rótulo “adotar, ajustar, ampliar autonomia”.

#### SVG `p7`

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 268 146.75" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130">
<defs>
<marker id="p7-m-base" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4A4F66"/>
</marker>
<marker id="p7-m-vermelho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C92A2A"/>
</marker>
<marker id="p7-m-verde" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#2B8A3E"/>
</marker>
<marker id="p7-m-rosa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#C2255C"/>
</marker>
<marker id="p7-m-anil" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#4B4FC8"/>
</marker>
<marker id="p7-m-cinza" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="#868E96"/>
</marker>
</defs>
<rect x="58.0" y="5.0" width="204.0" height="122.88" rx="3" fill="#FAFAFF" stroke="#4B4FC8" stroke-width="0.35" stroke-dasharray="3 2"/>
<text x="61.0" y="9.2" font-size="3.05" fill="#4B4FC8">Produção</text>
<!-- seta EV → T -->
<path d="M51.00,50.25 L61.00,50.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<!-- seta T → O -->
<path d="M103.00,50.25 L113.00,50.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<!-- seta T → PES -->
<path d="M82.00,56.50 L82.00,84.70" fill="none" stroke="#C2255C" stroke-width="0.42" marker-end="url(#p7-m-rosa)"/>
<text x="83.4" y="71.6" text-anchor="start" font-size="2.68" fill="#C2255C">abster</text>
<!-- seta O → AGS -->
<path d="M155.00,50.25 L161.85,50.25" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<!-- seta O → FIM -->
<path d="M134.00,44.00 L134.00,33.38" fill="none" stroke="#2B8A3E" stroke-width="0.42" marker-end="url(#p7-m-verde)"/>
<text x="135.4" y="39.69" text-anchor="start" font-size="2.68" fill="#2B8A3E">concluir</text>
<!-- seta AGS → R -->
<path d="M176.34,42.75 L176.34,33.38" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<text x="174.94" y="39.06" text-anchor="end" font-size="2.68" fill="#4A4F66">subtarefa</text>
<!-- seta R → AGS -->
<path d="M194.40,33.38 L194.40,42.75" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p7-m-cinza)"/>
<text x="195.8" y="39.06" text-anchor="start" font-size="2.68" fill="#868E96">resposta</text>
<!-- seta R → MOD -->
<path d="M207.00,24.62 L217.00,24.62" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<!-- seta MOD → R -->
<path d="M217.00,30.12 L207.00,30.12" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p7-m-cinza)"/>
<!-- seta AGS → C -->
<path d="M176.34,57.75 L176.34,67.12" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<text x="174.94" y="63.44" text-anchor="end" font-size="2.68" fill="#4A4F66">ação externa</text>
<!-- seta C → FER -->
<path d="M177.60,79.62 L177.60,87.47" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<!-- seta FER → C -->
<path d="M194.40,87.47 L194.40,79.62" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p7-m-cinza)"/>
<text x="195.8" y="84.55" text-anchor="start" font-size="2.68" fill="#868E96">observação</text>
<!-- seta AGS → A -->
<path d="M210.15,46.95 L217.00,46.95" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<!-- seta A → AGS -->
<path d="M217.00,53.00 L210.15,53.00" fill="none" stroke="#C92A2A" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p7-m-vermelho)"/>
<!-- seta A → O -->
<path d="M225.40,56.50 L225.40,105.75 L134.00,105.75 L134.00,56.50" fill="none" stroke="#2B8A3E" stroke-width="0.42" marker-end="url(#p7-m-verde)"/>
<text x="179.7" y="104.55" text-anchor="middle" font-size="2.68" fill="#2B8A3E">aprovado: novo estado</text>
<!-- seta A → PES -->
<path d="M250.60,56.50 L250.60,115.00 L82.00,115.00 L82.00,97.20" fill="none" stroke="#C2255C" stroke-width="0.42" marker-end="url(#p7-m-rosa)"/>
<text x="166.3" y="113.8" text-anchor="middle" font-size="2.68" fill="#C2255C">revisão</text>
<!-- seta EST → QE -->
<path d="M82.00,136.50 L82.00,127.95" fill="none" stroke="#868E96" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p7-m-cinza)"/>
<!-- seta EST → CMP -->
<path d="M108.25,142.75 L159.75,142.75" fill="none" stroke="#4A4F66" stroke-width="0.42" marker-end="url(#p7-m-base)"/>
<text x="134.0" y="141.55" text-anchor="middle" font-size="2.68" fill="#4A4F66">registro</text>
<!-- seta CMP → QC -->
<path d="M186.00,136.50 L186.00,127.95" fill="none" stroke="#4B4FC8" stroke-width="0.42" stroke-dasharray="2.2 1.6" marker-end="url(#p7-m-anil)"/>
<text x="187.4" y="133.23" text-anchor="start" font-size="2.68" fill="#4B4FC8">adotar, ajustar, ampliar autonomia</text>
<!-- nó EV (entrada) -->
<rect x="9.0" y="44.0" width="42.0" height="12.5" rx="2.2" fill="#FFE8CC" stroke="#E8590C" stroke-width="0.4"/>
<text x="30.0" y="49.44" text-anchor="middle" font-size="3.05" font-weight="500">EVENTOS</text>
<text x="30.0" y="53.19" text-anchor="middle" font-size="3.05" font-weight="400">alerta, e-mail, pedido</text>
<!-- nó T (decisao) -->
<polygon points="61.0,50.25 65.2,44.0 98.8,44.0 103.0,50.25 98.8,56.5 65.2,56.5" fill="#FFF3BF" stroke="#E67700" stroke-width="0.45"/>
<text x="82.0" y="51.32" text-anchor="middle" font-size="3.05" font-weight="500">1 TRIAGEM</text>
<!-- nó O (decisao) -->
<polygon points="113.0,50.25 117.2,44.0 150.8,44.0 155.0,50.25 150.8,56.5 117.2,56.5" fill="#FFF3BF" stroke="#E67700" stroke-width="0.45"/>
<text x="134.0" y="51.32" text-anchor="middle" font-size="3.05" font-weight="500">2 ORQUESTRAÇÃO</text>
<!-- nó FIM (saida) -->
<rect x="113.0" y="20.88" width="42.0" height="12.5" rx="2.2" fill="#D3F9D8" stroke="#2B8A3E" stroke-width="0.4"/>
<text x="134.0" y="26.32" text-anchor="middle" font-size="3.05" font-weight="500">CONCLUÍDO</text>
<text x="134.0" y="30.07" text-anchor="middle" font-size="3.05" font-weight="400">com prova</text>
<!-- nó AGS (executor) -->
<rect x="161.85" y="42.75" width="48.3" height="15.0" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="186.0" y="47.57" text-anchor="middle" font-size="3.05" font-weight="500">AGENTES</text>
<text x="186.0" y="51.32" text-anchor="middle" font-size="3.05" font-weight="400">pesquisador, programador,</text>
<text x="186.0" y="55.07" text-anchor="middle" font-size="3.05" font-weight="400">testador, revisor</text>
<!-- nó R (decisao) -->
<polygon points="165.0,27.12 169.2,20.88 202.8,20.88 207.0,27.12 202.8,33.38 169.2,33.38" fill="#FFF3BF" stroke="#E67700" stroke-width="0.45"/>
<text x="186.0" y="26.32" text-anchor="middle" font-size="3.05" font-weight="500">3 ROTEAMENTO</text>
<text x="186.0" y="30.07" text-anchor="middle" font-size="3.05" font-weight="400">DE MODELOS</text>
<!-- nó MOD (executor) -->
<rect x="217.0" y="19.62" width="42.0" height="15.0" rx="2.2" fill="#D0EBFF" stroke="#1971C2" stroke-width="0.4"/>
<text x="238.0" y="24.44" text-anchor="middle" font-size="3.05" font-weight="500">MODELOS</text>
<text x="238.0" y="28.19" text-anchor="middle" font-size="3.05" font-weight="400">pequeno, especialista,</text>
<text x="238.0" y="31.94" text-anchor="middle" font-size="3.05" font-weight="400">de fronteira</text>
<!-- nó C (decisao) -->
<polygon points="165.0,73.38 169.2,67.12 202.8,67.12 207.0,73.38 202.8,79.62 169.2,79.62" fill="#FFF3BF" stroke="#E67700" stroke-width="0.45"/>
<text x="186.0" y="72.57" text-anchor="middle" font-size="3.05" font-weight="500">4 CICLO DE</text>
<text x="186.0" y="76.32" text-anchor="middle" font-size="3.05" font-weight="400">EXECUÇÃO</text>
<!-- nó FER (ferramenta) -->
<rect x="165.0" y="87.47" width="42.0" height="12.5" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="186.0" y="92.92" text-anchor="middle" font-size="3.05" font-weight="500">FERRAMENTAS</text>
<text x="186.0" y="96.67" text-anchor="middle" font-size="3.05" font-weight="400">com chave idempotente</text>
<!-- nó A (decisao) -->
<polygon points="217.0,50.25 221.2,44.0 254.8,44.0 259.0,50.25 254.8,56.5 221.2,56.5" fill="#FFF3BF" stroke="#E67700" stroke-width="0.45"/>
<text x="238.0" y="51.32" text-anchor="middle" font-size="3.05" font-weight="500">5 AVALIAÇÃO</text>
<!-- nó PES (humano) -->
<rect x="61.0" y="84.7" width="42.0" height="12.5" rx="2.2" fill="#FFDEEB" stroke="#C2255C" stroke-width="0.4"/>
<text x="82.0" y="90.14" text-anchor="middle" font-size="3.05" font-weight="500">PESSOA</text>
<text x="82.0" y="93.89" text-anchor="middle" font-size="3.05" font-weight="400">abstenção, revisão</text>
<!-- nó EST (estado) -->
<rect x="55.75" y="136.5" width="52.5" height="12.5" rx="2.2" fill="#DBE4FF" stroke="#3B5BDB" stroke-width="0.4"/>
<text x="82.0" y="141.94" text-anchor="middle" font-size="3.05" font-weight="500">ESTADO, ORÇAMENTO</text>
<text x="82.0" y="145.69" text-anchor="middle" font-size="3.05" font-weight="400">E REGISTRO DE DECISÕES</text>
<!-- nó CMP (ferramenta) -->
<rect x="159.75" y="136.5" width="52.5" height="12.5" rx="2.2" fill="#E5DBFF" stroke="#7048E8" stroke-width="0.4"/>
<text x="186.0" y="141.94" text-anchor="middle" font-size="3.05" font-weight="500">6 COMPARAÇÃO</text>
<text x="186.0" y="145.69" text-anchor="middle" font-size="3.05" font-weight="400">bancada fora da produção</text>
</svg>
```

## Apêndices: arquivos do montador

Salve cada bloco com o nome indicado, na mesma pasta, e rode `python3 montar.py`.

### Apêndice A

Motor de desenho: grade, caixas, setas ortogonais, SVG final e SVG comentado.

#### Arquivo `grade.py`

```python
"""Diagramas em SVG com grade fixa: controle total de posição, sem cruzamentos acidentais,
tamanho de letra constante entre diagramas."""
from html import escape

ESTILO = {
    "entrada":   ("#FFE8CC", "#E8590C", ""),
    "cond":      ("#FFF9DB", "#E67700", ""),
    "decisao":   ("#FFF3BF", "#E67700", ""),
    "executor":  ("#D0EBFF", "#1971C2", ""),
    "ferramenta": ("#E5DBFF", "#7048E8", ""),
    "evidencia": ("#C3FAE8", "#099268", ""),
    "estado":    ("#DBE4FF", "#3B5BDB", ""),
    "humano":    ("#FFDEEB", "#C2255C", ""),
    "saida":     ("#D3F9D8", "#2B8A3E", ""),
    "refazer":   ("#FFE3E3", "#C92A2A", ""),
    "nota":      ("#F8F9FA", "#868E96", "3 2"),
    "acao":      ("#FFFFFF", "#495057", ""),
}
COR_LINHA = {"base": "#4A4F66", "vermelho": "#C92A2A", "verde": "#2B8A3E", "rosa": "#C2255C", "anil": "#4B4FC8", "cinza": "#868E96"}
FONTE = 3.05          # mm, cerca de 8,6 pt
LINHA = 3.75


class Diagrama:
    def __init__(self, cols, rows, cw=56, rh=18.5, w=None, h=12.5, margem=4):
        self.cw, self.rh, self.w, self.h, self.m = cw, rh, w or cw - 10, h, margem
        self.W, self.H = cols * cw + 2 * margem, rows * rh + 2 * margem
        self.nos, self.partes, self.quadros = {}, [], []

    # coordenadas em milímetros a partir da grade
    def X(self, c): return self.m + c * self.cw + self.cw / 2
    def Y(self, r): return self.m + r * self.rh + self.rh / 2

    def no(self, ident, c, r, texto, tipo="acao", wmul=1.0, hmul=1.0):
        self.nos[ident] = dict(x=self.X(c), y=self.Y(r), w=self.w * wmul, h=self.h * hmul, t=texto, k=tipo)

    def ancora(self, ident, c, r):
        self.nos[ident] = dict(x=self.X(c), y=self.Y(r), w=0.01, h=0.01, t="", k="ancora")

    def quadro(self, c0, r0, c1, r1, titulo):
        self.quadros.append((self.X(c0) - self.cw / 2 + 2, self.Y(r0) - self.rh / 2 + 1, self.X(c1) + self.cw / 2 - 2, self.Y(r1) + self.rh / 2 - 1, titulo))

    def porta(self, ident, lado, desloc=0.0):
        n = self.nos[ident]
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        return {"r": (x + w / 2, y + desloc * h), "l": (x - w / 2, y + desloc * h),
                "t": (x + desloc * w, y - h / 2), "b": (x + desloc * w, y + h / 2)}[lado]

    def seta(self, a, b, de="r", para="l", via=(), cor="base", tracejada=False, rotulo=None, pos_rotulo=0,
             da=0.0, db=0.0, lado_rotulo="acima"):
        p0, p1 = self.porta(a, de, da), self.porta(b, para, db)
        nb = self.nos[b]
        if not via and de in ("l", "r") and para in ("l", "r") and abs(p0[1] - nb["y"]) < nb["h"] / 2:
            p1 = (p1[0], p0[1])            # reta horizontal quando cabe na altura do destino
        if not via and de in ("t", "b") and para in ("t", "b") and abs(p0[0] - nb["x"]) < nb["w"] / 2:
            p1 = (p0[0], p1[1])            # reta vertical quando cabe na largura do destino
        pts = [p0]
        for vx, vy in via:     # via em grade; None repete a coordenada anterior
            px = self.X(vx) if vx is not None else pts[-1][0]
            py = self.Y(vy) if vy is not None else pts[-1][1]
            pts.append((px, py))
        # alinhar o último trecho com a porta de destino
        if via:
            lx, ly = pts[-1]
            if para in ("l", "r"):
                pts[-1] = (lx, p1[1])
            else:
                pts[-1] = (p1[0], ly)
        pts.append(p1)
        self.partes.append((f"{a} → {b}", pts, cor, tracejada, rotulo, pos_rotulo, lado_rotulo))

    def _no_svg(self, n):
        if n["k"] == "ancora":
            return ""
        f, s, dash = ESTILO[n["k"]]
        x, y, w, h = n["x"], n["y"], n["w"], n["h"]
        d = f' stroke-dasharray="{dash}"' if dash else ""
        if n["k"] in ("cond", "decisao"):
            k = min(4.2, w * 0.12)
            pts = f'{x-w/2},{y} {x-w/2+k},{y-h/2} {x+w/2-k},{y-h/2} {x+w/2},{y} {x+w/2-k},{y+h/2} {x-w/2+k},{y+h/2}'
            forma = f'<polygon points="{pts}" fill="{f}" stroke="{s}" stroke-width="0.45"{d}/>'
        else:
            forma = f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="2.2" fill="{f}" stroke="{s}" stroke-width="0.4"{d}/>'
        linhas = n["t"].split("\n")
        y0 = y - (len(linhas) - 1) * LINHA / 2 + FONTE * 0.35
        txt = []
        for i, ln in enumerate(linhas):
            peso = "500" if (i == 0 and ln.isupper() and len(ln) > 2) else "400"
            estilo = ' font-style="italic"' if n["k"] == "nota" else ""
            txt.append(f'<text x="{x}" y="{y0 + i*LINHA}" text-anchor="middle" font-size="{FONTE}" font-weight="{peso}"{estilo}>{escape(ln)}</text>')
        return forma + "".join(txt)

    def svg_legivel(self, ident):
        """Um elemento por linha, coordenadas com duas casas e comentários com o id de cada nó e seta."""
        import re as _re
        bruto = self.svg(ident, comentarios=True)
        bruto = _re.sub(r"(\d+\.\d{3,})", lambda m: f"{float(m.group(1)):.2f}", bruto)
        bruto = bruto.replace("><", ">\n<")
        return bruto

    def svg(self, ident, comentarios=False):
        defs = "".join(
            f'<marker id="{ident}-m-{nome}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{cor}"/></marker>' for nome, cor in COR_LINHA.items())
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.W} {self.H}" preserveAspectRatio="xMidYMid meet" '
               f'style="width:100%;height:100%;font-family:Poppins,DejaVu Sans,sans-serif;fill:#1E2130"><defs>{defs}</defs>']
        for x0, y0, x1, y1, tit in self.quadros:
            out.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" rx="3" fill="#FAFAFF" stroke="#4B4FC8" stroke-width="0.35" stroke-dasharray="3 2"/>'
                       f'<text x="{x0+3}" y="{y0+4.2}" font-size="{FONTE}" fill="#4B4FC8">{escape(tit)}</text>')
        for tipo, pts, cor, trac, rot, pos, lado in self.partes:
            c = COR_LINHA[cor]
            if comentarios:
                out.append(f"<!-- seta {tipo} -->")
            d = "M" + " L".join(f"{px:.2f},{py:.2f}" for px, py in pts)
            dash = ' stroke-dasharray="2.2 1.6"' if trac else ""
            out.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="0.42"{dash} marker-end="url(#{ident}-m-{cor})"/>')
            if rot:
                # rótulo no meio do trecho mais longo
                segs = list(zip(pts, pts[1:]))
                if pos == "longo":
                    (ax, ay), (bx, by) = max(segs, key=lambda s: abs(s[1][0]-s[0][0]) + abs(s[1][1]-s[0][1]))
                else:
                    (ax, ay), (bx, by) = segs[min(int(pos), len(segs) - 1)]
                mx, my = (ax + bx) / 2, (ay + by) / 2
                if abs(ay - by) < 0.01:   # horizontal
                    ty = my - 1.2 if lado == "acima" else my + 3.4
                    out.append(f'<text x="{mx}" y="{ty}" text-anchor="middle" font-size="{FONTE*0.88}" fill="{c}">{escape(rot)}</text>')
                else:
                    anc = "start" if lado != "esquerda" else "end"
                    tx = mx + 1.4 if anc == "start" else mx - 1.4
                    out.append(f'<text x="{tx}" y="{my+1}" text-anchor="{anc}" font-size="{FONTE*0.88}" fill="{c}">{escape(rot)}</text>')
        for nid, n in self.nos.items():
            if comentarios and n["k"] != "ancora":
                out.append(f"<!-- nó {nid} ({n['k']}) -->")
            out.append(self._no_svg(n))
        out.append("</svg>")
        return "".join(out)
```

### Apêndice B

Especificação dos oito diagramas. Cada função posiciona caixas na grade e liga as setas.

#### Arquivo `diagramas.py`

```python
"""Especificação dos oito diagramas do documento “Arquitetura do JEV”, na grade do módulo grade.py.
Cada função devolve um Diagrama; D.svg(id) produz o SVG final e D.svg_legivel(id) a versão comentada."""
from grade import Diagrama

def escada(D, conds, col, r0, acao_col, sim_lado="r"):
    """Condições empilhadas numa coluna: 'não' desce, 'sim' vai para o lado."""
    for i, (cid, txt, alvo) in enumerate(conds):
        D.no(cid, col, r0 + i, txt, "cond")
        if i:
            D.seta(conds[i-1][0], cid, "b", "t", rotulo="não", lado_rotulo="direita")
        if alvo:
            D.seta(cid, alvo, sim_lado, "l" if sim_lado == "r" else "r", rotulo="sim")

def p1():
    D = Diagrama(4, 7)
    D.no("IT", 0, 0, "ITEM RECEBIDO\ne-mail, alerta, portal", "entrada")
    D.no("NRM", 1, 0, "normalizar e\nregistrar o canal", "acao")
    D.no("ANX", 2, 1, "ANEXAR\nevidência ao caso aberto", "saida")
    D.no("INC", 2, 2, "INCIDENTE\ntipo decidido por regra", "estado")
    D.no("MOD", 1, 3, "MODELO\npropõe o tipo\ne cita o trecho", "executor", hmul=1.2)
    D.no("TIPO", 2, 4, "TIPO ACEITO", "estado")
    D.no("ABS", 1, 5, "ABSTER\ntriagem humana", "humano")
    D.no("CAL", 0, 4, "limiar calibrado em\ncasos rotulados", "nota")
    D.no("PRI", 3, 5, "PRIORIDADE\nimpacto × urgência", "estado")
    D.no("DES", 3, 6, "DESTINO\nresponsável e prazo", "saida")
    D.seta("IT", "NRM")
    escada(D, [("C1", "mesma assinatura\nde caso aberto?", "ANX"), ("C2", "alerta crítico do\nmonitoramento?", "INC")], 1, 1, 2)
    D.seta("NRM", "C1", "b", "t")
    D.seta("C2", "MOD", "b", "t", rotulo="não", lado_rotulo="direita")
    D.no("C3", 1, 4, "tipo permitido e\npontuação ≥ limiar?", "cond")
    D.seta("MOD", "C3", "b", "t")
    D.seta("C3", "TIPO", rotulo="sim")
    D.seta("C3", "ABS", "b", "t", rotulo="não", lado_rotulo="direita")
    D.seta("CAL", "C3", cor="cinza", tracejada=True)
    D.seta("INC", "PRI", "r", "t", via=[(3, None)], da=0)
    D.seta("TIPO", "PRI", "r", "t", via=[(3, None)])
    D.seta("ABS", "PRI")
    D.seta("PRI", "DES", "b", "t")
    return D

def p2():
    D = Diagrama(4, 8)
    D.no("CH", 0, 0, "CHAMADO\nerro 500 na finalização\nda compra", "entrada", hmul=1.2)
    D.no("EST", 1, 0, "ESTADO\ncom versão", "estado")
    D.no("PAU", 2, 1, "PAUSAR\ne encaminhar", "humano")
    D.no("FIM", 2, 2, "CONCLUIR", "saida")
    D.no("MOD", 2, 3, "MODELO propõe o papel\ninválido: pesquisador", "executor")
    D.no("PE", 2, 4, "PESQUISADOR\nevidência da causa", "executor")
    D.no("PR", 2, 5, "PROGRAMADOR\ndiferenças no código", "executor")
    D.no("TE", 2, 6, "TESTADOR\nrelatório de testes", "executor")
    D.no("RE", 1, 7, "REVISOR\nparecer", "executor")
    D.no("VAL", 3, 5, "VALIDAR ARTEFATO\nsem artefato: retorno\nrejeitado", "evidencia", hmul=1.2)
    D.seta("CH", "EST")
    escada(D, [("G", "limite de voltas ou\nsem progresso?", "PAU"), ("C0", "testes passam e\nrevisão aprovada?", "FIM"),
               ("C1", "hipóteses em\nconflito?", "MOD"), ("C2", "causa\ndesconhecida?", "PE"),
               ("C3", "sem correção\nválida?", "PR"), ("C4", "correção sem\nverificação?", "TE")], 1, 1, 2)
    D.seta("EST", "G", "b", "t")
    D.seta("C4", "RE", "b", "t", rotulo="não", lado_rotulo="direita")
    for x in ("MOD", "PE", "TE"):
        D.seta(x, "VAL", "r", "l", via=[(2.5, None), (None, 5)], cor="cinza")
    D.seta("PR", "VAL", cor="cinza")
    D.seta("RE", "VAL", "r", "l", via=[(2.5, None), (None, 5)], cor="cinza")
    D.seta("VAL", "EST", "t", "r", via=[(None, 0)], cor="vermelho", tracejada=True, rotulo="atualiza o estado", pos_rotulo="longo")
    return D

def p3():
    D = Diagrama(4, 7)
    D.no("SUB", 0, 0, "SUBTAREFA\nfamília, contexto,\nclasse de dados", "entrada", hmul=1.2)
    D.no("F1", 1, 0, "excluir modelos que\njá falharam ou não\nos superam", "acao", hmul=1.2)
    D.no("F2", 2, 0, "excluir por contexto,\nclasse de dados e\nqualidade mínima", "acao", hmul=1.2)
    D.no("CAT", 3, 0, "catálogo medido\nna bancada", "nota")
    D.no("ENC", 3, 1, "ENCAMINHAR", "humano")
    D.no("PAU", 3, 2, "PAUSAR\nreserva preservada", "humano")
    D.no("LIV", 1, 2, "orçamento com\nreserva de encerramento", "nota")
    D.no("ESC", 2, 3, "ESCOLHER\nmenor custo por sucesso", "estado")
    D.no("EXE", 2, 4, "EXECUTAR\no modelo escolhido", "executor")
    D.no("OK", 3, 5, "ACEITAR", "saida")
    D.no("FAL", 1, 5, "REGISTRAR FALHA\ne custo", "refazer")
    D.seta("SUB", "F1"); D.seta("F1", "F2")
    D.seta("CAT", "F2", "l", "r", cor="cinza", tracejada=True)
    D.no("C1", 2, 1, "sobrou algum\nmodelo?", "cond")
    D.no("C2", 2, 2, "algum cabe no saldo\nsem tocar a reserva?", "cond")
    D.seta("F2", "C1", "b", "t")
    D.seta("C1", "ENC", rotulo="não")
    D.seta("C1", "C2", "b", "t", rotulo="sim", lado_rotulo="direita")
    D.seta("C2", "PAU", rotulo="não")
    D.seta("C2", "ESC", "b", "t", rotulo="sim", lado_rotulo="direita")
    D.seta("LIV", "C2", cor="cinza", tracejada=True)
    D.seta("ESC", "EXE", "b", "t")
    D.no("V", 2, 5, "resultado\nverificado?", "cond")
    D.seta("EXE", "V", "b", "t")
    D.seta("V", "OK", rotulo="sim")
    D.seta("V", "FAL", "l", "r", rotulo="não")
    D.seta("FAL", "F1", "l", "b", via=[(0, None), (None, 0.5), (1, None)], cor="vermelho", tracejada=True, rotulo="escalada", pos_rotulo=1, lado_rotulo="esquerda")
    return D

def p4():
    D = Diagrama(5, 8, cw=52)
    D.no("PED", 0, 0, "PEDIDO\n“dermatologista,\nsemana que vem,\nà tarde”", "entrada", hmul=1.45)
    D.no("INT", 1, 0, "MODELO\ninterpreta datas\ne filtros", "executor", hmul=1.2)
    D.no("EST", 2, 0, "ESTADO\ncom versão", "estado")
    D.no("PAU", 3, 1, "PAUSAR\ne encaminhar", "humano")
    D.no("CON", 3, 2, "CONSULTAR\npela chave", "ferramenta")
    D.no("FIM", 1, 3, "CONCLUIR", "saida")
    D.no("EXE", 3, 4, "EXECUTAR\ncom chave idempotente", "ferramenta")
    D.no("PER", 3, 5, "PERGUNTAR\ne aguardar evento", "humano")
    D.no("BUS", 3, 6, "BUSCAR\nopções", "ferramenta")
    D.no("ENC", 2, 7, "ENCAMINHAR", "humano")
    D.no("OBS", 4, 4, "OBSERVAÇÃO\nresultado da ferramenta\nou resposta do usuário,\nlida pelo modelo", "evidencia", hmul=1.45)
    D.seta("PED", "INT"); D.seta("INT", "EST")
    conds = [("G", "cancelado ou\nlimite atingido?", "PAU"), ("C1", "operação externa\nsem resposta?", "CON"),
             ("C2", "confirmada e igual\nao pedido?", None), ("C3", "escolha válida\ne autorizada?", "EXE"),
             ("C4", "há opções\nsem escolha?", "PER"), ("C5", "há alternativa\npermitida?", "BUS")]
    escada(D, conds, 2, 1, 3)
    D.seta("C2", "FIM", "l", "r", rotulo="sim")
    D.seta("EST", "G", "b", "t")
    D.seta("C5", "ENC", "b", "t", rotulo="não", lado_rotulo="direita")
    D.seta("CON", "OBS", "r", "l", via=[(3.5, None), (None, 4)], cor="cinza")
    D.seta("EXE", "OBS", cor="cinza")
    D.seta("PER", "OBS", "r", "l", via=[(3.5, None), (None, 4)], cor="cinza")
    D.seta("BUS", "OBS", "r", "l", via=[(3.5, None), (None, 4)], cor="cinza")
    D.seta("OBS", "EST", "t", "r", via=[(None, 0)], cor="vermelho", tracejada=True, rotulo="atualiza o estado", pos_rotulo="longo")
    return D

def p5():
    D = Diagrama(3, 7, cw=64)
    D.no("AG", 0, 0, "EXECUTOR\nimplementa", "executor")
    D.no("ENT", 1, 0, "ENTREGA\ndiferenças, testes,\nregistros", "evidencia", hmul=1.2)
    D.no("L1", 1, 1, "CAMADA 1: CÓDIGO\ntestes, análise estática,\nescopo das mudanças", "acao", hmul=1.2)
    D.no("L2", 1, 2, "CAMADA 2: RUBRICA\naplicada por modelo,\ncalibrada com pessoas", "acao", hmul=1.2)
    D.no("ENCE", 2, 3, "ENCERRAR\ncom motivo", "refazer")
    D.no("OK", 2, 4, "APROVADO", "saida")
    D.no("REV", 2, 5, "REVISÃO HUMANA", "humano")
    D.no("RF", 0, 6, "REFAZER\ncom a lista do\nque corrigir", "refazer", hmul=1.2)
    D.seta("AG", "ENT"); D.seta("ENT", "L1", "b", "t"); D.seta("L1", "L2", "b", "t")
    escada(D, [("C1", "impossível\nno escopo?", "ENCE"), ("C2", "obrigatórios aprovados\ne rubrica ≥ mínimo?", "OK"),
               ("C3", "evidência\nambígua?", "REV")], 1, 3, 2)
    D.seta("L2", "C1", "b", "t")
    D.no("C4", 1, 6, "falha específica,\nnova e com tentativas?", "cond")
    D.seta("C3", "C4", "b", "t", rotulo="não", lado_rotulo="direita")
    D.seta("C4", "RF", "l", "r", rotulo="sim")
    D.seta("C4", "REV", "r", "b", via=[(2, None)], rotulo="não")
    D.seta("RF", "AG", "t", "b", cor="vermelho", tracejada=True, rotulo="nova tentativa", pos_rotulo=0, lado_rotulo="direita")
    return D

def p6():
    D = Diagrama(5, 7, cw=52)
    D.no("CAS", 0, 0.5, "CASOS REAIS\nconjunto de ajuste e\nconjunto de decisão", "entrada", hmul=1.2)
    D.no("BAN", 1, 0.5, "BANCADA\nambiente restaurado,\nvárias tentativas", "ferramenta", hmul=1.2)
    D.no("A", 2, 0, "A\nbase sem o JEV", "executor")
    D.no("B", 2, 1, "B\nmesma base com o JEV", "executor")
    D.no("MED", 3, 0.5, "MEDIR\npor categoria\nsucesso, custo,\nlatência, intervenção", "evidencia", hmul=1.55)
    D.no("IC", 3, 1.75, "INTERVALO DE 95%\nda diferença de sucesso", "acao")
    D.no("REJ", 4, 2.75, "REJEITAR", "refazer")
    D.no("AMP", 4, 3.75, "AMPLIAR\nA AMOSTRA", "ferramenta")
    D.no("ADO", 4, 4.75, "ADOTAR\nna categoria", "saida")
    D.no("AJU", 3, 5.75, "AJUSTAR B", "estado")
    D.seta("CAS", "BAN")
    D.seta("BAN", "A", "r", "l", via=[(1.5, None), (None, 0)])
    D.seta("BAN", "B", "r", "l", via=[(1.5, None), (None, 1)])
    D.seta("A", "MED", "r", "l", via=[(2.5, None), (None, 0.5)])
    D.seta("B", "MED", "r", "l", via=[(2.5, None), (None, 0.5)])
    D.seta("MED", "IC", "b", "t")
    escada(D, [("C1", "todo o intervalo\nabaixo da margem?", "REJ"), ("C2", "parte abaixo\nda margem?", "AMP"),
               ("C3", "mais barato por sucesso\nou menos intervenção?", "ADO")], 3, 2.75, 4)
    D.nos["C3"]["w"] *= 1.2
    D.seta("IC", "C1", "b", "t")
    D.seta("C3", "AJU", "b", "t", rotulo="não", lado_rotulo="direita")
    D.seta("AJU", "BAN", "l", "b", via=[(1, None)], cor="anil", tracejada=True, rotulo="medir de novo", pos_rotulo=0)
    D.seta("AMP", "CAS", "r", "b", via=[(4.47, None), (None, 6.45), (0, None)], cor="anil", tracejada=True, rotulo="mais casos", pos_rotulo=2, lado_rotulo="abaixo")
    return D

def p7():
    D = Diagrama(5, 7.5, cw=52)
    D.quadro(1, 0, 4, 5.75, "Produção")
    D.no("EV", 0, 2, "EVENTOS\nalerta, e-mail, pedido", "entrada")
    D.no("T", 1, 2, "1 TRIAGEM", "decisao")
    D.no("O", 2, 2, "2 ORQUESTRAÇÃO", "decisao")
    D.no("FIM", 2, 0.75, "CONCLUÍDO\ncom prova", "saida")
    D.no("AGS", 3, 2, "AGENTES\npesquisador, programador,\ntestador, revisor", "executor", hmul=1.2, wmul=1.15)
    D.no("R", 3, 0.75, "3 ROTEAMENTO\nDE MODELOS", "decisao")
    D.no("MOD", 4, 0.75, "MODELOS\npequeno, especialista,\nde fronteira", "executor", hmul=1.2)
    D.no("C", 3, 3.25, "4 CICLO DE\nEXECUÇÃO", "decisao")
    D.no("FER", 3, 4.35, "FERRAMENTAS\ncom chave idempotente", "ferramenta")
    D.no("A", 4, 2, "5 AVALIAÇÃO", "decisao")
    D.no("PES", 1, 4.2, "PESSOA\nabstenção, revisão", "humano")
    D.no("EST", 1, 7.0, "ESTADO, ORÇAMENTO\nE REGISTRO DE DECISÕES", "estado", wmul=1.25)
    D.no("CMP", 3, 7.0, "6 COMPARAÇÃO\nbancada fora da produção", "ferramenta", wmul=1.25)
    D.ancora("QE", 1, 6.2)
    D.ancora("QC", 3, 6.2)
    D.seta("EV", "T")
    D.seta("T", "O")
    D.seta("T", "PES", "b", "t", cor="rosa", rotulo="abster", lado_rotulo="direita")
    D.seta("O", "AGS")
    D.seta("O", "FIM", "t", "b", cor="verde", rotulo="concluir", lado_rotulo="direita")
    D.seta("AGS", "R", "t", "b", da=-0.2, db=-0.2, rotulo="subtarefa", lado_rotulo="esquerda")
    D.seta("R", "AGS", "b", "t", da=0.2, db=0.2, tracejada=True, cor="cinza", rotulo="resposta", lado_rotulo="direita")
    D.seta("R", "MOD", da=-0.2, db=-0.2)
    D.seta("MOD", "R", "l", "r", da=0.2, db=0.2, tracejada=True, cor="cinza")
    D.seta("AGS", "C", "b", "t", da=-0.2, db=-0.2, rotulo="ação externa", lado_rotulo="esquerda")
    D.seta("C", "FER", "b", "t", da=-0.2, db=-0.2)
    D.seta("FER", "C", "t", "b", da=0.2, db=0.2, tracejada=True, cor="cinza", rotulo="observação", lado_rotulo="direita")
    D.seta("AGS", "A", da=-0.22, db=-0.22)
    D.seta("A", "AGS", "l", "r", da=0.22, db=0.22, cor="vermelho", tracejada=True)
    D.seta("A", "O", "b", "b", via=[(None, 5.0), (2, None)], da=-0.3, cor="verde", rotulo="aprovado: novo estado", pos_rotulo=1, lado_rotulo="acima")
    D.seta("A", "PES", "b", "b", via=[(None, 5.5), (1, None)], da=0.3, cor="rosa", rotulo="revisão", pos_rotulo=1, lado_rotulo="acima")
    D.seta("EST", "QE", "t", "b", cor="cinza", tracejada=True)
    D.seta("EST", "CMP", rotulo="registro")
    D.seta("CMP", "QC", "t", "b", cor="anil", tracejada=True, rotulo="adotar, ajustar, ampliar autonomia", lado_rotulo="direita")
    return D

def p0():
    D = Diagrama(5, 4, cw=52)
    D.no("EV", 0, 1, "EVENTOS\nnormalizados e\nsem duplicatas", "entrada", hmul=1.2)
    D.no("EST", 1, 1, "ESTADO\ncom versão, limites\ne saldo do orçamento", "estado", hmul=1.2)
    D.no("N", 2, 1, "NÚCLEO\nDO JEV", "decisao")
    D.no("EXE", 3, 1, "EXECUTORES\nagentes, modelos,\nferramentas", "executor", hmul=1.2)
    D.no("VAL", 4, 1, "VALIDAR\nartefato e resultado", "evidencia")
    D.no("MOD", 2, 0, "MODELO\npropõe entre opções", "executor")
    D.no("PES", 3, 0, "PESSOA\nabstenção, revisão,\naprovação", "humano", hmul=1.2)
    D.no("REG", 2, 2.3, "REGISTRO\nde decisões", "nota")
    D.no("BAN", 3, 2.3, "BANCADA\nfora da produção", "ferramenta")
    D.seta("EV", "EST"); D.seta("EST", "N")
    D.seta("N", "EXE", rotulo="")
    D.seta("EXE", "VAL")
    D.seta("MOD", "N", "b", "t", tracejada=True, cor="cinza")
    D.seta("N", "PES", "r", "l", via=[(2.5, None), (None, 0)], da=-0.3, cor="rosa")
    D.seta("PES", "VAL", "r", "t", via=[(4, None)])
    D.seta("VAL", "EST", "b", "b", via=[(None, 3.25), (1, None)], cor="vermelho", tracejada=True, rotulo="atualiza o estado", pos_rotulo=1, lado_rotulo="acima")
    D.seta("N", "REG", "b", "t", da=-0.25, db=-0.25)
    D.seta("REG", "BAN")
    D.seta("BAN", "N", "t", "b", via=[(None, 1.72), (2.2, None)], db=0.25, cor="anil", tracejada=True, rotulo="calibra", pos_rotulo=1, lado_rotulo="acima")
    return D

TODOS = {"p0": p0, "p1": p1, "p2": p2, "p3": p3, "p4": p4, "p5": p5, "p6": p6, "p7": p7}
```

### Apêndice C

Folha de estilo de todas as páginas.

#### Arquivo `estilo.css`

```css
@page { size: A4 landscape; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: 'Lora', serif; color: #1E2130; font-size: 10.6pt; line-height: 1.55;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
a { color: inherit; text-decoration: none; }
a.ref { font-family: 'Poppins', sans-serif; font-size: 0.78em; color: #4B4FC8; vertical-align: 0.08em; }
.tag { font-family: 'Poppins', sans-serif; font-size: 0.8em; color: #6A6F84; }
.page { width: 297mm; height: 210mm; padding: 12mm 16mm 14mm; position: relative; page-break-after: always; overflow: hidden;
  background-color: #FFFFFF; background-image: radial-gradient(#D9DCEB 0.55px, transparent 0.75px); background-size: 5mm 5mm; }
.rodape { position: absolute; left: 16mm; right: 16mm; bottom: 6mm; display: grid; grid-template-columns: 1fr auto 1fr;
  align-items: center; font-family: 'Poppins', sans-serif; font-size: 8pt; color: #6A6F84; }
.rodape > span:last-child { text-align: right; }
.trilha { display: flex; gap: 1.6mm; }
.trilha .p { width: 5.2mm; height: 5.2mm; border-radius: 50%; border: 0.35mm solid #B7BAD6; display: grid; place-items: center;
  font-size: 6.5pt; color: #8A8FA8; background: #fff; }
.trilha .p.feito { border-color: #4B4FC8; color: #4B4FC8; }
.trilha .p.on { background: #4B4FC8; border-color: #4B4FC8; color: #fff; }

h1, h2, h3 { font-family: 'Poppins', sans-serif; margin: 0; font-weight: 500; }
h2 { font-size: 17pt; margin-bottom: 4mm; }
h2.menor { font-size: 12.5pt; margin-bottom: 3mm; }
.h3 { font-size: 10.5pt; color: #4B4FC8; margin: 0 0 2mm; }
p { margin: 0 0 2.2mm; }
strong { font-weight: 600; }
.lead { font-size: 12pt; line-height: 1.55; max-width: 230mm; color: #2A2E44; }
.sub2 { font-family: 'Poppins'; font-size: 9pt; color: #6A6F84; margin-bottom: 4mm; }
.duas { display: grid; grid-template-columns: 1fr 1fr; gap: 12mm; }
.tres { display: grid; grid-template-columns: 1.05fr 1.1fr 1fr; gap: 8mm; }

/* capa */
.capa { display: grid; grid-template-columns: 1fr 1.05fr; gap: 14mm; height: 100%; align-items: center; }
.capa .rotulo { font-family: 'Poppins'; font-size: 10pt; color: #6A6F84; margin-bottom: 6mm; }
.capa h1 { font-size: 31pt; line-height: 1.12; letter-spacing: -0.3pt; margin-bottom: 7mm; }
.capa .sub { font-size: 12pt; line-height: 1.6; color: #3A3F55; max-width: 120mm; }
.perguntas { list-style: none; margin: 0; padding: 0 0 0 8mm; border-left: 1.2mm solid #4B4FC8; }
.perguntas li { display: grid; grid-template-columns: 11mm 1fr; align-items: baseline; margin: 0 0 4.6mm; }
.perguntas .num { font-family: 'Poppins'; font-weight: 500; font-size: 15pt; color: #4B4FC8; }
.perguntas .t { display: block; font-family: 'Poppins'; font-size: 8.5pt; color: #6A6F84; margin-bottom: 0.6mm; }
.perguntas .q { display: block; font-style: italic; font-size: 15.5pt; line-height: 1.28; }

/* trilha grande */
.trilha-grande { display: grid; grid-template-columns: repeat(6, 1fr); gap: 4mm; margin-top: 6mm; position: relative; }
.trilha-grande::before { content: ""; position: absolute; top: 5.5mm; left: 8%; right: 8%; height: 0.5mm; background: #C9CCE6; }
.est { text-align: center; position: relative; }
.est .bola { width: 11mm; height: 11mm; border-radius: 50%; background: #4B4FC8; color: #fff; display: grid; place-items: center;
  font-family: 'Poppins'; font-size: 12pt; margin: 0 auto 2mm; }
.est .en { font-family: 'Poppins'; font-size: 9pt; font-weight: 500; }
.est .eq { font-style: italic; font-size: 9.6pt; line-height: 1.35; color: #3A3F55; margin-top: 1mm; }

/* cabeçalhos */
.cab { display: grid; grid-template-columns: 20mm 1fr; align-items: end; gap: 4mm; margin-bottom: 4.5mm; }
.cab .grande { font-family: 'Poppins'; font-weight: 500; font-size: 52pt; line-height: 0.9; color: #4B4FC8; }
.cab .titulo { font-family: 'Poppins'; font-weight: 500; font-size: 12pt; color: #4A4F66; margin-bottom: 1mm; }
.cab .pergunta { font-style: italic; font-size: 21pt; line-height: 1.15; }
.badge { display: inline-block; margin-top: 2mm; font-family: 'Poppins'; font-size: 8.6pt; color: #3B3F9E; background: #EEF0FF;
  border-radius: 1.5mm; padding: 0.8mm 2.5mm; }
.cab-min { display: grid; grid-template-columns: auto 1fr auto; gap: 4mm; align-items: baseline; margin-bottom: 3mm; }
.grande-p { font-family: 'Poppins'; font-size: 28pt; color: #4B4FC8; line-height: 1; }
.pergunta-p { font-style: italic; font-size: 17pt; }
.nota-dir { font-family: 'Poppins'; font-size: 8.2pt; color: #6A6F84; text-align: right; line-height: 1.45; max-width: 118mm; }

.diagrama { background: #FFFFFF; border: 0.35mm solid #E1E4F0; border-radius: 3mm; padding: 4mm 6mm; }
.ideia { margin-top: 4.5mm; display: grid; grid-template-columns: 34mm 1fr; gap: 5mm; align-items: start; }
.ideia .r { font-family: 'Poppins'; font-size: 9.2pt; font-weight: 500; color: #4B4FC8; padding-top: 1mm; }
.ideia .txt { font-size: 13pt; line-height: 1.45; border-left: 0.9mm solid #4B4FC8; padding-left: 5mm; }

/* listas numeradas: só para sequências reais */
ol.passos { margin: 0; padding: 0; list-style: none; counter-reset: p; }
ol.passos li { counter-increment: p; position: relative; padding-left: 7mm; margin-bottom: 2.1mm; }
ol.passos li::before { content: counter(p); position: absolute; left: 0; top: 0.3mm; font-family: 'Poppins'; font-weight: 500; font-size: 9.6pt; color: #4B4FC8; }
ol.passos.pequena li { font-size: 9.8pt; margin-bottom: 1.6mm; }
.dica { font-family: 'Poppins'; font-size: 7.8pt; color: #4B4FC8; background: #EEF0FF; border-radius: 1mm; padding: 0.2mm 1.6mm; margin-left: 1mm; }

.caixa { background: #F4F5FB; border-radius: 2.5mm; padding: 3.6mm 4.4mm; }
.caixa p { font-size: 10.1pt; line-height: 1.52; margin: 0; }
.caixa.anil { background: #EEF0FF; }
.caixa.alerta { background: #FFF1F1; }
.caixa.fixar { background: #FFF9DB; }
.caixa.novo-c { background: #FFFFFF; border: 0.45mm dashed #4B4FC8; }
.caixa.novo-c p { color: #2F3380; font-style: italic; }
.caixa .q, p.q { font-style: italic; font-size: 11pt; line-height: 1.45; }
.caixa .h3 { margin-bottom: 1.5mm; }
.citacao { font-style: italic; font-size: 11.2pt; border-left: 0.9mm solid #4B4FC8; padding-left: 4mm; }
.mini-nota { font-family: 'Poppins'; font-size: 8pt; color: #6A6F84; margin-top: 1.5mm; }
.amostra { margin: 1mm 0 3mm; }
.novo-box { display: inline-block; font-style: italic; color: #3B3F9E; border: 0.45mm dashed #4B4FC8; border-radius: 2mm; padding: 1.5mm 4mm; font-family: 'Poppins'; font-size: 9pt; }
.nota-pe { font-size: 9.8pt; color: #3A3F55; line-height: 1.5; }

/* tabelas */
table { border-collapse: collapse; width: 100%; }
th { font-family: 'Poppins'; font-weight: 500; font-size: 8.8pt; color: #4A4F66; text-align: left; padding: 1.8mm 2.6mm; border-bottom: 0.5mm solid #4B4FC8; }
td { font-size: 9.8pt; line-height: 1.4; padding: 1.8mm 2.6mm; border-bottom: 0.25mm solid #E1E4F0; vertical-align: top; }
td.k { font-family: 'Poppins'; font-size: 8.8pt; font-weight: 500; }
td.cinza { color: #6A6F84; font-weight: 400; }
td.it { font-style: italic; }
td.acr { font-style: italic; color: #2F3380; }
table.compacta td { font-size: 9.1pt; padding: 1.15mm 2.2mm; line-height: 1.33; }
table.compacta th { padding: 1.3mm 2.2mm; }
table.mini td { font-size: 8.9pt; padding: 0.9mm 1.8mm; }

/* quatro voltas */
table.voltas { table-layout: fixed; }
table.voltas th { font-size: 10pt; color: #1E2130; border-bottom: 0.6mm solid #4B4FC8; }
table.voltas td { font-size: 9.8pt; padding: 2.4mm 3mm; border-bottom: 1mm solid #FFFFFF; }
table.voltas td.rot { font-family: 'Poppins'; font-size: 9pt; font-weight: 500; width: 30mm; }
.v-estado { background: #DBE4FF; }
.v-decisao { background: #FFF3BF; font-family: 'Poppins'; font-size: 9.2pt !important; }
.v-acao { background: #E5DBFF; }
.v-obs { background: #C3FAE8; }

/* legenda */
.legenda { display: grid; grid-template-columns: 1fr 1fr; gap: 3.4mm 7mm; }
.chip { display: grid; grid-template-columns: 17mm 1fr; align-items: center; gap: 3mm; font-size: 10pt; line-height: 1.35; }
.forma { height: 9mm; border-radius: 2mm; border: 0.55mm solid; }
.forma.losango { width: 8.5mm; height: 8.5mm; transform: rotate(45deg); border-radius: 1mm; margin-left: 4mm; }
.linhas { display: grid; grid-template-columns: 30mm 1fr; gap: 3.2mm 5mm; align-items: center; font-size: 10pt; }

/* exercício */
.rascunho { border: 0.5mm dashed #B7BAD6; border-radius: 3mm; height: 150mm; display: grid; place-items: end center;
  font-family: 'Poppins'; font-size: 8.5pt; color: #9A9EB8; padding-bottom: 4mm; background: rgba(255,255,255,0.6); }

/* referências */
ol.refs { list-style: none; margin: 0; padding: 0; }
ol.refs li { display: grid; grid-template-columns: 9mm 1fr; margin-bottom: 3.2mm; font-size: 10pt; line-height: 1.5; }
ol.refs .rn { font-family: 'Poppins'; color: #4B4FC8; font-size: 9.5pt; }
ol.refs a { color: #3B3F9E; text-decoration: underline; text-decoration-color: #B7BAD6; word-break: break-all; }

/* linha do tempo de rodadas */
.tempo { display: flex; align-items: center; gap: 2mm; margin: 2mm 0 6mm; flex-wrap: wrap; }
.tempo .ch { font-family: 'Poppins'; font-size: 9.5pt; padding: 2mm 3.6mm; border-radius: 2mm; border: 0.5mm solid #1971C2; background: #D0EBFF; }
.tempo .ch.volta { border-color: #C92A2A; background: #FFE3E3; }
.tempo .ch.fim { border-color: #2B8A3E; background: #D3F9D8; }
.tempo .seta { color: #4A4F66; font-size: 12pt; }
.tempo .n { display: block; font-size: 7pt; color: #6A6F84; }

.tab-dec td.o { font-family:'Poppins'; font-size:9pt; color:#4B4FC8; width:8mm; text-align:center; }
.tab-dec td { font-size:9.8pt; padding:2mm 2.6mm; }
.chip-a { display:inline-block; font-family:'Poppins'; font-size:8.6pt; padding:0.6mm 2.2mm; border-radius:1.4mm; border:0.4mm solid; white-space:nowrap; }
.c-exe { background:#D0EBFF; border-color:#1971C2; } .c-fer { background:#E5DBFF; border-color:#7048E8; }
.c-hum { background:#FFDEEB; border-color:#C2255C; } .c-ok { background:#D3F9D8; border-color:#2B8A3E; }
.c-ref { background:#FFE3E3; border-color:#C92A2A; } .c-est { background:#DBE4FF; border-color:#3B5BDB; }
.origem { font-family:'Poppins'; font-size:8.4pt; color:#6A6F84; }
.escada { list-style:none; margin:0; padding:0; counter-reset:d; }
.escada li { counter-increment:d; display:grid; grid-template-columns:12mm 1fr; gap:3mm; align-items:start; padding:2.8mm 0; border-bottom:0.25mm solid #E1E4F0; }
.escada li::before { content:counter(d); width:9mm; height:9mm; border-radius:50%; background:#4B4FC8; color:#fff; display:grid; place-items:center; font-family:'Poppins'; font-size:11pt; }
.escada .t { font-family:'Poppins'; font-weight:500; font-size:10.5pt; }
.escada .d { font-size:9.9pt; color:#3A3F55; }
.col3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8mm; }
.fases { display:grid; grid-template-columns:repeat(4,1fr); gap:4mm; }
.fase { border-radius:2.5mm; padding:4mm; background:#F4F5FB; border-top:1.2mm solid #4B4FC8; }
.fase .n { font-family:'Poppins'; font-size:9pt; color:#4B4FC8; } .fase h3 { font-size:11.5pt; margin:0.5mm 0 2mm; }
.fase p { font-size:9.5pt; line-height:1.45; } .fase .portao { background:#fff; border-radius:1.6mm; padding:2.4mm 3mm; margin-top:2mm; font-size:9.1pt; line-height:1.4; }
.fase .portao b { font-family:'Poppins'; font-weight:500; font-size:8.4pt; color:#2B8A3E; display:block; margin-bottom:0.8mm; }
.tese { font-style:italic; font-size:21pt; line-height:1.3; border-left:1.2mm solid #4B4FC8; padding-left:6mm; }
.cod { font-family:'DejaVu Sans Mono', monospace; font-size:8.6pt; line-height:1.5; background:#F6F7FB; border-radius:2mm; padding:3mm 4mm; white-space:pre-wrap; color:#2A2E44; }
.cab .grande { font-size:46pt; }
.fig { width:100%; }
.cards { display:grid; grid-template-columns:repeat(3,1fr); gap:6mm; margin-top:3mm; }
.card { background:#F4F5FB; border-radius:3mm; padding:7mm 7mm 6mm; min-height:74mm; }
.card .cn { width:10mm; height:10mm; border-radius:50%; background:#4B4FC8; color:#fff; display:grid; place-items:center; font-family:'Poppins'; font-size:12pt; margin-bottom:4mm; }
.card h3 { font-size:14pt; margin-bottom:3mm; }
.card p { font-size:11.8pt; line-height:1.6; color:#2A2E44; }
.pol { }
.pol.sep { border-top:0.35mm solid #D9DCEB; padding-top:4.5mm; margin-top:5mm; }
.pcab { display:flex; align-items:baseline; gap:4mm; margin-bottom:2mm; }
.pcab .pn { font-family:'Poppins'; font-size:28pt; color:#4B4FC8; line-height:1; }
.pcab .pt { font-family:'Poppins'; font-weight:500; font-size:17pt; }
.pcab .pq { font-style:italic; font-size:13pt; color:#4A4F66; }
.pol .tab-dec td { font-size:9.2pt; padding:1.1mm 2.3mm; line-height:1.32; }
.pol .tab-dec th { padding:1.2mm 2.3mm; }
.pol .chip-a { font-size:8.2pt; padding:0.3mm 1.8mm; }
.pol table.compacta td { padding:0.9mm 2.2mm; }
.pol p { font-size:9.8pt; }
.interfaces { display:grid; grid-template-columns:repeat(2,1fr); gap:5mm 10mm; margin-top:7mm; }
.interfaces .cod { font-size:8.8pt; }
```

### Apêndice D

Monta o HTML das 14 páginas e imprime o PDF.

#### Arquivo `montar.py`

```python
"""Monta o PDF “Arquitetura do JEV”.
Arquivos necessários na mesma pasta: grade.py, diagramas.py, estilo.css, montar.py.
Requisitos: Python 3.10+, playwright (pip install playwright; playwright install chromium),
fontes Poppins e Lora instaladas no sistema (sem elas, o navegador usa substitutas).
Uso: python3 montar.py  → gera arquitetura_jev.html e arquitetura_jev.pdf"""
import os, sys
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
from diagramas import TODOS as DG

CSS = open(os.path.join(DIR, "estilo.css"), encoding="utf-8").read()

def chip(txt, c): return f'<span class="chip-a {c}">{txt}</span>'

paginas, pn = [], [0]
def pagina(corpo):
    pn[0] += 1
    rod = f'<div class="rodape"><span></span><span></span><span>{pn[0]}</span></div>' if pn[0] > 1 else ""
    paginas.append(f'<section class="page">{corpo}{rod}</section>')

def cab(sim, titulo, sub):
    return f'<div class="pcab"><span class="pn">{sim}</span><span class="pt">{titulo}</span><span class="pq">{sub}</span></div>'

def tabdec(linhas):
    corpo = "".join(f'<tr><td class="o">{i}</td><td>{c}</td><td>{d}</td><td class="origem">{o}</td></tr>' for i, (c, d, o) in enumerate(linhas, 1))
    return f'<table class="tab-dec"><tr><th></th><th>Condição, nesta ordem</th><th>Decisão</th><th>Origem</th></tr>{corpo}</table>'

# capa
pagina('''<div class="capa">
 <div>
  <h1>Arquitetura do JEV</h1>
  <p class="sub">Um núcleo de decisão e seis políticas: triagem, orquestração de agentes, roteamento de modelos, ciclo de execução, avaliação e comparação.</p>
 </div>
 <div><p class="tese">O modelo interpreta texto livre.<br/>O código controla o fluxo.</p></div>
</div>''')

# princípios
princ = [("Um núcleo, seis políticas", "Toda decisão passa pelo mesmo núcleo, com a mesma ordem de precedência. Cada tipo de decisão é uma política."),
         ("Regras antes de modelo", "Cancelamento, conclusão comprovada, limites e regras determinísticas decidem primeiro. O modelo propõe só quando nenhuma regra cobre o estado, e só entre opções permitidas."),
         ("Conclusão exige prova", "Cada executor entrega um artefato verificável. A conclusão depende de prova vinda da ferramenta ou dos testes."),
         ("Orçamento com reserva", "Parte do limite por tarefa fica reservada para avaliar e responder. O trabalho não consome a reserva."),
         ("Efeito externo seguro", "Toda ação com efeito fora do sistema usa chave idempotente. Resposta perdida leva a consulta, nunca a repetição cega."),
         ("Autonomia por evidência", "A autonomia cresce por fases e por categoria, conforme a comparação com a linha de base.")]
cards = "".join(f'<div class="card"><div class="cn">{i}</div><h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(princ, 1))
pagina(f'''<h2>Princípios</h2><div class="cards" style="margin-top:6mm">{cards}</div>''')

# arquitetura
pagina(f'''<h2>Visão geral</h2>
 <div class="fig" style="height:96mm">{DG["p0"]().svg("p0")}</div>
 <div class="col3" style="margin-top:6mm">
  <div><h3 class="h3">Estado persistido</h3><p>Fonte única da verdade da tarefa. Toda escrita informa a versão lida; escrita sobre versão desatualizada é recusada e refeita.</p></div>
  <div><h3 class="h3">Núcleo</h3><p>Lê o estado, aplica a política da decisão em curso e devolve uma ação permitida ou um encaminhamento. Não executa: quem age são os executores, e o resultado volta ao estado só depois de validado.</p></div>
  <div><h3 class="h3">Registro e bancada</h3><p>Cada decisão grava política, opções, escolha, motivo, origem e custo. A bancada, fora da produção, usa esse registro para calibrar os parâmetros.</p></div>
 </div>''')

# núcleo
usos = [("Triagem", "duplicata; alerta crítico", "classificar texto livre"),
        ("Orquestração de agentes", "máquina de estados com guardas", "estado ambíguo"),
        ("Roteamento de modelos", "restrições, qualidade mínima, custo, saldo", "—"),
        ("Ciclo de execução", "reconciliar, concluir, executar, perguntar, buscar", "interpretar pedido e resposta do usuário"),
        ("Avaliação", "testes, análise estática, escopo, tentativas", "rubrica de qualidade"),
        ("Comparação", "regra de adoção", "—")]
lu = "".join(f'<tr><td class="k">{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in usos)
pagina(f'''<h2>Núcleo de decisão</h2>
 <div class="duas" style="grid-template-columns:1fr 1.1fr;gap:11mm">
  <div><h3 class="h3">Ordem de precedência</h3><ol class="escada">
   <li><div><div class="t">Cancelamento</div><div class="d">Encerra, mesmo com operação pendente.</div></div></li>
   <li><div><div class="t">Conclusão comprovada</div><div class="d">Prova da ferramenta ou dos testes conclui a tarefa.</div></div></li>
   <li><div><div class="t">Limites</div><div class="d">Voltas, voltas sem progresso, tentativas e saldo. Limite atingido pausa com motivo.</div></div></li>
   <li><div><div class="t">Regras da política</div><div class="d">Decisões determinísticas: baratas, reproduzíveis, auditáveis.</div></div></li>
   <li><div><div class="t">Proposta do modelo</div><div class="d">Saída estruturada, restrita às opções permitidas. Proposta fora da lista é recusada e contada.</div></div></li>
   <li><div><div class="t">Alternativa segura</div><div class="d">A opção de menor risco da política, como coletar evidência ou abster.</div></div></li>
  </ol></div>
  <div><h3 class="h3">Regra e modelo por política</h3>
   <table class="compacta"><tr><th>Política</th><th>Decidido por regra</th><th>Modelo</th></tr>{lu}</table></div>
 </div>''')

# estado
contrato = [("id e versão", "correlacionar eventos; recusar escrita sobre versão desatualizada"),
            ("objetivo e critérios de conclusão", "o que conta como pronto"),
            ("autonomia", "ações executáveis sem pedir aprovação"),
            ("dados, evidências, artefatos", "base das decisões e das retomadas"),
            ("pendências", "o que falta e por que o sistema continua ou aguarda"),
            ("tentativas, voltas, prazo, saldo", "limites de repetição e gasto"),
            ("status e motivo", "em andamento, aguardando, concluído, interrompido, encaminhado"),
            ("chave da operação externa", "consultar e reconciliar reservas, envios, implantações"),
            ("registro de decisões", "política, opções, escolha, motivo, origem, custo")]
lc = "".join(f'<tr><td class="k">{a}</td><td>{b}</td></tr>' for a, b in contrato)
pagina(f'''<h2>Contrato de estado e interfaces</h2>
 <div class="duas" style="grid-template-columns:1.2fr 1fr;gap:11mm">
  <table class="compacta"><tr><th style="width:36%">Campo</th><th>Função</th></tr>{lc}</table>
  <div>
   <h3 class="h3">Progresso</h3>
   <p>Ao fim de cada volta, o núcleo calcula uma impressão dos dados e das pendências. Impressão igual por duas voltas seguidas pausa o ciclo.</p>
   <h3 class="h3" style="margin-top:5mm">Espera</h3>
   <p>Pergunta ao usuário deixa o estado em “aguardando” e encerra o processo. A resposta chega como evento, é gravada no estado e o ciclo retoma dali, sem repetir a pergunta.</p>
   <h3 class="h3" style="margin-top:5mm">Escopo</h3>
   <p>O estado guarda fatos, evidências e referências a artefatos. Cada executor recebe só o recorte de que precisa.</p>
  </div>
 </div>
 <div class="interfaces">
  <div><h3 class="h3">Proponente</h3><div class="cod">propor(politica, opcoes, contexto)
→ {{ escolha: uma das opcoes,
    motivo }}</div></div>
  <div><h3 class="h3">Executor</h3><div class="cod">executar(papel, recorte_do_estado)
→ {{ artefato_do_papel,
    evidencias }}</div></div>
  <div><h3 class="h3">Ferramenta com efeito externo</h3><div class="cod">executar(parametros, chave)
→ confirmado | recusado | sem resposta
consultar(chave) → resultado | nada</div></div>
  <div><h3 class="h3">Registro de decisão</h3><div class="cod">{{ tarefa, versao, politica, opcoes,
  escolha, motivo, origem, custo,
  modelo_e_versao, instante }}</div></div>
 </div>''')

POL = [("p1", 1, "Triagem", "O que chegou, com que urgência e quem assume"),
       ("p2", 2, "Orquestração de agentes", "Quem trabalha agora e quando parar"),
       ("p3", 3, "Roteamento de modelos", "Quanto de inteligência cada subtarefa merece"),
       ("p4", 4, "Ciclo de execução", "Agir sem duplicar, sem adivinhar, sem esperar à toa"),
       ("p5", 5, "Avaliação", "O resultado pode seguir?"),
       ("p6", 6, "Comparação", "Quando o JEV assume uma categoria")]
for chave, n, tit, q in POL:
    pagina(f'''<div class="pcab"><span class="pn">{n}</span><span class="pt">{tit}</span><span class="pq">{q}</span></div>
     <div class="fig" style="height:166mm">{DG[chave]().svg(chave)}</div>''')
pagina(f'''<div class="pcab"><span class="pn">+</span><span class="pt">Integração</span><span class="pq">Os seis usos num só sistema</span></div>
     <div class="fig" style="height:166mm">{DG["p7"]().svg("p7")}</div>''')

# fases e medidas
pagina('''<h2>Implantação em fases</h2>
 <div class="fases">
  <div class="fase"><div class="n">Fase 0</div><h3>Linha de base</h3><p>Bancada com casos reais; processo atual medido com as mesmas medidas; registro de decisões instalado.</p>
   <div class="portao"><b>Portão</b>medidas estáveis entre repetições; critérios de sucesso aceitos pelos donos do processo.</div></div>
  <div class="fase"><div class="n">Fase 1</div><h3>Modo sombra</h3><p>O JEV decide em paralelo, sem executar. Decisões comparadas às das pessoas.</p>
   <div class="portao"><b>Portão</b>triagem na precisão alvo por categoria; nenhuma aprovação com critério obrigatório reprovado.</div></div>
  <div class="fase"><div class="n">Fase 2</div><h3>Autonomia restrita</h3><p>Ações reversíveis executadas. Ações com efeito externo pedem aprovação.</p>
   <div class="portao"><b>Portão</b>regra de adoção cumprida na bancada e em amostra de produção da categoria.</div></div>
  <div class="fase"><div class="n">Fase 3</div><h3>Autonomia por categoria</h3><p>Categorias aprovadas liberadas. Casos rotineiros passam à bateria de regressão.</p>
   <div class="portao"><b>Portão contínuo</b>regressão perto de 100%; custo e intervenção humana por categoria. Falha grave devolve a categoria à fase anterior.</div></div>
 </div>
 <h3 class="h3" style="margin-top:7mm">Medidas</h3>
 <table class="compacta"><tr><th style="width:18%">Onde</th><th>Acompanhar</th><th style="width:31%">Tolerância zero</th></tr>
  <tr><td class="k">Núcleo</td><td>decisões por origem: guarda, regra, modelo, alternativa; propostas inválidas</td><td>—</td></tr>
  <tr><td class="k">Triagem</td><td>precisão e cobertura por categoria; abstenção; tempo até o responsável</td><td>incidente classificado como melhoria</td></tr>
  <tr><td class="k">Orquestração</td><td>rodadas por caso; retornos rejeitados; tempo até resolver</td><td>conclusão sem artefato validado</td></tr>
  <tr><td class="k">Roteamento</td><td>custo por sucesso por família; escaladas; pausas por saldo</td><td>reserva de encerramento consumida</td></tr>
  <tr><td class="k">Ciclo</td><td>voltas por tarefa; reconciliações; tempo em espera</td><td>efeito externo duplicado</td></tr>
  <tr><td class="k">Avaliação</td><td>concordância com revisão humana; tentativas por caso</td><td>aprovação com critério obrigatório reprovado</td></tr></table>''')

# parâmetros e riscos
params = [("tentativas de correção", "2", "sucesso na segunda tentativa"),
          ("voltas sem progresso", "2", "pausas resolvidas com uma ação simples"),
          ("voltas por tarefa", "12", "percentil 99 dos casos bem-sucedidos"),
          ("reserva de encerramento", "15% do limite", "custo real de avaliar e responder"),
          ("precisão alvo da triagem", "90%", "custo de encaminhamento errado por categoria"),
          ("margem de não inferioridade", "2 pontos", "perda aceitável para o dono do processo"),
          ("qualidade mínima por família", "0,80 a 0,85", "retrabalho aceitável")]
lp = "".join(f'<tr><td class="k">{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in params)
riscos = [("ação ou categoria inexistente proposta pelo modelo", "lista fechada de opções; recusa e contagem"),
          ("ciclo sem fim", "limites de voltas, tentativas e progresso"),
          ("orçamento esgotado antes da verificação", "reserva de encerramento"),
          ("efeito externo duplicado", "chave idempotente e consulta antes de repetir"),
          ("sucesso declarado sem prova", "artefato por papel; conclusão comprovada pela ferramenta"),
          ("avaliador por modelo desalinhado", "critérios obrigatórios em código; rubrica calibrada"),
          ("comparação enganosa", "mesma base com e sem o JEV; conjunto de decisão separado"),
          ("dado sensível no modelo errado", "classe de dados como restrição no roteamento"),
          ("atualizações concorrentes", "versão no estado")]
lr = "".join(f'<tr><td class="k">{a}</td><td>{b}</td></tr>' for a, b in riscos)
pagina(f'''<div class="duas" style="gap:11mm">
 <div><h2>Parâmetros</h2><table class="compacta"><tr><th>Parâmetro</th><th>Valor inicial</th><th>Recalibrar com</th></tr>{lp}</table></div>
 <div><h2>Riscos e mitigações</h2><table class="compacta"><tr><th>Risco</th><th>Mitigação</th></tr>{lr}</table></div>
</div>''')

# base técnica
refs = [("Building effective agents", "Anthropic, 2024", "https://www.anthropic.com/engineering/building-effective-agents"),
        ("Demystifying evals for AI agents", "Anthropic, 2026", "https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents"),
        ("FrugalGPT", "Chen, Zaharia e Zou, 2023", "https://arxiv.org/abs/2305.05176"),
        ("Making retries safe with idempotent APIs", "Amazon Builders' Library, 2021", "https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/")]
lrf = "".join(f'<li><span class="rn">•</span><span><em>{t}</em>. {a}. <a href="{u}">{u}</a></span></li>' for t, a, u in refs)
paginas[-1] = paginas[-1].replace('</div>\n</div><div class="rodape">', f'</div>\n</div><h3 class="h3" style="margin-top:7mm">Base técnica</h3><ol class="refs" style="columns:2;column-gap:10mm">{lrf}</ol><div class="rodape">')

doc = (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Arquitetura do JEV</title>'
       f'<style>{CSS}</style></head><body>{"".join(paginas)}</body></html>')
saida_html = os.path.join(DIR, "arquitetura_jev.html")
open(saida_html, "w", encoding="utf-8").write(doc)
print("páginas:", pn[0])

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    nav = p.chromium.launch()
    pg = nav.new_page()
    pg.goto("file://" + saida_html)
    pg.wait_for_timeout(800)
    pg.pdf(path=os.path.join(DIR, "arquitetura_jev.pdf"), prefer_css_page_size=True, print_background=True)
    nav.close()
print("PDF gerado:", os.path.join(DIR, "arquitetura_jev.pdf"))
```
