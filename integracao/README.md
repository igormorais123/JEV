# O Jev dentro do Claude Code e do Codex

Este pacote aplica o Jev aos fluxos de trabalho reais desta máquina. Ele foi construído para
responder a uma pergunta de economia — *dá para o Jev, que custa US$ 0,042 por milhão de tokens,
poupar trabalho do Opus e do Fable, que custam milhares de vezes mais?* — e a resposta honesta
tem duas partes.

## O que não funcionou, e por quê

**Roteamento de esforço não funciona neste fluxo de trabalho.** A ideia era classificar cada
pedido como simples ou difícil e, nos simples, evitar subagente e modelo caro. Medido em 60
pedidos reais sorteados do histórico do Claude Code:

| Formulação | Acurácia | Cobertura útil |
|---|---|---|
| Quatro classes de esforço | 51,7% | 0% — 55 dos 60 pedidos viraram `investigacao` |
| Binária, "o pedido diz onde mexer?" | 66,7% | 0% |
| Binária, "quantos minutos leva?" | 70,0% | 0% |
| Binária, **com o contexto da conversa anterior** | 71,8% | 0% |

*Cobertura útil* é a fração de pedidos que o Jev manda para o caminho barato com confiança
acima do corte. Ela é zero em todas as formulações: quando o Jev diz "simples", diz com
confiança de no máximo **0,73**, e não existe corte que economize sem arriscar estragar
trabalho.

A causa apareceu numa terceira pergunta: **54 dos 60 pedidos reais dependem do que foi dito
antes** — "continue", "verifique e corrija então", "piorou tudo". A informação que decidiria não
está no texto do pedido. Dar o contexto anterior ao modelo melhorou 2,6 pontos e não moveu a
cobertura. O gargalo não é a formulação da pergunta; é que a decisão de esforço não está escrita
na mensagem.

**Guarda de comando irreversível funciona, mas não vale aqui.** Sobre 60 comandos de shell
realmente executados, o Jev combinado com a regra por palavra libera 14 dos 30 alarmes falsos
sem soltar nenhum dos 4 comandos irreversíveis reais — e nos quatro ele nunca passou do corte de
confiança. É um bom resultado, e é inútil nesta máquina: o Claude Code aqui roda em
`acceptEdits` com `Bash(*)` liberado, então não há confirmação para poupar. Fica medido, para o
dia em que o modo de permissão mudar. O código está em `avaliacao/comandos.py`.

## O que funciona, e está instalado

**Dizer sobre o que é a mensagem, para sugerir a skill certa.** É a aplicação que o estudo
mediu desde o E1, e a linha de base não é inventada: são os oito `hookify.suggest-skill-*` que
já rodavam nesta máquina por `regex_match`.

Nos mesmos 60 pedidos reais, com corte de confiança 0,90:

| | Temas reais encontrados (de 23) | Sugestões à toa (em 37 sem tema) |
|---|---|---|
| **Jev** | **9** | **0** |
| Regex de hoje | 5 | 1 |

Quase o dobro da cobertura, sem nenhum disparo falso. E o erro do Jev é por omissão — 10 dos 13
erros foram deixar de sugerir, não sugerir errado —, que é o lado seguro para quem injeta
contexto num modelo caro.

O corte é **0,90**, não o 0,99 do guia prático, porque a assimetria aqui é outra: uma sugestão
perdida custa uma skill não carregada; uma sugestão errada custa três linhas de contexto. O
corte foi calibrado neste dado, que é o cuidado nº 2 do guia.

## Como está instalado

Um hook `UserPromptSubmit` no Claude Code (`~/.claude/settings.json`) e no Codex
(`~/.codex/hooks.json`), em modo **ativo**:

```
python integracao/instalar.py --ver          # estado atual
python integracao/instalar.py --instalar --modo ativo
python integracao/instalar.py --instalar --modo sombra   # classifica e registra, não injeta
python integracao/instalar.py --desinstalar
```

O instalador é idempotente e faz backup datado de cada arquivo antes de tocá-lo. Os oito
`hookify.suggest-skill-*` continuam ligados: a troca por este hook é uma decisão à parte, não
foi feita.

Para quem não tem hook — script, Codex por linha de comando, ou o próprio agente:

```
python -m jev_router.cli "redigir a contestação do processo"
python -m jev_router.cli --situacao          # gasto e teto
```

## Garantias de operação

- **Falha para o lado aberto.** Sem chave, sem rede, fora do teto ou com resposta fora do
  contrato, o hook sai em silêncio com código 0. A sessão segue como seguiria sem ele.
- **Segredo não sai daqui.** `redacao.py` mascara credencial antes do envio, por forma e não
  por lista. O teste `test_redacao.py` roda contra as chaves que de fato existem nesta máquina
  e exige que nenhuma sobreviva — sem imprimir nenhuma, nem na falha.
- **Custo sob teto verificado antes do envio.** US$ 0,000085 por chamada no pior caso, teto de
  US$ 0,05 por dia e US$ 1,00 acumulado, em `gastos.jsonl`. As 455 classificações desta
  construção custaram **US$ 0,0104**.
- **Latência**: 488 ms na primeira vez, 74 ms quando o pedido repete (cache em disco).
- **Acento**: a nota é escrita em bytes UTF-8, não pelo console. Por `print` ela chegava ao
  modelo como "confianÃ§a" — o teste `test_a_nota_sai_em_utf8_com_acento_intacto` roda o hook de
  verdade e trava isso.

## Como refazer a medição

```
python avaliacao/amostrar.py --n 60            # sorteia pedidos reais do histórico
python avaliacao/skills.py --rodar             # Jev contra os regex de hoje
python avaliacao/rodar.py                      # o roteamento de esforço que fracassou
python avaliacao/com_contexto.py               # com e sem o contexto da conversa
python avaliacao/comandos.py --extrair --rodar # o guarda de comando
```

Os gabaritos em `avaliacao/gabarito-*.json` foram anotados **antes** de cada execução, e trazem
o mesmo viés declarado do estudo: quem escreveu os critérios anotou o gabarito. Sob um anotador
independente os números podem ser outros — é exatamente o que o E8, o E11 e o E12 mediram.
