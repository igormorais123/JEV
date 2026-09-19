"""Terceiro juiz cego nos 10 desacordos do corpus de desempate (E11).

Mesmo procedimento do E8b, sob a Emenda 2 do pré-registro do E11, escrita antes desta execução:
o juiz recebe só a mensagem e as duas leituras, **em ordem sorteada**, sem saber qual veio de
quem e sem ver nenhuma resposta de modelo.

Este script prepara os casos cegos e o prompt; a chamada ao juiz é feita fora, por outro
fornecedor, e a resposta volta por `--consolidar`.

Uso:
    python -m executor.adjudicar_e11              # gera casos-cegos.json e prompt.txt
    python -m executor.adjudicar_e11 --consolidar bruta.jsonl
"""
import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from .gabarito import do_anotador_local
from .run_e1_triagem import CRITERIOS, INSTRUCOES

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-desempate.jsonl'
OUT = ROOT / 'runs' / 'e11-desempate'
SEMENTE = 20260919


def desacordos():
    local = do_anotador_local()
    casos = []
    for linha in CORPUS.read_text(encoding='utf-8').splitlines():
        if not linha.strip():
            continue
        caso = json.loads(linha)
        outro = local.get(caso['case_id'])
        if outro and outro != caso['gold']:
            casos.append({'case_id': caso['case_id'], 'text': caso['text'],
                          'autor': caso['gold'], 'anotador_local': outro})
    return casos


def cegar(casos):
    """Sorteia a ordem das duas leituras e guarda o mapa fora do prompt."""
    sorteio = random.Random(SEMENTE)
    cegos, mapa = [], {}
    for caso in casos:
        troca = sorteio.random() < 0.5
        a, b = ((caso['anotador_local'], caso['autor']) if troca
                else (caso['autor'], caso['anotador_local']))
        mapa[caso['case_id']] = {'A': 'anotador_local' if troca else 'autor',
                                 'B': 'autor' if troca else 'anotador_local',
                                 'autor': caso['autor'],
                                 'anotador_local': caso['anotador_local']}
        cegos.append({'case_id': caso['case_id'], 'text': caso['text'], 'A': a, 'B': b})
    return cegos, mapa


def montar_prompt(cegos):
    criterios = '\n'.join('- ' + c + ': ' + d for c, d in CRITERIOS.items())
    blocos = []
    for caso in cegos:
        blocos.append(caso['case_id'] + '\nMENSAGEM: ' + caso['text']
                      + '\nLEITURA A: ' + caso['A'] + '\nLEITURA B: ' + caso['B'])
    return (
        'Voce e o terceiro juiz de um estudo de anotacao. Dois anotadores independentes '
        'classificaram as mesmas mensagens de atendimento ao cliente e divergiram em '
        + str(len(cegos)) + ' casos. Voce NAO sabe qual leitura veio de qual anotador, e isso e '
        'proposital. Decida cada caso pelo merito.\n\n'
        'REGRA DE DECISAO (a mesma que os dois anotadores receberam):\n' + INSTRUCOES + '\n\n'
        'CLASSES:\n' + criterios + '\n\n'
        'Para cada caso, escolha A ou B, ou responda "nenhuma" se as duas leituras estiverem '
        'erradas (e entao diga a classe correta), ou "ambiguas" se a mensagem realmente admitir '
        'as duas leituras sem que uma seja melhor.\n\n'
        'SAIDA: uma linha JSON por caso, sem markdown e sem cercas:\n'
        '{"case_id":"...","escolha":"A|B|nenhuma|ambiguas","classe":"<classe correta>",'
        '"motivo":"ate 20 palavras"}\n\nCASOS EM DISPUTA:\n\n' + '\n\n'.join(blocos) + '\n')


def consolidar(caminho_bruto, juiz):
    mapa = json.loads((OUT / 'adjudicacao-mapa.json').read_text(encoding='utf-8'))
    decisoes = []
    for linha in Path(caminho_bruto).read_text(encoding='utf-8').splitlines():
        linha = linha.strip().strip('`')
        if not linha.startswith('{'):
            continue
        decisoes.append(json.loads(linha))
    resultado, placar = [], {'confirmam_o_autor': 0, 'confirmam_o_anotador_local': 0,
                             'terceira_leitura': 0, 'ambiguas': 0}
    for d in decisoes:
        info = mapa.get(d['case_id'])
        if not info:
            continue
        escolha = d.get('escolha')
        if escolha in ('A', 'B'):
            de_quem = info[escolha]
            classe = info[de_quem]
            placar['confirmam_o_autor' if de_quem == 'autor'
                    else 'confirmam_o_anotador_local'] += 1
        elif escolha == 'ambiguas':
            de_quem, classe = 'ambiguas', None
            placar['ambiguas'] += 1
        else:
            de_quem, classe = 'terceira_leitura', d.get('classe')
            placar['terceira_leitura'] += 1
        resultado.append({'case_id': d['case_id'], 'anotador_1_autor': info['autor'],
                          'anotador_2_local': info['anotador_local'],
                          'escolha_cega': escolha, 'confirma': de_quem,
                          'terceiro_juiz': classe, 'motivo': d.get('motivo')})
    saida = {'at': datetime.now(timezone.utc).isoformat(), 'terceiro_juiz': juiz,
             'preregistro': 'planning/preregistro-E11-desempate.md (Emenda 2)',
             'corpus': 'data/corpus/triagem-desempate.jsonl',
             'casos': resultado, 'placar': placar}
    (OUT / 'adjudicacao.json').write_text(json.dumps(saida, ensure_ascii=False, indent=1),
                                          encoding='utf-8')
    return saida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consolidar')
    parser.add_argument('--juiz', default='gpt-5.6-sol-high (Cursor), cego')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.consolidar:
        saida = consolidar(args.consolidar, args.juiz)
        print('Placar da adjudicacao:', json.dumps(saida['placar'], ensure_ascii=False))
        for c in saida['casos']:
            print('  %-12s autor=%-11s local=%-11s -> %s (%s)'
                  % (c['case_id'], c['anotador_1_autor'], c['anotador_2_local'],
                     c['terceiro_juiz'], c['confirma']))
        return
    casos = desacordos()
    if not casos:
        raise SystemExit('nenhum desacordo entre os anotadores neste corpus')
    cegos, mapa = cegar(casos)
    (OUT / 'casos-cegos.json').write_text(json.dumps(cegos, ensure_ascii=False, indent=1),
                                          encoding='utf-8')
    (OUT / 'adjudicacao-mapa.json').write_text(json.dumps(mapa, ensure_ascii=False, indent=1),
                                               encoding='utf-8')
    (OUT / 'prompt-adjudicacao.txt').write_text(montar_prompt(cegos), encoding='utf-8')
    print('%d casos em disputa, cegos e sorteados com semente %d.' % (len(cegos), SEMENTE))
    print('Prompt em runs/e11-desempate/prompt-adjudicacao.txt')


if __name__ == '__main__':
    main()
