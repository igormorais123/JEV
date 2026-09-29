"""Camada de leitura: antes de um `Read` grande, o Jev diz que parte do arquivo interessa.

É a aplicação de maior valor medido do estudo — ordenação de contexto — posta no ponto do
fluxo em que o modelo caro mais gasta: ler arquivo inteiro. O `Read` do Claude Code lê um
intervalo contíguo (`offset`, `limit`), então a camada faz só o que esse contrato permite:
classifica o arquivo em blocos contra o pedido vigente e encolhe o intervalo para o menor que
contém todo bloco que não foi descartado.

A política é a da aplicação de ordenação, que é a medida. Os blocos `essencial` com
confiança ≥ 0,90 são obrigatórios: a janela é o intervalo que os cobre, com um bloco vizinho
de cada lado (definição cortada na fronteira do bloco é o erro barato de evitar). Se nenhum
bloco chega a esse corte, fica a janela dos três mais bem colocados (classe, depois
confiança), o k = 3 da R26.

Não é "descarte o irrelevante com 0,99": o primeiro teste real, em `executor/ledger.py`
(784 linhas, 14 blocos), mostrou que em código o Jev raramente diz `irrelevante` com essa
confiança — as classes vieram `complementar` com confiança de 0,17 a 0,50 e dois blocos
`essencial` com 0,98 e 1,00 — e uma regra de descarte nunca dispararia. E não é "top-3 e
pronto": no mesmo teste um `essencial` de confiança 0,45 no primeiro bloco puxou a janela
para a linha 1 e a economia caiu de 69% para 39%. A regra de seleção é a que a R18, a R20 e
a R26 mediram: o topo mantém a resposta e corta a maior parte do texto; k = 1 falha quando
a resposta está dividida.

Um bloco fraco no meio de dois fortes fica, porque o intervalo é contíguo — a camada de
ferramenta (`ler.py`) é quem devolve trechos separados. E se metade ou mais dos blocos vier
`essencial`, o arquivo inteiro interessa e a camada não mexe.

Onde a camada não mexe, de propósito:
- arquivo pequeno (menos de 200 linhas): não paga a latência;
- `Read` que já veio com `offset` ou `limit`: o agente já sabe o que quer;
- sem pedido vigente na sessão: não há contra o que classificar;
- arquivo de instrução (CLAUDE.md, AGENTS.md, SKILL.md, MEMORY.md): se lê inteiro;
- qualquer falha, tempo esgotado ou teto: fica como estava (falha para o lado aberto);
- janela que pouparia menos de um quarto do arquivo ou menos de 80 linhas: não vale a nota.
"""
import time
from pathlib import Path

from . import nucleo

MINIMO_DE_LINHAS = 200
BLOCOS_NO_TOPO = 3          # R26: k = 3 quando não se sabe se a resposta está dividida
CONFIANCA_ESSENCIAL = 0.90  # todo essencial acima disto entra, mesmo além do topo
ECONOMIA_MINIMA = 0.25      # fração de linhas evitadas para valer a pena estreitar
ORDEM = {'essencial': 3, 'complementar': 2, 'incerto': 1, 'irrelevante': 0}
LINHAS_MINIMAS_EVITADAS = 80
TAMANHO_MAXIMO = 2_000_000  # bytes; acima disso o mecanismo de blocos não cabe

NAO_TOCAR = {'claude.md', 'agents.md', 'skill.md', 'memory.md', 'readme.md'}
# Recortar por linhas um arquivo estruturado entrega um pedaço sintaticamente inválido: metade de
# um objeto JSON, um YAML sem a chave-mãe, um CSV sem cabeçalho. O agente costuma querer o objeto
# inteiro, e a economia não paga o risco. `.jsonl` e `.ndjson` ficam de fora da exclusão: cada
# linha é um registro completo, e um pedaço deles continua válido.
ESTRUTURADOS = {'.json', '.yaml', '.yml', '.xml', '.toml', '.csv', '.tsv', '.ini', '.cfg', '.plist'}
BINARIOS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.ipynb', '.sqlite', '.sqlite3',
            '.db', '.zip', '.gz', '.exe', '.dll', '.bin', '.woff', '.woff2', '.ttf', '.ico'}


def analisar(caminho, pedido, tool_input=None, *, transporte=None,
             tempo_total=nucleo.TEMPO_TOTAL_PADRAO):
    """Decide o intervalo. Devolve um dicionário com `acao` em {'nada', 'estreitar'}.

    `nada` traz o `motivo`; `estreitar` traz `offset` e `limit` para o `Read`, os blocos com a
    classe e a confiança de cada um, e as estimativas do que deixou de entrar no contexto.
    """
    tool_input = tool_input or {}
    inicio = time.time()
    caminho = Path(caminho)
    base = {'arquivo': str(caminho), 'acao': 'nada'}

    if tool_input.get('offset') is not None or tool_input.get('limit') is not None:
        # Registra o intervalo: uma releitura depois de um Read estreitado é o sinal de
        # arrependimento, e o tamanho dela diz quanto do que ficou de fora fez falta.
        return {**base, 'motivo': 'read ja delimitado',
                'offset': tool_input.get('offset'), 'limit': tool_input.get('limit')}
    if not pedido:
        return {**base, 'motivo': 'sem pedido vigente'}
    if caminho.suffix.lower() in BINARIOS or caminho.name.lower() in NAO_TOCAR \
            or caminho.suffix.lower() in ESTRUTURADOS:
        return {**base, 'motivo': 'tipo de arquivo fora da camada'}
    try:
        if caminho.stat().st_size > TAMANHO_MAXIMO:
            return {**base, 'motivo': 'arquivo grande demais'}
        linhas = caminho.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
    except OSError:
        return {**base, 'motivo': 'nao foi possivel ler'}
    total = len(linhas)
    base['linhas'] = total
    if total < MINIMO_DE_LINHAS:
        return {**base, 'motivo': 'arquivo pequeno'}

    blocos = nucleo.dividir_em_blocos(linhas)
    if not blocos:
        return {**base, 'motivo': 'nao coube em blocos'}

    estados = [nucleo.estado_do_trecho(
        pedido, f'ARQUIVO {caminho.name}, linhas {a}-{b} de {total}:', ''.join(linhas[a-1:b]))
        for a, b in blocos]
    resultados = nucleo.classificar_em_paralelo(
        estados, nucleo.PERGUNTA_DE_CONTEXTO, origem='camada-leitura',
        tempo_total=tempo_total, transporte=transporte)
    resumo = nucleo.resumo_das_chamadas(resultados)
    base.update({**resumo, 'latencia_ms': round((time.time() - inicio) * 1000),
                 'blocos': len(blocos)})
    if resumo['falha']:
        return {**base, 'motivo': f'falha: {resumo["falha"]}'}

    detalhe = []
    for (a, b), (respostas, _) in zip(blocos, resultados):
        classe, confianca = nucleo.escolha(respostas, 'relevancia')
        detalhe.append({'inicio': a, 'fim': b, 'classe': classe, 'confianca': confianca,
                        'descarta_a_099': classe == 'irrelevante'
                        and (confianca or 0) >= nucleo.CORTE_DE_DESCARTE})
    base['classes'] = detalhe
    essenciais = [d for d in detalhe if d['classe'] == 'essencial']
    if len(essenciais) * 2 >= len(detalhe):
        return {**base, 'motivo': 'metade ou mais dos blocos e essencial; arquivo inteiro interessa'}
    obrigatorios = [i for i, d in enumerate(detalhe)
                    if d['classe'] == 'essencial' and (d['confianca'] or 0) >= CONFIANCA_ESSENCIAL]
    if obrigatorios:
        indices = set(range(max(0, min(obrigatorios) - 1), min(len(detalhe), max(obrigatorios) + 2)))
        politica = 'essencial>=0,90 com vizinhos'
    else:
        topo = sorted(range(len(detalhe)), key=lambda i: (ORDEM.get(detalhe[i]['classe'], -1),
                                                          detalhe[i]['confianca'] or 0), reverse=True)
        indices = set(topo[:BLOCOS_NO_TOPO])
        politica = 'top3'
    for i, d in enumerate(detalhe):
        d['mantido'] = i in indices
    janela = [d for d in detalhe if d['mantido']]
    primeiro, ultimo = janela[0]['inicio'], janela[-1]['fim']
    lidas = ultimo - primeiro + 1
    evitadas = total - lidas
    caracteres_evitados = sum(len(l) for l in linhas[:primeiro-1]) + \
        sum(len(l) for l in linhas[ultimo:])
    base.update({'linhas_lidas': lidas, 'linhas_evitadas': evitadas,
                 'caracteres_evitados': caracteres_evitados,
                 'tokens_evitados_estimados': nucleo.tokens(caracteres_evitados),
                 'mantidos': len(janela),
                 'descartaveis_a_099': sum(d['descarta_a_099'] for d in detalhe),
                 'politica': politica})
    if evitadas < LINHAS_MINIMAS_EVITADAS or evitadas / total < ECONOMIA_MINIMA:
        return {**base, 'motivo': 'economia pequena demais para valer o intervalo'}
    return {**base, 'acao': 'estreitar', 'offset': primeiro, 'limit': lidas}


def nota_para_o_agente(decisao):
    """Curta: cada token dela é pago pelo modelo caro, e ela precisa dizer como ler o resto."""
    nome = Path(decisao['arquivo']).name
    a = decisao['offset']
    b = a + decisao['limit'] - 1
    return (f"[jev/leitura] {nome} tem {decisao['linhas']} linhas; este Read foi limitado às "
            f"linhas {a}–{b}, a janela que cobre os {decisao['mantidos']} de {decisao['blocos']} "
            f"blocos que o Jev pôs no topo para o pedido vigente. Se precisar do restante, "
            f"chame Read com offset e limit.")
