"""E8: segundo anotador independente e cego sobre o gabarito dos 80 casos.

A limitação mais séria que sobrou dos experimentos anteriores é que o gabarito tem um
anotador só: eu. Um gabarito de uma pessoa não é um gabarito, é uma opinião bem documentada.

Este experimento não resolve isso — resolve uma parte dele. Um modelo local (qwen2.5-7b via
Ollama, na GPU do próprio PC, custo zero) recebe SÓ as instruções e os critérios, sem ver o
gabarito nem a resposta do Jev, e classifica os 80 casos. O que medimos:

1. Concordância entre o anotador independente e o meu gabarito (kappa de Cohen).
2. Onde os dois discordam: esses casos são os candidatos a gabarito ambíguo.
3. Como ficaria a acurácia do Jev se o gabarito fosse do outro anotador.

O que este experimento NÃO é: um anotador humano. Um modelo de 7B erra de formas próprias, e
concordância alta pode significar que a tarefa é fácil, não que o gabarito é bom. O valor está
na DISCORDÂNCIA: os casos onde um juiz independente lê diferente do que eu li.

Uso:
    python -m executor.run_e8_anotador
"""
import json
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .run_e1_triagem import CRITERIOS, INSTRUCOES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'e8-anotador'
OLLAMA = 'http://127.0.0.1:11434/api/chat'
MODELO = 'qwen2.5:7b-instruct'
CLASSES = list(CRITERIOS)

CORPORA = [('data/corpus/triagem-piloto.jsonl', 'piloto', 'runs/e1-triagem/relatorio.json'),
           ('data/corpus/triagem-confirmacao.jsonl', 'confirmacao', 'runs/e7-confirmacao/relatorio.json')]


def carregar_tudo():
    casos = []
    for arquivo, conjunto, relatorio in CORPORA:
        jev = {}
        alvo = ROOT / relatorio
        if alvo.exists():
            jev = {c['case_id']: c.get('jev') for c in
                   json.loads(alvo.read_text(encoding='utf-8'))['casos']}
        for linha in (ROOT / arquivo).read_text(encoding='utf-8').splitlines():
            if linha.strip():
                d = json.loads(linha)
                d['conjunto'] = conjunto
                d['jev'] = jev.get(d['case_id'])
                casos.append(d)
    return casos


def perguntar(texto):
    criterios = '\n'.join(f'- {nome}: {desc}' for nome, desc in CRITERIOS.items())
    sistema = (f'Voce e um anotador independente de um estudo de classificacao de mensagens de '
               f'atendimento ao cliente. Regra de decisao: {INSTRUCOES}\n\nClasses:\n{criterios}\n\n'
               'Responda SOMENTE com um objeto JSON: {"rotulo":"<uma das classes>","ambigua":true|false}')
    corpo = {'model': MODELO, 'stream': False, 'format': 'json',
             'options': {'temperature': 0, 'seed': 20260919},
             'messages': [{'role': 'system', 'content': sistema},
                          {'role': 'user', 'content': f'Mensagem:\n{texto}'}]}
    requisicao = urllib.request.Request(
        OLLAMA, data=json.dumps(corpo, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(requisicao, timeout=180) as resposta:
        dados = json.loads(resposta.read().decode('utf-8'))
    try:
        saida = json.loads(dados['message']['content'])
    except (ValueError, KeyError):
        return None, None
    rotulo = saida.get('rotulo')
    return (rotulo if rotulo in CLASSES else None), bool(saida.get('ambigua'))


def kappa_cohen(pares):
    """Concordância corrigida pelo acaso. 1 é concordância total; 0 é o nível do acaso."""
    n = len(pares)
    if not n:
        return None
    observada = sum(1 for a, b in pares if a == b) / n
    ca, cb = Counter(a for a, _ in pares), Counter(b for _, b in pares)
    esperada = sum((ca[c] / n) * (cb[c] / n) for c in set(ca) | set(cb))
    if esperada >= 1:
        return 1.0
    return round((observada - esperada) / (1 - esperada), 4)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    casos = carregar_tudo()
    print(f'{len(casos)} casos, anotador independente {MODELO} (local, sem custo de API).')
    for i, caso in enumerate(casos, 1):
        caso['anotador'], caso['anotador_ambigua'] = perguntar(caso['text'])
        if i % 20 == 0:
            print(f'  {i}/{len(casos)}', flush=True)

    validos = [c for c in casos if c['anotador']]
    pares = [(c['gold'], c['anotador']) for c in validos]
    concordam = sum(1 for a, b in pares if a == b)
    divergentes = [c for c in validos if c['gold'] != c['anotador']]

    com_jev = [c for c in validos if c.get('jev')]
    acuracia_meu = sum(1 for c in com_jev if c['jev'] == c['gold']) / len(com_jev) if com_jev else None
    acuracia_outro = (sum(1 for c in com_jev if c['jev'] == c['anotador']) / len(com_jev)
                      if com_jev else None)
    # Os casos em que os dois anotadores concordam formam um gabarito de consenso: nele o
    # desacordo entre humano e maquina nao contamina a medida do Jev.
    consenso = [c for c in com_jev if c['gold'] == c['anotador']]
    acuracia_consenso = (sum(1 for c in consenso if c['jev'] == c['gold']) / len(consenso)
                         if consenso else None)

    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(),
        'anotador_independente': MODELO,
        'natureza': ('modelo local, nao humano; mede reprodutibilidade do gabarito por um juiz '
                     'independente que so viu as instrucoes'),
        'casos': len(casos), 'respostas_validas': len(validos),
        'concordancia_bruta': round(concordam / len(validos), 4) if validos else None,
        'kappa_cohen': kappa_cohen(pares),
        'n_divergencias': len(divergentes),
        'divergencias': [{'case_id': c['case_id'], 'conjunto': c['conjunto'], 'family': c['family'],
                          'meu_gabarito': c['gold'], 'anotador': c['anotador'], 'jev': c.get('jev'),
                          'anotador_marcou_ambigua': c['anotador_ambigua'], 'text': c['text']}
                         for c in divergentes],
        'acuracia_jev_sob_meu_gabarito': round(acuracia_meu, 4) if acuracia_meu is not None else None,
        'acuracia_jev_sob_gabarito_do_outro': round(acuracia_outro, 4) if acuracia_outro is not None else None,
        'casos_de_consenso': len(consenso),
        'acuracia_jev_no_consenso': round(acuracia_consenso, 4) if acuracia_consenso is not None else None,
        'anotacoes': [{'case_id': c['case_id'], 'conjunto': c['conjunto'], 'gold': c['gold'],
                       'anotador': c['anotador'], 'ambigua': c['anotador_ambigua'], 'jev': c.get('jev')}
                      for c in casos],
    }
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print(f"\nConcordancia bruta {relatorio['concordancia_bruta']} | kappa {relatorio['kappa_cohen']}")
    print(f"Divergencias: {len(divergentes)} de {len(validos)}")
    for d in relatorio['divergencias']:
        print(f"  {d['case_id']:14} eu={d['meu_gabarito']:11} outro={d['anotador']:11} jev={d['jev']}")
    print(f"\nAcuracia do Jev sob o MEU gabarito:      {relatorio['acuracia_jev_sob_meu_gabarito']}")
    print(f"Acuracia do Jev sob o gabarito do OUTRO: {relatorio['acuracia_jev_sob_gabarito_do_outro']}")
    print(f"Acuracia do Jev nos {len(consenso)} casos de consenso:  {relatorio['acuracia_jev_no_consenso']}")


if __name__ == '__main__':
    main()
