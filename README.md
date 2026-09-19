# JEV

Projeto experimental para testes com o modelo de classificação JEV.

## Execução realizada

- [Relatório de execução — Helena](docs/RELATORIO-EXECUCAO-JEV-HELENA.md) — recomendação, evidência, red team e o que continua desconhecido.
- [Executor financeiro e contrato real da API](executor/README.md)
- [Pré-registro do E1](planning/preregistro-E1-triagem.md) · corpora em [triagem](data/corpus/triagem-piloto.jsonl) e [evidência](data/corpus/evidencia-piloto.jsonl)
- Resultados brutos em `runs/`: canários, sondagem de contrato, E1, E2 fatorial, E3 e a rodada simples dos 15 sistemas.

261 chamadas reais, **US$ 0,007638** de um teto de US$ 5,00 de gasto novo. A conciliação com o extrato do
provedor fecha sem divergência inexplicada. Na triagem, Jev 0,925 contra 0,600 da regra simples congelada;
na relação afirmação/evidência, 0,958 contra 0,625. Piloto com gabarito autoral provisório: não decide adoção.

## Plano de testes atual

- [Plano científico completo — Helena](docs/PLANO-CIENTIFICO-JEV-HELENA.md)
- [PDF para leitura](output/pdf/PLANO-CIENTIFICO-JEV-HELENA.pdf)
- [Painel de acompanhamento e métricas explicadas](lab/index.html) — execução, sistemas, resultados, orçamento e fontes.
- [Como usar e alimentar a interface](lab/README.md) — importação, backup e atualização conectada à pasta.
- [Matriz dos 15 sistemas](planning/matriz-testes.csv) e [plano estruturado](planning/plan.json)
- [Esquema de dados para a execução](planning/schema.sql)
- [Auditoria das tabelas do Hermes](research/hermes/auditoria-local.json)

A rodada simples cobre todos os 15 sistemas. Rodadas aprofundadas, critérios, corpus, orçamento e guia TypeSafe/OpenRouter estão no plano. Os testes dos sistemas ainda estão planejados; somente a auditoria offline do PDF foi executada. Custo novo de inferência: **US$ 0**.

O teto autorizado é de **US$ 5,00 de gasto novo**, decidido em 18/09/2026: o histórico de US$ 3,002937546 não ocupa esse limite. Os blocos planejados somam US$ 1,70, dentro do teto. O limite de US$ 50 informado pela chave continua sendo apenas uma segunda barreira do provedor, não uma autorização. O executor financeiro em `executor/` aplica o teto por reserva atômica antes de cada chamada; nenhuma chamada paga foi feita até aqui.

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
