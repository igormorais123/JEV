"""O cliente único do Jev no Hermes da VPS: chaves, provedores, teto, cache e registro.

Tudo que o Hermes manda ao Jev passa por `perguntar`. As regras valem para todo consumidor —
camadas do plugin, porteiros de cron, ferramenta `jev_advisor`:

- **Falha para o lado aberto.** Sem chave, sem rede, fora do teto, fora do contrato, fora do
  tempo ou com o interruptor `DESLIGADO` presente, devolve `(None, detalhe)` e quem chamou
  segue como seguiria sem o Jev.
- **Segredo não sai.** O estado passa pela redação por forma antes do envio.
- **Teto verificado antes do envio**, por reserva do pior caso num SQLite, e liquidado pelo
  custo que o provedor devolve (OpenRouter) ou pelo uso em tokens (TypeSafe).
- **Cache exato** de três dias: a mesma pergunta sobre o mesmo texto não é paga duas vezes.
- **Registro sem conteúdo**: `estado/decisoes.jsonl` guarda origem, tamanho, hash, classes,
  confiança, latência e custo — nunca o texto enviado.

Provedores (E5 do estudo: mesma resposta nos 40 casos): OpenRouter é o principal, com metade
da latência e 12% menos custo; TypeSafe entra quando o OpenRouter falha na rede, devolve 429 ou
5xx. Erro de contrato (4xx) não troca de provedor: a pergunta está errada, não a rota.
"""
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(os.environ.get('JEV_HERMES_RAIZ', '/root/.hermes/integrations/jev'))
ESTADO = RAIZ / 'estado'
CHAVES = RAIZ / 'jev.env'
DESLIGADO = RAIZ / 'DESLIGADO'
REGISTRO = ESTADO / 'decisoes.jsonl'
BANCO = ESTADO / 'jev.sqlite3'
FUSO = timezone(timedelta(hours=-3))

PROVEDORES = {
    'openrouter': {'url': 'https://openrouter.ai/api/alpha/decisions', 'modelo': 'typesafe/jev-1.13',
                   'variavel': 'OPENROUTER_API_KEY', 'saida_cobrada': False},
    'typesafe': {'url': 'https://api.typesafe.ai/v1/systemone', 'modelo': 'jev-1.13.0',
                 'variavel': 'TYPESAFE_API_KEY', 'saida_cobrada': True},
}
ORDEM_PADRAO = ('openrouter', 'typesafe')

# US$ 0,042 por milhão de tokens de entrada nos dois provedores; a TypeSafe cobra a saída
# pela mesma tarifa (executor/prices.json do projeto, conferido em 2026-09-19).
USD_POR_TOKEN = 0.042e-6
TETO_DIARIO_PADRAO = 0.50
TETO_MENSAL_PADRAO = 5.00
LIMITE_PADRAO = 12000      # caracteres de estado por chamada
LIMITE_MAXIMO = 60000
TRABALHADORES = 8          # acima disso o provedor devolveu 429 nas rodadas do estudo
CACHE_SEGUNDOS = 3 * 86400
TIMEOUT_PADRAO = 6.0

_trava = threading.Lock()


# ------------------------------------------------------------------------------ chaves

def _ler_arquivo(caminho):
    valores = {}
    try:
        for linha in caminho.read_text(encoding='utf-8', errors='replace').splitlines():
            linha = linha.strip()
            if not linha or linha.startswith('#') or '=' not in linha:
                continue
            nome, valor = linha.split('=', 1)
            valores[nome.strip()] = valor.strip().strip('"').strip("'")
    except OSError:
        pass
    return valores


def configuracao():
    """Ambiente primeiro, depois `jev.env`. Nunca devolvida a log nem a usuário."""
    arquivo = _ler_arquivo(CHAVES)
    return lambda nome, padrao=None: os.environ.get(nome) or arquivo.get(nome) or padrao


def tetos():
    cfg = configuracao()
    try:
        return float(cfg('JEV_TETO_DIARIO_USD', TETO_DIARIO_PADRAO)), \
            float(cfg('JEV_TETO_MENSAL_USD', TETO_MENSAL_PADRAO))
    except ValueError:
        return TETO_DIARIO_PADRAO, TETO_MENSAL_PADRAO


def ordem_de_provedores():
    cfg = configuracao()
    preferido = (cfg('JEV_PROVEDOR', '') or '').strip().lower()
    ordem = [preferido] if preferido in PROVEDORES else []
    ordem += [p for p in ORDEM_PADRAO if p not in ordem]
    return [p for p in ordem if cfg(PROVEDORES[p]['variavel'])]


def desligado():
    return DESLIGADO.exists() or os.environ.get('JEV_DESLIGADO') == '1'


# ----------------------------------------------------------------------------- redação

PADROES_DE_SEGREDO = [
    re.compile(r'\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{16,}'),
    re.compile(r'\bsk_[A-Za-z0-9]{16,}'),
    re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{16,}'),
    re.compile(r'\bAIza[A-Za-z0-9_\-]{20,}'),
    re.compile(r'\bxox[baprs]-[A-Za-z0-9\-]{10,}'),
    re.compile(r'\bpplx-[A-Za-z0-9]{16,}'),
    re.compile(r'\bapify_api_[A-Za-z0-9]{16,}'),
    re.compile(r'\bBSA[_A-Za-z0-9]{16,}'),
    re.compile(r'\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)'),
    re.compile(r'(?i)\b([A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|SENHA|PASSWD)[A-Z0-9_]*)\s*[:=]\s*'
               r'["\']?[^\s"\',;]{8,}'),
    re.compile(r'(?i)\b(?:authorization|bearer)\s*:?\s+[A-Za-z0-9_\-\.]{20,}'),
    re.compile(r'\b[a-z][a-z0-9+.\-]*://[^\s/@]+:[^\s/@]+@'),
    re.compile(r'(?i)\b(?=[A-Za-z0-9_\-]*[_\-])[A-Za-z0-9_\-]*'
               r'(?:secret|token|apikey|api_key|passwd|senha)[A-Za-z0-9_\-]*\b(?<=[A-Za-z0-9_\-]{16})'),
]
CORRIDA_LONGA = re.compile(r'\b(?=[A-Za-z0-9_\-]*[0-9])(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{40,}\b')
ROTULO = '[segredo]'


def redigir(texto):
    """(texto mascarado, quantas ocorrências). Por forma, não por lista de chaves conhecidas."""
    if not texto:
        return texto, 0
    total = 0
    for padrao in PADROES_DE_SEGREDO:
        texto, n = padrao.subn(
            lambda m: (m.group(1) + '=' + ROTULO) if m.groups() and m.group(1) else ROTULO, texto)
        total += n
    texto, n = CORRIDA_LONGA.subn(ROTULO, texto)
    return texto, total + n


# ------------------------------------------------------------------------ banco e teto

@contextmanager
def _banco():
    ESTADO.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(BANCO, timeout=10, isolation_level=None)
    try:
        conexao.execute('PRAGMA journal_mode=WAL')
        conexao.execute('CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY, em TEXT, dia TEXT, '
                        'mes TEXT, origem TEXT, provedor TEXT, reservado REAL, custo REAL, status TEXT)')
        conexao.execute('CREATE TABLE IF NOT EXISTS cache (chave TEXT PRIMARY KEY, em REAL, respostas TEXT)')
        yield conexao
    finally:
        conexao.close()


def _agora():
    return datetime.now(FUSO)


def pior_caso_usd(bytes_do_payload):
    """Pior custo de uma chamada, conhecido antes do envio.

    O provedor acrescenta instruções próprias (medido: 159 tokens estimados viraram 379), e o
    estado pode ser texto denso; dois bytes por token mais 1.500 de folga cobrem os dois, e o
    fator 2 cobre a saída cobrada pela TypeSafe.
    """
    return (bytes_do_payload / 2 + 1500) * USD_POR_TOKEN * 2


def situacao():
    """Gasto do dia e do mês, chamadas e cache. Sem valor de chave."""
    agora = _agora()
    with _banco() as conexao:
        def soma(campo, valor):
            linha = conexao.execute(
                f"SELECT COUNT(*), COALESCE(SUM(CASE WHEN status='liquidado' THEN custo ELSE reservado END),0) "
                f'FROM gastos WHERE {campo}=?', (valor,)).fetchone()
            return linha[0], round(linha[1], 8)
        chamadas_dia, gasto_dia = soma('dia', agora.date().isoformat())
        chamadas_mes, gasto_mes = soma('mes', agora.strftime('%Y-%m'))
        itens_cache = conexao.execute('SELECT COUNT(*) FROM cache').fetchone()[0]
    teto_dia, teto_mes = tetos()
    return {'dia': agora.date().isoformat(), 'chamadas_hoje': chamadas_dia, 'gasto_hoje_usd': gasto_dia,
            'chamadas_mes': chamadas_mes, 'gasto_mes_usd': gasto_mes, 'teto_diario_usd': teto_dia,
            'teto_mensal_usd': teto_mes, 'itens_no_cache': itens_cache,
            'provedores_com_chave': ordem_de_provedores(), 'desligado': desligado()}


def _reservar(origem, provedor, valor):
    agora = _agora()
    teto_dia, teto_mes = tetos()
    with _trava, _banco() as conexao:
        conexao.execute('BEGIN IMMEDIATE')
        try:
            gasto = "COALESCE(SUM(CASE WHEN status='liquidado' THEN custo ELSE reservado END),0)"
            dia = conexao.execute(f'SELECT {gasto} FROM gastos WHERE dia=?',
                                  (agora.date().isoformat(),)).fetchone()[0]
            mes = conexao.execute(f'SELECT {gasto} FROM gastos WHERE mes=?',
                                  (agora.strftime('%Y-%m'),)).fetchone()[0]
            if dia + valor > teto_dia:
                conexao.execute('ROLLBACK')
                return None, f'teto diário de US$ {teto_dia:.2f} alcançado'
            if mes + valor > teto_mes:
                conexao.execute('ROLLBACK')
                return None, f'teto mensal de US$ {teto_mes:.2f} alcançado'
            cursor = conexao.execute(
                'INSERT INTO gastos (em, dia, mes, origem, provedor, reservado, custo, status) '
                "VALUES (?,?,?,?,?,?,NULL,'reservado')",
                (agora.isoformat(timespec='seconds'), agora.date().isoformat(), agora.strftime('%Y-%m'),
                 origem, provedor, valor))
            conexao.execute('COMMIT')
            return cursor.lastrowid, None
        except Exception:
            conexao.execute('ROLLBACK')
            raise


def _liquidar(identificador, custo, status='liquidado'):
    with _trava, _banco() as conexao:
        conexao.execute('UPDATE gastos SET custo=?, status=? WHERE id=?', (custo, status, identificador))


# ------------------------------------------------------------------------------- cache

def _chave_de_cache(estado, perguntas):
    corpo = json.dumps({'state': estado, 'questions': perguntas}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(corpo.encode('utf-8')).hexdigest()


def _do_cache(chave):
    try:
        with _banco() as conexao:
            linha = conexao.execute('SELECT em, respostas FROM cache WHERE chave=?', (chave,)).fetchone()
        if linha and time.time() - linha[0] <= CACHE_SEGUNDOS:
            return json.loads(linha[1])
    except Exception:
        pass
    return None


def _para_o_cache(chave, respostas):
    try:
        with _banco() as conexao:
            conexao.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)',
                            (chave, time.time(), json.dumps(respostas, ensure_ascii=False)))
            conexao.execute('DELETE FROM cache WHERE em < ?', (time.time() - CACHE_SEGUNDOS,))
    except Exception:
        pass


# ---------------------------------------------------------------------------- contrato

class ErroDeContrato(Exception):
    pass


def validar(corpo, perguntas):
    """Uma resposta tipada por pergunta, coerente com o tipo pedido (formatos do executor/runner.py)."""
    respostas = corpo.get('answers') if isinstance(corpo, dict) else None
    if not isinstance(respostas, dict) or set(respostas) != set(perguntas):
        raise ErroDeContrato('respostas não batem com as perguntas')
    for nome, resposta in respostas.items():
        tipo = resposta.get('type') or perguntas[nome].get('type') or 'choice'
        if tipo == 'choice':
            criterios = perguntas[nome].get('criteria')
            if isinstance(criterios, dict) and resposta.get('choice') not in criterios:
                raise ErroDeContrato(f'escolha fora dos critérios em {nome}')
        elif tipo == 'score':
            if not isinstance(resposta.get('score'), (int, float)):
                raise ErroDeContrato(f'score ausente em {nome}')
        elif tipo == 'noul':
            valor = resposta.get('noul')
            if not isinstance(valor, (int, float)) or not 0 <= valor <= 1:
                raise ErroDeContrato(f'noul inválido em {nome}')
        else:
            raise ErroDeContrato(f'tipo desconhecido em {nome}')
        confianca = resposta.get('confidence')
        if confianca is not None and not (isinstance(confianca, (int, float)) and 0 <= confianca <= 1):
            raise ErroDeContrato(f'confiança inválida em {nome}')
    return respostas


# --------------------------------------------------------------------------- transporte

def transporte_http(url, cabecalhos, corpo, timeout):
    requisicao = urllib.request.Request(url, data=json.dumps(corpo, ensure_ascii=False).encode('utf-8'),
                                        headers=cabecalhos, method='POST')
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return resposta.status, json.loads(resposta.read().decode('utf-8'))
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read().decode('utf-8'))
        except (ValueError, OSError):
            return erro.code, {}
    except TimeoutError:
        return -1, {}
    except Exception as erro:
        # Timeout de socket chega como URLError(reason=timeout): a requisição pode ter sido
        # cobrada, e a reserva fica como custo.
        if 'timed out' in str(erro).lower():
            return -1, {}
        return 0, {}


def _custo(provedor, corpo, reservado):
    uso = corpo.get('usage') or {}
    if isinstance(uso.get('cost'), (int, float)):
        return float(uso['cost'])
    entrada = uso.get('input_tokens', uso.get('prompt_tokens'))
    saida = uso.get('output_tokens', uso.get('completion_tokens')) or 0
    if isinstance(entrada, int):
        cobrados = entrada + (saida if PROVEDORES[provedor]['saida_cobrada'] else 0)
        return cobrados * USD_POR_TOKEN
    return reservado  # sem uso reportado: custo conhecido é o pior caso reservado


def registrar(linha, arquivo=None):
    arquivo = arquivo or REGISTRO
    try:
        ESTADO.mkdir(parents=True, exist_ok=True)
        with open(arquivo, 'a', encoding='utf-8') as saida:
            saida.write(json.dumps(linha, ensure_ascii=False) + '\n')
    except OSError:
        pass


def _resumo_das_respostas(respostas):
    resumo = {}
    for nome, r in (respostas or {}).items():
        resumo[nome] = {k: r.get(k) for k in ('choice', 'confidence', 'score', 'noul') if k in r}
    return resumo


def perguntar(estado, perguntas, *, origem, timeout=TIMEOUT_PADRAO, limite=LIMITE_PADRAO,
              transporte=None, usar_cache=True):
    """Uma decisão do Jev. Devolve (respostas, detalhe); respostas é None em qualquer falha.

    `estado` é texto (ou objeto JSON, para os contratos legados do `jev_advisor`); `perguntas`
    é o mapa `questions` do contrato. Texto de terceiro vai só no estado — nunca na instrução.
    """
    inicio = time.time()
    detalhe = {'origem': origem, 'enviado': False}
    if desligado():
        return None, {**detalhe, 'erro': 'desligado'}
    if isinstance(estado, str):
        estado, mascarados = redigir(estado)
        tamanho = len(estado)
    else:
        texto, mascarados = redigir(json.dumps(estado, ensure_ascii=False))
        estado = json.loads(texto) if mascarados else estado
        tamanho = len(texto)
    detalhe.update({'caracteres': tamanho, 'mascarados': mascarados})
    if tamanho > min(limite, LIMITE_MAXIMO):
        return None, {**detalhe, 'erro': 'estado grande demais'}
    chave = _chave_de_cache(estado, perguntas)
    detalhe['hash'] = chave[:16]
    if usar_cache:
        respostas = _do_cache(chave)
        if respostas is not None:
            detalhe.update({'cache': True, 'custo_usd': 0.0,
                            'latencia_ms': round((time.time() - inicio) * 1000)})
            registrar({'em': _agora().isoformat(timespec='seconds'), **detalhe,
                       'respostas': _resumo_das_respostas(respostas)})
            return respostas, detalhe
    provedores = ordem_de_provedores()
    if not provedores:
        return None, {**detalhe, 'erro': 'sem chave'}
    cfg = configuracao()
    transporte = transporte or transporte_http
    for provedor in provedores:
        restante = timeout - (time.time() - inicio)
        if restante < 0.5:
            detalhe['erro'] = detalhe.get('erro') or 'sem tempo'
            break
        dados = PROVEDORES[provedor]
        corpo = {'model': dados['modelo'], 'state': estado, 'questions': perguntas}
        tamanho_do_corpo = len(json.dumps(corpo, ensure_ascii=False).encode('utf-8'))
        reservado = pior_caso_usd(tamanho_do_corpo)
        identificador, motivo = _reservar(origem, provedor, reservado)
        if identificador is None:
            return None, {**detalhe, 'erro': motivo}
        cabecalhos = {'Authorization': f"Bearer {cfg(dados['variavel'])}", 'Content-Type': 'application/json',
                      'User-Agent': 'hermes-jev/1.0', 'X-Title': 'Hermes Jev'}
        status, resposta = transporte(dados['url'], cabecalhos, corpo, restante)
        detalhe.update({'provedor': provedor, 'http': status, 'enviado': status != 0})
        if status == 200:
            custo = _custo(provedor, resposta, reservado)
            _liquidar(identificador, custo)
            detalhe['custo_usd'] = custo
            try:
                respostas = validar(resposta, perguntas)
            except ErroDeContrato as erro:
                detalhe['erro'] = f'contrato: {erro}'
                break
            if usar_cache:
                _para_o_cache(chave, respostas)
            detalhe.update({'cache': False, 'latencia_ms': round((time.time() - inicio) * 1000)})
            registrar({'em': _agora().isoformat(timespec='seconds'), **detalhe,
                       'respostas': _resumo_das_respostas(respostas)})
            return respostas, detalhe
        if status == 0:
            _liquidar(identificador, 0.0, 'nao_enviado')     # não saiu daqui: nada a cobrar
        elif status == 429:
            _liquidar(identificador, 0.0, 'recusado_429')    # limite de taxa não processa token
        elif status == -1:
            _liquidar(identificador, reservado, 'liquidado')  # timeout: pode ter sido cobrado
        else:
            _liquidar(identificador, _custo(provedor, resposta, 0.0), 'liquidado')
        detalhe['erro'] = f'http {status}'
        if 400 <= status < 500 and status != 429:
            break  # a pergunta está errada, não a rota
    detalhe['latencia_ms'] = round((time.time() - inicio) * 1000)
    registrar({'em': _agora().isoformat(timespec='seconds'), **detalhe})
    return None, detalhe


def classificar_em_paralelo(estados, perguntas, *, origem, tempo_total=TIMEOUT_PADRAO,
                            limite=LIMITE_PADRAO, transporte=None):
    """Uma chamada por estado, até oito ao mesmo tempo, dentro de um tempo total."""
    inicio = time.time()

    def uma(estado):
        restante = tempo_total - (time.time() - inicio)
        if restante <= 0.5:
            return None, {'erro': 'sem tempo', 'origem': origem}
        return perguntar(estado, perguntas, origem=origem, timeout=restante, limite=limite,
                         transporte=transporte)

    if not estados:
        return []
    with ThreadPoolExecutor(max_workers=min(TRABALHADORES, len(estados))) as pool:
        return list(pool.map(uma, estados))


def resumo_das_chamadas(resultados):
    custo, pagas, cache, falha = 0.0, 0, 0, None
    for respostas, detalhe in resultados:
        detalhe = detalhe or {}
        custo += detalhe.get('custo_usd') or 0.0
        if detalhe.get('cache'):
            cache += 1
        elif detalhe.get('enviado'):
            pagas += 1
        if respostas is None and falha is None:
            falha = detalhe.get('erro') or 'sem resposta'
    return {'chamadas': pagas, 'do_cache': cache, 'custo_usd': round(custo, 8), 'falha': falha}


def escolha(respostas, nome):
    bloco = (respostas or {}).get(nome) or {}
    return bloco.get('choice'), bloco.get('confidence')


def dec(valor, casas=2):
    if valor is None:
        return '?'
    return f'{valor:.{casas}f}'.replace('.', ',')


if __name__ == '__main__':
    print(json.dumps(situacao(), ensure_ascii=False, indent=1))
