"""Gera o mapa navegável do repositório: MAPA.md, mapa/pastas/*.md, mapa/simbolos.md e mapa/grafo.json.

Varre só arquivos versionados no Git (o mapa vai para o repositório, e link para arquivo sem commit
quebraria para quem clona); nunca abre `.env` nem nada que o .gitignore exclua. Arquivo novo entra no
mapa depois do commit dele. Liga os arquivos por três tipos de aresta: `importa` (import Python resolvido para
arquivo do repositório), `link` (link Markdown) e `cita` (o texto do arquivo nomeia outro arquivo pelo
caminho, ou pelo nome quando o nome é único). Uso: python mapa/gerar_mapa.py [--verificar]
"""
from __future__ import annotations

import ast
import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / 'mapa'
PASTAS = SAIDA / 'pastas'
PROPRIOS = {'MAPA.md', 'mapa/simbolos.md', 'mapa/grafo.json', 'mapa/gerar_mapa.py'}

# Finalidade de cada pasta, escrita à mão: é o que a varredura automática não sabe dizer.
FINALIDADE = {
    '.': 'Raiz do projeto JEV: avaliação científica do modelo Jev 1.13 (classificador barato via OpenRouter) e sua integração medida no Claude Code e no Codex.',
    '.reticle': 'Pasta de ferramenta local; só o .gitignore é versionado.',
    'data': 'Dados locais. Só o corpus de avaliação é versionado; o resto é ignorado.',
    'data/corpus': 'Corpus congelado dos experimentos (triagem, evidência, ressalvas), em JSONL. É o insumo dos executores `executor/run_e*.py`.',
    'docs': 'Documentos finais em Markdown: plano científico, relatórios, guia prático, limites, auditoria de números, hipóteses e medições das camadas.',
    'executor': 'Executor financeiro e dos experimentos E1–E16: livro-caixa com reserva atômica (`ledger.py`), preços, transporte compartilhado (`shared.py`), placar e um `run_e*.py` por experimento.',
    'executor/tests': 'Testes do executor: livro-caixa, preços, runner, placar, achados de cada revisão adversarial, entregáveis, MCP.',
    'integracao': 'O Jev dentro do fluxo real: roteador de prompts, hooks do Claude Code, servidor MCP, instalador, leitura de contexto para o Codex.',
    'integracao/avaliacao': 'Avaliação da integração com tráfego real do Igor (E13): amostragem, gabaritos e relatórios agregados. O texto original é privado e fica fora do Git.',
    'integracao/camadas': 'As camadas que decidem o que entra no contexto do modelo caro: leitura, busca, sentinela, saída, verificação, `ler` (skill /jev-ler), medição e rotina.',
    'integracao/hooks': 'Os scripts de hook instalados no Claude Code/Codex; cada um é um invólucro fino sobre uma camada.',
    'integracao/jev_router': 'Roteador de prompts: política, orçamento, redação de credenciais, cliente do provedor e CLI.',
    'integracao/tests': 'Testes da integração: camadas, guarda de comando, redação, roteador e rotina.',
    'lab': 'Painel local de acompanhamento (servidor stdlib + HTML/JS): fila de rodadas, execuções, métricas e orçamento.',
    'lab/data': 'Estado compartilhado do painel (`execution.json`).',
    'lab/tests': 'Testes do servidor do painel.',
    'laboratorio': 'Programa E14 de rodadas R0–R27: cada `rNN_*.py` roda uma rodada e grava `rNN-*.json`. Inclui auditoria do placar, canários, dossiê e mapa de limites.',
    'laboratorio/h100': 'Bateria H100: as cem hipóteses (dados, provas, avaliação, registro, relatório).',
    'laboratorio/q100': 'Bateria Q100: as cem perguntas estratégicas (respostas, registro, relatório).',
    'laboratorio/tests': 'Testes do laboratório: auditoria, canários, H100, Q100.',
    'output': 'Entregáveis gerados (HTML e PDF). Não editar à mão: regenerar pelos scripts de `planning/` e `laboratorio/`.',
    'output/pdf': 'PDFs finais: guia prático, plano científico e relatório final.',
    'planning': 'Protocolo, pré-registros dos experimentos, emendas, esquema SQL, matriz de testes e os geradores dos documentos/PDFs.',
    'research': 'Pesquisa de base: fontes consultadas, manifesto das fontes GitHub, inventário de sistemas, auditoria do PDF do Hermes.',
    'research/hermes': 'Material do Hermes: relatório final da Helena, dossiê quantitativo, auditoria local e decisões extraídas do PDF.',
    'runs': 'Resultados dos experimentos: um diretório por experimento com `relatorio.json` agregado; extrato do livro-caixa e erro grave. O banco `ledger.sqlite3` não é versionado.',
    'mapa': 'Este mapa: gerador, índice de símbolos, grafo em JSON e uma página por pasta.',
}

# Tarefas frequentes: onde começar. Cada caminho é conferido na geração.
ONDE = [
    ('Regras do projeto, orçamento de US$ 5 e cuidado com a chave', ['AGENTS.md']),
    ('Visão geral e como rodar o painel', ['README.md', 'lab/server.py']),
    ('Resultado final do estudo', ['docs/RELATORIO-FINAL-JEV.md', 'output/pdf/RELATORIO-FINAL-JEV.pdf']),
    ('Como aplicar o Jev na prática', ['docs/GUIA-PRATICO-JEV.md']),
    ('Onde o Jev falha', ['docs/LIMITES-DO-JEV.md', 'laboratorio/mapa-de-limites.json', 'output/mapa-de-limites.html']),
    ('Plano científico e protocolo', ['docs/PLANO-CIENTIFICO-JEV-HELENA.md', 'planning/protocolo.md']),
    ('Controle de gasto (reserva atômica, teto)', ['executor/ledger.py', 'executor/pricing.py', 'executor/prices.json', 'executor/README.md']),
    ('Chamar o Jev pelo transporte compartilhado', ['executor/shared.py']),
    ('Extrato do gasto conferível', ['runs/extrato-ledger.json', 'executor/exportar_extrato.py']),
    ('Hooks do Claude Code (leitura, busca, sentinela, saída)', ['integracao/README.md', 'integracao/camadas/nucleo.py', 'integracao/hooks/jev_leitura.py', 'integracao/instalar.py']),
    ('Medição das camadas no Claude Code', ['docs/CAMADAS-CLAUDE-CODE.md', 'integracao/camadas/medir.py']),
    ('Jev no Codex', ['integracao/USO-CODEX.md', 'docs/CAMADAS-CODEX.md', 'integracao/codex_jev.py', 'integracao/ler_contexto.py']),
    ('Servidor MCP (jev_assist, jev_rank_context)', ['integracao/jev_mcp.py', 'executor/assist.py']),
    ('Roteador de prompts e redação de credenciais', ['integracao/jev_router/roteador.py', 'integracao/jev_router/redacao.py']),
    ('Rodadas do laboratório R0–R27', ['laboratorio/PREREGISTRO.md', 'laboratorio/nucleo.py']),
    ('Cem hipóteses e cem perguntas', ['docs/CEM-HIPOTESES.md', 'docs/CEM-PERGUNTAS-ESTRATEGICAS.md', 'laboratorio/h100/provas.py', 'laboratorio/q100/respostas.py']),
    ('Conferir números publicados', ['docs/AUDITORIA-DE-NUMEROS.md', 'laboratorio/auditoria.py', 'laboratorio/auditoria-placar.json']),
    ('Regenerar documentos e PDFs', ['planning/build_plan.py', 'planning/build_deliverables.py', 'planning/build_relatorio_pdf.py']),
]

TEXTO = {'.py', '.md', '.json', '.jsonl', '.csv', '.txt', '.html', '.js', '.css', '.sql', '.ini'}
ICONE = {'.py': 'código', '.md': 'doc', '.json': 'dado', '.jsonl': 'dado', '.csv': 'dado', '.pdf': 'pdf',
         '.html': 'web', '.js': 'web', '.css': 'web', '.sql': 'esquema', '.txt': 'texto', '.ini': 'config'}


def arquivos_do_git() -> list[str]:
    saida = subprocess.run(['git', 'ls-files', '-z'], cwd=RAIZ,
                           capture_output=True, check=True).stdout.decode('utf-8')
    return sorted(p for p in saida.split('\0') if p and (RAIZ / p).is_file() and p not in PROPRIOS
                  and not p.startswith('mapa/'))


def ler(caminho: str) -> str:
    try:
        return (RAIZ / caminho).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def pasta_de(caminho: str) -> str:
    pai = str(PurePosixPath(caminho).parent)
    return pai


def resumo_curto(texto: str, limite: int = 160) -> str:
    texto = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', texto)  # link copiado da fonte quebraria fora dela
    texto = ' '.join(texto.split()).replace('|', '/')
    return texto if len(texto) <= limite else texto[:limite - 1].rstrip() + '…'


def descrever(caminho: str, texto: str) -> tuple[str, list[dict]]:
    """Devolve (descrição de uma linha, símbolos de topo) do arquivo."""
    ext = PurePosixPath(caminho).suffix.lower()
    simbolos: list[dict] = []
    if ext == '.py':
        try:
            arvore = ast.parse(texto)
        except SyntaxError:
            return 'Python (não analisável)', []
        for no in arvore.body:
            if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                tipo = 'classe' if isinstance(no, ast.ClassDef) else 'função'
                simbolos.append({'nome': no.name, 'tipo': tipo, 'linha': no.lineno})
                if isinstance(no, ast.ClassDef):
                    for filho in no.body:
                        if isinstance(filho, (ast.FunctionDef, ast.AsyncFunctionDef)) and not filho.name.startswith('__'):
                            simbolos.append({'nome': f'{no.name}.{filho.name}', 'tipo': 'método', 'linha': filho.lineno})
        doc = ast.get_docstring(arvore) or ''
        if doc:
            return resumo_curto(re.split(r'\n\s*\n', doc.strip())[0]), simbolos
        comentarios = [l.lstrip('# ').strip() for l in texto.splitlines()[:8] if l.startswith('#') and not l.startswith('#!')]
        nomes = ', '.join(s['nome'] for s in simbolos if s['tipo'] != 'método')[:120]
        return resumo_curto(' '.join(comentarios)) if comentarios else (f'Define: {nomes}' if nomes else 'Script Python'), simbolos
    if ext == '.md':
        titulo = next((l.lstrip('#').strip() for l in texto.splitlines() if l.startswith('#')), '')
        corpo = next((l.strip() for l in texto.splitlines() if l.strip() and not l.startswith(('#', '|', '-', '>', '```', '<'))), '')
        for i, l in enumerate(texto.splitlines(), 1):
            if l.startswith('## '):
                simbolos.append({'nome': l[3:].strip(), 'tipo': 'seção', 'linha': i})
        return resumo_curto(f'{titulo} — {corpo}' if titulo and corpo else titulo or corpo or 'Markdown'), simbolos
    if ext == '.json':
        try:
            dado = json.loads(texto)
        except ValueError:
            return 'JSON (inválido ou parcial)', []
        if isinstance(dado, dict):
            chaves = list(dado)
            return resumo_curto(f'Objeto com {len(chaves)} chaves: ' + ', '.join(map(str, chaves[:12]))), []
        if isinstance(dado, list):
            primeiro = dado[0] if dado else None
            campos = ', '.join(list(primeiro)[:10]) if isinstance(primeiro, dict) else type(primeiro).__name__
            return resumo_curto(f'Lista de {len(dado)} itens ({campos})'), []
        return 'JSON escalar', []
    if ext == '.jsonl':
        linhas = [l for l in texto.splitlines() if l.strip()]
        try:
            campos = ', '.join(list(json.loads(linhas[0]))[:10]) if linhas else ''
        except (ValueError, TypeError):
            campos = '?'
        return resumo_curto(f'{len(linhas)} registros JSONL (campos: {campos})'), []
    if ext == '.csv':
        cabecalho = next(csv.reader(io.StringIO(texto)), [])
        return resumo_curto(f'{max(len(texto.splitlines()) - 1, 0)} linhas; colunas: ' + ', '.join(cabecalho[:12])), []
    if ext == '.html':
        m = re.search(r'<title>(.*?)</title>', texto, re.S | re.I)
        return resumo_curto('Página: ' + (m.group(1).strip() if m else caminho)), []
    if ext in {'.js', '.css'}:
        m = re.search(r'/\*(.*?)\*/|//(.*)', texto[:2000], re.S)
        funcoes = re.findall(r'^\s*(?:async\s+)?function\s+(\w+)', texto, re.M)
        for nome in funcoes:
            linha = texto[:texto.find(f'function {nome}')].count('\n') + 1
            simbolos.append({'nome': nome, 'tipo': 'função', 'linha': linha})
        base = (m.group(1) or m.group(2) or '').strip() if m else ''
        return resumo_curto(base or ('JavaScript' if ext == '.js' else 'Folha de estilo') + (f'; {len(funcoes)} funções' if funcoes else '')), simbolos
    if ext == '.sql':
        tabelas = re.findall(r'CREATE TABLE(?: IF NOT EXISTS)?\s+(\w+)', texto, re.I)
        return resumo_curto('Esquema SQL; tabelas: ' + ', '.join(tabelas)), []
    if ext == '.pdf':
        return 'PDF gerado (binário)', []
    if ext in TEXTO:
        primeira = next((l.strip() for l in texto.splitlines() if l.strip()), '')
        return resumo_curto(primeira or 'Texto'), []
    return 'Arquivo', []


def modulos_de_import(texto: str) -> list[tuple[str, int]]:
    """(nome do módulo, nível relativo) de cada import do arquivo, inclusive dentro de funções."""
    try:
        arvore = ast.parse(texto)
    except SyntaxError:
        return []
    achados = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            achados += [(a.name, 0) for a in no.names]
        elif isinstance(no, ast.ImportFrom):
            base = no.module or ''
            achados.append((base, no.level))
            achados += [((base + '.' if base else '') + a.name, no.level) for a in no.names]
    return achados


def resolver_import(origem: str, modulo: str, nivel: int, conjunto: set[str]) -> str | None:
    pasta = PurePosixPath(origem).parent
    if nivel:
        for _ in range(nivel - 1):
            pasta = pasta.parent
        raizes = [pasta]
    else:
        # sys.path.insert dos scripts aponta para a raiz, para integracao/ ou para a pasta do próprio arquivo
        raizes = [PurePosixPath('.'), PurePosixPath('integracao'), PurePosixPath('integracao/hooks'),
                  PurePosixPath('laboratorio'), pasta, pasta.parent]
    partes = [p for p in modulo.split('.') if p]
    if not partes:
        return None
    for r in raizes:
        base = r.joinpath(*partes)
        for candidato in (f'{base}.py', f'{base}/__init__.py'):
            candidato = str(PurePosixPath(candidato))
            if candidato.startswith('./'):
                candidato = candidato[2:]
            if candidato in conjunto and candidato != origem:
                return candidato
    return None


def resolver_link(origem: str, alvo: str, conjunto: set[str]) -> str | None:
    alvo = alvo.split('#')[0].split('?')[0].strip()
    if not alvo or '://' in alvo or alvo.startswith('mailto:'):
        return None
    caminho = (RAIZ / pasta_de(origem) / alvo).resolve()
    try:
        rel = caminho.relative_to(RAIZ).as_posix()
    except ValueError:
        return None
    return rel if rel in conjunto else None


def usos_de_simbolos(origem: str, texto: str, conjunto: set[str], simbolos: dict[str, set[str]]) -> set[tuple[str, str]]:
    """(arquivo, nome) de cada função ou classe de outro arquivo que `origem` usa.

    Pega `from mod import nome` e o acesso por atributo depois de importar o módulo
    (`import executor.ledger as L` ... `L.Ledger`, ou `from executor import ledger` ... `ledger.Ledger`).
    """
    try:
        arvore = ast.parse(texto)
    except SyntaxError:
        return set()
    usos, apelidos = set(), {}
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom):
            base = no.module or ''
            modulo = resolver_import(origem, base, no.level, conjunto) if base else None
            for a in no.names:
                sub = resolver_import(origem, (base + '.' if base else '') + a.name, no.level, conjunto)
                if sub and sub != modulo:
                    apelidos[a.asname or a.name] = sub
                elif modulo and a.name in simbolos.get(modulo, ()):
                    usos.add((modulo, a.name))
        elif isinstance(no, ast.Import):
            for a in no.names:
                alvo = resolver_import(origem, a.name, 0, conjunto)
                if alvo:
                    apelidos[a.asname or a.name] = alvo
    for nome, alvo in apelidos.items():
        for m in re.finditer(rf'(?<![\w.]){re.escape(nome)}\.(\w+)', texto):
            if m.group(1) in simbolos.get(alvo, ()):
                usos.add((alvo, m.group(1)))
    return {u for u in usos if u[0] != origem}


def montar() -> dict:
    lista = arquivos_do_git()
    conjunto = set(lista)
    nos = {}
    textos = {}
    for c in lista:
        ext = PurePosixPath(c).suffix.lower()
        texto = ler(c) if ext in TEXTO else ''
        textos[c] = texto
        descricao, simbolos = descrever(c, texto)
        nos[c] = {'id': c, 'pasta': pasta_de(c), 'tipo': ICONE.get(ext, 'outro'), 'bytes': (RAIZ / c).stat().st_size,
                  'linhas': texto.count('\n') + (1 if texto and not texto.endswith('\n') else 0) if texto else None,
                  'descricao': descricao, 'simbolos': simbolos}

    arestas: set[tuple[str, str, str]] = set()
    # nomes únicos e específicos o bastante para uma menção pelo nome valer como referência
    por_nome = defaultdict(list)
    for c in lista:
        por_nome[PurePosixPath(c).name].append(c)
    genericos = {'README.md', '__init__.py', 'relatorio.json', 'summary.json', 'index.html', '.gitignore'}
    nomes_unicos = {n: cs[0] for n, cs in por_nome.items() if len(cs) == 1 and n not in genericos and len(n) >= 8 and '.' in n}
    padrao_nome = re.compile(r'(?<![\w./-])(' + '|'.join(sorted(map(re.escape, nomes_unicos), key=len, reverse=True)) + r')(?![\w-])') if nomes_unicos else None
    padrao_caminho = re.compile(r'(?<![\w.-])(' + '|'.join(sorted(map(re.escape, lista), key=len, reverse=True)) + r')(?![\w-])')

    for c in lista:
        texto = textos[c]
        if not texto or nos[c]['tipo'] == 'dado' and nos[c]['bytes'] > 2_000_000:
            continue
        if c.endswith('.py'):
            for modulo, nivel in modulos_de_import(texto):
                alvo = resolver_import(c, modulo, nivel, conjunto)
                if alvo:
                    arestas.add((c, alvo, 'importa'))
            # python -m pacote.modulo citado em texto
        for m in re.finditer(r'python\s+-m\s+([\w.]+)', texto):
            alvo = resolver_import(c, m.group(1), 0, conjunto)
            if alvo and alvo != c:
                arestas.add((c, alvo, 'cita'))
        if c.endswith('.md'):
            for m in re.finditer(r'\]\(([^)\s]+)\)', texto):
                alvo = resolver_link(c, m.group(1), conjunto)
                if alvo and alvo != c:
                    arestas.add((c, alvo, 'link'))
        normal = texto.replace('\\', '/')
        for m in padrao_caminho.finditer(normal):
            if m.group(1) != c:
                arestas.add((c, m.group(1), 'cita'))
        if padrao_nome:
            for m in padrao_nome.finditer(normal):
                alvo = nomes_unicos[m.group(1)]
                if alvo != c:
                    arestas.add((c, alvo, 'cita'))
    # uma relação forte esconde a fraca entre o mesmo par
    fortes = {(a, b) for a, b, t in arestas if t in ('importa', 'link')}
    arestas = {(a, b, t) for a, b, t in arestas if t != 'cita' or (a, b) not in fortes}

    pastas = sorted({'.'} | {str(p) for c in lista for p in [PurePosixPath(c).parent, *PurePosixPath(c).parents] if str(p) != '.'} | {'.'})

    simbolos = {c: {s['nome'] for s in n['simbolos'] if s['tipo'] in ('função', 'classe')} for c, n in nos.items() if c.endswith('.py')}
    usos = set()
    for c in lista:
        if c.endswith('.py'):
            usos |= {(c, alvo, nome) for alvo, nome in usos_de_simbolos(c, textos[c], conjunto, simbolos)}

    sys.path.insert(0, str(SAIDA))
    import conhecimento  # mesmo diretório; separado porque é outra camada do mapa
    saber = conhecimento.extrair(nos, textos)
    return {'nos': nos, 'arestas': sorted(arestas), 'pastas': pastas, 'textos': textos, 'usos': sorted(usos),
            'conceitos': saber['conceitos'], 'arestas_c': saber['arestas']}


# ---------- escrita ----------

def finalidade(pasta: str) -> str:
    if pasta in FINALIDADE:
        return FINALIDADE[pasta]
    m = re.fullmatch(r'runs/e(\d+b?)-(.+)', pasta)
    if m:
        return f'Resultados do experimento E{m.group(1)} ({m.group(2).replace("-", " ")}): relatório agregado e, quando houve, adjudicação cega e respostas brutas.'
    if pasta == 'runs/canaries':
        return 'Resumo dos canários de comportamento (verificação de que o modelo servido não mudou).'
    return ''


def pagina_da_pasta(pasta: str) -> str:
    return 'mapa/pastas/' + ('_raiz' if pasta == '.' else pasta.replace('/', '__').lstrip('.').lstrip('_') or pasta) + '.md'


def rel(de: str, para: str) -> str:
    """Link relativo do arquivo `de` para o caminho `para` (ambos relativos à raiz)."""
    base = PurePosixPath(de).parent
    subir = len([p for p in base.parts if p != '.'])
    return '/'.join(['..'] * subir + [para]) if para != '.' else '/'.join(['..'] * subir) or '.'


def lnk(de: str, para: str, texto: str | None = None) -> str:
    return f'[{texto or para}]({rel(de, para).replace(" ", "%20")})'


def tamanho(n: int) -> str:
    for unidade in ('B', 'KB', 'MB'):
        if n < 1024:
            return f'{n:.0f} {unidade}'
        n /= 1024
    return f'{n:.1f} GB'


def id_mermaid(texto: str) -> str:
    return 'n_' + re.sub(r'\W', '_', texto)


def experimentos(nos: dict) -> list[tuple[str, list[str]]]:
    grupos = defaultdict(list)
    for c in nos:
        nome = PurePosixPath(c).name.lower()
        for m in re.finditer(r'(?:^|[_/-])e(\d{1,2}b?)(?=[_.-])', ('/' + c.lower())):
            grupos['E' + m.group(1).upper().replace('B', 'b')].append(c)
            break
        else:
            if re.match(r'preregistro-e(\d+)', nome):
                grupos['E' + re.match(r'preregistro-e(\d+)', nome).group(1)].append(c)
    chave = lambda k: (int(re.sub(r'\D', '', k)), k)
    return [(k, sorted(set(v))) for k, v in sorted(grupos.items(), key=lambda kv: chave(kv[0]))]


def rodadas(nos: dict) -> list[tuple[str, list[str]]]:
    grupos = defaultdict(list)
    for c in nos:
        if not c.startswith('laboratorio/') or '/' in c[len('laboratorio/'):]:
            continue
        nome = PurePosixPath(c).name.lower()
        m = re.match(r'r(\d+)(b?)(?:[-_]r(\d+))?[-_]', nome)
        if m:
            ini = int(m.group(1))
            fim = int(m.group(3)) if m.group(3) else ini
            rotulo = f'R{ini}{m.group(2)}' + (f'–R{fim}' if fim != ini else '')
            grupos[rotulo].append(c)
    return sorted(((k, sorted(v)) for k, v in grupos.items()), key=lambda kv: (int(re.search(r'\d+', kv[0]).group()), kv[0]))


def escrever(dados: dict) -> list[str]:
    nos, arestas, pastas = dados['nos'], dados['arestas'], dados['pastas']
    saem, chegam = defaultdict(list), defaultdict(list)
    for a, b, t in arestas:
        saem[a].append((b, t))
        chegam[b].append((a, t))
    filhos = defaultdict(list)
    for p in pastas:
        if p != '.':
            filhos[str(PurePosixPath(p).parent)].append(p)
    arquivos_por_pasta = defaultdict(list)
    for c, n in nos.items():
        arquivos_por_pasta[n['pasta']].append(c)
    exps = experimentos(nos)
    import conhecimento as k
    conceitos, ac = dados['conceitos'], dados['arestas_c']
    usados_por, usa_de = defaultdict(set), defaultdict(set)
    for a, alvo, nome in dados['usos']:
        usados_por[(alvo, nome)].add(a)
        usa_de[a].add((alvo, nome))
    conceitos_do_arquivo = defaultdict(list)
    for (a, b, t), peso in ac.items():
        if a in nos:
            conceitos_do_arquivo[a].append((b, t, peso))
    n_arestas_total = len(arestas) + len(ac) + len(dados['usos'])
    gerados = []
    PASTAS.mkdir(parents=True, exist_ok=True)
    for velho in PASTAS.glob('*.md'):
        velho.unlink()

    def topo(caminho: str) -> str:
        return caminho.split('/')[0] if '/' in caminho else '.'

    # ----- MAPA.md -----
    m = ['# Mapa do repositório JEV', '',
         'Ponto de entrada para qualquer pessoa ou IA achar qualquer coisa nesta pasta. Gerado por '
         '`python mapa/gerar_mapa.py`; não editar à mão, regenerar depois de mudar arquivos.', '',
         f'**{len(nos)} arquivos** em **{len(pastas)} pastas** e **{len(conceitos)} conceitos do estudo** '
         f'(experimentos, rodadas, hipóteses, perguntas, sistemas, revisões), ligados por **{n_arestas_total} relações**: '
         f'{sum(1 for *_, t in arestas if t == "importa")} imports, {sum(1 for *_, t in arestas if t == "link")} links, '
         f'{sum(1 for *_, t in arestas if t == "cita")} citações entre arquivos; {len(dados["usos"])} usos de função ou classe de outro arquivo; '
         f'{sum(1 for (_, _, t) in ac if t != "apoia-se em")} ligações arquivo–conceito e {sum(1 for (_, _, t) in ac if t == "apoia-se em")} conceito–conceito.', '',
         '## Como usar este mapa', '',
         '- **Perguntar ao grafo direto:** `python mapa/consultar.py TERMO` (arquivo, função, `H012`, `R17`, `Q042`, palavra), '
         '`--caminho A B` (como duas coisas se ligam), `--vizinhos X --profundidade 2`. Só biblioteca padrão, lê `mapa/grafo.json`.',
         '- **Achar um arquivo por assunto:** a tabela "Onde está" abaixo, depois a página da pasta.',
         '- **Achar um estudo, hipótese ou pergunta:** a seção "Conhecimento do estudo" abaixo; cada conceito diz onde está, em que se apoia, o que sustenta e quem o menciona.',
         '- **Achar uma função, classe ou seção:** ' + lnk('MAPA.md', 'mapa/simbolos.md', 'mapa/simbolos.md') + ' (nome → arquivo:linha, e em quantos arquivos é usada).',
         '- **Ver quem usa um arquivo ou função:** a página da pasta mostra, para cada arquivo, o que ele usa, quem o usa, que funções de outros arquivos chama e que estudos menciona.',
         '- **Saber o que falta:** ' + lnk('MAPA.md', 'mapa/conhecimento/lacunas.md', 'lacunas e ideias abertas') + ' e '
         + lnk('MAPA.md', 'mapa/conhecimento/testes.md', 'testes, com o código sem teste direto') + '.',
         '- **Grafo para programas:** ' + lnk('MAPA.md', 'mapa/grafo.json', 'mapa/grafo.json') + ' (nós: arquivos, conceitos e símbolos; cada aresta tem tipo e, nas menções, peso).',
         '- **Fora do mapa de propósito:** `.env` (chave OpenRouter, nunca abrir), `.venv-s08/`, `graphify-out/`, `.planning/`, '
         '`runs/ledger.sqlite3`, `research/sources/`, `research/hermes/raw/`, material privado de `integracao/avaliacao/` '
         'e estado operacional de `integracao/` — tudo que o `.gitignore` exclui.', '',
         '## Onde está', '', '| preciso de | comece por |', '|---|---|']
    for tarefa, caminhos in ONDE:
        validos = [c for c in caminhos if c in nos]
        m.append(f'| {tarefa} | ' + ', '.join(lnk('MAPA.md', c, f'`{c}`') for c in validos) + ' |')

    # ----- conhecimento do estudo -----
    contagem = Counter(c[0] for c in conceitos)
    placar_h = Counter(conceitos[c]['atributos'].get('veredito', '?') for c in conceitos if c[0] == 'H')
    q_medidas = sum(1 for c in conceitos if c[0] == 'Q' and conceitos[c]['atributos'].get('fonte_da_resposta') == 'dado medido')
    resumo = {'E': 'pré-registro, executor, adjudicação, testes e resultado de cada um',
              'R': 'pré-registro, script, artefato e retratações de cada rodada; linhagem entre rodadas',
              'H': ', '.join(f'{n} {v}' for v, n in placar_h.most_common()) + '; cada uma com as rodadas em que a prova se apoia',
              'Q': f'{q_medidas} respondidas por dado medido; as demais por conta declarada ou coleta nova',
              'S': 'os sistemas do ecossistema Jev cobertos pelo plano',
              'V': 'revisões independentes do executor e os testes que fixam cada achado'}
    m += ['', '## Conhecimento do estudo', '',
          'Os conceitos são nós do grafo, lidos da fonte que os define. Cada página diz, por conceito, onde ele está, '
          'em que se apoia, o que sustenta e que arquivos o mencionam.', '',
          '| conceito | quantos | página | o que tem |', '|---|---:|---|---|']
    for letra, (titulo, _) in PAGINAS_C.items():
        m.append(f'| {titulo} | {contagem[letra]} | {lnk("MAPA.md", k.TIPOS[letra][1], PurePosixPath(k.TIPOS[letra][1]).name)} | {resumo[letra]} |')
    m += [f'| Testes | {sum(1 for c in nos if "/tests/" in c and PurePosixPath(c).name.startswith("test_"))} | '
          f'{lnk("MAPA.md", "mapa/conhecimento/testes.md", "testes.md")} | o que cada teste exercita e que estudo fixa; código sem teste direto |',
          f'| Lacunas e ideias | — | {lnk("MAPA.md", "mapa/conhecimento/lacunas.md", "lacunas.md")} | hipóteses que caíram, respostas sem dado medido, peças faltando, pendências declaradas |', '']
    entre = Counter()
    for (a, b, t), _ in ac.items():
        if t == 'apoia-se em':
            entre[(a[0], b[0])] += 1
    arq_c = Counter(b[0] for (a, b, t) in ac if a in nos)
    nomes = {x: PAGINAS_C[x][0] for x in PAGINAS_C}
    m += ['Como os tipos de conceito se apoiam uns nos outros (número de ligações), e quantas ligações os arquivos fazem a cada tipo:', '',
          '```mermaid', 'flowchart LR', '  ARQ(["arquivos"])']
    for x in PAGINAS_C:
        if contagem[x]:
            m.append(f'  {x}["{nomes[x]} ({contagem[x]})"]')
    for (a, b), n in sorted(entre.items()):
        if a != b:
            m.append(f'  {a} -->|{n}| {b}')
        else:
            m.append(f'  {a} -.->|{n} entre si| {a}')
    for x, n in sorted(arq_c.items()):
        m.append(f'  ARQ -.->|{n}| {x}')
    m += ['```', '']

    m += ['## Pastas', '', '| pasta | arquivos | finalidade |', '|---|---:|---|']

    def total(p: str) -> int:
        return sum(1 for c in nos if p == '.' or c.startswith(p + '/'))

    def arvore(p: str, nivel: int):
        nome = 'raiz' if p == '.' else PurePosixPath(p).name + '/'
        recuo = '&nbsp;&nbsp;&nbsp;&nbsp;' * nivel
        m.append(f'| {recuo}{lnk("MAPA.md", pagina_da_pasta(p), nome)} | {total(p)} | {finalidade(p)} |')
        for f in sorted(filhos[p]):
            arvore(f, nivel + 1)
    arvore('.', 0)

    # grafo das pastas de topo
    fluxo = Counter()
    for a, b, t in arestas:
        ta, tb = topo(a), topo(b)
        if ta != tb and ta != '.' and tb != '.':
            fluxo[(ta, tb, t)] += 1
    m += ['', '## Grafo entre as pastas de topo', '',
          'Setas cheias: imports de código (todos). Tracejadas: documentos e dados que citam ou linkam arquivos de outra pasta, '
          'só quando são 5 ou mais. O número é a quantidade de relações; a matriz abaixo traz todas.', '',
          '```mermaid', 'flowchart LR']
    tops = sorted({topo(c) for c in nos} - {'.'})
    agregado = defaultdict(Counter)
    for (a, b, t), n in fluxo.items():
        agregado[(a, b)]['importa' if t == 'importa' else 'outro'] += n
    desenhadas = [(a, b, c) for (a, b), c in sorted(agregado.items()) if c['importa'] or c['outro'] >= 5]
    for t in tops:
        if any(t in (a, b) for a, b, _ in desenhadas):
            m.append(f'  {id_mermaid(t)}["{t}/ ({total(t)})"]')
    for a, b, cont in desenhadas:
        if cont['importa']:
            m.append(f'  {id_mermaid(a)} -->|{cont["importa"]}| {id_mermaid(b)}')
        if cont['outro'] >= 5:
            m.append(f'  {id_mermaid(a)} -.->|{cont["outro"]}| {id_mermaid(b)}')
    m += ['```', '', 'Matriz completa (linha usa coluna; imports + citações + links):', '',
          '| de → para | ' + ' | '.join(f'{t}/' for t in tops) + ' |', '|---|' + '---:|' * len(tops)]
    for a in tops:
        m.append(f'| **{a}/** | ' + ' | '.join(str(sum(agregado[(a, b)].values()) or '') for b in tops) + ' |')
    m.append('')

    # fluxo conceitual, escrito à mão
    m += ['## Como as partes se ligam', '',
          '```mermaid', 'flowchart TD',
          '  prot["planning/ — protocolo e pré-registros"] --> corpus["data/corpus/ — corpus congelado"]',
          '  corpus --> exe["executor/run_e*.py — experimentos E1–E16"]',
          '  exe --> ledger["executor/ledger.py + shared.py — teto de gasto e transporte"]',
          '  ledger --> runs["runs/ — relatorio.json por experimento, extrato"]',
          '  lab14["laboratorio/rNN_*.py — rodadas R0–R27"] --> ledger',
          '  lab14 --> labjson["laboratorio/rNN-*.json — resultados"]',
          '  runs --> docs["docs/ — relatórios, guia, limites"]',
          '  labjson --> docs',
          '  docs --> out["output/ — PDFs e HTML"]',
          '  plan2["planning/build_*.py"] --> out',
          '  docs --> integ["integracao/ — camadas, hooks, MCP, roteador"]',
          '  integ --> ledger',
          '  integ --> hooks["Claude Code e Codex (hooks instalados)"]',
          '  painel["lab/ — painel local"] --> runs',
          '```', '']

    if exps:
        m += ['## Experimentos E1–E16: cada peça de cada um', '',
              'Pré-registro, executor, adjudicação, testes e resultados do mesmo experimento, juntos. '
              'O E13 (tráfego real) mora em ' + lnk('MAPA.md', pagina_da_pasta('integracao/avaliacao'), 'integracao/avaliacao/')
              + ' e o E14 (rodadas R0–R27) em ' + lnk('MAPA.md', pagina_da_pasta('laboratorio'), 'laboratorio/') + ', na tabela seguinte.', '',
              '| exp. | arquivos |', '|---|---|']
        for e, cs in exps:
            rotulo = f'[{e}]({k.pagina(e)}#{k.ancora(e)})' if e in conceitos else e
            m.append(f'| {rotulo} | ' + ' · '.join(lnk('MAPA.md', c, PurePosixPath(c).name if not c.startswith('runs/') else c[5:]) for c in cs) + ' |')
        m.append('')
    rods = rodadas(nos)
    if rods:
        m += ['## Rodadas do laboratório: script e resultado', '', '| rodada | arquivos |', '|---|---|']
        for r, cs in rods:
            ids = [f'R{a}{b}' for a, b in re.findall(r'R(\d+)(b?)', r)]
            rotulo = ' '.join(f'[{x}]({k.pagina(x)}#{k.ancora(x)})' if x in conceitos else x for x in ids)
            m.append(f'| {rotulo} | ' + ' · '.join(lnk('MAPA.md', c, PurePosixPath(c).name) for c in cs) + ' |')
        m.append('')

    # testes → alvo
    testes = defaultdict(set)
    for a, b, t in arestas:
        if t == 'importa' and '/tests/' in a and '/tests/' not in b and not b.endswith('__init__.py'):
            testes[b].add(a)
    if testes:
        m += ['## Código e seus testes', '', '| módulo | testado em |', '|---|---|']
        for alvo in sorted(testes):
            m.append(f'| {lnk("MAPA.md", alvo, f"`{alvo}`")} | ' + ', '.join(lnk('MAPA.md', t, PurePosixPath(t).name) for t in sorted(testes[alvo])) + ' |')
        m.append('')

    centrais = sorted(nos, key=lambda c: (-len(chegam[c]), c))[:20]
    m += ['## Arquivos mais referenciados', '', 'Os que mais outros arquivos importam, linkam ou citam: mudar um deles tem efeito amplo.', '',
          '| arquivo | recebe | descrição |', '|---|---:|---|']
    for c in centrais:
        m.append(f'| {lnk("MAPA.md", c, f"`{c}`")} | {len(chegam[c])} | {nos[c]["descricao"]} |')
    (RAIZ / 'MAPA.md').write_text('\n'.join(m) + '\n', encoding='utf-8')
    gerados.append('MAPA.md')

    # ----- uma página por pasta -----
    for p in pastas:
        pag = pagina_da_pasta(p)
        nome = 'raiz do projeto' if p == '.' else f'{p}/'
        linhas = [f'# {nome}', '', finalidade(p), '',
                  '← ' + lnk(pag, 'MAPA.md', 'MAPA.md') + (f' · pasta acima: {lnk(pag, pagina_da_pasta(str(PurePosixPath(p).parent)), str(PurePosixPath(p).parent) if str(PurePosixPath(p).parent) != "." else "raiz")}' if p != '.' else '')
                  + (f' · abrir a pasta: {lnk(pag, p, p + "/")}' if p != '.' else ''), '']
        if filhos[p]:
            linhas += ['## Subpastas', '', '| subpasta | arquivos | finalidade |', '|---|---:|---|']
            for f in sorted(filhos[p]):
                linhas.append(f'| {lnk(pag, pagina_da_pasta(f), PurePosixPath(f).name + "/")} | {total(f)} | {finalidade(f)} |')
            linhas.append('')
        meus = sorted(arquivos_por_pasta[p])
        mexp = re.fullmatch(r'runs/e(\d+b?)-.+', p)
        if mexp:
            pecas = dict(exps).get('E' + mexp.group(1), [])
            fora = [c for c in pecas if not c.startswith(p + '/')]
            if fora:
                linhas += [f'**Outras peças do E{mexp.group(1)}:** ' + ' · '.join(lnk(pag, c, f'`{c}`') for c in fora), '']
        if meus:
            linhas += ['## Arquivos', '', '| arquivo | tipo | tamanho | descrição |', '|---|---|---:|---|']
            for c in meus:
                n = nos[c]
                medida = f'{n["linhas"]} l.' if n['linhas'] else tamanho(n['bytes'])
                linhas.append(f'| {lnk(pag, c, PurePosixPath(c).name)} | {n["tipo"]} | {medida} | {n["descricao"]} |')
            linhas.append('')
            # grafo local: arquivos da pasta e seus vizinhos diretos
            locais = [(a, b, t) for a, b, t in arestas if (a in meus or b in meus) and t in ('importa', 'link')]
            if locais and len(locais) <= 80:
                linhas += ['## Grafo de imports e links', '', 'Nós em negrito são desta pasta; setas cheias são imports, tracejadas são links de documento.', '', '```mermaid', 'flowchart LR']
                envolvidos = sorted({x for a, b, _ in locais for x in (a, b)})
                for x in envolvidos:
                    rotulo = PurePosixPath(x).name if x in meus else x
                    linhas.append(f'  {id_mermaid(x)}["{"<b>" + rotulo + "</b>" if x in meus else rotulo}"]')
                for a, b, t in locais:
                    linhas.append(f'  {id_mermaid(a)} {"-->" if t == "importa" else "-.->"} {id_mermaid(b)}')
                linhas += ['```', '']
            elif locais:
                linhas += [f'_Grafo local omitido: {len(locais)} relações, grande demais para desenhar; ver as ligações abaixo ou `mapa/grafo.json`._', '']
            com_ligacao = [c for c in meus if saem[c] or chegam[c] or nos[c]['simbolos'] or conceitos_do_arquivo[c]]
            if com_ligacao:
                linhas += ['## Ligações e conteúdo de cada arquivo', '']
                for c in com_ligacao:
                    n = nos[c]
                    linhas.append(f'### {PurePosixPath(c).name}')
                    linhas.append('')
                    for rotulo, lista in (('usa', saem[c]), ('é usado por', chegam[c])):
                        if lista:
                            por_tipo = defaultdict(list)
                            for x, t in sorted(lista):
                                por_tipo[t].append(x)
                            partes = []
                            for t in ('importa', 'link', 'cita'):
                                if por_tipo[t]:
                                    verbo = {'importa': 'import', 'link': 'link', 'cita': 'citação'}[t]
                                    partes.append(f'{verbo}: ' + ', '.join(lnk(pag, x, f'`{x}`') for x in por_tipo[t]))
                            linhas.append(f'- **{rotulo}** — ' + '; '.join(partes))
                    if usa_de[c]:
                        linhas.append('- **chama de outros arquivos** — ' + ', '.join(
                            f'[`{PurePosixPath(alvo).stem}.{nome}`]({rel(pag, alvo)}#L{linha_do_simbolo(nos, alvo, nome)})' for alvo, nome in sorted(usa_de[c])))
                    papeis = [(b, t) for b, t, _ in conceitos_do_arquivo[c] if t != 'menciona']
                    if papeis:
                        linhas.append('- **papel nos estudos** — ' + ', '.join(
                            f'{t} [{b}]({rel(pag, k.pagina(b))}#{k.ancora(b)})' for b, t in sorted(papeis, key=lambda x: (x[1], k.ordem(x[0])))))
                    mencoes = sorted(((b, p) for b, t, p in conceitos_do_arquivo[c] if t == 'menciona'), key=lambda x: (-x[1], k.ordem(x[0])))
                    if mencoes:
                        linhas.append(f'- **menciona {len(mencoes)} conceito' + ('s' if len(mencoes) > 1 else '') + '** — ' + ', '.join(
                            f'[{b}]({rel(pag, k.pagina(b))}#{k.ancora(b)}) ({p}×)' for b, p in mencoes[:25]) + (f' … e mais {len(mencoes) - 25}' if len(mencoes) > 25 else ''))
                    sims = [s for s in n['simbolos'] if s['tipo'] != 'método']
                    if sims:
                        mostrados = sims[:40]

                        def rotulo_sim(s):
                            if s['tipo'] == 'seção':
                                return f'{s["nome"]} (l. {s["linha"]})'
                            quem = usados_por.get((c, s['nome']), set())
                            return f'[{s["nome"]}]({rel(pag, c)}#L{s["linha"]}) (l. {s["linha"]}' + (f'; usado em {len(quem)}' if quem else '') + ')'
                        linhas.append('- **conteúdo** — ' + ', '.join(rotulo_sim(s) for s in mostrados)
                                      + (f' … e mais {len(sims) - 40}' if len(sims) > 40 else ''))
                    linhas.append('')
        (RAIZ / pag).write_text('\n'.join(linhas).rstrip() + '\n', encoding='utf-8')
        gerados.append(pag)

    # ----- índice de símbolos -----
    s = ['# Índice de símbolos', '', 'Toda função, classe e método de topo dos arquivos Python e JavaScript, em ordem alfabética, com arquivo e linha. '
         'Seções de documentos ficam nas páginas de cada pasta. ← ' + lnk('mapa/simbolos.md', 'MAPA.md', 'MAPA.md'), '']
    todos = sorted(((sim['nome'], sim['tipo'], c, sim['linha']) for c, n in nos.items() for sim in n['simbolos'] if sim['tipo'] != 'seção'),
                   key=lambda x: (x[0].lower().lstrip('_'), x[2]))
    letra = None
    for nome, tipo, c, linha in todos:
        inicial = nome.lstrip('_')[:1].upper() or '_'
        if inicial != letra:
            letra = inicial
            s += ['', f'## {letra}', '']
        quem = usados_por.get((c, nome), set())
        s.append(f'- `{nome}` ({tipo}) — [{c}:{linha}]({rel("mapa/simbolos.md", c)}#L{linha})'
                 + (f' · usado em {len(quem)}: ' + ', '.join(PurePosixPath(q).name for q in sorted(quem)[:6]) + (' …' if len(quem) > 6 else '') if quem else ''))
    (SAIDA / 'simbolos.md').write_text('\n'.join(s) + '\n', encoding='utf-8')
    gerados.append('mapa/simbolos.md')

    gerados += escrever_conhecimento(dados, usados_por)

    # ----- grafo.json -----
    grafo = {'gerado_por': 'mapa/gerar_mapa.py',
             'como_consultar': 'python mapa/consultar.py TERMO | --caminho A B | --vizinhos X --profundidade N',
             'tipos_de_no': {'arquivo': 'lista `nos` (id = caminho)', 'conceito': 'lista `conceitos` (id = E12, R17, H012, Q042, S05, V13)',
                             'simbolo': 'lista `simbolos` (id = caminho::nome)'},
             'tipos_de_aresta': {'importa': 'arquivo → arquivo: import Python resolvido',
                                 'link': 'arquivo → arquivo: link Markdown',
                                 'cita': 'arquivo → arquivo: o texto nomeia o outro pelo caminho ou pelo nome único',
                                 'usa': 'arquivo → símbolo: chama função ou classe de outro arquivo',
                                 'define/executa/resultado/pré-registra/prova/registra/documenta/responde/adjudica/testa/emenda':
                                     'arquivo → conceito: o papel do arquivo naquele estudo',
                                 'menciona': 'arquivo → conceito: cita o identificador; `peso` = número de menções',
                                 'apoia-se em': 'conceito → conceito: a evidência de um vem do outro'},
             'pastas': [{'id': p, 'finalidade': finalidade(p), 'pagina': pagina_da_pasta(p), 'arquivos': total(p)} for p in pastas],
             'nos': [{k_: v for k_, v in n.items() if k_ != 'simbolos'} | {'simbolos': [f'{x["nome"]}:{x["linha"]}' for x in n['simbolos'] if x['tipo'] != 'seção']} for n in nos.values()],
             'conceitos': [conceitos[c] for c in sorted(conceitos, key=k.ordem)],
             'simbolos': [{'id': f'{c}::{x["nome"]}', 'arquivo': c, 'nome': x['nome'], 'tipo': x['tipo'], 'linha': x['linha'],
                           'usado_por': sorted(usados_por.get((c, x['nome']), set()))}
                          for c, n in nos.items() for x in n['simbolos'] if x['tipo'] in ('função', 'classe')],
             'arestas': [{'de': a, 'para': b, 'tipo': t} for a, b, t in arestas]
                        + [{'de': a, 'para': f'{alvo}::{nome}', 'tipo': 'usa'} for a, alvo, nome in dados['usos']]
                        + [{'de': a, 'para': b, 'tipo': t} | ({'peso': p} if t == 'menciona' else {}) for (a, b, t), p in sorted(ac.items())]}
    (SAIDA / 'grafo.json').write_text(json.dumps(grafo, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    gerados.append('mapa/grafo.json')
    return gerados


ROTULOS = {
    'familia': 'família', 'veredito': 'veredito', 'medido': 'mediu', 'natureza': 'natureza', 'previsao': 'previsão',
    'criterio': 'critério', 'fonte': 'fonte', 'detalhe': 'detalhe', 'resposta': 'resposta',
    'fonte_da_resposta': 'origem da resposta', 'confianca': 'confiança', 'decide': 'decide',
    'rodada_simples': 'rodada simples', 'teto': 'teto Jev / LLM auxiliar', 'rotulo_no_codigo': 'marca no código',
}
PAGINAS_C = {
    'E': ('Experimentos', 'Os experimentos pré-registrados do estudo (E1–E16). Cada um liga pré-registro, executor, adjudicação, testes e resultados.'),
    'R': ('Rodadas do laboratório', 'O programa E14: rodadas R0–R27 com pré-registro em `laboratorio/PREREGISTRO.md`, um script e um artefato de resultado cada.'),
    'H': ('Hipóteses', 'As cem hipóteses falsificáveis (H001–H100): enunciado, previsão, critério, veredito e o que foi medido, com as rodadas em que cada prova se apoia.'),
    'Q': ('Perguntas estratégicas', 'As cem perguntas de decisão (Q001–Q100): a resposta, de onde ela vem (dado medido, conta declarada, coleta nova) e com que confiança.'),
    'S': ('Sistemas avaliados', 'Os 15 sistemas do ecossistema Jev cobertos pelo plano (S01–S15), da tabela do protocolo.'),
    'V': ('Revisões adversariais', 'As rodadas de revisão independente do executor, marcadas `[Rn]` nos comentários do código (não confundir com as rodadas do laboratório). Os testes `test_achados_revisaoN.py` fixam o que cada uma achou.'),
}
RE_PENDENCIA = re.compile(r'\b(não medid[ao]s?|pendentes?|bloquead[ao]s?|próximos? passos?|próximos movimentos|em aberto|não testad[ao]s?|'
                          r'não executad[ao]s?|decisão do Igor|ainda não|falta medir|sem medida)\b', re.I)


def escrever_conhecimento(dados: dict, usados_por: dict) -> list[str]:
    import conhecimento as k
    nos, conceitos, ac = dados['nos'], dados['conceitos'], dados['arestas_c']
    pasta = SAIDA / 'conhecimento'
    pasta.mkdir(parents=True, exist_ok=True)
    for velho in pasta.glob('*.md'):
        velho.unlink()
    saem, chegam = defaultdict(list), defaultdict(list)
    for (a, b, t), peso in ac.items():
        saem[a].append((b, t, peso))
        chegam[b].append((a, t, peso))
    gerados = []

    def lc(de: str, cid: str, texto: str | None = None) -> str:
        return f'[{texto or cid}]({rel(de, k.pagina(cid))}#{k.ancora(cid)})'

    def la(de: str, arq: str, linha: int | None = None, texto: str | None = None) -> str:
        alvo = rel(de, arq) + (f'#L{linha}' if linha else '')
        return f'[{texto or (arq + (f":{linha}" if linha else ""))}]({alvo})'

    por_tipo = defaultdict(list)
    for cid in sorted(conceitos, key=k.ordem):
        por_tipo[cid[0]].append(cid)

    for letra, (titulo, intro) in PAGINAS_C.items():
        pag = k.TIPOS[letra][1]
        ids = por_tipo[letra]
        L = [f'# {titulo}', '', intro, '', '← ' + lnk(pag, 'MAPA.md', 'MAPA.md') + ' · ' + ' · '.join(
            lnk(pag, k.TIPOS[x][1], PAGINAS_C[x][0]) for x in PAGINAS_C if x != letra)
            + ' · ' + lnk(pag, 'mapa/conhecimento/testes.md', 'Testes') + ' · ' + lnk(pag, 'mapa/conhecimento/lacunas.md', 'Lacunas e ideias'), '',
            f'**{len(ids)}** itens: ' + ' '.join(lc(pag, c) for c in ids), '']
        if letra == 'H':
            placar = Counter(conceitos[c]['atributos'].get('veredito', '?') for c in ids)
            L += ['Placar: ' + ', '.join(f'**{n}** {v}' for v, n in placar.most_common()) + '.', '']
            fam = defaultdict(Counter)
            for c in ids:
                fam[conceitos[c]['atributos'].get('familia', '?')][conceitos[c]['atributos'].get('veredito', '?')] += 1
            L += ['| família | ' + ' | '.join(v for v, _ in placar.most_common()) + ' |', '|---|' + '---:|' * len(placar)]
            for f in sorted(fam):
                L.append(f'| {f} | ' + ' | '.join(str(fam[f][v] or '') for v, _ in placar.most_common()) + ' |')
            L.append('')
        if letra == 'Q':
            origem = Counter((conceitos[c]['atributos'].get('fonte_da_resposta', '?'), conceitos[c]['atributos'].get('confianca', '?')) for c in ids)
            L += ['| origem da resposta | confiança | perguntas |', '|---|---|---:|'] + [f'| {o} | {cf} | {n} |' for (o, cf), n in origem.most_common()] + ['']
        if letra in 'ER':
            L += ['| id | título | executa | pré-registro | resultados | outras peças |', '|---|---|---|---|---:|---|']
            for c in ids:
                d = conceitos[c]['definido_em']
                ex = [x for x in d if x['papel'] == 'executa']
                pr = [x for x in d if x['papel'] == 'pré-registra']
                rs = [x for x in d if x['papel'] == 'resultado']
                outras = [x for x in d if x['papel'] not in ('executa', 'pré-registra', 'resultado')]
                L.append(f'| {lc(pag, c)} | {conceitos[c]["titulo"][:90]} | ' + ', '.join(la(pag, x['arquivo'], texto=PurePosixPath(x['arquivo']).name) for x in ex)
                         + ' | ' + ', '.join(la(pag, x['arquivo'], x['linha'], PurePosixPath(x['arquivo']).name) for x in pr) + f' | {len(rs)} | '
                         + ', '.join(f'{x["papel"]}: ' + la(pag, x['arquivo'], texto=PurePosixPath(x['arquivo']).name) for x in outras) + ' |')
            L.append('')
            linhagem = [(a, b) for a in ids for b, t, _ in saem[a] if t == 'apoia-se em' and b[0] in 'ER']
            if linhagem and len(linhagem) <= 150:
                L += ['## Linhagem', '', 'Quem se apoia em quem: a seta sai do estudo que usa o resultado de outro, lida do pré-registro e das seções de resultado.', '',
                      '```mermaid', 'flowchart LR']
                for a, b in linhagem:
                    L.append(f'  {a} --> {b}')
                L += ['```', '']
        L += ['## Itens', '']
        for c in ids:
            cd = conceitos[c]
            L += [f'<a id="{k.ancora(c)}"></a>', '', f'### {c} — {cd["titulo"]}', '']
            for chave, valor in cd['atributos'].items():
                if chave in ROTULOS:
                    L.append(f'- **{ROTULOS[chave]}:** {primeira_frase_md(str(valor))}')
            for chave in ('emendas', 'retratacoes', 'secoes'):
                itens = cd['atributos'].get(chave)
                if itens:
                    nome = {'emendas': 'emendas', 'retratacoes': 'retratações', 'secoes': 'seções no pré-registro'}[chave]
                    if chave == 'secoes':
                        L.append(f'- **{nome}:** ' + '; '.join(la(pag, 'laboratorio/PREREGISTRO.md', s['linha'], s['titulo'][:80]) for s in itens))
                    else:
                        L.append(f'- **{nome}:** ' + '; '.join(primeira_frase_md(str(x)) for x in itens))
            if cd['definido_em']:
                L.append('- **onde está:** ' + '; '.join(f'{d["papel"]} ' + la(pag, d['arquivo'], d['linha']) for d in cd['definido_em']))
            apoia = sorted({b for b, t, _ in saem[c] if t == 'apoia-se em'}, key=k.ordem)
            if apoia:
                L.append('- **apoia-se em:** ' + ', '.join(lc(pag, b, f'{b}') for b in apoia))
            sustenta = sorted({a for a, t, _ in chegam[c] if t == 'apoia-se em' and a in conceitos}, key=k.ordem)
            if sustenta:
                L.append('- **sustenta:** ' + ', '.join(lc(pag, a) for a in sustenta))
            mencoes = sorted(((a, p) for a, t, p in chegam[c] if t == 'menciona' and a in nos), key=lambda x: (-x[1], x[0]))
            if mencoes:
                L.append(f'- **mencionado em {len(mencoes)} arquivo' + ('s' if len(mencoes) > 1 else '') + ':** ' + ', '.join(f'{la(pag, a, texto=a)} ({p}×)' for a, p in mencoes[:12])
                         + (f' … e mais {len(mencoes) - 12}' if len(mencoes) > 12 else ''))
            L.append('')
        (RAIZ / pag).write_text('\n'.join(L).rstrip() + '\n', encoding='utf-8')
        gerados.append(pag)

    # ----- testes -----
    pag = 'mapa/conhecimento/testes.md'
    arestas = dados['arestas']
    testes = sorted(c for c in nos if '/tests/' in c and PurePosixPath(c).name.startswith('test_') and c.endswith('.py'))
    importa = defaultdict(set)
    for a, b, t in arestas:
        if t == 'importa':
            importa[a].add(b)
    usa_sim = defaultdict(set)
    for a, alvo, nome in dados['usos']:
        usa_sim[a].add((alvo, nome))
    testados = {b for t_ in testes for b in importa[t_]} | {alvo for t_ in testes for alvo, _ in usa_sim[t_]}
    n_funcoes = {t_: len(re.findall(r'^\s*def (test_\w+)', dados['textos'][t_], re.M)) for t_ in testes}
    L = ['# Testes', '', f'**{len(testes)} arquivos de teste** com **{sum(n_funcoes.values())} funções `test_`**, rodados por `python -m pytest` '
         '(pastas em `pytest.ini`). Para cada arquivo: o que ele exercita (módulos e funções) e que estudos ele fixa.', '',
         '← ' + lnk(pag, 'MAPA.md', 'MAPA.md') + ' · ' + lnk(pag, 'mapa/conhecimento/lacunas.md', 'Lacunas e ideias'), '',
         '| arquivo | testes | módulos exercitados | estudos |', '|---|---:|---|---|']
    for t_ in testes:
        mods = sorted(b for b in importa[t_] if '/tests/' not in b and not b.endswith('__init__.py'))
        estudos = sorted({b for (a, b, tp), _ in ac.items() if a == t_}, key=k.ordem)
        L.append(f'| {la(pag, t_, texto=t_)} | {n_funcoes[t_]} | ' + ', '.join(la(pag, b, texto=PurePosixPath(b).name) for b in mods)
                 + ' | ' + ', '.join(lc(pag, e) for e in estudos) + ' |')
    L += ['', '## Funções exercitadas por cada teste', '']
    for t_ in testes:
        sims = sorted(usa_sim[t_])
        if sims:
            L.append(f'- {la(pag, t_, texto=PurePosixPath(t_).name)} — ' + ', '.join(
                f'`{PurePosixPath(alvo).stem}.{nome}`' for alvo, nome in sims))
    bibliotecas = sorted(c for c in nos if c.endswith('.py') and '/tests/' not in c and not c.endswith('__init__.py')
                         and c not in testados and any(c in importa[a] for a in nos if '/tests/' not in a))
    scripts = sorted(c for c in nos if c.endswith('.py') and '/tests/' not in c and not c.endswith('__init__.py')
                     and c not in testados and c not in bibliotecas and not c.startswith(('research/', 'planning/')))
    L += ['', '## Código sem teste direto', '',
          'Nenhum arquivo de teste importa estes módulos nem usa funções deles. Cobertura indireta (por outro módulo que os chama) não aparece aqui.', '',
          f'**Módulos usados por outros módulos ({len(bibliotecas)})** — onde um teste rende mais:', '']
    L += [f'- {la(pag, c, texto=c)} — {nos[c]["descricao"]}' for c in bibliotecas]
    L += ['', f'**Scripts de execução ({len(scripts)})** — rodam uma vez e gravam artefato; o teste costuma ser o próprio artefato auditado:', '',
          ', '.join(la(pag, c, texto=PurePosixPath(c).name) for c in scripts), '']
    (RAIZ / pag).write_text('\n'.join(L).rstrip() + '\n', encoding='utf-8')
    gerados.append(pag)

    # ----- lacunas e ideias -----
    pag = 'mapa/conhecimento/lacunas.md'
    L = ['# Lacunas e ideias abertas', '',
         'O que o próprio repositório declara como não sabido, falsificado, pendente ou sem teste. É por aqui que se decide o próximo estudo.', '',
         '← ' + lnk(pag, 'MAPA.md', 'MAPA.md') + ' · ' + lnk(pag, 'mapa/conhecimento/testes.md', 'Testes'), '']
    fals = [c for c in por_tipo['H'] if conceitos[c]['atributos'].get('veredito') != 'sustentada']
    L += [f'## Hipóteses que não se sustentaram ({len(fals)})', '', 'Cada uma é um limite medido do Jev, ou uma pergunta que a medição não fechou.', '']
    L += [f'- {lc(pag, c)} ({conceitos[c]["atributos"].get("veredito")}, mediu {conceitos[c]["atributos"].get("medido", "?")}) — {conceitos[c]["titulo"]}' for c in fals]
    fracas = [c for c in por_tipo['Q'] if conceitos[c]['atributos'].get('fonte_da_resposta') != 'dado medido' or conceitos[c]['atributos'].get('confianca') != 'alta']
    L += ['', f'## Perguntas respondidas sem dado medido ou sem confiança alta ({len(fracas)})', '',
          'A resposta existe, mas depende de parâmetro declarado ou de coleta pequena: medir isso é trabalho com retorno direto.', '']
    L += [f'- {lc(pag, c)} ({conceitos[c]["atributos"].get("fonte_da_resposta", "?")}; confiança {conceitos[c]["atributos"].get("confianca", "?")}) — {conceitos[c]["titulo"]}' for c in fracas]
    sem_prereg = [c for c in por_tipo['E'] if not any(d['papel'] == 'pré-registra' for d in conceitos[c]['definido_em'])]
    sem_script = [c for c in por_tipo['R'] if not any(d['papel'] == 'executa' for d in conceitos[c]['definido_em'])]
    sem_result = [c for c in por_tipo['R'] if not any(d['papel'] == 'resultado' for d in conceitos[c]['definido_em'])]
    retratadas = [c for c in conceitos if conceitos[c]['atributos'].get('retratacoes')]
    L += ['', '## Estudos com peça faltando', '',
          '- **experimentos sem pré-registro próprio em `planning/`:** ' + (', '.join(lc(pag, c) for c in sem_prereg) or 'nenhum'),
          '- **rodadas sem script próprio** (medidas dentro do script de outra rodada ou só documentadas): ' + (', '.join(lc(pag, c) for c in sem_script) or 'nenhuma'),
          '- **rodadas sem artefato de resultado próprio:** ' + (', '.join(lc(pag, c) for c in sem_result) or 'nenhuma'),
          '- **rodadas com condição retratada:** ' + (', '.join(lc(pag, c) for c in retratadas) or 'nenhuma'), '',
          '## Código sem teste direto', '', f'{len(bibliotecas)} módulos usados por outros módulos não têm teste que os importe: lista em '
          + lnk(pag, 'mapa/conhecimento/testes.md', 'Testes') + '.', '']
    L += ['## Pendências declaradas nos documentos', '', 'Linhas dos documentos que dizem "não medido", "pendente", "bloqueado", "em aberto", "próximo passo" ou "decisão do Igor".', '']
    docs_md = sorted(c for c in nos if c.endswith('.md'))
    for c in docs_md:
        achadas = []
        for i, linha in enumerate(dados['textos'][c].splitlines(), 1):
            if RE_PENDENCIA.search(linha) and not linha.lstrip().startswith('|'):
                achadas.append((i, primeira_frase_md(linha.strip('#*-> ').strip(), 170)))
        if achadas:
            L.append(f'**{la(pag, c, texto=c)}**')
            L.append('')
            L += [f'- {la(pag, c, i, f"l. {i}")} — {t}' for i, t in achadas[:15]]
            if len(achadas) > 15:
                L.append(f'- … e mais {len(achadas) - 15} linhas')
            L.append('')
    (RAIZ / pag).write_text('\n'.join(L).rstrip() + '\n', encoding='utf-8')
    gerados.append(pag)
    return gerados


def primeira_frase_md(texto: str, limite: int = 400) -> str:
    texto = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', ' '.join(texto.split())).replace('|', '/')
    return texto if len(texto) <= limite else texto[:limite - 1].rstrip() + '…'


def linha_do_simbolo(nos: dict, arquivo: str, nome: str) -> int:
    return next((s['linha'] for s in nos[arquivo]['simbolos'] if s['nome'] == nome), 1)


def consistencia() -> list[str]:
    """O grafo gravado tem de ser fechado: toda aresta liga nós que existem, e as coleções do estudo estão completas."""
    g = json.loads((SAIDA / 'grafo.json').read_text(encoding='utf-8'))
    ids = {n['id'] for n in g['nos']} | {c['id'] for c in g['conceitos']} | {s['id'] for s in g['simbolos']}
    erros = [f'aresta solta: {a["de"]} -> {a["para"]} ({a["tipo"]})' for a in g['arestas'] if a['de'] not in ids or a['para'] not in ids]
    tipos = Counter(c['id'][0] for c in g['conceitos'])
    for letra, esperado in (('H', 100), ('Q', 100), ('S', 15)):
        if tipos[letra] != esperado:
            erros.append(f'{letra}: {tipos[letra]} conceitos, esperado {esperado}')
    return erros


def verificar(gerados: list[str]) -> list[str]:
    """Todo link relativo das páginas geradas tem de apontar para algo que existe."""
    quebrados = consistencia()
    ancoras: dict[Path, str] = {}
    for g in gerados:
        if not g.endswith('.md'):
            continue
        texto = (RAIZ / g).read_text(encoding='utf-8')
        for alvo in re.findall(r'\]\(([^)\s]+)\)', texto):
            caminho, _, ancora = alvo.replace('%20', ' ').partition('#')
            destino = (RAIZ / PurePosixPath(g).parent / caminho if caminho else RAIZ / g).resolve()
            if not destino.exists():
                quebrados.append(f'{g} -> {alvo}')
            elif ancora and not re.fullmatch(r'L\d+', ancora) and destino.suffix == '.md' and destino.is_relative_to(SAIDA):
                if f'<a id="{ancora}"></a>' not in ancoras.setdefault(destino, destino.read_text(encoding='utf-8')):
                    quebrados.append(f'{g} -> {alvo} (âncora inexistente)')
    return quebrados


def main() -> int:
    dados = montar()
    gerados = escrever(dados)
    quebrados = verificar(gerados)
    print(f'{len(dados["nos"])} arquivos, {len(dados["pastas"])} pastas, {len(dados["arestas"])} relações; {len(gerados)} arquivos do mapa gerados.')
    if quebrados:
        print(f'{len(quebrados)} links quebrados:', *quebrados[:30], sep='\n  ')
        return 1
    if '--verificar' in sys.argv:
        print('Todos os links do mapa resolvem.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
