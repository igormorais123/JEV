"""R14 — o Jev lê o mapa de limites do Jev e decide o que fazer com ele.

O pedido é fechar o ciclo: decisão baseada em dado analisado pelo próprio instrumento,
registrada, mapeada e mensurada. Só que "a IA avalia a si mesma" é exatamente o tipo de coisa
que vira teatro se ninguém marcar o gabarito. Então aqui há duas colunas: a decisão do Jev
sobre cada dimensão medida, e a minha, escrita antes de rodar. A concordância entre as duas é
o que se mede — e é ela que diz se o instrumento serve para esta tarefa nova.

O ganho, se houver concordância: quando uma rodada futura acrescentar uma dimensão ao mapa, a
classificação de risco dela sai por US$ 0,00002 em vez de esperar eu ler.

    python laboratorio/r14_autorrecursivo.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from laboratorio.nucleo import em_paralelo, perguntar  # noqa: E402

MAPA = RAIZ / 'laboratorio' / 'mapa-de-limites.json'
DESTINO = RAIZ / 'laboratorio' / 'r14-decisoes.json'

DECISAO = {
    'seguro': ('A condicao nao muda o resultado de forma relevante: a queda de acuracia e '
               'pequena e o modelo continua avisando quando erra. Pode ser usada em producao '
               'sem cuidado especial.'),
    'exige-cuidado': ('A condicao degrada o resultado, mas a confianca do modelo cai junto, '
                      'entao um corte de confianca ainda protege. Pode ser usada com corte e '
                      'revisao humana do que fica abaixo dele.'),
    'proibido': ('A condicao quebra o resultado E o modelo continua confiante quando erra. '
                 'Nenhum corte de confianca protege. Nao pode ser usada em producao.'),
}

PERGUNTA = ('Abaixo estao os resultados de um teste de estresse de um classificador de texto. '
            'Considerando a queda de acuracia E se a confianca do modelo cai quando ele erra, '
            'que decisao operacional esta condicao merece?')

# Meu gabarito, escrito ANTES de rodar, a partir da leitura do mapa. A regra que usei:
# proibido = erra muito e continua confiante; exige-cuidado = erra e avisa; seguro = quase nao erra.
MEU_GABARITO = {
    'referencia/E12 original': 'seguro',
    'opcoes/2': 'seguro', 'opcoes/3': 'seguro', 'opcoes/5': 'seguro', 'opcoes/12': 'seguro',
    'opcoes/20': 'exige-cuidado', 'opcoes/40': 'exige-cuidado',
    'opcoes/80': 'exige-cuidado', 'opcoes/147': 'exige-cuidado',
    'ruido/5%': 'seguro', 'ruido/estilo Igor': 'seguro', 'ruido/15%': 'exige-cuidado',
    'ruido/30%': 'exige-cuidado', 'ruido/50%': 'exige-cuidado', 'ruido/70%': 'exige-cuidado',
    'diluicao/0k-antes': 'seguro', 'diluicao/8k-antes': 'seguro', 'diluicao/20k-antes': 'seguro',
    'diluicao/50k-antes': 'seguro', 'diluicao/50k-depois': 'seguro',
    'ordem das opcoes/inversa': 'seguro', 'ordem das opcoes/sorteada': 'seguro',
    'armadilha semantica/48 armadilhas': 'exige-cuidado',
    'armadilha semantica/A-adiado': 'seguro', 'armadilha semantica/B-concluida': 'seguro',
    'armadilha semantica/C-terceiro': 'exige-cuidado',
    'armadilha semantica/D-negado': 'seguro',
    'armadilha semantica/E-parcial': 'exige-cuidado',
    'armadilha semantica/F-pressuposto': 'exige-cuidado',
    'sobreposicao/parcial': 'seguro', 'sobreposicao/total': 'exige-cuidado',
    'idioma/ingles': 'seguro', 'idioma/misto': 'seguro', 'idioma/sem-acento': 'seguro',
    'instrucao/curta': 'seguro', 'instrucao/contraditoria': 'seguro',
    'combinado/ruido50+160opcoes+8k': 'exige-cuidado',
}


def fichas():
    mapa = json.loads(MAPA.read_text(encoding='utf-8'))
    referencia = mapa['dimensoes']['referencia'][0]['acuracia']
    saida = []
    for dimensao, niveis in mapa['dimensoes'].items():
        for nivel in niveis:
            if nivel['acuracia'] is None:
                continue
            chave = f"{dimensao}/{nivel['nivel']}"
            queda = (nivel['acuracia'] - referencia) * 100
            texto = (
                f"Condicao testada: {dimensao}, nivel {nivel['nivel']}.\n"
                f"Acuracia nesta condicao: {nivel['acuracia'] * 100:.1f} por cento, "
                f"em {nivel['n']} casos.\n"
                f"Acuracia na condicao normal, sem estresse: {referencia * 100:.1f} por cento.\n"
                f"Variacao: {queda:+.1f} pontos percentuais.\n")
            if nivel['conf_erros'] is not None:
                texto += (f"Confianca media que o modelo declarou nos casos em que ERROU: "
                          f"{nivel['conf_erros']:.2f} (de 0 a 1).\n")
            else:
                texto += "Confianca nos erros: nao disponivel nesta condicao.\n"
            if nivel['erros_acima_090'] is not None:
                texto += (f"Erros cometidos com confianca alta (0,90 ou mais): "
                          f"{nivel['erros_acima_090']}.\n")
            saida.append({'chave': chave, 'texto': texto, 'meu': MEU_GABARITO.get(chave)})
    return saida


def executar(ficha):
    respostas, detalhe = perguntar(ficha['texto'],
                                   {'decisao': {'type': 'choice', 'instructions': PERGUNTA,
                                                'criteria': dict(DECISAO)}},
                                   rodada='R14')
    alvo = (respostas or {}).get('decisao') or {}
    return {'chave': ficha['chave'], 'meu': ficha['meu'], 'jev': alvo.get('choice'),
            'confianca': alvo.get('confidence'),
            'erro': None if respostas else (detalhe or {}).get('erro')}


def main():
    lista = fichas()
    faltando = [f['chave'] for f in lista if not f['meu']]
    if faltando:
        print(f'AVISO: sem gabarito meu para {faltando}')
    print(f'{len(lista)} condições medidas vão ao Jev para decisão')

    linhas = em_paralelo(lista, executar, trabalhadores=10, rotulo='R14')
    validas = [l for l in linhas if l['jev'] and l['meu']]
    concordam = [l for l in validas if l['jev'] == l['meu']]
    divergem = [l for l in validas if l['jev'] != l['meu']]

    # A divergência que importa é a perigosa: o Jev afrouxar o que eu apertei.
    ordem = {'seguro': 0, 'exige-cuidado': 1, 'proibido': 2}
    afrouxou = [l for l in divergem if ordem[l['jev']] < ordem[l['meu']]]
    apertou = [l for l in divergem if ordem[l['jev']] > ordem[l['meu']]]

    resultado = {'condicoes': len(validas),
                 'concordancia': round(len(concordam) / len(validas), 4) if validas else None,
                 'divergencias': divergem, 'afrouxou': afrouxou, 'apertou': apertou,
                 'decisoes': linhas}
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')

    print(f"\n== R14: o Jev decidindo sobre os dados do Jev")
    print(f"   concordância com a minha leitura: {len(concordam)}/{len(validas)} = "
          f"{resultado['concordancia']:.1%}")
    print(f"   divergiu afrouxando (perigoso): {len(afrouxou)} | "
          f"divergiu apertando (conservador): {len(apertou)}")
    for linha in divergem:
        print(f"      {linha['chave']:38} eu={linha['meu']:14} jev={linha['jev']:14} "
              f"conf={linha['confianca']}")

    print('\n== as decisões, como o Jev as classificou')
    por_decisao = {}
    for linha in linhas:
        por_decisao.setdefault(linha['jev'], []).append(linha['chave'])
    for decisao in ('proibido', 'exige-cuidado', 'seguro'):
        itens = por_decisao.get(decisao, [])
        print(f"   {decisao:14} ({len(itens)}): {', '.join(itens[:6])}"
              + (' …' if len(itens) > 6 else ''))


if __name__ == '__main__':
    main()
