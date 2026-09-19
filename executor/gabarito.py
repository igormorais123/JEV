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
    return {
        'casos_programados': programados,
        'autor': {'acertos': acertos_autor,
                  'acuracia': round(acertos_autor / programados, 4) if programados else None},
        'oficial': {'acertos': acertos_oficial,
                    'acuracia': round(acertos_oficial / programados, 4) if programados else None,
                    'erros': erros_oficial},
        'casos_deste_relatorio_que_mudaram': sorted(
            {c['case_id'] for c in casos} & mudados),
        'adjudicado': procedencia['adjudicado'],
    }
