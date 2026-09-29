# Jev Flow — ficha de referência

**Repositório:** [igormorais123/jev-flow](https://github.com/igormorais123/jev-flow) (fork de [daltonrpj/jev-flow](https://github.com/daltonrpj/jev-flow))  
**Revisão examinada:** [`75e63491f63691418251534f50e8c8ddca9a5fc0`](https://github.com/igormorais123/jev-flow/tree/75e63491f63691418251534f50e8c8ddca9a5fc0) · commit de 24/09/2026  
**Cópia local:** `research/sources/jev-flow/` (ignorada pelo Git)  
**Licença:** MIT (`LICENSE`) · **Runtime:** Node.js 20+ · **Estado desta ficha:** inspeção do código e testes offline; sem chamada a provedor.

## O que é

Aplicação independente para desenhar, validar, simular e executar fluxos com perguntas tipadas ao Jev. O Studio (`/jev/flows`) edita os fluxos e mostra o caminho executado; o Compendium (`/jev/flows/compendium`) gera configurações sob demanda; Battle Arena, simulação de carrinho e Labs são superfícies de comparação e ensino. A aplicação roda em um servidor Node local; o guia estático para Pages não executa seus fluxos.

O mecanismo separa entrada, julgamento tipado (`Choice`, `Noul`, `Score`), validação da resposta, regras de roteamento e efeitos. O código em [`engine.mjs`](https://github.com/igormorais123/jev-flow/blob/75e63491f63691418251534f50e8c8ddca9a5fc0/services/jev-flow/engine.mjs) impõe limites de nós, passos, chamadas e tokens; verifica o fluxo antes de rodar e exige `budget.guard` e aprovação explícita de `jev.verify` antes de `action.webhook`. O catálogo de nós e seus contratos ficam em [`node-catalog.mjs`](https://github.com/igormorais123/jev-flow/blob/75e63491f63691418251534f50e8c8ddca9a5fc0/services/jev-flow/node-catalog.mjs).

Os cinco exemplos públicos usam entradas e respostas sintéticas. A configuração real de TypeSafe é explícita; a falta de credencial deixa o provedor indisponível. Um adaptador Laya local é opcional e depende de instalação e pesos externos. Fluxos, histórico, agendamentos e regras ficam em diretório de dados do sistema, configurável por `JEVFLOW_DATA_DIR`. [Arquitetura](https://github.com/igormorais123/jev-flow/blob/75e63491f63691418251534f50e8c8ddca9a5fc0/docs/architecture.md) · [Início rápido](https://github.com/igormorais123/jev-flow/blob/75e63491f63691418251534f50e8c8ddca9a5fc0/docs/quickstart.md) · [Segurança](https://github.com/igormorais123/jev-flow/blob/75e63491f63691418251534f50e8c8ddca9a5fc0/docs/security.md).

## O que vale aproveitar no JEV

- **Separação julgamento → política → efeito:** usar as respostas tipadas como evidência, com validação e decisão final no código. É compatível com a diretriz atual do projeto.
- **Prévia determinística e trilha:** fixtures permitem conferir o roteamento sem gastar chamadas; a trilha distingue resposta fornecida, provedor local, remoto e indisponibilidade.
- **Contratos de nós e limites:** a validação de fluxos, os limites explícitos e os gates de webhook são referências concretas para futuras integrações, sem copiar o runtime inteiro.
- **Catálogo gerado e certificado:** o número de 388.080 configurações é contagem de combinações válidas e únicas do gerador, não de fluxos escritos à mão nem de avaliações de modelo. O certificado deve acompanhar a revisão do código.

## Verificação nesta revisão

- `npm ci --ignore-scripts --no-audit --no-fund`: concluído.
- `npm test`: 83 testes, 81 passaram, 2 foram pulados por falta de Playwright, 0 falhas. A suíte usa fixtures e transportes injetados; não prova qualidade de julgamento do Jev ao vivo.
- `npm run catalog:certify -- --check`: certificado conferido para 388.080 configurações, com 388.080 chaves e IDs únicos.
- Nenhuma credencial foi configurada e nenhuma chamada paga foi feita.

## Encaixe no estudo

Referência adicional posterior ao corpus fechado em 18/09/2026. Não integra as 15 fichas S01–S15, a matriz de testes nem os placares históricos. Para avaliar adoção, comparar em casos reais do JEV: tempo de montar/revisar um fluxo, clareza da trilha, manutenção dos contratos e tratamento de falhas; medir respostas do modelo separadamente, com o mesmo corpus e gabarito dos outros fluxos.
