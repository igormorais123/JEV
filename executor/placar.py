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


def confianca_calculada(e9, e6, e8, adj, e12=None):
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
    # [R13] A revisao adversarial mostrou tres descontos que a lista declarava em outro lugar do
    # relatorio e nao cobrava aqui. Uma nota que comeca em 1,0 e so desconta o que lembra e
    # teatro de calibracao: se o motivo esta escrito no documento, tem de entrar na conta.
    if politica and politica.get('erros_entre_aceitos') == 0:
        teto = limite_superior_erro_da_politica(politica)
        if teto is not None and teto > 0.10:
            valor -= 0.10
            motivos.append(f'zero erro observado entre os aceitos, mas o limite superior de 95% '
                           f'por família é {pct(teto)} (-0,10)')
    # O E12 replicou a pergunta do comparador com 30 familias e quatro fornecedores. Enquanto
    # ele existir, e o estado DELE que pesa aqui: o desconto do E11 media a mesma coisa com um
    # quarto dos comparadores.
    replicou = replicacao_depende_do_gabarito(e12 or ler('e12-replicacao/relatorio.json'))
    if replicou is not None:
        if not all(replicou.values()):
            valor -= 0.15
            motivos.append('na replicação com 30 famílias e quatro comparadores a vantagem do '
                           'Jev separa de zero sob o gabarito adjudicado e não separa sob o do '
                           'anotador independente: mais poder não resolveu a divergência, o que '
                           'aponta o rótulo e não a amostra como gargalo (-0,15)')
        else:
            valor -= 0.05
            motivos.append('o Jev superou quatro comparadores econômicos sob todos os '
                           'gabaritos, mas os anotadores que produziram esses gabaritos são '
                           'modelos de linguagem (-0,05)')
        return round(max(0.0, min(1.0, valor)), 2), motivos
    e10 = ler('e10-llm-economico/relatorio.json')
    if not e10:
        valor -= 0.10
        motivos.append('o comparador é uma regra congelada, não um modelo de linguagem barato '
                       'no mesmo contrato: a pergunta "vale um LLM aqui?" segue aberta (-0,10)')
    elif (lambda s: s and s.get('oficial'))(
            desempate_depende_do_gabarito(ler('e11-desempate/relatorio.json'))):
        # O braco existe e sustenta a vantagem no gabarito adjudicado. Sobra o desconto pelo que
        # ele NAO resolve: os tres anotadores do estudo continuam sendo modelos.
        valor -= 0.05
        motivos.append('o comparador econômico foi vencido no gabarito adjudicado, mas os três '
                       'anotadores que produziram esse gabarito são modelos de linguagem (-0,05)')
    elif (lambda s: s and not all(s.values()))(
            desempate_depende_do_gabarito(ler('e11-desempate/relatorio.json'))):
        valor -= 0.15
        motivos.append('no corpus de desempate a vantagem do Jev sobre o LLM econômico separa '
                       'de zero sob o gabarito do autor e não separa sob o do anotador '
                       'independente (-0,15)')
    elif evidencia_dividida(e10, ler('e10b-piloto/relatorio.json')):
        valor -= 0.15
        motivos.append('o braço do LLM econômico separa de zero em 20 famílias e não separa na '
                       'partição de teste: a evidência sobre a necessidade do Jev está '
                       'dividida (-0,15)')
    elif comparador_empatou(e10):
        # Pior do que nao ter o braco: ter, e ele nao sustentar a recomendacao.
        valor -= 0.20
        motivos.append('o braço do LLM econômico foi executado e a vantagem do Jev sobre ele '
                       'não separou de zero (-0,20)')
    return round(max(0.0, min(1.0, valor)), 2), motivos


def limite_superior_erro_da_politica(politica):
    """O teto de erro por familia da propria politica recomendada, quando o E9 o publica."""
    for chave in ('limite_superior_erro_por_familia', 'limite_superior_por_familia',
                  'limite_superior_erro'):
        if chave in politica:
            return politica[chave]
    grave = ler('erro-grave.json')
    if not grave:
        return None
    tetos = [b['jev']['limite_superior_por_familia']
             for bloco in grave['por_conjunto'].values() for b in bloco.values()]
    return max(tetos) if tetos else None



def nota_de_confianca(adj, e9=None, e11=None, e12=None):
    """A nota tambem acompanha o estado da adjudicacao, em vez de ficar cravada."""
    replicou = replicacao_depende_do_gabarito(e12)
    if replicou is not None and not all(replicou.values()):
        adj12 = ler('e12-replicacao/adjudicacao.json')
        oficial = e12['por_gabarito'].get('oficial') or e12['por_gabarito']['autor']
        outro = e12['por_gabarito']['anotador local']
        comparadores = e12['comparadores']
        return ('Baixa para adoção, e agora com a melhor evidência que este estudo produziu '
                'sobre o motivo. A replicação pré-registrada — ' + str(e12['casos_programados'])
                + ' casos, ' + str(e12['familias']) + ' famílias novas, quatro comparadores '
                'econômicos de quatro fornecedores — dá vantagem ao Jev contra todos no '
                'gabarito adjudicado, de ' + pct(min(
                    oficial['comparacoes'][c]['pareada']['diferenca_observada']
                    for c in comparadores)) + ' a ' + pct(max(
                    oficial['comparacoes'][c]['pareada']['diferenca_observada']
                    for c in comparadores)) + ', e nenhuma vantagem contra o comparador de 8B '
                'sob o gabarito do anotador independente ('
                + pct(outro['comparacoes']['c1']['pareada']['diferenca_observada'])
                + '). Triplicar as famílias em relação ao E11 e quadruplicar os comparadores não '
                'moveu a divergência'
                + (', e o terceiro juiz cego confirmou meu gabarito em '
                   + str(adj12['placar']['confirmam_o_autor']) + ' de '
                   + str(len(adj12['casos'])) + ' casos em disputa' if adj12 else '')
                + '. O que falta não é mais execução nem mais orçamento: são anotadores humanos '
                'do domínio, porque os três juízes deste estudo são modelos de linguagem.')
    separa = desempate_depende_do_gabarito(e11)
    if separa and separa.get('oficial'):
        pg = e11['por_gabarito']
        return ('Baixa para adoção, e não por causa do desempenho. A comparação contra as regras '
                'congeladas e contra um LLM econômico é pareada, pré-registrada e replicou: no '
                'corpus de desempate a vantagem é '
                + pct(pg['oficial']['pareada']['diferenca_observada'])
                + ' no gabarito adjudicado, e os 10 desacordos foram a um terceiro juiz cego que '
                'confirmou meu gabarito em todos. O que continua sem resposta é a validade do '
                'rótulo: os três anotadores deste estudo são modelos de linguagem, o corpus foi '
                'escrito pelo avaliador e o tempo humano da conta de custo nunca foi '
                'cronometrado.')
    if separa and not all(separa.values()):
        # Enquanto a nota descrevia a politica de corte, ela justificava uma recomendacao que o
        # veredito tinha deixado de fazer. A nota acompanha o veredito.
        por_gabarito = e11['por_gabarito']
        return ('Baixa, e o motivo agora tem nome. A comparação contra as regras congeladas '
                'continua sólida: é pareada, pré-registrada e replicou em três corpora. O que '
                'não se sustenta é a afirmação de que o Jev é necessário: no corpus de '
                'desempate a vantagem sobre um LLM econômico é '
                + pct(por_gabarito['autor']['pareada']['diferenca_observada'])
                + ' sob o meu gabarito e '
                + pct(por_gabarito['anotador local']['pareada']['diferenca_observada'])
                + ' sob o do anotador independente, com o intervalo contendo zero. Os números '
                'do estudo são reprodutíveis; o rótulo contra o qual eles foram medidos é que '
                'não foi validado por gente.')
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


def contem_zero(ic):
    return ic[0] <= 0 <= ic[1]


def comparador_empatou(e10):
    """O braco do LLM economico desmentiu a recomendacao na PARTICAO DE TESTE?

    A regra esta congelada no pre-registro do E10, escrita antes da primeira chamada: se o IC95
    da diferenca pareada contiver zero, o resultado e AUSENCIA DE EVIDENCIA DE VANTAGEM, e a
    recomendacao do painel deixa de ser "use o Jev". Nao e equivalencia — com 10 familias o
    poder e baixo por construcao — mas tambem nao e vantagem demonstrada.
    """
    if not e10:
        return None
    return contem_zero(e10['pareada']['ic95'])


def desempate_depende_do_gabarito(e11):
    """No E11 a vantagem do Jev sobre o comparador barato sobrevive aos gabaritos?

    Entre a primeira versao desta funcao e esta, os 10 desacordos do corpus de desempate foram a
    um terceiro juiz cego, sob emenda escrita antes da execucao. Ele confirmou o gabarito do
    autor em 10 de 10, e com isso o gabarito OFICIAL do corpus passou a existir. A leitura muda:
    o que separa de zero sao o gabarito do autor e o oficial; o que nao separa e o do anotador
    independente sozinho, que o terceiro juiz nao sustentou em nenhum caso.

    A regra congelada no pre-registro do E11 olhava o gabarito do corpus, que e o meu. A
    politica deste painel, desde a decima segunda rodada, e nunca apresentar um gabarito sozinho.
    As duas coisas se encontram aqui: sob o meu gabarito o Jev separa de zero; sob o do anotador
    independente, nao separa. Quem decide isso nao e a preferencia de ninguem — e o fato de
    existirem dois gabaritos e eles discordarem.
    """
    if not e11 or 'por_gabarito' not in e11:
        return None
    return {nome: bloco['pareada']['ic95'][0] > 0
            for nome, bloco in e11['por_gabarito'].items()}


def replicacao_depende_do_gabarito(e12):
    """No E12 a vantagem do Jev sobre QUATRO comparadores sobrevive aos gabaritos?

    O E11 fez a mesma pergunta com 20 familias e um comparador so, e a resposta dependeu do
    gabarito. O E12 repetiu com 30 familias e quatro comparadores de quatro fornecedores, e a
    resposta continuou dependendo: sob o meu gabarito e sob o oficial — adjudicado por um juiz
    cego que confirmou o meu em 10 de 10 — o Jev separa de zero contra todos; sob o gabarito do
    anotador independente, empata com o comparador de 8B e nao separa de mais dois.

    Devolve, por gabarito, se a leitura daquele gabarito foi de vantagem. Poder maior nao
    resolveu a divergencia: ela nao era falta de amostra, e a validade do rotulo.
    """
    if not e12 or 'leitura_por_gabarito' not in e12:
        return None
    return {nome: leitura == 'vantagem-do-jev'
            for nome, leitura in e12['leitura_por_gabarito'].items()}


def evidencia_dividida(e10, e10b):
    """A particao de teste e a analise ampliada discordam entre si?

    O E10b rodou o mesmo comparador nas 10 familias do piloto, sob emenda declarada. Em 20
    familias a vantagem do Jev separa de zero; nas 10 da particao de teste, nao. Esconder
    qualquer um dos dois lados seria escolher o resultado depois de ve-lo, e por isso o painel
    diz que esta dividida em vez de escolher.
    """
    if not (e10 and e10b):
        return False
    return comparador_empatou(e10) and not contem_zero(e10b['pareada_80_casos']['ic95'])


def titulo_do_veredito(e9, e10=None, e11=None, e12=None):
    """O titulo tambem precisa cair quando o dado cair.

    Antes era uma frase cravada recomendando o corte de 0,90. Se o E9 sumisse, ou se a
    politica passasse a deixar erro entre os aceitos, o titulo continuaria recomendando.
    """
    # Puro de proposito: o E11 chega por parametro. Quando esta funcao foi buscar o relatorio
    # sozinha, o teste da setima rodada — que a chama com dados fabricados — passou a receber o
    # veredito do repositorio em vez do veredito dos dados dele.
    # O E12 e a replicacao do E11 com 30 familias e quatro comparadores, e e ele que manda
    # enquanto existir: mesma pergunta, mais poder, mais fornecedores.
    replicou = replicacao_depende_do_gabarito(e12)
    if replicou:
        if not all(replicou.values()):
            return ('Com mais famílias e quatro comparadores, a vantagem do Jev continua '
                    'dependendo de quem escreveu o gabarito')
        return ('Vantagem do Jev sobre quatro LLMs econômicos sob todos os gabaritos')
    separa = desempate_depende_do_gabarito(e11)
    if separa:
        if separa.get('oficial'):
            return ('Vantagem do Jev sobre o LLM econômico no gabarito adjudicado, '
                    'com a validade do rótulo ainda em aberto')
        if not all(separa.values()):
            return 'A vantagem do Jev depende de quem escreveu o gabarito: o gargalo é o rótulo'
        return 'Vantagem do Jev sobre o LLM econômico sob todos os gabaritos'
    e10b = ler('e10b-piloto/relatorio.json')
    if evidencia_dividida(e10, e10b):
        return 'Evidência dividida sobre a necessidade do Jev: não decidir com este estudo'
    if comparador_empatou(e10):
        return 'Sem evidência de vantagem sobre um LLM econômico: não adotar ainda'
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


def texto_da_replicacao(e12, replicou):
    """O texto do veredito quando a replicacao existe. Calculado, nunca escrito a mao."""
    adj = ler('e12-replicacao/adjudicacao.json')
    oficial = e12['por_gabarito'].get('oficial') or e12['por_gabarito']['autor']
    outro = e12['por_gabarito'].get('anotador local')
    comparadores = e12['comparadores']
    faixa = [oficial['comparacoes'][c]['pareada']['diferenca_observada'] for c in comparadores]
    texto = (
        'A replicação foi feita e não mudou a natureza do problema, só o tamanho da amostra. Em '
        'corpus novo de ' + str(e12['casos_programados']) + ' casos e ' + str(e12['familias'])
        + ' famílias, declaradas antes de o primeiro caso ser escrito, contra **quatro** '
        'comparadores econômicos de quatro fornecedores, o Jev acerta '
        + pct(e12['resumo']['jev']['acuracia_sobre_programados']) + ' e supera todos eles no '
        'gabarito adjudicado, por ' + pct(min(faixa)) + ' a ' + pct(max(faixa))
        + ', com todos os IC95 acima de zero.')
    if adj:
        pl = adj['placar']
        texto += (' Os ' + str(len(adj['casos'])) + ' casos em que eu e o anotador independente '
                  'discordamos foram a um terceiro juiz cego, de outro fornecedor, que confirmou '
                  'meu gabarito em ' + str(pl['confirmam_o_autor']) + ' de '
                  + str(len(adj['casos'])) + '.')
    if outro and not all(replicou.values()):
        pior = min(outro['comparacoes'][c]['pareada']['diferenca_observada']
                   for c in comparadores)
        melhor = max(outro['comparacoes'][c]['pareada']['diferenca_observada']
                     for c in comparadores)
        texto += (' **Sob o gabarito do anotador independente, que é o único que não passou pela '
                  'minha mão, a mesma comparação vai de ' + pct(pior) + ' a ' + pct(melhor)
                  + ', e o intervalo contém zero contra mais de um comparador.** Era essa a '
                  'divergência que o E11 tinha encontrado com 20 famílias e um comparador só, e '
                  'que este experimento existia para resolver com mais poder. Ela não era falta '
                  'de amostra: triplicar as famílias e quadruplicar os comparadores não a moveu. '
                  'O que decide o resultado não é quanto se mede, é quem escreveu o rótulo — e '
                  'os três anotadores deste estudo continuam sendo modelos de linguagem.')
    return texto


def texto_do_veredito(e9, e6, e10=None, e11=None, e12=None):
    """O veredito e calculado, nao escrito a mao.

    Um texto fixo com numeros dentro continua afirmando o mesmo depois que os dados mudam: na
    execucao seguinte o placar mentiria sem que ninguem percebesse.
    """
    if not e9:
        return 'Sem a análise de política de aceitação, o placar não tem recomendação operacional.'
    replicou = replicacao_depende_do_gabarito(e12)
    if replicou:
        return texto_da_replicacao(e12, replicou)
    separa = desempate_depende_do_gabarito(e11)
    adj11 = ler('e11-desempate/adjudicacao.json')
    if separa and separa.get('oficial') and adj11:
        of = e11['por_gabarito']['oficial']
        outro = e11['por_gabarito']['anotador local']
        pl = adj11['placar']
        return (
            'O desempate foi feito e decidiu. Em corpus novo de '
            + str(e11['jev']['casos_programados']) + ' casos e '
            + str(of['pareada']['n_familias']) + ' famílias, com as famílias declaradas antes de '
            'o primeiro caso ser escrito, o Jev supera um LLM genérico e barato por '
            + pct(of['pareada']['diferenca_observada']) + ', IC95 ['
            + pct(of['pareada']['ic95'][0]) + '; ' + pct(of['pareada']['ic95'][1]) + '], McNemar '
            'exato p = ' + dec(of['mcnemar_p'], 4) + ', no gabarito adjudicado. O anotador '
            'independente discordava de mim em ' + str(len(adj11['casos'])) + ' casos e sob o '
            'gabarito dele a diferença era ' + pct(outro['pareada']['diferenca_observada'])
            + ' — mas esses ' + str(len(adj11['casos'])) + ' casos foram a um terceiro juiz '
            'cego, com as leituras em ordem sorteada, e ele confirmou meu gabarito em '
            + str(pl['confirmam_o_autor']) + ' de ' + str(len(adj11['casos']))
            + '. O que isto autoriza dizer é que o Jev vence este comparador neste corpus. O que '
            'continua sem resposta é se a rubrica mede o que diz medir: os três anotadores do '
            'estudo são modelos de linguagem, e nenhum deles é uma pessoa do atendimento real.')
    if separa and not all(separa.values()):
        autor = e11['por_gabarito']['autor']
        outro = e11['por_gabarito']['anotador local']
        return (
            'O desempate foi feito e desempatou para os dois lados, conforme o gabarito. Em '
            'corpus novo de ' + str(e11['jev']['casos_programados']) + ' casos e '
            + str(autor['pareada']['n_familias']) + ' famílias, pré-registrado antes de existir '
            'qualquer dado, o Jev acerta '
            + pct(e11['jev']['acuracia_sobre_programados']) + ' contra '
            + pct(e11['llm']['acuracia_sobre_programados']) + ' do comparador barato sob o meu '
            'gabarito: diferença ' + pct(autor['pareada']['diferenca_observada']) + ', IC95 ['
            + pct(autor['pareada']['ic95'][0]) + '; ' + pct(autor['pareada']['ic95'][1])
            + '], McNemar exato p = ' + dec(autor['mcnemar_p'], 4) + '. Sob o gabarito do '
            'anotador independente, que é o único que não passou pela minha mão, a mesma '
            'comparação dá ' + pct(outro['pareada']['diferenca_observada']) + ', IC95 ['
            + pct(outro['pareada']['ic95'][0]) + '; ' + pct(outro['pareada']['ic95'][1])
            + '] — contém zero, e o sinal inverte. O experimento que existia para desempatar '
            'mostrou onde está o gargalo, e não é a comparação entre os modelos: é a validade '
            'do rótulo. Enquanto o gabarito for meu, a vantagem é minha de encomenda; enquanto '
            'o único gabarito independente for um modelo de 7B, ele também não decide. O que '
            'falta não é mais uma execução — são dois anotadores humanos do domínio.')
    e10b = ler('e10b-piloto/relatorio.json')
    if evidencia_dividida(e10, e10b):
        par, amp = e10['pareada'], e10b['pareada_80_casos']
        pil = e10b['pareada_piloto']
        return (
            'O braço que faltava mudou a conclusão, e mudou para os dois lados. Um LLM genérico '
            'e barato (' + e10['modelo'] + ') recebeu as mesmas instruções congeladas do E1, sem '
            'nenhum ajuste de prompt. Na partição de confirmação, que é a de teste, a vantagem '
            'do Jev é de ' + pct(par['diferenca_observada']) + ' com IC95 ['
            + pct(par['ic95'][0]) + '; ' + pct(par['ic95'][1]) + ']: não separa de zero. No '
            'piloto é de ' + pct(pil['diferenca_observada']) + ' e separa; nos '
            + str(amp['n_familias']) + ' grupos das duas partições juntas é de '
            + pct(amp['diferenca_observada']) + ', IC95 [' + pct(amp['ic95'][0]) + '; '
            + pct(amp['ic95'][1]) + '], e também separa. A partição que existe para decidir é a '
            'que não separa, e a decisão de olhar o piloto foi tomada depois de ver esse '
            'resultado — então nenhum dos dois lados pode ser apresentado sozinho. O que os '
            'dados sustentam é isto: a evidência não basta para decidir se o Jev é necessário '
            'nesta tarefa, e o desempate custa US$ 0,0004 por conjunto de 40 casos.')
    if comparador_empatou(e10):
        par = e10['pareada']
        return (
            'O braço que faltava mudou a conclusão. Um LLM genérico e barato ('
            + e10['modelo'] + '), com as mesmas instruções congeladas e nos mesmos '
            + str(e10['llm']['casos_programados']) + ' casos da partição de confirmação, acerta '
            + pct(e10['llm']['acuracia_sobre_programados']) + ' contra '
            + pct(e10['jev']['acuracia_sobre_programados']) + ' do Jev. A diferença de '
            + pct(par['diferenca_observada']) + ' tem IC95 [' + pct(par['ic95'][0]) + '; '
            + pct(par['ic95'][1]) + '] por reamostragem de famílias, e esse intervalo contém '
            'zero. Os dois erram em lados diferentes de '
            + str(e10['mcnemar_discordancias']) + ' casos, todos a favor do Jev, o que no '
            'McNemar exato dá p = 0,25. Pela regra congelada no pré-registro do E10, isto é '
            'ausência de evidência de vantagem, não equivalência: com 10 famílias o poder é '
            'baixo por construção. O que cai não é o desempenho do Jev — é a afirmação de que '
            'ele é necessário aqui. Enquanto essa pergunta não for respondida com amostra maior, '
            'a recomendação é não adotar com base neste estudo.')
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
        # Recontado dos casos, nao lido do bloco agregado: a auditoria de mutacao da decima
        # terceira rodada trocou cinco acertos por erros neste relatorio e este cartao nao se
        # mexeu. O corpus do E3 nao passa pela adjudicacao, entao o gabarito e o do proprio
        # arquivo — mas a CONTAGEM tem de ser feita agora, como nos demais cartoes.
        bruto_e3 = gabarito.contagem_bruta('runs/e3-evidencia/relatorio.json', 'jev')
        bruto_regra = gabarito.contagem_bruta('runs/e3-evidencia/relatorio.json', 'regra')
        acuracia_e3 = bruto_e3['acuracia']
        programados_e3 = bruto_e3['casos_programados']
        regra_e3 = bruto_regra['acuracia']
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
                f"{adj['terceiro_juiz']}, cego a quem escreveu cada leitura; "
                + str(d80['casos_programados']) + ' casos adjudicados (E1 e E7). O anotador '
                'independente cobre também os ' + str(len(gabarito.do_anotador_local())
                                                      - d80['casos_programados'])
                + ' casos do E11, que não passaram por adjudicação'))
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

    e10 = ler('e10-llm-economico/relatorio.json')
    if e10:
        d10 = gabarito.desempenho('runs/e10-llm-economico/relatorio.json', 'llm')
        # O Jev deste cartao tambem e recontado do mesmo arquivo: ler
        # e10['jev']['acuracia_sobre_programados'] seria o agregado gravado quando o E10 rodou,
        # e a auditoria de mutacao mostrou que esse cartao nao se mexia com o dado.
        d10_jev = gabarito.desempenho('runs/e10-llm-economico/relatorio.json', 'jev')
        par10 = e10['pareada']
        cartoes.append(cartao(
            'e10', 'Comparador: LLM econômico (E10)', valor_entre_gabaritos(d10),
            ' · '.join(nome + ' ' + pct(v) for nome, v in
                       sorted(gabaritos_do_conjunto(d10).items(), key=lambda kv: kv[1]))
            + ' · Jev ' + valor_entre_gabaritos(d10_jev),
            ('O estudo inteiro comparou o Jev contra uma regra congelada que eu mesmo escrevi — '
             'o comparador mais fácil de vencer que existe. Aqui '
             + e10['modelo'] + ' recebe as MESMAS instruções e critérios do E1, nos mesmos '
             + str(d10['casos_programados']) + ' casos da partição de confirmação, sem '
             'nenhum ajuste de prompt. Diferença pareada ' + pct(par10['diferenca_observada'])
             + ', IC95 [' + pct(par10['ic95'][0]) + '; ' + pct(par10['ic95'][1]) + '] por '
             'reamostragem de famílias. Só o Jev acerta em '
             + str(len(e10['so_jev_acerta'])) + ' casos ('
             + ', '.join(e10['so_jev_acerta']) + '); só o comparador acerta em '
             + str(len(e10['so_llm_acerta'])) + '. '
             + ('O intervalo contém zero: pela regra congelada no pré-registro, isto é ausência '
                'de evidência de vantagem, e o veredito acima mudou por causa disto.'
                if comparador_empatou(e10) else
                'O intervalo não contém zero: a vantagem do Jev tem, agora, um comparador que '
                'não fui eu que escrevi.')
             + ' Respostas fora do contrato contaram como erro, nunca foram reexecutadas: '
             'houve ' + str(len(e10['respostas_invalidas'])) + '.'),
            fonte_com_gabarito(str(d10['casos_programados']) + ' casos da partição de '
                               'confirmação, max_tokens 64, temperatura 0', 'faixa')))

    e10b = ler('e10b-piloto/relatorio.json')
    if e10b:
        d10b = gabarito.desempenho('runs/e10b-piloto/relatorio.json', 'llm')
        d10b_jev = gabarito.desempenho('runs/e10b-piloto/relatorio.json', 'jev')
        amp, pil = e10b['pareada_80_casos'], e10b['pareada_piloto']
        cartoes.append(cartao(
            'e10b', 'Comparador no piloto (E10b)', valor_entre_gabaritos(d10b),
            ' · '.join(nome + ' ' + pct(v) for nome, v in
                       sorted(gabaritos_do_conjunto(d10b).items(), key=lambda kv: kv[1]))
            + ' · Jev ' + valor_entre_gabaritos(d10b_jev),
            ('Análise secundária, sob emenda declarada antes da execução: o mesmo comparador nas '
             '10 famílias do piloto, para dobrar o poder depois de o resultado primário ter '
             'tocado zero. Aqui a vantagem do Jev é de ' + pct(pil['diferenca_observada'])
             + ', IC95 [' + pct(pil['ic95'][0]) + '; ' + pct(pil['ic95'][1]) + '], e **separa** '
             'de zero; nas ' + str(amp['n_familias']) + ' famílias das duas partições juntas é '
             'de ' + pct(amp['diferenca_observada']) + ', IC95 [' + pct(amp['ic95'][0]) + '; '
             + pct(amp['ic95'][1]) + '], e também separa. A emenda declarava que o piloto havia '
             'guiado o desenho do prompt do Jev; fui conferir no histórico e isso não se '
             'sustenta — o prompt entrou uma vez e nunca mudou. Sobra o viés menor de a rubrica '
             'e o corpus piloto terem sido escritos juntos. Esta leitura não restabelece a '
             'recomendação: a decisão de olhar o piloto foi tomada depois de ver o resultado '
             'primário, e é por isso que o veredito diz que a evidência está dividida em vez de '
             'escolher o lado que me convém.'),
            fonte_com_gabarito(str(d10b['casos_programados']) + ' casos do piloto; '
                               + str(amp['n_familias']) + ' famílias na análise ampliada',
                               'faixa')))

    e11 = ler('e11-desempate/relatorio.json')
    if e11:
        d11 = gabarito.desempenho('runs/e11-desempate/relatorio.json', 'jev')
        d11c = gabarito.desempenho('runs/e11-desempate/relatorio.json', 'llm')
        pg = e11.get('por_gabarito') or {}
        autor, outro = pg.get('autor'), pg.get('anotador local')
        cartoes.append(cartao(
            'e11', 'Desempate em corpus novo (E11)', valor_entre_gabaritos(d11),
            ' · '.join(nome + ' ' + pct(v) for nome, v in
                       sorted(gabaritos_do_conjunto(d11).items(), key=lambda kv: kv[1]))
            + ' · comparador ' + valor_entre_gabaritos(d11c),
            ('Corpus novo de ' + str(d11['casos_programados']) + ' casos em 20 famílias, '
             'declaradas no pré-registro antes de o primeiro caso ser escrito, para resolver os '
             'dois defeitos que sobraram do E10 e do E10b: poder baixo e análise escolhida '
             'depois de ver a outra. '
             + ('Sob o meu gabarito o Jev acerta tudo — ' + str(d11['autor']['acertos']) + ' de '
                + str(d11['casos_programados']) + ' — e a diferença é '
                + pct(autor['pareada']['diferenca_observada']) + ', IC95 ['
                + pct(autor['pareada']['ic95'][0]) + '; ' + pct(autor['pareada']['ic95'][1])
                + '], p = ' + dec(autor['mcnemar_p'], 4) + '. **Sob o gabarito do anotador '
                'independente a diferença é ' + pct(outro['pareada']['diferenca_observada'])
                + ', IC95 [' + pct(outro['pareada']['ic95'][0]) + '; '
                + pct(outro['pareada']['ic95'][1]) + '], e o sinal inverte.** Acerto perfeito no '
                'conjunto que só eu revisei é sinal de alerta, não de vitória: foi por isso que '
                'o anotador independente foi rodado também aqui, depois do resultado, e é por '
                'isso que os dois números vão lado a lado.'
                if autor and outro else 'Análise por gabarito ainda não calculada.')),
            fonte_com_gabarito(str(d11['casos_programados']) + ' casos, 20 famílias, dois '
                               'braços na mesma lista e na mesma ordem; o Jev pelo endpoint de '
                               'decisões e o comparador por chat, o que é um viés de interface '
                               'que este estudo não separa do resto', 'faixa')))

    e12 = ler('e12-replicacao/relatorio.json')
    if e12:
        oficial = e12['por_gabarito'].get('oficial') or e12['por_gabarito']['autor']
        outro = e12['por_gabarito'].get('anotador local')
        comparadores = e12['comparadores']
        melhor_barato = min(comparadores,
                            key=lambda c: e12['custo'][c]['custo_por_mil_classificacoes_usd']
                            if e12['custo'].get(c) else float('inf'))
        linha_comparadores = ' · '.join(
            c + ' ' + pct(e12['resumo'][c]['acuracia_sobre_programados']) for c in comparadores)
        incompletos = e12.get('bracos_incompletos') or []
        leitura = ('A leitura pré-registrada é de interseção-união: só há vantagem se o IC95 '
                   'separar de zero contra **todos** os comparadores. No gabarito adjudicado ela '
                   'separa contra os quatro, de ' + pct(min(
                       oficial['comparacoes'][c]['pareada']['diferenca_observada']
                       for c in comparadores)) + ' a ' + pct(max(
                       oficial['comparacoes'][c]['pareada']['diferenca_observada']
                       for c in comparadores)) + '.')
        if outro:
            contem_zero_em = [c for c in comparadores
                              if not outro['comparacoes'][c]['separa_de_zero']]
            leitura += (' **Sob o gabarito do anotador independente ela não separa contra '
                        + str(len(contem_zero_em)) + ' dos ' + str(len(comparadores))
                        + '** (' + ', '.join(contem_zero_em) + '), e contra o comparador de 8B a '
                        'diferença é exatamente '
                        + pct(outro['comparacoes']['c1']['pareada']['diferenca_observada'])
                        + '. O E11 já tinha encontrado essa divergência com 20 famílias e um '
                        'comparador; triplicar as famílias e quadruplicar os comparadores não a '
                        'moveu, o que é a evidência mais forte deste estudo de que o gargalo é a '
                        'validade do rótulo e não o tamanho da amostra.')
        if incompletos:
            leitura += (' Braço(s) fora da leitura por cobertura abaixo de 90%, conforme a '
                        'Emenda 2: ' + ', '.join(incompletos) + '.')
        leitura += (' O mais barato dos comparadores custa US$ '
                    + dec(e12['custo'][melhor_barato]['custo_por_mil_classificacoes_usd'], 6)
                    + ' por mil classificações, contra US$ '
                    + dec(e12['custo']['jev']['custo_por_mil_classificacoes_usd'], 6)
                    + ' do Jev.')
        d12 = gabarito.desempenho('runs/e12-replicacao/relatorio.json', 'jev')
        cartoes.append(cartao(
            'e12', 'Replicação com quatro comparadores (E12)',
            # A politica do painel, desde a decima segunda rodada, e nunca estampar um gabarito
            # sozinho: o numero grande e a FAIXA entre os tres, e a comparacao abre quem e quem.
            valor_entre_gabaritos(d12),
            ' · '.join(nome + ' ' + pct(v) for nome, v in
                       sorted(gabaritos_do_conjunto(d12).items(), key=lambda kv: kv[1]))
            + ' · ' + linha_comparadores, leitura,
            fonte_com_gabarito(str(e12['casos_programados']) + ' casos em '
                               + str(e12['familias']) + ' famílias novas, cinco braços na mesma '
                               'lista e na mesma ordem; o Jev pelo endpoint de decisões e os '
                               'comparadores por chat, viés de interface que este estudo não '
                               'separa do resto', 'faixa')))

    grave = ler('erro-grave.json')
    if grave:
        # [R13] O pre-registro do E1 manda reportar erro grave SEPARADO da acuracia media, e
        # isso nunca tinha sido feito. Acuracia media trata todos os erros como iguais; a
        # classe `cancelar` dispara acao irreversivel. Zero observado nao e zero: o teto vem
        # junto, no mesmo cartao, porque e ele que diz o que a amostra nao consegue excluir.
        total_falsos = teto = 0.0
        conjuntos, falsos_regra, total_casos, casos_com_regra = [], 0, 0, 0
        for nome, bloco in grave['por_conjunto'].items():
            pior = max(bloco.values(), key=lambda b: len(b['jev']['falso_cancelar']))
            total_falsos += len(pior['jev']['falso_cancelar'])
            teto = max(teto, pior['jev']['limite_superior_por_familia'])
            total_casos += pior['jev']['casos']
            com_regra = [b for b in bloco.values() if 'regra' in b]
            if com_regra:
                falsos_regra += max(len(b['regra']['falso_cancelar']) for b in com_regra)
                casos_com_regra += pior['jev']['casos']
            conjuntos.append(f"{nome} {pior['jev']['casos']} casos")
        cartoes.append(cartao(
            'egrave', 'Erro grave: `cancelar` indevido',
            # O denominador era 80 cravado no texto: com os corpora novos ele mentia.
            str(int(total_falsos)) + ' em ' + str(total_casos) + ' casos',
            'regra congelada ' + str(falsos_regra) + ' em ' + str(casos_com_regra),
            ('Erro grave é responder `cancelar` onde o gabarito diz outra coisa: dispara ação '
             'irreversível no atendimento. O pré-registro do E1 mandava reportá-lo separado da '
             'acurácia média desde o início. O Jev cometeu ' + str(int(total_falsos))
             + ', **sob os três gabaritos**, nos ' + str(total_casos) + ' casos classificados do '
             'estudo. Zero observado não é zero verdadeiro: o limite superior de 95% é '
             + pct(teto) + ' por família. A regra congelada, onde existe comparação com ela, '
             'comete ' + str(falsos_regra) + ' em ' + str(casos_com_regra) + '.'),
            fonte_com_gabarito(' · '.join(conjuntos), 'faixa')))

    # O saldo vale o do relatorio mais recente que registrou a carteira.
    # [E10] A cadeia era fixa e comecava no E7: depois do E10 o painel continuaria publicando o
    # saldo anterior ao ultimo experimento. Agora vence o relatorio com o carimbo mais novo.
    candidatos = [r for r in (e12, e11, e10b, e10, e7, e6, e5, e4, e2b)
                  if r and r.get('wallet_committed_nusd')]
    carteira = max(candidatos, key=lambda r: r.get('at', '')) if candidatos else {}
    comprometido = carteira.get('wallet_committed_nusd') or carteira.get('ledger_committed_nusd')
    disponivel = carteira.get('wallet_available_nusd') or carteira.get('available_nusd')

    confianca = confianca_calculada(e9, e6, e8, adj, e12)
    bloco = {
        'atualizado_em': datetime.now(timezone.utc).isoformat(),
        'veredito': {
            'titulo': titulo_do_veredito(e9, e10, e11, e12),
            'texto': texto_do_veredito(e9, e6, e10, e11, e12),
            'confianca': confianca[0],
            'confianca_motivos': confianca[1],
            'confianca_nota': nota_de_confianca(adj, e9, e11, e12),
            'confianca_metodo': ('descontos declarados sobre 1,0; cada um com motivo em '
                                 'confianca_motivos. Os PESOS são arbítrio meu, não medida: '
                                 'o que a conta garante é que a nota se mexa quando o dado '
                                 'se mexe e que cada desconto seja contestável no código, '
                                 'não que 0,10 seja o preço certo de um corpus sintético'),
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
