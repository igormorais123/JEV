"""R1, R2 e R3 — quantas opções, em que ordem, e escrito de que jeito.

As três rodadas compartilham o mesmo corpus (os 90 casos do E12) e o mesmo gabarito, e por isso
rodam num despacho só: o contraste é pareado caso a caso, e o que muda é apenas a condição.

R1: 2, 3, 5 e 12 opções.        H1: a acurácia cai material entre 5 e 12.
R2: três permutações das 5.     H2: a escolha é invariante à ordem.
R3: original, ruído leve, ruído pesado, "estilo Igor".  H3: invariante a ruído tipográfico.

    python laboratorio/r1_r3_estresse.py
"""
import json
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from executor.run_e12_replicacao import CRITERIOS, INSTRUCOES  # noqa: E402
from laboratorio.nucleo import (bootstrap_diferenca, em_paralelo, mcnemar_exato,  # noqa: E402
                                perguntar, wilson)

CORPUS = RAIZ / 'data' / 'corpus' / 'triagem-replicacao.jsonl'
DESTINO = RAIZ / 'laboratorio' / 'r1-r3-estresse.json'
SEMENTE = 20260919

# ---------------------------------------------------------------- R1: opções

# Distratores plausíveis, escritos ANTES de qualquer execução. Todos são ações de atendimento
# que não aparecem no corpus: se o Jev escolher um deles, é erro de discriminação, não
# ambiguidade do gabarito.
DISTRATORES = {
    'agendar': 'O remetente pede para marcar, remarcar ou desmarcar visita, instalacao ou atendimento.',
    'reclamar': 'O remetente registra insatisfacao com atendimento ou servico, sem pedir acao concreta.',
    'elogiar': 'O remetente agradece ou elogia o atendimento recebido.',
    'atualizar-cadastro': 'O remetente pede alteracao de endereco, telefone, e-mail ou titularidade.',
    'segunda-linha': 'O remetente pede contratacao de servico ou produto adicional.',
    'suporte-tecnico': 'O remetente relata falha tecnica e pede diagnostico ou reparo remoto.',
    'privacidade': 'O remetente pede exclusao de dados pessoais ou informacao sobre uso deles.',
}

# Colapso do gabarito nas condições de 2 e 3 opções, fixado junto com os distratores.
MAPA_3 = {'cancelar': 'encerrar', 'trocar': 'resolver-produto', 'rastrear': 'consultar',
          'cobranca': 'resolver-produto', 'informacao': 'consultar'}
CRITERIOS_3 = {
    'encerrar': 'O remetente pede encerrar, cancelar ou desistir de um pedido, servico ou contrato.',
    'resolver-produto': ('O remetente pede troca, devolucao, reparo, estorno, reembolso, segunda '
                         'via ou contesta um valor.'),
    'consultar': 'O remetente pede apenas informacao, status de entrega ou esclarecimento.',
}
MAPA_2 = {'cancelar': 'encerrar', 'trocar': 'outro', 'rastrear': 'outro',
          'cobranca': 'outro', 'informacao': 'outro'}
CRITERIOS_2 = {
    'encerrar': 'O remetente pede encerrar, cancelar ou desistir de um pedido, servico ou contrato.',
    'outro': 'O remetente pede qualquer outra coisa, ou apenas informacao.',
}


def criterios_12():
    tudo = dict(CRITERIOS)
    tudo.update(DISTRATORES)
    return tudo


# ---------------------------------------------------------------- R3: ruído

ABREVIACOES = {'você': 'vc', 'voce': 'vc', 'vocês': 'vcs', 'que': 'q', 'porque': 'pq',
               'para': 'pra', 'não': 'nao', 'também': 'tb', 'tambem': 'tb',
               'quando': 'qnd', 'muito': 'mt', 'por favor': 'pfv', 'está': 'ta',
               'esta': 'ta', 'estou': 'to', 'mesmo': 'msm', 'agora': 'agr'}

TECLAS_VIZINHAS = {'a': 'sq', 'e': 'wr', 'i': 'ou', 'o': 'ip', 'u': 'yi', 's': 'ad',
                   'r': 'et', 't': 'ry', 'n': 'bm', 'm': 'n', 'c': 'xv', 'd': 'sf',
                   'l': 'k', 'p': 'o', 'q': 'wa', 'v': 'cb', 'g': 'fh'}


def com_erro(texto, taxa, sorteio):
    """Erro de digitação por tecla vizinha, troca de ordem e letra faltando."""
    letras = list(texto)
    alvos = [i for i, letra in enumerate(letras) if letra.isalpha()]
    sorteio.shuffle(alvos)
    for posicao in alvos[:int(len(alvos) * taxa)]:
        letra = letras[posicao].lower()
        dado = sorteio.random()
        if dado < 0.45 and letra in TECLAS_VIZINHAS:
            letras[posicao] = sorteio.choice(TECLAS_VIZINHAS[letra])
        elif dado < 0.75 and posicao + 1 < len(letras):
            letras[posicao], letras[posicao + 1] = letras[posicao + 1], letras[posicao]
        else:
            letras[posicao] = ''
    return ''.join(letras)


def estilo_igor(texto, sorteio):
    """Abreviação, acento caído, pontuação sumida e um erro leve por cima.

    As regras saíram do histórico real: "qeu", "vc", "implenta", "acessessiveis", frases sem
    ponto final e sem maiúscula.
    """
    saida = texto.lower()
    for palavra, curta in ABREVIACOES.items():
        saida = re.sub(rf'\b{re.escape(palavra)}\b', curta, saida)
    saida = ''.join(c for c in unicodedata.normalize('NFD', saida)
                    if unicodedata.category(c) != 'Mn')
    saida = saida.replace(',', '').replace('.', ' ').replace('  ', ' ').strip()
    return com_erro(saida, 0.06, sorteio)


# ---------------------------------------------------------------- execução

def corpus():
    return [json.loads(linha) for linha in
            CORPUS.read_text(encoding='utf-8').splitlines() if linha.strip()]


def condicoes(casos):
    """Monta todas as chamadas de uma vez, para um despacho só."""
    sorteio = random.Random(SEMENTE)
    ordem_original = list(CRITERIOS)
    ordem_inversa = list(reversed(ordem_original))
    ordem_sorteada = ordem_original[:]
    sorteio.shuffle(ordem_sorteada)

    tarefas = []
    for caso in casos:
        base = {'case_id': caso['case_id'], 'family': caso['family'], 'gold': caso['gold']}
        texto = caso['text']

        # R1 — número de opções
        tarefas.append({**base, 'rodada': 'R1', 'condicao': '5-opcoes', 'texto': texto,
                        'criterios': dict(CRITERIOS), 'alvo': caso['gold']})
        tarefas.append({**base, 'rodada': 'R1', 'condicao': '12-opcoes', 'texto': texto,
                        'criterios': criterios_12(), 'alvo': caso['gold']})
        tarefas.append({**base, 'rodada': 'R1', 'condicao': '3-opcoes', 'texto': texto,
                        'criterios': dict(CRITERIOS_3), 'alvo': MAPA_3[caso['gold']]})
        tarefas.append({**base, 'rodada': 'R1', 'condicao': '2-opcoes', 'texto': texto,
                        'criterios': dict(CRITERIOS_2), 'alvo': MAPA_2[caso['gold']]})

        # R2 — ordem das opções (o dicionário preserva a ordem de inserção)
        for nome, ordem in (('ordem-inversa', ordem_inversa), ('ordem-sorteada', ordem_sorteada)):
            tarefas.append({**base, 'rodada': 'R2', 'condicao': nome, 'texto': texto,
                            'criterios': {k: CRITERIOS[k] for k in ordem}, 'alvo': caso['gold']})

        # R3 — ruído tipográfico
        for nome, alterado in (
                ('ruido-leve', com_erro(texto, 0.05, sorteio)),
                ('ruido-pesado', com_erro(texto, 0.15, sorteio)),
                ('estilo-igor', estilo_igor(texto, sorteio))):
            tarefas.append({**base, 'rodada': 'R3', 'condicao': nome, 'texto': alterado,
                            'criterios': dict(CRITERIOS), 'alvo': caso['gold']})
    return tarefas


def executar(tarefa):
    perguntas = {'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                          'criteria': tarefa['criterios']}}
    respostas, detalhe = perguntar(f"Mensagem do cliente:\n{tarefa['texto']}", perguntas,
                                   rodada=tarefa['rodada'])
    alvo = (respostas or {}).get('acao') or {}
    return {**{k: tarefa[k] for k in ('case_id', 'family', 'gold', 'rodada', 'condicao', 'alvo')},
            'escolha': alvo.get('choice'), 'confianca': alvo.get('confidence'),
            'erro': None if respostas else (detalhe or {}).get('erro'),
            'tipo_de_falha': None if respostas else (detalhe or {}).get('tipo')}


def acuracia(linhas):
    validas = [l for l in linhas if l['escolha']]
    acertos = sum(1 for l in validas if l['escolha'] == l['alvo'])
    return {'n': len(validas), 'sem_resposta': len(linhas) - len(validas),
            'acuracia': round(acertos / len(validas), 4) if validas else None,
            'ic95': wilson(acertos, len(validas)),
            'confianca_media': round(sum(l['confianca'] or 0 for l in validas) / len(validas), 4)
            if validas else None}


def pareado(linhas_a, linhas_b):
    """Compara duas condições caso a caso."""
    mapa_b = {l['case_id']: l for l in linhas_b}
    pares, so_a, so_b = [], 0, 0
    for a in linhas_a:
        b = mapa_b.get(a['case_id'])
        if not b or not a['escolha'] or not b['escolha']:
            continue
        ca, cb = a['escolha'] == a['alvo'], b['escolha'] == b['alvo']
        pares.append((1 if ca else 0, 1 if cb else 0))
        so_a += ca and not cb
        so_b += cb and not ca
    return {'pares': len(pares), 'so_a': so_a, 'so_b': so_b,
            'diferenca': round(sum(a - b for a, b in pares) / len(pares), 4) if pares else None,
            'ic95_da_diferenca': bootstrap_diferenca(pares),
            'mcnemar_p': mcnemar_exato(so_a, so_b)}


def main():
    casos = corpus()
    tarefas = condicoes(casos)
    print(f'{len(casos)} casos, {len(tarefas)} chamadas em {len(set(t["condicao"] for t in tarefas))}'
          f' condições + a original já paga')

    linhas = em_paralelo(tarefas, executar, trabalhadores=8, rotulo='R1-R3')

    # A condição de referência (5 opções, ordem original, texto original) vem do E12, já paga.
    e12 = json.loads((RAIZ / 'runs' / 'e12-replicacao' / 'relatorio.json')
                     .read_text(encoding='utf-8'))['casos']
    original = [{'case_id': c['case_id'], 'family': c['family'], 'gold': c['gold'],
                 'alvo': c['gold'], 'escolha': c.get('jev'), 'confianca': c.get('jev_confidence'),
                 'rodada': 'ref', 'condicao': 'original-E12'} for c in e12]

    por_condicao = {'original-E12': original}
    for linha in linhas:
        por_condicao.setdefault(linha['condicao'], []).append(linha)

    resultado = {'casos': len(casos), 'chamadas': len(tarefas),
                 'por_condicao': {nome: acuracia(grupo) for nome, grupo in por_condicao.items()},
                 'contrastes': {}, 'detalhe': linhas}

    for nome in por_condicao:
        if nome != 'original-E12':
            resultado['contrastes'][f'{nome} vs original'] = pareado(por_condicao[nome], original)

    # R2 pede uma medida própria: não é acurácia, é estabilidade da escolha.
    base = {l['case_id']: l['escolha'] for l in original}
    trocas = {}
    for nome in ('ordem-inversa', 'ordem-sorteada'):
        grupo = por_condicao.get(nome, [])
        mudaram = [l['case_id'] for l in grupo
                   if l['escolha'] and base.get(l['case_id'])
                   and l['escolha'] != base[l['case_id']]]
        trocas[nome] = {'mudaram': len(mudaram), 'de': len(grupo),
                        'fracao': round(len(mudaram) / len(grupo), 4) if grupo else None,
                        'casos': mudaram}
    resultado['R2_estabilidade'] = trocas

    # R1 pede saber para onde o erro foi quando havia 12 opções.
    doze = por_condicao.get('12-opcoes', [])
    resultado['R1_distratores_escolhidos'] = Counter(
        l['escolha'] for l in doze if l['escolha'] in DISTRATORES).most_common()

    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')

    print('\n== acurácia por condição')
    for nome, bloco in resultado['por_condicao'].items():
        if bloco['acuracia'] is None:
            continue
        print(f"   {nome:16} {bloco['acuracia']:.4f} IC95 {bloco['ic95']} "
              f"n={bloco['n']:3d} sem resposta={bloco['sem_resposta']} "
              f"conf.média={bloco['confianca_media']}")
    print('\n== contra a condição original (pareado)')
    for nome, bloco in resultado['contrastes'].items():
        print(f"   {nome:34} dif {bloco['diferenca']:+.4f} IC95 {bloco['ic95_da_diferenca']} "
              f"McNemar p={bloco['mcnemar_p']}")
    print('\n== R2: estabilidade da escolha sob permutação das opções')
    for nome, bloco in trocas.items():
        print(f"   {nome:16} mudaram {bloco['mudaram']}/{bloco['de']} = {bloco['fracao']:.1%}")
    print(f"\n== R1: distratores escolhidos na condição de 12 opções: "
          f"{resultado['R1_distratores_escolhidos']}")


if __name__ == '__main__':
    main()
