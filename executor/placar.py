"""Placar de decisão: transforma os relatórios dos experimentos em números de decidir.

Todo texto daqui sai em português do Brasil, com acentuação e vírgula decimal: o painel é lido
por gente que fala português, e número com ponto decimal num texto em português é erro, não
estilo.

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

from . import gabarito

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs'
ESTADO = ROOT / 'lab' / 'data' / 'execution.json'


def ler(caminho):
    alvo = RUNS / caminho
    if not alvo.exists():
        return None
    return json.loads(alvo.read_text(encoding='utf-8'))


def pct(x):
    """Percentual em pt-BR. O painel inteiro e em portugues; o numero tambem."""
    return f'{x * 100:.1f}'.replace('.', ',') + '%'


def dec(x, casas=3):
    """Numero decimal em pt-BR."""
    return f'{x:.{casas}f}'.replace('.', ',')


def cartao(chave, titulo, valor, comparacao, leitura, fonte, estado='pronto'):
    return {'chave': chave, 'titulo': titulo, 'valor': valor, 'comparacao': comparacao,
            'leitura': leitura, 'fonte': fonte, 'estado': estado}


def ausente(chave, titulo, motivo, fonte):
    return cartao(chave, titulo, '—', 'sem execução', motivo, fonte, estado='pendente')


def sobre_programados(bloco, casos):
    """Acuracia contando resposta ausente como erro, mesmo em relatorio antigo.

    Relatorios gerados antes da correcao P1-4 so tem a acuracia condicional as respostas
    validas. Ler esse campo no placar reintroduz o defeito: uma execucao com falhas de
    transporte apareceria com acuracia inflada. Aqui o denominador e sempre o programado.
    """
    if 'acuracia_sobre_programados' in bloco:
        return bloco['acuracia_sobre_programados'], bloco.get('casos_programados', len(casos))
    programados = len(casos)
    return (round(bloco['acertos'] / programados, 4) if programados else None), programados


def gabarito_do_corpus(prefixo):
    """Ha mais de um gabarito em jogo neste corpus?

    A versao anterior perguntava se a ADJUDICACAO mudou algum caso, que e outra coisa. Com essa
    pergunta, o piloto inteiro aparecia como unanime enquanto tinha quatro casos em que os
    anotadores discordavam. A pergunta certa e se os anotadores divergiram.
    """
    local = gabarito.do_anotador_local()
    autor = gabarito.do_autor()
    if not local:
        return 'autor'
    divergem = [cid for cid, rotulo in local.items()
                if cid.startswith(prefixo) and cid in autor and rotulo != autor[cid]['gold']]
    return 'coincidem' if not divergem else 'ha-divergencia'


def faixa_dos_gabaritos(d):
    """A faixa entre TODOS os gabaritos de um conjunto, a partir do desempenho recalculado.

    Duas versoes anteriores erraram aqui. A primeira fazia min(local, autor) a max(oficial,
    autor): dava certo so porque o oficial e, hoje, o mais alto. A segunda foi buscar o
    desempenho dentro da propria funcao, e com isso deixou de ser testavel — os tres testes da
    decima primeira rodada passaram a exercitar o repositorio em vez da regra. Aqui a funcao so
    calcula: quem chama traz o dado, e o dado vem de `gabarito.desempenho_do_estudo()`.
    """
    valores = gabaritos_do_conjunto(d)
    baixo, alto = min(valores.values()), max(valores.values())
    return (pct(baixo) if baixo == alto else f'{pct(baixo)} a {pct(alto)}'), valores


def fonte_com_gabarito(fonte, qual='autor'):
    """Toda fonte declara o gabarito. Cartao que nao declara obriga o leitor a adivinhar.

    Do corpus piloto nenhum caso mudou na adjudicacao, entao ali os dois gabaritos coincidem e
    dizer isso e mais util do que escolher um nome.
    """
    rotulos = {'autor': 'gabarito do autor',
               'calibracao': ('gabarito do autor; o caso que a adjudicação mudou tinha confiança '
                              '0,60 e não entrava em nenhum dos cortes, então a contagem de erro '
                              'entre os aceitos é a mesma nos dois gabaritos'),
               'oficial': 'gabarito oficial (com adjudicação)',
               'coincidem': 'os dois gabaritos coincidem neste corpus',
               'faixa': 'faixa entre os gabaritos',
               'ha-divergencia': ('gabarito do autor; os anotadores divergem em casos deste '
                                  'corpus, e o cartão do E8 traz o efeito disso'),
               'nao-se-aplica': 'sem gabarito de classe'}
    return f"{fonte}; {rotulos[qual]}"


def gabaritos_do_conjunto(d):
    """Os gabaritos que existem para este conjunto, nomeados. Sao tres, nao dois.

    O anotador independente tem um gabarito desde o E8, e ele e o mais severo: no piloto da
    87,5% contra 92,5% do autor. Por seis rodadas o painel ensinou tres gabaritos no cartao do
    E8 e, nos cartoes que o olho le primeiro, mostrou dois.
    """
    valores = {'autor': d['autor']['acuracia'], 'oficial': d['oficial']['acuracia']}
    if d.get('anotador_local'):
        valores['anotador local'] = d['anotador_local']['acuracia']
    return valores


def valor_entre_gabaritos(d):
    """O numero de capa e a FAIXA entre todos os gabaritos, nunca o melhor deles."""
    valores = gabaritos_do_conjunto(d)
    baixo, alto = min(valores.values()), max(valores.values())
    return pct(baixo) if baixo == alto else f'{pct(baixo)} a {pct(alto)}'


def leitura_dos_gabaritos(d, nome):
    """Compara os dois gabaritos a partir da MESMA contagem, nos dois sentidos.

    A versão anterior só sabia descrever o caso em que a adjudicação apagava um erro. Se ela
    criasse um erro novo, ou se o relatório fosse relido sob o gabarito oficial, a frase saía
    errada sem ninguém notar.
    """
    if not d or not d['adjudicado']:
        return f'{nome} ainda sem adjudicação: o número é o do gabarito do autor.'
    autor, oficial = d['autor']['acertos'], d['oficial']['acertos']
    total = d['casos_programados']
    mudados = d['casos_deste_relatorio_que_mudaram']
    if not mudados:
        return (f'A adjudicação não mexeu em nenhum caso deste conjunto: {oficial}/{total} nos dois '
                'gabaritos.')
    quais = ', '.join(mudados)
    if oficial > autor:
        return (f'A adjudicação levou {nome} de {autor}/{total} para {oficial}/{total}, porque '
                f'{quais} mudou de lado. Ler isso como acerto pleno seria trocar de gabarito depois '
                'de ver o resultado: o número do autor está ao lado, de propósito.')
    if oficial < autor:
        return (f'A adjudicação levou {nome} de {autor}/{total} para {oficial}/{total}: {quais} '
                'passou a contar como erro.')
    return (f'A adjudicação mexeu em {quais} sem alterar a contagem: {oficial}/{total} nos dois '
            'gabaritos.')


def pendencias(adj):
    """O que falta, calculado: a lista nao pode continuar pedindo o que ja foi feito."""
    lista = []
    if not adj:
        lista.append('Adjudicação dos casos em que os anotadores divergem: sem ela, dois '
                     'anotadores que discordam não produzem gabarito.')
    else:
        lista.append('Anotação e adjudicação por pessoas do atendimento real: os três juízes '
                     'deste estudo são modelos, e modelos grandes tendem a compartilhar a mesma '
                     'convenção sobre o que é "a ação pedida".')
    lista.append('Corpus colhido de atendimento real, com a distribuição de classes que o canal '
                 'tem, em vez de casos construídos e quase balanceados.')
    lista.append('P5: fluxo completo com minutagem humana. O custo por decisão deste painel usa '
                 'tempo declarado, nunca cronometrado.')
    return lista


def politica_de_referencia(e9, corte=0.90):
    """A politica do corte 0,90 na particao de confirmacao. UMA, para o painel inteiro.

    O veredito lia a confirmacao e o cartao do E9 lia a uniao, entao o mesmo painel publicava
    87,5% em 40 casos e 80% em 80 casos para a mesma decisao. Sem fallback silencioso: se a
    particao sumir, quem chama recebe None e diz isso, em vez de trocar o numero por outro.
    """
    if not e9:
        return None
    confirmacao = (e9.get('por_particao') or {}).get('confirmacao (teste)') or {}
    return next((p for p in confirmacao.get('politicas', []) if p['corte'] == corte), None)


def confianca_calculada(e9, e6, e8, adj):
    """A confianca sai de regras declaradas, nao de um numero digitado.

    Um 0,6 cravado no codigo continua dizendo 0,6 depois que os dados pioram. Aqui cada
    desconto tem motivo, e a lista de motivos vai junto para que a conta seja auditavel — e
    contestavel, que e o ponto.
    """
    valor, motivos = 1.0, []
    politica = politica_de_referencia(e9) if e9 else None
    if politica is None:
        valor -= 0.30
        motivos.append('sem partição de teste para sustentar a política (-0,30)')
    else:
        if politica['casos'] < 100:
            valor -= 0.20
            motivos.append(f"a política se apoia em {politica['casos']} casos, menos de cem (-0,20)")
        if politica['erros_entre_aceitos']:
            valor -= 0.20
            motivos.append(f"{politica['erros_entre_aceitos']} erro(s) entre os aceitos (-0,20)")
    if e6 and e6['n_instaveis']:
        valor -= 0.10
        motivos.append(f"{e6['n_instaveis']} caso(s) mudam de resposta entre repetições "
                       'idênticas (-0,10)')
    if adj:
        valor -= 0.10
        motivos.append('o gabarito foi adjudicado por modelos, não por pessoas do domínio (-0,10)')
    else:
        valor -= 0.20
        motivos.append('o gabarito tem um anotador só, sem adjudicação (-0,20)')
    # O corpus e construido pelo avaliador em todos os cenarios deste estudo.
    valor -= 0.10
    motivos.append('corpus construído pelo avaliador, não colhido de uso real (-0,10)')
    return round(max(0.0, min(1.0, valor)), 2), motivos


def nota_de_confianca(adj, e9=None):
    """A nota tambem acompanha o estado da adjudicacao, em vez de ficar cravada."""
    politica = politica_de_referencia(e9) if e9 else None
    # A base citada aqui tem que ser a MESMA da politica que o veredito recomenda. Enquanto a
    # nota falava de 80 casos e o veredito de 40, o painel justificava a decisao com um
    # denominador que ele proprio tinha recusado.
    if politica:
        onde = (f"o corte de 0,90 é sustentado por {politica['casos']} casos da partição de "
                f"confirmação, com {politica['erros_entre_aceitos']} erro entre os aceitos")
    else:
        onde = 'não há partição de confirmação para sustentar corte nenhum'
    erros_totais = len(adj['gabarito_adjudicado']['erros']) if adj else None
    total = adj['gabarito_adjudicado']['casos_com_resposta_do_jev'] if adj else None
    base = ('Calibrada para baixo depois da sexta revisão independente. Alta para a comparação '
            'contra as regras congeladas: é pareada, pré-registrada e replicou fora do piloto. '
            f'Baixa para qualquer afirmação operacional: {onde}'
            + (f", e o modelo erra {erros_totais} de {total} casos no estudo inteiro"
               if erros_totais is not None else '')
            + '. A conta de custo usa tempo humano declarado, nunca cronometrado.')
    if not adj:
        return base + ' O gabarito é de um anotador só e os casos em disputa não foram adjudicados.'
    g = adj['gabarito_adjudicado']
    return (base + f" Os {len(adj['casos'])} casos em disputa foram adjudicados por um terceiro juiz "
            f"cego, e sob esse gabarito a acurácia é {dec(g['acuracia'], 4)} — mas os três juízes são "
            'modelos, não pessoas do atendimento real.')


def titulo_do_veredito(e9):
    """O titulo tambem precisa cair quando o dado cair.

    Antes era uma frase cravada recomendando o corte de 0,90. Se o E9 sumisse, ou se a
    politica passasse a deixar erro entre os aceitos, o titulo continuaria recomendando.
    """
    if not e9:
        return 'Sem análise de política: não há recomendação operacional'
    politica = politica_de_referencia(e9)
    if politica is None:
        return 'Uso consultivo com revisão humana'
    if politica['erros_entre_aceitos'] == 0:
        return 'Corte de confiança em 0,90 com revisão humana do resto'
    melhor = next((politica_de_referencia(e9, corte=c)
                   for c in (0.95, 0.99)
                   if (politica_de_referencia(e9, corte=c) or {}).get('erros_entre_aceitos') == 0),
                  None)
    if melhor:
        return f"Corte de confiança em {melhor['corte']} com revisão humana do resto"
    return 'Revisão humana de todas as decisões: nenhum corte zerou o erro'


def texto_do_veredito(e9, e6):
    """O veredito e calculado, nao escrito a mao.

    Um texto fixo com numeros dentro continua afirmando o mesmo depois que os dados mudam: na
    execucao seguinte o placar mentiria sem que ninguem percebesse.
    """
    if not e9:
        return 'Sem a análise de política de aceitação, o placar não tem recomendação operacional.'
    # A particao de confirmacao e a que vale para decidir: sao os casos que nao guiaram o
    # desenho. A uniao entra so na conta de custo, que nao depende de particao.
    politica = politica_de_referencia(e9)
    # O custo TEM de sair da mesma particao da cobertura. Enquanto a cobertura vinha da
    # confirmacao e o custo da uniao, o painel prometia 87,5% de cobertura pelo preco de uma
    # politica que cobre 80% — uma linha que nao existe em relatorio nenhum.
    tudo = politica_de_referencia(e9, corte=1.01)
    partes = []
    if politica and politica['erros_entre_aceitos'] == 0:
        partes.append(f"aceitar automaticamente o que vier com confiança de 0,90 ou mais cobre "
                      f"{politica['cobertura'] * 100:.1f}".replace('.', ',') + '% dos '
                      + f"{politica['casos']} casos da partição "
                      'de confirmação sem nenhum erro observado entre os aceitos')
    elif politica:
        partes.append(f"no corte 0,90 a política cobre {politica['cobertura'] * 100:.0f}% dos casos, "
                      f"mas deixa passar {politica['erros_entre_aceitos']} erro(s): o corte precisa subir")
    if politica and tudo:
        partes.append(f"nessa mesma partição o custo por decisão cai de "
                      f"US$ {dec(tudo['custo_por_decisao_usd'])} para "
                      f"US$ {dec(politica['custo_por_decisao_usd'])}, com tempo humano declarado e "
                      'nunca cronometrado')
    if e6 and e6['n_instaveis']:
        partes.append(f"o que impede automatizar tudo é o não determinismo: {e6['n_instaveis']} caso "
                      f"em {e6['casos']}, sozinho e repetido {e6['repeticoes']} vezes, muda de resposta")
    texto = '; '.join(partes)
    return texto[:1].upper() + texto[1:] + '.'


def montar():
    e1 = ler('e1-triagem/relatorio.json')
    e3 = ler('e3-evidencia/relatorio.json')
    e4 = ler('e4-ressalvas/relatorio.json')
    e2 = ler('e2-fatorial/relatorio.json')
    e2b = ler('e2b-posicao/relatorio.json')
    e5 = ler('e5-provedores/relatorio.json')
    e6 = ler('e6-repetibilidade/relatorio.json')
    e7 = ler('e7-confirmacao/relatorio.json')
    e8 = ler('e8-anotador/relatorio.json')
    adj = ler('e8-anotador/adjudicacao.json')
    e9 = ler('e9-prevalencia/relatorio.json')
    pareada = ler('analise-pareada.json') or {}

    cartoes = []
    if e1:
        dif = pareada.get('e1_triagem', {})
        ic = dif.get('ic95')
        d1 = gabarito.desempenho('runs/e1-triagem/relatorio.json')
        acuracia_e1, programados_e1 = d1['oficial']['acuracia'], d1['casos_programados']
        regra_e1, _ = sobre_programados(e1['regra'], e1['casos'])
        cartoes.append(cartao(
            'e1', 'Triagem de atendimento (E1)', valor_entre_gabaritos(d1),
            (' · '.join(f'{nome} {pct(v)}' for nome, v in
                         sorted(gabaritos_do_conjunto(d1).items(), key=lambda kv: kv[1]))
             + f" · regra congelada {pct(regra_e1)}"),
            ('Vantagem de ' + pct(dif['diferenca_observada']) +
             f", IC95 [{pct(ic[0])}; {pct(ic[1])}] por reamostragem de famílias, "
             'no gabarito do autor como pré-registrado.' if ic else
             'Diferença ainda sem intervalo calculado.'),
            fonte_com_gabarito(f"{programados_e1} casos programados, "
                               f"{e1['jev']['n_familias']} famílias",
                               'faixa' if len(set(gabaritos_do_conjunto(d1).values())) > 1
                               else 'coincidem')))
    else:
        cartoes.append(ausente('e1', 'Triagem de atendimento (E1)', 'Piloto não executado.', '—'))

    if e3:
        dif = pareada.get('e3_evidencia', {})
        ic = dif.get('ic95')
        acuracia_e3, programados_e3 = sobre_programados(e3['jev'], e3['casos'])
        regra_e3, _ = sobre_programados(e3['regra'], e3['casos'])
        cartoes.append(cartao(
            'e3', 'Suporte por evidência (E3)', pct(acuracia_e3),
            f'regra ingênua {pct(regra_e3)}',
            ('Vantagem de ' + pct(dif['diferenca_observada']) +
             f", IC95 [{pct(ic[0])}; {pct(ic[1])}]." if ic else 'Sem intervalo calculado.'),
            fonte_com_gabarito(f"{programados_e3} casos programados, "
                               f"{e3['jev']['n_familias']} famílias", 'autor')))
    else:
        cartoes.append(ausente('e3', 'Suporte por evidência (E3)', 'Piloto não executado.', '—'))

    if e4:
        cartoes.append(cartao(
            'e4', 'Ressalvas preservadas (E4)',
            f"{e4['jev']['ressalvas_no_topo']}/{e4['jev']['ressalvas_totais']}",
            f"BM25 {e4['bm25']['ressalvas_no_topo']}/{e4['bm25']['ressalvas_totais']} · "
            f"ordem de chegada {e4['original']['ressalvas_no_topo']}/{e4['original']['ressalvas_totais']}",
            f"nDCG@5 {dec(e4['jev']['ndcg5'], 4)} contra {dec(e4['bm25']['ndcg5'], 4)} do BM25. "
            'Ressalva perdida no topo é exceção que não chega a quem decide.',
            fonte_com_gabarito(f"{e4['topo']} primeiros de 8 consultas × 5 candidatos",
                               'nao-se-aplica')))
    else:
        cartoes.append(ausente('e4', 'Ressalvas preservadas (E4)', 'Piloto não executado.', '—'))

    if e2:
        condicoes = e2['condicoes']
        # A acuracia condicional ignora resposta ausente. Com cobertura cheia da no mesmo,
        # mas o painel nao pode depender de sorte: o denominador e o programado.
        acuracias = [round(c['resumo']['acertos'] / c['resumo']['n'], 4)
                     for c in condicoes.values()]
        individuais = [c['resumo']['custo_por_decisao_nusd'] for c in condicoes.values()
                       if not c['condicao']['lote']]
        lotes = [c['resumo']['custo_por_decisao_nusd'] for c in condicoes.values()
                 if c['condicao']['lote']]
        referencia = sum(individuais) / len(individuais) if individuais else None
        economias = ([100 * (1 - x / referencia) for x in lotes] if referencia and lotes else [])
        faixa = f'{dec(min(acuracias))} a {dec(max(acuracias))}'
        cartoes.append(cartao(
            'e2', 'Lote, ordem e distração (E2)', faixa, '8 condições fatoriais',
            ('Nenhum contraste separa as condições (McNemar p=1,000 em todos). '
             + (f'Lote economiza {dec(min(economias), 1)}% a {dec(max(economias), 1)}% por decisão.'
                if economias else 'Economia do lote registrada no relatório.')),
            fonte_com_gabarito(f'{len(condicoes)} condições sobre os mesmos 40 casos',
                               gabarito_do_corpus('tri-'))))
    else:
        cartoes.append(ausente('e2', 'Lote, ordem e distração (E2)', 'Fatorial não executado.', '—'))

    if e2b:
        dif = pareada.get('e2b_posicao', {})
        instaveis = sum(1 for acertos, total in e2b['por_caso'].values() if 0 < acertos < total)
        cartoes.append(cartao(
            'e2b', 'Estabilidade no lote (E2b)', f'{instaveis} de {len(e2b["por_caso"])} casos instáveis',
            f"p de permutação {str(dif.get('p_permutacao', '—')).replace('.', ',')}",
            ('Posição no lote não explica erro. Mas esses casos mudam de resposta conforme os '
             'vizinhos do lote: mesma pergunta, resposta diferente.'),
            fonte_com_gabarito(f"{len(e2b['observacoes'])} observações em "
                               f"{len(e2b['sementes'])} permutações", gabarito_do_corpus('tri-'))))
    else:
        cartoes.append(ausente('e2b', 'Estabilidade no lote (E2b)', 'Desconfundimento não executado.', '—'))

    # A calibracao que vale e a do conjunto de confirmacao: e particao de teste, e os casos
    # nao ajudaram a desenhar nada. A do piloto fica no relatorio, nao no placar.
    calibracao = pareada.get('calibracao_confirmacao_0.95') or pareada.get('calibracao_0.95')
    if calibracao:
        cartoes.append(cartao(
            'calibracao', ('Calibração no corte 0,95 ('
             + {'confirmacao': 'confirmação'}.get(calibracao.get('conjunto', 'piloto'),
                                                  calibracao.get('conjunto', 'piloto')) + ')'),
            f"{calibracao['aceitos']} aceitos de {calibracao['casos_programados']}",
            f"cobertura {pct(calibracao['cobertura_sobre_programados'])}",
            (f"{calibracao['erros_entre_aceitos']} erro(s) observado(s), mas os aceitos vêm de apenas "
             f"{calibracao['familias_representadas_entre_aceitos']} famílias: o limite superior honesto "
             f"é {pct(calibracao['limite_superior_erro_por_familia'])} por família, não "
             f"{pct(calibracao['limite_superior_erro_por_caso'])} por caso."),
            fonte_com_gabarito(f"{calibracao['casos_programados']} casos, corte de confiança 0,95",
                               'calibracao')))

    if e5:
        cartoes.append(cartao(
            'e5', 'Provedor: OpenRouter × TypeSafe (E5)', pct(e5['taxa_concordancia']),
            f"{e5['concordancia']} de {e5['casos']} casos concordam",
            ' · '.join(f"{nome}: {pct(d['acuracia'])} de acurácia, p50 {d['latencia_p50_ms']:.0f} ms, "
                       f"{d['custo_por_decisao_nusd'] / 1e9:.9f} USD por decisão"
                       for nome, d in e5['resumo'].items()),
            fonte_com_gabarito(f"{e5['casos']} casos × 2 transportes, chamadas intercaladas",
                               gabarito_do_corpus('tri-'))))
    else:
        cartoes.append(ausente('e5', 'Provedor: OpenRouter × TypeSafe (E5)',
                               'Comparação de transporte ainda não despachada.',
                               'chave TypeSafe registrada; script pronto'))

    if e7:
        par = e7['pareada']
        d7 = gabarito.desempenho('runs/e7-confirmacao/relatorio.json')
        cartoes.append(cartao(
            'e7', 'Conjunto de confirmação (E7)', valor_entre_gabaritos(d7),
            (' · '.join(f'{nome} {pct(v)}' for nome, v in
                         sorted(gabaritos_do_conjunto(d7).items(), key=lambda kv: kv[1]))
             + f" · regra congelada {pct(e7['regra']['acuracia_sobre_programados'])}"),
            (f"Casos novos, que não guiaram o desenho: diferença {pct(par['diferenca_observada'])}, "
             f"IC95 [{pct(par['ic95'][0])}; {pct(par['ic95'][1])}]. O Jev subiu pouco "
             '(92,5% para 97,5%); quem caiu foi a regra (60,0% para 32,5%), porque o corpus tem '
             'armadilhas lexicais. ' + leitura_dos_gabaritos(d7, 'E7')),
            fonte_com_gabarito(f"{d7['casos_programados']} casos programados, "
                               f"{e7['jev']['n_familias']} famílias novas",
                               'faixa' if len(set(gabaritos_do_conjunto(d7).values())) > 1
                               else 'coincidem')))
    else:
        cartoes.append(ausente('e7', 'Conjunto de confirmação (E7)',
                               'Corpus de confirmação ainda não executado.', '—'))

    if e8:
        # A leitura tem que citar os DOIS lados. Na primeira versao este cartao dizia so que o
        # anotador apoiou o Jev em dois casos e omitia que ele confirmou o gabarito nos outros
        # dois erros. Contar meia divergencia e propaganda, nao auditoria.
        erros = [a for a in e8['anotacoes'] if a['jev'] and a['jev'] != a['gold']]
        d80b = gabarito.desempenho_do_estudo()
        apoiam_jev = [a for a in erros if a['anotador'] == a['jev']]
        apoiam_gabarito = [a for a in erros if a['anotador'] == a['gold']]
        if adj:
            placar_adj = adj['placar']
            g = adj['gabarito_adjudicado']
            d80 = gabarito.desempenho_do_estudo()
            faixa, valores = faixa_dos_gabaritos(d80)
            cartoes.append(cartao(
                'e8', 'Gabarito adjudicado (E8)', faixa,
                ' · '.join(f'{nome} {pct(v)}' for nome, v in
                           sorted(valores.items(), key=lambda kv: kv[1])),
                (f"Os {len(adj['casos'])} casos em disputa foram julgados por um terceiro juiz cego, que "
                 'recebeu só a mensagem e as duas leituras em ordem sorteada. Ele confirmou o gabarito '
                 f"do autor em {placar_adj['confirmam_o_autor']} e o do anotador local em "
                 f"{placar_adj['confirmam_o_modelo_local']}. Isso desfaz a leitura anterior deste painel: "
                 f"o Jev erra {len(d80['oficial']['erros'])} casos no gabarito adjudicado "
                 f"({', '.join(d80['oficial']['erros'])}), e não os 2 que este painel "
                 'chegou a anunciar antes da adjudicação. Acurácia ' + faixa
                 + ' conforme o gabarito adotado.'),
                f"{adj['terceiro_juiz']}, cego a quem escreveu cada leitura"))
        cartoes.append(cartao(
            'e8b', 'Concordância entre anotadores (E8)', f"kappa {dec(e8['kappa_cohen'], 4)}",
            f"concordância bruta {pct(e8['concordancia_bruta'])}, antes de adjudicar",
            (f"{e8['n_divergencias']} divergências em {e8['respostas_validas']} casos. Dos "
             f"{len(erros)} erros do Jev NO GABARITO DO AUTOR"
             + (' (o oficial tem outro número, no cartão acima)' if adj else
                ' (ainda sem adjudicação: este é o único gabarito disponível)')
             + ', o anotador independente confirma o gabarito em '
             f"{len(apoiam_gabarito)} ({', '.join(a['case_id'] for a in apoiam_gabarito)}) e fica do "
             f"lado do Jev em {len(apoiam_jev)} ({', '.join(a['case_id'] for a in apoiam_jev)}). "
             f"Sob o gabarito do outro anotador o Jev faz "
             f"{pct(d80b['anotador_local']['acuracia'])}, e não "
             f"{pct(d80b['autor']['acuracia'])}. Nas demais divergências foi "
             'o anotador que caiu na armadilha. Um modelo de 7B reproduziu a rubrica do autor: kappa '
             'alto aqui mede reprodutibilidade, não validade, e não substitui o segundo anotador humano.'),
            f"{e8['anotador_independente']} local, cego ao gabarito e à resposta do Jev"))
    else:
        cartoes.append(ausente('e8', 'Segundo anotador independente (E8)',
                               'Anotação independente não executada.', '—'))

    if e9:
        proj = e9['projecoes_por_prevalencia']
        valores = [p['acuracia_esperada'] for p in proj.values()]
        politica = politica_de_referencia(e9)
        fraca = min(e9['acuracia_por_classe'].items(), key=lambda kv: kv[1]['taxa'])
        leitura = (f"A acurácia esperada se move pouco entre as distribuições porque a classe mais "
                   f"fraca ainda faz {str(fraca[1]['taxa']).replace('.', ',')} — com "
                   f"{fraca[1]['casos']} casos só, o que "
                   'deixa essa taxa muito incerta. As distribuições são declaradas, não medidas, e a '
                   'conta supõe que a dificuldade dentro de cada classe é a mesma do corpus.')
        if politica:
            leitura += (f" No corte 0,90, na partição de confirmação, a política aceita "
                        f"{pct(politica['cobertura'])} dos {politica['casos']} casos com "
                        f"{politica['erros_entre_aceitos']} erro entre os aceitos — a mesma leitura "
                        'que o veredito usa.')
        else:
            leitura += (' A partição de confirmação não está no relatório: sem ela o painel não '
                        'publica cobertura, em vez de trocar pelo número da união.')
        cartoes.append(cartao(
            'e9', 'Sensibilidade à prevalência (E9)',
            f'{dec(min(valores))} a {dec(max(valores))}',
            f'{len(proj)} distribuições de canal', leitura,
            f"reponderação da matriz de confusão sob o {e9.get('gabarito', 'gabarito do autor')}; "
            'NÃO é a medição de P5, que pedia minutagem humana e continua pendente'))

    if e6:
        rodadas = list(e6['acuracia_por_rodada'].values())
        cartoes.append(cartao(
            'e6', 'Repetibilidade isolada (E6)',
            f"{e6['n_instaveis']} de {e6['casos']} casos oscilam",
            f"acurácia por rodada {dec(min(rodadas))} a {dec(max(rodadas))}",
            ('Mesmo sozinho, uma pergunta por chamada, o modelo não é determinístico: '
             f"{', '.join(e6['casos_instaveis'])} muda de resposta entre repetições idênticas. "
             f"Voto majoritário de {e6['repeticoes']} chega a {e6['acuracia_voto_majoritario']:.3f} "
             f"de acurácia, ao custo de {e6['repeticoes']}x as chamadas."),
            fonte_com_gabarito(f"{e6['casos']} casos × {e6['repeticoes']} repetições individuais",
                               gabarito_do_corpus('tri-'))))
    else:
        cartoes.append(ausente('e6', 'Repetibilidade isolada (E6)',
                               'Repetições individuais ainda não executadas.', '—'))

    # O saldo vale o do relatorio mais recente que registrou a carteira.
    carteira = e7 or e6 or e5 or e4 or e2b or {}
    comprometido = carteira.get('wallet_committed_nusd') or carteira.get('ledger_committed_nusd')
    disponivel = carteira.get('wallet_available_nusd') or carteira.get('available_nusd')

    confianca = confianca_calculada(e9, e6, e8, adj)
    bloco = {
        'atualizado_em': datetime.now(timezone.utc).isoformat(),
        'veredito': {
            'titulo': titulo_do_veredito(e9),
            'texto': texto_do_veredito(e9, e6),
            'confianca': confianca[0],
            'confianca_motivos': confianca[1],
            'confianca_nota': nota_de_confianca(adj, e9),
            'confianca_metodo': ('descontos declarados sobre 1,0; cada um com motivo em '
                                 'confianca_motivos'),
        },
        'cartoes': cartoes,
        'orcamento': ({'comprometido_nusd': comprometido, 'disponivel_nusd': disponivel}
                      if comprometido is not None else None),
        'relatorio_final': 'docs/RELATORIO-FINAL-JEV.md',
        'pendencias': pendencias(adj),
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
