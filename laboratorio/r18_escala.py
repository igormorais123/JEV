"""R18 — a R17 em escala, com as perguntas geradas por máquina e filtradas por mecanismo.

A R17 deixou três coisas sem resolver, todas por falta de amostra:

    1. "Carregar os oito trechos foi pior que carregar os dois certos" -- 15 contra 18, p = 0,375.
       Se for real, selecionar não é só mais barato, é melhor. Com n = 20 não dá para dizer.
    2. Contra o BM25, 4 a 0 no pareamento e p = 0,125. Sugestivo e insuficiente.
    3. Quantos trechos mandar? Dois foi uma escolha minha, nunca medida. A curva entre economia
       e acerto não existe.

E deixou um defeito acionável: numa pergunta o Jev escolheu a função certa e a resposta saiu
errada porque a constante estava declarada **fora** da função. Isso vira a quarta pergunta:
recortar o candidato com o cabeçalho do módulo junto resolve?

**O gargalo era escrever as perguntas.** Vinte, à mão, com a expressão regular de verificação
antes de rodar. Aqui elas são geradas por um LLM a partir do próprio trecho, e o que as torna
utilizáveis não é confiar no gerador -- é o **filtro mecânico** que roda depois:

    a regex precisa casar com o texto do trecho alvo          (a resposta está mesmo lá)
    a regex não pode casar com mais de 2 dos 7 distratores     (a pergunta discrimina)
    a pergunta não pode citar o nome da função                 (senão a busca por nome resolve)

Uma pergunta que passa nos três tem a resposta verificável no alvo e não é respondível por
acaso. Nenhuma delas foi lida por mim antes de rodar, e é essa a diferença: o gabarito desta
rodada não é autoral.

**H18a.** Com n grande, a seleção do Jev não perde resposta contra carregar tudo.
**H18b.** O Jev supera o BM25 na colocação do alvo no topo, com p < 0,05.
**H18c.** A curva de k mostra um joelho: acima de certo k o acerto para de subir e o custo não.
**H18d.** Recortar com o cabeçalho do módulo aumenta o acerto sem mudar a ordenação.

**Falsificação.** Se `jev` perder mais de 10% dos casos contra `todos`, H18a cai e a economia
medida na R17 foi sorte de amostra pequena.

    python laboratorio/r18_escala.py --gerar     # gera e filtra as perguntas
    python laboratorio/r18_escala.py --rodar     # executa os arranjos
"""
import argparse
import ast
import json
import random
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import chave, em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r15_adversario_externo import http  # noqa: E402
from laboratorio.r17_economia_de_contexto import (CRITERIOS_JEV, ORDEM_JEV,  # noqa: E402
                                                  ordenar_com_bm25, pool)

PERGUNTAS = RAIZ / 'laboratorio' / 'r18-perguntas.json'
DESTINO = RAIZ / 'laboratorio' / 'r18-escala.json'
SEMENTE = 20260920
ALVOS = 110          # funções sorteadas para virar pergunta
CANDIDATOS = 8
KS = (1, 2, 3, 5)
GERADOR = 'openai/gpt-oss-120b'
RESPONDEDOR = 'mistralai/mistral-nemo'

PEDIDO = (
    'Abaixo esta uma funcao Python de um projeto real. Escreva UMA pergunta factual que so '
    'possa ser respondida lendo esta funcao, e uma expressao regular Python que aceite a '
    'resposta correta.\n\n'
    'Regras: a pergunta nao pode citar o nome da funcao nem o nome do arquivo. A pergunta deve '
    'ter resposta curta e objetiva (um valor, um nome, um comportamento). A regex deve ser '
    'permissiva quanto a redacao e estrita quanto ao conteudo, e deve casar com algum texto '
    'presente no corpo da funcao.\n\n'
    'Responda APENAS com JSON: {{"pergunta": "...", "regex": "..."}}\n\n'
    'Funcao:\n{trecho}')


# ------------------------------------------------------------------ geração

def gerar(api_key):
    todas = pool()
    sorteio = random.Random(SEMENTE)
    chaves = sorted(todas)
    sorteio.shuffle(chaves)
    escolhidos = [c for c in chaves if 300 < len(todas[c]) < 3000][:ALVOS]
    print(f'{len(escolhidos)} funções vão ao gerador')

    def uma(alvo):
        # 1.600 tokens, nao 400: este gerador e um modelo de raciocinio, e o rascunho dele sai
        # no campo `reasoning` consumindo o mesmo orcamento. Com 400, 88 das 110 chamadas
        # voltaram com `content` vazio -- pagas e inuteis. O diagnostico esta no historico.
        corpo = {'model': GERADOR, 'max_tokens': 1600, 'temperature': 0.4,
                 'response_format': {'type': 'json_object'},
                 'messages': [{'role': 'user',
                               'content': PEDIDO.format(trecho=todas[alvo][:3000])}]}
        status, resposta = http(corpo, api_key, rodada='R18-geracao', modelo=GERADOR)
        if status != 200:
            return None
        try:
            mensagem = resposta['choices'][0]['message']
        except (KeyError, IndexError, TypeError):
            return None
        bruto = (mensagem.get('content') or '').strip()
        if not bruto:
            # Ultimo recurso: o JSON as vezes aparece no fim do rascunho.
            achado = re.search(r'\{[^{}]*"pergunta"[^{}]*\}', mensagem.get('reasoning') or '',
                               re.S)
            bruto = achado.group(0) if achado else ''
        try:
            bloco = json.loads(bruto)
            return {'alvo': alvo, 'pergunta': str(bloco['pergunta']).strip(),
                    'regex': str(bloco['regex']).strip()}
        except (KeyError, TypeError, ValueError):
            return None

    brutas = [p for p in em_paralelo(escolhidos, uma, trabalhadores=8, rotulo='R18-gera') if p]
    print(f'{len(brutas)} perguntas geradas')

    sorteio2 = random.Random(SEMENTE + 7)
    aprovadas, recusas = [], {}
    for item in brutas:
        alvo, texto_alvo = item['alvo'], todas[item['alvo']]
        motivo = None
        try:
            padrao = re.compile(item['regex'], re.IGNORECASE)
        except re.error:
            motivo = 'regex invalida'
        if motivo is None:
            nome = alvo.split('::')[1]
            arquivo = alvo.split('::')[0].split('/')[-1].replace('.py', '')
            if nome.lower() in item['pergunta'].lower() or arquivo.lower() in item['pergunta'].lower():
                motivo = 'a pergunta cita o nome'
            elif not padrao.search(texto_alvo):
                motivo = 'a resposta nao esta no alvo'
        if motivo is None:
            outros = [c for c in chaves if c != alvo]
            sorteio2.shuffle(outros)
            distratores = outros[:CANDIDATOS - 1]
            casam = sum(1 for d in distratores if padrao.search(todas[d]))
            if casam > 2:
                motivo = f'a regex casa com {casam} distratores'
            else:
                item['distratores'] = distratores
        if motivo:
            recusas[motivo] = recusas.get(motivo, 0) + 1
        else:
            aprovadas.append(item)

    print(f'{len(aprovadas)} aprovadas pelo filtro; recusas: {recusas}')
    PERGUNTAS.write_text(json.dumps(
        {'semente': SEMENTE, 'gerador': GERADOR, 'pedido': PEDIDO,
         'aprovadas': aprovadas, 'recusas': recusas, 'geradas': len(brutas)},
        ensure_ascii=False, indent=1), encoding='utf-8')
    return aprovadas


# ------------------------------------------------------------------ execução

def com_cabecalho(caminho, trecho, todas_fontes):
    """O trecho mais as constantes de topo do módulo — a mitigação da H18d."""
    fonte = todas_fontes.get(caminho)
    if fonte is None:
        return trecho
    try:
        arvore = ast.parse(fonte)
    except SyntaxError:
        return trecho
    linhas = fonte.splitlines()
    topo = []
    for no in arvore.body:
        if isinstance(no, (ast.Assign, ast.AnnAssign)):
            topo.append('\n'.join(linhas[no.lineno - 1:no.end_lineno]))
    cabecalho = '\n'.join(topo)[:1500]
    return (cabecalho + '\n\n' + trecho) if cabecalho else trecho


def ordenar(caso, recorte):
    def julgar(candidato):
        estado = (f"Pergunta: {caso['pergunta']}\n\n"
                  f"Trecho de codigo ({candidato['chave']}):\n{candidato[recorte]}")
        respostas, _ = perguntar(estado, {'relevancia': {
            'type': 'choice',
            'instructions': 'Este trecho de codigo responde a pergunta acima?',
            'criteria': dict(CRITERIOS_JEV)}}, rodada='R18')
        bloco = (respostas or {}).get('relevancia') or {}
        return {**candidato, 'classe': bloco.get('choice'), 'confianca': bloco.get('confidence')}

    julgados = [julgar(c) for c in caso['candidatos']]
    julgados.sort(key=lambda c: (ORDEM_JEV.get(c['classe'], 9), -(c['confianca'] or 0)))
    return julgados


def responder(caso, trechos, recorte, api_key):
    contexto = '\n\n'.join(f"--- {t['chave']} ---\n{t[recorte]}" for t in trechos)
    corpo = {'model': RESPONDEDOR, 'max_tokens': 200, 'temperature': 0,
             'messages': [{'role': 'user', 'content':
                           f'Com base apenas nos trechos de codigo abaixo, responda em uma frase '
                           f'curta.\n\nPergunta: {caso["pergunta"]}\n\n{contexto}'}]}
    status, resposta = http(corpo, api_key, rodada='R18-resposta', modelo=RESPONDEDOR)
    bytes_enviados = len(contexto.encode('utf-8'))
    if status != 200:
        return None, bytes_enviados
    try:
        return resposta['choices'][0]['message']['content'], bytes_enviados
    except (KeyError, IndexError, TypeError):
        return None, bytes_enviados


def rodar(api_key):
    dados = json.loads(PERGUNTAS.read_text(encoding='utf-8'))
    todas = pool()
    fontes = {}
    for pasta in ('executor', 'integracao', 'laboratorio', 'lab'):
        for arquivo in (RAIZ / pasta).rglob('*.py'):
            caminho = arquivo.relative_to(RAIZ).as_posix()
            if 'tests' not in caminho and '__pycache__' not in caminho:
                try:
                    fontes[caminho] = arquivo.read_text(encoding='utf-8')
                except OSError:
                    pass

    sorteio = random.Random(SEMENTE + 13)
    casos = []
    for i, item in enumerate(dados['aprovadas']):
        chaves = [item['alvo']] + item['distratores']
        sorteio.shuffle(chaves)
        candidatos = []
        for c in chaves:
            arquivo = c.split('::')[0]
            candidatos.append({'chave': c, 'texto': todas[c],
                               'com_cabecalho': com_cabecalho(arquivo, todas[c], fontes),
                               'bytes': len(todas[c].encode('utf-8'))})
        casos.append({'id': f'e{i:03d}', 'pergunta': item['pergunta'], 'alvo': item['alvo'],
                      'aceita': item['regex'], 'candidatos': candidatos})

    print(f'{len(casos)} casos × {CANDIDATOS} candidatos × 2 recortes = '
          f'{len(casos) * CANDIDATOS * 2} chamadas de ordenação')

    ordens = {}
    for recorte in ('texto', 'com_cabecalho'):
        ordens[recorte] = em_paralelo(casos, lambda c, r=recorte: ordenar(c, r),
                                      trabalhadores=8, rotulo=f'R18-ord-{recorte[:4]}')

    tarefas = []
    for i, caso in enumerate(casos):
        jev = ordens['texto'][i]
        jev_cab = ordens['com_cabecalho'][i]
        bm25 = ordenar_com_bm25(caso)
        ao_acaso = list(caso['candidatos'])
        sorteio.shuffle(ao_acaso)
        arranjos = [('todos', caso['candidatos'], 'texto'),
                    ('bm25-2', bm25[:2], 'texto'),
                    ('sorteio-2', ao_acaso[:2], 'texto'),
                    ('jev-cab-2', jev_cab[:2], 'com_cabecalho')]
        for k in KS:
            arranjos.append((f'jev-{k}', jev[:k], 'texto'))
        for nome, trechos, recorte in arranjos:
            tarefas.append({'caso': caso, 'arranjo': nome, 'trechos': trechos,
                            'recorte': recorte})

    print(f'{len(tarefas)} chamadas de resposta')
    saidas = em_paralelo(tarefas,
                         lambda t: responder(t['caso'], t['trechos'], t['recorte'], api_key),
                         trabalhadores=6, rotulo='R18-resp')

    linhas = []
    for tarefa, (texto, bytes_enviados) in zip(tarefas, saidas):
        caso = tarefa['caso']
        try:
            certo = bool(texto and re.search(caso['aceita'], texto, re.IGNORECASE))
        except re.error:
            certo = False
        linhas.append({'id': caso['id'], 'arranjo': tarefa['arranjo'],
                       'alvo_presente': any(t['chave'] == caso['alvo'] for t in tarefa['trechos']),
                       'certo': certo, 'bytes': bytes_enviados,
                       'resposta': (texto or '')[:160]})

    analisar(linhas, casos, ordens)


def analisar(linhas, casos, ordens):
    resultado = {'casos': len(casos), 'candidatos': CANDIDATOS, 'ks': list(KS),
                 'respondedor': RESPONDEDOR, 'arranjos': {}, 'detalhe': linhas}
    base = [l for l in linhas if l['arranjo'] == 'todos']
    bytes_base = sum(l['bytes'] for l in base)

    ordem_exibicao = ['todos'] + [f'jev-{k}' for k in KS] + ['jev-cab-2', 'bm25-2', 'sorteio-2']
    print(f"\n   {'arranjo':12} {'acertos':>10} {'taxa':>7} {'IC95':>18} "
          f"{'alvo presente':>14} {'bytes':>10} {'economia':>9}")
    for arranjo in ordem_exibicao:
        grupo = [l for l in linhas if l['arranjo'] == arranjo]
        if not grupo:
            continue
        acertos = sum(1 for l in grupo if l['certo'])
        enviados = sum(l['bytes'] for l in grupo)
        bloco = {'n': len(grupo), 'acertos': acertos,
                 'taxa': round(acertos / len(grupo), 4),
                 'ic95': wilson(acertos, len(grupo)),
                 'alvo_presente': sum(1 for l in grupo if l['alvo_presente']),
                 'bytes': enviados,
                 'economia': round(1 - enviados / bytes_base, 4) if bytes_base else None}
        resultado['arranjos'][arranjo] = bloco
        print(f"   {arranjo:12} {acertos:>5}/{len(grupo):<4} {bloco['taxa']:>7.1%} "
              f"{str(bloco['ic95']):>18} {bloco['alvo_presente']:>10}/{len(grupo)} "
              f"{enviados:>10,} {bloco['economia']:>8.1%}")

    por_id = {}
    for linha in linhas:
        por_id.setdefault(linha['id'], {})[linha['arranjo']] = linha

    def pareado(a, b, campo='certo'):
        so_a = sum(1 for v in por_id.values()
                   if v.get(a, {}).get(campo) and not v.get(b, {}).get(campo))
        so_b = sum(1 for v in por_id.values()
                   if v.get(b, {}).get(campo) and not v.get(a, {}).get(campo))
        return {'so_' + a: so_a, 'so_' + b: so_b, 'p': mcnemar_exato(so_a, so_b)}

    resultado['pareado'] = {
        'H18a jev-2 vs todos (resposta)': pareado('jev-2', 'todos'),
        'H18b jev-2 vs bm25-2 (alvo no topo)': pareado('jev-2', 'bm25-2', 'alvo_presente'),
        'H18b jev-2 vs bm25-2 (resposta)': pareado('jev-2', 'bm25-2'),
        'H18d jev-cab-2 vs jev-2 (resposta)': pareado('jev-cab-2', 'jev-2'),
        'controle jev-2 vs sorteio-2': pareado('jev-2', 'sorteio-2'),
    }
    print('\n   comparações pareadas (McNemar exato)')
    for nome, bloco in resultado['pareado'].items():
        marca = ' *' if bloco['p'] < 0.05 else ''
        print(f'   {nome:38} {bloco}{marca}')

    print('\n   H18c — a curva de k')
    for k in KS:
        bloco = resultado['arranjos'].get(f'jev-{k}')
        if bloco:
            print(f"   k={k}: acerto {bloco['taxa']:.1%}, contexto {bloco['economia']:.1%} "
                  f"menor, alvo presente em {bloco['alvo_presente']}/{bloco['n']}")

    jev2, todos = resultado['arranjos']['jev-2'], resultado['arranjos']['todos']
    perdeu = resultado['pareado']['H18a jev-2 vs todos (resposta)']['so_todos']
    resultado['veredito'] = {
        'H18a': ('sustentada' if perdeu <= 0.10 * len(casos) else 'falsificada'),
        'H18b': ('sustentada'
                 if resultado['pareado']['H18b jev-2 vs bm25-2 (alvo no topo)']['p'] < 0.05
                 else 'nao demonstrada'),
        'H18d': ('sustentada'
                 if resultado['pareado']['H18d jev-cab-2 vs jev-2 (resposta)']['p'] < 0.05
                 else 'nao demonstrada'),
    }
    print(f"\n   veredito: {resultado['veredito']}")

    for caso in casos:
        for candidato in caso['candidatos']:
            candidato.pop('texto', None), candidato.pop('com_cabecalho', None)
    resultado['perguntas'] = [{'id': c['id'], 'pergunta': c['pergunta'], 'alvo': c['alvo'],
                               'aceita': c['aceita']} for c in casos]
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n   gravado em {DESTINO.name}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gerar', action='store_true')
    parser.add_argument('--rodar', action='store_true')
    args = parser.parse_args()
    api_key = chave()
    if args.gerar or not PERGUNTAS.exists():
        gerar(api_key)
    if args.rodar:
        rodar(api_key)


if __name__ == '__main__':
    main()
