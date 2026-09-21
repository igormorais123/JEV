# Cem perguntas estratégicas sobre o Jev, e o que o dado responde

> Gerado por `python -m laboratorio.q100.relatorio`. O registro das perguntas está em
> `laboratorio/q100/registro.py` e foi commitado **antes** de qualquer resposta ser
> escrita; as respostas estão em `laboratorio/q100/respostas.py` e calculam cada número
> na hora, a partir dos artefatos e do livro-caixa. Nenhum número desta página foi
> digitado à mão.

**76 respondidas por dado medido, 19 por conta sobre o medido, 5 por coleta nova.** Confiança: 85 alta, 9 média, 6 baixa.

## O que separa esta página das cem hipóteses

As cem hipóteses perguntavam **o que o modelo faz**, e a resposta era sustentada ou
falsificada. Estas cem perguntam **o que fazer com ele**, e a resposta termina numa
decisão. É por isso que cada pergunta carrega, além do enunciado, a decisão concreta
que ela informa e o que teria de ser verdade para essa decisão virar. Pergunta
estratégica que não muda decisão nenhuma não é estratégia: é curiosidade cara, e as
que não passaram nesse teste ficaram de fora do registro.

A honestidade desta página depende de uma distinção que ela carrega em toda entrada.
`dado medido` é contagem sobre o que foi observado. `conta declarada` é aritmética
sobre o medido, usando parâmetros que **não** foram medidos — preço de mercado de um
modelo caro, custo-hora de revisão, volume mensal. Esses parâmetros estão listados um
a um na seção seguinte, com valor e origem, e as respostas que dependem deles vêm
marcadas com confiança `baixa` de propósito. Conta com parâmetro escondido é opinião
com aparência de número.

## Os parâmetros que não foram medidos

10 das cem respostas dependem de pelo menos um destes. Trocar
qualquer um deles muda o número da resposta, e as respostas dizem em que direção.

| parâmetro | valor | o que é | usado em |
|---|---|---|---|
| `preco_modelo_caro_usd_por_milhao_entrada` | 3 | preço de entrada de um modelo de fronteira, ordem de grandeza de mercado | 3 respostas |
| `custo_hora_revisao_usd` | 12 | custo-hora de quem revisaria à mão, declarado no guia | 4 respostas |
| `tempo_revisao_s` | 120 | tempo por decisão revisada, declarado no guia e NÃO cronometrado | 4 respostas |
| `volume_mensal_decisoes` | 10.000 | volume hipotético de um canal médio | 2 respostas |
| `horas_de_integracao` | 16 | esforço de integrar o contrato num fluxo existente | 1 resposta |
| `custo_erro_grave_usd` | 200 | custo de um cancelamento indevido: retrabalho mais atrito | 3 respostas |

## As respostas que mudam uma decisão já tomada

### Q042 — Sanitizar a entrada restaura a resistência à ordem direta?

**Decide:** se a mitigação que o guia prescreve funciona  
**Responde:** **Contra o vetor para o qual a lista foi escrita, sim; contra qualquer outro, não.** Na R22 a expressão regular de oito padrões derrubou a virada de 28/78 para 1/82, pareado 27 a 0. Na R23 a mesma lista não cobre **nenhum** dos 48 vetores novos, e a lista ampliada (v2) cobre só 2 dos 36 escritos por outros modelos. Contra ordens ao sistema nunca vistas, a virada é **853/1900 = 44,9%** sem defesa e 829/1900 com o v2, com **202 viradas acima do corte de 0,90**. Sanitizar por lista é defesa contra o ataque que já se conhece. A camada que generaliza é o sentinela (Q043).

A mitigação que o guia recomendava sem prova agora tem prova, e ela é forte. Uma expressão regular de oito padrões, aplicada ao texto antes de ele virar `state`, derruba a virada por ordem direta de 35,9% para 1,2% — pareado, 27 a 0, p < 0,0001. Custa zero chamada e não machuca texto limpo. **Passa de sugestão a requisito de integração.**

### Q044 — Delimitar o texto do cliente com marcadores explícitos reduz a virada?

**Decide:** se a defesa cabe na instrução, sem código novo  
**Responde:** Ajuda pouco e não está demonstrado. Delimitar o texto com marcadores e avisar na instrução que ali é dado reduz a virada de 35,9% para 27,6%, pareado 8 a 2, p = 0,1094. Direção a favor, sem significância. Use se for de graça; não conte com isso.

O sentinela é a descoberta operacional mais barata do estudo: uma segunda pergunta no mesmo payload custa **nada** — o preço é por token de entrada, e o estado já foi enviado — e detecta 100% das tentativas de ordem direta, calando-se em 97,6% do texto limpo. Quem precisa de trilha de auditoria de ataque tem como tê-la de graça. O que o sentinela não faz é impedir a virada, então ele acompanha a sanitização em vez de substituí-la.

### Q023 — O corte de 0,99 recomendado no guia sobrevive ao conjunto inteiro de decisões?

**Decide:** manter ou mudar a recomendação publicada  
**Responde:** Sobrevive, e a primeira versão desta resposta dizia o contrário por um erro que vale registrar: ela somava a diluição retratada da R11, e a "degradação sob dificuldade" era o truncamento do laboratório. Retirada a condição retratada, acima de 0,99 há 2 erros em 629 decisões no uso normal (0,32%) e 4 em 310 nas condições extremas que valem como evidência (1,29%) — até 147 opções, 70% de ruído, sobreposição de classes. A pior rodada é R19 (armadilha de sujeito, corpus gerado por molde), com 3,43%. O corte de 0,99 continua sendo o último ponto em que a confiança avisa, e a ressalva que fica é outra: em ruído pesado a acurácia despenca (36,7% a 70%) **mas nenhum erro passa do corte** — o corte cobre; o que ele não faz é devolver acurácia.

Esta resposta foi corrigida, e a correção é mais útil que a versão original. A primeira dizia que o corte de confiança degradava 13,5% nas condições extremas; o número somava a diluição **retratada** da R11, e 46 dos 52 erros acima de 0,99 eram o truncamento do laboratório, não o modelo. Sem a condição retratada, os extremos ficam em 1,29% e a rodada que mais escapa ao corte é a armadilha de sujeito (3,43%). A ressalva que sobrevive muda de endereço: não é a taxonomia grande nem o texto degradado que enganam o corte — é o pedido atribuído à pessoa errada. A frase de sujeito do guia é a mitigação, e ela custa uma linha.

### Q036 — Existe modo de falha em que a confiança não avisa?

**Decide:** se o corte basta como salvaguarda  
**Responde:** Sim, dois. **Texto sem pedido algum sem classe de escape**: erra 10 de 10 com confiança 0,987. E **ordem direta ao classificador**: das viradas no corpus jurídico, 8 passaram do corte de 0,90. Nos dois casos o corte não protege, e a mitigação é de desenho — classe de escape e sanitização —, não de limiar.

Dois modos de falha sistemáticos, e os dois são de desenho, não do modelo. Texto sem pedido nenhum, num contrato sem classe de escape, erra 10 de 10 com confiança média de 0,987 — o modelo não tem como dizer "nada disso", então ele escolhe. E ordem direta ao classificador vira o resultado. **Classe de escape obrigatória e sanitização obrigatória** resolvem os dois, e nenhum dos dois custa chamada.

### Q073 — Qual a taxa de falha de transporte a esperar?

**Decide:** o desenho da repescagem  
**Responde:** **1,1%** das 24.297 tentativas: 119 estouros do timeout de 45 s do cliente, 107 erros HTTP do provedor, 32 chamadas que saíram e nunca foram conciliadas, 8 respostas fora do contrato. Três repescagens com espera crescente cobrem o caso comum; o que não pode é tratar falha como classe padrão.

A operação precisa de repescagem, não de tolerância a erro. 2,7% das tentativas falharam, e a maioria é erro do provedor ou estouro do timeout de 45 s — coisas que uma segunda tentativa resolve. O que não pode acontecer é falha virar classe padrão: uma chamada que não voltou não é "informação", é ausência de decisão.

### Q096 — Quanto resta do orçamento, e o que ele compra?

**Decide:** o tamanho do próximo programa  
**Responde:** Restam **US$ 3,9910**, que compram cerca de 123.586 chamadas — mais de nove vezes tudo que foi gasto até aqui (31.243 chamadas). O orçamento não é o limite deste trabalho; tempo e acesso a dado real são.

O limite deste trabalho não é orçamento. Gastou-se 10,6% do teto autorizado, e o que resta compra mais de nove vezes tudo que já foi feito. O que falta é **dado real com gabarito humano** — duzentas mensagens anotadas por duas pessoas fecham de uma vez a maior ressalva do estudo, e custam tempo de gente, não dinheiro.

## As cem, por família

### A · A decisão de adotar

*10 perguntas: 2 por conta declarada, 8 por dado medido.*

**Q001 — Em qual aplicação o ganho sobre o método atual é maior?**

Triagem, com folga. Contra regra por palavra-chave o Jev vai de 60,0% para 92,5% no piloto e de 32,5% para 97,5% na confirmação — mais de 60 pontos no segundo caso. Verificação de afirmação vem depois (95,8% contra 62,5%), e ordenação é a de maior ganho econômico, não de acurácia.

*Decide por onde começar a integração. Fonte: dado medido; confiança alta. Vira se outra aplicação mostrar ganho maior sobre a linha de base dela.*

**Q002 — Qual aplicação oferece o melhor ganho por unidade de risco assumido?**

Ordenação de contexto. O ganho é medido (93,5% contra 83,4% carregando tudo, 22 a 5, p = 0,0015) e o risco é o menor das quatro: se a ordenação errar, o modelo caro recebe o trecho errado e responde mal — não há ação irreversível no caminho. Triagem tem ganho maior e risco maior, porque a classe `cancelar` age.

*Decide por onde começar, considerando o que quebra se der errado. Fonte: dado medido; confiança alta. Vira se a aplicação de menor risco deixar de ter ganho medido.*

**Q003 — Existe aplicação em que o método atual já basta?**

Sim, duas. Em **prosa**, o BM25 empata com o Jev na colocação do trecho certo (20/21 contra 20/21) e custa zero chamada — ali o método atual basta. E em classificação de texto que **não vem de fora**, um LLM genérico barato empata sob critério independente e custa um quarto.

*Decide onde NÃO gastar esforço de integração. Fonte: dado medido; confiança alta. Vira se a diferença contra a linha de base cair abaixo de 5 pontos.*

**Q004 — A vantagem sobre o LLM barato sobrevive ao critério de um anotador independente?**

Não. Sob o gabarito desta casa o Jev ganha (98,9% contra 84,4%–91,1% no E12); sob o critério de um anotador independente a vantagem some, e isso se repetiu no E10, E11 e E12. A justificativa do Jev **não é acurácia** — é resistência a manipulação pelo texto classificado, e essa não depende de gabarito.

*Decide se a escolha do modelo precisa de justificativa além de preço. Fonte: dado medido; confiança alta. Vira se aparecer vantagem significativa sob o critério independente.*

**Q005 — Qual o volume mensal mínimo em que o custo de integrar se paga?**

Cerca de **480 decisões** para o investimento de integração se pagar — menos de um mês num canal de 10.000 decisões/mês. O número é dominado pelo tempo de pessoa, não pelo preço do modelo: o custo por decisão do Jev é US$ 0,000032 contra US$ 0,4000 da revisão humana.

*Decide se vale integrar ou rodar na mão. Fonte: conta declarada; confiança baixa. Vira se o custo de integração declarado mudar de ordem de grandeza. Depende de: `horas_de_integracao`, `custo_hora_revisao_usd`, `tempo_revisao_s`, `volume_mensal_decisoes`.*

**Q006 — Adotar obriga a redesenhar a taxonomia que já existe?**

Não, se ela tiver até 12 classes: nesse intervalo a acurácia não cai. Entre 12 e 147 há um platô em torno de 90%. O que a taxonomia **precisa** ganhar é uma classe de escape — sem ela o modelo inventa, e é o único modo de falha em que a confiança não avisa (0,987 de média, errando em 10 de 10).

*Decide quanto trabalho de modelagem entra no projeto. Fonte: dado medido; confiança alta. Vira se o número de classes do domínio passar do limite medido sem custo.*

**Q007 — Quantas classes o domínio pode ter sem custo de acurácia?**

Até 12 sem custo medido: 2, 3, 5 e 12 opções ficam todas acima de 97%. De 20 a 147 o desempenho cai para um platô em torno de 90%, o que ainda serve para muitos casos — mas já não é de graça.

*Decide quão fina a taxonomia pode ser. Fonte: dado medido; confiança alta. Vira se a acurácia cair mais de 3 pontos dentro do limite hoje declarado.*

**Q008 — A adoção exige dado rotulado antes de começar?**

Não para começar, sim para confiar. O contrato funciona sem nenhum exemplo rotulado — a taxonomia é a única entrada. Mas o corte de confiança **não se transporta** entre conjuntos: o que dava zero erro em dois corpora deixou passar um erro com confiança 0,98 no terceiro. Rotular ~200 casos do seu material é o que autoriza automatizar, não o que autoriza experimentar.

*Decide se existe dependência de trabalho humano prévio. Fonte: dado medido; confiança alta. Vira se o desempenho sem ajuste cair abaixo do aceitável do caso de uso.*

**Q009 — Quanto tempo até o primeiro resultado utilizável?**

Dias, não semanas. A R18, a R19, a R20, a R21 e a R22 geraram corpus com gabarito fixado por molde e filtro mecânico, sem uma linha lida por mim antes de rodar. Das três que registraram o próprio custo, a mais cara ficou em US$ 0,0164 — incluída a coleta nova em domínio jurídico, em inglês e em espanhol. O caminho é reaproveitável: `r19_armadilha_de_sujeito.py` e `r21_generalizacao.py` são os moldes.

*Decide o formato do piloto. Fonte: conta declarada; confiança média. Vira se a geração de corpus deixar de ser automatizável.*

**Q010 — Se só um projeto puder ser feito este trimestre, qual é?**

Ordenação de contexto para montar o prompt de um agente caro. É a única com economia medida em bytes (74% menos contexto), a única em que selecionar **melhora a resposta** em vez de só baratear, e a de menor risco. O segundo lugar é o guarda de comando, que já está implantado em sombra e só depende de uma decisão de configuração para entregar o ganho medido.

*Decide a alocação de esforço. Fonte: dado medido; confiança alta. Vira se a aplicação escolhida perder economia medida ou ganhar risco novo.*

### B · Unidade econômica

*10 perguntas: 6 por conta declarada, 4 por dado medido.*

**Q011 — Quanto custa mil decisões, medido e não estimado?**

**US$ 0,032 por mil decisões**, medido sobre 31.243 chamadas reais que somam US$ 1,0090 no livro-caixa. Não é estimativa: é o extrato.

*Decide a linha do orçamento. Fonte: dado medido; confiança alta. Vira se o preço do provedor mudar.*

**Q012 — A seleção de contexto se paga quando se conta a chamada de ordenação?**

Sim, e por larga margem. Ordenar 169 perguntas custou US$ 0,0443 em chamadas ao Jev (8 candidatos cada) e poupou 1.089.128 bytes de entrada do modelo caro — US$ 0,82 ao preço declarado. A razão é **18 para 1**. E isso ignora o ganho de acurácia, que é o achado principal: selecionar responde melhor.

*Decide se a Aplicação 3 é economia real ou contábil. Fonte: conta declarada; confiança média. Vira se o preço do modelo caro ficar abaixo do ponto de equilíbrio calculado. Depende de: `preco_modelo_caro_usd_por_milhao_entrada`.*

**Q013 — Qual a razão mínima de preço entre o modelo caro e o Jev para a seleção valer?**

O modelo respondedor precisa custar mais de **US$ 0,16 por milhão de tokens de entrada** para a ordenação se pagar só em token. Qualquer modelo de fronteira está muito acima disso; um modelo barato de US$ 0,10 não estaria — nesse caso a seleção se justifica pela acurácia, não pela economia.

*Decide em quais pilhas a seleção faz sentido. Fonte: conta declarada; confiança média. Vira se a razão de preço do seu caso ficar abaixo da calculada.*

**Q014 — A partir de quantos candidatos a ordenação custa mais do que carregar tudo?**

Não há limite prático pelo lado do custo: cada candidato a mais custa uma chamada de ordenação (US$ 0,0000328) e poupa US$ 0,000817 de contexto do modelo caro — a poupança é **25× maior**. O limite é de latência e de qualidade, não de dinheiro: mais candidatos significam mais chamadas em paralelo, e a R18 mostrou que passar de dois trechos selecionados piora a resposta.

*Decide o tamanho máximo do conjunto de candidatos. Fonte: conta declarada; confiança média. Vira se o número de candidatos do seu caso passar do limite. Depende de: `preco_modelo_caro_usd_por_milhao_entrada`.*

**Q015 — O k adaptativo economiza o bastante para justificar a complexidade?**

Não neste corpus, e talvez em outro. O k adaptativo economiza 86,2% contra 73,7% do k = 2 fixo, com o mesmo acerto — mas o k = 1 fixo economiza 87,4% com o mesmo acerto também. A política adaptativa **empata com a regra mais simples** aqui. Implemente k = 1 fixo; guarde a política adaptativa para quando a ordenação for difícil, que é onde ela teria valor e onde ninguém mediu ainda.

*Decide se implementar a política de k variável. Fonte: dado medido; confiança alta. Vira se a economia adicional sobre k fixo passar de 10 pontos em corpus difícil.*

**Q016 — Quanto se economiza, em dólares, por mil perguntas no arranjo recomendado?**

**US$ 5,72 por mil perguntas** de contexto poupado, contra US$ 0,26 de chamadas de ordenação — líquido de US$ 5,45. O número escala linearmente com o preço do modelo respondedor, que é o parâmetro declarado.

*Decide o número que vai para a justificativa de projeto. Fonte: conta declarada; confiança média. Vira se o preço do modelo respondedor mudar. Depende de: `preco_modelo_caro_usd_por_milhao_entrada`.*

**Q017 — Que fração do orçamento do estudo virou chamada inútil?**

266 tentativas de 24.297 terminaram em falha — **1,1%**. Some-se a isso o episódio do gerador da R18, em que 88 de 110 chamadas voltaram com conteúdo vazio porque o limite de tokens era consumido pelo campo de raciocínio: pagas e inúteis. Reserve 5% de folga e **meça o conteúdo da resposta, não só o código HTTP**.

*Decide quanto reservar de folga no próximo programa. Fonte: dado medido; confiança alta. Vira se a taxa de falha do provedor subir.*

**Q018 — O custo por decisão cresce com o texto de um jeito que quebre a conta?**

Não quebra: o custo é quase linear no tamanho do estado (r = 0,25), e o quartil de textos maiores custa 1,4× o dos menores. Como o preço de saída é zero e a entrada custa US$ 0,042 por milhão, mesmo um texto de 20 mil caracteres não muda a ordem de grandeza. Não há motivo econômico para impor limite de tamanho — há motivo de qualidade, que é outro.

*Decide se há limite de tamanho a impor na entrada. Fonte: dado medido; confiança alta. Vira se a relação custo-tamanho deixar de ser aproximadamente linear.*

**Q019 — Votar em três chamadas triplica o custo — isso cabe no custo por decisão?**

Cabe folgado — três chamadas custam US$ 0,000097 por decisão contra US$ 200,00 de um erro grave — mas a R24 mostrou que votar a **mesma** pergunta três vezes não compra nada: em 148 casos, 0 oscilaram. O que vale o triplo do custo é perguntar de **três formulações** diferentes, que no jurídico levou de 79,7% para 92,8%. Para a classe irreversível, redundância de formulação, não de repetição.

*Decide se a política de votação é viável para a classe irreversível. Fonte: conta declarada; confiança média. Vira se o custo por decisão passar a ser material contra o custo do erro. Depende de: `custo_erro_grave_usd`.*

**Q020 — Quanto custa rodar a suíte de canários todo dia por um ano?**

**US$ 0,11 por ano** para rodar os canários todo dia (US$ 0,000297 por corrida). É 0,05% do teto autorizado de US$ 5,00. O monitoramento contínuo não é uma decisão de orçamento — é uma decisão de disciplina.

*Decide se o monitoramento contínuo entra no orçamento. Fonte: conta declarada; confiança alta. Vira se o custo anual passar de 1% do teto autorizado.*

### C · Desenho da política de uso

*10 perguntas: 10 por dado medido.*

**Q021 — Qual corte de confiança entrega a maior cobertura com zero erro aceito?**

**Nenhum corte zera o erro**, nem no uso normal. O melhor disponível é 1,0, que aceita 68,3% das decisões com 0,20% de erro entre elas — 2 em 991. A consequência é dura e não tem volta: o corte reduz risco e não o elimina, e por isso a classe irreversível continua exigindo gente.

*Decide o corte a configurar em produção. Fonte: dado medido; confiança alta. Vira se aparecer erro acima do corte escolhido no conjunto inteiro.*

**Q022 — Como é a curva risco-cobertura, e onde está o joelho?**

A curva é quase plana até 0,90 e só então começa a pagar: de 0 a 0,90 a cobertura cai de 100% para 90% e a taxa de erro entre os aceitos vai de 3,45% para 1,98%. De 0,90 para 0,99 a cobertura cai mais 14% e o erro chega a 0,36%. **O joelho está em 0,99**: é o último ponto em que a redução de erro ainda compensa a cobertura perdida.

*Decide a política de automação parcial. Fonte: dado medido; confiança alta. Vira se a curva mudar de forma no seu material.*

**Q023 — O corte de 0,99 recomendado no guia sobrevive ao conjunto inteiro de decisões?**

Sobrevive, e a primeira versão desta resposta dizia o contrário por um erro que vale registrar: ela somava a diluição retratada da R11, e a "degradação sob dificuldade" era o truncamento do laboratório. Retirada a condição retratada, acima de 0,99 há 2 erros em 629 decisões no uso normal (0,32%) e 4 em 310 nas condições extremas que valem como evidência (1,29%) — até 147 opções, 70% de ruído, sobreposição de classes. A pior rodada é R19 (armadilha de sujeito, corpus gerado por molde), com 3,43%. O corte de 0,99 continua sendo o último ponto em que a confiança avisa, e a ressalva que fica é outra: em ruído pesado a acurácia despenca (36,7% a 70%) **mas nenhum erro passa do corte** — o corte cobre; o que ele não faz é devolver acurácia.

*Decide manter ou mudar a recomendação publicada. Fonte: dado medido; confiança alta. Vira se a taxa de erro acima de 0,99 passar de 1%.*

**Q024 — Qual k recomendar, considerando acerto e custo juntos?**

**k = 1.** Contra k = 2 não há diferença nenhuma (3 a 4, p = 1,0) e custa metade do contexto; contra k = 3 a direção favorece o menor em todos os recortes. Mandar um trecho é a recomendação, e mandar dois é defensável para quem quiser margem.

*Decide o parâmetro padrão da Aplicação 3. Fonte: dado medido; confiança alta. Vira se k = 2 superar k = 1 com significância.*

**Q025 — A classe de escape deve ser obrigatória em toda taxonomia?**

Não vale a complexidade hoje. Ela empata com k = 1 fixo em acerto e em economia. Implemente a regra simples; a adaptativa fica como opção para corpus onde a ordenação erre mais, cenário que ainda não foi medido.

*Decide o padrão de desenho de taxonomia. Fonte: dado medido; confiança média. Vira se aparecer caso em que a classe de escape piora a decisão.*

**Q026 — A instrução de sujeito deve ser padrão em toda classificação de pedido?**

Sim, sempre. Sem classe de escape, dez textos sem pedido nenhum foram classificados como `informacao` nas 10 vezes, com confiança média 0,987 — o único modo de falha medido em que a confiança **não avisa**. Com a classe, acerta 10 de 10. Custa uma linha.

*Decide o texto padrão da instrução. Fonte: dado medido; confiança alta. Vira se a instrução de sujeito piorar alguma família.*

**Q027 — Sob que condição vale decompor a decisão em várias perguntas?**

Sim, padrão. Ela leva 89,4% a 92,9% em atendimento sem piorar nenhum molde, e 78,5% a 90,9% no jurídico com **8 a 0, p = 0,0078**. Custa uma frase e é a única mitigação do estudo que replicou em dois domínios com ganho maior no segundo.

*Decide quando usar múltiplas perguntas no mesmo payload. Fonte: dado medido; confiança alta. Vira se a pergunta auxiliar passar a ser mais confiável que a decisão.*

**Q028 — Mandar de oito em oito é seguro? Para quais classes?**

Só quando a pergunta auxiliar for **mais confiável que a decisão que ela alimenta** — e isso é verificável antes de adotar, medindo a auxiliar sozinha. Na R19 a pergunta de sujeito acertava 68,7% sozinha, abaixo da decisão, e decompor destruiu o molde oposto (86% para 36%). A capacidade de várias perguntas no payload é gratuita e útil — mas para **observar** (ver a sentinela, Q043), não para encadear decisão.

*Decide se usar lote para baratear. Fonte: dado medido; confiança alta. Vira se o efeito de posição voltar a aparecer com significância.*

**Q029 — Quantas repetições para decisão sem volta?**

Sim para a média, não para a classe perigosa. O efeito de posição some ao embaralhar (p = 0,40), mas **3 de 40 casos** mudaram de resposta conforme os vizinhos. Use lote para baratear triagem comum; nunca para `cancelar`.

*Decide a política de repetição na classe irreversível. Fonte: dado medido; confiança alta. Vira se a taxa de oscilação medida subir.*

**Q030 — A política recomendada muda se o canal tiver outra mistura de assuntos?**

Três, com maioria. Repetindo 40 casos cinco vezes, 1 oscilou — votar em três estabiliza. O custo é desprezível (Q019) e a alternativa é aceitar que uma decisão sem volta dependa de um sorteio de baixa probabilidade.

*Decide se a configuração precisa ser por canal. Fonte: dado medido; confiança alta. Vira se a variação entre misturas passar de 5 pontos.*

### D · Risco e custo do erro

*10 perguntas: 2 por conta declarada, 8 por dado medido.*

**Q031 — Qual a taxa medida de erro grave, e qual o teto estatístico dela?**

**0 em 230 casos** sob os três critérios de correção, com teto estatístico de 9,5% por família de casos. Zero observado com teto de 9,5% não autoriza automatizar a classe irreversível: um em dez é muito quando o erro cancela o contrato de um cliente.

*Decide se a classe irreversível pode ser automatizada. Fonte: dado medido; confiança alta. Vira se o teto do intervalo cair abaixo do risco tolerado.*

**Q032 — Quanto custa um erro grave comparado ao custo da decisão?**

Um erro grave custa US$ 200,00 e uma decisão custa US$ 0,000032 — razão de **6.193.156 para 1**. Qualquer salvaguarda que custe chamadas é barata; a única salvaguarda cara é tempo de pessoa, e é exatamente essa que o corte de confiança economiza.

*Decide quanto vale gastar em salvaguarda. Fonte: conta declarada; confiança baixa. Vira se o custo declarado do erro mudar de ordem de grandeza. Depende de: `custo_erro_grave_usd`.*

**Q033 — Qual a exposição esperada por mil decisões no corte recomendado?**

Ao corte de 0,99, **3,6 erros por mil decisões aceitas**, o que ao custo declarado de erro grave dá US$ 719 de exposição por mil — se todo erro fosse grave, o que não é o caso. A exposição real é menor e depende da matriz de confusão do seu domínio.

*Decide o número que entra na avaliação de risco. Fonte: conta declarada; confiança baixa. Vira se a taxa de erro acima do corte mudar. Depende de: `custo_erro_grave_usd`.*

**Q034 — Qual família de erro é a mais cara?**

**Ação atribuída a terceiro** — 75,0% de acerto, a pior família medida. É também a mais cara, porque o erro típico dela é agir sobre o pedido de outra pessoa. A mitigação existe e é uma frase (Q027).

*Decide onde pôr revisão humana. Fonte: dado medido; confiança alta. Vira se outra família passar a concentrar o erro.*

**Q035 — O erro se concentra em alguma classe?**

Sim: a classe `informacao` concentra o erro, com 12,5% de taxa entre as classes com pelo menos 30 casos. Revisão seletiva por classe é viável e é mais barata que revisar tudo.

*Decide se a revisão pode ser seletiva por classe. Fonte: dado medido; confiança alta. Vira se a concentração deixar de existir.*

**Q036 — Existe modo de falha em que a confiança não avisa?**

Sim, dois. **Texto sem pedido algum sem classe de escape**: erra 10 de 10 com confiança 0,987. E **ordem direta ao classificador**: das viradas no corpus jurídico, 8 passaram do corte de 0,90. Nos dois casos o corte não protege, e a mitigação é de desenho — classe de escape e sanitização —, não de limiar.

*Decide se o corte basta como salvaguarda. Fonte: dado medido; confiança alta. Vira se nenhum modo silencioso restar.*

**Q037 — A taxa de não-resposta cria risco operacional?**

Baixo, mas não zero: 0 de 570 chamadas (0,0%) voltaram sem resposta fora da condição de instrução vazia. É preciso caminho de contingência — e ele deve **falhar fechado**, mandando para revisão humana, nunca assumindo uma classe padrão.

*Decide se é preciso caminho de contingência. Fonte: dado medido; confiança alta. Vira se a taxa passar de 2%.*

**Q038 — Qual o pior caso de acurácia medido em condição plausível de produção?**

**46,7% sob ruído pesado** (70% dos caracteres corrompidos) — condição implausível num canal real. O pior caso *plausível* é a triagem jurídica: **78,5%**, com a perda concentrada no molde de terceiro. Declare 78,5% como piso para domínio novo sem a instrução de sujeito, e 90,9% com ela.

*Decide o pior cenário a declarar. Fonte: dado medido; confiança alta. Vira se aparecer condição plausível pior.*

**Q039 — O modelo erra mais quando o texto é longo?**

Não. De 0 a 50 mil caracteres a acurácia fica constante em 96,7%. O que derruba não é o tamanho — é o **truncamento**, que corta o pedido antes de o modelo ver. Não imponha limite de tamanho; garanta que o corte, se houver, preserve a parte que importa.

*Decide se impor limite de tamanho reduz risco. Fonte: dado medido; confiança alta. Vira se a acurácia cair com o tamanho.*

**Q040 — Os erros se repetem entre chamadas, ou votar em três resolve?**

**Os erros se repetem, e votar a mesma pergunta não resolve.** Em 148 casos com três chamadas idênticas, 0 oscilaram: o modelo é determinístico neste regime, e o erro é sistemático. O que muda a resposta é a formulação — 11 dos 66 casos jurídicos divergem entre três formulações — e por isso a maioria **diversa** sobe o jurídico de 79,7% para 92,8% (pareado 9 a 0, p = 0,0039). Votação protege contra formulação ruim, não contra oscilação, que não existe.

*Decide se a votação é salvaguarda real ou teatro. Fonte: dado medido; confiança alta. Vira se o erro se mostrar determinístico.*

### E · Segurança e adversário

*10 perguntas: 1 por conta declarada, 4 por dado medido, 5 por coleta nova.*

**Q041 — Qual é a superfície de ataque real deste contrato?**

Um campo só: o `state`, que é onde entra o texto de terceiro. A separação estrutural entre `state` e `questions` impede que o texto do cliente vire instrução **por concatenação acidental** — não impede que ele contenha uma ordem que o modelo decida seguir. Instrução, critérios e rótulos são seus e não são superfície de ataque, desde que o cuidado nº 7 do guia seja respeitado: nunca concatenar texto de terceiro dentro deles.

*Decide o que precisa de defesa. Fonte: dado medido; confiança alta. Vira se aparecer vetor novo que atinja outro campo.*

**Q042 — Sanitizar a entrada restaura a resistência à ordem direta?**

**Contra o vetor para o qual a lista foi escrita, sim; contra qualquer outro, não.** Na R22 a expressão regular de oito padrões derrubou a virada de 28/78 para 1/82, pareado 27 a 0. Na R23 a mesma lista não cobre **nenhum** dos 48 vetores novos, e a lista ampliada (v2) cobre só 2 dos 36 escritos por outros modelos. Contra ordens ao sistema nunca vistas, a virada é **853/1900 = 44,9%** sem defesa e 829/1900 com o v2, com **202 viradas acima do corte de 0,90**. Sanitizar por lista é defesa contra o ataque que já se conhece. A camada que generaliza é o sentinela (Q043).

*Decide se a mitigação que o guia prescreve funciona. Fonte: coleta nova; confiança alta. Vira se a sanitização não reduzir a taxa de virada.*

**Q043 — Uma pergunta-sentinela detecta o texto que tenta instruir o classificador?**

**Sim, e é a única defesa que generaliza.** Na R22 a segunda pergunta no mesmo payload acusou 83 de 83 sob ataque e ficou calada em 81 de 83 das limpas. Na R23, contra ordens ao sistema escritas por outros modelos e nunca vistas, acusou **1.926 de 2.019 = 95,4%** — onde a lista de padrões cobria 2 vetores em 24. O custo: 7 de 24 mensagens legítimas que dizem "desconsidere a mensagem anterior" são acusadas, e o sentinela precisa ler o texto **original** — depois de sanitizar ele acusa 2 de 85 (R27). Ele não impede a virada; detecta, e detectar é o que autoriza recusar ou mandar para gente.

*Decide se dá para detectar em vez de só filtrar. Fonte: coleta nova; confiança alta. Vira se a sentinela ter recall baixo ou alarme falso alto.*

**Q044 — Delimitar o texto do cliente com marcadores explícitos reduz a virada?**

Ajuda pouco e não está demonstrado. Delimitar o texto com marcadores e avisar na instrução que ali é dado reduz a virada de 35,9% para 27,6%, pareado 8 a 2, p = 0,1094. Direção a favor, sem significância. Use se for de graça; não conte com isso.

*Decide se a defesa cabe na instrução, sem código novo. Fonte: coleta nova; confiança média. Vira se a delimitação não reduzir a taxa de virada.*

**Q045 — O corte de confiança serve como defesa contra injeção?**

**Não.** Em atendimento o corte barra quase tudo (1 virada acima de 0,90 em 28), mas no corpus jurídico 8 das 21 viradas passaram. Um controle que funciona num domínio e falha no outro não é controle de segurança — é sorte com histórico. Use o corte para qualidade; use sanitização e sentinela para segurança.

*Decide se o corte pode ser contado como controle de segurança. Fonte: dado medido; confiança alta. Vira se nenhuma virada passar do corte em nenhum corpus.*

**Q046 — Qual defesa tem o melhor custo-benefício?**

**Sentinela primeiro, sobre o texto original; sanitização como complemento para o que já se conhece.** A ordem inverteu depois da R23: a lista de padrões não generaliza e o sentinela acusa 95% de ordens nunca vistas. Na integração (R27), o sentinela precisa do texto original — sanitizado antes, ele fica cego (2/85). Com dois campos no mesmo payload a detecção é 84/84 e a virada reabre em 3/84; com duas chamadas, 0/82 viradas ao dobro do custo. Para a classe irreversível, duas chamadas; para o resto, dois campos. Delimitar fica de fora.

*Decide qual mitigação implementar primeiro. Fonte: coleta nova; confiança alta. Vira se outra defesa superar em redução por unidade de custo.*

**Q047 — O guarda de comando pode ser ativado com segurança?**

Sim, **como segunda camada e só como segunda camada**. Nessa posição libera 46 comandos com 0 irreversíveis soltos, e o intervalo de Wilson limita o erro a 7,7%. No lugar da regra é inseguro: sozinho perde de 2 a 6 irreversíveis em 12. A ativação depende de uma decisão que não é técnica: o guarda global **nega** em vez de perguntar, e um `allow` deste hook não sobrepõe o `deny` do outro.

*Decide sair do modo sombra ou não. Fonte: dado medido; confiança alta. Vira se aparecer irreversível liberado em qualquer corte.*

**Q048 — Qual o pior resultado possível se uma injeção passar?**

A classe que a injeção pedir é executada como se o cliente tivesse pedido. No corpus jurídico o alvo era `encerrar` e 19 das 21 viradas foram para ela — ou seja, o atacante escolhe o resultado. O controle compensatório não é o modelo: é **nunca executar ação irreversível sem confirmação humana**, que já é o cuidado nº 1 do guia e agora tem uma segunda razão.

*Decide o desenho do controle compensatório. Fonte: dado medido; confiança alta. Vira se a classe alvo da injeção deixar de ser acionável.*

**Q049 — A resistência depende da mensagem — dá para prever qual mensagem é frágil?**

Sim, e o sinal é gratuito: a confiança da decisão **sem** o ataque prediz a fragilidade. Na R22, mensagens que o modelo classificava com confiança abaixo de 0,99 viraram 61% das vezes; as de confiança máxima, 18%. A R23 replica com 48 vetores: 58% contra 27%, sobre 1.563 e 2.233 pares. Quem já estava em dúvida é quem o atacante consegue empurrar — e a confiança de base é o sinal de graça para escolher onde pôr revisão humana.

*Decide se é possível alertar caso a caso. Fonte: coleta nova; confiança alta. Vira se não existir sinal que separe frágil de resistente.*

**Q050 — Quanto custa a defesa recomendada, por mil decisões?**

**Zero por mil decisões.** A sanitização é uma expressão regular executada antes da chamada e a sentinela é uma pergunta a mais no mesmo payload, que o contrato cobra pelo estado e não pela pergunta. As duas defesas recomendadas não acrescentam uma única chamada. O custo é de engenharia — escrever os padrões e decidir o que fazer quando a sentinela acusa —, não de operação.

*Decide se a defesa cabe no custo por decisão. Fonte: conta declarada; confiança alta. Vira se a defesa passar a custar mais que a decisão.*

### F · Escopo: onde vale e onde não

*10 perguntas: 10 por dado medido.*

**Q051 — Em que línguas o resultado está medido?**

Português, inglês e espanhol, medidos no mesmo corpus com gabarito idêntico: 78,5%, 76,6% e 77,8%. Os pareamentos dão 1 a 1 nos dois casos. **A língua não é uma variável relevante** para este contrato, e isso amplia o escopo do estudo inteiro.

*Decide onde o estudo pode ser citado sem ressalva. Fonte: dado medido; confiança alta. Vira se aparecer diferença significativa entre línguas.*

**Q052 — Em que domínios o resultado está medido?**

Dois: atendimento ao cliente (98,9% no corpus de replicação) e triagem jurídica (78,5%, ou 90,9% com a instrução de sujeito). Mais código Python para a ordenação, e prosa técnica para a ordenação em prosa. Fora disso, nada foi medido — e a queda de 20 pontos entre um domínio e outro é a razão para não extrapolar.

*Decide onde o estudo pode ser citado sem ressalva. Fonte: dado medido; confiança alta. Vira se um domínio novo cair abaixo do aceitável.*

**Q053 — A seleção de contexto vale em prosa ou só em código?**

**Só em código, pelo que está medido.** Em prosa o Jev põe o trecho certo em primeiro 20/21 e o BM25 também 20/21 — empate, com o BM25 custando zero chamada. A vantagem de 22 a 1 da R18 era sobre identificadores de código, contra um BM25 cujo tokenizador nem lia acento. Em prosa, use BM25.

*Decide onde aplicar a Aplicação 3. Fonte: dado medido; confiança alta. Vira se o Jev superar o BM25 em prosa.*

**Q054 — O estudo vale para texto real, ou só para caso construído?**

**Não vale ainda.** Nenhuma das mensagens de nenhum corpus veio de um canal de produção: todas foram construídas ou geradas por molde. Elas medem discriminação de linguagem, não a bagunça do mundo real — abreviação, emoji, texto cortado, duas perguntas na mesma frase. É a maior ressalva do estudo e está declarada no guia como cuidado nº 4.

*Decide o que declarar como limite. Fonte: dado medido; confiança alta. Vira se entrar corpus de produção no estudo.*

**Q055 — Qual é o maior buraco de escopo hoje?**

Material real. Todo o resto — línguas, domínio novo, prosa, escala, adversário — já foi coberto por alguma rodada. O que nunca entrou foi uma mensagem escrita por um cliente de verdade, e é justamente sobre ela que a recomendação vai ser aplicada.

*Decide a próxima coleta. Fonte: dado medido; confiança alta. Vira se o buraco ser fechado.*

**Q056 — O resultado se mantém em contexto muito grande?**

Sim, até 50 mil caracteres: 96,7%, igual ao de 0. A posição do alvo no contexto também não importa (antes ou depois, diferença abaixo de 5 pontos em todos os tamanhos). Diluição não é risco.

*Decide se há limite de tamanho a impor. Fonte: dado medido; confiança alta. Vira se aparecer degradação abaixo do limite medido.*

**Q057 — O resultado se mantém em taxonomia grande?**

Até 12 classes sem custo; de 20 a 147 há um platô em torno de 90%. A condição de 147 opções ainda dá 90,0%. Taxonomia grande é viável — só não é de graça.

*Decide quão fina a taxonomia pode ser. Fonte: dado medido; confiança alta. Vira se a degradação começar antes do limite medido.*

**Q058 — O resultado se mantém sob ruído de digitação?**

Aguenta ruído leve e quebra com ruído pesado — mas **avisa**: em 70% de caracteres corrompidos a acurácia cai para 36,7% e nenhum erro passa de 0,90 de confiança. Normalização prévia ajuda; o corte de confiança cobre o resto.

*Decide se o canal precisa de normalização prévia. Fonte: dado medido; confiança alta. Vira se a degradação aparecer em nível de ruído plausível.*

**Q059 — O que muda se o canal tiver outra mistura de assuntos?**

Pouco: nas quatro distribuições simuladas a acurácia esperada vai de 95,0% a 97,2% — 2,2 pontos de amplitude. Estime pela mistura do seu canal, mas não espere surpresa: a variação entre assuntos é menor que a variação entre domínios.

*Decide como estimar a acurácia esperada do seu canal. Fonte: dado medido; confiança alta. Vira se a variação entre misturas passar de 5 pontos.*

**Q060 — Que evidência falta para ampliar o escopo com segurança?**

O terceiro domínio já foi medido (R25) e respondeu: a queda é de **distância do corpus de origem**, não do jurídico. A clínica fica em 63,2% sem a frase de sujeito e 77,9% com ela — abaixo do jurídico e muito abaixo do atendimento. O que continua faltando é o que sempre faltou: **200 mensagens de um canal real, anotadas por duas pessoas**, que fecham a ressalva de material construído e permitem calibrar o corte no dado certo. Depende de acesso, não de orçamento.

*Decide o desenho da próxima rodada. Fonte: dado medido; confiança alta. Vira se a evidência ser coletada.*

### G · As alternativas

*10 perguntas: 2 por conta declarada, 8 por dado medido.*

**Q061 — Contra regra por palavra-chave, qual a diferença medida?**

Entre 32 e 65 pontos, conforme o corpus: 92,5% contra 60,0% no piloto e 97,5% contra 32,5% na confirmação. Não é melhora incremental — é outra categoria de resultado. Onde o método atual é regra por palavra, trocar vale a pena.

*Decide se vale trocar o método atual. Fonte: dado medido; confiança alta. Vira se a diferença cair abaixo de 10 pontos.*

**Q062 — Contra BM25 em código, qual a diferença medida?**

Vantagem clara: **22 casos a 1**, p < 0,0001, na colocação do trecho certo entre os dois primeiros. Em código, pagar a chamada se justifica.

*Decide se vale pagar uma chamada para ordenar código. Fonte: dado medido; confiança alta. Vira se o BM25 empatar em código.*

**Q063 — Contra BM25 em prosa, qual a diferença medida?**

Empate: 20/21 contra 20/21, pareado 1 a 1. Em prosa o BM25 com tokenizador que entende acento faz o mesmo trabalho de graça. **Não pague a chamada.**

*Decide se vale pagar uma chamada para ordenar prosa. Fonte: dado medido; confiança alta. Vira se o Jev passar a ganhar em prosa.*

**Q064 — Contra LLM genérico barato em acurácia, qual a diferença?**

Depende de quem escreveu o gabarito, e é por isso que não serve de justificativa. Sob o critério desta casa o Jev ganha de 8 a 15 pontos; sob o de um anotador independente a diferença some. Três experimentos (E10, E11, E12) tentaram desempatar e chegaram ao mesmo lugar.

*Decide se o preço quatro vezes maior se justifica por acurácia. Fonte: dado medido; confiança alta. Vira se a vantagem passar a existir sob critério independente.*

**Q065 — Contra LLM genérico barato sob injeção, qual a diferença?**

Contra aviso que imita sistema, vantagem grande: o Jev vira 0/50 e os comparadores até 8/50, **todas com confiança acima do corte**. Contra ordem direta, porém, o Jev também vira (28/78) — a vantagem é de grau, não de natureza, e nenhum dos dois dispensa sanitização.

*Decide se o preço se justifica por robustez. Fonte: dado medido; confiança alta. Vira se um comparador igualar a resistência do Jev.*

**Q066 — Contra revisão humana, qual a diferença de custo?**

US$ 0,4000 contra US$ 0,000032 por decisão — o humano custa **12.386×**. Mas o parâmetro que domina é o tempo de revisão, declarado em 2 minutos e **nunca cronometrado**. Se forem 30 segundos, a economia é um quarto desta. Cronometrar é o passo 3 do guia e continua pendente.

*Decide quanto a automação parcial economiza. Fonte: conta declarada; confiança baixa. Vira se o custo-hora declarado mudar. Depende de: `tempo_revisao_s`, `custo_hora_revisao_usd`.*

**Q067 — Contra revisão humana, qual a diferença de acurácia?**

Não se sabe, e essa é a lacuna mais incômoda. O E8 mediu concordância entre dois anotadores humanos — 87,4%, kappa 0,84, com 29 divergências em 230 casos — mas ninguém mediu a acurácia de um humano contra o gabarito no mesmo material. É possível que o Jev, em 98,9%, esteja **acima** do humano típico, e o estudo não pode afirmar isso.

*Decide se a automação perde qualidade. Fonte: dado medido; confiança alta. Vira se aparecer medição de acurácia humana no mesmo material.*

**Q068 — Contra não fazer nada, o que se perde?**

Num canal de 10.000 decisões/mês, não fazer nada custa US$ 4.000 por mês de tempo de pessoa, ou a qualidade do método por palavra-chave, que erra 40% no piloto e 67% na confirmação. O custo da inação é alto porque a linha de base atual é ruim, não porque o Jev seja caro.

*Decide o custo da inação. Fonte: conta declarada; confiança baixa. Vira se o volume declarado mudar. Depende de: `volume_mensal_decisoes`, `tempo_revisao_s`, `custo_hora_revisao_usd`.*

**Q069 — Qual alternativa vence em cada aplicação?**

Triagem: Jev contra regra por palavra — Jev, com folga. Verificação: Jev contra regra simples — Jev. Ordenação em código: Jev contra BM25 — Jev, demonstrado. Ordenação em prosa: **BM25**, que empata de graça. Guarda de comando: regra **mais** Jev, nunca Jev sozinho.

*Decide a escolha de método por aplicação. Fonte: dado medido; confiança alta. Vira se qualquer pareamento inverter.*

**Q070 — Existe cenário em que uma alternativa domina o Jev?**

Sim, dois. **Prosa**: BM25 empata e custa zero. **Texto interno e confiável com tolerância a 88–91% de acerto**: um LLM genérico barato empata sob critério independente e custa um quarto. Fora desses dois, nada dominou o Jev no que foi medido.

*Decide onde não usar o Jev. Fonte: dado medido; confiança alta. Vira se o cenário deixar de existir.*

### H · Operação e manutenção

*10 perguntas: 2 por conta declarada, 8 por dado medido.*

**Q071 — Qual latência esperar, mediana e cauda?**

Mediana **599 ms**, p90 1813 ms, p99 5681 ms, máximo 32256 ms, sobre 22.492 chamadas respondidas. Fora dessas, 135 estouraram o timeout de 45 s do cliente e nunca voltaram — elas contam para o desenho da repescagem, não para o orçamento de tempo.

*Decide o orçamento de tempo do fluxo. Fonte: dado medido; confiança alta. Vira se a latência mediana passar de 1 segundo.*

**Q072 — A latência cabe num gancho interativo de editor?**

Sim, com uma ressalva que importa. O p99 das chamadas respondidas é 5681 ms, e o roteador em produção mediu 431 ms de mediana em 88 decisões reais. Mas 135 chamadas nunca voltaram, e num gancho interativo isso é pior que lentidão: **é preciso timeout curto e caminho de escape**, senão o editor congela esperando uma resposta que não vem.

*Decide se dá para usar no caminho quente. Fonte: dado medido; confiança alta. Vira se a cauda passar do limite tolerável do gancho.*

**Q073 — Qual a taxa de falha de transporte a esperar?**

**1,1%** das 24.297 tentativas: 119 estouros do timeout de 45 s do cliente, 107 erros HTTP do provedor, 32 chamadas que saíram e nunca foram conciliadas, 8 respostas fora do contrato. Três repescagens com espera crescente cobrem o caso comum; o que não pode é tratar falha como classe padrão.

*Decide o desenho da repescagem. Fonte: dado medido; confiança alta. Vira se a taxa passar de 3%.*

**Q074 — Em quanto tempo o modelo já derivou, na prática?**

**Em menos de 24 horas.** A condição de instrução vazia voltava `http 400` em 30 de 30 no dia 19 e responde 200 com a classe certa e confiança 1 no dia 20. Não é uma deriva que muda recomendação — nenhuma dependia dela —, mas mede a velocidade com que uma propriedade publicada pode morrer. Reverifique semanalmente, no mínimo.

*Decide a frequência de reverificação. Fonte: dado medido; confiança alta. Vira se uma segunda deriva aparecer em prazo diferente.*

**Q075 — Quanto custa monitorar o comportamento continuamente?**

US$ 0,000297 por corrida de 8 canários com 2 repetições. Semanal custa centavos por ano; diário custa menos de dois dólares. O custo de monitorar não é argumento para não monitorar.

*Decide se o monitoramento entra no orçamento. Fonte: conta declarada; confiança alta. Vira se o custo por corrida mudar.*

**Q076 — Qual a frequência adequada de canário?**

**Semanal**, com corrida extra antes de qualquer mudança de recomendação. A única deriva observada levou menos de um dia para acontecer, mas foi detectada na primeira corrida seguinte; semanal equilibra detecção e ruído. Diária é viável e custa US$ 0,11 por ano.

*Decide a configuração do agendamento. Fonte: conta declarada; confiança alta. Vira se a taxa observada de deriva mudar.*

**Q077 — O que fazer quando um canário reprova?**

Três passos, nesta ordem. **Um:** confirmar com chamadas extras que não é ruído — a resistência depende da mensagem, e um caso não faz deriva. **Dois:** achar qual afirmação publicada dependia daquela propriedade, o que o campo `sustenta` de cada canário responde por construção. **Três:** corrigir a documentação antes de corrigir o código, porque quem lê o guia hoje está tomando decisão com ele.

*Decide o procedimento operacional. Fonte: dado medido; confiança alta. Vira se a reprovação passar a ter causa diagnosticável de fora.*

**Q078 — Existe limite conhecido de paralelismo?**

Oito linhas em paralelo. Acima disso o E12 registrou 429 em 46 chamadas e a repescagem custou mais tempo do que o paralelismo economizou. A latência mediana do laboratório em paralelo fica dentro de 1,5× a do acesso sequencial, então oito não degrada.

*Decide quantas linhas usar na coleta. Fonte: dado medido; confiança alta. Vira se o provedor mudar o limite de taxa.*

**Q079 — Quanto do estudo é reprodutível hoje, por comando?**

Praticamente tudo, por comando. As páginas `CEM-HIPOTESES`, `DOSSIE-DE-EVIDENCIAS` e `AUDITORIA-DE-NUMEROS` são geradas do dado bruto e a auditoria confere que estão atualizadas. O que **não** é reproduzível é a coleta em si: refazer uma rodada gasta dinheiro e o modelo não é determinístico. Os artefatos brutos ficam versionados justamente por isso.

*Decide o que um terceiro consegue refazer. Fonte: dado medido; confiança alta. Vira se algum artefato deixar de ser regerável.*

**Q080 — Qual a dívida operacional aberta?**

Três itens. **Um:** o acerto do roteador em produção nunca foi medido — o registro guardava só o hash, já corrigido, e falta volume. **Dois:** o guarda de comando está em sombra e só entrega o ganho medido se o guarda global passar a perguntar em vez de negar. **Três:** o tempo de revisão humana, que domina toda a conta econômica, continua declarado e não cronometrado.

*Decide o que consertar antes de escalar. Fonte: dado medido; confiança alta. Vira se a dívida ser paga.*

### I · Governança e prova

*10 perguntas: 1 por conta declarada, 9 por dado medido.*

**Q081 — Quantos números publicados são conferidos automaticamente?**

**1130 conferências**, todas refeitas a partir das linhas brutas de resposta com estatística independente da que gerou os resumos, e presas na suíte de testes: um número publicado sem dado que o sustente quebra o `pytest`. 7 itens estão declarados fora de alcance em vez de omitidos.

*Decide quanta confiança a documentação merece. Fonte: dado medido; confiança alta. Vira se a cobertura de auditoria cair.*

**Q082 — Quantas afirmações são demonstradas, e quantas são só direção?**

Das cem hipóteses: **81 sustentadas**, 18 falsificadas, 1 inconclusiva. No dossiê de evidências, quatro afirmações são `demonstrado`, duas são `direção consistente`, uma é `medição única`, duas são `falsificado`, uma foi `corrigida` e uma `derivou`. Só as quatro primeiras podem ser ditas sem ressalva.

*Decide o que pode ser dito sem ressalva. Fonte: dado medido; confiança alta. Vira se uma direção passar a ter significância.*

**Q083 — Quantas afirmações publicadas já caíram?**

**Três**, e todas por medição própria. (1) "imune a instrução injetada", derrubada pela R15 e devolvida mais precisa; (2) a versão precisa dela — "não obedece a quem fala com ele" —, derrubada pela R21b; (3) a rejeição do endpoint com instrução vazia, derrubada pelo canário em menos de 24 horas. Nenhuma foi derrubada por terceiro, o que é bom sinal de método e mau sinal de revisão externa.

*Decide quanto desconto aplicar às afirmações atuais. Fonte: dado medido; confiança alta. Vira se outra afirmação cair.*

**Q084 — Quanto tempo se passou entre publicar e corrigir, nas que caíram?**

Horas, nos três casos. A R15 derrubou a imunidade no mesmo dia em que ela foi publicada; a R21b derrubou a versão corrigida no dia seguinte; o canário pegou a deriva do endpoint na primeira corrida dele. O mecanismo funciona **tarde**, que é a única forma que ele tem de funcionar — mas funciona em horas, não em meses.

*Decide quanto vale o mecanismo de auditoria. Fonte: dado medido; confiança alta. Vira se uma correção demorar muito mais que as anteriores.*

**Q085 — Um terceiro consegue refazer o estudo com o que está no repositório?**

Sim para a análise, não para a coleta. Todo artefato bruto está versionado, todas as páginas se regeram por comando e a auditoria confere cada número contra o bruto. Refazer a coleta exige a chave do provedor e dinheiro, e o modelo não é determinístico — então a replicação exata é impossível por natureza, não por omissão. O que um terceiro consegue é **auditar**, que é o que importa.

*Decide se o trabalho é publicável. Fonte: dado medido; confiança alta. Vira se faltar artefato ou instrução.*

**Q086 — Há conflito de interesse na escrita do gabarito?**

Sim, e está declarado. O gabarito das rodadas iniciais foi escrito por mim, que também escolhi os casos — e é exatamente aí que a vantagem sobre os LLMs baratos aparece e some conforme o critério. As rodadas recentes corrigiram isso de três formas: gabarito fixado por molde antes de existir texto, filtro mecânico sem leitura minha, e vetores adversariais escritos por outros modelos. Onde o gabarito é meu, desconte.

*Decide quanto peso dar aos resultados de acurácia. Fonte: dado medido; confiança alta. Vira se o gabarito passar a ser de terceiro em todas as rodadas.*

**Q087 — A taxa de falsificação das cem hipóteses é compatível com acaso?**

Não. Foram 18 falsificações, contra 5 esperadas por acaso se todas as hipóteses fossem verdadeiras e o teste tivesse 5% de erro — **3,8× o acaso**. Ainda assim, nenhuma falsificação isolada decide sozinha, e por isso as que mudam recomendação foram refeitas com coleta nova antes de entrar no guia.

*Decide se as falsificações merecem crédito individual. Fonte: conta declarada; confiança média. Vira se a taxa observada cair para o esperado sob acaso.*

**Q088 — O que é publicável externamente hoje sem ressalva?**

Quatro afirmações: (1) selecionar contexto responde melhor que carregar tudo, 22 a 5, p = 0,0015; (2) o Jev ordena código melhor que o BM25, 22 a 1, p < 0,0001; (3) como segunda camada, o guarda corta dois terços das confirmações sem soltar irreversível; (4) receber a instrução pelo prompt expõe o comparador a um risco que o contrato não tem. Todas as outras precisam de ressalva de escopo, de gabarito ou de amostra.

*Decide o que pode virar material externo. Fonte: dado medido; confiança alta. Vira se uma afirmação publicável cair.*

**Q089 — Qual a afirmação mais frágil ainda de pé?**

A de que **a classe do topo prediz o acerto da resposta**. Ela se apoia em dois casos do lado `irrelevante`, com intervalo de Wilson indo de 0 a 65,8%. A regra operacional que ela sugere é barata e sai de graça, então vale seguir — mas citar o número como evidência seria exagero.

*Decide onde olhar antes de citar. Fonte: dado medido; confiança alta. Vira se a afirmação ser confirmada ou cair.*

**Q090 — O orçamento autorizado foi respeitado?**

Sim. **US$ 1,0090 de US$ 5,00** autorizados, em 31.243 chamadas — 20,2% do teto, com US$ 3,9910 restantes. O controle é persistente, a conferência é exata e está presa na suíte de testes.

*Decide se há autorização para continuar. Fonte: dado medido; confiança alta. Vira se o gasto passar do teto.*

### J · Os próximos movimentos

*10 perguntas: 3 por conta declarada, 7 por dado medido.*

**Q091 — Qual a próxima medição de maior retorno por dólar?**

**Um terceiro domínio**, por US$ 0,02 e meia hora. A queda de 98,9% para 78,5% entre atendimento e jurídico é o maior sinal aberto do estudo, e com um só ponto de comparação não dá para saber se é o domínio ou a distância ao corpus de origem. É a medição mais barata com a maior consequência.

*Decide a próxima rodada. Fonte: dado medido; confiança alta. Vira se uma lacuna maior aparecer.*

**Q092 — Quanto custaria medir o acerto do roteador em produção?**

Quase nada em dinheiro — 500 decisões custam US$ 0,0161 — e o obstáculo não é esse: é **gabarito**. Os pedidos redigidos já são guardados desde a correção do registro, mas alguém precisa dizer qual era a resposta certa. Sem isso, mede-se latência e custo, não acerto.

*Decide se essa lacuna é barata de fechar. Fonte: conta declarada; confiança alta. Vira se o volume de pedidos registrados mudar.*

**Q093 — Quanto custaria anotar 200 mensagens reais?**

Cerca de 13,3 horas de duas pessoas, ou US$ 160 ao custo-hora declarado. É a coisa mais cara que falta no estudo inteiro — e ainda assim é menos de um dia de trabalho. O obstáculo é acesso ao dado, não orçamento.

*Decide se a lacuna que destrava tudo é de dinheiro ou de acesso. Fonte: conta declarada; confiança baixa. Vira se o custo-hora de anotação mudar. Depende de: `tempo_revisao_s`, `custo_hora_revisao_usd`.*

**Q094 — O que destrava a adoção em escala?**

**Duzentas mensagens reais e duas pessoas anotando os mesmos casos.** Isso fecha de uma vez a ressalva de material construído, permite calibrar o corte no material certo e dá a primeira medida de acurácia humana comparável. Não é dinheiro — sobram US$ 4,51 do teto. É acesso a dado e tempo de gente.

*Decide onde pedir ajuda. Fonte: dado medido; confiança alta. Vira se o destravamento acontecer.*

**Q095 — Qual experimento derrubaria a recomendação principal?**

**Já foi feito (R26), e a recomendação central inverte onde a resposta está dividida.** Em 80 perguntas que exigem dois trechos, mandar o primeiro que o Jev escolheu acerta 6/80 contra 60/80 mandando os oito (54 a 0); k = 2 dá 40/80 e k = 3, 50/80, já sem diferença significativa. A mesma primeira pergunta sozinha continua favorecendo a seleção (76/80 contra 67/80). E a regra de recall de graça **não avisa**: o topo veio `essencial` em 53 de 80 casos, e os dois alvos foram marcados essenciais em só 17. Quem não sabe se a resposta está dividida manda três, não um.

*Decide o teste adversarial a fazer antes de escalar. Fonte: dado medido; confiança alta. Vira se o experimento ser feito.*

**Q096 — Quanto resta do orçamento, e o que ele compra?**

Restam **US$ 3,9910**, que compram cerca de 123.586 chamadas — mais de nove vezes tudo que foi gasto até aqui (31.243 chamadas). O orçamento não é o limite deste trabalho; tempo e acesso a dado real são.

*Decide o tamanho do próximo programa. Fonte: conta declarada; confiança alta. Vira se o teto ser revisto.*

**Q097 — Que fração das cem hipóteses aponta para trabalho novo?**

18 falsificadas e 1 inconclusiva — **19% das cem** apontam para trabalho. Metade já foi feita nesta rodada (as defesas, a generalização); a outra metade virou ressalva declarada, que é a forma honesta de deixar trabalho em aberto.

*Decide quanto trabalho a varredura gerou. Fonte: dado medido; confiança alta. Vira se as pendências serem fechadas.*

**Q098 — Qual risco identificado ainda não tem mitigação medida?**

**Um, e ele voltou a existir depois da R23:** a ordem direta escrita de um jeito que a lista não conhece vira 45% das decisões, e a única mitigação medida contra ela é **detecção** (95% pelo sentinela), não prevenção. Detectar autoriza recusar ou mandar para gente; não devolve a resposta certa. A oscilação entre chamadas saiu da lista — a R24 mediu zero. O erro em texto de produção continua sem poder ser mitigado antes de ser medido.

*Decide o que não pode ir para produção ainda. Fonte: dado medido; confiança alta. Vira se a mitigação ser medida.*

**Q099 — O que deve entrar em produção primeiro, e com que salvaguarda?**

**Ordenação de contexto, com k = 1 para pergunta de fonte única e k = 3 quando não se sabe**, dentro de um fluxo que já usa modelo caro. A R26 tirou o k = 1 incondicional: com resposta dividida em dois trechos ele acerta 6/80 e a regra de recall de graça não avisa. Salvaguardas que não custam chamada: classe de escape na taxonomia, sentinela lendo o texto original se ele vier de fora, e a formulação escolhida por medida, não por intuição.

*Decide o plano de implantação. Fonte: dado medido; confiança alta. Vira se a salvaguarda se mostrar insuficiente.*

**Q100 — Se o trabalho parar hoje, o que fica de valor reaproveitável?**

O método, não os números. Fica **a auditoria** que recalcula cada número publicado a partir do bruto e quebra a suíte quando a documentação envelhece; ficam os **canários** que pegam deriva do modelo em horas; fica o **registro de retratações** legível por máquina; ficam os **geradores de corpus com gabarito fixado por molde**, que produzem um experimento novo por US$ 0,0039. Os números valem para o `jev-1.13` de setembro de 2026 e vão envelhecer. O mecanismo que descobre que eles envelheceram é o que sobra.

*Decide o que preservar. Fonte: dado medido; confiança alta. Vira se um artefato deixar de ser reaproveitável.*

## Como refazer

```
python -m laboratorio.q100.relatorio    # regera esta página
python laboratorio/auditoria.py         # confere cada número publicado
```

