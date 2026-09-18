# Validação local da entrega — 18/09/2026

- Auditoria offline do Anexo F: 96 decisões, 48 casos únicos, 54 chamadas. Gabarito versus predição consistente em todas as linhas; totais por tarefa conferidos por assertivas no script.
- Resultado pareado: triagem 0 mudanças; evidências 3 mudanças; afirmações 1 mudança. Seis decisões incorretas sobre cinco casos únicos. Teste nominal de McNemar sem ajuste de agrupamento, não confirmação de equivalência.
- Matriz do plano: 15 sistemas; 156 unidades heterogêneas; até 168 tentativas Jev e 18 LLM na rodada simples. Cotas planejadas somam US$ 1,70.
- Esquema SQLite carregado em memória: 11 tabelas criadas, sem executar inferências ou criar banco operacional.
- Painel verificado em Chrome com Playwright: 15 cartões, filtro de código com dois sistemas, abertura de ficha, 96 linhas históricas, filtro com seis erros, exportação CSV e simulação de cenários financeiros. Sem erros JavaScript, sem requisições HTTP externas e sem transbordamento horizontal no viewport móvel de 390 px.
- PDF renderizado com PDFium e inspecionado visualmente, incluindo tabelas, índice, passos TypeSafe e fichas. Links locais do documento/README conferidos.
- Artefatos textuais examinados para o padrão da chave OpenRouter: nenhuma ocorrência. `.env` ignorado pelo Git e ACL sem herança, restrita ao usuário local.
- Nenhuma inferência paga nesta etapa. A consulta de metadados da chave é registrada à parte e não mede saldo de créditos da conta.

Estes checks validam a entrega documental, os cálculos derivados do PDF e a interface. Não constituem testes dos 15 sistemas, não auditam o ledger original do Hermes e não implementam o controlador financeiro especificado no plano.
