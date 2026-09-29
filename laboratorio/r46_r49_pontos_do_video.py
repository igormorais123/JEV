"""R46 a R49 — quatro pontos levantados por uma avaliação externa do Jev, refeitos com o método da casa.

De onde vem. O vídeo "Jev: IA de Decisões Rápidas e de Baixíssimo Custo" (canal ViktorKav,
2026-09-21, https://youtu.be/RZNmluFIgK0) rodou 1.395 chamadas e mostrou quatro coisas que este
estudo nunca mediu. Aqui cada uma vira rodada com gabarito por construção, e a previsão é a do
vídeo: se ela não repetir, a rodada diz.

R46 — conta embutida na leitura. No vídeo, "10 hubs USB, metade agora, metade mês que vem": o Jev
      respondeu que o primeiro lote tem 10, três vezes, com 96 a 98% de probabilidade. Pedidos
      gerados por fórmula (o gabarito é aritmética, não opinião), em quatro moldes.
      H46a  Quando os números dos lotes estão escritos ("6 agora e 4 depois") o acerto é 95% ou mais.
      H46b  Quando o lote exige conta ("metade agora", "um terço agora") o acerto fica abaixo de
            60% e pelo menos metade dos erros passa do corte de 0,90.
      H46c  Decompor conserta: uma pergunta para o total e outra para a regra de divisão, com a
            conta feita em código, acerta 90% ou mais nos mesmos pedidos.

R47 — o fiscal diante de evidência incompleta. No vídeo, com a observação "só o primeiro
      resultado foi visto, o resto está oculto", o Jev condenou (`defeito`) em 12 de 12, havendo
      a opção `inconclusiva`. Casos por construção: lista de itens públicos e privados, pedido
      "devolver só os públicos", e quatro tipos de observação.
      H47a  Observação completa (certa ou errada): 95% ou mais.
      H47b  Observação parcial e coerente com o pedido: escolhe `inconclusiva` em menos de 50%.
      H47c  Duas perguntas (a observação mostra tudo? o que foi visto contraria o pedido?), com o
            veredito montado em código, acertam 90% ou mais nos quatro tipos.

R48 — referência pública. Banking77 (inglês, 77 classes), duas mensagens por classe sorteadas
      com semente, 154 no total. No vídeo: 129/154 = 83,8%, e 103/105 com probabilidade da
      escolha de 0,95 ou mais.
      H48a  Acerto entre 78% e 90%.
      H48b  Com probabilidade da escolha de 0,95 ou mais, acerto de 97% ou mais e cobertura entre
            55% e 80%.
      H48c  A fórmula da confiança, (K·p − 1)/(K − 1), vale com K = 77 em 97% ou mais das respostas.

R49 — 64 perguntas no mesmo payload. No vídeo a mediana foi de 254 ms com uma pergunta e 263 ms
      com 64. A R33 foi até 16.
      H49   Com 64 perguntas a latência mediana fica a 1,5 vez ou menos da chamada única, todas
            as 64 voltam respondidas, e as quatro perguntas de base têm a mesma resposta nas 16
            cópias em 98% ou mais das vezes.

    python laboratorio/r46_r49_pontos_do_video.py --rodar R46 R47 R48 R49 --banking CAMINHO.csv
"""

import argparse
import csv
import json
import random
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import em_paralelo  # noqa: E402
from laboratorio.r31_r37_segunda_leva import gravar, medidas, perguntar, taxa  # noqa: E402

LAB = RAIZ / 'laboratorio'
SEMENTE = 20260923
CORTE = 0.90

# ===================================================================== R46
NOMES = ['Otavio BH', 'Marina SP', 'Loja Centro', 'Rui Recife', 'Carla POA', 'Deposito Sul']
ITENS = ['hubs USB', 'teclados', 'cabos HDMI', 'monitores', 'mouses', 'fontes']
MOLDES_R46 = {
    'numeros-escritos': lambda n, a: (f'{a} agora urgente, {n - a} pode ser mes que vem', a),
    'metade': lambda n, a: ('metade agora urgente, metade pode ser mes que vem', n // 2),
    'um-terco': lambda n, a: ('um terco agora urgente, o resto pode ser mes que vem', n // 3),
    'tudo-agora': lambda n, a: ('tudo agora, urgente', n),
}
REGRAS = {'metade-metade': 'Metade vai agora e metade depois.', 'um-terco-agora': 'Um terco vai agora e o resto depois.',
          'tudo-agora': 'Tudo vai agora, em um lote so.', 'quantidades-escritas': 'O texto escreve a quantidade de cada lote.'}
REGRA_DO_MOLDE = {'metade': 'metade-metade', 'um-terco': 'um-terco-agora', 'tudo-agora': 'tudo-agora', 'numeros-escritos': 'quantidades-escritas'}


def casos_r46():
    sorteio = random.Random(SEMENTE)
    casos = []
    for molde, monta in MOLDES_R46.items():
        for n in (6, 12, 18, 24, 30, 36, 48, 60, 90, 120):
            a = sorteio.choice([x for x in range(1, n) if x not in (n // 2, n // 3)])
            trecho, gold = monta(n, a)
            opcoes = sorted({n, n // 2, n // 3, a, n - a, n * 2})
            casos.append({'molde': molde, 'total': n, 'gold': gold, 'opcoes': opcoes,
                          'texto': f'{sorteio.choice(NOMES)}, {n} {sorteio.choice(ITENS)}, {trecho}'})
    return casos


def rodar_r46():
    def uma(t):
        c = t['caso']
        numeros = {str(o): f'{o} unidades.' for o in c['opcoes']}
        if t['arranjo'] == 'direta':
            perguntas = {'primeiro_lote': {'type': 'choice', 'instructions': 'Quantas unidades vao na primeira entrega, a de agora?', 'criteria': numeros}}
        else:
            perguntas = {'total': {'type': 'choice', 'instructions': 'Qual e a quantidade total do pedido?', 'criteria': numeros},
                         'regra': {'type': 'choice', 'instructions': 'Como o pedido divide a entrega?', 'criteria': dict(REGRAS)}}
        respostas, detalhe = perguntar(f"Pedido recebido: \"{c['texto']}\"", perguntas, 'R46')
        r = respostas or {}
        linha = {'molde': c['molde'], 'gold': c['gold'], 'arranjo': t['arranjo'], 'texto': c['texto'], **medidas(detalhe)}
        if t['arranjo'] == 'direta':
            bloco = r.get('primeiro_lote') or {}
            linha.update(resposta=int(bloco['choice']) if bloco.get('choice') else None, confianca=bloco.get('confidence'))
        else:
            total, regra = (r.get('total') or {}).get('choice'), (r.get('regra') or {}).get('choice')
            conta = {'metade-metade': lambda n: n // 2, 'um-terco-agora': lambda n: n // 3, 'tudo-agora': lambda n: n}
            calculado = conta[regra](int(total)) if total and regra in conta else None
            linha.update(total=total, regra=regra, regra_certa=regra == REGRA_DO_MOLDE[c['molde']], total_certo=str(c['total']) == total,
                         resposta=calculado, precisa_de_outra_via=regra == 'quantidades-escritas')
        return linha

    def analisar(linhas):
        saida = {}
        for arranjo in ('direta', 'decomposta'):
            for molde in MOLDES_R46:
                ls = [l for l in linhas if l['arranjo'] == arranjo and l['molde'] == molde]
                if arranjo == 'decomposta' and molde == 'numeros-escritos':
                    saida[f'{arranjo}/{molde}'] = {'reconheceu_que_os_numeros_estao_escritos': taxa(sum(l.get('precisa_de_outra_via', False) for l in ls), len(ls))}
                    continue
                erros = [l for l in ls if l['resposta'] != l['gold']]
                bloco = taxa(len(ls) - len(erros), len(ls))
                if arranjo == 'direta':
                    bloco['erros_acima_do_corte'] = sum((l['confianca'] or 0) >= CORTE for l in erros)
                    bloco['erros_que_devolvem_o_total'] = sum(l['resposta'] == int(l['texto'].split(', ')[1].split(' ')[0]) for l in erros)
                else:
                    bloco['total_certo'] = sum(l['total_certo'] for l in ls)
                    bloco['regra_certa'] = sum(l['regra_certa'] for l in ls)
                saida[f'{arranjo}/{molde}'] = bloco
        return saida

    tarefas = [{'caso': c, 'arranjo': a} for c in casos_r46() for a in ('direta', 'decomposta')]
    gravar('r46-conta-na-leitura', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R46'), analisar)


# ===================================================================== R47
VEREDITOS = {'aprovado': 'O que foi observado mostra que o resultado cumpre o pedido por inteiro.',
             'defeito': 'O que foi observado mostra que o resultado descumpre o pedido.',
             'inconclusiva': 'O que foi observado nao basta para aprovar nem para condenar.'}


def casos_r47():
    sorteio = random.Random(SEMENTE + 1)
    nomes = ['alfa', 'beta', 'gama', 'delta', 'epsilon', 'zeta', 'eta', 'teta']
    casos = []
    for tipo in ('completa-certa', 'completa-errada', 'parcial-coerente', 'parcial-ja-errada'):
        for _ in range(12):
            itens = sorteio.sample(nomes, 4)
            publico = {i: sorteio.random() < 0.5 for i in itens}
            publico[itens[0]], publico[itens[1]] = True, False  # sempre há ao menos um de cada
            certos = [i for i in itens if publico[i]]
            lista = ', '.join(f"{i} ({'publico' if publico[i] else 'privado'})" for i in itens)
            if tipo == 'completa-certa':
                observacao, gold = f"Resultado completo observado: {', '.join(certos)}.", 'aprovado'
            elif tipo == 'completa-errada':
                observacao, gold = f"Resultado completo observado: {', '.join(certos + [itens[1]])}.", 'defeito'
            elif tipo == 'parcial-coerente':
                observacao, gold = f'Apenas o primeiro resultado foi observado: {certos[0]}. O restante esta oculto.', 'inconclusiva'
            else:
                observacao, gold = f'Apenas o primeiro resultado foi observado: {itens[1]}. O restante esta oculto.', 'defeito'
            casos.append({'tipo': tipo, 'gold': gold, 'completa': tipo.startswith('completa'),
                          'contraria': gold == 'defeito',
                          'texto': f'Pedido: devolver exatamente os itens publicos da lista. Lista: {lista}.\nObservacao do revisor: {observacao}'})
    return casos


def rodar_r47():
    def uma(t):
        c = t['caso']
        if t['arranjo'] == 'direta':
            perguntas = {'veredito': {'type': 'choice', 'instructions': 'Com base apenas no que foi observado, qual e o veredito sobre o resultado?', 'criteria': dict(VEREDITOS)}}
        else:
            perguntas = {'alcance': {'type': 'choice', 'instructions': 'A observacao mostra o resultado inteiro ou so uma parte?',
                                     'criteria': {'inteiro': 'A observacao cobre o resultado completo.', 'parte': 'A observacao cobre so parte do resultado; ha algo oculto.'}},
                         'contraria': {'type': 'choice', 'instructions': 'Algum item que FOI observado contraria o pedido?',
                                       'criteria': {'contraria': 'Ha item observado que nao deveria estar ali.', 'nao-contraria': 'Tudo o que foi observado e compativel com o pedido.'}}}
        respostas, detalhe = perguntar(c['texto'], perguntas, 'R47')
        r = respostas or {}
        linha = {'tipo': c['tipo'], 'gold': c['gold'], 'arranjo': t['arranjo'], **medidas(detalhe)}
        if t['arranjo'] == 'direta':
            linha.update(veredito=(r.get('veredito') or {}).get('choice'), confianca=(r.get('veredito') or {}).get('confidence'))
        else:
            alcance, contraria = (r.get('alcance') or {}).get('choice'), (r.get('contraria') or {}).get('choice')
            veredito = None if not (alcance and contraria) else 'defeito' if contraria == 'contraria' else 'aprovado' if alcance == 'inteiro' else 'inconclusiva'
            linha.update(veredito=veredito, alcance_certo=(alcance == 'inteiro') == c['completa'], contraria_certo=(contraria == 'contraria') == c['contraria'])
        return linha

    def analisar(linhas):
        saida = {}
        for arranjo in ('direta', 'decomposta'):
            for tipo in ('completa-certa', 'completa-errada', 'parcial-coerente', 'parcial-ja-errada'):
                ls = [l for l in linhas if l['arranjo'] == arranjo and l['tipo'] == tipo and l['veredito']]
                bloco = taxa(sum(l['veredito'] == l['gold'] for l in ls), len(ls))
                bloco['vereditos'] = {v: sum(l['veredito'] == v for l in ls) for v in VEREDITOS}
                if arranjo == 'direta':
                    bloco['erros_acima_do_corte'] = sum(l['veredito'] != l['gold'] and (l['confianca'] or 0) >= CORTE for l in ls)
                else:
                    bloco['alcance_certo'], bloco['contraria_certo'] = sum(l['alcance_certo'] for l in ls), sum(l['contraria_certo'] for l in ls)
                saida[f'{arranjo}/{tipo}'] = bloco
            ls = [l for l in linhas if l['arranjo'] == arranjo and l['veredito']]
            saida[f'{arranjo}/conjunto'] = taxa(sum(l['veredito'] == l['gold'] for l in ls), len(ls))
        return saida

    tarefas = [{'caso': c, 'arranjo': a} for c in casos_r47() for a in ('direta', 'decomposta')]
    gravar('r47-fiscal-com-evidencia-parcial', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R47'), analisar)


# ===================================================================== R48
def rodar_r48(caminho):
    with open(caminho, encoding='utf-8', newline='') as arquivo:
        linhas_csv = list(csv.DictReader(arquivo))
    por_classe = {}
    for l in linhas_csv:
        por_classe.setdefault(l['category'], []).append(l['text'])
    sorteio = random.Random(SEMENTE + 2)
    casos = [{'gold': classe, 'texto': texto} for classe in sorted(por_classe) for texto in sorteio.sample(sorted(por_classe[classe]), 2)]
    criterios = {classe: f"The message is about: {classe.replace('_', ' ')}." for classe in sorted(por_classe)}

    def uma(c):
        respostas, detalhe = perguntar(f"The bank customer wrote: \"{c['texto']}\"", {'assunto': {
            'type': 'choice', 'instructions': 'Which topic is this banking customer message about?', 'criteria': dict(criterios)}}, 'R48')
        bloco = (respostas or {}).get('assunto') or {}
        p = (bloco.get('probabilities') or {}).get(bloco.get('choice'))
        return {'gold': c['gold'], 'escolha': bloco.get('choice'), 'confianca': bloco.get('confidence'), 'p': p, 'texto': c['texto'], **medidas(detalhe)}

    def analisar(linhas):
        ls = [l for l in linhas if l['escolha']]
        k = len(criterios)
        com_p = [l for l in ls if l['p'] is not None]
        saida = {'classes': k, 'acuracia': taxa(sum(l['escolha'] == l['gold'] for l in ls), len(ls)),
                 'formula': taxa(sum(abs((k * l['p'] - 1) / (k - 1) - l['confianca']) <= 0.015 for l in com_p), len(com_p)),
                 'referencia_do_video': {'acuracia': '129/154', 'p>=0.95': '103/105'},
                 'latencia_mediana_ms': statistics.median(l['latencia_ms'] for l in ls if l['latencia_ms']),
                 'custo_medio_usd': sum(l['custo_usd'] for l in ls) / len(ls)}
        for corte in (0.90, 0.95, 0.99):
            aceitos = [l for l in com_p if l['p'] >= corte]
            saida[f'p>={corte}'] = {**taxa(sum(l['escolha'] == l['gold'] for l in aceitos), len(aceitos)), 'cobertura': round(len(aceitos) / len(com_p), 4)}
        return saida

    gravar('r48-banking77', em_paralelo(casos, uma, trabalhadores=8, rotulo='R48'), analisar)


# ===================================================================== R49
BASE_R49 = [
    ('assunto', 'Qual e o assunto da mensagem?', {'entrega': 'Fala de entrega.', 'cobranca': 'Fala de cobranca.', 'outro': 'Outro assunto.'}),
    ('cancelamento', 'O pedido envolve cancelamento?', {'envolve': 'Envolve cancelamento.', 'nao-envolve': 'Nao envolve.'}),
    ('dado-faltando', 'Falta algum dado para encaminhar o pedido?', {'falta': 'Falta dado, como numero do pedido.', 'completo': 'Tem o que precisa.'}),
    ('tom', 'Qual e o tom da mensagem?', {'calmo': 'Neutro ou cordial.', 'irritado': 'Irritado.'}),
]
MENSAGENS_R49 = [
    'Meu pedido 4471 chegou, mas veio um produto diferente do que comprei. Quero trocar.',
    'Cobraram duas vezes a fatura de agosto no meu cartao. Isso e um absurdo, resolvam hoje.',
    'Bom dia, quero cancelar a assinatura, por favor.',
    'Onde esta minha encomenda? Nao tenho o numero do pedido aqui.',
    'Gostaria de saber o horario de funcionamento da loja no feriado.',
    'Quero desistir da compra 9920 e receber o dinheiro de volta.',
]


def rodar_r49():
    def uma(t):
        copias = t['copias']
        perguntas = {f'{nome}-{n}': {'type': 'choice', 'instructions': instrucao, 'criteria': dict(criterios)}
                     for n in range(copias) for nome, instrucao, criterios in BASE_R49}
        respostas, detalhe = perguntar(f"O cliente escreveu: \"{t['mensagem']}\"", perguntas, 'R49')
        r = respostas or {}
        estaveis = sum(len({(r.get(f'{nome}-{n}') or {}).get('choice') for n in range(copias)}) == 1 for nome, _, _ in BASE_R49)
        return {'mensagem': t['i'], 'copias': copias, 'repeticao': t['repeticao'], 'perguntas': len(perguntas), 'respondidas': len(r),
                'base': {nome: (r.get(f'{nome}-0') or {}).get('choice') for nome, _, _ in BASE_R49},
                'perguntas_de_base_com_a_mesma_resposta_em_todas_as_copias': estaveis, 'rede_ms': (detalhe or {}).get('network_ms'), **medidas(detalhe)}

    def analisar(linhas):
        saida = {}
        for copias in (1, 4, 16):
            ls = [l for l in linhas if l['copias'] == copias and l['respondidas']]
            saida[f'{copias * 4}-perguntas'] = {
                'chamadas': len(ls), 'todas_respondidas': sum(l['respondidas'] == l['perguntas'] for l in ls),
                'latencia_mediana_ms': statistics.median(l['latencia_ms'] for l in ls if l['latencia_ms']),
                'rede_mediana_ms': statistics.median(l['rede_ms'] for l in ls if l['rede_ms']) if any(l['rede_ms'] for l in ls) else None,
                'custo_medio_usd': sum(l['custo_usd'] for l in ls) / len(ls),
                'copias_estaveis': taxa(sum(l['perguntas_de_base_com_a_mesma_resposta_em_todas_as_copias'] for l in ls), 4 * len(ls))}
        unica = {(l['mensagem'], l['repeticao']): l['base'] for l in linhas if l['copias'] == 1}
        grande = {(l['mensagem'], l['repeticao']): l['base'] for l in linhas if l['copias'] == 16}
        comuns = [k for k in unica if k in grande]
        saida['base_igual_entre_4_e_64'] = taxa(sum(unica[k][q] == grande[k][q] for k in comuns for q in unica[k]), 4 * len(comuns))
        return saida

    tarefas = [{'i': i, 'mensagem': m, 'copias': c, 'repeticao': r} for i, m in enumerate(MENSAGENS_R49) for c in (1, 4, 16) for r in range(4)]
    gravar('r49-sessenta-e-quatro-perguntas', em_paralelo(tarefas, uma, trabalhadores=4, rotulo='R49'), analisar)


def main():
    analise = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analise.add_argument('--rodar', nargs='*', default=[])
    analise.add_argument('--banking', help='caminho do test.csv do Banking77 (PolyAI-LDN/task-specific-datasets)')
    args = analise.parse_args()
    for nome in args.rodar:
        print(f'\n===== {nome}')
        {'R46': rodar_r46, 'R47': rodar_r47, 'R49': rodar_r49, 'R48': lambda: rodar_r48(args.banking)}[nome]()


if __name__ == '__main__':
    main()
