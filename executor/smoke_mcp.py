"""Real stdio smoke: public local test error, reviews, metrics; explicit paid action."""
import json
import subprocess
import sys
from pathlib import Path
from .shared import ROOT


def exchange(requests):
    result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/'integracao/jev_mcp.py')],
                            input=('\n'.join(json.dumps(r) for r in requests)+'\n').encode(),
                            capture_output=True, timeout=90, check=True)
    if result.stderr:
        raise RuntimeError('MCP wrote stderr')
    return [json.loads(line) for line in result.stdout.splitlines()]


def main():
    output = ROOT/'runs/e15-implantacao/mcp-smoke.json'
    if output.exists():
        raise RuntimeError('Smoke already recorded; do not spend again without new reason')
    messages = [
        {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}},
        {'jsonrpc':'2.0','method':'notifications/initialized'},
        {'jsonrpc':'2.0','id':2,'method':'tools/list'},
        {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{
            'name':'jev_assist','arguments':{'task':'log','state':
                'sqlite3.IntegrityError: NOT NULL constraint failed: attempts.request_path'}}},
        {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'jev_metrics','arguments':{}}},
    ]
    responses = exchange(messages)
    response = next(r for r in responses if r['id']==3)['result']
    assert not response['isError']
    classified = json.loads(response['content'][0]['text'])
    assert classified['choice'] == 'contrato'
    assert classified['autonomous'] is False
    attempt = classified['receipt']['attempt_id']
    reviews = exchange([{'jsonrpc':'2.0','id':5,'method':'tools/call','params':{
        'name':'jev_record_review','arguments':{'attempt_id':attempt,'expected_choice':'contrato',
        'reviewer_kind':'assistant','evidence':'Observed local pytest failure during E15 development; SQLite NOT NULL violation. Author review, not independent human gold.'}}}])
    assert not reviews[0]['result']['isError']
    output.write_text(json.dumps({'responses':responses,'review':reviews,
                      'evidence_level':'live_component','host_native_reload_verified':False}, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'choice':classified['choice'],
                      'confidence':classified['confidence'], 'cost_usd':classified['receipt']['custo_usd'],
                      'attempt_id':attempt,'protocol':'stdio','review_recorded':True}))


if __name__=='__main__':
    main()
