"""R29 — fora de casa, o que carrega a decisão: o rótulo, a descrição, a ordem ou a instrução?

De onde vem. Três afirmações do estudo foram medidas só no corpus de atendimento, onde a
acurácia já estava no teto (96,7%), e uma quarta ficou declarada fora de alcance:

1. "O Jev decide pelo rótulo, a descrição é quase decorativa" (R11: critérios idênticos, 93,3%).
2. "A instrução quase não importa" (R11: curta e contraditória, 96,7%) — contra a R21 e a R24,
   em que uma frase de instrução vale de 12 a 16 pontos no jurídico.
3. "A ordem das opções não muda a escolha" (R2: 0 de 90).
4. A R24 subiu o jurídico de 79,7% para 95,5% com uma instrução reescrita, mas inverteu a ordem
   dos critérios na mesma formulação e declarou não saber qual das duas mudanças ganhou.

Um efeito medido no teto não diz nada sobre o que acontece longe dele. Esta rodada refaz as
quatro medições nos dois domínios em que o Jev erra de verdade: jurídico (R21, 69 mensagens) e
clínica (R25, 76), com gabarito fixado por molde antes de existir texto.

**Arranjos.**

    base            a pergunta original
    descr-iguais    os mesmos rótulos, todos com a mesma descrição vazia de sentido
    rotulo-opaco    rótulos c1 a c5 com as descrições originais
    ordem-inversa   a pergunta original com os critérios na ordem inversa
    reescrita       a instrução reescrita da R24, com os critérios na ordem ORIGINAL

**Previsões e falsificação, escritas antes de rodar.**

H29a  Com descrições iguais a acurácia fica a 5 pontos ou menos da `base` em cada domínio. Queda
      acima de 10 pontos falsifica "o rótulo decide" como regra geral: era efeito de teto.
H29b  Com rótulos opacos a acurácia cai mais de 10 pontos. Se ficar a 5 pontos ou menos, o Jev
      lê a descrição quando o rótulo não diz nada, e taxonomia com código interno é viável.
H29c  A ordem inversa muda 3% ou menos das respostas. Acima de 5% falsifica a invariância fora
      do atendimento.
H29d  A reescrita, na ordem original, ganha da `base` no conjunto, McNemar exato p < 0,05. Se
      ganhar, o ganho da R24 é da redação; se empatar, era da ordem, e H29c precisa cair junto.

    python laboratorio/r29_o_que_carrega_a_decisao.py --rodar
"""

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r21_generalizacao import CLASSES_PT, INSTRUCAO_PT, Medidor  # noqa: E402
from laboratorio.r24_votacao import CORPORA as CORPORA_R24  # noqa: E402
from laboratorio.r25_terceiro_dominio import CLASSES as CLASSES_CLINICA  # noqa: E402
from laboratorio.r25_terceiro_dominio import INSTRUCAO as INSTRUCAO_CLINICA  # noqa: E402

DESTINO = RAIZ / 'laboratorio' / 'r29-o-que-carrega.json'
CUSTO_MAXIMO_PREVISTO = 0.10
DESCRICAO_VAZIA = 'Uma das classes possiveis para a mensagem.'

DOMINIOS = {
    'juridico': {'arquivo': 'r21-corpus.json', 'campo': 'pt', 'quem': 'O cliente',
                 'instrucao': INSTRUCAO_PT, 'criterios': CLASSES_PT,
                 'reescrita': CORPORA_R24['juridico']['formulacoes']['reescrita']},
    'clinica': {'arquivo': 'r25-corpus.json', 'campo': 'texto', 'quem': 'O paciente',
                'instrucao': INSTRUCAO_CLINICA, 'criterios': CLASSES_CLINICA,
                'reescrita': ('Leia a mensagem do paciente a clinica e diga o que ele esta pedindo '
                              'agora, para ele mesmo. Pedido de outra pessoa, recusado ou apenas '
                              'relatado nao conta.')},
}
ARRANJOS = ('base', 'descr-iguais', 'rotulo-opaco', 'ordem-inversa', 'reescrita')


def montar(arranjo, d):
    criterios, instrucao, volta = dict(d['criterios']), d['instrucao'], {}
    if arranjo == 'descr-iguais':
        criterios = {k: DESCRICAO_VAZIA for k in criterios}
    elif arranjo == 'rotulo-opaco':
        volta = {f'c{n}': k for n, k in enumerate(criterios, 1)}
        criterios = {f'c{n}': v for n, v in enumerate(criterios.values(), 1)}
    elif arranjo == 'ordem-inversa':
        criterios = dict(reversed(list(criterios.items())))
    elif arranjo == 'reescrita':
        instrucao = d['reescrita']
    return instrucao, criterios, volta


def classificar(tarefa):
    d = DOMINIOS[tarefa['dominio']]
    instrucao, criterios, volta = montar(tarefa['arranjo'], d)
    estado = f"{d['quem']} escreveu: \"{tarefa['caso'][d['campo']]}\""
    respostas, _ = perguntar(estado, {'pedido': {'type': 'choice', 'instructions': instrucao,
                                                 'criteria': criterios}}, rodada='R29')
    bloco = (respostas or {}).get('pedido') or {}
    escolha = bloco.get('choice')
    return {'dominio': tarefa['dominio'], 'i': tarefa['i'], 'arranjo': tarefa['arranjo'],
            'molde': tarefa['caso']['molde'], 'gold': tarefa['caso']['gold'],
            'escolha': volta.get(escolha, escolha), 'confianca': bloco.get('confidence')}


def analisar(linhas):
    por = {}
    for l in linhas:
        if l['escolha']:
            por.setdefault(l['arranjo'], {})[(l['dominio'], l['i'])] = l
    saida = {'arranjos': {}, 'contra_base': {}, 'detalhe': linhas}
    for arranjo, casos in por.items():
        bloco = {'por_dominio': {}, 'por_molde': {}}
        for dominio in list(DOMINIOS) + ['conjunto']:
            do = [l for k, l in casos.items() if dominio == 'conjunto' or k[0] == dominio]
            acertos = sum(l['escolha'] == l['gold'] for l in do)
            bloco['por_dominio'][dominio] = {'acertos': acertos, 'n': len(do), 'taxa': round(acertos / len(do), 4),
                                             'ic95': wilson(acertos, len(do))}
            if dominio != 'conjunto':
                for m in sorted({l['molde'] for l in do}):
                    dm = [l for l in do if l['molde'] == m]
                    bloco['por_molde'][f'{dominio}/{m}'] = f"{sum(l['escolha'] == l['gold'] for l in dm)}/{len(dm)}"
        saida['arranjos'][arranjo] = bloco
        if arranjo != 'base':
            comuns = [k for k in casos if k in por['base']]
            mudou = sum(casos[k]['escolha'] != por['base'][k]['escolha'] for k in comuns)
            so_este = sum(casos[k]['escolha'] == casos[k]['gold'] and por['base'][k]['escolha'] != casos[k]['gold'] for k in comuns)
            so_base = sum(casos[k]['escolha'] != casos[k]['gold'] and por['base'][k]['escolha'] == casos[k]['gold'] for k in comuns)
            saida['contra_base'][arranjo] = {'pares': len(comuns), 'respostas_que_mudaram': mudou,
                                             'fracao_que_mudou': round(mudou / len(comuns), 4),
                                             'certo_so_neste': so_este, 'certo_so_na_base': so_base,
                                             'p': mcnemar_exato(so_este, so_base)}
    return saida


def main():
    analise = argparse.ArgumentParser(description=__doc__)
    analise.add_argument('--rodar', action='store_true')
    args = analise.parse_args()
    if not args.rodar:
        analise.print_help()
        return
    medidor = Medidor()
    tarefas = []
    for dominio, d in DOMINIOS.items():
        casos = json.loads((RAIZ / 'laboratorio' / d['arquivo']).read_text(encoding='utf-8'))['casos']
        tarefas += [{'dominio': dominio, 'i': i, 'caso': c, 'arranjo': a} for i, c in enumerate(casos) for a in ARRANJOS]
    print(f'{len(tarefas)} chamadas')
    linhas = em_paralelo(tarefas, classificar, trabalhadores=8, rotulo='R29')
    DESTINO.with_name('r29-bruto.json').write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding='utf-8')
    resultado = analisar(linhas)
    gasto, chamadas, _ = medidor.gasto()
    resultado['custo_usd'], resultado['chamadas'] = round(gasto, 6), chamadas
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    for arranjo, b in resultado['arranjos'].items():
        print(f"  {arranjo:14} " + '  '.join(f"{d} {v['acertos']}/{v['n']}={v['taxa']}" for d, v in b['por_dominio'].items()))
    for arranjo, b in resultado['contra_base'].items():
        print(f'  {arranjo:14} {b}')
    print(f'{chamadas} chamadas, US$ {gasto:.6f}')


if __name__ == '__main__':
    main()
