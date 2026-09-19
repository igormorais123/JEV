"""O gabarito oficial do estudo, num lugar só.

Havia três gabaritos circulando ao mesmo tempo — o do autor, o do anotador local e o adjudicado
— e cada parte do painel usava o que tinha à mão. O resultado foi um placar que se contradizia:
um cartão dizia 3 erros, o outro dizia 4, os dois certos em gabaritos diferentes, e nenhum dos
dois dizia qual estava usando.

Aqui o gabarito oficial é definido uma vez: vale o do autor, **exceto** nos casos que foram
adjudicados por um terceiro juiz cego, onde vale a adjudicação. Quem consome declara qual usou.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPORA = [('data/corpus/triagem-piloto.jsonl', 'piloto'),
           ('data/corpus/triagem-confirmacao.jsonl', 'confirmacao')]
ADJUDICACAO = ROOT / 'runs' / 'e8-anotador' / 'adjudicacao.json'


ANOTACAO = ROOT / 'runs' / 'e8-anotador' / 'relatorio.json'


def do_anotador_local():
    """O gabarito do anotador independente, caso a caso.

    Ele existe desde o E8 e ficou fora dos cartoes por seis rodadas: o painel ensinava tres
    gabaritos no cartao do E8 e, nos cartoes que o olho le primeiro, fingia que eram dois.
    E o terceiro e o mais severo.
    """
    if not ANOTACAO.exists():
        return {}
    dados = json.loads(ANOTACAO.read_text(encoding='utf-8'))
    return {a['case_id']: a['anotador'] for a in dados['anotacoes'] if a.get('anotador')}


def do_autor():
    """O gabarito como foi pré-registrado, antes de qualquer adjudicação."""
    mapa = {}
    for arquivo, conjunto in CORPORA:
        alvo = ROOT / arquivo
        if not alvo.exists():
            continue
        for linha in alvo.read_text(encoding='utf-8').splitlines():
            if linha.strip():
                d = json.loads(linha)
                mapa[d['case_id']] = {'gold': d['gold'], 'family': d['family'],
                                      'conjunto': conjunto, 'origem': 'autor'}
    return mapa


def adjudicado():
    """O gabarito oficial: o do autor, com os casos em disputa substituídos pela adjudicação."""
    mapa = do_autor()
    if not ADJUDICACAO.exists():
        return mapa, {'adjudicado': False, 'casos_substituidos': []}
    dados = json.loads(ADJUDICACAO.read_text(encoding='utf-8'))
    substituidos = []
    for caso in dados['casos']:
        entrada = mapa.get(caso['case_id'])
        if entrada is None:
            continue
        if entrada['gold'] != caso['terceiro_juiz']:
            substituidos.append({'case_id': caso['case_id'], 'de': entrada['gold'],
                                 'para': caso['terceiro_juiz']})
        entrada['gold'] = caso['terceiro_juiz']
        entrada['origem'] = 'adjudicado'
    return mapa, {'adjudicado': True, 'juiz': dados['terceiro_juiz'],
                  'casos_em_disputa': len(dados['casos']),
                  'casos_substituidos': substituidos}


def rotulo(procedencia):
    """Frase curta para o painel dizer, em cada cartão, qual gabarito está por trás do número."""
    if not procedencia.get('adjudicado'):
        return 'gabarito do autor, sem adjudicação'
    n = len(procedencia['casos_substituidos'])
    if not n:
        return 'gabarito adjudicado (a adjudicação confirmou o autor em todos os casos em disputa)'
    return f'gabarito adjudicado ({n} caso(s) mudaram em relação ao do autor)'


def desempenho(relatorio, campo_resposta='jev'):
    """Recalcula acertos de um relatório sob os DOIS gabaritos, do autor e o oficial.

    O painel lia a acurácia já calculada dentro de cada relatório, e essas acurácias foram
    gravadas antes da adjudicação. O resultado foi um cartão que estampava 97,5% no número
    grande e dizia, na linha de baixo, que no gabarito oficial não havia erro nenhum. Números
    de gabaritos diferentes na mesma caixa. Aqui os dois saem da mesma conta.
    """
    caminho = ROOT / relatorio if not str(relatorio).startswith(str(ROOT)) else Path(relatorio)
    if not caminho.exists():
        return None
    casos = json.loads(caminho.read_text(encoding='utf-8'))['casos']
    oficial, procedencia = adjudicado()
    programados = len(casos)
    acertos_autor = sum(1 for c in casos if c.get(campo_resposta) == c['gold'])
    erros_oficial, acertos_oficial = [], 0
    for c in casos:
        alvo = oficial.get(c['case_id'], {}).get('gold', c['gold'])
        if c.get(campo_resposta) == alvo:
            acertos_oficial += 1
        else:
            erros_oficial.append(c['case_id'])
    mudados = {m['case_id'] for m in procedencia['casos_substituidos']}
    local = do_anotador_local()
    acertos_local = sum(1 for c in casos
                        if c.get(campo_resposta) == local.get(c['case_id'], c['gold']))
    # Divergencia entre ANOTADORES neste corpus: e outra pergunta, e e a que interessa para
    # dizer se ha mais de um gabarito em jogo. Perguntar so o que a adjudicacao mudou deixava
    # o piloto inteiro parecendo unanime, com quatro casos em disputa dentro dele.
    divergentes = sorted(c['case_id'] for c in casos
                         if c['case_id'] in local and local[c['case_id']] != c['gold'])
    saida = {
        'casos_programados': programados,
        'autor': {'acertos': acertos_autor,
                  'acuracia': round(acertos_autor / programados, 4) if programados else None},
        'oficial': {'acertos': acertos_oficial,
                    'acuracia': round(acertos_oficial / programados, 4) if programados else None,
                    'erros': erros_oficial},
        'casos_deste_relatorio_que_mudaram': sorted(
            {c['case_id'] for c in casos} & mudados),
        'casos_em_que_os_anotadores_divergem': divergentes,
        'adjudicado': procedencia['adjudicado'],
    }
    if local:
        saida['anotador_local'] = {
            'acertos': acertos_local,
            'acuracia': round(acertos_local / programados, 4) if programados else None}
    return saida


def desempenho_do_estudo(relatorios=('runs/e1-triagem/relatorio.json',
                                     'runs/e7-confirmacao/relatorio.json')):
    """O desempenho sobre os 80 casos, somado a partir dos relatórios, sob os três gabaritos.

    O cartão do E8 lia `acuracia_jev_sob_meu_gabarito` e `acuracia_jev_sob_gabarito_do_outro`,
    dois números gravados dentro do relatório do E8 no momento em que ele rodou. Um teste de
    mutação da décima terceira rodada trocou as anotações do anotador local e os cartões do E1 e
    do E7 acompanharam; o do E8 não se mexeu. Era o mesmo defeito da nona rodada — número velho
    numa caixa nova — sobrevivendo no único cartão que ninguém tinha remexido. Aqui a conta é
    feita agora, das mesmas fontes que os outros cartões usam.
    """
    partes = [desempenho(r) for r in relatorios]
    partes = [p for p in partes if p]
    if not partes:
        return None
    total = sum(p['casos_programados'] for p in partes)
    saida = {
        'casos_programados': total,
        'adjudicado': any(p['adjudicado'] for p in partes),
        'casos_em_que_os_anotadores_divergem': sorted(
            c for p in partes for c in p['casos_em_que_os_anotadores_divergem']),
        'casos_deste_relatorio_que_mudaram': sorted(
            c for p in partes for c in p['casos_deste_relatorio_que_mudaram']),
    }
    for chave in ('autor', 'oficial', 'anotador_local'):
        if not all(p.get(chave) for p in partes):
            continue
        acertos = sum(p[chave]['acertos'] for p in partes)
        saida[chave] = {'acertos': acertos,
                        'acuracia': round(acertos / total, 4) if total else None}
        if chave == 'oficial':
            saida[chave]['erros'] = [e for p in partes for e in p['oficial']['erros']]
    return saida


def contagem_bruta(relatorio, campo_resposta='jev'):
    """Conta acertos direto dos casos, para corpora cujo gabarito vive no próprio relatório.

    A auditoria de mutação da décima terceira rodada trocou cinco acertos por erros em cada
    relatório e perguntou quais cartões se mexiam. O E3 não se mexeu: ele lia o bloco agregado
    `jev` gravado no alto do arquivo, e aquele bloco continua dizendo o que dizia quando o
    experimento rodou. Nenhum teste pegava isso porque os dois números batem enquanto ninguém
    mexe nos dados — que é exatamente a situação em que um número congelado parece correto.
    """
    caminho = ROOT / relatorio if not str(relatorio).startswith(str(ROOT)) else Path(relatorio)
    if not caminho.exists():
        return None
    casos = json.loads(caminho.read_text(encoding='utf-8')).get('casos') or []
    programados = len(casos)
    acertos = sum(1 for c in casos if c.get(campo_resposta) == c.get('gold'))
    return {'acertos': acertos, 'casos_programados': programados,
            'acuracia': round(acertos / programados, 4) if programados else None}
