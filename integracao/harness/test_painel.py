import json
from pathlib import Path
import tempfile
import threading
import time
import sys
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
from integracao.harness.painel import Desk, make_server


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.desk=Desk(Path(self.tmp.name))
        self.server=make_server(self.desk,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,path,body=None,headers=None):
        req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers or {})
        with urllib.request.urlopen(req) as r:return json.load(r)
    def test_cross_origin_and_missing_token_cannot_execute(self):
        for headers in ({},{'Origin':'https://example.com','X-Harness-Token':'fake'}):
            with self.assertRaises(urllib.error.HTTPError) as err:self.request('/api/run',{'tool':'Janus','action':'wos'},headers)
            self.assertEqual(err.exception.code,403);err.exception.close()
        self.assertEqual(self.desk.runs(),[])
    def test_unknown_action_and_paused_tool_cannot_execute(self):
        with self.assertRaises(ValueError):self.desk.start('Janus','shell',{'command':'anything'})
        self.desk.preference('Janus',False)
        with self.assertRaises(ValueError):self.desk.start('Janus','wos')
    def test_paid_operation_cannot_bypass_readiness(self):
        with patch('integracao.harness.painel.wallet_status',return_value={'paid_ready':False}):
            with self.assertRaises(ValueError):self.desk.start('workbench','log',{'text':'fixture'})
        self.assertEqual(self.desk.runs(),[])
    def test_real_replay_persists_result(self):
        result=self.request('/api/state')
        self.assertEqual(len(result['tools']),16)
        job=self.request('/api/run',{'tool':'Janus','action':'wos'},{'X-Harness-Token':result['token']})['id']
        for _ in range(100):
            row=next(r for r in self.desk.runs() if r['id']==job)
            if row['status']!='executando':break
            time.sleep(.1)
        self.assertEqual(row['status'],'concluido',row['output'])
        self.assertIn('DO NOT ROUTE',row['output'])
        reopened=Desk(Path(self.tmp.name))
        self.assertEqual(reopened.runs()[0]['id'],job)
    def test_inference_input_not_stored(self):
        with patch('integracao.jev_mcp.call',return_value={'choice':'erro','receipt':{'status':'success'}}):
            with self.desk.connect() as db:
                db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)',('fixture','workbench','log','executando',time.time(),None,None,''))
            self.desk.execute('fixture','workbench','log',{'text':'UNIQUE_PRIVATE_INPUT'})
        self.assertNotIn('UNIQUE_PRIVATE_INPUT',json.dumps(self.desk.runs()))

    def test_cancel_stops_owned_process(self):
        with patch('integracao.harness.painel.test_commands',return_value=[([sys.executable,'-c','import time; time.sleep(30)'],Path(self.tmp.name))]):
            identity=self.desk.start('Janus','test')
            for _ in range(100):
                if identity in self.desk.processes:break
                time.sleep(.01)
            self.desk.cancel(identity)
            for _ in range(100):
                row=self.desk.runs()[0]
                if row['status']=='cancelado':break
                time.sleep(.02)
        self.assertEqual(row['status'],'cancelado')
        self.assertNotIn(identity,self.desk.processes)

if __name__=='__main__':unittest.main()
