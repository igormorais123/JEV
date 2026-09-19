import json
import subprocess
import sys
from unittest.mock import patch

from integracao import jev_mcp


def test_stdio_handshake_and_catalog():
    requests = [
        {'jsonrpc':'2.0', 'id':1, 'method':'initialize', 'params':{'protocolVersion':'2024-11-05'}},
        {'jsonrpc':'2.0', 'method':'notifications/initialized'},
        {'jsonrpc':'2.0', 'id':2, 'method':'tools/list'},
    ]
    result = subprocess.run([sys.executable, str(jev_mcp.ROOT/'integracao/jev_mcp.py')],
                             input='\n'.join(json.dumps(r) for r in requests).encode()+b'\n',
                             capture_output=True, timeout=15, check=True)
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(responses) == 2
    assert len(responses[1]['result']['tools']) == 4
    assert result.stderr == b''


def test_rank_keeps_all_candidates_and_ids():
    def answer(task, state):
        choice = 'essencial' if state.endswith('yes') else 'irrelevante'
        return {'choice':choice, 'confidence':.99}
    with patch.object(jev_mcp, 'evaluate', side_effect=answer):
        result = jev_mcp.call('jev_rank_context', {'query':'q', 'candidates':[
            {'id':'a', 'text':'no'}, {'id':'b', 'text':'yes'}]})
    assert [r['id'] for r in result['candidates']] == ['b', 'a']
    assert result['discarded'] == []


def test_bad_arguments_cannot_call_provider():
    with patch.object(jev_mcp, 'evaluate') as evaluate:
        result = jev_mcp.handle({'id':1, 'method':'tools/call', 'params':{
            'name':'jev_assist', 'arguments':{'task':'log', 'state':'a'*60001}}})
    assert result['result']['isError']
    evaluate.assert_not_called()
