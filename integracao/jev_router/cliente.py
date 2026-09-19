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
import sys
import urllib.error
import urllib.request
from pathlib import Path

from . import orcamento, redacao

URL = 'https://openrouter.ai/api/alpha/decisions'
MODELO = 'typesafe/jev-1.13'
TIMEOUT_PADRAO = 6.0

RAIZ_DO_PROJETO = Path(__file__).resolve().parents[2]
if str(RAIZ_DO_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DO_PROJETO))


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

    # Sanitizar antes do envio. Excesso causa abstenção, nunca perda silenciosa.
    estado, mascarados = redacao.limpar(estado)
    if len(estado) > orcamento.LIMITE_DE_CARACTERES:
        return None, {'erro': 'input_too_large', 'sent': False}
    from executor.shared import ask
    try:
        if transporte is not transporte_http:
            # Test doubles never contaminate the live wallet or cost log.
            import tempfile
            from executor.ledger import Ledger
            from executor.pricing import load_prices, usd_to_nusd
            with tempfile.TemporaryDirectory() as directory:
                db = Path(directory) / 'test.sqlite3'
                with Ledger(db, 'simulation') as ledger:
                    ledger.set_wallet_cap(usd_to_nusd('5'))
                return ask(estado, perguntas, consumer='router', api_key=api_key,
                           timeout=timeout, transport=transporte, db_path=db,
                           prices=load_prices(), legacy_paths=())
        respostas, detalhe = ask(estado, perguntas, consumer='router',
                                 api_key=api_key, timeout=timeout)
        orcamento.registrar(detalhe.get('custo_usd'), origem=origem,
                            attempt_id=detalhe.get('attempt_id'), modelo=MODELO,
                            caracteres=len(estado), mascarados=mascarados,
                            custo_reportado=detalhe.get('custo_usd') is not None,
                            evidence_level='live_component')
        return respostas, detalhe
    except Exception as error:
        return None, {'erro': type(error).__name__, 'custo_usd': None}
