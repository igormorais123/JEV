"""Análise pareada com a unidade de agrupamento correta.

O critério congelado no pré-registro pedia que "o limite inferior do intervalo de Wilson
sobre famílias não cruzasse zero". Isso é vacuoso: Wilson é intervalo de uma proporção,
que vive em [0,1] e nunca é negativo. O teste que deveria existir é sobre a DIFERENÇA
pareada de acurácia, respeitando a dependência dentro da família.

Aqui está o procedimento que substitui aquele critério, junto com o limite superior de
erro quando não se observa erro nenhum — porque zero erros não é taxa de erro zero.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMENTE = 20260918
REPETICOES = 20000


def bootstrap_cluster(clusters, repeticoes=REPETICOES, semente=SEMENTE):
    """IC 95% da diferença média pareada, reamostrando FAMÍLIAS inteiras.

    clusters: {familia: [(acerto_a, acerto_b), ...]} com um par por caso.
    A reamostragem é de famílias, não de casos: casos da mesma família são dependentes
    por construção, e tratá-los como independentes estreitaria o intervalo artificialmente.
    """
    nomes = list(clusters)
    if not nomes:
        return None
    sorteador = random.Random(semente)
    diferencas = []
    for _ in range(repeticoes):
        amostra = [clusters[sorteador.choice(nomes)] for _ in nomes]
        casos = [par for familia in amostra for par in familia]
        if not casos:
            continue
        a = sum(1 for x, _ in casos if x) / len(casos)
        b = sum(1 for _, y in casos if y) / len(casos)
        diferencas.append(a - b)
    diferencas.sort()
    corte = int(len(diferencas) * 0.025)
    todos = [par for familia in clusters.values() for par in familia]
    observada = (sum(1 for x, _ in todos if x) - sum(1 for _, y in todos if y)) / len(todos)
    return {
        'diferenca_observada': round(observada, 4),
        'ic95': [round(diferencas[corte], 4), round(diferencas[-corte - 1], 4)],
        # Medida de cauda da distribuicao bootstrap, nao um p-valor calibrado sob hipotese
        # nula. Sem o min(1.0) a conta passa de 1 quando todas as diferencas sao iguais.
        'massa_de_cauda_bilateral': round(min(1.0, 2 * min(
            sum(1 for d in diferencas if d <= 0) / len(diferencas),
            sum(1 for d in diferencas if d >= 0) / len(diferencas))), 4),
        'n_familias': len(nomes), 'n_casos': len(todos), 'repeticoes': repeticoes,
    }


def limite_superior_erro(erros, total, confianca=0.95):
    """Clopper-Pearson unilateral. Com zero erros em n, o limite é 1 - (1-c)^(1/n).

    Serve para não confundir "não vimos erro" com "não há erro".
    """
    if total == 0:
        return 1.0
    if erros == 0:
        return round(1 - (1 - confianca) ** (1 / total), 6)
    from math import comb
    baixo, alto = erros / total, 1.0
    for _ in range(200):
        meio = (baixo + alto) / 2
        cauda = sum(comb(total, k) * meio ** k * (1 - meio) ** (total - k) for k in range(erros + 1))
        if cauda > 1 - confianca:
            baixo = meio
        else:
            alto = meio
    return round((baixo + alto) / 2, 6)


def analisar_e1():
    dados = json.loads((ROOT / 'runs' / 'e1-triagem' / 'relatorio.json').read_text(encoding='utf-8'))
    clusters = defaultdict(list)
    for caso in dados['casos']:
        clusters[caso['family']].append((caso['jev'] == caso['gold'], caso['regra'] == caso['gold']))
    return bootstrap_cluster(clusters)


def analisar_e3():
    dados = json.loads((ROOT / 'runs' / 'e3-evidencia' / 'relatorio.json').read_text(encoding='utf-8'))
    clusters = defaultdict(list)
    for caso in dados['casos']:
        clusters[caso['family']].append((caso['jev'] == caso['gold'], caso['regra'] == caso['gold']))
    return bootstrap_cluster(clusters)


def analisar_posicao_e2b(repeticoes=REPETICOES, semente=SEMENTE):
    """Teste de posição por permutação, com o CASO como unidade.

    O qui-quadrado anterior tratou 200 observações como independentes, quando são 40 casos
    repetidos 5 vezes. Aqui embaralhamos os rótulos de posição dentro de cada caso, o que
    preserva a dificuldade do caso e testa só a posição.
    """
    dados = json.loads((ROOT / 'runs' / 'e2b-posicao' / 'relatorio.json').read_text(encoding='utf-8'))
    por_caso = defaultdict(list)
    for o in dados['observacoes']:
        por_caso[o['case_id']].append((o['posicao'], bool(o['acerto'])))

    def amplitude(atribuicao):
        acertos = defaultdict(lambda: [0, 0])
        for posicao, acerto in atribuicao:
            acertos[posicao][0] += acerto
            acertos[posicao][1] += 1
        taxas = [a / t for a, t in acertos.values() if t]
        return max(taxas) - min(taxas) if taxas else 0.0

    observado = amplitude([par for lista in por_caso.values() for par in lista])
    sorteador = random.Random(semente)
    extremos = 0
    for _ in range(repeticoes):
        embaralhado = []
        for lista in por_caso.values():
            posicoes = [p for p, _ in lista]
            sorteador.shuffle(posicoes)
            embaralhado.extend(zip(posicoes, [a for _, a in lista]))
        if amplitude(embaralhado) >= observado:
            extremos += 1
    # (extremos + 1) / (repeticoes + 1) evita p igual a zero e nao subestima a cauda.
    # Arredondar para 4 casas traria o zero de volta quando extremos = 0, entao guardamos
    # o valor com precisao suficiente para o piso aparecer.
    p_valor = (extremos + 1) / (repeticoes + 1)
    return {'amplitude_observada': round(observado, 4),
            'p_permutacao': float(f'{p_valor:.6g}'),
            'p_permutacao_piso': float(f'{1 / (repeticoes + 1):.6g}'),
            'n_casos': len(por_caso), 'n_observacoes': sum(len(v) for v in por_caso.values()),
            'repeticoes': repeticoes}


def analisar_calibracao(corte=0.95, conjunto='piloto'):
    """Risco-cobertura com duas correcoes exigidas pela segunda revisao.

    1. A cobertura usa TODOS os casos programados. Caso sem confidence e falha do braco,
       nao um caso que nunca existiu; exclui-lo do denominador inflaria a cobertura.
    2. O limite superior de erro e calculado tambem no nivel de FAMILIA. Tratar 28 casos
       de dez familias como 28 ensaios independentes estreita o intervalo artificialmente,
       porque casos da mesma familia sao dependentes por construcao. O limite por familia
       e a leitura conservadora; o limite por caso e o piso otimista.
    """
    origem = ROOT / 'runs' / ('e7-confirmacao' if conjunto == 'confirmacao' else 'e1-triagem')
    programados = json.loads((origem / 'relatorio.json').read_text(encoding='utf-8'))['casos']
    com_confianca = [c for c in programados if c.get('jev_confidence') is not None]
    aceitos = [c for c in com_confianca if c['jev_confidence'] >= corte]
    erros = sum(1 for c in aceitos if c['jev'] != c['gold'])

    familias = defaultdict(list)
    for c in aceitos:
        familias[c['family']].append(c['jev'] == c['gold'])
    familias_com_erro = sum(1 for v in familias.values() if not all(v))

    return {
        'conjunto': conjunto,
        'corte': corte,
        'casos_programados': len(programados),
        'casos_com_confianca': len(com_confianca),
        'aceitos': len(aceitos),
        'erros_entre_aceitos': erros,
        'cobertura_sobre_programados': round(len(aceitos) / len(programados), 4) if programados else None,
        'familias_representadas_entre_aceitos': len(familias),
        'familias_com_erro': familias_com_erro,
        'limite_superior_erro_por_caso': limite_superior_erro(erros, len(aceitos)),
        'limite_superior_erro_por_familia': limite_superior_erro(familias_com_erro, len(familias)),
        'leitura': ('Os dois limites medem eventos DIFERENTES e nao sao intercambiaveis. '
                    'O limite por caso supoe casos independentes, o que este desenho nao tem. '
                    'O limite por familia e sobre a probabilidade de uma familia conter ao menos '
                    'um caso aceito errado, dando peso igual a familias de tamanhos diferentes; '
                    'e o numero que devemos citar, e nao um limite conservador do risco por caso.'),
    }


def main():
    saida = {'e1_triagem': analisar_e1(), 'e3_evidencia': analisar_e3(),
             'e2b_posicao': analisar_posicao_e2b(),
             'calibracao_0.9': analisar_calibracao(0.90),
             'calibracao_0.95': analisar_calibracao(0.95),
             'calibracao_0.99': analisar_calibracao(0.99)}
    # A calibracao que o painel cita e a da particao de confirmacao. Gravar so a do piloto
    # apagava a chave e fazia o placar cair silenciosamente no numero do desenvolvimento.
    if (ROOT / 'runs' / 'e7-confirmacao' / 'relatorio.json').exists():
        # 0,90 e o corte que a recomendacao usa: deixa-lo de fora era nao calcular
        # justamente o limite de erro do numero que o relatorio vende.
        for corte in (0.90, 0.95, 0.99):
            saida[f'calibracao_confirmacao_{corte}'] = analisar_calibracao(corte, conjunto='confirmacao')
    destino = ROOT / 'runs' / 'analise-pareada.json'
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding='utf-8')
    for nome, dados in saida.items():
        print(f'{nome}: {json.dumps(dados, ensure_ascii=False)}')
    print(f'\nGravado em {destino.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
