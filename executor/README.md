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

## O que ainda falta antes da primeira chamada paga

1. Preencher `prices.json` com tarifas conferidas no provedor, com data e fonte.
2. Reduzir o limite da chave no painel do provedor ao valor autorizado.
3. Conciliação real contra o extrato, com baseline capturado antes do primeiro despacho.
4. Esclarecer a abrangência do teto de US$ 5 (ver `README.md` na raiz).
