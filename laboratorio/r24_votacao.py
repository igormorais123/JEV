"""R24 — votar em três chamadas, medido de ponta a ponta.

O guia recomenda votação para a classe irreversível, e Q098 registra que ela nunca foi testada de
ponta a ponta: a única evidência era a repetibilidade do E6 (1 caso em 40 oscilou), da qual se
inferiu que votar ajudaria pouco. Inferência não é medida. Esta rodada mede duas votações nos
dois corpus mais difíceis do estudo:

  **igual**    três chamadas idênticas. Só captura oscilação do modelo.
  **diversa**  três formulações da mesma pergunta — a instrução base, a instrução com a frase de
               sujeito, e a instrução reescrita com os critérios em outra ordem. Captura também
               o erro que depende da formulação, que a R1-R3 mostrou existir.

Cada corpus é medido em três políticas, pareadas caso a caso contra a chamada única: maioria
simples das três iguais, maioria simples das três diversas, e a diversa com desempate pela
confiança. O que se reporta é acerto, oscilação (quantos casos tiveram as três respostas
discordando) e o custo em chamadas por ponto de acurácia ganho.

**Falsificação.** Se nenhuma votação ganhar da chamada única em pareamento com p < 0,05 em
nenhum dos dois corpus, a recomendação do guia passa a dizer "votar protege contra oscilação,
que é rara, e não contra erro" — que é o que Q040 já suspeitava — e deixa de sugerir votação
como salvaguarda de acurácia.

    python laboratorio/r24_votacao.py --rodar
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor.run_e1_triagem import CRITERIOS, INSTRUCOES  # noqa: E402
from laboratorio.nucleo import (chave, em_paralelo, mcnemar_exato, perguntar,  # noqa: E402
                                wilson)
from laboratorio.r21_generalizacao import (CLASSES_PT, INSTRUCAO_PT, SUJEITO_PT,  # noqa: E402
                                           Medidor)

DESTINO = RAIZ / 'laboratorio' / 'r24-votacao.json'
CUSTO_MAXIMO_PREVISTO = 0.10

SUJEITO_ATENDIMENTO = (' Considere apenas o que quem escreve esta pedindo para si mesmo; acao de '
                       'outra pessoa, mencionada de passagem ou recusada, nao conta.')

CORPORA = {
    'atendimento': {
        'arquivo': RAIZ / 'laboratorio' / 'r19-corpus.json', 'campo': 'texto',
        'criterios': CRITERIOS,
        'formulacoes': {
            'base': INSTRUCOES,
            'sujeito': INSTRUCOES + SUJEITO_ATENDIMENTO,
            'reescrita': ('Leia a mensagem e diga qual acao o cliente esta pedindo agora, para '
                          'ele mesmo. Assunto mencionado nao e acao pedida; acao de terceiro, '
                          'negada, condicional ou ja concluida nao conta.'),
        }},
    'juridico': {
        'arquivo': RAIZ / 'laboratorio' / 'r21-corpus.json', 'campo': 'pt',
        'criterios': CLASSES_PT,
        'formulacoes': {
            'base': INSTRUCAO_PT,
            'sujeito': INSTRUCAO_PT + SUJEITO_PT,
            'reescrita': ('Leia a mensagem do cliente ao escritorio e diga o que ele esta '
                          'pedindo agora, para ele mesmo. Pedido de outra pessoa, recusado ou '
                          'apenas relatado nao conta.'),
        }},
}


def criterios_invertidos(criterios):
    """A mesma taxonomia, com as classes na ordem inversa: a R1-R3 mediu efeito de ordem."""
    return dict(reversed(list(criterios.items())))


def classificar(tarefa):
    corpus = CORPORA[tarefa['corpus']]
    instrucao = corpus['formulacoes'][tarefa['formulacao']]
    criterios = (criterios_invertidos(corpus['criterios']) if tarefa['formulacao'] == 'reescrita'
                 else dict(corpus['criterios']))
    respostas, _ = perguntar(f'O cliente escreveu: "{tarefa["texto"]}"',
                             {'acao': {'type': 'choice', 'instructions': instrucao,
                                       'criteria': criterios}}, rodada='R24')
    bloco = (respostas or {}).get('acao') or {}
    return {'corpus': tarefa['corpus'], 'i': tarefa['i'], 'formulacao': tarefa['formulacao'],
            'repeticao': tarefa['repeticao'], 'gold': tarefa['gold'],
            'escolha': bloco.get('choice'), 'confianca': bloco.get('confidence')}


def votar(respostas, por_confianca=False):
    validas = [r for r in respostas if r['escolha']]
    if not validas:
        return None
    if por_confianca:
        peso = Counter()
        for r in validas:
            peso[r['escolha']] += (r['confianca'] or 0)
        return peso.most_common(1)[0][0]
    contagem = Counter(r['escolha'] for r in validas)
    melhor, quantos = contagem.most_common(1)[0]
    if quantos == 1:  # três respostas diferentes: fica a primeira, como a chamada única faria
        return validas[0]['escolha']
    return melhor


def analisar(linhas):
    saida = {'corpora': {}, 'detalhe': linhas}
    for nome in CORPORA:
        do_corpus = [l for l in linhas if l['corpus'] == nome]
        por_caso = {}
        for l in do_corpus:
            por_caso.setdefault(l['i'], {'gold': l['gold'], 'igual': [], 'diversa': []})
            if l['formulacao'] == 'base':
                por_caso[l['i']]['igual'].append(l)
            if l['repeticao'] == 0:
                por_caso[l['i']]['diversa'].append(l)

        politicas = {}
        for caso in por_caso.values():
            unica = next((r for r in caso['igual'] if r['repeticao'] == 0), None)
            caso['politicas'] = {
                'unica': unica['escolha'] if unica else None,
                'maioria-igual': votar(caso['igual']),
                'maioria-diversa': votar(caso['diversa']),
                'diversa-por-confianca': votar(caso['diversa'], por_confianca=True),
            }
            respostas_iguais = [r['escolha'] for r in caso['igual'] if r['escolha']]
            respostas_diversas = [r['escolha'] for r in caso['diversa'] if r['escolha']]
            caso['oscilou'] = len(set(respostas_iguais)) > 1 if len(respostas_iguais) == 3 else None
            caso['divergiu'] = (len(set(respostas_diversas)) > 1
                                if len(respostas_diversas) == 3 else None)

        for politica in ('unica', 'maioria-igual', 'maioria-diversa', 'diversa-por-confianca'):
            validos = [c for c in por_caso.values() if c['politicas'][politica]]
            acertos = sum(1 for c in validos if c['politicas'][politica] == c['gold'])
            bloco = {'n': len(validos), 'acertos': acertos,
                     'taxa': round(acertos / len(validos), 4) if validos else None,
                     'ic95': wilson(acertos, len(validos))}
            if politica != 'unica':
                pares = [c for c in validos if c['politicas']['unica']]
                so_unica = sum(1 for c in pares if c['politicas']['unica'] == c['gold']
                               and c['politicas'][politica] != c['gold'])
                so_politica = sum(1 for c in pares if c['politicas'][politica] == c['gold']
                                  and c['politicas']['unica'] != c['gold'])
                bloco['pareado_contra_unica'] = {'certo_so_unica': so_unica,
                                                 'certo_so_votacao': so_politica,
                                                 'p': mcnemar_exato(so_unica, so_politica)}
            politicas[politica] = bloco

        oscilaram = [c for c in por_caso.values() if c['oscilou'] is not None]
        divergiram = [c for c in por_caso.values() if c['divergiu'] is not None]
        por_formulacao = {}
        for formulacao in CORPORA[nome]['formulacoes']:
            grupo = [l for l in do_corpus if l['formulacao'] == formulacao and l['repeticao'] == 0
                     and l['escolha']]
            acertos = sum(1 for l in grupo if l['escolha'] == l['gold'])
            por_formulacao[formulacao] = {'n': len(grupo), 'acertos': acertos,
                                          'taxa': round(acertos / len(grupo), 4) if grupo else None}
        saida['corpora'][nome] = {
            'casos': len(por_caso),
            'politicas': politicas,
            'por_formulacao': por_formulacao,
            'oscilacao': {'n': len(oscilaram),
                          'oscilaram': sum(1 for c in oscilaram if c['oscilou']),
                          'taxa': round(sum(1 for c in oscilaram if c['oscilou']) / len(oscilaram), 4)
                          if oscilaram else None},
            'divergencia_entre_formulacoes': {
                'n': len(divergiram),
                'divergiram': sum(1 for c in divergiram if c['divergiu']),
                'taxa': round(sum(1 for c in divergiram if c['divergiu']) / len(divergiram), 4)
                if divergiram else None},
        }
    return saida


def main():
    analise = argparse.ArgumentParser(description=__doc__)
    analise.add_argument('--rodar', action='store_true')
    args = analise.parse_args()
    chave()
    medidor = Medidor()

    tarefas = []
    for nome, corpus in CORPORA.items():
        casos = json.loads(corpus['arquivo'].read_text(encoding='utf-8'))['casos']
        for i, caso in enumerate(casos):
            for repeticao in range(3):
                tarefas.append({'corpus': nome, 'i': i, 'formulacao': 'base',
                                'repeticao': repeticao, 'texto': caso[corpus['campo']],
                                'gold': caso['gold']})
            for formulacao in ('sujeito', 'reescrita'):
                tarefas.append({'corpus': nome, 'i': i, 'formulacao': formulacao, 'repeticao': 0,
                                'texto': caso[corpus['campo']], 'gold': caso['gold']})
    print(f'{len(tarefas)} chamadas (5 por caso), teto US$ {CUSTO_MAXIMO_PREVISTO}')
    if not args.rodar:
        return

    linhas = em_paralelo(tarefas, classificar, trabalhadores=8, rotulo='R24')
    resultado = analisar(linhas)
    for nome, bloco in resultado['corpora'].items():
        print(f"\n   {nome}: {bloco['casos']} casos; oscilaram {bloco['oscilacao']['oscilaram']}/"
              f"{bloco['oscilacao']['n']}, divergiram entre formulações "
              f"{bloco['divergencia_entre_formulacoes']['divergiram']}/"
              f"{bloco['divergencia_entre_formulacoes']['n']}")
        for politica, p in bloco['politicas'].items():
            par = p.get('pareado_contra_unica', {})
            print(f"   {politica:22} {p['acertos']:>3}/{p['n']:<3} {p['taxa']}  {par}")
        for formulacao, f in bloco['por_formulacao'].items():
            print(f"   formulação {formulacao:10} {f['acertos']}/{f['n']} = {f['taxa']}")

    gasto, chamadas, _ = medidor.gasto()
    resultado['custo_usd'] = round(gasto, 6)
    resultado['chamadas'] = chamadas
    if gasto > CUSTO_MAXIMO_PREVISTO:
        print(f'ATENÇÃO: passou do teto previsto de US$ {CUSTO_MAXIMO_PREVISTO}')
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{chamadas} chamadas nesta corrida, US$ {gasto:.6f}')


if __name__ == '__main__':
    main()
