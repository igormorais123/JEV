"""Ponte OpenAI → Jev: deixa o OmniRoute (e qualquer cliente OpenAI) usar o Jev como "modelo".

O Jev não conversa: responde perguntas fechadas sobre um texto pela API de decisões. O OmniRoute
só roteia chat no formato OpenAI. Esta ponte traduz um para o outro:

    POST /{typesafe|openrouter}/v1/chat/completions
    {"model": "jev-1.13", "messages": [{"role": "user", "content": "<JSON do contrato>"}]}

O conteúdo da última mensagem do usuário é o contrato do Jev em JSON:

    {"state": "texto ou objeto", "questions": {"nome": {"type": "choice", ...}}}
    {"state": "...", "question": {...}}          # atalho: uma pergunta, respondida como "decisao"

A resposta é um chat.completion cujo `content` é o JSON das respostas tipadas. O prefixo do
caminho escolhe o provedor; a chave vem no `Authorization` que o OmniRoute envia (ela fica
guardada, criptografada, no banco do OmniRoute). Gasto, teto, cache e registro passam pelo
mesmo núcleo que o Hermes usa: um só caminho financeiro.

Escuta só no IP da ponte Docker (172.17.0.1:20145), liberado no firewall apenas para a sub-rede
Docker. Erros saem no formato de erro da OpenAI, com o status que faz o OmniRoute tentar o
próximo provedor do combo (502 em falha de rota, 429 em limite, 400 em contrato inválido).
"""
import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jev_hermes import nucleo  # noqa: E402

ENDERECO = os.environ.get('JEV_PONTE_ENDERECO', '172.17.0.1')
PORTA = int(os.environ.get('JEV_PONTE_PORTA', '20145'))
MODELOS = ('jev-1.13', 'jev-latest')
AJUDA = ('O conteúdo da última mensagem do usuário deve ser JSON: {"state": ..., "questions": '
         '{"nome": {"type": "choice", "instructions": "...", "criteria": {"opcao": "descricao", ...}}}} '
         'ou {"state": ..., "question": {...}}. Tipos: choice, score (criteria em lista), noul.')


def texto_da_mensagem(mensagem):
    conteudo = mensagem.get('content')
    if isinstance(conteudo, list):
        return ''.join(p.get('text', '') for p in conteudo if isinstance(p, dict))
    return conteudo if isinstance(conteudo, str) else ''


def contrato(corpo):
    """(estado, perguntas) a partir do corpo de chat. ValueError com explicação se não der."""
    usuario = [m for m in corpo.get('messages') or [] if m.get('role') == 'user']
    if not usuario:
        raise ValueError('nenhuma mensagem de usuário. ' + AJUDA)
    texto = texto_da_mensagem(usuario[-1]).strip()
    if texto.startswith('```'):
        texto = texto.strip('`').split('\n', 1)[-1]
    try:
        dado = json.loads(texto)
    except ValueError:
        raise ValueError('a mensagem não é JSON. ' + AJUDA)
    if not isinstance(dado, dict) or 'state' not in dado:
        raise ValueError('falta "state". ' + AJUDA)
    perguntas = dado.get('questions') or ({'decisao': dado['question']} if 'question' in dado else None)
    if not isinstance(perguntas, dict) or not perguntas:
        raise ValueError('falta "questions". ' + AJUDA)
    return dado['state'], perguntas


def rota(caminho, cabecalhos):
    partes = [p for p in caminho.split('/') if p]
    provedor = partes[0] if partes and partes[0] in nucleo.PROVEDORES else None
    autorizacao = cabecalhos.get('Authorization') or ''
    chave = autorizacao[7:].strip() if autorizacao.lower().startswith('bearer ') else ''
    return provedor, chave


class Ponte(BaseHTTPRequestHandler):
    server_version = 'JevPonte/1.0'

    def log_message(self, *_):
        pass  # o registro é o do núcleo, sem conteúdo

    def _json(self, status, dado):
        corpo = json.dumps(dado, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _erro(self, status, mensagem, tipo='invalid_request_error'):
        self._json(status, {'error': {'message': mensagem, 'type': tipo, 'code': status}})

    def do_GET(self):
        if self.path.rstrip('/').endswith('/models'):
            self._json(200, {'object': 'list', 'data': [
                {'id': m, 'object': 'model', 'created': 1789862400, 'owned_by': 'typesafe'} for m in MODELOS]})
        elif self.path.rstrip('/').endswith('/health'):
            self._json(200, {'ok': True, 'desligado': nucleo.desligado()})
        else:
            self._erro(404, 'rota desconhecida')

    def do_POST(self):
        provedor, chave = rota(self.path, self.headers)
        if not self.path.rstrip('/').endswith('/chat/completions'):
            return self._erro(404, 'use /{typesafe|openrouter}/v1/chat/completions')
        if not provedor or not chave:
            return self._erro(401, 'caminho sem provedor ou sem chave Bearer', 'authentication_error')
        try:
            corpo = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
            estado, perguntas = contrato(corpo)
        except ValueError as erro:
            return self._erro(400, str(erro))
        respostas, detalhe = nucleo.perguntar(estado, perguntas, origem=f'omniroute-{provedor}',
                                              timeout=20, limite=nucleo.LIMITE_MAXIMO,
                                              rota=[(provedor, chave)])
        if respostas is None:
            erro = detalhe.get('erro') or 'sem resposta'
            status = 429 if ('429' in erro or 'teto' in erro) else 400 if erro.startswith(('http 4', 'contrato', 'estado')) else 502
            return self._erro(status, f'Jev: {erro}', 'rate_limit_error' if status == 429 else 'api_error')
        conteudo = json.dumps({'answers': respostas, 'cache': bool(detalhe.get('cache')),
                               'custo_usd': detalhe.get('custo_usd')}, ensure_ascii=False)
        uso = detalhe.get('uso') or {}
        entrada = uso.get('input_tokens') or uso.get('prompt_tokens') or 0
        saida = uso.get('output_tokens') or uso.get('completion_tokens') or 0
        identificador = 'chatcmpl-jev-' + uuid.uuid4().hex[:20]
        modelo = detalhe.get('modelo_resolvido') or corpo.get('model') or MODELOS[0]
        if corpo.get('stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            base = {'id': identificador, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': modelo}
            for pedaco in ({**base, 'choices': [{'index': 0, 'delta': {'role': 'assistant', 'content': conteudo},
                                                 'finish_reason': None}]},
                           {**base, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}],
                            'usage': {'prompt_tokens': entrada, 'completion_tokens': saida,
                                      'total_tokens': entrada + saida}}):
                self.wfile.write(f'data: {json.dumps(pedaco, ensure_ascii=False)}\n\n'.encode('utf-8'))
            self.wfile.write(b'data: [DONE]\n\n')
            return
        self._json(200, {'id': identificador, 'object': 'chat.completion', 'created': int(time.time()),
                         'model': modelo,
                         'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': conteudo},
                                      'finish_reason': 'stop'}],
                         'usage': {'prompt_tokens': entrada, 'completion_tokens': saida,
                                   'total_tokens': entrada + saida}})


def main():
    servidor = ThreadingHTTPServer((ENDERECO, PORTA), Ponte)
    servidor.daemon_threads = True
    servidor.serve_forever()


if __name__ == '__main__':
    main()
