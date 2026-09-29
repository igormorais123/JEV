"""Offline upstream CLI over the real bridge; inference is explicitly simulated."""
import json
import os
import subprocess
import unittest
from integracao.harness.ponte import Bridge, ROOT
from integracao.harness.usar_ferramenta import command

class IntegrationTests(unittest.TestCase):
    def test_every_uses_bridge_despite_upstream_default_url(self):
        seen=[]
        def simulated(payload):
            seen.append(payload)
            return {'answers':{key:{'type':'noul','noul':.97} for key in payload['questions']},'usage':{}}
        with Bridge(decision=simulated) as bridge:
            from integracao.harness.painel import clean_env
            env=clean_env()
            env.update(TYPESAFE_API_KEY=bridge.token,TYPESAFE_BASE_URL=bridge.url.removesuffix('/v1'))
            args=['Does this function strip whitespace?',str(ROOT/'integracao/harness/fixtures'),'--yes','--no-cache','--json']
            p=subprocess.run(command('every',args),cwd=ROOT/'research/sources/every',env=env,capture_output=True,text=True,encoding='utf-8',timeout=20)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertGreaterEqual(len(seen),1)
            self.assertLessEqual(len(seen),8)
            self.assertEqual(json.loads(p.stdout)['meta']['units'],2)
    def test_cli_through_bridge(self):
        seen=[]
        def simulated(payload):
            seen.append(payload)
            answers={}
            for name,q in payload['questions'].items():
                criteria=q['criteria']; chosen='bug' if 'bug' in criteria else next(iter(criteria))
                answers[name]={'type':'choice','choice':chosen,'confidence':1,'probabilities':{k:float(k==chosen) for k in criteria}}
            return {'answers':answers,'usage':{'input_tokens':0,'output_tokens':0},'model':'simulated-contract-only'}
        with Bridge(decision=simulated) as bridge:
            env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('TOKEN','SECRET','API_KEY','OPENAI','ANTHROPIC','TYPESAFE','OPENROUTER'))}
            env.update(TYPESAFE_API_KEY=bridge.token,TYPESAFE_BASE_URL=bridge.url.removesuffix('/v1'))
            p=subprocess.run(['node',str(ROOT/'research/sources/jev-cli/dist/cli.js'),'classify','Erro ao abrir arquivo','--labels','bug,outro','--json','--provider','typesafe'],env=env,capture_output=True,text=True,encoding='utf-8',timeout=20)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout)['label'],'bug')
            self.assertEqual(len(seen),1)

    def test_mcp_process(self):
        requests=[{'jsonrpc':'2.0','id':1,'method':'initialize'}, {'jsonrpc':'2.0','id':2,'method':'tools/list'}, {'jsonrpc':'2.0','id':3,'method':'resources/read','params':{'uri':'harness://agent-guide'}}]
        p=subprocess.run([__import__('sys').executable,str(ROOT/'integracao/harness/mcp.py')],input='\n'.join(map(json.dumps,requests))+'\n',capture_output=True,text=True,encoding='utf-8',timeout=30)
        results=[json.loads(line) for line in p.stdout.splitlines()]
        self.assertEqual(len(results),3,p.stderr)
        names={t['name'] for t in results[1]['result']['tools']}
        self.assertTrue({'harness_catalog','harness_offline','harness_status','harness_test'}<=names)
        self.assertIn('idempotency_key',results[2]['result']['contents'][0]['text'])

if __name__=='__main__':unittest.main()
