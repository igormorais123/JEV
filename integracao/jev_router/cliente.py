"""Chamada ao endpoint de decisões do Jev, no formato que um hook pode usar.

Diferenças em relação ao `executor/runner.py`, que serve ao experimento:

- **Falha para o lado aberto.** Se a chave falta, a rede cai, o teto estoura ou a resposta vem
  fora do contrato, a função devolve `None` e o fluxo de trabalho segue como se o roteador não
  existisse. Um roteador de economia que derruba a sessão custa mais do que economiza.
- **Timeout curto.** O hook roda entre a tecla e a resposta; o padrão é de segundos.
- **Entrada truncada**, para que o custo máximo por chamada seja conhecido antes do envio.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from . import orcamento, redacao

URL = 'https://openrouter.ai/api/alpha/decisions'
MODELO = 'typesafe/jev-1.13'
TIMEOUT_PADRAO = 6.0

RAIZ_DO_PROJETO = Path(__file__).resolve().parents[2]


def chave():
    """Lê do ambiente ou do .env do projeto. O valor nunca é registrado nem devolvido em log."""
    if os.environ.get('OPENROUTER_API_KEY'):
        return os.environ['OPENROUTER_API_KEY']
    env = RAIZ_DO_PROJETO / '.env'
    if env.exists():
        for linha in env.read_text(encoding='utf-8', errors='replace').splitlines():
            if linha.strip().startswith('OPENROUTER_API_KEY='):
                valor = linha.split('=', 1)[1].strip().strip('"').strip("'")
                if valor:
                    return valor
    return None


def transporte_http(url, cabecalhos, corpo, timeout):
    requisicao = urllib.request.Request(
        url, data=json.dumps(corpo, ensure_ascii=False).encode('utf-8'),
        headers=cabecalhos, method='POST')
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return resposta.status, json.loads(resposta.read().decode('utf-8'))
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read().decode('utf-8'))
        except (ValueError, OSError):
            return erro.code, {}
    except Exception:
        return 0, {}


def perguntar(estado, perguntas, *, timeout=TIMEOUT_PADRAO, transporte=None, origem='hook'):
    """Faz uma chamada e devolve o mapa de respostas, ou None se qualquer coisa der errado.

    Devolve também o custo reportado pelo provedor, que é o valor autoritativo da cobrança.
    """
    transporte = transporte or transporte_http
    permitido, motivo = orcamento.pode_gastar()
    if not permitido:
        return None, {'erro': motivo}
    api_key = chave()
    if not api_key:
        return None, {'erro': 'sem OPENROUTER_API_KEY'}

    # A redação vem antes da truncagem: mascarar encurta o texto, e o que interessa é que
    # nenhuma credencial atravesse a fronteira desta máquina.
    estado, mascarados = redacao.limpar(estado)
    estado = estado[:orcamento.LIMITE_DE_CARACTERES]
    corpo = {'model': MODELO, 'state': estado, 'questions': perguntas}
    status, resposta = transporte(
        URL, {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json',
              'User-Agent': 'jev-router/1.0'}, corpo, timeout)

    custo = ((resposta.get('usage') or {}).get('cost')) if isinstance(resposta, dict) else None
    orcamento.registrar(custo if custo is not None else 0.0, origem=origem, http=status,
                        modelo=MODELO, caracteres=len(estado), mascarados=mascarados,
                        custo_reportado=custo is not None)

    if status != 200 or not isinstance(resposta, dict):
        return None, {'erro': f'http {status}', 'custo_usd': custo}
    respostas = resposta.get('answers')
    if not isinstance(respostas, dict) or set(respostas) != set(perguntas):
        return None, {'erro': 'resposta fora do contrato', 'custo_usd': custo}
    for chave_da_pergunta, resposta_unica in respostas.items():
        if not isinstance(resposta_unica, dict) or resposta_unica.get('choice') is None:
            return None, {'erro': f'{chave_da_pergunta} sem escolha', 'custo_usd': custo}
    return respostas, {'custo_usd': custo, 'http': status}
