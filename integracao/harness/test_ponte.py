import json
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch
from pathlib import Path
from integracao.harness.ponte import Bridge, decide

class BridgeTests(unittest.TestCase):
    def test_missing_wallet_never_calls_model(self):
        with patch('integracao.harness.ponte.active_runtime',return_value=None),patch('integracao.harness.ponte.DB',Path('does-not-exist-wallet')),patch('integracao.harness.ponte.ask') as ask:
            with self.assertRaisesRegex(RuntimeError,'missing_wallet'): decide({'state':'x','questions':{'a':{}}})
            ask.assert_not_called()
    def test_auth_origin_and_call_cap(self):
        seen=[]
        with Bridge(limit=1,decision=lambda body:seen.append(body) or {'answers':{}}) as b:
            def post(token,origin=None):
                headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
                if origin: headers['Origin']=origin
                req=urllib.request.Request(b.url+'/systemone',data=b'{"state":"fixture","questions":{}}',headers=headers)
                return urllib.request.urlopen(req)
            for token,origin in [('wrong',None),(b.token,'https://example.com')]:
                with self.assertRaises(urllib.error.HTTPError) as e:post(token,origin)
                self.assertEqual(e.exception.code,403)
                e.exception.close()
            with post(b.token) as r:self.assertEqual(json.load(r),{'answers':{}})
            with self.assertRaises(urllib.error.HTTPError) as e:post(b.token)
            self.assertEqual(e.exception.code,400)
            e.exception.close()
            self.assertEqual(len(seen),1)

if __name__=='__main__': unittest.main()
