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
                  and not p.startswith('mapa/pastas/'))


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
    return {'nos': nos, 'arestas': sorted(arestas), 'pastas': pastas, 'textos': textos}


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
         f'**{len(nos)} arquivos** em **{len(pastas)} pastas**, ligados por **{len(arestas)} relações** '
         f'({sum(1 for *_, t in arestas if t == "importa")} imports, {sum(1 for *_, t in arestas if t == "link")} links, '
         f'{sum(1 for *_, t in arestas if t == "cita")} citações).', '',
         '## Como usar este mapa', '',
         '- **Achar um arquivo por assunto:** a tabela "Onde está" abaixo, depois a página da pasta.',
         '- **Achar uma função, classe ou seção:** ' + lnk('MAPA.md', 'mapa/simbolos.md', 'mapa/simbolos.md') + ' (nome → arquivo:linha).',
         '- **Ver quem usa um arquivo:** a página da pasta mostra, para cada arquivo, o que ele usa e quem o usa.',
         '- **Grafo para programas:** ' + lnk('MAPA.md', 'mapa/grafo.json', 'mapa/grafo.json') + ' (nós = arquivos com descrição; arestas `importa`, `link`, `cita`).',
         '- **Fora do mapa de propósito:** `.env` (chave OpenRouter, nunca abrir), `.venv-s08/`, `graphify-out/`, `.planning/`, '
         '`runs/ledger.sqlite3`, `research/sources/`, `research/hermes/raw/`, material privado de `integracao/avaliacao/` '
         'e estado operacional de `integracao/` — tudo que o `.gitignore` exclui.', '',
         '## Onde está', '', '| preciso de | comece por |', '|---|---|']
    for tarefa, caminhos in ONDE:
        validos = [c for c in caminhos if c in nos]
        m.append(f'| {tarefa} | ' + ', '.join(lnk('MAPA.md', c, f'`{c}`') for c in validos) + ' |')
    m += ['', '## Pastas', '', '| pasta | arquivos | finalidade |', '|---|---:|---|']

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
        for k, cs in exps:
            m.append(f'| {k} | ' + ' · '.join(lnk('MAPA.md', c, PurePosixPath(c).name if not c.startswith('runs/') else c[5:]) for c in cs) + ' |')
        m.append('')
    rods = rodadas(nos)
    if rods:
        m += ['## Rodadas do laboratório: script e resultado', '', '| rodada | arquivos |', '|---|---|']
        for k, cs in rods:
            m.append(f'| {k} | ' + ' · '.join(lnk('MAPA.md', c, PurePosixPath(c).name) for c in cs) + ' |')
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
            com_ligacao = [c for c in meus if saem[c] or chegam[c] or nos[c]['simbolos']]
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
                    sims = [s for s in n['simbolos'] if s['tipo'] != 'método']
                    if sims:
                        mostrados = sims[:40]
                        linhas.append('- **conteúdo** — ' + ', '.join(f'[{s["nome"]}]({rel(pag, c)}#L{s["linha"]}) (l. {s["linha"]})' if s['tipo'] != 'seção' else f'{s["nome"]} (l. {s["linha"]})' for s in mostrados)
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
        s.append(f'- `{nome}` ({tipo}) — [{c}:{linha}]({rel("mapa/simbolos.md", c)}#L{linha})')
    (SAIDA / 'simbolos.md').write_text('\n'.join(s) + '\n', encoding='utf-8')
    gerados.append('mapa/simbolos.md')

    # ----- grafo.json -----
    grafo = {'gerado_por': 'mapa/gerar_mapa.py',
             'tipos_de_aresta': {'importa': 'import Python resolvido para arquivo do repositório',
                                 'link': 'link Markdown para arquivo do repositório',
                                 'cita': 'o texto nomeia o arquivo pelo caminho ou pelo nome único'},
             'pastas': [{'id': p, 'finalidade': finalidade(p), 'pagina': pagina_da_pasta(p), 'arquivos': total(p)} for p in pastas],
             'nos': [{k: v for k, v in n.items() if k != 'simbolos'} | {'simbolos': [f'{x["nome"]}:{x["linha"]}' for x in n['simbolos'] if x['tipo'] != 'seção']} for n in nos.values()],
             'arestas': [{'de': a, 'para': b, 'tipo': t} for a, b, t in arestas]}
    (SAIDA / 'grafo.json').write_text(json.dumps(grafo, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    gerados.append('mapa/grafo.json')
    return gerados


def verificar(gerados: list[str]) -> list[str]:
    """Todo link relativo das páginas geradas tem de apontar para algo que existe."""
    quebrados = []
    for g in gerados:
        if not g.endswith('.md'):
            continue
        texto = (RAIZ / g).read_text(encoding='utf-8')
        for alvo in re.findall(r'\]\(([^)\s]+)\)', texto):
            caminho = alvo.split('#')[0].replace('%20', ' ')
            if caminho and not (RAIZ / PurePosixPath(g).parent / caminho).exists():
                quebrados.append(f'{g} -> {alvo}')
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
