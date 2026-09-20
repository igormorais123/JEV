"""R19 — atacar a pior fraqueza medida, e testar uma capacidade do contrato que ninguém usou.

O mapa de limites tem uma família pior que todas as outras: **ação atribuída a terceiro**,
75,0% em 8 casos. É a única armadilha semântica em que o Jev erra com frequência, e nenhuma
rodada tentou consertá-la — mediu-se e seguiu-se em frente. Oito casos também são poucos para
comparar mitigação nenhuma.

Duas coisas novas aqui.

**Primeira: o gabarito não vem de leitura.** As mensagens são geradas por molde, e o molde
define a resposta certa por construção. Quando o pedido é *"escreva uma mensagem em que a IRMÃ
do cliente quer cancelar e quem escreve só pergunta como funciona"*, a resposta é `informacao`
porque o molde mandou ser — não porque eu li e achei. O gerador não escolhe a classe, ele
preenche um molde cuja classe já está fixada.

**Segunda: o contrato aceita várias perguntas numa chamada, e o estudo nunca usou isso.** Todas
as 6.000 chamadas mandaram uma pergunta só. Se a confusão é sobre **quem** pede, talvez
perguntar o sujeito junto com a ação resolva — e custa a mesma chamada, porque o estado é o
mesmo e o preço é por token de entrada.

**H19a.** Uma instrução que manda considerar só quem escreve melhora a família do terceiro.
**H19b.** Perguntar o sujeito e a ação na mesma chamada melhora mais do que instruir.
**H19c.** A classe de escape, que resolveu o texto sem pedido, não ajuda aqui — o problema não é
falta de opção, é atribuição errada.

**Falsificação.** Se nenhuma formulação superar a atual em mais de 5 pontos na família do
terceiro, a fraqueza é do modelo e não da pergunta, e entra no guia como limite.

    python laboratorio/r19_armadilha_de_sujeito.py --gerar
    python laboratorio/r19_armadilha_de_sujeito.py --rodar
"""
import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor.run_e12_replicacao import CRITERIOS, INSTRUCOES  # noqa: E402
from laboratorio.nucleo import chave, em_paralelo, mcnemar_exato, perguntar, wilson  # noqa: E402
from laboratorio.r15_adversario_externo import http  # noqa: E402

CORPUS = RAIZ / 'laboratorio' / 'r19-corpus.json'
DESTINO = RAIZ / 'laboratorio' / 'r19-armadilha.json'
SEMENTE = 20260920
GERADOR = 'mistralai/mistral-nemo'
POR_MOLDE = 26

# Cada molde fixa a resposta certa ANTES de existir mensagem. O gerador preenche, não decide.
MOLDES = [
    ('terceiro-quer', 'informacao',
     'Escreva uma mensagem curta de cliente para um atendimento em que OUTRA PESSOA (parente, '
     'socio, chefe) quer {acao}, mas quem escreve apenas pergunta como funciona e nao pede nada. '
     'Nao use as palavras "apenas pergunto" nem "so quero saber".'),
    ('terceiro-quer-eu-nao', 'informacao',
     'Escreva uma mensagem curta de cliente em que OUTRA PESSOA quer {acao} e quem escreve diz '
     'que NAO quer isso, so quer entender as consequencias.'),
    ('terceiro-contra-eu-quero', '{acao_classe}',
     'Escreva uma mensagem curta de cliente em que outra pessoa ACONSELHA A NAO fazer nada, mas '
     'quem escreve decide e pede {acao} para si mesmo, de forma clara.'),
    ('terceiro-ja-fez', 'informacao',
     'Escreva uma mensagem curta de cliente em que OUTRA PESSOA ja fez {acao} no passado e quem '
     'escreve so quer saber se aquilo continua valendo. Nao pede nada novo.'),
    ('eu-peco-terceiro-cita', '{acao_classe}',
     'Escreva uma mensagem curta de cliente em que quem escreve pede {acao} para si, e menciona '
     'de passagem que um parente teve outro problema diferente.'),
]

ACOES = [
    ('cancelar o plano', 'cancelar'),
    ('trocar o produto por outro igual', 'trocar'),
    ('a segunda via do boleto', 'cobranca'),
    ('saber onde esta o pedido', 'rastrear'),
]

# ------------------------------------------------------------------ formulações

SUJEITO = {
    'quem-escreve': 'A acao e pedida por quem escreve a mensagem, para si mesmo.',
    'outra-pessoa': 'A acao e de outra pessoa, ou foi so mencionada, ou foi recusada por quem escreve.',
}

FORMULACOES = {
    'A-atual': {
        'perguntas': {'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                               'criteria': dict(CRITERIOS)}},
        'ler': lambda r: (r.get('acao') or {}),
    },
    'B-instrucao-de-sujeito': {
        'perguntas': {'acao': {'type': 'choice', 'criteria': dict(CRITERIOS), 'instructions': (
            'Qual acao o atendimento deve tomar? Considere APENAS o que QUEM ESCREVE esta '
            'pedindo para si mesmo. Acao de outra pessoa, acao mencionada de passagem e acao '
            'recusada por quem escreve NAO contam como pedido.')}},
        'ler': lambda r: (r.get('acao') or {}),
    },
    'C-com-escape': {
        'perguntas': {'acao': {'type': 'choice', 'instructions': INSTRUCOES, 'criteria': {
            **CRITERIOS,
            'nao-se-aplica': 'A mensagem nao contem pedido de acao de quem escreve.'}}},
        'ler': lambda r: (r.get('acao') or {}),
    },
    'D-sujeito-e-acao': {
        # Duas perguntas na MESMA chamada: o contrato aceita, e o estudo nunca tinha usado.
        'perguntas': {
            'sujeito': {'type': 'choice', 'criteria': dict(SUJEITO), 'instructions':
                        'De quem e a acao mencionada na mensagem?'},
            'acao': {'type': 'choice', 'instructions': INSTRUCOES, 'criteria': dict(CRITERIOS)},
        },
        # Se a ação é de outra pessoa, o pedido de quem escreve é informação.
        'ler': lambda r: ({'choice': 'informacao',
                           'confidence': (r.get('sujeito') or {}).get('confidence')}
                          if (r.get('sujeito') or {}).get('choice') == 'outra-pessoa'
                          else (r.get('acao') or {})),
    },
}


def gerar(api_key):
    sorteio = random.Random(SEMENTE)
    pedidos = []
    for nome, gold, molde in MOLDES:
        for i in range(POR_MOLDE):
            acao, classe = ACOES[i % len(ACOES)]
            pedidos.append({'molde': nome, 'i': i, 'acao': acao, 'classe': classe,
                            'gold': classe if gold.startswith('{') else gold,
                            'pedido': molde.format(acao=acao, acao_classe=classe)})

    def uma(item):
        corpo = {'model': GERADOR, 'max_tokens': 220, 'temperature': 1.0,
                 'messages': [{'role': 'user', 'content':
                               item['pedido'] + ' Responda so com a mensagem, sem aspas, '
                               'sem explicacao, em portugues do Brasil, ate 45 palavras.'}]}
        status, resposta = http(corpo, api_key, rodada='R19-geracao', modelo=GERADOR)
        if status != 200:
            return None
        try:
            texto = resposta['choices'][0]['message']['content'].strip().strip('"')
        except (KeyError, IndexError, TypeError, AttributeError):
            return None
        return {**item, 'texto': ' '.join(texto.split())[:400]} if len(texto) > 25 else None

    brutos = [x for x in em_paralelo(pedidos, uma, trabalhadores=8, rotulo='R19-gera') if x]
    # Filtro mecânico: mensagem tem de mencionar outra pessoa nos moldes que pedem terceiro.
    # O primeiro recorte desta lista derrubou 34 de 70 mensagens geradas, muitas delas boas --
    # o gerador escreve "o gerente", "a titular da conta", "a pessoa que assinou". A lista
    # cresceu antes de qualquer rodada paga de classificação.
    marcas = re.compile(r'\b(minha|meu|nossa|nosso|ela|ele|dela|dele|irm|espos|marid|m[aã]e|pai|'
                        r's[oó]cio|chefe|amig|filh|namorad|colega|vizinh|patr[aã]o|tio|tia|prim|'
                        r'gerent|diretor|respons[aá]vel|titular|contratant|assinant|pessoa|'
                        r'algu[eé]m|terceir|parente|sogr|cunhad|av[oó]|neto|genro|nora|'
                        r'funcion[aá]ri|equipe|departament|setor)', re.I)
    aprovados, recusas = [], Counter()
    for item in brutos:
        precisa_terceiro = item['molde'].startswith('terceiro') or item['molde'].startswith('eu-peco')
        if precisa_terceiro and not marcas.search(item['texto']):
            recusas['sem mencao a terceiro'] += 1
            continue
        aprovados.append({k: item[k] for k in ('molde', 'gold', 'classe', 'texto')})
    print(f'{len(brutos)} gerados, {len(aprovados)} aprovados; recusas: {dict(recusas)}')
    print(Counter(a['molde'] for a in aprovados))
    CORPUS.write_text(json.dumps({'semente': SEMENTE, 'gerador': GERADOR, 'moldes': MOLDES,
                                  'casos': aprovados}, ensure_ascii=False, indent=1),
                      encoding='utf-8')
    return aprovados


def executar(tarefa):
    forma = FORMULACOES[tarefa['formulacao']]
    respostas, detalhe = perguntar(f"Mensagem do cliente:\n{tarefa['texto']}",
                                   forma['perguntas'], rodada='R19')
    bloco = forma['ler'](respostas or {})
    return {'formulacao': tarefa['formulacao'], 'i': tarefa['i'], 'molde': tarefa['molde'],
            'gold': tarefa['gold'], 'escolha': bloco.get('choice'),
            'confianca': bloco.get('confidence'),
            'sujeito': ((respostas or {}).get('sujeito') or {}).get('choice'),
            'texto': tarefa['texto'][:120]}


def rodar():
    casos = json.loads(CORPUS.read_text(encoding='utf-8'))['casos']
    tarefas = [{**c, 'i': i, 'formulacao': f}
               for f in FORMULACOES for i, c in enumerate(casos)]
    print(f'{len(casos)} mensagens × {len(FORMULACOES)} formulações = {len(tarefas)} chamadas')

    linhas = em_paralelo(tarefas, executar, trabalhadores=8, rotulo='R19')
    resultado = {'casos': len(casos), 'formulacoes': {}, 'detalhe': linhas}

    moldes = [m[0] for m in MOLDES]
    print(f"\n   {'formulação':24} {'geral':>8} " + ' '.join(f'{m[:13]:>14}' for m in moldes))
    for nome in FORMULACOES:
        grupo = [l for l in linhas if l['formulacao'] == nome]
        validas = [l for l in grupo if l['escolha']]
        certos = sum(1 for l in validas if l['escolha'] == l['gold'])
        bloco = {'n': len(validas), 'acertos': certos,
                 'taxa': round(certos / len(validas), 4) if validas else None,
                 'ic95': wilson(certos, len(validas)), 'por_molde': {}}
        linha = f"   {nome:24} {bloco['taxa']:>7.1%} "
        for molde in moldes:
            sub = [l for l in validas if l['molde'] == molde]
            acertos = sum(1 for l in sub if l['escolha'] == l['gold'])
            taxa = acertos / len(sub) if sub else None
            bloco['por_molde'][molde] = {'n': len(sub), 'acertos': acertos,
                                         'taxa': round(taxa, 4) if taxa is not None else None}
            linha += f'{(f"{taxa:.0%}" if taxa is not None else "—"):>14} '
        resultado['formulacoes'][nome] = bloco
        print(linha)

    # A família que importa: os moldes em que a ação é de outra pessoa.
    de_terceiro = ('terceiro-quer', 'terceiro-quer-eu-nao', 'terceiro-ja-fez')
    print('\n   só a família do terceiro (onde o gabarito é `informacao`)')
    for nome in FORMULACOES:
        sub = [l for l in linhas if l['formulacao'] == nome and l['molde'] in de_terceiro
               and l['escolha']]
        acertos = sum(1 for l in sub if l['escolha'] == l['gold'])
        resultado['formulacoes'][nome]['familia_terceiro'] = {
            'n': len(sub), 'acertos': acertos,
            'taxa': round(acertos / len(sub), 4) if sub else None,
            'ic95': wilson(acertos, len(sub))}
        bloco = resultado['formulacoes'][nome]['familia_terceiro']
        print(f"   {nome:24} {acertos:>3}/{len(sub):<3} {bloco['taxa']:>7.1%} "
              f"IC95 {bloco['ic95']}")

    por_caso = {}
    for linha in linhas:
        por_caso.setdefault(linha['i'], {})[linha['formulacao']] = linha

    def pareado(a, b, familia=None):
        so_a = so_b = 0
        for bloco in por_caso.values():
            la, lb = bloco.get(a), bloco.get(b)
            if not la or not lb or (familia and la['molde'] not in familia):
                continue
            ca, cb = la['escolha'] == la['gold'], lb['escolha'] == lb['gold']
            so_a += ca and not cb
            so_b += cb and not ca
        return {'so_' + a: so_a, 'so_' + b: so_b, 'p': mcnemar_exato(so_a, so_b)}

    resultado['pareado'] = {}
    print('\n   contra a formulação atual, na família do terceiro (McNemar exato)')
    for nome in ('B-instrucao-de-sujeito', 'C-com-escape', 'D-sujeito-e-acao'):
        bloco = pareado(nome, 'A-atual', familia=de_terceiro)
        geral = pareado(nome, 'A-atual')
        resultado['pareado'][nome] = {'familia_terceiro': bloco, 'geral': geral}
        marca = ' *' if bloco['p'] < 0.05 else ''
        print(f'   {nome:24} {bloco}{marca}   geral: {geral}')

    # O que a pergunta de sujeito acertou por si só, na D.
    d = [l for l in linhas if l['formulacao'] == 'D-sujeito-e-acao' and l['sujeito']]
    esperado = {m: ('outra-pessoa' if m in de_terceiro else 'quem-escreve') for m in moldes}
    acertos = sum(1 for l in d if l['sujeito'] == esperado[l['molde']])
    resultado['pergunta_de_sujeito'] = {
        'n': len(d), 'acertos': acertos,
        'taxa': round(acertos / len(d), 4) if d else None,
        'ic95': wilson(acertos, len(d)),
        'distribuicao': Counter(l['sujeito'] for l in d).most_common()}
    print(f"\n   a pergunta 'de quem é a ação?', sozinha: {acertos}/{len(d)} = "
          f"{resultado['pergunta_de_sujeito']['taxa']:.1%}")

    base = resultado['formulacoes']['A-atual']['familia_terceiro']['taxa']
    melhores = sorted(((v['familia_terceiro']['taxa'], k)
                       for k, v in resultado['formulacoes'].items()), reverse=True)
    ganho = melhores[0][0] - base
    resultado['veredito'] = (
        f'{melhores[0][1]} melhora {ganho:+.1%} na família do terceiro'
        if ganho > 0.05 else
        'nenhuma formulação melhora mais de 5 pontos: a fraqueza é do modelo, não da pergunta')
    print(f"\n   veredito: {resultado['veredito']}")

    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gerar', action='store_true')
    parser.add_argument('--rodar', action='store_true')
    args = parser.parse_args()
    if args.gerar or not CORPUS.exists():
        gerar(chave())
    if args.rodar:
        rodar()


if __name__ == '__main__':
    main()
