# Executor financeiro (Etapa 2 do plano)

Implementa o controle exigido na seção 7 do `planning/protocolo.md`: nenhuma chamada paga sai sem
reserva atômica do pior custo possível.

## Como decide liberar

`gasto liquidado + reservas pendentes + pior custo da próxima tentativa <= teto global e teto do bloco`

Tudo em nanodólares inteiros (1 USD = 1.000.000.000). Conversões de preço por milhão de tokens
arredondam para cima, então o controle nunca subestima gasto.

## Regras que o código aplica

- **Sem preço ou sem teto de tokens, não despacha.** `executor/prices.json` está vazio de propósito:
  enquanto nenhuma tarifa for conferida no provedor, toda reserva falha com `PricingError`.
- **Timeout conserva a reserva.** A chamada pode ter sido cobrada; só há liberação por
  `cancel_before_send`, que exige evidência de que a requisição não saiu.
- **Retry é tentativa nova**, com reserva própria e `parent_attempt_id` declarado.
- **Resposta sem `usage` liquida pelo pior caso reservado**, com `cost_source = worst_case_no_usage`
  e `known_cost_nusd` nulo — custo comprometido, não custo conhecido.
- **Custo acima da reserva** é registrado como `overrun_nusd`; se estourar o teto global, o
  experimento passa a `paused`.
- **Conciliação por delta** sobre o último snapshot do provedor, sem somar duas vezes ledger e extrato.
- Gasto histórico entra como `historical_commitment` e ocupa o teto total.

## Uso

```python
from executor.ledger import Ledger
from executor.pricing import usd_to_nusd

with Ledger('runs/ledger.sqlite3', 'exp-simples') as ledger:
    ledger.authorize(usd_to_nusd('1.70'))
    ledger.set_block_cap('rodada-simples', usd_to_nusd('0.25'))
    ledger.register_arm('arm-s01', 'S01', 'openrouter', 'typesafe/jev-1.13')
    reserva = ledger.reserve(arm_id='arm-s01', block_id='rodada-simples', provider='openrouter',
                             model='typesafe/jev-1.13', max_input_tokens=2000, max_output_tokens=200,
                             payload_sha256=sha, request_path=..., runtime_manifest_path=...)
    # envia, e depois: ledger.settle(reserva['attempt_id'], usage=resposta['usage'])
```

## Testes

```powershell
python -m pytest executor/tests -q
```

Cobrem concorrência (24 threads disputando um teto exato), reinício após queda do processo, timeout,
resposta sem `usage`, `usage` parcial, arredondamento, ausência de preço e conciliação por delta.
Nenhum teste faz rede.

## Contrato real do endpoint (sondado em 18/09/2026)

O plano supunha `questions` como lista. O endpoint recusa esse formato com HTTP 400. A forma aceita é:

```json
{
  "model": "typesafe/jev-1.13",
  "state": "texto do caso",
  "questions": {
    "acao": {
      "type": "choice",
      "instructions": "Classifique a acao que o usuario pediu.",
      "criteria": {"cancelar": "Pede cancelamento.", "rastrear": "Pede informacao de entrega."}
    }
  }
}
```

`type` é o discriminador e aceita `choice`, `noul` e `score`. Em `score`, `criteria` é array, não objeto.
A resposta vem assim:

```json
{
  "model": "typesafe/jev-1.13-20260917",
  "answers": {"acao": {"type": "choice", "choice": "cancelar",
                        "probabilities": {"cancelar": 1, "rastrear": 0}, "confidence": 1}},
  "usage": {"input_tokens": 379, "output_tokens": 46, "cost": 1.5918e-05},
  "id": "gen-dec-...", "provider": "TypeSafe"
}
```

`usage.cost` é o valor autoritativo da cobrança e bate exatamente com a tarifa publicada.

## Por que a reserva usa o contexto cheio

A estimativa de tokens do payload subestimou o consumo real: 159 estimados contra 379 cobrados, porque o
provedor acrescenta instruções que o cliente não vê. Reservar pela estimativa deixaria o teto furado, então
a reserva usa o contexto publicado (32.000 tokens, US$ 0,001344 por chamada) salvo teto menor declarado.
Com US$ 5 de teto isso comporta mais de 3.700 chamadas, muito acima das 168 do plano.

## Estado em 18/09/2026

Etapa 2 concluída. Os 3 canários de contrato responderam corretamente, com confidence 1, entre 374 e 578 ms,
custo real de US$ 0,000046410 somando as três. Ledger real em `runs/ledger.sqlite3`.

## O que ainda falta

1. Reduzir o limite da chave no painel do provedor ao valor autorizado (exige acesso à conta; a API de
   chaves precisa de provisioning key, que não temos).
2. Repetir a conciliação por extrato: o agregado do provedor tem defasagem e ainda não refletia as chamadas
   no fim da rodada.
3. Mapear os formatos `noul` e `score`, ainda não aceitos nas sondas feitas.
