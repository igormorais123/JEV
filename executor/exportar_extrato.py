"""Exporta um extrato auditável do livro-caixa para dentro do repositório.

[R13] A revisão adversarial apontou, com razão, que `runs/ledger.sqlite3` é ignorado pelo Git:
quem clona o repositório não leva o livro-caixa, e o "US$ 0,018174462" do relatório é uma
citação que ninguém de fora consegue conferir. Este script publica o extrato em JSON — por
tentativa, sem nenhum segredo — e o total, com o hash SHA-256 do banco, para que a conferência
seja possível sem expor a chave nem o corpo das requisições.

Uso:
    python -m executor.exportar_extrato
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANCO = ROOT / 'runs' / 'ledger.sqlite3'
DESTINO = ROOT / 'runs' / 'extrato-ledger.json'

# Nada de corpo de requisição, cabeçalho, chave ou identificador do provedor que permita
# reconstruir a chamada. O extrato existe para conferir DINHEIRO, não para republicar dados.
CONSULTA = '''
select a.attempt_id, a.arm_id, b.block_id, r.provider, a.model_resolved, a.status,
       b.reserved_nusd, b.settled_nusd, b.cost_source, a.started_at_utc, a.ended_at_utc
  from attempts a
  left join attempt_budget b on b.attempt_id = a.attempt_id
  left join arms r on r.arm_id = a.arm_id
 order by a.attempt_id
'''


def exportar():
    if not BANCO.exists():
        raise SystemExit(f'livro-caixa ausente: {BANCO}')
    db = sqlite3.connect(f'file:{BANCO}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        linhas = [dict(r) for r in db.execute(CONSULTA)]
        total = db.execute(
            'select coalesce(sum(settled_nusd), 0) from attempt_budget').fetchone()[0]
        abertas = db.execute(
            "select count(*) from attempt_budget b join attempts a using (attempt_id) "
            "where b.settled_nusd is null and a.status not in ('cancelled', 'timeout')"
        ).fetchone()[0]
    finally:
        db.close()
    extrato = {
        'gerado_em': datetime.now(timezone.utc).isoformat(),
        'banco': 'runs/ledger.sqlite3 (não versionado; hash abaixo)',
        'sha256_do_banco': hashlib.sha256(BANCO.read_bytes()).hexdigest(),
        'tentativas': len(linhas),
        'comprometido_nusd': int(total),
        'comprometido_usd': round(int(total) / 1e9, 9),
        'reservas_pendentes_sem_liquidacao': abertas,
        'colunas_omitidas': ('qualquer coluna que carregue requisição, resposta, cabeçalho ou '
                             'identificador de credencial'),
        'linhas': linhas,
    }
    DESTINO.write_text(json.dumps(extrato, ensure_ascii=False, indent=1), encoding='utf-8')
    return extrato


if __name__ == '__main__':
    e = exportar()
    print(f"Extrato: {e['tentativas']} tentativas, US$ {e['comprometido_usd']:.9f}, "
          f"{e['reservas_pendentes_sem_liquidacao']} pendentes.")
    print(f"sha256 do banco: {e['sha256_do_banco']}")
