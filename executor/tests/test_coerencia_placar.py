"""O placar não pode se contradizer.

A oitava rodada de revisão encontrou o painel publicando dois números para a mesma decisão: o
veredito citava 87,5% em 40 casos da confirmação e o cartão do E9, no mesmo JSON, citava 80% em
80 casos da união. Os dois estavam certos e os dois eram a mesma recomendação.

Este teste roda `montar()` contra os relatórios REAIS do repositório — não contra dicionários
fabricados — e exige que o painel escolha uma leitura e a use inteira.
"""
import json
import re
import unittest
from pathlib import Path

from executor import placar

ROOT = Path(__file__).resolve().parents[2]


def tem_relatorios():
    return all((ROOT / 'runs' / nome / 'relatorio.json').exists()
               for nome in ('e7-confirmacao', 'e9-prevalencia', 'e8-anotador'))


@unittest.skipUnless(tem_relatorios(), 'requer os relatórios de execução')
def veredito_recomenda_corte(bloco):
    """O veredito mudou de assunto?

    [E10] Estes testes exigem que cobertura e custo saiam da mesma partição — e faziam sentido
    enquanto o veredito era a política de corte. Depois que o braço do LLM econômico não separou
    de zero, o veredito passou a ser "não adotar ainda", e não cita cobertura nenhuma. Exigir a
    frase antiga transformaria o teste num impedimento a mudar de conclusão, que é o oposto do
    que ele existe para proteger.
    """
    return 'corte de confiança' in bloco['veredito']['titulo'].lower()


class CoerenciaDoPlacar(unittest.TestCase):
    def setUp(self):
        self.bloco = placar.montar()
        self.cartoes = {c['chave']: c for c in self.bloco['cartoes']}

    def numeros(self, texto):
        return set(re.findall(r'\d+[.,]?\d*', texto))

    def test_veredito_e_cartao_e9_citam_a_mesma_cobertura(self):
        if not veredito_recomenda_corte(self.bloco):
            self.skipTest('o veredito não recomenda corte: não há cobertura a conferir')
        veredito = self.bloco['veredito']['texto']
        cartao = self.cartoes['e9']['leitura']
        e9 = json.loads((ROOT / 'runs/e9-prevalencia/relatorio.json').read_text(encoding='utf-8'))
        politica = placar.politica_de_referencia(e9)
        self.assertIsNotNone(politica, 'sem partição de confirmação não há política de referência')
        cobertura = f"{politica['cobertura'] * 100:.1f}".replace('.', ',')
        self.assertIn(cobertura, veredito)
        self.assertIn(cobertura, cartao)
        self.assertIn(str(politica['casos']), veredito)
        self.assertIn(str(politica['casos']), cartao)

    def test_custo_do_veredito_sai_da_mesma_particao_da_cobertura(self):
        """A quimera da décima rodada: 87,5% de cobertura com o preço de quem cobre 80%.

        Custo por decisão depende da fração enviada a revisão humana, que é justamente o que a
        cobertura mede. Misturar as duas partições promete uma política que não existe em
        relatório nenhum.
        """
        if not veredito_recomenda_corte(self.bloco):
            self.skipTest('o veredito não recomenda corte: não há custo de política a conferir')
        e9 = json.loads((ROOT / 'runs/e9-prevalencia/relatorio.json').read_text(encoding='utf-8'))
        politica = placar.politica_de_referencia(e9)
        tudo = placar.politica_de_referencia(e9, corte=1.01)
        self.assertIsNotNone(tudo, 'a partição precisa da política de revisar tudo para comparar')
        veredito = self.bloco['veredito']['texto']
        self.assertIn(f"{politica['custo_por_decisao_usd']:.3f}".replace('.', ','), veredito)
        self.assertIn(f"{tudo['custo_por_decisao_usd']:.3f}".replace('.', ','), veredito)
        uniao = next(p for p in e9['politicas_de_aceitacao'] if p['corte'] == 0.90)
        if abs(uniao['custo_por_decisao_usd'] - politica['custo_por_decisao_usd']) > 1e-9:
            self.assertNotIn(f"{uniao['custo_por_decisao_usd']:.3f}".replace('.', ','), veredito,
                             'o custo da união não pode aparecer junto da cobertura da confirmação')

    def test_rotulo_de_corpus_pergunta_pela_divergencia_entre_anotadores(self):
        """O rótulo dizia "coincidem" no piloto, que tem quatro casos em disputa.

        Ele perguntava se a adjudicação mudou algum caso — outra coisa. Enquanto o terceiro
        juiz confirmasse o autor, o corpus inteiro parecia unânime.
        """
        from executor import gabarito
        local, autor = gabarito.do_anotador_local(), gabarito.do_autor()
        divergem = [c for c, r in local.items()
                    if c.startswith('tri-') and c in autor and r != autor[c]['gold']]
        rotulo = placar.gabarito_do_corpus('tri-')
        if divergem:
            self.assertEqual(rotulo, 'ha-divergencia',
                             f'{len(divergem)} casos em disputa no piloto e o rótulo diz outra coisa')
        else:
            self.assertEqual(rotulo, 'coincidem')

    def test_cartao_do_gabarito_mostra_a_faixa_entre_os_tres(self):
        """O E8 estampava 96,2%, o mais alto dos três gabaritos."""
        # [E11] O relatorio do E8 passou a cobrir 140 casos, porque o anotador independente
        # rodou tambem no corpus do desempate. O cartao continua falando dos 80 ADJUDICADOS, que
        # sao os unicos com terceiro juiz. Comparar o cartao com o agregado do E8 passou a
        # comparar escopos diferentes: aqui a conta e refeita sobre os 80.
        from executor import gabarito
        d80 = gabarito.desempenho_do_estudo()
        valor = self.cartoes['e8']['valor']
        self.assertIn(' a ', valor)
        self.assertIn(f"{d80['anotador_local']['acuracia'] * 100:.1f}".replace('.', ','), valor)

    def test_politica_de_referencia_nao_cai_para_a_uniao(self):
        """Sem a partição, o painel tem de ficar em silêncio, não trocar o número."""
        e9 = {'politicas_de_aceitacao': [{'corte': 0.90, 'cobertura': 0.8, 'casos': 80,
                                          'erros_entre_aceitos': 0}]}
        self.assertIsNone(placar.politica_de_referencia(e9))

    def test_cartao_do_gabarito_adjudicado_declara_o_gabarito(self):
        cartao = self.cartoes.get('e8')
        self.assertIsNotNone(cartao, 'o cartão do gabarito adjudicado sumiu')
        self.assertIn('oficial', cartao['comparacao'].lower())

    def test_cartao_de_concordancia_diz_que_usa_o_gabarito_do_autor(self):
        cartao = self.cartoes['e8b']
        self.assertIn('GABARITO DO AUTOR', cartao['leitura'])

    def test_nota_de_confianca_usa_a_base_da_politica_recomendada(self):
        """A nota justificava o corte com 80 casos enquanto o veredito falava de 40.

        Justificar uma decisão com um denominador que o próprio painel recusou é pior do que
        não justificar: dá aparência de base maior do que a que existe.
        """
        nota = self.bloco['veredito']['confianca_nota']
        e9 = json.loads((ROOT / 'runs/e9-prevalencia/relatorio.json').read_text(encoding='utf-8'))
        if not veredito_recomenda_corte(self.bloco):
            # [E11] Quando o veredito deixa de recomendar um corte, a nota tem de deixar de
            # justificar um corte. Exigir a frase antiga obrigaria a nota a defender uma
            # recomendacao que o painel nao faz mais — que e o defeito que este teste nasceu
            # para impedir, so que ao contrario.
            self.assertNotIn('o corte de 0,90 é sustentado', nota,
                             'a nota justifica um corte que o veredito não recomenda')
            return
        politica = placar.politica_de_referencia(e9)
        self.assertIn(f"{politica['casos']} casos da partição de confirmação", nota)
        adj = json.loads((ROOT / 'runs/e8-anotador/adjudicacao.json').read_text(encoding='utf-8'))
        erros = len(adj['gabarito_adjudicado']['erros'])
        self.assertIn(f'erra {erros} de', nota)
        # O painel e em pt-BR: numero com virgula, sempre.
        self.assertNotIn('.5%', self.bloco['veredito']['texto'])

    def test_cartoes_mostram_a_faixa_entre_TODOS_os_gabaritos(self):
        """O olho pega o número de capa; ele tem de conter o pior gabarito, não só o melhor.

        Por seis rodadas o painel ensinou três gabaritos no cartão do E8 e mostrou dois nos
        cartões que se lê primeiro — deixando de fora justamente o mais severo.
        """
        from executor import gabarito
        for chave, relatorio in (('e1', 'runs/e1-triagem/relatorio.json'),
                                 ('e7', 'runs/e7-confirmacao/relatorio.json')):
            d = gabarito.desempenho(relatorio)
            valores = placar.gabaritos_do_conjunto(d)
            self.assertIn('anotador local', valores,
                          'o gabarito do anotador independente tem de entrar na conta')
            valor = self.cartoes[chave]['valor']
            if len(set(valores.values())) > 1:
                self.assertIn(' a ', valor)
                baixo = f"{min(valores.values()) * 100:.1f}".replace('.', ',')
                self.assertIn(baixo, valor, f'{chave} esconde o pior gabarito')
            comparacao = self.cartoes[chave]['comparacao']
            for nome in valores:
                self.assertIn(nome, comparacao)

    def test_pendencias_nao_pedem_o_que_ja_foi_feito(self):
        texto = ' '.join(self.bloco['pendencias']).lower()
        self.assertNotIn('adjudicação dos casos', texto)
        self.assertIn('pessoas do atendimento real', texto)

    def test_e9_usa_o_gabarito_oficial(self):
        e9 = json.loads((ROOT / 'runs/e9-prevalencia/relatorio.json').read_text(encoding='utf-8'))
        self.assertTrue(e9['procedencia_do_gabarito']['adjudicado'])
        adj = json.loads((ROOT / 'runs/e8-anotador/adjudicacao.json').read_text(encoding='utf-8'))
        erros_oficiais = len(adj['gabarito_adjudicado']['erros'])
        tudo = next(p for p in e9['politicas_de_aceitacao'] if p['corte'] == 0.0)
        self.assertEqual(tudo['erros_entre_aceitos'], erros_oficiais)


class ConfiancaCalculada(unittest.TestCase):
    """A confiança era um número digitado, e número digitado não cai quando o dado piora."""

    def test_erro_entre_aceitos_derruba_a_confianca(self):
        e9 = {'por_particao': {'confirmacao (teste)': {'politicas': [
            {'corte': 0.90, 'casos': 40, 'erros_entre_aceitos': 0}]}}}
        limpo, _ = placar.confianca_calculada(e9, None, None, {'x': 1})
        e9_ruim = {'por_particao': {'confirmacao (teste)': {'politicas': [
            {'corte': 0.90, 'casos': 40, 'erros_entre_aceitos': 2}]}}}
        sujo, motivos = placar.confianca_calculada(e9_ruim, None, None, {'x': 1})
        self.assertLess(sujo, limpo)
        self.assertTrue(any('erro' in m for m in motivos))

    def test_sem_particao_de_teste_a_confianca_cai_mais(self):
        sem, motivos = placar.confianca_calculada(None, None, None, None)
        self.assertLessEqual(sem, 0.5)
        self.assertTrue(any('sem partição' in m for m in motivos))

    def test_cada_desconto_tem_motivo(self):
        valor, motivos = placar.confianca_calculada(
            {'por_particao': {'confirmacao (teste)': {'politicas': [
                {'corte': 0.90, 'casos': 40, 'erros_entre_aceitos': 0}]}}},
            {'n_instaveis': 1, 'casos': 40, 'repeticoes': 5}, None, {'x': 1})
        # [R13] Este teste cravava "4 motivos, valor 0,5", e por isso reprovou quando a revisão
        # adversarial acrescentou dois descontos legítimos. Contagem fixa não é invariante: o
        # que tem de valer é que TODO desconto apareça na lista e que a soma feche com a nota.
        self.assertTrue(motivos, 'nota abaixo de 1,0 sem nenhum motivo declarado')
        descontos = [float(re.search(r'-0,(\d+)\)', m).group(1)) / 100
                     for m in motivos if re.search(r'-0,(\d+)\)', m)]
        self.assertEqual(len(descontos), len(motivos),
                         'algum motivo não declara quanto descontou')
        self.assertAlmostEqual(valor, round(1.0 - sum(descontos), 2), places=2,
                               msg='a nota não é a soma dos descontos que ela declara')


class GabaritoOficial(unittest.TestCase):
    def test_adjudicacao_substitui_apenas_o_que_mudou(self):
        from executor import gabarito
        autor = gabarito.do_autor()
        oficial, procedencia = gabarito.adjudicado()
        if not procedencia['adjudicado']:
            self.skipTest('sem adjudicação no repositório')
        mudados = {c['case_id'] for c in procedencia['casos_substituidos']}
        for case_id, entrada in oficial.items():
            if case_id not in mudados:
                self.assertEqual(entrada['gold'], autor[case_id]['gold'], case_id)

    def test_rotulo_distingue_com_e_sem_adjudicacao(self):
        from executor import gabarito
        self.assertIn('sem adjudicação', gabarito.rotulo({'adjudicado': False}))
        self.assertIn('adjudicado', gabarito.rotulo({'adjudicado': True, 'casos_substituidos': []}))


if __name__ == '__main__':
    unittest.main()


@unittest.skipUnless(tem_relatorios(), 'requer os relatórios de execução')
class PainelPublicadoEhReproduzivel(unittest.TestCase):
    """O que está no ar tem que ser o que os relatórios produzem.

    Sem isto, uma edição manual em `lab/data/execution.json` passaria despercebida, e o painel
    poderia afirmar algo que nenhum experimento sustenta.
    """

    def test_bloco_publicado_bate_com_o_gerado(self):
        publicado = json.loads(
            (ROOT / 'lab/data/execution.json').read_text(encoding='utf-8')).get('decision')
        self.assertIsNotNone(publicado, 'o painel está sem placar de decisão')
        gerado = placar.montar()
        for campo in ('veredito', 'cartoes', 'pendencias', 'orcamento'):
            self.assertEqual(publicado[campo], gerado[campo],
                             f'{campo} publicado difere do que os relatórios geram')

    def test_custo_somado_no_painel_fecha_com_o_ledger(self):
        """O painel cobre os experimentos do dossiê; o ledger passou a cobrir mais que isso.

        Desde que laboratório (E14) e roteador liquidam no mesmo livro-caixa, o total do ledger
        inclui `shared-*`, que o painel do dossiê nunca publicou. Comparar os dois totais
        acusava uma divergência real mas inócua e escondia a que importa: uma edição manual em
        `lab/data/execution.json`. A comparação passa a ser contra as tentativas cujo
        `attempt_id` o próprio painel declara.
        """
        import sqlite3
        estado = json.loads((ROOT / 'lab/data/execution.json').read_text(encoding='utf-8'))
        publicadas = {a['id']: a['cost_usd'] or 0
                      for r in estado['runs'] for a in r['attempts']}
        caminho = ROOT / 'runs' / 'ledger.sqlite3'
        if not caminho.exists():
            self.skipTest('sem ledger')
        db = sqlite3.connect(str(caminho))
        try:
            linhas = db.execute(
                'SELECT attempt_id, COALESCE(CASE WHEN settled_nusd IS NULL THEN reserved_nusd'
                ' ELSE settled_nusd END, 0) FROM attempt_budget').fetchall()
        finally:
            db.close()
        no_ledger = {identificador: valor / 1e9 for identificador, valor in linhas}
        ausentes = [i for i in publicadas if i not in no_ledger]
        self.assertFalse(ausentes, f'o painel publica tentativa que o ledger não tem: {ausentes[:3]}')
        self.assertAlmostEqual(sum(publicadas.values()),
                               sum(no_ledger[i] for i in publicadas), places=9)


class FaixaDosTresGabaritos(unittest.TestCase):
    """[R11] A faixa do E8 era um máximo disfarçado.

    Ela fazia min(local, autor) a max(oficial, autor): dava certo só porque o oficial é, hoje,
    o mais alto. Se o anotador local passasse o oficial, o teto sumia do intervalo.
    """

    @staticmethod
    def desempenho(local=None, autor=0.90, oficial=0.95):
        d = {'autor': {'acuracia': autor}, 'oficial': {'acuracia': oficial}}
        if local is not None:
            d['anotador_local'] = {'acuracia': local}
        return d

    def test_faixa_cobre_os_tres_mesmo_com_o_local_no_topo(self):
        faixa, valores = placar.faixa_dos_gabaritos(
            self.desempenho(local=0.99, autor=0.90, oficial=0.95))
        self.assertEqual(set(valores.values()), {0.99, 0.90, 0.95})
        self.assertIn('99,0%', faixa)
        self.assertIn('90,0%', faixa)

    def test_faixa_vira_valor_unico_quando_todos_coincidem(self):
        faixa, _ = placar.faixa_dos_gabaritos(
            self.desempenho(local=0.95, autor=0.95, oficial=0.95))
        self.assertNotIn(' a ', faixa)

    def test_sem_anotador_local_a_faixa_usa_os_dois_que_existem(self):
        _, valores = placar.faixa_dos_gabaritos(self.desempenho(local=None))
        self.assertNotIn('anotador local', valores)
        self.assertEqual(set(valores), {'autor', 'oficial'})

    def test_a_funcao_e_pura_e_nao_consulta_o_repositorio(self):
        """[R13] Se ela for buscar o dado sozinha, os testes acima param de testar a regra."""
        valores = placar.faixa_dos_gabaritos(self.desempenho(local=0.10, autor=0.20))[1]
        self.assertEqual(valores['anotador local'], 0.10)


@unittest.skipUnless(tem_relatorios(), 'requer os relatórios de execução')
class RelatorioFinalBateComOsDados(unittest.TestCase):
    """O markdown também é uma superfície do painel, e já afirmou uma faixa que não existia."""

    def test_faixa_citada_no_relatorio_existe_nos_dados(self):
        from executor import gabarito
        _, valores = placar.faixa_dos_gabaritos(gabarito.desempenho_do_estudo())
        texto = (ROOT / 'docs/RELATORIO-FINAL-JEV.md').read_text(encoding='utf-8')
        baixo = f'{min(valores.values())}'.replace('.', ',')
        alto = f'{max(valores.values())}'.replace('.', ',')
        self.assertIn(f'{baixo} a {alto}', texto)
        # Nenhum numero fora da lista pode ser apresentado como extremo da faixa.
        for proibido in ('0,9750 a', 'a 0,9750'):
            ocorrencias = texto.count(proibido)
            self.assertEqual(ocorrencias, 0, f'{proibido} aparece {ocorrencias} vez(es)')


@unittest.skipUnless(tem_relatorios(), 'requer os relatórios de execução')
class PainelEmPortugues(unittest.TestCase):
    """O painel é lido por quem fala português; o texto e o número têm de ser em português."""

    PALAVRAS_SEM_ACENTO = re.compile(
        r'\b(nao|sao|decisao|particao|confianca|acuracia|familia|familias|criterio|numero|'
        r'analise|politica|revisao|confirmacao|aceitacao|adjudicacao)\b')

    def setUp(self):
        self.bloco = placar.montar()

    def textos(self):
        yield self.bloco['veredito']['titulo']
        yield self.bloco['veredito']['texto']
        yield self.bloco['veredito']['confianca_nota']
        for motivo in self.bloco['veredito'].get('confianca_motivos', []):
            yield motivo
        for pendencia in self.bloco['pendencias']:
            yield pendencia
        for c in self.bloco['cartoes']:
            for campo in ('titulo', 'valor', 'comparacao', 'leitura', 'fonte'):
                yield c[campo]

    def test_nenhum_texto_perde_acento(self):
        faltas = [t for t in self.textos() if self.PALAVRAS_SEM_ACENTO.search(t)]
        self.assertEqual(faltas, [], 'texto em português sem acentuação')

    def test_nenhum_percentual_com_ponto_decimal(self):
        faltas = [t for t in self.textos() if re.search(r'\d\.\d+\s*%', t)]
        self.assertEqual(faltas, [], 'percentual com ponto decimal num painel em português')


def test_cartao_e8_reage_a_mudanca_no_gabarito_do_anotador_local():
    """Décima terceira rodada: teste de mutação.

    Os cartões do E1 e do E7 recalculam a acurácia sob os três gabaritos. O do E8 lia dois
    números agregados gravados dentro do próprio relatório do E8 no momento em que ele rodou.
    Mutar as anotações do anotador local movia E1 e E7 e deixava o E8 parado, exibindo um valor
    que já não correspondia aos dados. Um painel que não se mexe quando o dado muda não está
    medindo o dado.
    """
    import importlib
    import json
    import shutil
    import tempfile

    from executor import gabarito, placar

    origem = ROOT / 'runs' / 'e8-anotador' / 'relatorio.json'
    if not origem.exists():
        raise unittest.SkipTest('E8 ainda não executado')
    copia = Path(tempfile.mkdtemp()) / 'relatorio.json'
    shutil.copy(origem, copia)

    def cartao(chave):
        return next(c for c in placar.montar()['cartoes'] if c['chave'] == chave)

    try:
        antes = {c: cartao(c) for c in ('e1', 'e7', 'e8')}
        dados = json.loads(origem.read_text(encoding='utf-8'))
        autor = gabarito.do_autor()
        mexidos = 0
        for anotacao in dados['anotacoes']:
            caso = anotacao['case_id']
            if caso in autor and anotacao.get('anotador'):
                if anotacao['anotador'] != autor[caso]['gold']:
                    anotacao['anotador'] = autor[caso]['gold']
                    mexidos += 1
        assert mexidos, 'sem divergência para mutar: o teste perderia o sentido'
        origem.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
        importlib.reload(gabarito)
        importlib.reload(placar)
        for chave in ('e1', 'e7', 'e8'):
            assert cartao(chave) != antes[chave], (
                f'o cartão {chave} não reagiu à mudança no gabarito do anotador local')
    finally:
        shutil.copy(copia, origem)
        importlib.reload(gabarito)
        importlib.reload(placar)


@unittest.skipUnless((ROOT / 'runs' / 'extrato-ledger.json').exists(), 'extrato ainda não gerado')
class ExtratoPublicadoConfereComOPainel(unittest.TestCase):
    """[R13] O custo publicado tem de ser conferível por quem clona o repositório.

    `runs/ledger.sqlite3` é ignorado pelo Git. Enquanto o único registro do gasto fosse o banco
    local, o "US$ 0,018174462" do relatório era uma citação, não uma reprodução. O extrato
    versionado fecha isso — e este teste garante que ele não se descole do painel.
    """

    def extrato(self):
        return json.loads((ROOT / 'runs' / 'extrato-ledger.json').read_text(encoding='utf-8'))

    def test_total_do_extrato_bate_com_o_orcamento_do_painel(self):
        orcamento = placar.montar().get('orcamento')
        if not orcamento:
            self.skipTest('painel sem bloco de orçamento')
        self.assertEqual(self.extrato()['comprometido_nusd'],
                         orcamento['comprometido_nusd'],
                         'o extrato versionado e o painel discordam sobre o gasto')

    def test_soma_das_linhas_bate_com_o_total_declarado(self):
        extrato = self.extrato()
        soma = sum(linha['settled_nusd'] or 0 for linha in extrato['linhas'])
        self.assertEqual(soma, extrato['comprometido_nusd'],
                         'o total do extrato não é a soma das suas próprias linhas')

    def test_extrato_nao_carrega_segredo(self):
        texto = (ROOT / 'runs' / 'extrato-ledger.json').read_text(encoding='utf-8')
        for padrao in (r'sk-[A-Za-z0-9_-]{10,}', r'Bearer\s+\S+', r'api[_-]?key'):
            self.assertIsNone(re.search(padrao, texto, re.I),
                              f'o extrato publicado casa com {padrao}')

    def test_nenhuma_reserva_pendente_sem_liquidacao(self):
        self.assertEqual(self.extrato()['reservas_pendentes_sem_liquidacao'], 0)


@unittest.skipUnless((ROOT / 'runs' / 'extrato-ledger.json').exists(), 'extrato ainda não gerado')
class ReadmeNaoContradizOsDados(unittest.TestCase):
    """[R13] O README dizia "nove rodadas" quando o relatório já dizia treze.

    É a mesma classe de defeito que as rodadas 9 a 13 passaram a caçar: duas superfícies do
    mesmo estudo com denominadores diferentes. A superfície que mais gente lê primeiro era a que
    estava mais desatualizada.
    """

    def test_readme_cita_o_gasto_do_extrato(self):
        extrato = json.loads(
            (ROOT / 'runs' / 'extrato-ledger.json').read_text(encoding='utf-8'))
        texto = (ROOT / 'README.md').read_text(encoding='utf-8')
        valor = f"{extrato['comprometido_usd']:.9f}"
        self.assertTrue(valor in texto or valor.replace('.', ',') in texto,
                        f'o README não cita o gasto real ({valor})')
        # O README e escrito em pt-BR, onde 1474 se escreve 1.474. Exigir so a forma crua
        # obrigaria o documento a errar a propria lingua para agradar o teste.
        tentativas = str(extrato['tentativas'])
        com_separador = f"{extrato['tentativas']:,}".replace(',', '.')
        self.assertTrue(tentativas in texto or com_separador in texto,
                        'o README não cita o número real de tentativas')

    def test_readme_e_relatorio_concordam_sobre_as_rodadas_de_revisao(self):
        numeros = {'nove': 9, 'dez': 10, 'onze': 11, 'doze': 12, 'treze': 13, 'quatorze': 14,
                   'catorze': 14, 'quinze': 15, 'dezesseis': 16, 'dezessete': 17,
                   'dezoito': 18, 'dezenove': 19, 'vinte': 20}
        def rodadas(caminho):
            texto = (ROOT / caminho).read_text(encoding='utf-8').lower()
            achados = {v for k, v in numeros.items()
                       if re.search(rf'\b{k} rodadas de revis', texto)}
            return achados
        no_readme = rodadas('README.md')
        no_relatorio = rodadas('docs/RELATORIO-FINAL-JEV.md')
        if not no_readme or not no_relatorio:
            self.skipTest('um dos documentos não declara o número de rodadas')
        self.assertEqual(no_readme, no_relatorio,
                         f'README diz {no_readme} rodadas e o relatório diz {no_relatorio}')


class OrfasNaoSeApagam(unittest.TestCase):
    """[E11] O run de tentativas órfãs se substituía e perdia o que já tinha.

    Ele é reconstruído do zero a cada publicação, mas contava a si mesmo como "já publicado".
    Na passagem seguinte, as órfãs antigas apareciam como publicadas, o run saía só com as
    novas, e as antigas sumiam do painel — 16 chamadas do E4 e 3 sondagens, US$ 0,000649, que
    voltaram a fazer o custo do painel divergir do livro-caixa depois de a oitava rodada ter
    fechado exatamente isso.
    """

    def test_republicar_duas_vezes_nao_perde_orfas(self):
        from executor import publicar_experimentos as pub
        estado = json.loads((ROOT / 'lab/data/execution.json').read_text(encoding='utf-8'))
        primeiro = pub.tentativas_orfas_run(estado, 'agora')
        if not primeiro:
            self.skipTest('sem tentativas órfãs no ledger')
        estado_depois = dict(estado)
        estado_depois['runs'] = [r for r in estado['runs']
                                 if r['id'] != primeiro['id']] + [primeiro]
        segundo = pub.tentativas_orfas_run(estado_depois, 'agora')
        self.assertIsNotNone(segundo, 'a segunda passagem devolveu nada e apagaria as órfãs')
        self.assertEqual({a['id'] for a in primeiro['attempts']},
                         {a['id'] for a in segundo['attempts']},
                         'republicar mudou o conjunto de tentativas órfãs')


@unittest.skipUnless((ROOT / 'runs' / 'extrato-ledger.json').exists(), 'extrato ainda não gerado')
class NumeroVelhoNaoSobrevive(unittest.TestCase):
    """[R14] O número certo aparecer não impede o errado de continuar ali.

    O teste anterior exigia que o gasto do extrato fosse citado, e ele era. Só que "625 chamadas,
    US$ 0,018174462" continuava escrito na seção 7, na seção 9 e no primeiro parágrafo do README,
    de execuções anteriores. Os dois números conviviam e a suíte passava. O mesmo valia para o
    kappa: o relatório publicava 0,8593, dos 80 casos, enquanto o arquivo vivo já dizia 0,8301
    sobre 140.
    """

    DOCUMENTOS = ('docs/RELATORIO-FINAL-JEV.md', 'README.md')

    def texto(self):
        return '\n'.join((ROOT / d).read_text(encoding='utf-8') for d in self.DOCUMENTOS)

    def test_nenhum_gasto_antigo_sobrevive_nos_documentos(self):
        extrato = json.loads(
            (ROOT / 'runs' / 'extrato-ledger.json').read_text(encoding='utf-8'))
        atual = f"{extrato['comprometido_usd']:.9f}"
        texto = self.texto()
        # Só os valores que se apresentam como o TOTAL do estudo. Custo de um experimento
        # isolado (US$ 0,000702 do E10, US$ 0,001923295 do incidente do E11) é histórico
        # legítimo e tem de continuar publicado.
        contextos = (r'US\$ (0[.,]\d{6,9}) (?:comprometidos|no total|de\s+US\$ 5)',
                     r'(?:chamadas reais, |Custo total:\*\* )US\$ (0[.,]\d{6,9})',
                     r'US\$ (0[.,]\d{6,9})\s+em \d+ chamadas')
        achados = {m for padrao in contextos for m in re.findall(padrao, texto)}
        self.assertTrue(achados, 'nenhum total de gasto encontrado nos documentos')
        for achado in achados:
            with self.subTest(valor=achado):
                self.assertAlmostEqual(
                    float(achado.replace(',', '.')), extrato['comprometido_usd'], places=9,
                    msg=f'{achado} é publicado como total e o real é US$ {atual}')

    def test_o_kappa_publicado_e_o_do_arquivo_vivo(self):
        caminho = ROOT / 'runs' / 'e8-anotador' / 'relatorio.json'
        if not caminho.exists():
            self.skipTest('E8 ainda não executado')
        e8 = json.loads(caminho.read_text(encoding='utf-8'))
        texto = self.texto()
        atual = f"{e8['kappa_cohen']:.4f}".replace('.', ',')
        for achado in set(re.findall(r'kappa de (\d,\d{4})', texto)):
            with self.subTest(kappa=achado):
                self.assertEqual(achado, atual,
                                 f'o relatório publica kappa {achado} e o arquivo diz {atual}')


@unittest.skipUnless((ROOT / 'runs' / 'e11-desempate' / 'relatorio.json').exists(),
                     'E11 ainda não executado')
class ErroGraveNaoEIndependenteDoGabarito(unittest.TestCase):
    """[R15] O relatório afirmava que o erro grave era a métrica que não dependia do gabarito.

    Não era. O único falso-`cancelar` do comparador no E11 é `dsp-d03-01`, que está entre os 10
    casos em disputa — sob o gabarito do anotador independente ele acerta e o erro grave some. A
    frase ancorava a conclusão num caso que o parágrafo seguinte declarava contestado, e nenhum
    teste podia pegá-la porque o erro grave só era calculado sob um gabarito.
    """

    def relatorio(self):
        return json.loads(
            (ROOT / 'runs/e11-desempate/relatorio.json').read_text(encoding='utf-8'))

    def test_o_erro_grave_do_e11_e_reportado_sob_os_tres_gabaritos(self):
        bloco = self.relatorio().get('erro_grave') or {}
        self.assertEqual(set(bloco), {'autor', 'oficial', 'anotador local'},
                         'o erro grave do E11 não cobre os três gabaritos')
        for nome, por_campo in bloco.items():
            with self.subTest(gabarito=nome):
                self.assertEqual(set(por_campo), {'jev', 'llm'})

    def test_o_relatorio_nao_afirma_independencia_do_gabarito(self):
        texto = (ROOT / 'docs/RELATORIO-FINAL-JEV.md').read_text(encoding='utf-8')
        self.assertNotIn('É a única métrica do E11 em que a\n'
                         'diferença não depende do gabarito', texto,
                         'a afirmação derrubada na 15ª rodada voltou ao documento')
        self.assertIn('não depende do gabarito"*. **Não é.**', texto,
                      'a retificação da 15ª rodada sumiu do documento')

    def test_o_jev_nao_comete_erro_grave_em_nenhum_gabarito(self):
        for nome, por_campo in (self.relatorio().get('erro_grave') or {}).items():
            with self.subTest(gabarito=nome):
                self.assertEqual(por_campo['jev']['falso_cancelar'], [],
                                 f'o Jev comete erro grave sob o gabarito {nome} e o relatório '
                                 'afirma que não comete sob nenhum')


class DocumentoNaoArgumentaRecomendacaoAnterior(unittest.TestCase):
    """[R15] A quinta recomendação foi grampeada num relatório que ainda argumentava a quarta.

    A seção 1 dizia que o Jev vence no gabarito adjudicado enquanto a 3.10 se intitulava "por que
    ele não desempatou" e fechava com "o relatório não fecha a favor de ninguém". O leitor que
    chegasse lá encontrava a conclusão anterior, defendida, sem nada dizendo que fora superada.
    """

    FRASES_APOSENTADAS = ('e por que ele não desempatou',
                          'o relatório não fecha a favor de ninguém',
                          'esta amostra não separar os dois')

    def test_nenhuma_frase_da_recomendacao_anterior_sobrevive(self):
        texto = (ROOT / 'docs/RELATORIO-FINAL-JEV.md').read_text(encoding='utf-8')
        for frase in self.FRASES_APOSENTADAS:
            with self.subTest(frase=frase):
                self.assertNotIn(frase, texto,
                                 f'"{frase}" é da recomendação anterior e continua no documento')
