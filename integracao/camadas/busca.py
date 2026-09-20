"""Camada de busca: depois de um `Grep` que devolve muitos arquivos, o Jev diz por onde começar.

O resultado do Grep já entrou no contexto; o que esta camada poupa é o que vem DEPOIS — os
`Read` que o agente faria em cada arquivo listado. Ela classifica cada arquivo (caminho mais
as linhas que casaram, quando o Grep as trouxe) contra o pedido vigente e injeta uma nota de
três linhas: leia primeiro estes, provavelmente irrelevantes aqueles.

É a aplicação de ordenação (E16: 8 de 8 fontes essenciais no topo, contra 7 de 8 da busca
lexical), mas com um candidato mais pobre — nome de arquivo e poucas linhas — que o estudo
não mediu. Por isso a nota nunca esconde nada: a lista completa do Grep continua no contexto,
e o registro guarda a ordem sugerida para que a medição confira depois se o agente leu o que
o Jev pôs no topo.
"""
import re
import time
from pathlib import Path

from . import nucleo

MINIMO_DE_ARQUIVOS = 6
MAXIMO_DE_ARQUIVOS = 16
LINHAS_POR_ARQUIVO = 5

# "caminho:linha:texto" (content), "caminho:contagem" (count) e "caminho" (files). Letra de
# unidade do Windows ("C:\...") não é separador.
LINHA_COM_CONTEUDO = re.compile(r'^(?P<arquivo>(?:[A-Za-z]:)?[^:\n]+?):(?P<linha>\d+)[:-](?P<texto>.*)$')
LINHA_COM_CONTAGEM = re.compile(r'^(?P<arquivo>(?:[A-Za-z]:)?[^:\n]+?):(?P<n>\d+)$')


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
    """Devolve lista de (arquivo, [linhas casadas]) na ordem em que o Grep os trouxe."""
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


def analisar(resposta, pedido, tool_input=None, *, transporte=None,
             tempo_total=nucleo.TEMPO_TOTAL_PADRAO):
    tool_input = tool_input or {}
    inicio = time.time()
    base = {'acao': 'nada', 'padrao': (tool_input.get('pattern') or '')[:200]}
    if not pedido:
        return {**base, 'motivo': 'sem pedido vigente'}
    grupos = agrupar(texto_da_resposta(resposta))
    base['arquivos'] = len(grupos)
    if len(grupos) < MINIMO_DE_ARQUIVOS:
        return {**base, 'motivo': 'poucos arquivos'}
    candidatos = grupos[:MAXIMO_DE_ARQUIVOS]
    estados = []
    for arquivo, linhas in candidatos:
        amostra = '\n'.join(linhas[:LINHAS_POR_ARQUIVO]) or '(o Grep so trouxe o caminho)'
        estados.append(nucleo.estado_do_trecho(
            pedido, f'ARQUIVO CANDIDATO {arquivo}\nLINHAS QUE CASARAM COM "{base["padrao"]}":',
            amostra))
    resultados = nucleo.classificar_em_paralelo(
        estados, nucleo.PERGUNTA_DE_CONTEXTO, origem='camada-busca',
        tempo_total=tempo_total, transporte=transporte, limite=4000)
    resumo = nucleo.resumo_das_chamadas(resultados)
    base.update({**resumo, 'latencia_ms': round((time.time() - inicio) * 1000)})
    if resumo['falha']:
        return {**base, 'motivo': f'falha: {resumo["falha"]}'}
    ordem = {'essencial': 3, 'complementar': 2, 'incerto': 1, 'irrelevante': 0}
    classes = []
    for (arquivo, _), (respostas, _) in zip(candidatos, resultados):
        classe, confianca = nucleo.escolha(respostas, 'relevancia')
        classes.append({'arquivo': arquivo, 'classe': classe, 'confianca': confianca})
    classes.sort(key=lambda c: (ordem.get(c['classe'], -1), c['confianca'] or 0), reverse=True)
    primeiro = [c['arquivo'] for c in classes if c['classe'] == 'essencial']
    depois = [c['arquivo'] for c in classes if c['classe'] == 'complementar']
    fora = [c['arquivo'] for c in classes
            if c['classe'] == 'irrelevante' and (c['confianca'] or 0) >= nucleo.CORTE_DE_DESCARTE]
    base.update({'classes': classes, 'primeiro': primeiro, 'depois': depois, 'fora': fora,
                 'nao_classificados': len(grupos) - len(candidatos)})
    if not primeiro and not fora:
        return {**base, 'motivo': 'nada a ordenar: nenhum essencial nem descartável'}
    return {**base, 'acao': 'sugerir'}


def nota_para_o_agente(decisao):
    nome = lambda a: Path(a).name if len(a) > 60 else a
    partes = [f"[jev/busca] {decisao['arquivos']} arquivos no Grep."]
    if decisao['primeiro']:
        partes.append('Leia primeiro: ' + ', '.join(nome(a) for a in decisao['primeiro'][:5]) + '.')
    if decisao['fora']:
        partes.append('Provavelmente irrelevantes ao pedido (confiança ≥ 0,99): '
                      + ', '.join(nome(a) for a in decisao['fora'][:6]) + '.')
    if decisao['nao_classificados']:
        partes.append(f"{decisao['nao_classificados']} arquivos além do 16º não foram classificados.")
    return ' '.join(partes)
