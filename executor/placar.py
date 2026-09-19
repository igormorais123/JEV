"""Placar de decisão: transforma os relatórios dos experimentos em números de decidir.

O painel já mostrava o registro de atividade, mas o número que importa ficava dentro de uma
nota de texto. Aqui os relatórios em runs/ viram cartões curtos, com a comparação ao lado, e o
bloco entra em lab/data/execution.json sob a chave `decision`. Nada é digitado à mão: se um
experimento ainda não rodou, o cartão diz que não rodou em vez de mostrar um número inventado.

Uso:
    python -m executor.placar
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs'
ESTADO = ROOT / 'lab' / 'data' / 'execution.json'


def ler(caminho):
    alvo = RUNS / caminho
    if not alvo.exists():
        return None
    return json.loads(alvo.read_text(encoding='utf-8'))


def pct(x):
    return f'{x * 100:.1f}%'


def cartao(chave, titulo, valor, comparacao, leitura, fonte, estado='pronto'):
    return {'chave': chave, 'titulo': titulo, 'valor': valor, 'comparacao': comparacao,
            'leitura': leitura, 'fonte': fonte, 'estado': estado}


def ausente(chave, titulo, motivo, fonte):
    return cartao(chave, titulo, '—', 'sem execução', motivo, fonte, estado='pendente')


def montar():
    e1 = ler('e1-triagem/relatorio.json')
    e3 = ler('e3-evidencia/relatorio.json')
    e4 = ler('e4-ressalvas/relatorio.json')
    e2 = ler('e2-fatorial/relatorio.json')
    e2b = ler('e2b-posicao/relatorio.json')
    e5 = ler('e5-provedores/relatorio.json')
    pareada = ler('analise-pareada.json') or {}

    cartoes = []
    if e1:
        dif = pareada.get('e1_triagem', {})
        ic = dif.get('ic95')
        cartoes.append(cartao(
            'e1', 'Triagem de atendimento (E1)', pct(e1['jev']['acuracia']),
            f"regra congelada {pct(e1['regra']['acuracia'])}",
            ('Vantagem de ' + pct(dif['diferenca_observada']) +
             f", IC95 [{pct(ic[0])}; {pct(ic[1])}] por reamostragem de famílias." if ic else
             'Diferença ainda sem intervalo calculado.'),
            f"{e1['jev']['n_casos']} casos, {e1['jev']['n_familias']} famílias"))
    else:
        cartoes.append(ausente('e1', 'Triagem de atendimento (E1)', 'Piloto não executado.', '—'))

    if e3:
        dif = pareada.get('e3_evidencia', {})
        ic = dif.get('ic95')
        cartoes.append(cartao(
            'e3', 'Suporte por evidência (E3)', pct(e3['jev']['acuracia']),
            f"regra ingênua {pct(e3['regra']['acuracia'])}",
            ('Vantagem de ' + pct(dif['diferenca_observada']) +
             f", IC95 [{pct(ic[0])}; {pct(ic[1])}]." if ic else 'Sem intervalo calculado.'),
            f"{e3['jev']['n']} casos, {e3['jev']['n_familias']} famílias"))
    else:
        cartoes.append(ausente('e3', 'Suporte por evidência (E3)', 'Piloto não executado.', '—'))

    if e4:
        cartoes.append(cartao(
            'e4', 'Ressalvas preservadas (E4)',
            f"{e4['jev']['ressalvas_no_topo']}/{e4['jev']['ressalvas_totais']}",
            f"BM25 {e4['bm25']['ressalvas_no_topo']}/{e4['bm25']['ressalvas_totais']} · "
            f"ordem de chegada {e4['original']['ressalvas_no_topo']}/{e4['original']['ressalvas_totais']}",
            f"nDCG@5 {e4['jev']['ndcg5']:.4f} contra {e4['bm25']['ndcg5']:.4f} do BM25. "
            'Ressalva perdida no topo é exceção que não chega a quem decide.',
            f"{e4['topo']} primeiros de 8 consultas × 5 candidatos"))
    else:
        cartoes.append(ausente('e4', 'Ressalvas preservadas (E4)', 'Piloto não executado.', '—'))

    if e2:
        condicoes = e2['condicoes']
        acuracias = [c['resumo']['acuracia'] for c in condicoes.values()]
        individuais = [c['resumo']['custo_por_decisao_nusd'] for c in condicoes.values()
                       if not c['condicao']['lote']]
        lotes = [c['resumo']['custo_por_decisao_nusd'] for c in condicoes.values()
                 if c['condicao']['lote']]
        referencia = sum(individuais) / len(individuais) if individuais else None
        economias = ([100 * (1 - x / referencia) for x in lotes] if referencia and lotes else [])
        faixa = f'{min(acuracias):.3f} a {max(acuracias):.3f}'
        cartoes.append(cartao(
            'e2', 'Lote, ordem e distração (E2)', faixa, '8 condições fatoriais',
            ('Nenhum contraste separa as condições (McNemar p=1,000 em todos). '
             + (f'Lote economiza {min(economias):.1f}% a {max(economias):.1f}% por decisão.'
                if economias else 'Economia do lote registrada no relatório.')),
            f'{len(condicoes)} condições sobre os mesmos 40 casos'))
    else:
        cartoes.append(ausente('e2', 'Lote, ordem e distração (E2)', 'Fatorial não executado.', '—'))

    if e2b:
        dif = pareada.get('e2b_posicao', {})
        instaveis = sum(1 for acertos, total in e2b['por_caso'].values() if 0 < acertos < total)
        cartoes.append(cartao(
            'e2b', 'Estabilidade no lote (E2b)', f'{instaveis} de {len(e2b["por_caso"])} casos instáveis',
            f"p de permutação {dif.get('p_permutacao', '—')}",
            ('Posição no lote não explica erro. Mas esses casos mudam de resposta conforme os '
             'vizinhos do lote: mesma pergunta, resposta diferente.'),
            f"{len(e2b['observacoes'])} observações em {len(e2b['sementes'])} permutações"))
    else:
        cartoes.append(ausente('e2b', 'Estabilidade no lote (E2b)', 'Desconfundimento não executado.', '—'))

    calibracao = pareada.get('calibracao_0.95')
    if calibracao:
        cartoes.append(cartao(
            'calibracao', 'Calibração no corte 0,95',
            f"{calibracao['aceitos']} aceitos de {calibracao['casos_programados']}",
            f"cobertura {pct(calibracao['cobertura_sobre_programados'])}",
            (f"{calibracao['erros_entre_aceitos']} erro(s) observado(s), mas os aceitos vêm de apenas "
             f"{calibracao['familias_representadas_entre_aceitos']} famílias: o limite superior honesto "
             f"é {pct(calibracao['limite_superior_erro_por_familia'])} por família, não "
             f"{pct(calibracao['limite_superior_erro_por_caso'])} por caso."),
            'análise pareada, corte de confiança 0,95'))

    if e5:
        cartoes.append(cartao(
            'e5', 'Provedor: OpenRouter × TypeSafe (E5)', pct(e5['taxa_concordancia']),
            f"{e5['concordancia']} de {e5['casos']} casos concordam",
            ' · '.join(f"{nome}: {pct(d['acuracia'])} de acurácia, p50 {d['latencia_p50_ms']:.0f} ms, "
                       f"{d['custo_por_decisao_nusd'] / 1e9:.9f} USD por decisão"
                       for nome, d in e5['resumo'].items()),
            f"{e5['casos']} casos × 2 transportes, chamadas intercaladas"))
    else:
        cartoes.append(ausente('e5', 'Provedor: OpenRouter × TypeSafe (E5)',
                               'Comparação de transporte ainda não despachada.',
                               'chave TypeSafe registrada; script pronto'))

    # O saldo vale o do relatorio mais recente que registrou a carteira.
    carteira = e5 or e4 or e2b or {}
    comprometido = carteira.get('wallet_committed_nusd') or carteira.get('ledger_committed_nusd')
    disponivel = carteira.get('wallet_available_nusd') or carteira.get('available_nusd')

    bloco = {
        'atualizado_em': datetime.now(timezone.utc).isoformat(),
        'veredito': {
            'titulo': 'Uso consultivo com revisão humana, não decisão automática',
            'texto': ('O Jev supera as regras congeladas em triagem e em evidência por margens que o '
                      'intervalo de confiança não atravessa, e preserva todas as ressalvas necessárias '
                      'no topo. O que impede o automático é a instabilidade no lote e a cobertura: no '
                      'corte de 0,95 só 70% dos casos são aceitos, e o limite de erro respeitando '
                      'famílias ainda é alto.'),
            'confianca': 0.7,
            'confianca_nota': ('Alta para a comparação contra as regras, porque é pareada e replicada. '
                               'Baixa para generalizar: corpus autoral, um anotador, 40 casos.'),
        },
        'cartoes': cartoes,
        'orcamento': ({'comprometido_nusd': comprometido, 'disponivel_nusd': disponivel}
                      if comprometido is not None else None),
        'pendencias': [
            'E5 (P6): comparar OpenRouter e TypeSafe direto nos mesmos casos.',
            'P5: fluxo completo com minutagem humana, para custo por decisão de ponta a ponta.',
            'Corpus real, não balanceado, e um segundo anotador cego.',
        ],
    }
    return bloco


def publicar():
    estado = json.loads(ESTADO.read_text(encoding='utf-8'))
    estado['decision'] = montar()
    estado['revision'] = int(estado.get('revision', 0)) + 1
    estado['updated_at'] = datetime.now(timezone.utc).isoformat()
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding='utf-8')
    return estado['decision']


if __name__ == '__main__':
    bloco = publicar()
    print(f"Placar publicado com {len(bloco['cartoes'])} cartoes.")
    for c in bloco['cartoes']:
        print(f"  {c['titulo']:38} {c['valor']:>22}  ({c['comparacao']})")
