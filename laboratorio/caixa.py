"""O livro-caixa conciliado: o número que a documentação declara e a auditoria confere.

Enquanto o gasto era em rodadas, "quem gasta atualiza o número" bastava: conciliava-se depois
da rodada e a auditoria conferia por igualdade exata contra o SQLite. Com os hooks do Claude
Code ligados, o livro-caixa cresce a toda hora — duas chamadas entre a conciliação e a
auditoria já quebravam a suíte. A igualdade exata continua, mas contra um **corte**: o
instantâneo que `conciliar_caixa.py --gravar` grava em `runs/caixa-conciliado.json`
(versionado). Os geradores de página e a auditoria leem o instantâneo; a auditoria confere
além disso que ele é recente e que o livro-caixa ao vivo nunca é menor do que ele.
"""
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LEDGER = RAIZ / 'runs' / 'ledger.sqlite3'
INSTANTANEO = RAIZ / 'runs' / 'caixa-conciliado.json'
VALIDADE_HORAS = 48  # a rotina diária renova; mais que dois dias é sinal de rotina parada


def ao_vivo():
    """Totais e por experimento, direto do SQLite, agora."""
    if not LEDGER.exists():
        return None
    conexao = sqlite3.connect(f'file:{LEDGER}?mode=ro', uri=True)
    chamadas, gasto = conexao.execute('select count(*), sum(settled_nusd) from attempt_budget').fetchone()
    por_experimento = [{'experimento': e, 'chamadas': n, 'usd': (u or 0) / 1e9} for e, n, u
                       in conexao.execute('select experiment_id, count(*), sum(settled_nusd) '
                                          'from attempt_budget group by 1 order by 1')]
    conexao.close()
    return {'chamadas': chamadas, 'usd': (gasto or 0) / 1e9, 'por_experimento': por_experimento}


def gravar_instantaneo():
    dado = ao_vivo()
    if dado is None:
        raise RuntimeError('livro-caixa ausente')
    dado['em'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    # O corte em UTC, no formato das colunas `recorded_at` e `started_at_utc` do livro-caixa:
    # as páginas que leem decisões e tentativas param aqui, não no que os hooks gastaram depois.
    dado['corte_utc'] = datetime.now(timezone.utc).isoformat()
    INSTANTANEO.write_text(json.dumps(dado, ensure_ascii=False, indent=1), encoding='utf-8')
    return dado


def conciliado():
    """O instantâneo; sem ele (repositório recém-clonado com ledger), o ao vivo."""
    try:
        return json.loads(INSTANTANEO.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ao_vivo()


def totais():
    """(chamadas, usd) do conciliado — a assinatura que os geradores sempre usaram."""
    dado = conciliado()
    if dado is None:
        return 0, 0.0
    return dado['chamadas'], dado['usd']


def corte_utc():
    """O instante do último instantâneo, ou None (sem instantâneo, tudo conta)."""
    dado = conciliado()
    return (dado or {}).get('corte_utc')


def idade_horas():
    dado = conciliado()
    if not dado or 'em' not in dado:
        return None
    return (time.time() - time.mktime(time.strptime(dado['em'], '%Y-%m-%dT%H:%M:%S'))) / 3600
