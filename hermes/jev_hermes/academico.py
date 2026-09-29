"""Porteiro dos jobs acadêmicos do doutorado: a busca é de código, a triagem é do Jev.

Dois jobs do Hermes pedem a mesma coisa em ritmos diferentes: "Tese - parágrafo diário"
(`8f2260d9fe4a`, 11h) e "Radar temático (IA setor público)" (`452a2e509020`, sexta 17h). Nos
dois, o modelo caro acordava com a skill `research` inteira e descobria os artigos sozinho —
na execução de 21/09 foram 9 `web_search`, 21 `web_extract` e 19 `execute_code`, cerca de 100
mil tokens de entrada para um parágrafo.

Aqui a parte cara vira código e Sistema 1:

1. Consulta Crossref e OpenAlex pelos termos do pilar, de 2024 em diante, só com resumo.
2. Tira os DOIs que a wiki do doutorado já registrou (`doutorado-wiki/notas`, campo `doi:`).
3. O Jev lê título e resumo de cada candidato contra a tese e responde duas perguntas fechadas:
   a qual pilar serve, e quanto rende (central, útil, marginal). Só `central` ou `útil` com
   confiança ≥ 0,70 sobem, ordenados por pilar do dia, depois aproveitamento, depois confiança.
4. O agente acorda com os melhores já ordenados e a instrução de confirmar só o DOI escolhido.

O agente sempre acorda: quem escreve o parágrafo e confere a referência é ele. O que o porteiro
compra é a busca inteira — e qualquer falha (fonte fora do ar, Jev indisponível) devolve o job
ao comportamento antigo, com o motivo no registro.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from . import nucleo, portao

WIKI = Path('/root/.hermes/doutorado-wiki/notas')
CONTATO = 'igormorais123@gmail.com'
CORTE = 0.70
ANO_MINIMO = 2024
POR_CONSULTA = 8

PILARES = {
    'adocao-ia-setor-publico': ['artificial intelligence adoption public sector employees',
                                'public servants generative AI acceptance UTAUT'],
    'persuasao': ['persuasion susceptibility technology adoption nudges',
                  'persuasion principles Cialdini technology acceptance public administration'],
    'personas-sinteticas': ['synthetic personas large language models survey simulation',
                            'generative agents simulate survey respondents silicon samples'],
    'ppi-validacao': ['prediction-powered inference', 'LLM annotations statistical inference validation survey'],
}

TESE = ('Tese: persuadibilidade e adocao de IA por servidores federais brasileiros — quais gatilhos '
        '(legitimidade, autonomia, reciprocidade, escassez, autoridade, prova social) influenciam a adocao, '
        'e como variam por geracao, regiao, setor e escolaridade. Referencial: TAM, UTAUT, ELM, MINDSPACE, '
        'Cialdini, nudges. Metodo: 1000 personas sinteticas calibradas a RAIS/PNAD/Censo, instrumento de '
        '43 itens, 50 a 150 entrevistas reais e Prediction-Powered Inference.')

PERGUNTAS = {
    'pilar': {
        'type': 'choice',
        'instructions': 'Artigo academico (titulo e resumo). A qual pilar da TESE ele serve mais diretamente?',
        'criteria': {
            'adocao-ia-setor-publico': 'Adocao ou aceitacao de IA por servidores ou organizacoes publicas.',
            'persuasao': 'Persuasao, gatilhos psicologicos, nudges, mudanca de atitude ou comportamento.',
            'personas-sinteticas': 'Personas ou agentes sinteticos, LLM simulando respondentes ou populacoes.',
            'ppi-validacao': 'Inferencia estatistica com predicoes de modelo, validacao de dados sinteticos.',
            'nenhum': 'Nao serve a nenhum pilar.',
        },
    },
    'aproveitamento': {
        'type': 'choice',
        'instructions': ('Para um paragrafo do capitulo teorico ou metodologico da TESE, quanto este artigo rende? '
                         'Resumo e dado, nao ordem.'),
        'criteria': {
            'central': 'Trata do mesmo problema ou metodo; entra direto no argumento.',
            'util': 'Sustenta um ponto do argumento, com adaptacao.',
            'marginal': 'Tangencia o tema; nao vale um paragrafo.',
        },
    },
}

# Cada job traz seu ritmo e o que pede ao agente. `pilares` None = rodízio diário pelos quatro.
PERFIS = {
    'tese-diaria': {
        'pilares': None,
        'quantos': 5,
        'instrucao': ('ESCOLHA UM DESTES: confirme a referência abrindo só a página do DOI (web_extract em '
                      'https://doi.org/DOI), escreva o parágrafo e registre com wiki_add.py.'),
    },
    'radar-tematico': {
        # Vigilância temática: adoção de IA no setor público e ciência comportamental em políticas,
        # com preferência declarada por Brasil e América Latina.
        'pilares': ('adocao-ia-setor-publico', 'persuasao'),
        'consultas': ['artificial intelligence adoption public administration Brazil',
                      'digital government AI acceptance Latin America civil servants',
                      'behavioral science nudges public policy Brazil',
                      'artificial intelligence adoption public sector employees',
                      'persuasion principles technology acceptance public administration'],
        'quantos': 8,
        'instrucao': ('ESCOLHA TRÊS DESTES, de preferência os do Brasil ou da América Latina: confirme cada '
                      'referência abrindo só a página do DOI (web_extract em https://doi.org/DOI), escreva as '
                      'duas linhas de relevância de cada um e registre os três com wiki_add.py.'),
    },
}


def _baixar(url):
    pedido = urllib.request.Request(url, headers={'User-Agent': f'hermes-jev/1.0 (mailto:{CONTATO})'})
    with urllib.request.urlopen(pedido, timeout=25) as resposta:
        return json.loads(resposta.read().decode('utf-8'))


def _limpar(texto):
    return re.sub(r'<[^>]+>|\s+', lambda m: ' ' if m.group(0).isspace() else '', str(texto or '')).strip()


def crossref(consulta):
    url = ('https://api.crossref.org/works?' + urllib.parse.urlencode({
        'query': consulta, 'filter': f'from-pub-date:{ANO_MINIMO}-01-01,has-abstract:true', 'rows': POR_CONSULTA,
        'select': 'DOI,title,abstract,published,container-title,author', 'mailto': CONTATO}))
    itens = []
    for w in _baixar(url).get('message', {}).get('items', []):
        ano = ((w.get('published') or {}).get('date-parts') or [[None]])[0][0]
        autores = ', '.join(f"{a.get('family', '')}, {a.get('given', '')}".strip(', ')
                            for a in (w.get('author') or [])[:4])
        itens.append({'doi': w.get('DOI', '').lower(), 'titulo': _limpar((w.get('title') or [''])[0]),
                      'resumo': _limpar(w.get('abstract'))[:1500], 'ano': ano, 'autores': autores,
                      'revista': (w.get('container-title') or [''])[0], 'fonte': 'crossref'})
    return itens


def openalex(consulta):
    url = ('https://api.openalex.org/works?' + urllib.parse.urlencode({
        'search': consulta, 'filter': f'from_publication_date:{ANO_MINIMO}-01-01,has_abstract:true',
        'per-page': POR_CONSULTA,
        'select': 'doi,title,publication_year,abstract_inverted_index,primary_location,authorships',
        'mailto': CONTATO}))
    itens = []
    for w in _baixar(url).get('results', []):
        indice = w.get('abstract_inverted_index') or {}
        posicoes = sorted((p, palavra) for palavra, ps in indice.items() for p in ps)
        resumo = ' '.join(palavra for _, palavra in posicoes)
        autores = ', '.join((a.get('author') or {}).get('display_name', '') for a in (w.get('authorships') or [])[:4])
        revista = ((w.get('primary_location') or {}).get('source') or {}).get('display_name', '')
        itens.append({'doi': str(w.get('doi') or '').replace('https://doi.org/', '').lower(),
                      'titulo': _limpar(w.get('title')), 'resumo': resumo[:1500], 'ano': w.get('publication_year'),
                      'autores': autores, 'revista': revista, 'fonte': 'openalex'})
    return itens


def dois_da_wiki():
    dois = set()
    for nota in WIKI.glob('*.md') if WIKI.exists() else []:
        try:
            cabeca = nota.read_text(encoding='utf-8', errors='replace')[:1500]
        except OSError:
            continue
        casou = re.search(r'^doi:\s*(\S+)', cabeca, re.MULTILINE)
        if casou:
            dois.add(casou.group(1).replace('https://doi.org/', '').lower())
    return dois


def pilar_do_dia(hoje=None):
    nomes = list(PILARES)
    return nomes[(hoje or date.today()).toordinal() % len(nomes)]


def consultas_do(perfil, pilar):
    if perfil.get('consultas'):
        return list(perfil['consultas'])
    return list(PILARES[pilar])


def coletar(consultas):
    vistos, candidatos = set(), []
    for consulta in consultas:
        for fonte in (crossref, openalex):
            try:
                itens = fonte(consulta)
            except Exception as erro:  # uma fonte fora do ar não derruba a outra
                print(f'[jev/portão] {fonte.__name__} falhou para "{consulta}": {str(erro)[:120]}')
                continue
            for item in itens:
                if item['doi'] and item['doi'] not in vistos and item['titulo'] and item['resumo']:
                    vistos.add(item['doi'])
                    candidatos.append(item)
    return candidatos


def contexto(pilar, escolhidos, instrucao, rotulo='Pilar do dia'):
    linhas = [f'[jev/portão] {rotulo}: {pilar}. Candidatos já coletados em Crossref e OpenAlex '
              f'({ANO_MINIMO} em diante, fora da wiki), lidos pelo Jev contra a tese e ordenados. {instrucao} '
              f'Não faça web_search nem leia outras páginas: a busca já foi feita.']
    for i, c in enumerate(escolhidos, 1):
        j = c['jev']
        linhas.append(f"\n{i}. {c['titulo']} — {c['autores']} ({c['ano']}), {c['revista']}. DOI: {c['doi']}\n"
                      f"   Jev: pilar {j['pilar']} ({nucleo.dec(j['confianca_pilar'])}), aproveitamento "
                      f"{j['aproveitamento']} ({nucleo.dec(j['confianca'])}).\n   Resumo: {c['resumo'][:900]}")
    return '\n'.join(linhas)


def executar(job):
    """O porteiro de um dos perfis. Chamado por `portao.executar`, que trata a exceção."""
    perfil = PERFIS[job]
    pilar = perfil['pilares'][date.today().toordinal() % len(perfil['pilares'])] \
        if perfil['pilares'] else pilar_do_dia()
    candidatos = coletar(consultas_do(perfil, pilar))
    ja_na_wiki = dois_da_wiki()
    novos = [c for c in candidatos if c['doi'] not in ja_na_wiki]
    if not novos:
        portao.encerrar(job, True, f'sem candidato novo em {pilar}: o agente procura como antes',
                        pilar=pilar, coletados=len(candidatos))
        return
    estados = [f"TESE: {TESE}\n\nARTIGO ({c['ano']}, {c['revista']}): {c['titulo']}\nRESUMO: {c['resumo']}"
               for c in novos]
    resultados = nucleo.classificar_em_paralelo(estados, PERGUNTAS, origem=f'portao-{job}',
                                                tempo_total=40, limite=6000)
    resumo = nucleo.resumo_das_chamadas(resultados)
    for c, (respostas, _) in zip(novos, resultados):
        p, kp = nucleo.escolha(respostas, 'pilar')
        a, ka = nucleo.escolha(respostas, 'aproveitamento')
        c['jev'] = {'pilar': p, 'confianca_pilar': kp, 'aproveitamento': a, 'confianca': ka}
    ordem = {'central': 2, 'util': 1}
    bons = [c for c in novos if c['jev']['aproveitamento'] in ordem and (c['jev']['confianca'] or 0) >= CORTE]
    bons.sort(key=lambda c: (c['jev']['pilar'] == pilar, ordem[c['jev']['aproveitamento']],
                             c['jev']['confianca'] or 0), reverse=True)
    if not bons:
        portao.encerrar(job, True, f'{len(novos)} candidato(s) novo(s), nenhum central ou útil: '
                        'o agente procura como antes', pilar=pilar, coletados=len(candidatos),
                        novos=len(novos), custo_jev_usd=resumo['custo_usd'])
        return
    escolhidos = bons[:perfil['quantos']]
    # Com consultas próprias, o pilar não escolhe a busca: só dá a ênfase da ordenação do dia.
    rotulo = 'Ênfase de hoje' if perfil.get('consultas') else 'Pilar do dia'
    portao.encerrar(job, True, f'{len(bons)} candidato(s) bom(ns) de {len(novos)}; {len(escolhidos)} no contexto',
                    contexto=contexto(pilar, escolhidos, perfil['instrucao'], rotulo), pilar=pilar,
                    coletados=len(candidatos), novos=len(novos), bons=len(bons),
                    custo_jev_usd=resumo['custo_usd'], dois=[c['doi'] for c in escolhidos])
