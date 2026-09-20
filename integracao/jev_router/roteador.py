"""Orquestra a classificação: cache, chamada ao Jev, política e registro da decisão.

O registro em `decisoes.jsonl` é o que permite medir depois se a coisa serviu, em vez de
acreditar que serviu. Ele é escrito nos dois modos, inclusive em sombra.
"""
import hashlib
import json
import time
from pathlib import Path

from . import cliente, politica

RAIZ = Path(__file__).resolve().parents[1]
CACHE = RAIZ / 'cache'
DECISOES = RAIZ / 'decisoes.jsonl'
# O pedido redigido, guardado só para auditoria posterior. Fica em `estado/`, que o .gitignore
# já exclui, e passa pela mesma redação de credenciais aplicada antes de qualquer envio.
#
# Isto existe por causa de um defeito encontrado ao tentar auditar as 28 primeiras decisões de
# produção: `decisoes.jsonl` guardava só o SHA-256 do pedido, e recasar o hash com o texto do
# transcript recuperou 1 caso de 28. Um registro que não permite medir se a decisão foi certa
# não serve à finalidade que o próprio arquivo declara no topo deste módulo.
PEDIDOS = RAIZ / 'estado' / 'pedidos.jsonl'

# Abaixo disto o pedido é curto demais para ter tema ("ok", "continue", "sim"). Eles herdam o
# fluxo normal sem gastar chamada, e são justamente os que mais se repetem.
MINIMO_DE_CARACTERES = 25


def impressao(texto):
    material = json.dumps({'state': texto, 'questions': politica.PERGUNTAS,
                           'model': cliente.MODELO, 'version': 'shared-v1'},
                          sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


def do_cache(marca):
    arquivo = CACHE / f'{marca}.json'
    if not arquivo.exists():
        return None
    try:
        return json.loads(arquivo.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        return None


def para_o_cache(marca, respostas):
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / f'{marca}.json').write_text(
            json.dumps(respostas, ensure_ascii=False), encoding='utf-8')
    except OSError:
        pass


def guardar_pedido(marca_do_pedido, pedido):
    """Grava o pedido redigido para que a próxima auditoria tenha texto, não só hash.

    Falha em silêncio de propósito: nada aqui pode atrapalhar o fluxo de quem está pedindo.
    """
    from . import redacao
    try:
        limpo, _ = redacao.limpar(pedido)
        PEDIDOS.parent.mkdir(parents=True, exist_ok=True)
        with PEDIDOS.open('a', encoding='utf-8') as arquivo:
            arquivo.write(json.dumps({'pedido_sha256': marca_do_pedido,
                                      'em': time.strftime('%Y-%m-%dT%H:%M:%S'),
                                      'pedido': limpo}, ensure_ascii=False) + '\n')
    except Exception:
        pass


def registrar(decisao):
    try:
        with DECISOES.open('a', encoding='utf-8') as arquivo:
            arquivo.write(json.dumps(decisao, ensure_ascii=False) + '\n')
    except OSError:
        pass


def classificar(pedido, *, contexto='', modo='sombra', usar_cache=True, transporte=None,
                origem='hook'):
    """Devolve a decisão para um pedido, ou None se não houve classificação.

    None significa "siga como antes": é o resultado de pedido curto, de falha de rede, de teto
    estourado ou de resposta fora do contrato.
    """
    pedido = (pedido or '').strip()
    if len(pedido) < MINIMO_DE_CARACTERES:
        return None

    estado = (f'Diretório de trabalho: {contexto}\n\n' if contexto else '') + \
             f'Pedido do usuário:\n{pedido}'
    marca = impressao(estado)

    respostas = do_cache(marca) if usar_cache else None
    veio_do_cache = respostas is not None
    custo = 0.0
    latencia = 0
    if respostas is None:
        inicio = time.time()
        respostas, detalhe = cliente.perguntar(estado, politica.PERGUNTAS,
                                               transporte=transporte, origem=origem)
        latencia = round((time.time() - inicio) * 1000)
        custo = (detalhe or {}).get('custo_usd')
        if respostas is None:
            registrar({'em': time.strftime('%Y-%m-%dT%H:%M:%S'), 'modo': modo, 'marca': marca,
                       'classificou': False, 'motivo': (detalhe or {}).get('erro'),
                       'latencia_ms': latencia, 'custo_usd': custo, 'origem': origem})
            return None
        if usar_cache:
            para_o_cache(marca, respostas)

    decisao = politica.decidir(respostas)
    decisao.update({'em': time.strftime('%Y-%m-%dT%H:%M:%S'), 'modo': modo, 'marca': marca,
                    'classificou': True, 'cache': veio_do_cache, 'latencia_ms': latencia,
                    'custo_usd': custo, 'origem': origem,
                    'attempt_id': None if veio_do_cache else detalhe.get('attempt_id'),
                    'evidence_level': 'cache' if veio_do_cache else detalhe.get('evidence_level'),
                    'pedido_sha256': hashlib.sha256(pedido.encode()).hexdigest()})
    registrar(decisao)
    guardar_pedido(decisao['pedido_sha256'], pedido)
    return decisao


# Nome antigo, de quando isto roteava esforço. Mantido para não quebrar chamada existente.
rotear = classificar
