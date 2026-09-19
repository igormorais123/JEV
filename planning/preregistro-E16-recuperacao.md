# E16 — recuperação de contexto com candidatos reais

Registrado após E15 e antes de despachar E16, 2026-09-19.

E15 usou negativos artificiais fáceis. Hipótese: o JEV também identifica o trecho
essencial quando os quatro candidatos são funções reais do mesmo repositório.
Oito perguntas, quatro candidatos por pergunta, 32 chamadas individuais, sem lote.
Gabarito fixo: função que implementa diretamente a resposta. Outras funções podem
ajudar, mas não devem ultrapassar a essencial. Algumas fontes já apareceram no E15:
não apresentar esta rodada como confirmação totalmente independente.

Comparador congelado: contagem de termos únicos compartilhados entre pergunta e
candidato, sem ajuste posterior. Não chamá-lo de BM25 nem de busca de produção.
Ordem embaralhada com semente 20260919. Ordenação Jev: essencial > complementar >
incerto > irrelevante; confiança desempata. O alvo deve estar no top-1 em >=7/8 e
no top-2 em 8/8 para liberar ordenação assistida. Não remover candidatos: devolver
ordem completa, referências e hashes para recuperar a fonte.

Registrar bytes do conjunto e do top-2 como proxy, nunca como tokens/Astra poupados.
Registrar cobertura, top-1/top-2, latência, custo e falhas sobre todos os 32 casos.
Teto conjunto E15/E16: US$ 2, dentro da carteira global. Sem retries automáticos.
O corte e as rubricas do E15 permanecem inalterados.
