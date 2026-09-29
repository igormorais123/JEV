"""Local Jev control desk. Fixed operations, persistent runs, shared inference wallet."""
import argparse
from contextlib import contextmanager
import json
import hashlib
import os
from pathlib import Path
import secrets
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from integracao.apoio import status as wallet_status
from integracao.jev_router.redacao import limpar
from integracao.harness.usar_ferramenta import SOURCES
from integracao.harness.agent_layer import AgentError, dispatch as agent_dispatch, error_body, API_VERSION

HERE = Path(__file__).parent
DATA = ROOT / 'integracao/estado/harness'
NPM = shutil.which('npm.cmd') or shutil.which('npm')
META = {
 'jev-cli': ('Jev CLI','Apoio ao Codex','Classificar, extrair e verificar pelo terminal.'),
 'every': ('Every','Apoio ao Codex','Inspecionar funções e apoiar a análise de código.'),
 'jev-review': ('Jev Review','Apoio ao Codex','Revisar alterações com julgamentos estruturados.'),
 'Janus': ('Janus','Avaliação','Comparar qualidade e custo do roteamento de modelos.'),
 'jevcal': ('jevcal','Avaliação','Calibrar limites de confiança em experimentos.'),
 'jev-rerank-bench': ('Rerank Bench','Avaliação','Medir a ordenação de documentos para contexto.'),
 'jev-search': ('Jev Search','Aplicações','Pesquisar e organizar resultados da web.'),
 'jev-ultrafast': ('Ultrafast','Aplicações','Experimentar agentes que operam o navegador.'),
 'system-one-adapter-python': ('System One Adapter','Infraestrutura','Conectar interfaces de avaliação em Python.'),
 'openjev': ('OpenJev / SemIf','Infraestrutura','Explorar decisões com modelos locais.'),
 'pi-model-router': ('Pi Model Router','Extensões Pi','Escolher modelos dentro do agente Pi.'),
 'pi-warden': ('Pi Warden','Extensões Pi','Controlar operações dentro do agente Pi.'),
 'jevstudio': ('Jev Studio','Laboratório','Montar e observar experiências em uma interface visual.'),
 'heist-one': ('HEIST ONE','Laboratório','Observar agentes em um jogo demonstrativo.'),
 'Jeeves': ('Jeeves','Aplicações','Operar um bot com banco e integrações de comunidade.'),
 'should-ai-kill-us-all': ('News experiment','Laboratório','Demonstrar classificação de notícias.')}


def clean_env():
    env = {k:v for k,v in os.environ.items() if not any(x in k.upper() for x in
           ('API_KEY','TOKEN','SECRET','OPENAI','ANTHROPIC','TYPESAFE','OPENROUTER'))}
    return {**env, 'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8','CI':'1'}


def test_commands(tool):
    d = SOURCES / tool
    py = str(d / '.venv/Scripts/python.exe')
    if tool == 'jevstudio':
        return [([sys.executable, str(d/'tests'/f'test_{s}.py')], d) for s in
                ('funis','juiz','cadeiras','piloto','roteador','endereco')]
    if tool == 'should-ai-kill-us-all':
        return [(['node',str(HERE/'test_news.mjs')], ROOT)]
    if tool == 'Jeeves':
        script=ROOT/'tmp/harness/jeeves-test.cmd'
        if not script.is_file(): raise ValueError('Ambiente MSVC x64 indisponível; consulte o relatório.')
        return [(['cmd.exe','/d','/c',str(script)],d)]
    if tool in ('every','Janus','jevcal','jev-rerank-bench','jev-ultrafast','openjev','system-one-adapter-python'):
        args=[py,'-m','pytest','-q','--tb=short']
        if tool == 'system-one-adapter-python': args += ['--allowed-hosts=^127\\.0\\.0\\.1$,^::1$,^localhost$']
        return [(args,d)]
    return [([NPM,'run','check' if tool=='jev-review' else 'test'],d)]


class Desk:
    def __init__(self, folder=DATA):
        folder.mkdir(parents=True,exist_ok=True)
        self.db=folder/'painel.sqlite3'
        self.lock=threading.RLock()
        self.processes={}
        self.cancelled=set()
        with self.connect() as db:
            db.executescript('CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, tool TEXT, action TEXT, status TEXT, started REAL, finished REAL, code INTEGER, output TEXT); CREATE TABLE IF NOT EXISTS prefs(tool TEXT PRIMARY KEY, enabled INTEGER);')
            db.executescript('CREATE TABLE IF NOT EXISTS agent_requests(request_key TEXT PRIMARY KEY, request_hash TEXT NOT NULL, job_id TEXT NOT NULL UNIQUE, client_id TEXT NOT NULL); CREATE TABLE IF NOT EXISTS agent_results(job_id TEXT PRIMARY KEY, result_json TEXT NOT NULL);')
            db.execute("UPDATE runs SET status='interrompido', finished=? WHERE status IN ('executando','cancelando')",(time.time(),))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.db,timeout=10)
        db.row_factory=sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def runs(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT runs.*,agent_requests.client_id FROM runs LEFT JOIN agent_requests ON agent_requests.job_id=runs.id ORDER BY started DESC LIMIT 60')]

    def catalog(self):
        report=json.loads((HERE/'resultados.json').read_text(encoding='utf-8'))
        with self.connect() as db: prefs=dict(db.execute('SELECT tool,enabled FROM prefs'))
        rows=[]
        for r in report['systems']:
            tool=r['system']; name,group,description=META[tool]
            actions=[{'id':'test','label':'Executar testes','paid':False}]
            if tool=='Janus': actions += [{'id':'banking77','label':'Replay Banking77','paid':False},{'id':'wos','label':'Replay WOS','paid':False}]
            if tool=='jevcal': actions += [{'id':'demo','label':'Gerar demonstração','paid':False}]
            if tool=='jev-cli': actions += [{'id':'live','label':'Avaliar 7 casos reais','paid':True}]
            if tool=='every': actions += [{'id':'sample','label':'Analisar código de exemplo','paid':True}]
            if tool in ('jev-cli','every'): actions += [{'id':'help','label':'Consultar comandos','paid':False}]
            rows.append({**r,'name':name,'group':group,'description':description,
                'enabled':bool(prefs.get(tool,1)), 'installed':(SOURCES/tool).is_dir(),'actions':actions})
        return rows

    def preference(self,tool,enabled):
        if tool not in META or type(enabled) is not bool: raise ValueError('Preferência inválida.')
        with self.connect() as db: db.execute('INSERT OR REPLACE INTO prefs VALUES(?,?)',(tool,int(enabled)))

    def validate_operation(self,tool,action,payload=None):
        payload={} if payload is None else payload
        if not isinstance(tool,str) or not isinstance(action,str) or not isinstance(payload,dict):
            raise AgentError('invalid_request','Operação ou payload inválido.','read_manifest')
        if tool=='workbench':
            if action not in ('log','evidence','context'): raise ValueError('Operação desconhecida.')
            if set(payload)!={'text'} or not isinstance(payload['text'],str) or not 1<=len(payload['text'])<=12000:
                raise ValueError('Informe um texto de até 12.000 caracteres.')
            paid=True
        else:
            row=next((r for r in self.catalog() if r['system']==tool),None)
            if not row: raise AgentError('unknown_tool','Ferramenta desconhecida.','read_manifest')
            if not row['enabled']: raise AgentError('tool_paused','Ferramenta pausada.','configure_if_requested')
            if not row['installed']: raise AgentError('missing_installation','Fontes ausentes.','inspect_installation')
            match=next((a for a in row['actions'] if a['id']==action),None)
            if not match: raise ValueError('Operação desconhecida.')
            if payload: raise AgentError('invalid_request','Esta operação não aceita payload.','read_manifest')
            paid=match['paid']
        wallet=wallet_status() if paid else None
        if paid and not wallet.get('paid_ready'): raise AgentError('wallet_unavailable','Carteira indisponível: '+wallet.get('reason','unknown'),'inspect_wallet')
        return {'tool':tool,'action':action,'ready':True,'paid':paid,'sent':False,
                'wallet':wallet,'note':'Preview não reserva saldo nem garante capacidade futura. A execução revalida tudo.'}

    def start(self,tool,action,payload=None,*,request_key=None,client_id='html'):
        payload={} if payload is None else payload
        fingerprint=hashlib.sha256(json.dumps({'tool':tool,'action':action,'payload':payload,'client_id':client_id},sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        with self.lock:
            with self.connect() as db:
                if request_key:
                    previous=db.execute('SELECT request_hash,job_id FROM agent_requests WHERE request_key=?',(request_key,)).fetchone()
                    if previous:
                        if previous['request_hash']!=fingerprint:raise AgentError('idempotency_conflict','Chave já usada com outro pedido.','inspect_original_request')
                        return previous['job_id']
                self.validate_operation(tool,action,payload)
                if db.execute("SELECT COUNT(*) FROM runs WHERE status IN ('executando','cancelando')").fetchone()[0]>=2:
                    raise AgentError('capacity_exceeded','Duas operações estão em andamento.','wait_then_retry_same_key',True)
                if db.execute("SELECT 1 FROM runs WHERE tool=? AND status IN ('executando','cancelando')",(tool,)).fetchone():
                    raise AgentError('tool_busy','Esta ferramenta já está em execução.','wait_then_retry_same_key',True)
                identity=secrets.token_hex(8)
                db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)',(identity,tool,action,'executando',time.time(),None,None,''))
                if request_key:db.execute('INSERT INTO agent_requests VALUES(?,?,?,?)',(request_key,fingerprint,identity,client_id))
            threading.Thread(target=self.execute,args=(identity,tool,action,payload),daemon=True).start()
        return identity

    def append(self,identity,text):
        text=limpar(text)[0]
        with self.connect() as db:
            db.execute('UPDATE runs SET output=substr(output || ?, -60000) WHERE id=?',(text,identity))

    def save_result(self,identity,result):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO agent_results VALUES(?,?)',(identity,json.dumps(result,ensure_ascii=False)))

    def execute(self,identity,tool,action,payload):
        code=1
        try:
            if tool=='workbench':
                from integracao.jev_mcp import call
                result=call('jev_assist',{'task':action,'state':payload['text']})
                # Input is never persisted in the operation history.
                self.append(identity,json.dumps(result,ensure_ascii=False,indent=2))
                receipt=result.get('receipt',{})
                self.save_result(identity,{'task':action,'choice':result.get('choice'),'confidence':result.get('confidence'),
                    'receipt':{k:receipt[k] for k in ('attempt_id','status','settled_nusd','cost_source','latency_ms','usage','provider','model','evidence_level','sent') if k in receipt},
                    'review_required':True})
                code=0 if result.get('choice') is not None and receipt.get('status')=='success' else 1
            else:
                if action=='test': commands=test_commands(tool)
                elif action=='live': commands=[([sys.executable,str(HERE/'avaliar_ao_vivo.py')],ROOT)]
                elif action=='sample': commands=[([sys.executable,str(HERE/'usar_ferramenta.py'),'every','--','Does this function strip whitespace from a string?',str(HERE/'fixtures'),'--yes','--no-cache','--json','--above','0.5'],ROOT)]
                elif action=='help': commands=[([sys.executable,str(HERE/'usar_ferramenta.py'),tool,'--','--help'],ROOT)]
                else:
                    args=['measure','--task',action] if tool=='Janus' else ['demo']
                    commands=[([sys.executable,str(HERE/'usar_ferramenta.py'),tool,'--',*args],ROOT)]
                code=0
                for cmd,cwd in commands:
                    with self.lock:
                        if identity in self.cancelled: break
                        p=subprocess.Popen(cmd,cwd=cwd,env=clean_env(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                            text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                        self.processes[identity]=p
                    try:
                        output,_=p.communicate(timeout=360)
                        self.append(identity,output+'\n')
                        code=code or p.returncode or 0
                        if p.returncode==0 and action in ('sample','live'):
                            # These operations use only our frozen synthetic fixtures.
                            try:
                                parsed=json.loads(output[output.index('{'):])
                                self.save_result(identity,{'upstream':parsed,'evidence':'live_synthetic',
                                    'billing_authority':'shared_wallet','native_cost_is_authoritative':False})
                            except ValueError:pass
                        elif p.returncode==0 and action in ('wos','banking77'):
                            verdict=re.search(r'VERDICT:\s+(DO NOT ROUTE|ROUTE)',output)
                            if verdict:self.save_result(identity,{'verdict':verdict.group(1),'evidence':'historical_replay','new_model_calls':0})
                    except subprocess.TimeoutExpired:
                        self.kill(p)
                        output,_=p.communicate()
                        self.append(identity,output+'\nTempo máximo de 6 minutos atingido.\n')
                        code=124
                        break
                    finally:
                        with self.lock: self.processes.pop(identity,None)
            state='concluido' if code==0 else 'falhou'
        except Exception as e:
            self.append(identity,'Operação interrompida: '+type(e).__name__+'\n')
            state='falhou'
        with self.lock:
            if identity in self.cancelled: state='cancelado'
            with self.connect() as db:
                db.execute('UPDATE runs SET status=?,finished=?,code=? WHERE id=?',(state,time.time(),code,identity))
            self.cancelled.discard(identity)

    @staticmethod
    def kill(p):
        if p.poll() is not None: return
        if os.name=='nt': subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        else: p.kill()

    def cancel(self,identity):
        with self.lock:
            with self.connect() as db:
                row=db.execute('SELECT tool,status FROM runs WHERE id=?',(identity,)).fetchone()
                if not row or row['status']!='executando': raise ValueError('Execução não está ativa.')
                if row['tool']=='workbench': raise ValueError('Inferência enviada: aguarde o recibo financeiro.')
                db.execute("UPDATE runs SET status='cancelando' WHERE id=?",(identity,))
            self.cancelled.add(identity)
            p=self.processes.get(identity)
            if p:self.kill(p)


def make_server(desk,port=8767):
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def send(self,code,body,kind='application/json; charset=utf-8'):
            if not isinstance(body,bytes): body=json.dumps(body,ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers(); self.wfile.write(body)
        def trusted(self,mutate=False):
            host=f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host')!=host: return False
            origin=self.headers.get('Origin')
            if origin and origin!='http://'+host:return False
            if self.headers.get('Sec-Fetch-Site')=='cross-site':return False
            return not mutate or secrets.compare_digest(self.headers.get('X-Harness-Token',''),token)
        def do_GET(self):
            if not self.trusted():self.send(403,{'error':'Origem não autorizada.'});return
            path=urlsplit(self.path).path
            try:
                if path=='/api/session':self.send(200,{'service':'jev-harness','api_version':API_VERSION,'token':token});return
                if path in ('/api/v1/manifest','/api/v1/status'):
                    self.send(200,{'api_version':API_VERSION,'ok':True,'data':agent_dispatch(desk,path.rsplit('/',1)[-1],{})});return
                if path=='/api/state':
                    self.send(200,{'tools':desk.catalog(),'runs':desk.runs(),'wallet':wallet_status(),'token':token});return
                files={'/':HERE/'web/index.html','/app.js':HERE/'web/app.js','/style.css':HERE/'web/style.css',
                       '/relatorio':HERE/'RELATORIO.md','/guia':HERE/'README.md','/agents':HERE/'AGENT-GUIDE.md'}
                if path not in files:self.send(404,{'error':'Não encontrado.'});return
                mime='text/html' if path=='/' else 'text/javascript' if path.endswith('.js') else 'text/css' if path.endswith('.css') else 'text/plain'
                self.send(200,files[path].read_bytes(),mime+'; charset=utf-8')
            except Exception as e:self.send(500,error_body(e) if path.startswith('/api/v1/') else {'error':'Não foi possível ler o estado local.'})
        def do_POST(self):
            if not self.trusted(True):
                self.send(403,error_body(AgentError('session_rejected','Sessão inválida.','bootstrap_then_retry_same_key')) if self.path.startswith('/api/v1/') else {'error':'Atualize a página para renovar a sessão.'})
                return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=70000: raise ValueError('Pedido excede o limite.')
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict):raise ValueError('Pedido inválido.')
                if self.path.startswith('/api/v1/'):
                    result=agent_dispatch(desk,self.path.removeprefix('/api/v1/'),body)
                    self.send(200,{'api_version':API_VERSION,'ok':True,'data':result});return
                if self.path=='/api/run':result={'id':desk.start(body.get('tool'),body.get('action'),body.get('payload'))}
                elif self.path=='/api/cancel':desk.cancel(body.get('id'));result={'ok':True}
                elif self.path=='/api/preference':desk.preference(body.get('tool'),body.get('enabled'));result={'ok':True}
                else:self.send(404,{'error':'Operação desconhecida.'});return
                self.send(200,result)
            except ValueError as e:self.send(400,error_body(e) if self.path.startswith('/api/v1/') else {'error':str(e)})
            except Exception as e:self.send(500,error_body(e) if self.path.startswith('/api/v1/') else {'error':'Falha local; nenhuma repetição automática foi feita.'})
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8767)
    args=parser.parse_args()
    DATA.mkdir(parents=True,exist_ok=True)
    # One owner per local history: a second server must not reset running jobs.
    owner=(DATA/'server.lock').open('a+b')
    owner.seek(0); owner.write(b'1'); owner.flush(); owner.seek(0)
    if os.name=='nt':
        import msvcrt
        try: msvcrt.locking(owner.fileno(),msvcrt.LK_NBLCK,1)
        except OSError: raise SystemExit('O painel já está em execução nesta máquina.')
    desk=Desk()
    server=make_server(desk,args.port)
    print(f'Jev Harness: http://127.0.0.1:{server.server_port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        for p in list(desk.processes.values()):desk.kill(p)
        server.server_close()
        owner.close()

if __name__=='__main__':main()
