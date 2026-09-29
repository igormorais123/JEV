"""Fluxo 1 — avaliações: "ficou bom o suficiente para seguir?".

O quadro: agente de código implementa → diferenças + testes + registros → JEV avalia →
APROVADO, REFAZER ou HUMANO; "a avaliação não gera só uma nota → ela muda o fluxo". O
`workflows.judge` já dava o veredito; este módulo fecha o laço:

- **Evidência observada pelo harness, nunca relatada pelo agente.** `observar_testes` roda o
  comando de teste que quem montou a tarefa escolheu e conta o resultado; `observar_diff` lê o
  `git diff` da pasta. O agente não escreve nenhuma das duas.
- **REFAZER devolve ao agente o que falhou**: as faltas objetivas (testes que falharam, código de
  saída) e os critérios que o Jev leu como não atendidos com confiança ≥ 0,90 nas evidências
  verificadas. Refazer é o erro barato — custa uma tentativa, limitada —; aprovar é o caro, e só o
  `judge` aprova.
- **HUMANO** quando as tentativas acabam, quando refazer não mudou o resultado (mesmas faltas duas
  vezes), quando o caso é sensível ou quando a avaliação não tem evidência. Com `--avisar`, Igor
  recebe o resumo no WhatsApp.
- O modelo de cada tentativa vem do fluxo 3 (`modelos`): a segunda tentativa sobe um nível.

CLI: `python3 -m jev_hermes.avaliacao --pasta DIR --pedido TASK.md --teste "python3 -m pytest -q"
[--criterio "id: descrição"]... [--max-tentativas 3] [--orcamento 5] [--avisar]`.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from . import isolamento, modelos, nucleo, workflows

REGISTRO = nucleo.ESTADO / 'avaliacoes.jsonl'
CORTE_REFAZER = 0.90
MAX_TENTATIVAS = 3
CAUDA = 3500   # caracteres finais da saída de teste que entram na evidência
# Sem critério declarado: o pedido, qualquer que seja o tipo (correção, funcionalidade, pesquisa).
CRITERIO_PADRAO = {'id': 'pedido-atendido', 'descricao': (
    'As mudancas observadas fazem o que o PEDIDO ORIGINAL pede (correcao, funcionalidade, refatoracao '
    'ou o arquivo de resposta pedido) e respeitam o que ele proibe.')}


# ------------------------------------------------------------------------ observadores

def contar(texto, codigo_saida):
    """Contagem de testes lida da saída do pytest ou do unittest. None onde não dá para ler."""
    passaram = falharam = executados = None
    achados = dict((m.group(2), int(m.group(1))) for m in
                   re.finditer(r'(\d+) (passed|failed|errors?|skipped)', texto or ''))
    if achados:
        passaram = achados.get('passed', 0)
        falharam = achados.get('failed', 0) + achados.get('error', 0) + achados.get('errors', 0)
        executados = passaram + falharam
    rodados = re.search(r'Ran (\d+) tests?', texto or '')
    if rodados and executados is None:
        executados = int(rodados.group(1))
        falhas = re.search(r'FAILED \((?:failures=(\d+))?(?:, )?(?:errors=(\d+))?', texto or '')
        falharam = sum(int(g) for g in falhas.groups() if g) if falhas else 0
        passaram = executados - falharam
    return {'executados': executados, 'passaram': passaram, 'falharam': falharam, 'codigo_saida': codigo_saida}


def observar_testes(comando, pasta, timeout=600):
    """Roda o comando de teste (sem shell, isolado) e devolve a Observacao com a contagem lida."""
    partes = shlex.split(comando)
    try:
        if not (shutil.which(partes[0]) or (Path(pasta) / partes[0]).exists()):
            raise FileNotFoundError(partes[0])   # dentro do bwrap viraria só "saiu com 1"
        processo = subprocess.run(isolamento.isolar(partes, pasta), cwd=str(pasta), capture_output=True, text=True,
                                  timeout=timeout)
        texto, codigo = (processo.stdout or '') + (processo.stderr or ''), processo.returncode
    except subprocess.TimeoutExpired:
        texto, codigo = f'tempo esgotado depois de {timeout} s', 124
    except FileNotFoundError:
        texto, codigo = f'comando não encontrado: {partes[0]}', 127
    return workflows.Observacao(tipo='teste', origem=f'harness:{Path(partes[0]).name}', referencia=comando[:300],
                                conteudo=texto[-CAUDA:], resultado=contar(texto, codigo))


def _git(pasta, *argumentos):
    return subprocess.run(['git', *argumentos], cwd=str(pasta), capture_output=True, text=True, timeout=60)


def linha_de_base(pasta):
    """Onde o agente começou: o commit do estado atual (inclusive mudanças não commitadas, sem mexer
    no índice nem na árvore) e os arquivos não rastreados que já existiam. None fora de git."""
    if _git(pasta, 'rev-parse', '--is-inside-work-tree').returncode != 0:
        return None
    base = _git(pasta, 'stash', 'create').stdout.strip() or 'HEAD'
    antes = set(_git(pasta, 'ls-files', '--others', '--exclude-standard').stdout.splitlines())
    return {'commit': base, 'nao_rastreados': sorted(antes)}


# Caches que rodar o Python e o pytest geram: não são mudança do agente e, no diff, só apareciam como
# "arquivo binário novo", ruído que baixava a confiança do juiz abaixo do corte.
CACHE = re.compile(r'(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache)/|\.py[co]$')


def _novos(pasta, base):
    agora = set(_git(pasta, 'ls-files', '--others', '--exclude-standard').stdout.splitlines())
    return sorted(n for n in agora - set(base['nao_rastreados']) if not CACHE.search(n))


def observar_diff(pasta, base=None):
    """O que o agente mudou desde a linha de base, com os arquivos novos. Não altera o índice do
    repositório; arquivo novo com nome de segredo entra só pelo nome, nunca pelo conteúdo."""
    base = base or linha_de_base(pasta)
    if base is None:
        return None
    diff = _git(pasta, 'diff', base['commit'], '--stat').stdout + '\n' + _git(pasta, 'diff', base['commit']).stdout
    for nome in _novos(pasta, base):
        if workflows.NOME_SECRETO.search(nome):
            diff += f'\n(arquivo novo com nome de segredo, conteúdo omitido: {nome})'
        else:
            diff += '\n' + _git(pasta, 'diff', '--no-index', '--', os.devnull, nome).stdout
    return workflows.Observacao(tipo='diff', origem='harness:git', referencia=f"git diff {base['commit'][:12]}",
                                conteudo=diff.strip()[:workflows.MAX_EVIDENCIA - 200] or '(nenhuma mudança)')


ARQUIVO_DE_TESTE = re.compile(r'(^|/)(tests?/|test_[^/]*\.py$|[^/]*_test\.py$|conftest\.py$)')
CONFIG_DE_TESTE = re.compile(r'(^|/)(conftest\.py|pytest\.ini|tox\.ini|setup\.cfg|pyproject\.toml|noxfile\.py)$')


def observar_integridade(pasta, base):
    """Guarda do harness contra o agente que se aprova mexendo nos testes: linha removida ou
    trocada num arquivo de teste que já existia, arquivo de teste apagado, ou configuração do
    pytest criada. Acrescentar teste novo é livre. Devolve uma Observacao de falha, ou None."""
    if base is None:
        return None
    problemas = []
    for linha in _git(pasta, 'diff', '--numstat', base['commit']).stdout.splitlines():
        partes = linha.split('\t')
        if len(partes) == 3 and ARQUIVO_DE_TESTE.search(partes[2]) and partes[1] not in ('0', '-'):
            problemas.append(f'{partes[2]}: {partes[1]} linha(s) de teste removida(s) ou alterada(s)')
    for nome in _novos(pasta, base):
        if CONFIG_DE_TESTE.search(nome):
            problemas.append(f'{nome}: configuração do pytest criada pelo agente')
    if not problemas:
        return None
    return workflows.Observacao(tipo='teste', origem='harness:integridade', referencia='integridade dos testes',
                                conteudo='O agente mexeu no que o avalia:\n' + '\n'.join(problemas),
                                resultado={'executados': 1, 'passaram': 0, 'falharam': 1, 'codigo_saida': 1})


CITADO = re.compile(r'[\w./-]+\.[A-Za-z]{1,5}\b')
MAX_CITADOS, MAX_CITADO = 3, 3000


def observar_citados(pasta, diff):
    """Arquivos do repositório que as mudanças citam sem alterá-los — o código que um laudo aponta,
    por exemplo. Sem eles o juiz vê a conclusão, mas não a fonte para conferi-la. Só arquivos
    rastreados, pequenos e sem nome de segredo (`workflows.observar_arquivo` recusa o resto)."""
    if diff is None:
        return []
    rastreados = set(_git(pasta, 'ls-files').stdout.splitlines())
    alterados = set(re.findall(r'^diff --git a/(\S+)', diff.conteudo, re.M))
    acrescentado = '\n'.join(l[1:] for l in diff.conteudo.splitlines() if l.startswith('+') and not l.startswith('+++'))
    citados = []
    for nome in dict.fromkeys(m.removeprefix('./') for m in CITADO.findall(acrescentado)):
        if nome in rastreados and nome not in alterados and (Path(pasta) / nome).stat().st_size <= MAX_CITADO:
            try:
                citados.append(workflows.observar_arquivo(nome, [pasta], tipo='artefato'))
            except workflows.EntradaInvalida:
                continue
        if len(citados) == MAX_CITADOS:
            break
    return citados


def observar_tudo(comando_teste, pasta, base):
    """A evidência que o juiz recebe nos fluxos 1 e 2: testes, diff, arquivos citados e integridade."""
    diff = observar_diff(pasta, base)
    return [o for o in (observar_testes(comando_teste, pasta), diff, *observar_citados(pasta, diff),
                        observar_integridade(pasta, base)) if o is not None]


def preparar_git(pasta):
    """Pasta fora de repositório ganha um git com o estado inicial, para o diff medir só o agente."""
    if _git(pasta, 'rev-parse', '--is-inside-work-tree').returncode == 0:
        return False
    for argumentos in (['init', '-q'], ['add', '-A'],
                       ['-c', 'user.name=hermes', '-c', 'user.email=hermes@localhost', 'commit', '-qm', 'estado inicial',
                        '--allow-empty']):
        subprocess.run(['git', *argumentos], cwd=str(pasta), capture_output=True, check=True)
    return True


# ------------------------------------------------------------------------------ o laço

def _faltas_do_jev(veredito):
    """Critérios que o Jev leu como não atendidos com confiança alta nas evidências verificadas.
    Só contam se nada mais pede uma pessoa: caso sensível, ordem embutida ou sem evidência."""
    if veredito.get('sensivel') or not veredito.get('evidencias_verificadas'):
        return []
    if not (veredito.get('jev') or {}).get('consultado'):
        return []
    if any('tenta dar ordens' in m for m in veredito.get('motivos', [])):
        return []
    avaliacoes = veredito.get('criterios') or []
    if any(c['avaliacao_jev'] == 'sem-evidencia' for c in avaliacoes):
        return []
    return [f"critério {c['id']} não atendido pelas evidências (confiança {nucleo.dec(c['confianca'])})"
            for c in avaliacoes if c['avaliacao_jev'] == 'nao-atendido' and (c['confianca'] or 0) >= CORTE_REFAZER]


def laco(pedido, criterios, implementar, observar, *, max_tentativas=MAX_TENTATIVAS, sensivel=False,
         transporte=None, offline=None):
    """Implementar → observar → avaliar → aprovado / refazer / humano.

    `implementar(pedido, retorno, tentativa)` devolve {'texto': relato do agente, 'custo_usd', ...};
    `observar()` devolve a lista de `workflows.Observacao` que o harness leu depois da tentativa.
    """
    max_tentativas = max(1, min(int(max_tentativas), workflows.MAXIMO_DE_TENTATIVAS))
    criterios = list(criterios) or [CRITERIO_PADRAO]
    historico, retorno, faltas_anteriores = [], None, None
    for tentativa in range(1, max_tentativas + 1):
        inicio = time.time()
        relato = implementar(pedido, retorno, tentativa) or {}
        observacoes = [o for o in observar() if o is not None]
        veredito = workflows.judge({'pedido_original': pedido[:workflows.MAX_TEXTO], 'criterios': criterios,
                                    'resultado': (relato.get('texto') or '(o agente não relatou nada)')[:workflows.MAX_TEXTO],
                                    'tentativa': tentativa, 'max_tentativas': max_tentativas, 'sensivel': sensivel},
                                   observacoes=observacoes, offline=offline, transporte=transporte,
                                   sensivel_por_regra=False)
        faltas = veredito.get('faltas_reparaveis') or []
        if veredito['veredito'] == 'revisao_humana':
            faltas = faltas or _faltas_do_jev(veredito)
        passo = {'tentativa': tentativa, 'veredito': veredito['veredito'], 'faltas': faltas,
                 'motivos': veredito.get('motivos', []), 'custo_agente_usd': relato.get('custo_usd'),
                 'modelo': relato.get('modelo'), 'segundos': round(time.time() - inicio, 1),
                 'testes': next(((o.resultado or {}) for o in observacoes if o.tipo == 'teste'), None)}
        historico.append(passo)
        if veredito['veredito'] == 'passou':
            return _fim('aprovado', 'o judge aprovou com evidência verificada', historico)
        refazer = veredito['veredito'] == 'retry' or (bool(faltas) and not sensivel and tentativa < max_tentativas)
        if not refazer:
            break
        if faltas_anteriores is not None and sorted(faltas) == sorted(faltas_anteriores):
            return _fim('humano', 'refazer não mudou o resultado: as mesmas faltas duas vezes', historico)
        faltas_anteriores = faltas
        saida_teste = next((o.conteudo for o in observacoes if o.tipo == 'teste'), '')
        retorno = {'faltas': faltas, 'saida_dos_testes': saida_teste[-2000:]}
    ultimo = historico[-1]
    if ultimo['tentativa'] >= max_tentativas and ultimo['faltas']:
        motivo = f'tentativas esgotadas ({max_tentativas}) com faltas'
    else:
        motivo = '; '.join(ultimo['motivos'][:3]) or 'a avaliação pede uma pessoa'
    return _fim('humano', motivo, historico)


def _fim(resultado, motivo, historico):
    saida = {'resultado': resultado, 'motivo': motivo, 'tentativas': len(historico), 'historico': historico,
             'custo_agente_usd': round(sum(h.get('custo_agente_usd') or 0 for h in historico), 4)}
    nucleo.registrar({'em': nucleo._agora().isoformat(timespec='seconds'), 'resultado': resultado,
                      'tentativas': len(historico), 'custo_agente_usd': saida['custo_agente_usd'],
                      'vereditos': [h['veredito'] for h in historico]}, REGISTRO)
    return saida


# ------------------------------------------------------------------ tarefa de código real

FERRAMENTAS_DE_EDICAO = ['Read', 'Edit', 'Write', 'Glob', 'Grep', 'Bash(git diff:*)', 'Bash(git status:*)',
                         'Bash(ls:*)', 'Bash(cat:*)']


# O que o agente entrega além do código. O juiz só aceita o que o harness observa: teste novo vira
# evidência; verificação feita à mão, não. Relato com o que não aparece no diff leva a "insuficiente".
ENTREGA = ('Não altere nem apague os testes existentes. Se o pedido permite mudar código, acrescente testes '
           'novos que provem o que ele exige: eles viram evidência. Ao terminar, relate em até cinco linhas só '
           'o que aparece nas mudanças (arquivos, funções, testes acrescentados); não cite verificações feitas à '
           'mão nem contagens de testes, pois quem roda e confere os testes é o harness.')


def prompt_de_implementacao(pedido, criterios, comando_teste, retorno, tentativa):
    partes = [f'Você trabalha nesta pasta isolada. Tarefa:\n{pedido}']
    if criterios:
        partes.append('Critérios de aceite:\n' + '\n'.join(f"- {c['id']}: {c['descricao']}" for c in criterios))
    if retorno:
        partes.append(f'Esta é a tentativa {tentativa}. A avaliação da tentativa anterior encontrou:\n'
                      + '\n'.join(f'- {f}' for f in retorno['faltas'])
                      + f"\nFinal da saída dos testes:\n{retorno['saida_dos_testes']}")
    partes.append(f'Teste exatamente com: {comando_teste} (outro Python pode não ter pytest). {ENTREGA}')
    return '\n\n'.join(partes)


def tarefa_de_codigo(pasta, pedido, comando_teste, criterios=(), *, max_tentativas=MAX_TENTATIVAS,
                     orcamento_usd=5.0, sensivel=False, transporte=None):
    """O laço com um agente Claude Code de verdade. O modelo de cada tentativa vem do fluxo 3."""
    pasta = Path(pasta).resolve()
    preparar_git(pasta)
    base = linha_de_base(pasta)
    orcamento = modelos.Orcamento(orcamento_usd)
    estado = {'nivel': None}
    ferramentas = FERRAMENTAS_DE_EDICAO + [f'Bash({comando_teste}:*)']

    def implementar(pedido_, retorno, tentativa):
        decisao = modelos.escolher(f'Implementar em código: {pedido_}', orcamento, tentativa=tentativa,
                                   nivel_anterior=estado['nivel'], transporte=transporte)
        if not decisao.get('nivel'):
            modelos.registrar(decisao)
            return {'texto': f"sem orçamento: {decisao['motivo']}", 'custo_usd': 0.0}
        estado['nivel'] = decisao['nivel']
        feito = modelos.executar_claude(prompt_de_implementacao(pedido_, criterios, comando_teste, retorno, tentativa),
                                        pasta, decisao, ferramentas=ferramentas, orcamento=orcamento)
        modelos.registrar(decisao, feito['custo_usd'])
        if feito.get('limite'):   # limite da assinatura: a próxima tentativa escolhe de novo, sem subir
            estado['nivel'] = None
        return feito

    def observar():
        return observar_tudo(comando_teste, pasta, base)

    saida = laco(pedido, list(criterios), implementar, observar, max_tentativas=max_tentativas,
                 sensivel=sensivel, transporte=transporte)
    saida['orcamento'] = orcamento.como_dict()
    return saida


def avisar(texto, destino=None):
    """Mensagem a Igor pelo `hermes send` (sem modelo). Falha de envio não derruba o fluxo."""
    try:
        subprocess.run(['hermes', 'send', '-t', destino or 'whatsapp', texto], capture_output=True, timeout=60)
        return True
    except Exception:
        return False


def _criterios(textos):
    criterios = []
    for i, texto in enumerate(textos or [], 1):
        ident, _, descricao = texto.partition(':')
        if not descricao:
            ident, descricao = f'c{i}', texto
        criterios.append({'id': re.sub(r'[^a-z0-9_.-]', '-', ident.strip().lower())[:40] or f'c{i}',
                          'descricao': descricao.strip()})
    return criterios


if __name__ == '__main__':
    import argparse
    analisador = argparse.ArgumentParser(description='Fluxo 1: implementar, avaliar e refazer até aprovar ou escalar.')
    analisador.add_argument('--pasta', required=True)
    analisador.add_argument('--pedido', required=True, help='texto ou caminho de arquivo com a tarefa')
    analisador.add_argument('--teste', required=True, help='comando que o harness roda para observar os testes')
    analisador.add_argument('--criterio', action='append', help='"id: descrição" (repetível)')
    analisador.add_argument('--max-tentativas', type=int, default=MAX_TENTATIVAS)
    analisador.add_argument('--orcamento', type=float, default=5.0, help='US$ nominais do Claude Code')
    analisador.add_argument('--sensivel', action='store_true')
    analisador.add_argument('--avisar', action='store_true', help='avisa Igor no WhatsApp quando precisar de uma pessoa')
    a = analisador.parse_args()
    caminho_pedido = Path(a.pedido)
    texto_pedido = caminho_pedido.read_text(encoding='utf-8') if caminho_pedido.is_file() else a.pedido
    fim = tarefa_de_codigo(a.pasta, texto_pedido, a.teste, _criterios(a.criterio),
                           max_tentativas=a.max_tentativas, orcamento_usd=a.orcamento, sensivel=a.sensivel)
    if a.avisar and fim['resultado'] == 'humano':
        avisar(f"🔧 Tarefa de código precisa de você ({Path(a.pasta).name}): {fim['motivo']}. "
               f"{fim['tentativas']} tentativa(s), US$ {fim['custo_agente_usd']:.2f} nominais.")
    print(json.dumps(fim, ensure_ascii=False, indent=1))
