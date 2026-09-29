"""Authenticated loopback adapter to the existing shared wallet, never a new payer."""
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from executor.shared import DB, ask, active_runtime


def decide(payload):
    runtime = active_runtime()
    wallet = runtime['db_path'] if runtime else DB
    if not wallet.is_file():
        raise RuntimeError('missing_wallet: recuperar a carteira historica; nenhuma chamada enviada')
    state = payload.get('state')
    questions = payload.get('questions')
    if not isinstance(questions, dict) or not 1 <= len(questions) <= 128:
        raise ValueError('invalid_questions')
    # System One accepts structured state; shared transport uses its lossless JSON form.
    if not isinstance(state, str):
        state = json.dumps(state, ensure_ascii=False)
    answers, receipt = ask(state, questions, consumer='tools')
    if answers is None:
        raise RuntimeError('shared_transport_'+receipt.get('status','unavailable'))
    return {'answers': answers, 'model': receipt.get('model_resolved'),
            'usage': receipt.get('usage') or {}, 'receipt': receipt}


class Bridge:
    def __init__(self, limit=8, decision=decide):
        self.token = secrets.token_urlsafe(32)
        self.remaining = limit
        self.lock = threading.Lock()
        outer = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                if self.path not in ('/v1/systemone','/systemone'):
                    self.send_error(404); return
                if self.headers.get('Origin') or not secrets.compare_digest(
                    self.headers.get('Authorization',''), 'Bearer '+outer.token):
                    self.send_error(403); return
                try:
                    size = int(self.headers.get('Content-Length','0'))
                    if not 0 < size <= 90000: raise ValueError('invalid_size')
                    payload=json.loads(self.rfile.read(size))
                    if not isinstance(payload,dict): raise ValueError('invalid_payload')
                    with outer.lock:
                        if outer.remaining <= 0: raise RuntimeError('session_call_limit')
                        outer.remaining -= 1
                    result=decision(payload)
                    code=200
                except Exception as error:
                    # Never return provider bodies or credentials to third-party clients.
                    result={'error':type(error).__name__, 'message':'JEV indisponivel ou limite atingido. Consulte jev_status.'}
                    code=400  # Nonretryable; no automatic second paid request.
                body=json.dumps(result,ensure_ascii=False).encode()
                self.send_response(code)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers(); self.wfile.write(body)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.url=f'http://127.0.0.1:{self.server.server_port}/v1'
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
    def __enter__(self):
        self.thread.start(); return self
    def __exit__(self,*args):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
