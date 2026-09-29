"""Agent SDK: no UI, no provider secrets, no implicit inference retries."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from integracao.harness.agent_layer import API_VERSION, AgentError

ROOT=Path(__file__).resolve().parents[2]
BASE='http://127.0.0.1:8767'


class Client:
    def __init__(self,base=BASE):
        parts=urlsplit(base)
        if parts.scheme!='http' or parts.hostname!='127.0.0.1' or parts.username or parts.path not in ('','/') or parts.query or parts.fragment:
            raise ValueError('Only a local loopback harness endpoint is supported.')
        self.base=base.rstrip('/')
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _request(self,path,body=None,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Harness-Token']=token
        request=urllib.request.Request(self.base+path,data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,headers=headers)
        try:
            with self.opener.open(request,timeout=25) as response:return json.load(response)
        except urllib.error.HTTPError as e:
            try:data=json.load(e)
            except (ValueError,UnicodeError):data={}
            finally:e.close()
            info=data.get('error')
            if isinstance(info,dict):raise AgentError(info.get('code','http_error'),info.get('message','HTTP error'),info.get('next_action','inspect_status'),info.get('retryable',False))
            raise AgentError('protocol_error','Resposta incompatível do serviço local.','bootstrap')
        except (urllib.error.URLError,TimeoutError,OSError):
            raise AgentError('transport_unavailable','Serviço local indisponível ou resposta perdida. Não reenviar com nova chave.','bootstrap_then_retry_same_key',True)
        except (ValueError,UnicodeError):raise AgentError('protocol_error','Resposta não é JSON válido.','inspect_service')

    def session(self):
        result=self._request('/api/session')
        if result.get('service')!='jev-harness' or result.get('api_version')!=API_VERSION:
            raise AgentError('incompatible_service','Porta ocupada por serviço incompatível.','restart_correct_service')
        return result

    def call(self,operation,arguments=None):
        session=self.session()
        result=self._request('/api/v1/'+operation,arguments or {},session['token'])
        if not result.get('ok') or result.get('api_version')!=API_VERSION:
            raise AgentError('protocol_error','Envelope inesperado.','inspect_service')
        return result['data']

    def bootstrap(self):
        try:
            self.session()
            return {'service':'jev-harness','ready':True,'started':False,'url':self.base,'api_version':API_VERSION}
        except AgentError as e:
            if e.code!='transport_unavailable':raise
        if self.base!=BASE:raise AgentError('custom_endpoint_offline','Inicialização automática usa a porta padrão 8767.','start_service')
        folder=ROOT/'integracao/estado'
        folder.mkdir(parents=True,exist_ok=True)
        env={k:v for k,v in os.environ.items() if not any(x in k.upper() for x in ('API_KEY','TOKEN','SECRET','OPENAI','ANTHROPIC','TYPESAFE','OPENROUTER'))}
        env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
        with (folder/'harness-bootstrap.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,str(ROOT/'integracao/harness/painel.py')],cwd=ROOT,env=env,
                stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for _ in range(50):
            try:
                self.session()
                return {'service':'jev-harness','ready':True,'started':True,'url':self.base,'api_version':API_VERSION}
            except AgentError as e:
                if e.code!='transport_unavailable':raise
            if child.poll() is not None:break
            time.sleep(.1)
        raise AgentError('bootstrap_failed','O servidor não ficou pronto; consulte integracao/estado/harness-bootstrap.log.','inspect_bootstrap_log')
