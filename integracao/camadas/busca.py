"""Camada de busca: depois de uma listagem com muitos itens, o Jev diz por onde começar.

Vale para o `Grep` e o `Glob` (itens são arquivos) e para as listagens externas — busca de
threads no Gmail, arquivos no Drive, eventos na Agenda, resultados do WebSearch — em que
cada item é um registro que o agente abriria em seguida. O resultado da listagem já entrou
no contexto; o que esta camada poupa é o que vem DEPOIS: os `Read`, `get_message` e
`read_file_content` que o agente faria item a item. Ela classifica cada item contra o pedido
vigente e injeta uma nota curta: leia primeiro estes, provavelmente irrelevantes aqueles.

É a aplicação de triagem e ordenação (E1: 92,5% a 98,9% em triagem; E16: 8 de 8 fontes
essenciais no topo), mas com um candidato mais pobre — nome de arquivo e poucas linhas, ou
o assunto e o resumo de um e-mail — que o estudo não mediu. Por isso a nota nunca esconde
nada: a lista completa continua no contexto, e o registro guarda a ordem sugerida para que
a medição confira depois se o agente abriu o que o Jev pôs no topo.
"""
import json
import re
import time
from pathlib import Path

from . import nucleo

MINIMO_DE_ITENS = 6
MAXIMO_DE_ITENS = 16
LINHAS_POR_ARQUIVO = 5
CARACTERES_POR_ITEM = 700

FERRAMENTAS_DE_ARQUIVO = ('Grep', 'Glob')
FERRAMENTAS_DE_LISTAGEM = (
    'WebSearch',
    'mcp__claude_ai_Gmail__search_threads', 'mcp__claude_ai_Gmail__list_drafts',
    'mcp__claude_ai_Google_Drive__search_files', 'mcp__claude_ai_Google_Drive__list_recent_files',
    'mcp__claude_ai_Google_Calendar__list_events', 'mcp__claude_ai_Google_Calendar__search_events',
)
FERRAMENTAS = FERRAMENTAS_DE_ARQUIVO + FERRAMENTAS_DE_LISTAGEM
MATCHER = '|'.join(f.replace('-', r'\-') for f in FERRAMENTAS)

# "caminho:linha:texto" (content), "caminho:contagem" (count) e "caminho" (files). Letra de
# unidade do Windows ("C:\...") não é separador.
LINHA_COM_CONTEUDO = re.compile(r'^(?P<arquivo>(?:[A-Za-z]:)?[^:\n]+?):(?P<linha>\d+)[:-](?P<texto>.*)$')
LINHA_COM_CONTAGEM = re.compile(r'^(?P<arquivo>(?:[A-Za-z]:)?[^:\n]+?):(?P<n>\d+)$')

# Campos que identificam um item de listagem para o leitor, na ordem de preferência.
ROTULOS = ('subject', 'title', 'summary', 'name', 'snippet', 'id', 'threadId', 'url')


def texto_da_resposta(resposta):
    """O PostToolUse entrega `tool_response` em forma que varia; aqui vira texto."""
    if resposta is None:
        return ''
    if isinstance(resposta, str):
        return resposta
    if isinstance(resposta, dict):
        for chave in ('content', 'file', 'stdout', 'output', 'text', 'result', 'filenames'):
            valor = resposta.get(chave)
            if isinstance(valor, str) and valor:
                return valor
            if isinstance(valor, list) and valor:
                return '\n'.join(texto_da_resposta(v) for v in valor)
            if isinstance(valor, dict):
                dentro = texto_da_resposta(valor)
                if dentro:
                    return dentro
        return ''
    if isinstance(resposta, list):
        return '\n'.join(texto_da_resposta(v) for v in resposta)
    return str(resposta)


def agrupar(texto):
    """Grep/Glob: lista de (arquivo, [linhas casadas]) na ordem em que vieram."""
    grupos = {}
    for linha in texto.splitlines():
        linha = linha.rstrip()
        if not linha or linha.startswith(('Found ', 'No files', 'No matches')):
            continue
        m = LINHA_COM_CONTEUDO.match(linha)
        if m:
            grupos.setdefault(m['arquivo'].strip(), []).append(m['texto'].strip())
            continue
        m = LINHA_COM_CONTAGEM.match(linha)
        if m:
            grupos.setdefault(m['arquivo'].strip(), [])
            continue
        if '/' in linha or '\\' in linha or '.' in linha:
            grupos.setdefault(linha.strip(), [])
    return list(grupos.items())


def _maior_lista_de_dicionarios(valor, profundidade=0):
    """Numa resposta JSON qualquer, a lista de registros é o que se quer ordenar."""
    if profundidade > 4:
        return []
    melhor = []
    if isinstance(valor, list):
        if valor and all(isinstance(v, dict) for v in valor):
            melhor = valor
        for v in valor:
            achado = _maior_lista_de_dicionarios(v, profundidade + 1)
            if len(achado) > len(melhor):
                melhor = achado
    elif isinstance(valor, dict):
        for v in valor.values():
            achado = _maior_lista_de_dicionarios(v, profundidade + 1)
            if len(achado) > len(melhor):
                melhor = achado
    return melhor


def itens_de_listagem(resposta):
    """Listagens externas: lista de (rótulo, texto do item) a partir do JSON devolvido."""
    dado = resposta
    if isinstance(resposta, (str, dict, list)):
        texto = texto_da_resposta(resposta) if not isinstance(resposta, str) else resposta
        if isinstance(resposta, str) or texto:
            try:
                dado = json.loads(texto)
            except ValueError:
                dado = resposta if not isinstance(resposta, str) else None
    registros = _maior_lista_de_dicionarios(dado) if dado is not None else []
    itens = []
    for i, r in enumerate(registros):
        rotulo = next((str(r[c]) for c in ROTULOS if r.get(c)), f'item {i + 1}')
        corpo = json.dumps(r, ensure_ascii=False)[:CARACTERES_POR_ITEM]
        itens.append((rotulo[:120], corpo))
    return itens


def candidatos(resposta, ferramenta, padrao=''):
    if ferramenta in FERRAMENTAS_DE_ARQUIVO:
        return [(arquivo, '\n'.join(linhas[:LINHAS_POR_ARQUIVO]) or '(so o caminho)',
                 f'ARQUIVO CANDIDATO {arquivo}\nLINHAS QUE CASARAM COM "{padrao}":')
                for arquivo, linhas in agrupar(texto_da_resposta(resposta))]
    return [(rotulo, corpo, f'ITEM DA LISTAGEM ({ferramenta}) — {rotulo}:')
            for rotulo, corpo in itens_de_listagem(resposta)]


def analisar(resposta, pedido, tool_input=None, *, ferramenta='Grep', transporte=None,
             tempo_total=nucleo.TEMPO_TOTAL_PADRAO):
    tool_input = tool_input or {}
    inicio = time.time()
    padrao = (tool_input.get('pattern') or tool_input.get('query') or tool_input.get('q') or '')[:200]
    base = {'acao': 'nada', 'ferramenta': ferramenta, 'padrao': padrao}
    if not pedido:
        return {**base, 'motivo': 'sem pedido vigente'}
    todos = candidatos(resposta, ferramenta, padrao)
    base['itens'] = len(todos)
    if len(todos) < MINIMO_DE_ITENS:
        return {**base, 'motivo': 'poucos itens'}
    escolhidos = todos[:MAXIMO_DE_ITENS]
    estados = [nucleo.estado_do_trecho(pedido, rotulo_estado, corpo)
               for _, corpo, rotulo_estado in escolhidos]
    resultados = nucleo.classificar_em_paralelo(
        estados, nucleo.PERGUNTA_DE_CONTEXTO, origem='camada-busca',
        tempo_total=tempo_total, transporte=transporte, limite=4000)
    resumo = nucleo.resumo_das_chamadas(resultados)
    base.update({**resumo, 'latencia_ms': round((time.time() - inicio) * 1000)})
    if resumo['falha']:
        return {**base, 'motivo': f'falha: {resumo["falha"]}'}
    ordem = {'essencial': 3, 'complementar': 2, 'incerto': 1, 'irrelevante': 0}
    classes = []
    for (rotulo, _, _), (respostas, _) in zip(escolhidos, resultados):
        classe, confianca = nucleo.escolha(respostas, 'relevancia')
        classes.append({'item': rotulo, 'classe': classe, 'confianca': confianca})
    classes.sort(key=lambda c: (ordem.get(c['classe'], -1), c['confianca'] or 0), reverse=True)
    primeiro = [c['item'] for c in classes if c['classe'] == 'essencial']
    depois = [c['item'] for c in classes if c['classe'] == 'complementar']
    fora = [c['item'] for c in classes
            if c['classe'] == 'irrelevante' and (c['confianca'] or 0) >= nucleo.CORTE_DE_DESCARTE]
    base.update({'classes': classes, 'primeiro': primeiro, 'depois': depois, 'fora': fora,
                 'nao_classificados': len(todos) - len(escolhidos)})
    if not primeiro and not fora:
        return {**base, 'motivo': 'nada a ordenar: nenhum essencial nem descartável'}
    return {**base, 'acao': 'sugerir'}


def nota_para_o_agente(decisao):
    nome = lambda a: Path(a).name if ('/' in a or '\\' in a) and len(a) > 60 else a
    partes = [f"[jev/busca] {decisao['itens']} itens em {decisao['ferramenta']}."]
    if decisao['primeiro']:
        partes.append('Abra primeiro: ' + '; '.join(nome(a) for a in decisao['primeiro'][:5]) + '.')
    if decisao['fora']:
        partes.append('Provavelmente irrelevantes ao pedido (confiança ≥ 0,99): '
                      + '; '.join(nome(a) for a in decisao['fora'][:6]) + '.')
    if decisao['nao_classificados']:
        partes.append(f"{decisao['nao_classificados']} itens além do 16º não foram classificados.")
    return ' '.join(partes)
