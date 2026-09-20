# JEV

Projeto experimental para testes com o modelo de classificação JEV.

## Execução realizada

- **[Relatório final](docs/RELATORIO-FINAL-JEV.md)** — recomendação, os nove experimentos, contra-hipóteses
  testadas e os limites que o estudo não autoriza ultrapassar. Comece por aqui.
- **[Guia prático](docs/GUIA-PRATICO-JEV.md)** — como aplicar, passo a passo, com os cuidados em ordem de risco.
- **[Os limites do Jev](docs/LIMITES-DO-JEV.md)** — mapa empírico do programa E14: onde ele quebra, onde não
  quebra, a queda da afirmação de imunidade a manipulação e a classe de escape obrigatória.
- **[Cem hipóteses sobre o Jev](docs/CEM-HIPOTESES.md)** — o registro com as cem, a previsão de cada uma
  escrita antes do teste, e o que o dado respondeu: 81 sustentadas, 18 falsificadas, 1 inconclusiva.
  Entre as falsificadas está a imunidade a meta-instrução, que era a afirmação mais forte do estudo.
- **[Cem perguntas estratégicas](docs/CEM-PERGUNTAS-ESTRATEGICAS.md)** — o que fazer com o modelo, não o que
  ele faz. Cada pergunta declara a decisão que informa e o que a faria virar; 76 se respondem com dado
  medido, 19 com conta sobre o medido e 5 exigiram coleta nova. Os parâmetros não medidos estão declarados
  um a um, e um teste quebra se alguma resposta usar um deles calada.
- **[Bateria complementar](docs/BATERIA-COMPLEMENTAR.md)** — cinco rodadas que fecham o que o estudo tinha
  declarado em aberto: a sanitização por lista não generaliza (o sentinela sim), votar a mesma pergunta não
  serve (a formulação decide), a acurácia cai com a distância do domínio, e as duas defesas cabem num payload
  se o sentinela ler o texto original. Mais de 14 mil chamadas novas, cada número recalculado pela auditoria.
- **[Dossiê de evidências](docs/DOSSIE-DE-EVIDENCIAS.md)** — cada afirmação do estudo com a força dela
  (demonstrado, direção, medição única, falsificado) e, em cada uma, o que ela **não** prova. Página gerada
  a partir do dado bruto.
- **[Auditoria dos números](docs/AUDITORIA-DE-NUMEROS.md)** — as 1.128 conferências que recalculam cada número
  publicado a partir das linhas de resposta originais, com estatística independente da que gerou os resumos.
  Presa na suíte de testes: número sem dado que o sustente quebra o `pytest`.
- **Canários de comportamento** (`python -m laboratorio.canarios_de_comportamento --rodar`) — oito propriedades
  em que o guia se apoia, verificáveis em 16 chamadas por menos de US$ 0,0003. A auditoria pega erro meu; o
  canário pega mudança do modelo. A primeira corrida derrubou uma afirmação publicada em menos de 24 horas.
- [O Jev nos fluxos desta máquina](integracao/README.md) — os dois hooks instalados, o que cada um decide, o que foi medido e como ligar ou desligar.
- [Pré-registro do E14](laboratorio/PREREGISTRO.md) — hipóteses, emendas datadas e o falso achado que produzi
  e corrigi antes de publicar, mantido no registro.
- [Relatório de execução intermediário](docs/RELATORIO-EXECUCAO-JEV-HELENA.md) — escrito antes do E5 ao E9;
  mantido como registro histórico, superado pelo final onde houver divergência.
- [Executor financeiro e contrato real da API](executor/README.md)
- Pré-registros: [E1 piloto](planning/preregistro-E1-triagem.md),
  [E7 confirmação](planning/preregistro-E7-confirmacao.md),
  [E10 LLM econômico](planning/preregistro-E10-llm-economico.md),
  [E11 desempate](planning/preregistro-E11-desempate.md) e
  [E12 replicação](planning/preregistro-E12-replicacao.md), todos com emendas declaradas.
- Corpora: [triagem piloto](data/corpus/triagem-piloto.jsonl),
  [triagem confirmação](data/corpus/triagem-confirmacao.jsonl),
  [evidência](data/corpus/evidencia-piloto.jsonl), [ressalvas](data/corpus/ressalvas-piloto.jsonl)
  e [replicação](data/corpus/triagem-replicacao.jsonl).
- Resultados brutos em `runs/`, um diretório por experimento.

**1.474 chamadas reais, US$ 0,035707114** neste dossiê (E1 a E12), conciliados contra um extrato
de provedor de US$ 0,034640289 — os números vêm do ledger em `runs/ledger.sqlite3`, não deste
texto. O programa de limites E14 e as rodadas E15/E16 liquidam no mesmo livro-caixa e levam o
ledger a 4.558 tentativas e 0,283629435 de unidade de conta; **essa parte ainda não foi
conciliada contra extrato do provedor**, e por isso o total do dossiê continua sendo o número
auditado. Teto autorizado: US$ 5,00. Na triagem piloto, Jev 0,925 contra 0,600 da regra
congelada; no conjunto de confirmação, 0.975 contra
0.325; na relação afirmação/evidência, 0,958 contra 0,625. Esses números usam o gabarito do autor, como pré-registrado; o gabarito oficial, depois da adjudicação cega descrita na seção 3.6.1 do relatório final, move a confirmação para 40/40 e o estudo inteiro para 0,9625. O painel exibe a faixa entre os dois, nunca só o melhor.

Na replicação (E12), 90 casos novos em 30 famílias contra **quatro** LLMs econômicos de quatro
fornecedores: o Jev acerta 0,9889 e supera todos eles no gabarito adjudicado, de +7,8% a +14,4%,
e **não separa de zero contra nenhum deles** sob o gabarito do anotador independente — contra o
llama-3.1-8b a diferença é exatamente 0,0. A regra
de leitura estava congelada antes de existir qualquer caso, e o veredito que ela produz é
`depende-do-gabarito`.

**O que isto não decide:** adoção. O gabarito é autoral e de um anotador humano só, os corpora são
construídos e não colhidos de uso real, e o modelo não é determinístico. A recomendação operacional e os
sete limites estão na seção 1 e na seção 8 do relatório final.

## Plano de testes atual

- [Plano científico completo — Helena](docs/PLANO-CIENTIFICO-JEV-HELENA.md)
- [PDF para leitura](output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf)
- [Painel de acompanhamento e métricas explicadas](lab/index.html) — execução, sistemas, resultados, orçamento e fontes.
- [Como usar e alimentar a interface](lab/README.md) — importação, backup e atualização conectada à pasta.
- [Matriz dos 15 sistemas](planning/matriz-testes.csv) e [plano estruturado](planning/plan.json)
- [Esquema de dados para a execução](planning/schema.sql)
- [Auditoria das tabelas do Hermes](research/hermes/auditoria-local.json)

O plano previa rodada simples e rodada aprofundada para os 15 sistemas. A rodada simples foi executada como suíte offline de cada repositório, o que mede estado de código e não comportamento do componente. **A rodada aprofundada está bloqueada por dependência de dados**, não por tempo ou orçamento: ela pede centenas de casos por sistema, e produzi-los de forma autoral multiplicaria o viés que o relatório final aponta como limite principal. O desbloqueio está no item 1 da seção 10 do relatório final.

O teto autorizado é de **US$ 5,00 de gasto novo**, decidido em 18/09/2026: o histórico de US$ 3,002937546 não ocupa esse limite. Os blocos planejados somam US$ 1,70, dentro do teto. O limite de US$ 50 informado pela chave continua sendo apenas uma segunda barreira do provedor, não uma autorização. O executor financeiro em `executor/` aplica o teto por reserva atômica antes de cada chamada. Estado atual: 1.474 tentativas registradas, US$ 0,035707114 comprometidos, 0 reservas pendentes sem liquidação, conciliado contra o extrato do provedor, que marca US$ 0,034640289. Esses números podem ser conferidos por quem clona o repositório: `runs/extrato-ledger.json` traz o extrato por tentativa, gerado por `python -m executor.exportar_extrato`. O controle passou por **dezesseis rodadas de revisão independente**, por modelos de outros fornecedores, e o defeito mais caro de todos não veio de nenhuma delas: veio da execução do E12, que foi a primeira a levar HTTP 429 e mostrou que o executor liquidava por US$ 0,499 chamadas em que nenhum token foi processado. O histórico está na seção 9 do relatório final.

Para reproduzir os cálculos e documentos, usar Python com ReportLab instalado:

```powershell
python research/audit_hermes_pdf.py
python planning/build_plan.py
python planning/build_deliverables.py
```

`planning/protocolo.md` e `planning/build_plan.py` são as fontes do documento. O gerador produz o Markdown final, a matriz, o painel e o PDF. Nenhum desses comandos faz inferências ou acessa credenciais.

## Estudo inicial

- [Triagem de projetos e plano de avaliação — Helena](docs/TRIAGEM-JEV-HELENA.md)
- [Fontes, arquivos e revisões consultadas](research/FONTES.md)
- [Manifesto das 18 fontes GitHub](research/sources-manifest.json)

Pesquisa de 18/09/2026, sem inferências pagas. Orçamento cumulativo máximo para testes futuros: **US$ 5**. A credencial fica somente no `.env` local; consultar `AGENTS.md` antes de executar experimentos.

## Continuar em outra máquina

```powershell
git clone https://github.com/igormorais123/JEV.git
cd JEV
python lab/server.py --port 8766
```

Abra http://127.0.0.1:8766. O painel usa apenas a biblioteca padrão do Python; não precisa instalar pacotes para acompanhar os testes. Se já clonou, execute `git pull --ff-only` na pasta antes de iniciar.

O estado compartilhado fica em `lab/data/execution.json`. Para levar alterações posteriores, faça commit/push desse arquivo ou use Exportar backup e Importar na interface. Evite editar o mesmo acompanhamento simultaneamente em duas máquinas.

A chave de API não acompanha o Git. Configure o `.env` local somente quando for executar chamadas; o painel funciona sem credenciais. Para regenerar o PDF, instale ReportLab (`python -m pip install reportlab`).
