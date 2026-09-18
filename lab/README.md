# JEV — interface de acompanhamento

Abra `lab/index.html` no navegador ou execute, na raiz do projeto:

```powershell
python lab/server.py --port 8766
```

Acesse **http://127.0.0.1:8766**. O servidor escuta apenas o computador local e serve uma lista fechada de arquivos. Não lê `.env` e não tem rota de inferência.

## O que funciona

- Terminal: fila de 30 rodadas planejadas, etapa atual, atividade registrada e custos dos próximos testes.
- Execução: status por sistema/rodada e por etapa do plano, com gravação persistente.
- Sistemas: perguntas, protocolos, critérios e notas/bloqueios editáveis.
- Resultados: abas de novas execuções e histórico de referência, importação JSON validada, execuções, tentativas, decisões, filtros, paginação, detalhes e exportação CSV.
- Métricas explicadas: acurácia, intervalo de Wilson, precisão, recall, F1, macro-F1, matriz de confusão, latência e custo. Cada número vem com significado, denominador, fórmula acessível e limite de interpretação.
- Orçamento: histórico separado, gasto novo conhecido, reservas e custos ainda desconhecidos. Não é bloqueio de gastos nem autorização para chamadas.
- Arquivos: plano, PDFs, CSVs, fontes e contrato de dados.

O HTML aberto diretamente salva o acompanhamento em `localStorage`, restrito ao navegador/origem. Exporte backup para transportar esse estado. No modo conectado, o estado canônico é **`lab/data/execution.json`**, salvo atomicamente e com uma revisão anterior em `execution.previous.json`. A tela consulta atualizações a cada 5 segundos quando visível e sem formulário aberto. Um formulário aberto protege a edição contra substituição automática; salvar com revisão antiga exige recarregar e conferir.

Status de acompanhamento não é evidência de execução. O arquivo inicial contém **zero execuções novas**; as 96 decisões do Hermes são dados históricos já conferidos. O painel não simula resultados para preencher gráficos.

## Métricas e significado

- **Acurácia:** acertos / decisões com gabarito. Não inclui registros sem avaliação.
- **Precisão da classe:** quando o modelo escolheu essa classe, quantas escolhas estavam certas.
- **Recall da classe:** quantos casos reais dessa classe ele conseguiu encontrar.
- **F1:** equilíbrio entre precisão e recall. Macro-F1 dá o mesmo peso a cada classe presente.
- **Intervalo de 95%:** faixa de incerteza de Wilson, sob hipóteses de amostragem independente. Não é uma probabilidade individual de acerto. O painel desativa a conta se identifica repetição de caso/grupo. Seleção enviesada e relações não registradas não são corrigidas pelo intervalo.
- **Matriz de confusão:** linhas são gabaritos; colunas são respostas. A diagonal reúne acertos.
- **p50/mediana:** duração central; **p95:** posição que deixa aproximadamente 95% dos tempos abaixo. O p95 usa a posição `ceil(0.95*N)`; com poucos tempos, aproxima-se do máximo. Cache e falhas são separados da duração de respostas bem-sucedidas.
- **Custo conhecido:** soma do informado; `null` não é zero nem prova de gratuidade.

As métricas de classificação pressupõem rótulos categóricos sob a mesma rubrica. Não usar F1 para comparar textos livres ou notas contínuas sem um protocolo apropriado. Os filtros evitam somar individual e lote no painel de métricas. Nos dados novos, escolha uma execução, tarefa e partição. Métricas operacionais se referem à execução inteira, explicitamente identificada, pois falhas podem não ter decisão associada.

## Como importar resultados reais

Clique **Importar resultados**, escolha o arquivo e revise a prévia. O formato é JSON UTF-8, até 8 MB. Exporte um backup antes de recuperar anotações antigas: status/notas de um backup substituem os mesmos campos locais, mas preservam execuções existentes.

Estrutura ilustrativa abaixo — **não é resultado executado**. Substitua os campos pelos dados reais. `cost_usd`, contagens ou duração desconhecidos devem ser `null`; sempre informe a reserva pendente como número. IDs de tentativa são únicos globalmente, inclusive entre execuções, para não contar a mesma cobrança duas vezes.

```json
{
  "schema_version": 1,
  "kind": "jev-lab-results",
  "runs": [{
    "id": "IDENTIFICADOR-REAL-DA-EXECUCAO",
    "system_id": "S01",
    "phase": "simple",
    "evidence": "live_component",
    "status": "completed",
    "started_at": "2026-09-18T20:00:00Z",
    "finished_at": null,
    "provider": "PROVEDOR-REAL",
    "model": "VERSAO-EFETIVAMENTE-RETORNADA",
    "dataset": "NOME-E-VERSAO-DO-CONJUNTO",
    "notes": "Exemplo de formato. Preencher com evidência real.",
    "attempts": [{
      "id": "UUID-REAL-DA-TENTATIVA",
      "status": "success",
      "latency_ms": null,
      "input_tokens": null,
      "output_tokens": null,
      "cost_usd": null,
      "reserved_usd": 0,
      "cache_hit": false
    }],
    "decisions": [{
      "id": "ID-REAL-DA-DECISAO",
      "case_id": "NAMESPACE:CASO",
      "attempt_id": "UUID-REAL-DA-TENTATIVA",
      "task": "triage",
      "split": "test",
      "expected": null,
      "predicted": "SAIDA-REAL",
      "correct": null,
      "confidence": null,
      "group_id": "FAMILIA-DO-CASO"
    }],
    "artifacts": []
  }]
}
```

Valores permitidos:

| Campo | Valores |
|---|---|
| system_id | S01 a S15, conforme matriz do plano |
| phase | simple, deep, pilot, confirmation |
| evidence | offline, replay, live_component, mock_integration, live_e2e |
| status da execução | running, completed, failed |
| status da tentativa | success, timeout, error, pending |
| split | pilot, development, calibration, test, diagnostic |
| correct | true, false, null |
| confidence | número entre 0 e 1 ou null |

`artifacts` aceita objetos com `label` e `url`. URLs HTTP(S) podem ser abertas; outros caminhos são mostrados como texto. HTML nos campos é exibido como texto, não executado. Pacotes contendo padrões de credenciais são recusados.

Reimportar uma execução idêntica é idempotente. Uma atualização do mesmo ID pode acrescentar tentativas/decisões, concluir status pendente, preencher custos/tokens/duração antes desconhecidos e reconciliar reservas. Não pode remover evidências, mudar a identidade do teste, reescrever decisões ou valores já conhecidos. Para corrigir informação conhecida, preserve a evidência e faça uma revisão explícita do dado na origem; não invente outra tentativa para repetir a mesma cobrança.

## Como o executor futuro publica sem intervenção manual

1. Ler `GET /api/state` e guardar `revision`.
2. Atualizar o estado em memória com os registros reais e o progresso correspondente. Nenhuma chave entra nesse objeto.
3. Enviar `PUT /api/state`, com `Content-Type: application/json` e `X-Jev-Lab: 1`. Preservar a revisão lida.
4. HTTP 200 devolve a revisão nova. HTTP 409 significa alteração concorrente: reler, conciliar e tentar novamente. HTTP 400 aponta formato/atualização inválida, sem salvar.
5. O painel recebe a revisão na próxima consulta. Custos desconhecidos e falhas continuam visíveis.

Essa publicação acompanha testes feitos por outro processo. Ela não implementa o executor de inferências nem o controle financeiro previsto no plano.

## Reconstrução e verificação

```powershell
python lab/build_ui.py
python -m unittest discover -s lab/tests -p "test_*.py"
```

Fontes visuais: `dashboard.html`, `dashboard.css`, `dashboard.js` e `metrics.js`. `index.html` é o artefato HTML autossuficiente gerado. O gerador de documentos também chama esse build, preservando a interface atual.
