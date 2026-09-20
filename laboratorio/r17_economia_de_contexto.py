"""R17 — a pergunta que o projeto inteiro nunca respondeu: quanto token isso economiza?

Todo relatório deste estudo carrega o mesmo campo vazio: `astra_savings_measured: null`. A
promessa que abriu o trabalho era usar o Jev, que custa US$ 0,042 por milhão de tokens, para
poupar o modelo caro. O E16 mediu ordenação e acertou 8 de 8, e ainda assim não podia dizer que
economizou nada — porque escolher bem os trechos só economiza se **a resposta continuar certa**
com os trechos escolhidos. Bytes selecionados não são tokens poupados.

Aqui a economia é medida com a resposta na mão. Vinte perguntas factuais sobre este próprio
repositório, cada uma com **verificação automática por expressão regular**: ou a resposta contém
o valor certo, ou não contém. Não há gabarito de opinião, não há anotador, não há critério meu
sobre o que é "uma boa resposta". Cada pergunta recebe oito candidatos -- o trecho que contém a
resposta e sete funções reais sorteadas do mesmo repositório -- e o mesmo modelo respondedor é
chamado quatro vezes:

    todos      os oito trechos, que é o que um agente sem seleção carregaria
    jev        os dois que o Jev ordenou no topo
    bm25       os dois que o BM25 ordenou no topo
    sorteio    dois trechos ao acaso, que é o piso de qualquer método

**H17.** Com os dois trechos do Jev, a taxa de acerto empata com a de carregar os oito, e o
contexto enviado cai mais de 60%.

**Critério de falsificação.** Se `jev` perder mais de um caso para `todos`, a seleção não
preserva a resposta e a economia é falsa — e o relatório continua dizendo que não mediu nada. Se
`bm25` empatar com `jev`, o Jev não é necessário nesta aplicação, e isso também será dito.

**Limite declarado.** Isto mede economia de **contexto de entrada num passo de pergunta e
resposta**, não a economia de uma sessão de trabalho inteira, onde o agente reescreve, testa e
volta atrás. E o respondedor é um LLM barato, não o Opus: ele é mais sensível a contexto ruim,
então o ganho aqui é um limite superior do que se veria com um modelo mais forte.

    python laboratorio/r17_economia_de_contexto.py
"""
import ast
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import chave, em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r15_adversario_externo import http  # noqa: E402

DESTINO = RAIZ / 'laboratorio' / 'r17-economia-de-contexto.json'
SEMENTE = 20260919
CANDIDATOS = 8
TOPO = 2
RESPONDEDOR = 'mistralai/mistral-nemo'

# As vinte perguntas. `alvo` é o arquivo e a função cujo corpo contém a resposta; `aceita` é a
# expressão regular que decide se a resposta está certa. Escrever a regex ANTES de rodar é o que
# tira o julgamento da equação -- não dá para afrouxar o critério depois de ver o resultado.
PERGUNTAS = [
    ('executor/runner.py::load_api_key',
     'De onde a chave da API e lida quando ela nao esta na variavel de ambiente?',
     r'\.env'),
    ('laboratorio/nucleo.py::em_paralelo',
     'Quantas linhas em paralelo o laboratorio usa por padrao ao despachar em lote?',
     r'\b8\b|\boito\b'),
    ('laboratorio/nucleo.py::wilson',
     'Que valor de z o intervalo de confianca usa por padrao?',
     r'1[.,]96'),
    ('laboratorio/nucleo.py::bootstrap_diferenca',
     'Quantas reamostragens o bootstrap faz por padrao?',
     r'10[.,]?000'),
    ('laboratorio/nucleo.py::mcnemar_exato',
     'O teste de McNemar aqui usa aproximacao normal ou a distribuicao binomial exata?',
     r'binomial|exat'),
    ('executor/shared.py::ask',
     'Qual o tamanho maximo do payload, em bytes, antes de o envio ser recusado?',
     r'90[._,]?000|90\s*mil'),
    ('executor/shared.py::strict_answers',
     'Que faixa de valores a confianca precisa respeitar para a resposta ser aceita?',
     r'0\s*(a|e|-|até|ate|<=|,)\s*1|entre\s*0|\[0'),
    ('integracao/jev_router/roteador.py::impressao',
     'Que algoritmo de hash e usado para a impressao digital do pedido?',
     r'sha[\s-]?256'),
    ('integracao/jev_router/orcamento.py::pode_gastar',
     'O que a funcao devolve quando o gasto ultrapassa o teto: uma excecao ou um par com o motivo?',
     r'par|tupla|tuple|dois valores|False.*motivo|motivo.*False|booleano'),
    ('executor/run_e4_ressalvas.py::bm25',
     'Quais sao os dois parametros de ajuste do BM25 nesta implementacao?',
     r'k1.*b\b|b\b.*k1'),
    ('executor/run_e6_repetibilidade.py::entropia',
     'A entropia calculada aqui usa logaritmo de base 2?',
     r'\blog2\b|base\s*2|\b2\b'),
    ('executor/pricing.py::usd_to_nusd',
     'Por qual fator o valor em dolares e multiplicado para virar a unidade inteira do ledger?',
     r'10\*\*9|1e9|1[._,]?000[._,]?000[._,]?000|bilh'),
    ('integracao/jev_router/redacao.py::limpar',
     'O que a funcao devolve alem do texto limpo?',
     r'quantos|contagem|lista|numero|achados|padr|quantidade|marcas|substitu'),
    ('executor/runner.py::validate_contract',
     'O que acontece quando a resposta traz uma pergunta que nao foi feita?',
     r'erro|excec|exce|ValueError|rejeit|invalid|falha|levanta|raise'),
    ('laboratorio/r16_guarda_de_comando.py::placar',
     'Quando ha corte de confianca, o que acontece com o caso abaixo do corte?',
     r'confirma'),
    ('integracao/hooks/jev_guarda_comando.py::avaliar',
     'O que a funcao devolve quando a regra por palavra nao barrou o comando?',
     r'None|nada|nulo|nenhum'),
    ('executor/run_e8_anotador.py::kappa_cohen',
     'Qual estatistica de concordancia entre anotadores e calculada?',
     r'kappa|capa'),
    ('integracao/jev_router/politica.py::decidir',
     'Que campo da resposta do modelo e comparado com o corte antes de sugerir a skill?',
     r'confian|confidence'),
    ('executor/analise.py::bootstrap_cluster',
     'A reamostragem e feita por caso individual ou por grupo?',
     r'grupo|cluster|famil|conglomerado|bloco'),
    ('laboratorio/nucleo.py::gasto_total_autorizado',
     'De qual fonte o gasto acumulado e lido?',
     r'ledger|sqlite|livro'),
]


def pool():
    """Toda função de topo de módulo do código do projeto, com o código-fonte."""
    saida = {}
    for pasta in ('executor', 'integracao', 'laboratorio', 'lab'):
        for arquivo in sorted((RAIZ / pasta).rglob('*.py')):
            caminho = arquivo.relative_to(RAIZ).as_posix()
            if 'tests' in caminho or '__pycache__' in caminho:
                continue
            try:
                fonte = arquivo.read_text(encoding='utf-8')
                arvore = ast.parse(fonte)
            except (OSError, SyntaxError):
                continue
            linhas = fonte.splitlines()
            for no in arvore.body:
                if not isinstance(no, ast.FunctionDef):
                    continue
                trecho = '\n'.join(linhas[no.lineno - 1:no.end_lineno])
                # Teto de tamanho do trecho. Comecou em 2.600 e duas funcoes do proprio
                # gabarito ficaram de fora, o que teria trocado a pergunta por causa de um
                # limite tecnico -- ajuste feito antes de rodar, e declarado aqui.
                if len(trecho) > 4600:
                    continue
                saida[f'{caminho}::{no.name}'] = trecho
    return saida


def montar():
    todas = pool()
    faltando = [alvo for alvo, _, _ in PERGUNTAS if alvo not in todas]
    if faltando:
        raise SystemExit(f'alvo inexistente no repositorio: {faltando}')
    sorteio = random.Random(SEMENTE)
    chaves = sorted(todas)
    casos = []
    for i, (alvo, pergunta, aceita) in enumerate(PERGUNTAS):
        distratores = [c for c in chaves if c != alvo]
        sorteio.shuffle(distratores)
        escolhidos = [alvo] + distratores[:CANDIDATOS - 1]
        sorteio.shuffle(escolhidos)
        casos.append({'id': f'q{i:02d}', 'pergunta': pergunta, 'alvo': alvo, 'aceita': aceita,
                      'candidatos': [{'chave': c, 'texto': todas[c],
                                      'bytes': len(todas[c].encode('utf-8'))}
                                     for c in escolhidos]})
    return casos


# ------------------------------------------------------------------ ordenadores

ORDEM_JEV = {'essencial': 0, 'complementar': 1, 'incerto': 2, 'irrelevante': 3}
CRITERIOS_JEV = {
    'essencial': 'Este trecho contem a resposta da pergunta. Sem ele nao da para responder.',
    'complementar': 'Ajuda a entender o contexto, mas nao contem a resposta.',
    'incerto': 'Nao da para dizer sem ver mais codigo.',
    'irrelevante': 'Nao tem relacao com a pergunta.',
}


def ordenar_com_jev(caso):
    def julgar(candidato):
        estado = (f"Pergunta: {caso['pergunta']}\n\n"
                  f"Trecho de codigo ({candidato['chave']}):\n{candidato['texto']}")
        respostas, _ = perguntar(estado, {'relevancia': {
            'type': 'choice',
            'instructions': 'Este trecho de codigo responde a pergunta acima?',
            'criteria': dict(CRITERIOS_JEV)}}, rodada='R17')
        bloco = (respostas or {}).get('relevancia') or {}
        return {**candidato, 'classe': bloco.get('choice'),
                'confianca': bloco.get('confidence')}

    julgados = [julgar(c) for c in caso['candidatos']]
    # essencial > complementar > incerto > irrelevante; a confiança desempata dentro da classe.
    julgados.sort(key=lambda c: (ORDEM_JEV.get(c['classe'], 9), -(c['confianca'] or 0)))
    return julgados


def tokeniza(texto):
    return re.findall(r'[a-z_]{2,}', texto.lower())


def ordenar_com_bm25(caso, k1=1.5, b=0.75):
    """BM25 de verdade, não contagem de termos. É a linha de base honesta para recuperação."""
    import math
    docs = [tokeniza(c['texto']) for c in caso['candidatos']]
    media = sum(len(d) for d in docs) / len(docs)
    consulta = tokeniza(caso['pergunta'])
    freq_doc = Counter(t for d in docs for t in set(d))
    pontos = []
    for candidato, doc in zip(caso['candidatos'], docs):
        contagem = Counter(doc)
        total = 0.0
        for termo in consulta:
            if termo not in contagem:
                continue
            n = freq_doc[termo]
            idf = math.log(1 + (len(docs) - n + 0.5) / (n + 0.5))
            tf = contagem[termo]
            total += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(doc) / media))
        pontos.append({**candidato, 'bm25': round(total, 4)})
    pontos.sort(key=lambda c: -c['bm25'])
    return pontos


# ------------------------------------------------------------------ respondedor

def responder(caso, trechos, api_key):
    contexto = '\n\n'.join(f"--- {t['chave']} ---\n{t['texto']}" for t in trechos)
    corpo = {'model': RESPONDEDOR, 'max_tokens': 220, 'temperature': 0,
             'messages': [{'role': 'user', 'content':
                           f'Com base apenas nos trechos de codigo abaixo, responda em uma frase '
                           f'curta e direta.\n\nPergunta: {caso["pergunta"]}\n\n{contexto}'}]}
    status, resposta = http(corpo, api_key, rodada='R17-resposta', modelo=RESPONDEDOR)
    if status != 200:
        return None, len(contexto.encode('utf-8'))
    try:
        return resposta['choices'][0]['message']['content'], len(contexto.encode('utf-8'))
    except (KeyError, IndexError, TypeError):
        return None, len(contexto.encode('utf-8'))


def main():
    api_key = chave()
    casos = montar()
    print(f'{len(casos)} perguntas × {CANDIDATOS} candidatos = '
          f'{len(casos) * CANDIDATOS} chamadas de ordenação ao Jev')

    ordenados = em_paralelo(casos, ordenar_com_jev, trabalhadores=8, rotulo='R17-ordem')

    sorteio = random.Random(SEMENTE + 1)
    tarefas = []
    for caso, jev in zip(casos, ordenados):
        bm25 = ordenar_com_bm25(caso)
        ao_acaso = list(caso['candidatos'])
        sorteio.shuffle(ao_acaso)
        caso['_jev'], caso['_bm25'] = jev, bm25
        for arranjo, trechos in (('todos', caso['candidatos']),
                                 ('jev', jev[:TOPO]),
                                 ('bm25', bm25[:TOPO]),
                                 ('sorteio', ao_acaso[:TOPO])):
            tarefas.append({'caso': caso, 'arranjo': arranjo, 'trechos': trechos})

    print(f'{len(tarefas)} chamadas de resposta ao {RESPONDEDOR}')
    saidas = em_paralelo(tarefas, lambda t: responder(t['caso'], t['trechos'], api_key),
                         trabalhadores=6, rotulo='R17-resp')

    linhas = []
    for tarefa, (texto, bytes_enviados) in zip(tarefas, saidas):
        caso = tarefa['caso']
        certo = bool(texto and re.search(caso['aceita'], texto, re.IGNORECASE))
        linhas.append({'id': caso['id'], 'arranjo': tarefa['arranjo'],
                       'alvo_no_topo': any(t['chave'] == caso['alvo'] for t in tarefa['trechos']),
                       'certo': certo, 'bytes': bytes_enviados,
                       'resposta': (texto or '')[:200]})

    resultado = {'perguntas': len(casos), 'candidatos': CANDIDATOS, 'topo': TOPO,
                 'respondedor': RESPONDEDOR, 'arranjos': {}, 'detalhe': linhas}

    base = [l for l in linhas if l['arranjo'] == 'todos']
    bytes_base = sum(l['bytes'] for l in base)

    print(f"\n   {'arranjo':10} {'acertos':>9} {'IC95':>18} {'alvo no topo':>13} "
          f"{'bytes':>10} {'economia':>10}")
    for arranjo in ('todos', 'jev', 'bm25', 'sorteio'):
        grupo = [l for l in linhas if l['arranjo'] == arranjo]
        acertos = sum(1 for l in grupo if l['certo'])
        enviados = sum(l['bytes'] for l in grupo)
        bloco = {'n': len(grupo), 'acertos': acertos,
                 'taxa': round(acertos / len(grupo), 4) if grupo else None,
                 'ic95': wilson(acertos, len(grupo)),
                 'alvo_no_topo': sum(1 for l in grupo if l['alvo_no_topo']),
                 'bytes': enviados,
                 'economia': round(1 - enviados / bytes_base, 4) if bytes_base else None}
        resultado['arranjos'][arranjo] = bloco
        print(f"   {arranjo:10} {acertos:>4}/{len(grupo):<4} {str(bloco['ic95']):>18} "
              f"{bloco['alvo_no_topo']:>10}/{len(grupo)} {enviados:>10,} "
              f"{bloco['economia']:>9.1%}")

    # O que decide: o Jev perde caso para o contexto inteiro? E ele bate o BM25?
    por_id = {}
    for linha in linhas:
        por_id.setdefault(linha['id'], {})[linha['arranjo']] = linha['certo']
    def pareado(a, b):
        so_a = sum(1 for v in por_id.values() if v.get(a) and not v.get(b))
        so_b = sum(1 for v in por_id.values() if v.get(b) and not v.get(a))
        return {'so_' + a: so_a, 'so_' + b: so_b, 'p_mcnemar': mcnemar_exato(so_a, so_b)}
    resultado['pareado'] = {'jev_vs_todos': pareado('jev', 'todos'),
                            'jev_vs_bm25': pareado('jev', 'bm25'),
                            'jev_vs_sorteio': pareado('jev', 'sorteio')}
    print('\n   comparações pareadas (McNemar exato)')
    for nome, bloco in resultado['pareado'].items():
        print(f"   {nome:18} {bloco}")

    jev, todos, bm25 = (resultado['arranjos'][k] for k in ('jev', 'bm25', 'todos'))
    perdeu = resultado['pareado']['jev_vs_todos']['so_todos']
    resultado['veredito'] = (
        'H17 falsificada: a selecao perde resposta' if perdeu > 1 else
        'inconclusiva: o BM25 empata e o Jev nao e necessario'
        if jev['acertos'] <= bm25['acertos'] else
        'H17 sustentada')
    print(f"\n   veredito: {resultado['veredito']}")

    for caso in casos:
        caso.pop('_jev', None), caso.pop('_bm25', None)
        for candidato in caso['candidatos']:
            candidato.pop('texto', None)
    resultado['casos'] = casos
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
