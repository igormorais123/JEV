"""Rodada de oito casos, autorizada separadamente por Igor em 21/09/2026: US$ 0,03."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from executor import shared
from executor.ledger import Ledger
from executor.pricing import load_prices, usd_to_nusd


def main():
    output = ROOT / 'runs/typesafe-smoke-20260921'
    output.mkdir(parents=True, exist_ok=True)
    db = output / 'ledger.sqlite3'
    report_path = output / 'resultados.json'
    # Never replay a paid run on a repeated invocation.
    if db.exists() or report_path.exists():
        raise SystemExit('Rodada já iniciada. Conferir os registros; não repetir automaticamente.')
    corpus = json.loads((ROOT / 'tmp/validacao-typesafe-2026-09-21.json').read_text(encoding='utf-8'))
    (output / 'protocolo.json').write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding='utf-8')
    prices = load_prices()
    prices['snapshot_id'] = 'typesafe-models-2026-09-21-output-free'
    prices['captured_at_utc'] = datetime.now(timezone.utc).isoformat()
    price = prices['models']['typesafe:jev-1.13.0']
    price.update(output_nusd_per_million_tokens=0, input_nusd_per_million_tokens=42000000,
                 source_captured_at_utc=prices['captured_at_utc'],
                 nota='Documentação consultada em 21/09/2026: US$ 0,042/M entrada; saída gratuita.',
                 raw_pricing={'input_usd_per_million': '0.042', 'output_usd_per_million': '0'})
    (output / 'precos.json').write_text(json.dumps(prices, ensure_ascii=False, indent=2), encoding='utf-8')
    consumer = 'typesafe-smoke-20260921'
    shared.CAPS[consumer] = '0.03'
    with Ledger(db, 'authorization', prices=prices) as ledger:
        ledger.set_wallet_cap(usd_to_nusd('0.03'), note='Igor autorizou orçamento NOVO separado de US$ 0,03 para oito testes TypeSafe em 21/09/2026. Não renova os US$ 5 antigos.')
    report = {'provider': 'typesafe', 'model': 'jev-1.13.0', 'budget_usd': .03,
              'corpus': 'synthetic', 'gold_author': 'assistant_before_execution', 'cases': [],
              'started_at': datetime.now(timezone.utc).isoformat()}
    def save():
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    save()
    for case in corpus['cases']:
        try:
            answers, receipt = shared.ask(case['state'], case['questions'], consumer=consumer,
                provider='typesafe', db_path=db, prices=prices, legacy_paths=(), timeout=20)
        except Exception as error:
            report['stopped_error_type'] = type(error).__name__
            save()
            break
        answer = (answers or {}).get('decision', {})
        row = {'id': case['id'], 'task': case['task'], 'expected': case['expected'],
               'predicted': answer.get('choice'), 'confidence': answer.get('confidence'),
               'correct': answer.get('choice') == case['expected'] if answers else None,
               'receipt': receipt}
        report['cases'].append(row)
        save()
        print(json.dumps({'id': row['id'], 'status': receipt['status'], 'correct': row['correct'],
                          'predicted': row['predicted'], 'latency_ms': receipt.get('latency_ms')}), flush=True)
        if receipt['status'] != 'success':
            break
    with Ledger(db, 'authorization', prices=prices) as ledger:
        report['committed_usd'] = ledger.wallet_committed_nusd() / 1e9
        report['remaining_usd'] = ledger.wallet_available_nusd() / 1e9
        report['billing'] = [dict(r) for r in ledger.db.execute(
            'SELECT attempt_id,reserved_nusd,settled_nusd,cost_source FROM attempt_budget')]
    successful = [r for r in report['cases'] if r['receipt']['status'] == 'success']
    report['completed_at'] = datetime.now(timezone.utc).isoformat()
    report['summary'] = {'attempts': len(report['cases']), 'successful': len(successful),
        'correct': sum(r['correct'] is True for r in report['cases']),
        'median_latency_ms': median(r['receipt']['latency_ms'] for r in successful) if successful else None}
    save()
    print(json.dumps({'summary': report['summary'], 'committed_usd': report['committed_usd'],
                      'remaining_usd': report['remaining_usd']}))


if __name__ == '__main__':
    main()
