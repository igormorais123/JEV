"""A camada de conhecimento do mapa: os conceitos do estudo como nós do grafo.

Os arquivos dizem onde as coisas estão; os conceitos dizem do que o estudo trata. São seis tipos:
experimento (E1–E16), rodada do laboratório (R0–R27), hipótese (H001–H100), pergunta estratégica
(Q001–Q100), sistema avaliado (S01–S15) e revisão adversarial ([R1]–[R16] nos comentários, que não é
rodada). Cada conceito é lido da fonte que o define — o JSON das cem hipóteses, o documento das cem
perguntas, o pré-registro do laboratório, a tabela do protocolo, a docstring do executor — e nunca
inventado: conceito sem fonte não entra.

Arestas que saem daqui: arquivo → conceito (`define`, `executa`, `resultado`, `testa`, `menciona`, com
peso = número de menções) e conceito → conceito (`apoia-se em`), extraídas do texto que cada conceito
usa como evidência.
"""
from __future__ import annotations

import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import PurePosixPath

TIPOS = {
    'E': ('experimento', 'mapa/conhecimento/experimentos.md'),
    'R': ('rodada', 'mapa/conhecimento/rodadas.md'),
    'H': ('hipótese', 'mapa/conhecimento/hipoteses.md'),
    'Q': ('pergunta', 'mapa/conhecimento/perguntas.md'),
    'S': ('sistema', 'mapa/conhecimento/sistemas.md'),
    'V': ('revisão', 'mapa/conhecimento/revisoes.md'),
}

# E13 e E14 não têm executor próprio: moram em pastas inteiras.
EXPERIMENTOS_SEM_EXECUTOR = {
    'E13': 'Integração com tráfego real do Igor: amostragem, gabaritos e relatórios agregados (integracao/avaliacao/).',
    'E14': 'Programa de rodadas do laboratório, R0 a R27 (laboratorio/).',
}

RE_E = re.compile(r'(?<![\w/.-])E(1[0-6]|[1-9])(b?)(?![\w-])')
RE_R_FAIXA = re.compile(r'(?<![\w\[/.-])R(\d{1,2})(b?)\s*(?:[-–]|a|e)\s*R(\d{1,2})(?![\w\]])')
RE_R = re.compile(r'(?<![\w\[/.-])R(\d{1,2})(b?)(?![\w\]-])')
RE_REV = re.compile(r'\[R(\d{1,2})\]|revis[aã]o\s+(?:n[ºo.]\s*)?(\d{1,2})\b|test_achados_revisao(\d*)\.py', re.I)
RE_H = re.compile(r'(?<![\w])H(\d{3})(?![\w])')
RE_Q = re.compile(r'(?<![\w])Q(\d{3})(?![\w])')
RE_S = re.compile(r'(?<![\w])S(0[1-9]|1[0-5])(?![\w])')


def tipo_de(cid: str) -> str:
    return cid[0]


def pagina(cid: str) -> str:
    return TIPOS[tipo_de(cid)][1]


def ancora(cid: str) -> str:
    return cid.lower()


def ids_no_texto(texto: str, existentes: set[str], com_revisoes: bool = True) -> Counter:
    """Conta as menções a conceitos existentes. `[R13]` é revisão, não rodada."""
    achados = Counter()
    for m in RE_E.finditer(texto):
        achados[f'E{m.group(1)}{m.group(2)}'] += 1
    for m in RE_R_FAIXA.finditer(texto):
        ini, fim = int(m.group(1)), int(m.group(3))
        if 0 <= fim - ini <= 10:
            for n in range(ini, fim + 1):
                achados[f'R{n}'] += 1
    for m in RE_R.finditer(texto):
        achados[f'R{int(m.group(1))}{m.group(2)}'] += 1
    for m in RE_H.finditer(texto):
        achados[f'H{m.group(1)}'] += 1
    for m in RE_Q.finditer(texto):
        achados[f'Q{m.group(1)}'] += 1
    for m in RE_S.finditer(texto):
        achados[f'S{m.group(1)}'] += 1
    if com_revisoes:
        for m in RE_REV.finditer(texto):
            n = m.group(1) or m.group(2) or (m.group(3) if m.group(3) is not None else None)
            if n is not None:
                achados[f'V{int(n) if n else 1}'] += 1
    return Counter({k: v for k, v in achados.items() if k in existentes})


def primeira_frase(texto: str, limite: int = 220) -> str:
    texto = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', ' '.join(texto.split())).replace('|', '/')
    return texto if len(texto) <= limite else texto[:limite - 1].rstrip() + '…'


def linha_de(texto: str, trecho: str) -> int | None:
    pos = texto.find(trecho)
    return texto[:pos].count('\n') + 1 if pos >= 0 else None


def corpos_decorados(texto: str, decorador: str) -> dict[str, tuple[int, str]]:
    """{id: (linha, corpo)} para cada função marcada com @decorador('ID')."""
    marcas = [(m.group(1), m.start()) for m in re.finditer(rf"@{decorador}\('(\w+)'\)", texto)]
    saida = {}
    for i, (cid, ini) in enumerate(marcas):
        fim = marcas[i + 1][1] if i + 1 < len(marcas) else len(texto)
        saida[cid] = (texto[:ini].count('\n') + 1, texto[ini:fim])
    return saida


def refs_de_rodada_no_codigo(corpo: str) -> set[str]:
    """Rodadas que um corpo de função usa: artefatos rNN-*.json e ajudantes _rNN()."""
    refs = set()
    for m in re.finditer(r"\br(\d{1,2})(b?)(?:-r(\d{1,2}))?[-_][\w-]*\.json|\b_r(\d{1,2})(b?)\(", corpo):
        if m.group(1):
            ini, fim = int(m.group(1)), int(m.group(3) or m.group(1))
            refs.add(f'R{ini}{m.group(2)}')
            refs.update(f'R{n}' for n in range(ini + 1, fim + 1))
        else:
            refs.add(f'R{int(m.group(4))}{m.group(5)}')
    return refs


def extrair(nos: dict, textos: dict) -> dict:
    conceitos: dict[str, dict] = {}
    arestas: dict[tuple[str, str, str], int] = {}  # (de, para, tipo) -> peso

    def ligar(de, para, tipo, peso=1):
        if de != para:
            arestas[(de, para, tipo)] = arestas.get((de, para, tipo), 0) + peso

    def novo(cid, titulo, **atributos):
        conceitos.setdefault(cid, {'id': cid, 'tipo': TIPOS[tipo_de(cid)][0], 'titulo': titulo,
                                   'pagina': pagina(cid), 'atributos': {}, 'definido_em': []})
        conceitos[cid]['atributos'].update({k: v for k, v in atributos.items() if v not in (None, '', [])})
        return conceitos[cid]

    def definido(cid, arquivo, linha=None, papel='define'):
        if cid in conceitos and arquivo in nos:
            conceitos[cid]['definido_em'].append({'arquivo': arquivo, 'linha': linha, 'papel': papel})
            ligar(arquivo, cid, papel)

    # ---- experimentos: executor, pré-registro, resultados
    for c in nos:
        nome = PurePosixPath(c).name
        m = re.match(r'(?:run|adjudicar)_e(\d+)(b?)[_.]', nome)
        if m and c.startswith('executor/'):
            cid = f'E{int(m.group(1))}{m.group(2)}'
            doc = nos[c]['descricao']
            titulo = re.sub(rf'^{cid}\b[\s:,—–-]*', '', doc).strip() or doc
            if nome.startswith('run_'):
                novo(cid, titulo[:1].upper() + titulo[1:])
    for cid, titulo in EXPERIMENTOS_SEM_EXECUTOR.items():
        novo(cid, titulo)
    for c in nos:
        nome = PurePosixPath(c).name
        m = re.match(r'(run|adjudicar)_e(\d+)(b?)[_.]', nome)
        if m and c.startswith('executor/'):
            definido(f'E{int(m.group(2))}{m.group(3)}', c, papel='executa' if m.group(1) == 'run' else 'adjudica')
        m = re.match(r'(preregistro|emenda)-E(\d+)(b?)-', nome)
        if m:
            cid = f'E{int(m.group(2))}{m.group(3)}'
            definido(cid, c, 1, 'pré-registra' if m.group(1) == 'preregistro' else 'emenda')
            if m.group(1) == 'preregistro' and cid in conceitos:
                emendas = re.findall(r'^# (Emenda[^\n]*)', textos[c], re.M)
                conceitos[cid]['atributos']['emendas'] = emendas
        m = re.match(r'runs/e(\d+)(b?)-[^/]+/(.+)', c)
        if m:
            definido(f'E{int(m.group(1))}{m.group(2)}', c, papel='resultado')
        m = re.match(r'test_(?:e|calibracao_e)(\d+)(b?)[_.]', nome)
        if m:
            definido(f'E{int(m.group(1))}{m.group(2)}', c, papel='testa')
    if 'integracao/README.md' in nos:
        definido('E13', 'integracao/README.md', papel='define')
    if 'laboratorio/PREREGISTRO.md' in nos:
        definido('E14', 'laboratorio/PREREGISTRO.md', 1, 'pré-registra')

    # ---- rodadas: seções do pré-registro do laboratório, scripts e artefatos
    prereg = textos.get('laboratorio/PREREGISTRO.md', '')
    secoes = [(m.start(), m.group(1), m.group(2)) for m in re.finditer(r'^##+ (R\d+b?(?:\s*(?:e|,|–|-)\s*R\d+b?)*)\s+—\s+(.+)$', prereg, re.M)]
    texto_da_secao = {}
    for i, (ini, rotulo, titulo) in enumerate(secoes):
        fim = secoes[i + 1][0] if i + 1 < len(secoes) else len(prereg)
        linha = prereg[:ini].count('\n') + 1
        for r in re.findall(r'R(\d+)(b?)', rotulo):
            cid = f'R{int(r[0])}{r[1]}'
            existente = cid in conceitos
            c_ = novo(cid, titulo.strip() if not existente else conceitos[cid]['titulo'])
            c_['atributos'].setdefault('secoes', []).append({'linha': linha, 'titulo': titulo.strip()})
            texto_da_secao[cid] = texto_da_secao.get(cid, '') + prereg[ini:fim]
            if not existente:
                c_['definido_em'].append({'arquivo': 'laboratorio/PREREGISTRO.md', 'linha': linha, 'papel': 'pré-registra'})
    for c in nos:
        nome = PurePosixPath(c).name
        if not c.startswith('laboratorio/') or '/' in c[len('laboratorio/'):]:
            continue
        m = re.match(r'r(\d+)(b?)(?:[-_]r(\d+))?[-_]', nome)
        if not m:
            continue
        ini = int(m.group(1))
        fim = int(m.group(3)) if m.group(3) else ini
        for n in range(ini, fim + 1):
            cid = f'R{n}{m.group(2) if n == ini else ""}'
            if cid not in conceitos:
                novo(cid, nos[c]['descricao'] if c.endswith('.py') else f'Rodada {cid}')
            definido(cid, c, papel='executa' if c.endswith('.py') else 'resultado')
    for cdef in conceitos.values():
        if cdef['titulo'].startswith('Rodada '):
            script = next((d['arquivo'] for d in cdef['definido_em'] if d['papel'] == 'executa'), None)
            if script:
                cdef['titulo'] = re.sub(r'^R\d+b?\s*[—–:-]\s*', '', nos[script]['descricao'])
    if 'laboratorio/PREREGISTRO.md' in nos:
        for cid in texto_da_secao:
            ligar('laboratorio/PREREGISTRO.md', cid, 'pré-registra')
    try:
        retr = json.loads(textos.get('laboratorio/retratacoes.json', '') or '{}').get('retratadas', [])
    except ValueError:
        retr = []
    for item in retr:
        m = re.match(r'r(\d+)(b?)[-_]', item.get('artefato', ''))
        if m and f'R{int(m.group(1))}{m.group(2)}' in conceitos:
            conceitos[f'R{int(m.group(1))}{m.group(2)}']['atributos'].setdefault('retratacoes', []).append(
                f"{', '.join(item.get('condicoes', []))} ({item.get('em', '')}): {primeira_frase(item.get('motivo', ''), 200)}")

    # ---- hipóteses: o JSON de resultados é a fonte; provas.py e registro.py definem
    try:
        h100 = json.loads(textos.get('laboratorio/h100-resultados.json', '') or '{}').get('resultados', [])
    except ValueError:
        h100 = []
    for h in h100:
        novo(h['id'], h['enunciado'], familia=h.get('familia'), veredito=h.get('veredito'), medido=h.get('medido'),
             previsao=h.get('previsao'), criterio=h.get('criterio'), fonte=h.get('fonte'), natureza=h.get('natureza'),
             detalhe=primeira_frase(h.get('detalhe', ''), 300))
        definido(h['id'], 'laboratorio/h100-resultados.json', papel='resultado')
    provas = corpos_decorados(textos.get('laboratorio/h100/provas.py', ''), 'prova')
    for cid, (linha, corpo) in provas.items():
        if cid in conceitos:
            definido(cid, 'laboratorio/h100/provas.py', linha, 'prova')
            for r in refs_de_rodada_no_codigo(corpo) | set(ids_no_texto(corpo, set(conceitos), False)):
                if r in conceitos and r != cid:
                    ligar(cid, r, 'apoia-se em')
    reg = textos.get('laboratorio/h100/registro.py', '')
    for m in re.finditer(r'^\s+H\((\d+),', reg, re.M):
        cid = f'H{int(m.group(1)):03d}'
        if cid in conceitos:
            definido(cid, 'laboratorio/h100/registro.py', reg[:m.start()].count('\n') + 2, 'registra')
    try:
        arvore = ast.parse(reg)
        for no in arvore.body:
            if isinstance(no, ast.Assign) and any(getattr(t, 'id', '') == 'EMENDAS' for t in no.targets):
                for emenda in ast.literal_eval(no.value):
                    for cid in emenda.get('atinge', []):
                        if cid in conceitos:
                            conceitos[cid]['atributos'].setdefault('emendas', []).append(
                                f"{emenda.get('em', '')}: {emenda.get('o_que', '')}")
    except (SyntaxError, ValueError):
        pass
    for h in h100:
        for r in ids_no_texto(' '.join(str(h.get(k, '')) for k in ('fonte', 'criterio', 'detalhe', 'previsao')), set(conceitos), False):
            if r != h['id']:
                ligar(h['id'], r, 'apoia-se em')
    doc_h = textos.get('docs/CEM-HIPOTESES.md', '')
    for cid in list(conceitos):
        if cid.startswith('H'):
            linha = linha_de(doc_h, f'| `{cid}` |')
            if linha:
                definido(cid, 'docs/CEM-HIPOTESES.md', linha, 'documenta')

    # ---- perguntas: o documento traz pergunta, resposta e de onde vem a resposta
    doc_q = textos.get('docs/CEM-PERGUNTAS-ESTRATEGICAS.md', '')
    familia = None
    blocos = re.split(r'\n(?=### |\*\*Q\d{3} — )', doc_q)
    posicao = 0
    for bloco in blocos:
        inicio = doc_q.find(bloco, posicao)
        posicao = max(inicio, posicao)
        mf = re.match(r'### ([A-J]) · (.+)', bloco)
        if mf:
            familia = f'{mf.group(1)} · {mf.group(2).strip()}'
            continue
        mq = re.match(r'\*\*(Q\d{3}) — (.+?)\*\*', bloco)
        if not mq:
            continue
        cid = mq.group(1)
        paragrafos = [p.strip() for p in bloco.split('\n\n')[1:] if p.strip()]
        italico = lambda p: p.startswith('*') and not p.startswith('**')  # a resposta pode abrir em negrito
        resposta = next((p for p in paragrafos if not italico(p)), '')
        meta = next((p.strip('*') for p in paragrafos if italico(p) and 'Fonte:' in p), '')
        mfonte = re.search(r'Fonte: ([^;]+); confiança ([a-zé]+)', meta)
        novo(cid, mq.group(2).strip(), familia=familia, resposta=primeira_frase(resposta, 320),
             fonte_da_resposta=mfonte.group(1) if mfonte else None, confianca=mfonte.group(2) if mfonte else None,
             decide=primeira_frase(meta.split('Fonte:')[0], 200) if meta else None)
        definido(cid, 'docs/CEM-PERGUNTAS-ESTRATEGICAS.md', doc_q[:inicio].count('\n') + 2, 'documenta')
        for r in ids_no_texto(resposta + ' ' + meta, set(conceitos) | {f'Q{n:03d}' for n in range(1, 101)}, False):
            if r != cid:
                ligar(cid, r, 'apoia-se em')
    respostas = corpos_decorados(textos.get('laboratorio/q100/respostas.py', ''), 'resposta')
    for cid, (linha, corpo) in respostas.items():
        if cid in conceitos:
            definido(cid, 'laboratorio/q100/respostas.py', linha, 'responde')
            for r in refs_de_rodada_no_codigo(corpo) | set(ids_no_texto(corpo, set(conceitos), False)):
                if r in conceitos and r != cid:
                    ligar(cid, r, 'apoia-se em')
    # arestas Q→Q criadas antes de todas as perguntas existirem
    for chave in [k for k in arestas if k[1] not in conceitos and k[0] in conceitos]:
        del arestas[chave]

    # ---- sistemas: a tabela do protocolo
    prot = textos.get('planning/protocolo.md', '')
    for m in re.finditer(r'^\| (S\d{2}) \| ([^|]+)\| ([^|]+)\| ([^|]+)\|', prot, re.M):
        cid = m.group(1)
        novo(cid, m.group(2).strip(), rodada_simples=m.group(3).strip(), teto=m.group(4).strip())
        definido(cid, 'planning/protocolo.md', prot[:m.start()].count('\n') + 1, 'define')

    # ---- revisões adversariais: os testes de achados e as marcas [Rn] no código
    revisoes = Counter()
    for c, t in textos.items():
        if c.endswith(('.py', '.md', '.gitignore')) or PurePosixPath(c).name == '.gitignore':
            for m in RE_REV.finditer(t):
                n = m.group(1) or m.group(2) or (m.group(3) if m.group(3) is not None else None)
                if n is not None:
                    revisoes[int(n) if n else 1] += 1
    for c in nos:
        m = re.match(r'test_achados_revisao(\d*)\.py$', PurePosixPath(c).name)
        if m:
            revisoes[int(m.group(1)) if m.group(1) else 1] += 1
    for n in sorted(revisoes):
        if n <= 30:
            novo(f'V{n}', f'Revisão adversarial {n}', rotulo_no_codigo=f'[R{n}]')
    for c in nos:
        m = re.match(r'test_achados_revisao(\d*)\.py$', PurePosixPath(c).name)
        if m:
            definido(f'V{int(m.group(1)) if m.group(1) else 1}', c, papel='testa')

    # ---- menções: todo arquivo de texto contra todos os conceitos
    existentes = set(conceitos)
    for c, t in textos.items():
        if not t or c.startswith('mapa/'):
            continue
        fortes = {(a, b) for (a, b, tipo) in arestas if tipo != 'menciona'}
        for cid, n in ids_no_texto(t, existentes).items():
            if (c, cid) not in fortes:
                ligar(c, cid, 'menciona', n)

    # ---- seções do pré-registro: a rodada que cita rodada anterior ou experimento se apoia nela;
    # a que cita rodada posterior está só apontando adiante, e isso não é evidência
    for cid, texto in texto_da_secao.items():
        for r in ids_no_texto(texto, existentes, False):
            if r == cid or r[0] not in 'RE':
                continue
            if r[0] == 'R' and ordem(r) >= ordem(cid):
                continue
            ligar(cid, r, 'apoia-se em')

    for cdef in conceitos.values():
        vistos, unicos = set(), []
        for d in cdef['definido_em']:
            chave = (d['arquivo'], d['papel'])
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(d)
        cdef['definido_em'] = unicos
    return {'conceitos': conceitos, 'arestas': arestas}


def ordem(cid: str):
    m = re.match(r'([A-Z])(\d+)(b?)', cid)
    return ('ERHQSV'.index(m.group(1)) if m.group(1) in 'ERHQSV' else 9, int(m.group(2)), m.group(3))
