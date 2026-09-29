# Arquitetura do JEV — fontes e validação

Data da revisão: 24/09/2026.

## Material de origem

| Arquivo preservado | SHA-256 |
|---|---|
| `docs/ARQUITETURA-DO-JEV.pdf` | `7b121fd58addf6cd2f46728528ca639f0da4ed73f2156b37325cc9463d915d97` |
| `docs/arquitetura-assets/fonte-original.md` | `3d41559f6e0fb7dbe706ad6ff26d008c382e10fa18769c616b1d8c0de00fa3c2` |

Os hashes conferem com os arquivos fornecidos em Downloads. O PDF original tem 14 páginas. O texto e os códigos anexados no Markdown foram tratados como material de referência.

## Decisões fundamentadas

| Tema | Evidência consultada | Aplicação na revisão |
|---|---|---|
| Cobertura de contexto | [R18–R20](../../laboratorio/r18-r20-consolidado.json): 169 perguntas, 158 acertos com dois trechos versus 141 com oito; 383.150 versus 1.472.278 bytes | Medir qualidade da resposta junto do contexto; preservar origem e recuperar candidatos omitidos |
| Resposta distribuída | [R26](../../laboratorio/r26-dois-trechos.json): 6, 40, 50 e 60 acertos em 80 pares, para um, dois, três e oito trechos | Seleção adaptável à cobertura; três trechos como começo operacional para estrutura distribuída ou desconhecida |
| Confiança e entrada hostil | [R21b](../../laboratorio/r21b-cruzamento.json): 28 mudanças em 81 casos; uma acima de 0,90 | Confiança não concede autoridade; saída tipada ainda exige evidência e validação |
| Reserva financeira | [test_ledger.py](../../executor/tests/test_ledger.py), [test_liquidacao_429.py](../../executor/tests/test_liquidacao_429.py) | Reserva antes do envio, compromisso preservado na incerteza e conciliação por recibo |
| Continuidade | [Guia do harness](../../integracao/harness/AGENT-GUIDE.md), [test_agents.py](../../integracao/harness/test_agents.py) | Pedido aceito, execução e conclusão separados; mesma chave e mesmos parâmetros; efeitos após interrupção precisam de conciliação |
| Escolha explícita | [test_seletores.py](../../integracao/tests/test_seletores.py) | Restringir ao catálogo, preservar a escolha do usuário e tratar abstenção/falha |
| Fluxos inspecionáveis | [Jev Flow](../../research/JEV-FLOW.md), commit `75e63491f63691418251534f50e8c8ddca9a5fc0` | Contratos de nós, prévia, fixtures e trilha; controle de passos/tokens separado da reserva monetária |
| Comparação | [Dossiê](../../docs/DOSSIE-DE-EVIDENCIAS.md), [Limites](../../docs/LIMITES-DO-JEV.md) e metodologia de avaliação do projeto | Pareamento por caso, margem prévia, famílias correlacionadas e custo total por sucesso |

As propostas de estado unificado, reserva de encerramento e adoção por categoria pertencem à arquitetura revisada. Os testes citados confirmam os contratos específicos descritos, com transporte simulado; não constituem implantação integral dessas propostas.

Foram retirados os limites iniciais arbitrários do texto de origem (tentativas, voltas e percentual de reserva). A página de parâmetros descreve como medi-los e quando revê-los.

## Verificações executadas

```powershell
python -m pytest executor/tests/test_ledger.py executor/tests/test_liquidacao_429.py integracao/harness/test_agents.py integracao/tests/test_seletores.py -q
```

Resultado: **45 testes e 3 subtestes aprovados**, em 7,07 segundos. A tentativa de incluir `laboratorio/tests/test_auditoria.py` encontrou a dependência ausente `statsmodels` durante a coleta. Os números reproduzidos na edição foram conferidos diretamente nos três JSONs indicados acima.

Na análise anterior do Jev Flow: 83 testes locais, 81 aprovados e 2 ignorados; 388.080 configurações do certificado verificadas. Detalhes e escopo em [JEV-FLOW.md](../../research/JEV-FLOW.md).

O auxiliar JEV informou `paid_ready: false`, `runtime_check_failed` e `BudgetError`. A revisão de conteúdo prosseguiu pela leitura direta das fontes, sem inferências pagas pelo executor JEV.

## Documento e diagramação

- 18 páginas em A4 paisagem, 10 diagramas vetoriais e imagem na capa.
- Texto e relações dos diagramas derivam do mesmo Markdown.
- Conteúdo dentro da área útil e texto dentro das caixas: verificação automática na geração.
- Revisão visual das 18 páginas renderizadas do PDF: capa, hierarquia, tabelas, setas, rótulos e rodapés.
- HTML com imagem e SVGs incorporados; sem scripts ou recursos remotos de apresentação.
- Hashes dos entregáveis e medidas por página em [validacao-layout.json](validacao-layout.json).

## Complemento de 28/09/2026

Fonte: [10 Levels of Jev](../../research/TEN-LEVELS-OF-JEV.md), com análise dos dez níveis, referências de tempo e revisão do código `777adaf47d37ae0553220d35b2f15b3a3a063305`.

- Triagem: pontuação por critério, normalização e pesos em código.
- Contexto: perguntas por arquivo, agrupamento de perguntas independentes e lotes limitados.
- Orquestração: perguntas formuladas pelo agente, com opções, escape e fonte.
- Execução: verificação no ponto de chamada e compactação em pausa segura.
- Avaliação: classificação de falhas separada da confirmação por testes e artefato.
- Parâmetros e fontes atualizados nas seções existentes.

Mantidos **18 páginas e 10 diagramas**, agora com 93 nós e 101 relações. Acréscimo líquido inferior a 100 palavras no texto e nas tabelas (excluídos os blocos Mermaid, marcadores de página e URLs dos links). O PDF foi comparado à versão anterior por renderização: apenas as páginas 8, 9, 10, 12, 13, 17 e 18 mudaram. As sete páginas alteradas foram conferidas visualmente; as onze páginas restantes, incluindo a capa, permaneceram iguais.

Verificações: A4 paisagem; ausência de texto fora das caixas e de conteúdo fora da área útil; fonte mínima dos nós de 10,9 pt; links locais resolvidos; hashes do manifesto correspondentes aos entregáveis. As fontes, margens e cores da edição anterior foram preservadas.

Esta atualização alterou a documentação e os diagramas. A execução dos 45 testes e 3 subtestes citados acima permanece datada de 24/09/2026. Em 28/09, o auxiliar JEV continuou sem prontidão (`runtime_check_failed`, `BudgetError`); a seleção das contribuições foi realizada por leitura direta.

## Identidade e autoria — 28/09/2026

Marca INTEIA na capa e assinatura tipográfica **Professor Igor Vasconcelos**, conforme solicitação do autor. Identificação discreta nos rodapés das páginas internas. O vetor [inteia-marca.svg](../../docs/arquitetura-assets/inteia-marca.svg) é uma cópia integral de `web/assets/inteia-nome-oficial.svg` do acervo INTEIA-laboratorio-3d; contornos e cores preservados. Capa e página interna conferidas visualmente; autoria verificada por extração de texto nas 18 páginas.

## Imagem da capa original

Ferramenta: `image_gen.imagegen`, geração nativa de imagem. Ativo: [capa.png](../../docs/arquitetura-assets/capa.png). SHA-256: `2d385633dceeec5c0603e32dfd1cd18d90fc9ca2e7f70d08f564df2517201874`.

Prompt final utilizado:

> Use case: stylized-concept. Create a sophisticated editorial 3D illustration for the cover of a Portuguese engineering document about a decision architecture named JEV. No text, no lettering, no logos. A precisely crafted translucent indigo central architectural module surrounded by six smaller functional modules on a warm white plane, connected by a few clean fine indigo and mint pathways; visible layers suggest incoming information, a governed decision core, and verified outputs. Elegant isometric product photography with soft daylight, realistic frosted glass and matte ceramic, dark navy accents, very subtle shadow. Calm, intelligent, refined, spacious, practical engineering rather than science fiction. Landscape 3:2 composition, object composition centered toward the right with substantial warm-white negative space on the left. Crisp at print resolution. Avoid human figures, robots, brains, hands, glowing neon, circuit-board cliches, busy networks, tiny decorative text, watermark. This is a conceptual cover image; the technical diagrams are provided separately.
