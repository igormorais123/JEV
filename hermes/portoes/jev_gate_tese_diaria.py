#!/usr/bin/env python3
"""Porteiro do job "Tese - paragrafo diario" (8f2260d9fe4a), 11h.

O que o job fazia: o modelo caro acordava com a skill `research` inteira, procurava um artigo
recente (9 `web_search`, 21 `web_extract`, 19 `execute_code` na execução de 21/09) e escrevia
o parágrafo — 100 mil tokens de entrada por dia, 3,1 M em 30 dias, para um parágrafo.

O que o porteiro faz antes do agente, sem modelo caro:
1. Escolhe o pilar do dia (roda pelos quatro) e consulta Crossref e OpenAlex por termos do
   pilar, só 2024 em diante, com resumo.
2. Tira os DOIs que a wiki do doutorado já tem (`doutorado-wiki/notas`, campo `doi:`).
3. O Jev lê título e resumo de cada candidato contra a tese: pilar e aproveitamento
   (central, util, marginal). Só `central` ou `util` com confiança ≥ 0,70 sobem.
4. Acorda o agente com os 5 melhores já ordenados — DOI, título, autores, ano, revista,
   resumo, leitura do Jev — e a instrução de escolher um deles, confirmar no DOI e escrever.
   Sem candidato bom, o agente acorda como antes (procura sozinho), e o motivo fica no registro.

Falha para acordar: qualquer erro deixa o job como era.
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, '/root/.hermes/integrations/jev')
from jev_hermes import nucleo, portao  # noqa: E402

JOB = 'tese-diaria'
WIKI = Path('/root/.hermes/doutorado-wiki/notas')
CONTATO = 'igormorais123@gmail.com'
CORTE = 0.70
CANDIDATOS_NO_CONTEXTO = 5
ANO_MINIMO = 2024

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


def _baixar(url):
    pedido = urllib.request.Request(url, headers={'User-Agent': f'hermes-jev/1.0 (mailto:{CONTATO})'})
    with urllib.request.urlopen(pedido, timeout=25) as resposta:
        return json.loads(resposta.read().decode('utf-8'))


def _limpar(texto):
    return re.sub(r'<[^>]+>|\s+', lambda m: ' ' if m.group(0).isspace() else '', str(texto or '')).strip()


def crossref(consulta):
    url = ('https://api.crossref.org/works?' + urllib.parse.urlencode({
        'query': consulta, 'filter': f'from-pub-date:{ANO_MINIMO}-01-01,has-abstract:true', 'rows': 8,
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
        'per-page': 8, 'select': 'doi,title,publication_year,abstract_inverted_index,primary_location,authorships',
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


def coletar(pilar):
    vistos, candidatos = set(), []
    for consulta in PILARES[pilar]:
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


def contexto(pilar, escolhidos):
    linhas = [f'[jev/portão] Pilar do dia: {pilar}. Candidatos já coletados em Crossref e OpenAlex (2024 em '
              f'diante, fora da wiki), lidos pelo Jev contra a tese e ordenados. ESCOLHA UM DESTES: confirme a '
              f'referência abrindo só a página do DOI (web_extract em https://doi.org/DOI), escreva o parágrafo '
              f'e registre com wiki_add.py. Não faça web_search nem leia outras páginas: a busca já foi feita.']
    for i, c in enumerate(escolhidos, 1):
        j = c['jev']
        linhas.append(f"\n{i}. {c['titulo']} — {c['autores']} ({c['ano']}), {c['revista']}. DOI: {c['doi']}\n"
                      f"   Jev: pilar {j['pilar']} ({nucleo.dec(j['confianca_pilar'])}), aproveitamento "
                      f"{j['aproveitamento']} ({nucleo.dec(j['confianca'])}).\n   Resumo: {c['resumo'][:900]}")
    return '\n'.join(linhas)


def main():
    pilar = pilar_do_dia()
    candidatos = coletar(pilar)
    ja_na_wiki = dois_da_wiki()
    novos = [c for c in candidatos if c['doi'] not in ja_na_wiki]
    if not novos:
        portao.encerrar(JOB, True, f'sem candidato novo em {pilar}: o agente procura como antes',
                        pilar=pilar, coletados=len(candidatos))
        return
    estados = [f"TESE: {TESE}\n\nARTIGO ({c['ano']}, {c['revista']}): {c['titulo']}\nRESUMO: {c['resumo']}"
               for c in novos]
    resultados = nucleo.classificar_em_paralelo(estados, PERGUNTAS, origem='portao-tese-diaria',
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
        portao.encerrar(JOB, True, f'{len(novos)} candidato(s) novo(s), nenhum central ou útil: o agente procura como antes',
                        pilar=pilar, coletados=len(candidatos), novos=len(novos), custo_jev_usd=resumo['custo_usd'])
        return
    escolhidos = bons[:CANDIDATOS_NO_CONTEXTO]
    portao.encerrar(JOB, True, f'{len(bons)} candidato(s) bom(ns) de {len(novos)}; {len(escolhidos)} no contexto',
                    contexto=contexto(pilar, escolhidos), pilar=pilar, coletados=len(candidatos),
                    novos=len(novos), bons=len(bons), custo_jev_usd=resumo['custo_usd'],
                    dois=[c['doi'] for c in escolhidos])


if __name__ == '__main__':
    portao.executar(JOB, main)
