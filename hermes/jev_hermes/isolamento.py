"""Isolamento do código que os fluxos 1, 2 e 5 executam, com `bwrap`.

O agente escreve código e os testes o executam; nem um nem outro precisa ver o resto da máquina.
Dentro do isolamento, /root (onde ficam os segredos do Hermes, as chaves e os outros projetos) é
um diretório vazio em memória, /tmp também; volta a aparecer só a pasta da tarefa (gravável) e o
intérprete de quem roda os testes (somente leitura). O que for gravado fora da pasta some ao fim.

- Testes rodados pelo harness: sem rede.
- O `claude` do agente: com rede (ele fala com a API) e com a própria configuração
  (~/.claude e ~/.claude.json), sem a qual não há login.

Sem `bwrap` (Windows, testes locais) ou com JEV_ISOLAMENTO=0, o comando roda como está.
"""
import os
import re
import shutil
from pathlib import Path

CLAUDE = ('/root/.claude', '/root/.claude.json')


def _raizes(executavel):
    """Onde o executável e o que ele carrega moram: o ambiente virtual e a instalação real."""
    caminho = Path(shutil.which(executavel) or executavel)
    raizes = {caminho.parent.parent, Path(os.path.realpath(caminho)).parent.parent}
    config = caminho.parent.parent / 'pyvenv.cfg'
    if config.exists():
        casa = re.search(r'^home\s*=\s*(.+)$', config.read_text(encoding='utf-8'), re.M)
        if casa:
            raizes.add(Path(casa.group(1).strip()).parent)
    return raizes


def isolar(partes, pasta, *, rede=False, executaveis=(), claude=False):
    """O comando `partes` dentro do bwrap, gravando só em `pasta`. `executaveis`: outros programas
    que precisam continuar visíveis (o intérprete que o agente usará para testar)."""
    bwrap = shutil.which('bwrap')
    if not bwrap or os.environ.get('JEV_ISOLAMENTO') == '0':
        return list(partes)
    raizes = set()
    for executavel in (partes[0], *executaveis):
        raizes |= _raizes(executavel)
    pasta = str(Path(pasta).resolve())
    comando = [bwrap, '--ro-bind', '/', '/', '--tmpfs', '/root', '--tmpfs', '/tmp']
    for raiz in sorted(str(r) for r in raizes):
        if raiz.startswith(('/root/', '/tmp/')) and Path(raiz).exists():
            comando += ['--ro-bind', raiz, raiz]
    if claude:
        for item in CLAUDE:
            if Path(item).exists():
                comando += ['--bind', item, item]
    comando += ['--bind', pasta, pasta, '--dev', '/dev', '--proc', '/proc', '--unshare-all']
    if rede:
        comando += ['--share-net']
    return comando + ['--die-with-parent', '--chdir', pasta, '--', *partes]
