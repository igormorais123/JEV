"""R50 — o checklist de contrato: uma chamada com oito perguntas contra oito chamadas de uma.

De onde vem. O vídeo "Coloquei o GPT 6 Astra e o Jev no mesmo app" (canal Hora de Codar,
2026-09-21, https://youtu.be/NPog8eJRojM) monta um auditor de contrato com oito perguntas de
risco, manda **uma pergunta por chamada, em sequência** (3,8 s no total, 894 ms cada) e afirma
que esse é o jeito certo. A R33 e a R49 medem o contrário: várias perguntas no mesmo payload
custam a mesma latência de uma. Esta rodada mede a aplicação inteira, que passa a existir em
`integracao/camadas/checklist.py`, com gabarito por construção.

Corpus: 36 contratos montados por sorteio. Cada um dos oito pontos entra numa de três formas,
escritas antes de rodar: cláusula arriscada, cláusula segura, ou ausente (o gabarito então é
`nao-consta`). Cláusulas neutras de recheio vão junto. Viés declarado: quem escreveu as
cláusulas escreveu também as descrições das opções.

H50a  Numa chamada só, o acerto por item é de 90% ou mais (288 julgamentos).
H50b  A resposta de cada item na chamada única é igual à da chamada isolada em 95% ou mais, e a
      chamada única leva um terço ou menos do tempo das oito em sequência.
H50c  Entre os itens que saem verdes ou vermelhos (probabilidade de 0,90 ou mais) o acerto é de
      97% ou mais; nenhum ponto arriscado sai verde.
H50d  Ponto ausente sai `nao-consta` em 85% ou mais.

    python laboratorio/r50_checklist_de_contrato.py --rodar
"""

import argparse
import random
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / 'integracao'))

from camadas import checklist  # noqa: E402
from laboratorio.nucleo import em_paralelo  # noqa: E402
from laboratorio.r31_r37_segunda_leva import gravar, medidas, perguntar, taxa  # noqa: E402

SEMENTE = 20260924
CLAUSULAS = {
    'exclusividade': {
        'exclusividade-ampla': 'Durante a vigencia e por doze meses apos o termino, o CONTRATADO nao podera prestar servicos, direta ou indiretamente, a nenhuma outra empresa do mesmo segmento da CONTRATANTE.',
        'sem-exclusividade': 'O presente contrato nao gera exclusividade, podendo o CONTRATADO atender livremente outros clientes, inclusive concorrentes da CONTRATANTE.'},
    'imagem': {
        'cessao-ilimitada': 'O CONTRATADO cede a CONTRATANTE, em carater definitivo, irrevogavel e por prazo indeterminado, o direito de usar sua imagem, voz e todo o conteudo produzido, em qualquer midia e para qualquer finalidade.',
        'cessao-limitada': 'A CONTRATANTE podera utilizar a imagem do CONTRATADO e o conteudo produzido exclusivamente na campanha objeto deste contrato, pelo prazo de seis meses contados da primeira publicacao.'},
    'multa': {
        'multa-so-do-contratado': 'Caso o CONTRATADO rescinda o contrato antes do prazo, pagara multa equivalente a 50% do valor total. A CONTRATANTE podera rescindir a qualquer tempo, sem onus, mediante aviso de cinco dias.',
        'multa-equilibrada': 'A parte que rescindir o contrato sem justa causa antes do prazo pagara a outra multa de 10% do valor remanescente, regra que vale igualmente para CONTRATANTE e CONTRATADO.'},
    'pagamento': {
        'prazo-longo': 'O pagamento sera efetuado em ate 120 dias corridos apos a emissao da nota fiscal, condicionada a aprovacao final de todas as entregas.',
        'prazo-normal': 'O pagamento sera efetuado em ate 15 dias apos a emissao da nota fiscal de cada entrega.'},
    'renovacao': {
        'renovacao-automatica': 'Findo o prazo, o contrato sera prorrogado automaticamente por periodos iguais e sucessivos, salvo se uma das partes manifestar oposicao por escrito com 90 dias de antecedencia.',
        'renovacao-por-acordo': 'O contrato se encerra ao final do prazo, e qualquer prorrogacao dependera de termo aditivo assinado pelas duas partes.'},
    'foro': {
        'foro-do-contratante': 'Fica eleito o foro da comarca da sede da CONTRATANTE, com renuncia a qualquer outro, por mais privilegiado que seja.',
        'foro-do-contratado': 'Fica eleito o foro da comarca de domicilio do CONTRATADO para dirimir as questoes oriundas deste contrato.',
        'arbitragem': 'As controversias decorrentes deste contrato serao resolvidas de forma definitiva por arbitragem, perante camara arbitral indicada pela CONTRATANTE.'},
    'aprovacao': {
        'aprovacao-sem-limite': 'As entregas serao submetidas a CONTRATANTE, que podera solicitar quantas alteracoes julgar necessarias ate sua plena satisfacao, sem custo adicional.',
        'aprovacao-com-limite': 'Cada entrega admite ate duas rodadas de ajustes. Nao havendo manifestacao da CONTRATANTE em cinco dias uteis, a entrega sera considerada aprovada.'},
    'responsabilidade': {
        'responsabilidade-ilimitada': 'O CONTRATADO respondera integralmente por todo e qualquer dano, direto ou indireto, inclusive lucros cessantes, causado a CONTRATANTE ou a terceiros.',
        'responsabilidade-limitada': 'A responsabilidade do CONTRATADO por danos fica limitada ao valor total efetivamente pago neste contrato, excluidos danos indiretos e lucros cessantes.'},
}
RECHEIO = [
    'O objeto deste contrato e a producao de tres videos publicitarios para os canais digitais da CONTRATANTE.',
    'O prazo de vigencia e de seis meses, contados da assinatura.',
    'As partes se obrigam a manter sigilo sobre as informacoes comerciais a que tiverem acesso.',
    'O valor total dos servicos e de R$ 24.000,00, dividido conforme o cronograma de entregas.',
    'Este contrato nao estabelece vinculo empregaticio entre as partes.',
    'Qualquer alteracao deste instrumento so tera validade se feita por escrito.',
]


def montar_contratos(quantos=36):
    sorteio = random.Random(SEMENTE)
    contratos = []
    for n in range(quantos):
        gold, clausulas = {}, list(RECHEIO)
        for item, formas in CLAUSULAS.items():
            forma = sorteio.choice(list(formas) + ['nao-consta'])
            gold[item] = forma
            if forma != 'nao-consta':
                clausulas.append(formas[forma])
        sorteio.shuffle(clausulas)
        texto = 'CONTRATO DE PRESTACAO DE SERVICOS\n\n' + '\n\n'.join(f'CLAUSULA {i}. {c}' for i, c in enumerate(clausulas, 1))
        contratos.append({'i': n, 'texto': texto, 'gold': gold})
    return contratos


def main():
    analise = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    analise.add_argument('--rodar', action='store_true')
    if not analise.parse_args().rodar:
        return
    lista = checklist.carregar_lista('contrato-prestacao-de-servicos')
    todas = checklist.perguntas_da(lista)
    itens = {item['id']: item for item in lista['itens']}

    def uma(t):
        c = t['contrato']
        perguntas = todas if t['arranjo'] == 'uma-chamada' else {t['item']: todas[t['item']]}
        respostas, detalhe = perguntar(f"DOCUMENTO:\n{c['texto']}", perguntas, 'R50')
        vigia = ((respostas or {}).get('_sentinela') or {}).get('choice')
        lidos = {}
        for nome in perguntas:
            if nome != '_sentinela':
                resposta, p = checklist.ler_item(itens[nome], (respostas or {}).get(nome))
                lidos[nome] = {'resposta': resposta, 'p': p, 'gold': c['gold'][nome],
                               'cor': checklist.semaforo(itens[nome], resposta, p, vigia not in (None, 'nao-tenta'))}
        return {'i': c['i'], 'arranjo': t['arranjo'], 'item': t.get('item'), 'sentinela': vigia, 'lidos': lidos, **medidas(detalhe)}

    def analisar(linhas):
        unica = {l['i']: l for l in linhas if l['arranjo'] == 'uma-chamada'}
        isolada = {(l['i'], l['item']): l for l in linhas if l['arranjo'] == 'item-por-item'}
        julgados = [(i, nome, v) for i, l in unica.items() for nome, v in l['lidos'].items() if v['resposta']]
        decididos = [v for _, _, v in julgados if v['cor'] in ('verde', 'vermelho', 'não consta')]
        ausentes = [v for _, _, v in julgados if v['gold'] == 'nao-consta']
        comuns = [(i, nome, v) for i, nome, v in julgados
                  if ((isolada.get((i, nome)) or {}).get('lidos') or {}).get(nome, {}).get('resposta')]
        por_item = {}
        for _, nome, v in julgados:
            por_item.setdefault(nome, []).append(v['resposta'] == v['gold'])
        isolados = [l['lidos'][l['item']] for l in isolada.values() if l['lidos'][l['item']]['resposta']]
        em_sequencia = [sum(isolada[(i, nome)]['latencia_ms'] or 0 for nome in itens if (i, nome) in isolada) for i in unica]
        return {'contratos': len(unica),
                'uma_chamada': taxa(sum(v['resposta'] == v['gold'] for _, _, v in julgados), len(julgados)),
                'item_por_item': taxa(sum(v['resposta'] == v['gold'] for v in isolados), len(isolados)),
                'por_item': {nome: f'{sum(v)}/{len(v)}' for nome, v in por_item.items()},
                'igual_a_chamada_isolada': taxa(sum(v['resposta'] == isolada[(i, nome)]['lidos'][nome]['resposta'] for i, nome, v in comuns), len(comuns)),
                'decididos_sem_gente': {'cobertura': round(len(decididos) / len(julgados), 4),
                                        **taxa(sum(v['resposta'] == v['gold'] for v in decididos), len(decididos))},
                'arriscado_que_saiu_verde': sum(v['cor'] == 'verde' and v['gold'] in itens[nome]['risco'] for _, nome, v in julgados),
                'seguro_que_saiu_vermelho': sum(v['cor'] == 'vermelho' and v['gold'] not in itens[nome]['risco'] for _, nome, v in julgados),
                'ausente_reconhecido': taxa(sum(v['resposta'] == 'nao-consta' for v in ausentes), len(ausentes)),
                'sentinela_calado': taxa(sum(l['sentinela'] == 'nao-tenta' for l in unica.values()), len(unica)),
                'latencia_mediana_uma_chamada_ms': statistics.median(l['latencia_ms'] for l in unica.values() if l['latencia_ms']),
                'latencia_mediana_oito_em_sequencia_ms': statistics.median(em_sequencia),
                'custo_medio_uma_chamada_usd': sum(l['custo_usd'] for l in unica.values()) / len(unica),
                'custo_medio_oito_chamadas_usd': sum(l['custo_usd'] for l in isolada.values()) / len(unica)}

    contratos = montar_contratos()
    tarefas = [{'contrato': c, 'arranjo': 'uma-chamada'} for c in contratos]
    tarefas += [{'contrato': c, 'arranjo': 'item-por-item', 'item': nome} for c in contratos for nome in itens]
    gravar('r50-checklist-de-contrato', em_paralelo(tarefas, uma, trabalhadores=8, rotulo='R50'), analisar)


if __name__ == '__main__':
    main()
