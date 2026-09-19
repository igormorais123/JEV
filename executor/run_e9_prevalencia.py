"""E9: o que acontece com o desempenho quando a distribuição de classes não é a do corpus.

Os corpora do estudo são quase balanceados: cada classe aparece 7 a 9 vezes em 40. Um canal
de atendimento real não é assim — costuma ter muito rastreio e pouco cancelamento. A acurácia
observada num corpus balanceado não se transporta para uma distribuição diferente.

Isto não exige chamadas novas. A matriz de confusão dá a acurácia por classe; a acurácia
esperada sob outra prevalência é a média dessas taxas ponderada pela nova distribuição.
O que a reponderação NÃO corrige: casos de uma classe num canal real podem ser mais difíceis
do que os casos daquela classe no corpus. A reponderação assume que a dificuldade dentro da
classe é a mesma, e essa suposição é grande.

Junto vai a conta de operação que o plano pedia em P5: custo e tempo por decisão sob políticas
de cobertura diferentes, com o custo humano da revisão entrando como parâmetro declarado.

Uso:
    python -m executor.run_e9_prevalencia
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'e9-prevalencia'

# Cenarios de prevalencia. Nenhum e medido: sao hipoteses declaradas, para mostrar a
# SENSIBILIDADE do resultado a distribuicao, nao para afirmar qual e a distribuicao real.
CENARIOS = {
    'corpus-do-estudo': None,  # preenchido com a distribuicao observada
    'canal-de-entrega': {'rastrear': 0.55, 'informacao': 0.20, 'cobranca': 0.12,
                         'trocar': 0.08, 'cancelar': 0.05},
    'canal-financeiro': {'cobranca': 0.50, 'informacao': 0.22, 'cancelar': 0.13,
                         'rastrear': 0.10, 'trocar': 0.05},
    'pos-venda-de-produto': {'trocar': 0.40, 'rastrear': 0.22, 'informacao': 0.18,
                             'cobranca': 0.12, 'cancelar': 0.08},
}

# Parametros de operacao declarados, nao medidos. Trocar aqui muda toda a conta de P5.
MINUTOS_REVISAO_HUMANA = 2.0
CUSTO_HORA_HUMANA_USD = 12.0


def carregar():
    casos = []
    for relatorio in ('e1-triagem', 'e7-confirmacao'):
        alvo = ROOT / 'runs' / relatorio / 'relatorio.json'
        if alvo.exists():
            dados = json.loads(alvo.read_text(encoding='utf-8'))
            for c in dados['casos']:
                casos.append({'case_id': c['case_id'], 'gold': c['gold'], 'jev': c.get('jev'),
                              'confidence': c.get('jev_confidence'),
                              'custo_nusd': c.get('jev_cost_nusd'),
                              'latency_ms': c.get('latency_ms'), 'origem': relatorio})
    return casos


def acuracia_por_classe(casos):
    por_classe = defaultdict(lambda: [0, 0])
    for c in casos:
        por_classe[c['gold']][1] += 1
        if c['jev'] == c['gold']:
            por_classe[c['gold']][0] += 1
    saida = {}
    for classe, (a, n) in sorted(por_classe.items()):
        item = {'acertos': a, 'casos': n, 'taxa': round(a / n, 4)}
        if a == n:
            # Uma classe sem erro nao tem risco zero: com 16 casos o limite ainda e alto.
            item['limite_superior_erro'] = round(1 - 0.05 ** (1 / n), 4)
        saida[classe] = item
    return saida


def aceitacao(casos, corte):
    """Politica: aceitar automaticamente acima do corte, mandar o resto para revisao humana."""
    aceitos = [c for c in casos if c['confidence'] is not None and c['confidence'] >= corte]
    revisados = [c for c in casos if c not in aceitos]
    erros_aceitos = sum(1 for c in aceitos if c['jev'] != c['gold'])
    custo_api = sum(c['custo_nusd'] or 0 for c in casos) / 1e9
    custo_humano = len(revisados) * (MINUTOS_REVISAO_HUMANA / 60) * CUSTO_HORA_HUMANA_USD
    return {
        'corte': corte, 'casos': len(casos), 'aceitos': len(aceitos),
        'cobertura': round(len(aceitos) / len(casos), 4) if casos else None,
        'erros_entre_aceitos': erros_aceitos,
        'enviados_a_revisao': len(revisados),
        'custo_api_usd': round(custo_api, 6),
        'custo_humano_usd': round(custo_humano, 4),
        'custo_total_usd': round(custo_api + custo_humano, 4),
        'custo_por_decisao_usd': round((custo_api + custo_humano) / len(casos), 6) if casos else None,
    }


def limite_superior_zero_erro(n, confianca=0.95):
    """Clopper-Pearson unilateral para zero erro em n. 16/16 nao e taxa de erro zero."""
    return round(1 - (1 - confianca) ** (1 / n), 4) if n else 1.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    casos = [c for c in carregar() if c['jev']]
    # A particao importa. Juntar piloto e confirmacao numa conta so apaga justamente a
    # separacao que o E7 existe para preservar, entao reportamos as tres visoes.
    por_particao = {
        'piloto (desenvolvimento)': [c for c in casos if c['origem'] == 'e1-triagem'],
        'confirmacao (teste)': [c for c in casos if c['origem'] == 'e7-confirmacao'],
        'uniao': casos,
    }
    taxas = acuracia_por_classe(casos)
    observada = {classe: d['casos'] / len(casos) for classe, d in taxas.items()}
    CENARIOS['corpus-do-estudo'] = {k: round(v, 4) for k, v in observada.items()}

    projecoes = {}
    for nome, distribuicao in CENARIOS.items():
        soma = sum(distribuicao.values())
        esperada = sum(distribuicao.get(classe, 0) / soma * d['taxa'] for classe, d in taxas.items())
        # A classe com menos casos manda no erro da projecao: com 7 casos, a taxa daquela
        # classe tem incerteza enorme, e a projecao herda essa incerteza inteira.
        menor = min(taxas.items(), key=lambda kv: kv[1]['casos'])
        projecoes[nome] = {
            'distribuicao': distribuicao,
            'acuracia_esperada': round(esperada, 4),
            'classe_dominante': max(distribuicao, key=distribuicao.get),
            'classe_menos_observada': {'classe': menor[0], 'casos_no_estudo': menor[1]['casos'],
                                       'taxa': menor[1]['taxa']},
        }

    politicas = [aceitacao(casos, corte) for corte in (0.0, 0.90, 0.95, 0.99, 1.01)]
    base = next(p for p in politicas if p['corte'] == 1.01)  # tudo revisado por humano
    for p in politicas:
        p['economia_versus_revisao_total_usd'] = round(base['custo_total_usd'] - p['custo_total_usd'], 4)
        p['economia_percentual'] = (round(100 * (1 - p['custo_total_usd'] / base['custo_total_usd']), 1)
                                    if base['custo_total_usd'] else None)

    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(),
        'casos_usados': len(casos),
        'origem': 'E1 piloto + E7 confirmacao',
        'aviso_particao': ('A uniao mistura desenvolvimento e teste. A leitura que vale para decidir '
                           'e a da particao de confirmacao; a uniao esta aqui so por ter mais casos.'),
        'por_particao': {nome: {'casos': len(grupo),
                                'acuracia_por_classe': acuracia_por_classe(grupo),
                                'politicas': [aceitacao(grupo, corte)
                                              for corte in (0.90, 0.95, 0.99)]}
                         for nome, grupo in por_particao.items()},
        'acuracia_por_classe': taxas,
        'projecoes_por_prevalencia': projecoes,
        'aviso_projecao': ('A reponderacao assume que a dificuldade DENTRO de cada classe e a '
                           'mesma do corpus. Um canal real pode ter casos daquela classe muito '
                           'mais dificeis. A projecao mostra sensibilidade, nao previsao.'),
        'parametros_de_operacao': {'minutos_revisao_humana': MINUTOS_REVISAO_HUMANA,
                                   'custo_hora_humana_usd': CUSTO_HORA_HUMANA_USD,
                                   'natureza': 'declarados, nao medidos; nenhum cronometro foi usado'},
        'politicas_de_aceitacao': politicas,
    }
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')

    print(f'Acuracia por classe ({len(casos)} casos dos dois corpora):')
    for classe, d in taxas.items():
        print(f"  {classe:12} {d['acertos']:2}/{d['casos']:2} = {d['taxa']}")
    print('\nAcuracia esperada por cenario de prevalencia:')
    for nome, p in projecoes.items():
        print(f"  {nome:22} {p['acuracia_esperada']}  (dominante: {p['classe_dominante']})")
    print(f"\nPolitica de aceitacao ({MINUTOS_REVISAO_HUMANA} min por revisao, "
          f"US$ {CUSTO_HORA_HUMANA_USD}/h):")
    print(f"  {'corte':>6} {'cobertura':>10} {'erros':>6} {'revisao':>8} {'US$/decisao':>12} {'economia':>9}")
    for p in politicas:
        rotulo = 'todos' if p['corte'] == 0.0 else ('nenhum' if p['corte'] == 1.01 else f"{p['corte']}")
        print(f"  {rotulo:>6} {p['cobertura']:>10} {p['erros_entre_aceitos']:>6} "
              f"{p['enviados_a_revisao']:>8} {p['custo_por_decisao_usd']:>12} "
              f"{str(p['economia_percentual']) + '%':>9}")


if __name__ == '__main__':
    main()
