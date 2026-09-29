"""Agent workflows against an isolated HTTP server and real local subprocesses."""
import concurrent.futures
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from integracao.harness.agent_client import Client
from integracao.harness.agent_layer import AgentError
from integracao.harness.painel import Desk,make_server
from integracao.harness.mcp import handle


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.folder=Path(self.temp.name)
        self.desk=Desk(self.folder)
        self.server=make_server(self.desk,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.client=Client(f'http://127.0.0.1:{self.server.server_port}')
    def tearDown(self):
        for p in list(self.desk.processes.values()):self.desk.kill(p)
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.temp.cleanup()
    def payload(self,key='test-key'):
        return {'tool':'should-ai-kill-us-all','action':'test','idempotency_key':key,'client_id':'test-agent'}
    def test_concurrent_duplicate_only_starts_one_job_and_survives_restart(self):
        body=self.payload()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            jobs=list(pool.map(lambda _:self.client.call('submit',body),range(5)))
        self.assertEqual(len({j['job_id'] for j in jobs}),1)
        completed=self.client.call('wait',{'job_id':jobs[0]['job_id'],'timeout_seconds':10})
        self.assertEqual(completed['state'],'succeeded')
        self.assertEqual(len(self.desk.runs()),1)
        reopened=Desk(self.folder)
        self.assertEqual(reopened.start(body['tool'],body['action'],request_key=body['idempotency_key'],client_id=body['client_id']),completed['job_id'])
        with self.assertRaises(AgentError) as e:self.client.call('submit',{**body,'action':'demo'})
        self.assertEqual(e.exception.code,'idempotency_conflict')
    def test_preview_does_not_start_and_strict_schema_rejects_injection(self):
        result=self.client.call('preview',{'tool':'Janus','action':'wos'})
        self.assertFalse(result['sent'])
        self.assertEqual(self.desk.runs(),[])
        for extra in ({'command':'echo arbitrary'},{'payload':{'command':'echo arbitrary'}}):
            with self.assertRaises(AgentError):self.client.call('submit',{**self.payload(),**extra})
        self.assertEqual(self.desk.runs(),[])
    def test_paid_replay_key_returns_original_when_wallet_later_blocked(self):
        body={'tool':'workbench','action':'log','payload':{'text':'synthetic module error'},'idempotency_key':'paid-key'}
        with patch('integracao.harness.painel.wallet_status',return_value={'paid_ready':True}),patch('integracao.jev_mcp.call',return_value={'choice':'dependencia','confidence':.99,'receipt':{'status':'success','attempt_id':'receipt-fixture','settled_nusd':1}}) as model:
            first=self.client.call('submit',body)
            final=self.client.call('wait',{'job_id':first['job_id'],'timeout_seconds':5})
            self.assertEqual(final['result']['receipt']['attempt_id'],'receipt-fixture')
            with patch('integracao.harness.painel.wallet_status',return_value={'paid_ready':False}):
                again=self.client.call('submit',body)
            self.assertEqual(first['job_id'],again['job_id'])
            self.assertEqual(model.call_count,1)
        with self.desk.connect() as db:
            stored=''.join(str(tuple(r)) for r in db.execute('SELECT * FROM agent_requests'))
        self.assertNotIn('synthetic module error',stored)
    def test_pause_respected_and_cancel_is_idempotent(self):
        self.client.call('configure',{'tool':'Janus','enabled':False})
        with self.assertRaises(AgentError) as e:self.client.call('submit',{'tool':'Janus','action':'wos','idempotency_key':'paused-key'})
        self.assertEqual(e.exception.code,'tool_paused')
        self.client.call('configure',{'tool':'Janus','enabled':True})
        with patch('integracao.harness.painel.test_commands',return_value=[([sys.executable,'-c','import time;time.sleep(30)'],self.folder)]):
            first=self.client.call('submit',{'tool':'Janus','action':'test','idempotency_key':'cancel-key'})
            self.client.call('cancel',{'job_id':first['job_id']})
            final=self.client.call('wait',{'job_id':first['job_id'],'timeout_seconds':5})
            again=self.client.call('cancel',{'job_id':first['job_id']})
        self.assertEqual(final['state'],'cancelled')
        self.assertEqual(again['state'],'cancelled')
    def test_compact_status_logs_pagination_and_old_job_lookup(self):
        with self.desk.connect() as db:
            for i in range(65):
                db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)',(f'old-{i}','Janus','wos','concluido',i,i,0,'abcde'*1000))
        state=self.client.call('status')
        self.assertEqual(len(state['recent_jobs']),10)
        self.assertNotIn('abcde',json.dumps(state))
        old=self.client.call('job',{'job_id':'old-0'})
        self.assertEqual(old['state'],'succeeded')
        log=self.client.call('logs',{'job_id':'old-0','offset':2,'limit':3})
        self.assertEqual(log['text'],'cde');self.assertEqual(log['next_offset'],5)
        self.assertTrue(log['has_more'])
    def test_mcp_returns_structured_errors_and_resource(self):
        with patch('integracao.harness.mcp.Client',return_value=self.client):
            result=handle({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'harness_run','arguments':self.payload()}})
            self.assertFalse(result['result']['isError'])
            job=result['result']['structuredContent']['data']
            self.client.call('wait',{'job_id':job['job_id'],'timeout_seconds':5})
            error=handle({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'harness_job','arguments':{'job_id':'absent'}}})
            self.assertTrue(error['result']['isError'])
            self.assertEqual(error['result']['structuredContent']['error']['code'],'not_found')
        guide=handle({'id':3,'method':'resources/read','params':{'uri':'harness://agent-guide'}})
        self.assertIn('idempotency_key',guide['result']['contents'][0]['text'])

    def test_restart_marks_interruption_without_reexecuting(self):
        body=self.payload('interrupted-key')
        with patch('threading.Thread.start'):
            identifier=self.desk.start(body['tool'],body['action'],request_key=body['idempotency_key'],client_id=body['client_id'])
        reopened=Desk(self.folder)
        with patch.object(reopened,'execute') as execute:
            same=reopened.start(body['tool'],body['action'],request_key=body['idempotency_key'],client_id=body['client_id'])
            self.assertEqual(identifier,same)
            execute.assert_not_called()
        self.assertEqual(reopened.runs()[0]['status'],'interrompido')

if __name__=='__main__':unittest.main()
