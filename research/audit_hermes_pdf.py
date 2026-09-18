"""Recalcula tabelas do PDF, sem rede e sem importar codigo do Hermes.

Entrada: texto extraido do PDF com pypdf; nao equivale ao ledger original.
Uso: python research/audit_hermes_pdf.py
"""
import csv
import hashlib
import json
import math
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'research' / 'hermes'
SOURCE = DEST / 'Jev-Dossie-Quantitativo.txt'


def wilson(k, n, z=1.959963984540054):
    p = k / n
    centre = (p + z*z/(2*n)) / (1+z*z/n)
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1+z*z/n)
    return [max(0, centre-half), min(1, centre+half)]


def main():
    rows = []
    page = None
    pattern = re.compile(r'^fase2 (solo|batch) (\d+) (\S+) (triage|evidence|claim) (development|holdout) (\S+) (\S+) ([01]) ([\d.]+)$')
    for line in SOURCE.read_text(encoding='utf-8').splitlines():
        pm = re.match(r'=== PAGINA (\d+) ===', line)
        if pm:
            page = int(pm.group(1))
        match = pattern.match(line.strip())
        if not match:
            continue
        mode, call, case, app, split, expected, predicted, correct, confidence = match.groups()
        rows.append(dict(phase='fase2', mode=mode, call_id=int(call),
                         case_id='fase2:'+case, app=app, split=split,
                         expected=expected, predicted=predicted, correct=int(correct),
                         confidence_pdf=float(confidence), source_page=page,
                         provenance='pdf_table_transcription_not_raw_ledger'))
    assert len(rows) == 96, f'Esperadas 96 linhas, encontradas {len(rows)}'
    assert len({(r['case_id'], r['mode']) for r in rows}) == 96
    assert len({r['case_id'] for r in rows}) == 48
    assert len({r['call_id'] for r in rows}) == 54
    assert all(r['correct'] == int(r['expected'] == r['predicted']) for r in rows)
    with (DEST / 'fase2-decisoes-do-pdf.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    paired = []
    expected_counts = {'triage': (16,16), 'evidence': (14,13), 'claim': (15,16)}
    for app in ['triage','evidence','claim']:
        for mode in ['solo','batch']:
            for split in ['all','development','holdout']:
                selected = [r for r in rows if r['app']==app and r['mode']==mode and (split=='all' or r['split']==split)]
                n, k = len(selected), sum(r['correct'] for r in selected)
                if split == 'all':
                    assert k == expected_counts[app][mode=='batch']
                summary.append(dict(app=app,mode=mode,split=split,n=n,correct=k,
                                    accuracy=k/n,wilson_95=wilson(k,n)))
        pairs = {}
        for row in rows:
            if row['app']==app:
                pairs.setdefault(row['case_id'], {})[row['mode']] = row
        b = sum(p['solo']['correct']==1 and p['batch']['correct']==0 for p in pairs.values())
        c = sum(p['solo']['correct']==0 and p['batch']['correct']==1 for p in pairs.values())
        discordant = b+c
        pvalue = min(1, 2*sum(math.comb(discordant, i) for i in range(min(b,c)+1))/2**discordant) if discordant else 1.0
        paired.append(dict(app=app,n_pairs=len(pairs),solo_only_correct=b,batch_only_correct=c,
                           delta_batch_minus_solo=(c-b)/len(pairs),mcnemar_exact_two_sided=pvalue,
                           prediction_changes=sum(p['solo']['predicted']!=p['batch']['predicted'] for p in pairs.values())))
    known = Decimal('2.999678514')+Decimal('0.001915032')
    reserved = Decimal('0.001344')
    report = dict(
        method='offline_recalculation_from_pdf_tables', paid_calls=0,new_cost_usd='0',
        input_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        source='Jev-Dossie-Quantitativo.pdf, anexo F, paginas 43-47',
        n_rows=len(rows),n_unique_cases=48,n_calls=54,
        caveat='Casos sinteticos autorais; independencia semantica externa nao demonstrada. Confidence arredondada no PDF. Nao valida ledger, payload ou custo original.',
        summary=summary, paired=paired,
        historical_budget_from_reports=dict(known_usd=str(known),unresolved_reserved_usd=str(reserved),
            conservative_committed_usd=str(known+reserved), remaining_under_5_usd=str(Decimal('5')-known-reserved)),
        batching_reported_cost_reduction=1-0.000496776/0.000937272,
        zero_error_examples=[dict(n=n,one_sided_95_upper_error=1-.05**(1/n)) for n in [12,16,59,299,598]],
        planning_paired_noninferiority=[dict(discordance=.1,margin=d,alpha_one_sided=.05,power=.8,
            approximate_pairs=math.ceil((1.644853626951+0.841621233573)**2*.1/d**2)) for d in [.05,.02]])
    (DEST / 'auditoria-local.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['method','n_rows','n_unique_cases','n_calls','paired','historical_budget_from_reports','planning_paired_noninferiority']},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
