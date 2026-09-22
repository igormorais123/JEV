# Dossiê de evidências — o que o estudo do Jev sustenta, e com que força

> Gerado por `python laboratorio/gerar_dossie.py`. Todo número desta página sai do JSON bruto
> na hora da geração, e `laboratorio/auditoria.py` reconfere cada um contra as linhas de resposta
> originais, com estatística independente da que produziu os resumos.

Os outros documentos respondem outras perguntas: o [guia prático](GUIA-PRATICO-JEV.md) diz **o que
fazer**, o [pré-registro](../laboratorio/PREREGISTRO.md) diz **o que foi prometido antes de medir**,
o [mapa de limites](LIMITES-DO-JEV.md) diz **onde quebra** e a
[auditoria](AUDITORIA-DE-NUMEROS.md) mostra **conferência por conferência**. Este aqui responde a
pergunta que faltava: *desta afirmação, quanto é prova?*

## Como ler

Cada afirmação recebe uma de quatro forças, e a diferença entre elas é o ponto do documento:

| força | o que significa | o que você pode fazer com ela |
|---|---|---|
| **demonstrado** | comparação pareada com p < 0,05 | decidir em cima |
| **direção consistente** | o sinal se repete e nunca se inverte, sem atingir p < 0,05 | adotar se o custo for baixo; não usar para convencer ninguém |
| **medição única** | um número observado, sem comparador ou com n pequeno demais | tratar como hipótese, e medir de novo antes de depender |
| **falsificado** | a hipótese foi testada e o dado disse não | parar de fazer, e registrar por quê |
| **corrigida** | uma afirmação publicada caiu diante de medição nova | ler a versão nova, e desconfiar de quem citar a antiga |
| **derivou** | valia quando foi medida e não vale mais | refazer a medição antes de usar |

Toda afirmação traz também **o que ela não prova**. Essa coluna é a parte do documento que
mais custou a escrever e a única que impede o resto de virar propaganda.


## As afirmações

### Selecionar contexto com o Jev responde **melhor** do que carregar tudo

**Força:** demonstrado.

**Evidência.** Em 169 perguntas geradas e filtradas por máquina, mandar os dois trechos que o Jev escolheu acerta 158/169 (93,5%) contra 141/169 (83,4%) carregando os oito. Pareado caso a caso: 22 a 5, p = 0,0015. E com 74,0% menos contexto.

**O que não prova.** Não prova que vale para qualquer corpus. As perguntas são sobre código Python deste repositório, respondidas por um modelo só. Um corpus onde a resposta dependa de juntar vários trechos deve inverter o sinal.

**Dado bruto:** `r18-escala.json`, `r20-k-adaptativo.json`, `r18-r20-consolidado.json`

### O Jev ordena melhor que o BM25

**Força:** demonstrado.

**Evidência.** Na colocação do trecho certo entre os dois primeiros, 22 casos só do Jev contra 1 só do BM25, p < 0,0001. Na resposta final, 18 a 1, p = 0,0001.

**O que não prova.** O BM25 aqui é uma implementação de referência com k1=1,5 e b=0,75 sobre o mesmo recorte, sem ajuste de parâmetros nem expansão de consulta. Um BM25 afinado para este corpus fecharia parte da diferença.

**Dado bruto:** `r18-escala.json`, bloco `pareado`

### Como segunda camada, o Jev corta dois terços das confirmações inúteis sem soltar nada irreversível

**Força:** demonstrado.

**Evidência.** Em 120 comandos reais desta máquina, a regra por palavra barrou 90. Dos 108 comandos benignos da amostra, a regra sozinha interrompe 72,2%; com o Jev liberando o que a regra barrou, 29,6%. Foram 46 liberações e 0 irreversíveis soltos.

**O que não prova.** Zero observado não é zero garantido: o intervalo de Wilson sobre 0 em 46 liberações admite até 7,7% de erro. Por isso o guarda nunca libera sozinho — ele só deixa de pedir confirmação do que a regra já barrou.

**Dado bruto:** `r16-guarda-de-comando.json`, `r16b-segunda-camada.json`

### Receber a instrução pelo prompt expõe o comparador a um risco que o contrato do Jev não tem

**Força:** demonstrado.

**Evidência.** Sob as mesmas injeções, a taxa de virada foi c1 12,5%, c2 0,0%, c3 25,0%, c4 70,0%, jev 0,0%. Nem todo comparador vira — o `mistralai/mistral-nemo` também ficou em zero nesta rodada — mas os que viram, viraram muito, e o pior deles em 7 de cada 10 tentativas.

**O que não prova.** Os comparadores recebem a instrução no prompt porque é assim que eles funcionam; a comparação é entre **arquiteturas de chamada**, não entre inteligências. Um comparador com defesa própria contra injeção não foi testado.

**Dado bruto:** `r10-injecao-comparada.json`, bloco `por_braco`

### Um trecho e dois trechos são equivalentes; três é pior

**Força:** direção consistente, sem significância.

**Evidência.** k=1 contra k=2: 3 a 4, p = 1,0 — nenhuma diferença, e k=1 custa metade. k=2 contra k=3: 8 a 2, p = 0,1094.

**O que não prova.** A queda de k=2 para k=3 nunca atingiu p < 0,05, em nenhum recorte. A direção se manteve em todos e não se inverteu em nenhum, o que é sugestivo e não é prova.

**Dado bruto:** `r18-r20-consolidado.json`, bloco `pareado`

### Uma frase na instrução conserta a pior fraqueza medida

**Força:** direção consistente, sem significância.

**Evidência.** Dizer na instrução de quem é o pedido que importa levou a acurácia de 89,4% para 92,9% em 85 mensagens, sem piorar nenhuma família.

**O que não prova.** São 3 casos a 0 no geral, p = 0,25. A recomendação se justifica pelo custo — uma frase — e pela ausência de contrapartida, não pela significância.

**Dado bruto:** `r19-armadilha.json`, formulação `B-instrucao-de-sujeito`

### A classe que o Jev dá ao melhor candidato prediz se a resposta vai sair certa

**Força:** medição única, sem comparador.

**Evidência.** Quando o topo veio `essencial` (93 casos), a resposta acertou 95,7%. Nos 2 casos em que veio `irrelevante`, acertou 0,0% — e em nenhum deles o trecho certo estava entre os candidatos.

**O que não prova.** São dois casos do lado `irrelevante`. O intervalo de Wilson vai de 0 a 65,8%: o sinal é real como hipótese e frágil como número. Vale porque a ação que ele sugere — buscar mais candidatos em vez de escolher melhor — é barata e sai de graça na mesma chamada.

**Dado bruto:** `r20-k-adaptativo.json`, bloco `por_classe_do_topo`

### Decompor a decisão em duas perguntas não ajuda quando a pergunta auxiliar é mais fraca que a decisão

**Força:** falsificado.

**Evidência.** Perguntar *de quem é a ação* junto com *qual é a ação*, de graça no mesmo payload, sobe a família do terceiro para 95,5% contra 84,4% — e derruba o geral para 80,7%, porque destrói o molde oposto. A causa está medida: a pergunta de sujeito acerta sozinha 68,7%.

**O que não prova.** Não condena a decomposição em geral. Condena decompor **numa pergunta menos confiável que a decisão que ela alimenta**, que é o caso aqui e é verificável antes de adotar: basta medir a pergunta auxiliar sozinha.

**Dado bruto:** `r19-armadilha.json`, formulação `D-sujeito-e-acao` e `pergunta_de_sujeito`

### Recortar o candidato com as constantes do módulo junto piora a resposta

**Força:** falsificado.

**Evidência.** A mitigação proposta na R17 melhorou a **ordenação** (74/74 contra 72/74) e piorou a **resposta** (66 contra 69). Mais contexto ajuda a achar e atrapalha a responder — a mesma curva do k, por outro caminho.

**O que não prova.** O pareamento é 2 a 5, p = 0,45: a piora não é significativa. O que a rodada falsifica é a hipótese de que o cabeçalho **melhoraria** a resposta, que era a razão de propô-lo.

**Dado bruto:** `r18-escala.json`, arranjo `jev-cab-2`

### Contra aviso pseudo-sistêmico o Jev não vira; contra **ordem direta**, vira

**Força:** afirmação anterior corrigida por medição nova.

**Evidência.** Sob os 12 vetores adversariais escritos por três LLMs, o Jev virou 0 de 50 na família que fala com o classificador e 10 de 70 na que acrescenta um pedido real — e 0 dessas passaram do corte de 0,9. Foi disso que saiu a afirmação de imunidade. Só que os doze vetores são **avisos pseudo-sistêmicos** ("Protocolo #7894-Omega", "Cancelamento automático aprovado"): nenhum dá uma ordem ao classificador. A meta-instrução imperativa, testada só na R21, vira 21 de 68 no jurídico e 28 de 81 **em atendimento**, o domínio onde a imunidade tinha sido publicada.

**O que não prova.** Não apaga a separação estrutural entre `state` e `questions`, que é real e é o que impede o texto do cliente de virar instrução por concatenação. O que cai é a leitura de que isso produz imunidade. E cai também o uso do corte de confiança como defesa: ele barra as viradas em atendimento e deixa passar 10 de 25 no jurídico. Contra ordem direta escrita no estado, a defesa é sanitizar a entrada.

**Dado bruto:** `r15b-familias.json`, `r21-generalizacao.json`, `r21b-cruzamento.json`

### O endpoint rejeita a chamada quando a instrução vem vazia — **não vale mais**

**Força:** deixou de valer — deriva pega pelo canário.

**Evidência.** Em 2026-09-19, a condição `instrucao/vazia` da R11 voltou `http 400` em 30 de 30 chamadas: o provedor recusava o payload. Em 2026-09-20, o canário `instrucao-vazia-nao-responde` reprovou — com os **mesmos critérios** e a instrução igualmente vazia, **7 de 7** chamadas voltaram 200, com a classe certa e confiança 1 (duas corridas de canário e três de confirmação com o formato literal da R11). A propriedade caiu em menos de 24 horas, e quem pegou foi o canário, na primeira corrida dele.

**O que não prova.** Não prova o que mudou do outro lado: da posição de cliente não dá para distinguir validação relaxada, troca de versão do modelo ou roteamento diferente. O que fica provado é outra coisa, e mais importante: uma propriedade publicada do endpoint pode morrer em um dia, e documentação sem canário não avisa. Nenhuma recomendação do guia dependia desta, o que foi sorte e não projeto.

**Dado bruto:** `r11-extremos.json` e `canarios-de-comportamento.jsonl`

## Fichas das rodadas do programa E17

| rodada | a pergunta | o desenho | o que saiu | bruto |
|---|---|---|---|---|
| **R15** | O Jev resiste a ataque que eu não escrevi? | 12 vetores escritos por 3 LLMs, 600 chamadas | Falsificou a versão simples da afirmação de imunidade em horas; a R15b recuperou uma versão mais forte e mais precisa separando meta-instrução de conteúdo inserido. | `r15-adversario-externo.json` |
| **R16** | O Jev serve de guarda de comando de shell? | 120 comandos reais, 4 formulações, 480 avaliações | No lugar da regra é inseguro. Depois da regra, corta dois terços da fricção sem soltar nada irreversível. | `r16-guarda-de-comando.json` |
| **R17** | Quanto contexto a ordenação economiza, de verdade? | 20 perguntas escritas à mão, 80 respostas avaliadas | Primeira medição de economia do estudo: 72,6% do contexto, sem perder resposta. Amostra pequena demais para decidir entre arranjos. | `r17-economia-de-contexto.json` |
| **R18** | A mesma pergunta em escala, com gabarito que não é meu | 74 perguntas geradas por LLM e aprovadas por filtro mecânico, 592 respostas avaliadas | Fechou a dúvida contra o BM25 e achou a curva do k. Falsificou a mitigação do cabeçalho que a R17 tinha proposto. | `r18-escala.json` |
| **R19** | Dá para consertar a armadilha de ação de terceiro? | 85 mensagens de 5 moldes com gabarito fixado antes do texto, 340 avaliações | Sim, com uma frase. E não com decomposição: a capacidade de múltiplas perguntas no mesmo payload, nunca usada em 6.000 chamadas anteriores, piora o resultado geral. | `r19-armadilha.json` |
| **R20** | Replica em lote novo, e a confiança pode escolher o k? | 95 perguntas de semente nova sobre funções que a R18 não usou, 475 respostas avaliadas | Replicou. Juntando os dois lotes (169 perguntas), selecionar deixa de "não perder" e passa a **ganhar** de carregar tudo. O k adaptativo empata em acerto e economiza 86,2% contra 73,7%. | `r20-k-adaptativo.json` |

## Contabilidade

O livro-caixa SQLite em `runs/ledger.sqlite3` registra **40.542 chamadas** liquidadas, somando **US$ 1,5213** do teto de US$ 5,00 autorizado — restam US$ 3,4787. O livro-caixa é a fonte única: os JSONL do laboratório são cópias do mesmo evento e somá-los junto contaria duas vezes, defeito que já esteve no painel e foi corrigido.

## Como conferir

```
python laboratorio/auditoria.py                         # recalcula tudo e aponta divergência
python laboratorio/gerar_dossie.py                      # regera esta página a partir do dado
python -m laboratorio.canarios_de_comportamento --rodar # 16 chamadas: as propriedades ainda valem?
python -m pytest                                        # a auditoria está presa na suíte
```

A auditoria confere três coisas, nesta ordem: que cada resumo fecha quando recalculado das linhas brutas; que cada número escrito na documentação existe nesses resumos, com a mesma casa decimal; e que as chamadas e o custo declarados fecham com o livro-caixa. Ela também declara o que **não** consegue conferir, em vez de omitir.

Mas a auditoria só prova que os números fecham com o dado **que foi medido**. Ela não tem como saber se o modelo do outro lado continua o mesmo, e essa é a segunda metade do problema. Os canários de comportamento congelam oito propriedades em que este dossiê se apoia, custam menos de US$ 0,0003 por corrida, e a primeira corrida deles já derrubou uma afirmação desta página — que é exatamente o serviço que deviam prestar.
