# Documento de arquitetura

## Arquivos

- [Fonte editável](../../docs/ARQUITETURA-DO-JEV-REVISAO.md): texto, ordem das páginas e dez fluxos Mermaid.
- [PDF](../../output/pdf/ARQUITETURA-DO-JEV-REVISAO.pdf) e [HTML](../../output/arquitetura-jev.html): entregáveis A4 em paisagem, com 18 páginas.
- [Fontes e validação](VERIFICACAO.md): evidências, testes, integridade dos originais e origem da capa.
- [Manifesto de leiaute](validacao-layout.json): hashes e verificações da última geração.
- [Ativos](../../docs/arquitetura-assets/): capa, SVGs gerados e Markdown original.

## Regenerar

Requer Node.js 20 ou superior e Google Chrome. Na pasta `planning/arquitetura`:

```powershell
npm install --ignore-scripts
npm run build
```

No Windows, o caminho padrão do navegador é `C:/Program Files/Google/Chrome/Application/chrome.exe`. Defina `JEV_DOC_CHROME` para usar outra instalação. Também é possível apontar `JEV_DOC_NODE_MODULES` e `JEV_DOC_BROWSER_MODULES` para instalações existentes de `markdown-it` e `playwright`, respectivamente.

O comando gera o HTML, o PDF, os SVGs e o manifesto. Falha se houver link local quebrado, texto fora de uma caixa de diagrama ou conteúdo ultrapassando a área útil da página. A conferência visual final usa o PDF renderizado em imagens.

## Editar

O Markdown mantém blocos Mermaid padrão e marcadores de página `<!-- page: ... -->`. Cada seção `###` vira um cartão no PDF. O arquivo `style.css` controla tipografia, margens, cores e grades.

`diagrams.mjs` lê rótulos, nós, classes e relações diretamente dos blocos Mermaid; suas coordenadas e rotas definem a composição dos dez diagramas desta edição. Ele aceita o subconjunto utilizado no documento e recusa comandos desconhecidos. Ao acrescentar nós ou diagramas, ajuste também essas coordenadas. Os SVGs são vetoriais; o HTML incorpora a capa e os diagramas, sem depender de scripts ou de recursos de rede para a leitura.

A ilustração da capa é um ativo pronto. Regenerar o documento não chama serviço de imagem nem faz inferências.

## Atualizar o mapa durante a edição

Na raiz do repositório, os novos arquivos desta entrega podem ser incluídos explicitamente:

```powershell
$arquivos = Get-Content planning/arquitetura/arquivos-mapa.txt
python mapa/gerar_mapa.py --verificar --incluir $arquivos
```

O gerador aceita apenas arquivos existentes, dentro do repositório e não ignorados pelo Git. Após versioná-los, o comando habitual `python mapa/gerar_mapa.py --verificar` já os inclui.
