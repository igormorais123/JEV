"""Camada de leitura pelo shell: o mesmo filtro do `Read`, na porta por onde o texto entra.

A medição de 2026-09-21 sobre as sessões desta máquina mostrou que 81% do texto devolvido por
ferramenta entra pelo `Bash`, e que a maior parte disso é leitura de arquivo (`cat`, `sed -n`,
`head`); o `Read`, que a camada de leitura cobre, responde por 9%. Esta camada leva a mesma
política — `leitura.analisar`, sem mudar nada nela — ao comando de shell: quando um segmento
do comando é `cat ARQUIVO` de um arquivo grande, ele vira `sed -n 'A,Bp' ARQUIVO` com a
janela que o Jev escolheu, e o agente recebe a nota dizendo o que ficou de fora.

Reescrever um comando é mais arriscado do que encolher um `Read`, e por isso as regras são
estreitas, todas para o lado de não mexer:

- O hook responde `allow` junto com o comando novo, e `allow` dispensa a confirmação do
  usuário. Então só se mexe em comando em que **todo** segmento é de leitura pura e conhecida
  (`cat`, `sed -n 'A,Bp'`, `head`, `tail`, `echo`, `cd`, `ls`, `wc`, `pwd`). Um `rm`, um
  `python`, um `git` em qualquer ponto do comando, e a camada não toca em nada.
- Nada de pipe, redirecionamento, substituição, variável, curinga, subshell, heredoc, quebra
  de linha ou barra invertida: o comando fica como veio.
- Só se estreita leitura do arquivo inteiro (`cat ARQUIVO`, ou `head`/`sed` cujo intervalo
  cobre o arquivo todo). `sed -n '300,420p'` é o agente dizendo o que quer: fica, e é
  registrado, porque é por ele que se mede o arrependimento depois de um `cat` estreitado.
- No máximo dois arquivos estreitados por comando, classificados em paralelo.
- O segmento novo é sempre `sed -n 'A,Bp' ARQUIVO`: leitura, como o que substitui.
"""
import re
import shlex
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import leitura, nucleo

MAXIMO_DE_ARQUIVOS = 2
PROIBIDOS = ('\n', '\r', '`', '$', '\\', '(', ')', '{', '}', '<', '>', '|', '*', '?', '~', '#', '!')
SO_LEITURA = {'cat', 'sed', 'head', 'tail', 'echo', 'cd', 'ls', 'wc', 'pwd'}
INTERVALO = re.compile(r'^(\d+),(\d+)p$')


def dividir(comando):
    """Segmentos de nível superior e os separadores (`&&`, `||`, `;`) entre eles.

    Devolve (segmentos, separadores) com len(separadores) == len(segmentos) - 1, ou None se o
    comando tiver qualquer construção fora do que esta camada entende.
    """
    fora_de_aspas = []
    aspas = None
    for c in comando:
        if aspas:
            if c == aspas:
                aspas = None
            elif c in ('\n', '\r', '`', '$', '\\', '!'):
                return None  # dentro de aspas duplas ainda expandem; nas simples, não arrisco
            fora_de_aspas.append(' ')
        elif c in ('"', "'"):
            aspas = c
            fora_de_aspas.append(' ')
        else:
            fora_de_aspas.append(c)
    if aspas:
        return None
    mascara = ''.join(fora_de_aspas)
    if any(p in mascara for p in PROIBIDOS):
        return None
    segmentos, separadores, inicio, i = [], [], 0, 0
    while i < len(mascara):
        dois = mascara[i:i + 2]
        if dois in ('&&', '||'):
            segmentos.append(comando[inicio:i]); separadores.append(dois); i += 2; inicio = i
        elif mascara[i] == ';':
            segmentos.append(comando[inicio:i]); separadores.append(';'); i += 1; inicio = i
        elif mascara[i] == '&':
            return None  # execução em segundo plano
        else:
            i += 1
    segmentos.append(comando[inicio:])
    if any(not s.strip() for s in segmentos):
        return None
    return segmentos, separadores


def _caminho(texto, cwd):
    """Caminho do Git Bash (`/c/Users/...`) ou do Windows, resolvido contra o diretório vigente."""
    m = re.match(r'^/([a-zA-Z])/(.*)$', texto)
    if m:
        texto = f'{m.group(1).upper()}:/{m.group(2)}'
    elif texto.startswith('/'):
        return None  # /tmp, /usr: caminho do MSYS, não sei onde fica no Windows
    caminho = Path(texto)
    if not caminho.is_absolute():
        if cwd is None:
            return None
        caminho = Path(cwd) / caminho
    return caminho


def interpretar(segmento, cwd):
    """O que o segmento faz: {'tipo': 'cat'|'intervalo'|'cd'|'outro', ...}, ou None se não é
    de leitura pura. `cwd` é o diretório vigente antes do segmento (None se desconhecido)."""
    try:
        partes = shlex.split(segmento, posix=True)
    except ValueError:
        return None
    if not partes or partes[0] not in SO_LEITURA:
        return None
    nome, args = partes[0], partes[1:]
    if nome == 'cd':
        if len(args) != 1:
            return None
        return {'tipo': 'cd', 'cwd': _caminho(args[0], cwd)}
    if nome == 'cat' and len(args) == 1 and not args[0].startswith('-'):
        return {'tipo': 'cat', 'texto': args[0], 'caminho': _caminho(args[0], cwd)}
    if nome == 'sed':
        # Só `sed -n 'A,Bp' ARQUIVO`: qualquer outro sed pode escrever (`-i`, comando `w`).
        if len(args) == 3 and args[0] == '-n' and INTERVALO.match(args[1]) \
                and not args[2].startswith('-'):
            a, b = map(int, INTERVALO.match(args[1]).groups())
            return {'tipo': 'intervalo', 'inicio': a, 'fim': b, 'texto': args[2],
                    'caminho': _caminho(args[2], cwd)}
        return None
    if nome == 'head':
        quantidade, resto = 10, args
        if len(args) == 3 and args[0] == '-n' and args[1].isdigit():
            quantidade, resto = int(args[1]), args[2:]
        elif len(args) == 2 and re.match(r'^-\d+$', args[0]):
            quantidade, resto = int(args[0][1:]), args[1:]
        if len(resto) == 1 and not resto[0].startswith('-'):
            return {'tipo': 'intervalo', 'inicio': 1, 'fim': quantidade, 'texto': resto[0],
                    'caminho': _caminho(resto[0], cwd)}
        return {'tipo': 'outro'}
    return {'tipo': 'outro'}


def _linhas(caminho):
    try:
        if caminho.stat().st_size > leitura.TAMANHO_MAXIMO:
            return None
        with caminho.open('rb') as arquivo:
            return sum(1 for _ in arquivo)
    except OSError:
        return None


def analisar(comando, pedido, cwd, *, transporte=None, tempo_total=nucleo.TEMPO_TOTAL_PADRAO):
    """Devolve {'acao': 'nada'|'reescrever', 'leituras': [...], ...}.

    `leituras` traz uma decisão de `leitura.analisar` por arquivo lido (estreitado ou não),
    para o registro; `reescrever` traz também o `comando` novo.
    """
    base = {'acao': 'nada', 'leituras': []}
    partido = dividir(comando or '')
    if partido is None:
        return {**base, 'motivo': 'comando fora da gramatica da camada'}
    segmentos, separadores = partido
    if '||' in separadores:
        return {**base, 'motivo': 'comando fora da gramatica da camada'}
    interpretados, vigente = [], Path(cwd) if cwd else None
    for segmento in segmentos:
        visto = interpretar(segmento, vigente)
        if visto is None:
            return {**base, 'motivo': 'ha segmento que nao e leitura pura'}
        if visto['tipo'] == 'cd':
            vigente = visto['cwd']
        interpretados.append(visto)

    candidatos = []
    for indice, visto in enumerate(interpretados):
        if visto['tipo'] not in ('cat', 'intervalo') or visto.get('caminho') is None:
            continue
        if visto['tipo'] == 'intervalo':
            total = _linhas(visto['caminho'])
            inteiro = total is not None and visto['inicio'] == 1 and visto['fim'] >= total
            if not inteiro:
                base['leituras'].append(leitura.analisar(
                    visto['caminho'], pedido,
                    {'offset': visto['inicio'], 'limit': visto['fim'] - visto['inicio'] + 1}))
                continue
        candidatos.append(indice)
    if not candidatos:
        return {**base, 'motivo': 'nenhuma leitura de arquivo inteiro'}
    if not pedido:
        return {**base, 'motivo': 'sem pedido vigente'}

    escolhidos = candidatos[:MAXIMO_DE_ARQUIVOS]
    with ThreadPoolExecutor(max_workers=len(escolhidos)) as pool:
        decisoes = list(pool.map(
            lambda i: leitura.analisar(interpretados[i]['caminho'], pedido, {},
                                       transporte=transporte, tempo_total=tempo_total),
            escolhidos))
    base['leituras'].extend(decisoes)
    novos = list(segmentos)
    estreitados = []
    for indice, decisao in zip(escolhidos, decisoes):
        if decisao['acao'] != 'estreitar':
            continue
        a = decisao['offset']
        b = a + decisao['limit'] - 1
        novos[indice] = f" sed -n '{a},{b}p' {shlex.quote(interpretados[indice]['texto'])} "
        estreitados.append(decisao)
    if not estreitados:
        return {**base, 'motivo': 'nenhum arquivo para estreitar'}
    comando_novo = novos[0]
    for separador, segmento in zip(separadores, novos[1:]):
        comando_novo += separador + segmento
    return {**base, 'acao': 'reescrever', 'comando': comando_novo.strip(),
            'estreitados': estreitados}


def nota_para_o_agente(decisao):
    """Curta, e diz como ler o resto com a mesma ferramenta que o agente estava usando."""
    partes = []
    for d in decisao['estreitados']:
        a = d['offset']
        b = a + d['limit'] - 1
        partes.append(f"{Path(d['arquivo']).name} tem {d['linhas']} linhas e saiu só de "
                      f"{a} a {b} ({d['mantidos']} de {d['blocos']} blocos que o Jev pôs no "
                      f"topo para o pedido vigente)")
    return ("[jev/leitura] " + '; '.join(partes) +
            ". Se precisar do restante, peça o intervalo com sed -n 'A,Bp'.")
