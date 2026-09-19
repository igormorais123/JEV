"""Publica no painel as decisões caso a caso de E2, E2b e E5.

Até agora esses experimentos entravam no painel como nota de texto: o placar mostrava o
resultado, mas a aba de métricas ficava vazia porque não havia decisão nenhuma para contar.
Aqui os relatórios em runs/ viram tentativas e decisões no formato que o painel valida.

E4 fica de fora de propósito: é ranqueamento, medido por nDCG@5 e por ressalva preservada,
e os relatórios não guardam a tentativa de cada documento. Forçá-lo no formato de
classificação produziria uma matriz de confusão que não corresponde ao que foi medido.

Uso:
    python -m executor.publicar_experimentos
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from .run_e1_triagem import carregar

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs'
ESTADO = ROOT / 'lab' / 'data' / 'execution.json'


def ler(caminho):
    alvo = RUNS / caminho
    return json.loads(alvo.read_text(encoding='utf-8')) if alvo.exists() else None


def gabarito():
    return {c['case_id']: (c['gold'], c['family']) for c in carregar()}


def tentativa(attempt_id, status, latency_ms, cost_nusd):
    return {'id': attempt_id, 'status': 'success' if status == 'success' else 'error',
            'latency_ms': latency_ms, 'input_tokens': None, 'output_tokens': None,
            'cost_usd': (cost_nusd / 1e9) if cost_nusd is not None else None,
            'reserved_usd': 0, 'cache_hit': False}


def decisao(did, case_id, attempt_id, split, expected, predicted, confidence, question_id, group_id):
    return {'id': did, 'case_id': case_id, 'attempt_id': attempt_id, 'task': 'triage',
            'split': split, 'expected': expected, 'predicted': predicted,
            'correct': None if predicted is None else predicted == expected,
            'confidence': confidence, 'question_id': question_id, 'group_id': group_id}


def e2_run(rel, gold, agora):
    tentativas, decisoes = {}, []
    for condicao, saidas in rel['saidas'].items():
        for case_id, s in saidas.items():
            aid = s['attempt_id']
            if aid not in tentativas:
                # Numa chamada de lote a latência é da chamada inteira; o custo já vem rateado.
                tentativas[aid] = tentativa(aid, s['status'], s['latency_ms'], None)
            esperado, familia = gold[case_id]
            decisoes.append(decisao(f'{condicao}:{case_id}', case_id, aid, 'diagnostic',
                                    esperado, s.get('pred'), s.get('confidence'),
                                    condicao, familia))
    # O custo por condição está no resumo; distribuímos por tentativa para não perder o total.
    total = sum(d['resumo']['custo_total_nusd'] for d in rel['condicoes'].values())
    if tentativas:
        cota = total / len(tentativas) / 1e9
        for t in tentativas.values():
            t['cost_usd'] = cota
    return {
        'id': 'e2-fatorial-lote-ordem-distracao', 'system_id': 'S01', 'phase': 'pilot',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': rel['modelo'],
        'dataset': ('os mesmos 40 casos do E1 em 8 condições (2 lote × 2 ordem × 2 distração), '
                    f"ordem de execução embaralhada com semente {rel['seed']}"),
        'notes': ('Acurácia entre 0,925 e 0,950 nas 8 condições; McNemar p=1,000 em todos os '
                  'contrastes. O lote de 8 reduz o custo por decisão sem perda detectável. '
                  'Partição diagnóstica: os mesmos casos aparecem 8 vezes, uma por condição, '
                  'então as decisões NÃO são independentes.'),
        'attempts': list(tentativas.values()), 'decisions': decisoes,
    }


def e2b_run(rel, gold, agora):
    tentativas, decisoes = {}, []
    for o in rel['observacoes']:
        aid = o['attempt_id']
        if aid not in tentativas:
            tentativas[aid] = tentativa(aid, 'success', o['latency_chamada_ms'], None)
        decisoes.append(decisao(f"s{o['semente']}-l{o['lote']}-p{o['posicao']}:{o['case_id']}",
                                o['case_id'], aid, 'diagnostic', o['gold'], o.get('pred'),
                                o.get('confidence'), f"posicao-{o['posicao']}", o['family']))
    custo = sum(o['cost_nusd'] for o in rel['observacoes'])
    if tentativas:
        cota = custo / len(tentativas) / 1e9
        for t in tentativas.values():
            t['cost_usd'] = cota
    instaveis = [c for c, (acertos, total) in rel['por_caso'].items() if 0 < acertos < total]
    return {
        'id': 'e2b-posicao-desconfundida', 'system_id': 'S01', 'phase': 'pilot',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': 'typesafe/jev-1.13',
        'dataset': (f"os mesmos 40 casos em {len(rel['sementes'])} permutações "
                    f"(sementes {rel['sementes'][0]} a {rel['sementes'][-1]}), lotes de "
                    f"{rel['tamanho_lote']}, {len(rel['observacoes'])} observações"),
        'notes': ('Embaralhando a ordem, o efeito de posição desaparece (permutação p=0,403): o que o '
                  'E2 leu como "posições 4 e 8 são piores" era confusão entre posição e caso. '
                  f"O achado que sobra é outro: {len(instaveis)} casos ({', '.join(instaveis)}) mudam "
                  'de resposta conforme os vizinhos do lote.'),
        'attempts': list(tentativas.values()), 'decisions': decisoes,
    }


def e5_run(rel, gold, agora):
    tentativas, decisoes = [], []
    for r in rel['resultados']:
        for braco in ('openrouter', 'typesafe'):
            d = r[braco]
            tentativas.append(tentativa(d['attempt_id'], d['status'], d['latency_ms'], d['cost_nusd']))
            decisoes.append(decisao(f"{braco}:{r['case_id']}", r['case_id'], d['attempt_id'],
                                    'pilot', r['gold'], d.get('pred'), d.get('confidence'),
                                    braco, r['family']))
    return {
        'id': 'e5-provedores-openrouter-typesafe', 'system_id': 'S01', 'phase': 'pilot',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter e typesafe', 'model': 'typesafe/jev-1.13 e jev-1.13.0',
        'dataset': f"os mesmos {rel['casos']} casos do E1, chamadas intercaladas entre os dois transportes",
        'notes': ('Os dois transportes concordam em 40 de 40 casos, com a mesma acurácia de 0,925. '
                  'O endpoint direto é cerca de duas vezes mais lento e mais caro por decisão, porque '
                  'cobra tokens de saída que o OpenRouter não cobra. Cada caso aparece duas vezes, '
                  'uma por transporte: as decisões são pareadas, não independentes.'),
        'attempts': tentativas, 'decisions': decisoes,
    }


def e6_run(rel, gold, agora):
    tentativas, decisoes = [], []
    for o in rel['observacoes']:
        tentativas.append(tentativa(o['attempt_id'], o['status'], o['latency_ms'], o['cost_nusd']))
        decisoes.append(decisao(f"r{o['repeticao']}:{o['case_id']}", o['case_id'], o['attempt_id'],
                                'diagnostic', o['gold'], o.get('pred'), o.get('confidence'),
                                f"repeticao-{o['repeticao']}", o['family']))
    return {
        'id': 'e6-repetibilidade-individual', 'system_id': 'S01', 'phase': 'pilot',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': rel['modelo'],
        'dataset': (f"os mesmos {rel['casos']} casos do E1, cada um sozinho numa chamada, "
                    f"repetidos {rel['repeticoes']} vezes"),
        'notes': ('Separa instabilidade do modelo de efeito do lote. Mesmo isolado, '
                  f"{rel['n_instaveis']} caso(s) mudam de resposta entre repeticoes identicas: "
                  f"{', '.join(rel['casos_instaveis'])}. A acuracia por rodada varia de "
                  f"{min(rel['acuracia_por_rodada'].values())} a {max(rel['acuracia_por_rodada'].values())}; "
                  f"o voto majoritario de {rel['repeticoes']} chega a {rel['acuracia_voto_majoritario']}, "
                  f"a {rel['repeticoes']}x o custo. Os mesmos casos se repetem: decisoes nao independentes."),
        'attempts': tentativas, 'decisions': decisoes,
    }


def e7_run(rel, gold, agora):
    tentativas, decisoes = [], []
    for c in rel['casos']:
        tentativas.append(tentativa(c['jev_attempt_id'], c['jev_status'], c['latency_ms'],
                                    c['jev_cost_nusd']))
        decisoes.append(decisao(f"jev:{c['case_id']}", c['case_id'], c['jev_attempt_id'],
                                'test', c['gold'], c.get('jev'), c.get('jev_confidence'),
                                'confirmacao', c['family']))
    par = rel['pareada']
    return {
        'id': 'e7-confirmacao-triagem', 'system_id': 'S01', 'phase': 'confirmation',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': rel['modelo'],
        'dataset': (f"{rel['jev']['casos_programados']} casos novos em {rel['jev']['n_familias']} "
                    'familias escritas para armadilhas que o piloto nao cobria; gabarito autoral, '
                    'um anotador'),
        'notes': (f"Conjunto de confirmacao pre-registrado. Jev {rel['jev']['acertos']}/"
                  f"{rel['jev']['casos_programados']} contra {rel['regra']['acertos']}/"
                  f"{rel['regra']['casos_programados']} da regra congelada; diferenca pareada "
                  f"{par['diferenca_observada']:+.3f}, IC95 [{par['ic95'][0]:.3f}; {par['ic95'][1]:.3f}]. "
                  f"{rel['veredito']} Partição de teste: cada caso aparece uma vez so."),
        'attempts': tentativas, 'decisions': decisoes,
    }


def e10_run(rel, gold, agora):
    """O braço do LLM econômico. As tentativas são do comparador, não do Jev.

    O Jev não foi reexecutado aqui: as respostas dele vêm do E7, os mesmos 40 casos. Publicar
    tentativas do Jev neste run contaria a mesma chamada duas vezes no custo do painel.
    """
    tentativas, decisoes = [], []
    for c in rel['casos']:
        status = 'success' if c.get('llm') else 'invalid_response'
        tentativas.append(tentativa(c['llm_attempt_id'], status, c['llm_latency_ms'],
                                    c['llm_cost_nusd']))
        decisoes.append(decisao(f"llm:{c['case_id']}", c['case_id'], c['llm_attempt_id'],
                                'test', c['gold'], c.get('llm'), c.get('llm_confidence'),
                                'comparador-economico', c['family']))
    par = rel['pareada']
    return {
        'id': 'e10-comparador-llm-economico', 'system_id': 'S01', 'phase': 'confirmation',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': rel['modelo'],
        'dataset': (f"os mesmos {rel['llm']['casos_programados']} casos da particao de "
                    'confirmacao, com as instrucoes e criterios congelados do E1, sem ajuste '
                    'de prompt'),
        'notes': ('O braco que faltava desde o plano: ate aqui o unico comparador era uma regra '
                  f"congelada escrita pelo avaliador. {rel['modelo']} acerta "
                  f"{rel['llm']['acertos']}/{rel['llm']['casos_programados']} contra "
                  f"{rel['jev']['acertos']}/{rel['jev']['casos_programados']} do Jev; diferenca "
                  f"pareada {par['diferenca_observada']:+.4f}, IC95 [{par['ic95'][0]:.4f}; "
                  f"{par['ic95'][1]:.4f}], que contem zero. So o Jev acerta em "
                  f"{len(rel['so_jev_acerta'])} casos, so o comparador em "
                  f"{len(rel['so_llm_acerta'])}: McNemar exato p = 0,25. Pela regra congelada no "
                  'pre-registro, isto e ausencia de evidencia de vantagem, e o veredito do '
                  f"painel mudou por causa disto. {len(rel['respostas_invalidas'])} respostas "
                  'fora do contrato, contadas como erro e nunca reexecutadas.'),
        'attempts': tentativas, 'decisions': decisoes,
    }


def e10b_run(rel, gold, agora):
    """O braco secundario do comparador, nas 10 familias do piloto."""
    tentativas, decisoes = [], []
    for c in rel['casos']:
        status = 'success' if c.get('llm') else 'invalid_response'
        tentativas.append(tentativa(c['llm_attempt_id'], status, c['llm_latency_ms'],
                                    c['llm_cost_nusd']))
        decisoes.append(decisao(f"llm:{c['case_id']}", c['case_id'], c['llm_attempt_id'],
                                'diagnostic', c['gold'], c.get('llm'), c.get('llm_confidence'),
                                'comparador-economico-piloto', c['family']))
    amp, pil = rel['pareada_80_casos'], rel['pareada_piloto']
    return {
        'id': 'e10b-comparador-no-piloto', 'system_id': 'S01', 'phase': 'pilot',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': rel['modelo'],
        'dataset': 'os 40 casos do piloto, com as mesmas instrucoes congeladas do E1',
        'notes': ('Analise SECUNDARIA sob emenda declarada antes da execucao, para dobrar o '
                  'poder depois de o resultado primario ter tocado zero. No piloto a vantagem '
                  f"do Jev e {pil['diferenca_observada']:+.4f}, IC95 [{pil['ic95'][0]:.4f}; "
                  f"{pil['ic95'][1]:.4f}], e separa de zero; nas {amp['n_familias']} familias "
                  f"das duas particoes e {amp['diferenca_observada']:+.4f}, IC95 "
                  f"[{amp['ic95'][0]:.4f}; {amp['ic95'][1]:.4f}], e tambem separa. A particao "
                  'que existe para decidir continua sendo a de confirmacao, que nao separa: o '
                  'veredito do painel passou a dizer que a evidencia esta dividida.'),
        'attempts': tentativas, 'decisions': decisoes,
    }


def e11_run(rel, gold, agora):
    """O desempate: DOIS bracos na mesma lista, entao duas tentativas e duas decisoes por caso."""
    tentativas, decisoes = [], []
    for c in rel['casos']:
        tentativas.append(tentativa(c['jev_attempt_id'], c['jev_status'], c['jev_latency_ms'],
                                    c['jev_cost_nusd']))
        decisoes.append(decisao(f"jev:{c['case_id']}", c['case_id'], c['jev_attempt_id'],
                                'test', c['gold'], c.get('jev'), c.get('jev_confidence'),
                                'desempate-jev', c['family']))
        tentativas.append(tentativa(c['llm_attempt_id'],
                                    'success' if c.get('llm') else 'invalid_response',
                                    c['llm_latency_ms'], c['llm_cost_nusd']))
        decisoes.append(decisao(f"llm:{c['case_id']}", c['case_id'], c['llm_attempt_id'],
                                'test', c['gold'], c.get('llm'), c.get('llm_confidence'),
                                'desempate-comparador', c['family']))
    pg = rel.get('por_gabarito') or {}
    autor = (pg.get('autor') or {}).get('pareada') or rel['pareada']
    outro = (pg.get('anotador local') or {}).get('pareada')
    nota = ('Corpus novo de 60 casos em 20 familias, declaradas no pre-registro antes de o '
            'primeiro caso existir, para resolver o poder baixo e o pos-hoc que sobraram do E10 '
            f"e do E10b. Sob o gabarito do autor: Jev {rel['jev']['acertos']}/"
            f"{rel['jev']['casos_programados']} contra {rel['llm']['acertos']}/"
            f"{rel['llm']['casos_programados']}, diferenca {autor['diferenca_observada']:+.4f}, "
            f"IC95 [{autor['ic95'][0]:.4f}; {autor['ic95'][1]:.4f}], McNemar exato p = "
            f"{rel['mcnemar_p_exato']}.")
    if outro:
        nota += (' Sob o gabarito do anotador independente, que e o unico que nao passou pela '
                 f"mao do avaliador: {outro['diferenca_observada']:+.4f}, IC95 "
                 f"[{outro['ic95'][0]:.4f}; {outro['ic95'][1]:.4f}] — contem zero, e o sinal "
                 'inverte. O gargalo nao e a comparacao entre os modelos, e a validade do '
                 'rotulo.')
    return {
        'id': 'e11-desempate-corpus-novo', 'system_id': 'S01', 'phase': 'confirmation',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': rel['modelo'],
        'dataset': ('60 casos novos em 20 familias de fenomeno linguistico, nenhuma repetida dos '
                    'corpora anteriores; dois bracos na mesma lista e na mesma ordem'),
        'notes': nota,
        'attempts': tentativas, 'decisions': decisoes,
    }


def e12_run(rel, gold, agora):
    """A replicacao: CINCO bracos na mesma lista, entao cinco tentativas por caso.

    A nota e montada a partir do relatorio, nunca escrita a mao: um texto fixo com numeros
    dentro continua afirmando o mesmo depois que os dados mudam.
    """
    tentativas, decisoes = [], []
    bracos = [('jev', 'replicacao-jev')] + [(chave, 'replicacao-' + chave)
                                            for chave in rel['comparadores']]
    for c in rel['casos']:
        for campo, pergunta in bracos:
            aid = c.get(campo + '_attempt_id')
            if not aid:
                continue
            estado = c.get('jev_status') if campo == 'jev' else (
                'success' if c.get(campo) else 'invalid_response')
            tentativas.append(tentativa(aid, estado, c.get(campo + '_latency_ms'),
                                        c.get(campo + '_cost_nusd')))
            decisoes.append(decisao(campo + ':' + c['case_id'], c['case_id'], aid, 'test',
                                    c['gold'], c.get(campo), c.get(campo + '_confidence'),
                                    pergunta, c['family']))

    principal = (rel['por_gabarito'].get('oficial')
                 or rel['por_gabarito'].get('autor'))
    partes = []
    for chave, modelo in rel['comparadores'].items():
        comp = principal['comparacoes'][chave]
        partes.append('%s (%s): %+.4f, IC95 [%.4f; %.4f]'
                      % (chave, modelo, comp['pareada']['diferenca_observada'],
                         comp['pareada']['ic95'][0], comp['pareada']['ic95'][1]))
    nota = ('Corpus novo de %d casos em %d familias, declaradas no pre-registro antes de o '
            'primeiro caso existir, contra QUATRO comparadores economicos de quatro '
            'fornecedores. E o item 1 do proximo movimento do relatorio final. Diferenca pareada '
            'do Jev contra cada um, no gabarito de referencia: %s. Leitura pre-registrada por '
            'interseccao-uniao (so ha vantagem se TODOS separarem de zero): %s.'
            % (rel['casos_programados'], rel['familias'], '; '.join(partes), rel['veredito']))
    if len(set(rel['leitura_por_gabarito'].values())) > 1:
        nota += (' As leituras divergem entre gabaritos (%s), e o pre-registro manda reportar a '
                 'divergencia em vez de escolher a mais favoravel.'
                 % '; '.join(n + ': ' + v for n, v in sorted(rel['leitura_por_gabarito'].items())))
    return {
        'id': 'e12-replicacao-quatro-comparadores', 'system_id': 'S01', 'phase': 'confirmation',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': rel['at'], 'finished_at': rel['at'],
        'provider': 'openrouter', 'model': rel['modelo'],
        'dataset': ('%d casos novos em %d familias de fenomeno linguistico, nenhuma repetida dos '
                    'corpora anteriores; cinco bracos na mesma lista e na mesma ordem'
                    % (rel['casos_programados'], rel['familias'])),
        'notes': nota,
        'attempts': tentativas, 'decisions': decisoes,
    }


def tentativas_orfas_run(estado, agora):
    """Tentativas que existem no ledger e nao aparecem no painel.

    O painel somava US$ 0,017525 e o ledger US$ 0,018174: a diferenca eram as chamadas do E4
    (ranqueamento, que nao publica decisoes) e tres sondagens de contrato. Dois numeros de custo
    no mesmo painel e exatamente a contradicao que a oitava revisao cobrou, entao aqui o custo
    fecha com o ledger. Sao tentativas sem decisao: entram pelo custo, nao pela metrica.
    """
    import sqlite3
    caminho = ROOT / 'runs' / 'ledger.sqlite3'
    if not caminho.exists():
        return None
    # O proprio run de orfas NAO conta como publicacao: ele e reconstruido do zero a cada
    # execucao e substitui o anterior. Enquanto ele contava, a segunda passagem via as orfas
    # antigas como "ja publicadas", montava o run so com as novas e sumia com as antigas — foi
    # o que aconteceu quando o E11 perdido entrou e as 16 chamadas do E4 sairam do painel.
    ja_publicadas = {a['id'] for r in estado['runs'] for a in r['attempts']
                     if r['id'] != 'tentativas-sem-decisao-publicada'}
    db = sqlite3.connect(str(caminho))
    db.row_factory = sqlite3.Row
    try:
        linhas = [r for r in db.execute(
            'SELECT ab.attempt_id, ab.block_id, ab.settled_nusd, ab.reserved_nusd,'
            ' a.status, a.latency_ms FROM attempt_budget ab'
            ' LEFT JOIN attempts a ON a.attempt_id = ab.attempt_id')
            if r['attempt_id'] not in ja_publicadas]
    finally:
        db.close()
    if not linhas:
        return None
    tentativas = []
    for r in linhas:
        custo = r['settled_nusd'] if r['settled_nusd'] is not None else r['reserved_nusd']
        tentativas.append({'id': r['attempt_id'],
                           'status': 'success' if r['status'] == 'success' else 'error',
                           'latency_ms': r['latency_ms'], 'input_tokens': None,
                           'output_tokens': None, 'cost_usd': (custo or 0) / 1e9,
                           'reserved_usd': (r['reserved_nusd'] or 0) / 1e9, 'cache_hit': False})
    blocos = sorted({r['block_id'] for r in linhas})
    return {
        'id': 'tentativas-sem-decisao-publicada', 'system_id': 'S01', 'phase': 'pilot',
        'evidence': 'live_component', 'status': 'completed',
        'started_at': agora, 'finished_at': agora,
        'provider': 'openrouter', 'model': 'typesafe/jev-1.13',
        'dataset': f"tentativas dos blocos {', '.join(blocos)}, lidas do ledger",
        'notes': ('Chamadas pagas que nao viram decisao no painel: o E4 e ranqueamento e nao entra '
                  'no formato de classificacao, e as sondagens de contrato nao tinham gabarito. '
                  'Elas entram aqui para que o custo somado no painel seja o mesmo do ledger, em vez '
                  'de dois numeros de custo no mesmo lugar. Sem decisoes: nao afetam nenhuma metrica.'),
        'attempts': tentativas, 'decisions': [],
    }


def publicar():
    gold = gabarito()
    agora = datetime.now(timezone.utc).isoformat()
    novos = []
    for arquivo, construir in [('e2-fatorial/relatorio.json', e2_run),
                               ('e2b-posicao/relatorio.json', e2b_run),
                               ('e5-provedores/relatorio.json', e5_run),
                               ('e6-repetibilidade/relatorio.json', e6_run),
                               ('e7-confirmacao/relatorio.json', e7_run),
                               ('e10-llm-economico/relatorio.json', e10_run),
                               ('e10b-piloto/relatorio.json', e10b_run),
                               ('e11-desempate/relatorio.json', e11_run),
                               ('e12-replicacao/relatorio.json', e12_run)]:
        rel = ler(arquivo)
        if rel:
            novos.append(construir(rel, gold, agora))

    estado = json.loads(ESTADO.read_text(encoding='utf-8'))
    por_id = {r['id']: r for r in estado['runs']}
    for run in novos:
        por_id[run['id']] = run
    estado['runs'] = list(por_id.values())
    orfas = tentativas_orfas_run(estado, agora)
    if orfas:
        novos.append(orfas)
        por_id[orfas['id']] = orfas
    estado['runs'] = list(por_id.values())
    estado['revision'] = int(estado.get('revision', 0)) + 1
    estado['updated_at'] = agora
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding='utf-8')
    return novos


if __name__ == '__main__':
    for run in publicar():
        print(f"{run['id']:38} {len(run['attempts']):4} tentativas  {len(run['decisions']):4} decisoes")
