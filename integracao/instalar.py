"""Instala (ou remove) o hook do Jev no Claude Code e no Codex.

É idempotente: rodar duas vezes não duplica a entrada. Faz backup datado de cada arquivo que
toca, antes de tocar. Remover é `--desinstalar`, e devolve o arquivo ao estado anterior sem
depender do backup.

    python integracao/instalar.py --ver
    python integracao/instalar.py --instalar --modo ativo
    python integracao/instalar.py --desinstalar
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
HOOK = RAIZ / 'hooks' / 'jev_prompt_router.py'

CLAUDE = Path.home() / '.claude' / 'settings.json'
CODEX = Path.home() / '.codex' / 'hooks.json'

MARCA = 'jev_prompt_router.py'
COMANDO = f'python "{HOOK.as_posix()}"'

ENTRADA = {'hooks': [{'type': 'command', 'command': COMANDO, 'timeout': 8,
                      'statusMessage': 'classificando o tema com o Jev'}]}


# Os dois hooks que o projeto instala, cada um no seu evento. O guarda entrou depois da R16 e
# tem modo proprio de proposito: sao decisoes de risco diferente -- sugerir uma skill errada
# custa tres linhas de contexto, deixar de pedir confirmacao de um comando custa o comando.
GANCHOS = {
    'roteador': {
        'evento': 'UserPromptSubmit',
        'arquivo': RAIZ / 'hooks' / 'jev_prompt_router.py',
        'marca': 'jev_prompt_router.py',
        'variavel': 'JEV_ROUTER_MODO',
        'modo_arquivo': RAIZ / 'modo.txt',
        'timeout': 8,
        'rotulo': 'classificando o tema com o Jev',
    },
    'guarda': {
        'evento': 'PreToolUse',
        'arquivo': RAIZ / 'hooks' / 'jev_guarda_comando.py',
        'marca': 'jev_guarda_comando.py',
        'variavel': 'JEV_GUARDA_MODO',
        'modo_arquivo': RAIZ / 'modo-guarda.txt',
        'timeout': 8,
        'rotulo': 'conferindo o efeito do comando com o Jev',
        'matcher': 'Bash|PowerShell',
    },
    # As tres camadas que decidem o que ENTRA no contexto do modelo caro (docs/CAMADAS-CLAUDE-CODE.md).
    'leitura': {
        'evento': 'PreToolUse',
        'arquivo': RAIZ / 'hooks' / 'jev_leitura.py',
        'marca': 'jev_leitura.py',
        'variavel': 'JEV_LEITURA_MODO',
        'modo_arquivo': RAIZ / 'modo-leitura.txt',
        'timeout': 10,
        'rotulo': 'o Jev está escolhendo que parte do arquivo ler',
        'matcher': 'Read',
    },
    # A mesma política da leitura, na porta por onde 81% do texto entra: `cat ARQUIVO` dentro
    # de um comando de shell que é só leitura. Reescreve o comando, então só no Claude Code.
    'leitura-shell': {
        'evento': 'PreToolUse',
        'arquivo': RAIZ / 'hooks' / 'jev_leitura_shell.py',
        'marca': 'jev_leitura_shell.py',
        'variavel': 'JEV_LEITURA_SHELL_MODO',
        'modo_arquivo': RAIZ / 'modo-leitura-shell.txt',
        'timeout': 10,
        'rotulo': 'o Jev está escolhendo que parte do arquivo o comando lê',
        'matcher': 'Bash',
        'so_claude': True,
    },
    'busca': {
        'evento': 'PostToolUse',
        'arquivo': RAIZ / 'hooks' / 'jev_busca.py',
        'marca': 'jev_busca.py',
        'variavel': 'JEV_BUSCA_MODO',
        'modo_arquivo': RAIZ / 'modo-busca.txt',
        'timeout': 10,
        'rotulo': 'o Jev está ordenando a listagem',
        'matcher': None,  # preenchido abaixo a partir da lista de ferramentas da camada
    },
    'saida': {
        'evento': 'PostToolUse',
        'arquivo': RAIZ / 'hooks' / 'jev_saida.py',
        'marca': 'jev_saida.py',
        'variavel': 'JEV_SAIDA_MODO',
        'modo_arquivo': RAIZ / 'modo-saida.txt',
        'timeout': 10,
        'rotulo': 'o Jev está procurando a causa na saída',
        'matcher': 'Bash|PowerShell',
    },
    # Não classifica nada: ao fim de cada sessão regera a página de medição das camadas, para
    # que ela nunca dependa de alguém lembrar de rodar o medidor. Só no Claude Code: o Codex
    # não tem SessionEnd. A rotina completa (caixa, páginas, auditoria, commit) é a tarefa
    # agendada do Windows, criada por `--agendar`.
    'medicao': {
        'evento': 'SessionEnd',
        'arquivo': RAIZ / 'camadas' / 'rotina.py',
        'marca': 'camadas/rotina.py',
        'argumentos': '--so-medir',
        'variavel': None,
        'modo_arquivo': None,
        'timeout': 60,
        'rotulo': 'regerando a medição das camadas do Jev',
        'so_claude': True,
    },
    'sentinela': {
        'evento': 'PostToolUse',
        'arquivo': RAIZ / 'hooks' / 'jev_sentinela.py',
        'marca': 'jev_sentinela.py',
        'variavel': 'JEV_SENTINELA_MODO',
        'modo_arquivo': RAIZ / 'modo-sentinela.txt',
        'timeout': 10,
        'rotulo': 'o sentinela do Jev está lendo o conteúdo externo',
        'matcher': None,  # preenchido abaixo a partir da lista de ferramentas da camada
    },
}
sys.path.insert(0, str(RAIZ))
from camadas.busca import MATCHER as _MATCHER_BUSCA  # noqa: E402
from camadas.sentinela import MATCHER as _MATCHER_SENTINELA  # noqa: E402
GANCHOS['busca']['matcher'] = _MATCHER_BUSCA
GANCHOS['sentinela']['matcher'] = _MATCHER_SENTINELA


def entrada_de(nome):
    ganho = GANCHOS[nome]
    comando = f'python "{ganho["arquivo"].as_posix()}"'
    if ganho.get('argumentos'):
        comando += ' ' + ganho['argumentos']
    bloco = {'hooks': [{'type': 'command',
                        'command': comando,
                        'timeout': ganho['timeout'],
                        'statusMessage': ganho['rotulo']}]}
    if ganho.get('matcher'):
        bloco['matcher'] = ganho['matcher']
    return bloco


def instalado_em(dados, nome):
    ganho = GANCHOS[nome]
    for grupo in (dados.get('hooks') or {}).get(ganho['evento']) or []:
        for gancho in grupo.get('hooks') or []:
            if ganho['marca'] in (gancho.get('command') or ''):
                return True
    return False


def instalar_gancho(caminho, nome, modo, define_ambiente):
    ganho = GANCHOS[nome]
    if not caminho.exists():
        print(f'  {caminho}: nao existe, pulado')
        return
    if not ganho['arquivo'].exists():
        print(f'  hook {nome} nao encontrado em {ganho["arquivo"]}', file=sys.stderr)
        return
    if ganho.get('so_claude') and caminho != CLAUDE:
        return
    if ganho.get('modo_arquivo'):
        ganho['modo_arquivo'].write_text(modo + chr(10), encoding='utf-8')
    dados = carregar(caminho)
    if instalado_em(dados, nome):
        print(f'  {caminho.name}: {nome} ja instalado')
        # O matcher pode ter crescido (a camada passou a cobrir mais ferramentas): atualiza.
        for grupo in dados['hooks'][ganho['evento']]:
            if any(ganho['marca'] in (g.get('command') or '') for g in grupo.get('hooks') or []):
                if ganho.get('matcher') and grupo.get('matcher') != ganho['matcher']:
                    grupo['matcher'] = ganho['matcher']
                    print(f'  {caminho.name}: matcher de {nome} atualizado')
    else:
        copia = backup(caminho)
        dados.setdefault('hooks', {}).setdefault(ganho['evento'], []).append(entrada_de(nome))
        print(f'  {caminho.name}: {nome} acrescentado em {ganho["evento"]} '
              f'(backup em {copia.name})')
    if define_ambiente and ganho.get('variavel'):
        dados.setdefault('env', {})[ganho['variavel']] = modo
        print(f'  {caminho.name}: {ganho["variavel"]}={modo}')
    gravar(caminho, dados)


def desinstalar_gancho(caminho, nome):
    ganho = GANCHOS[nome]
    if not caminho.exists():
        return
    dados = carregar(caminho)
    grupos = (dados.get('hooks') or {}).get(ganho['evento'])
    if not grupos:
        print(f'  {caminho.name}: {nome} nao esta la')
        return
    copia = backup(caminho)
    restantes = []
    for grupo in grupos:
        ganchos = [g for g in (grupo.get('hooks') or [])
                   if ganho['marca'] not in (g.get('command') or '')]
        if ganchos:
            restantes.append({**grupo, 'hooks': ganchos})
    if restantes:
        dados['hooks'][ganho['evento']] = restantes
    else:
        dados['hooks'].pop(ganho['evento'], None)
    if ganho.get('variavel'):
        (dados.get('env') or {}).pop(ganho['variavel'], None)
    gravar(caminho, dados)
    print(f'  {caminho.name}: {nome} removido (backup em {copia.name})')


def gravar_modo(modo):
    """O Codex não tem campo `env` no hooks.json; o modo dele vem deste arquivo."""
    (RAIZ / 'modo.txt').write_text(modo + '\n', encoding='utf-8')


def backup(caminho):
    destino = caminho.with_suffix(caminho.suffix + f'.bak-jev-{time.strftime("%Y%m%d-%H%M%S")}')
    shutil.copy2(caminho, destino)
    return destino


def carregar(caminho):
    return json.loads(caminho.read_text(encoding='utf-8'))


def gravar(caminho, dados):
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')


def ja_instalado(dados):
    for grupo in (dados.get('hooks') or {}).get('UserPromptSubmit') or []:
        for gancho in grupo.get('hooks') or []:
            if MARCA in (gancho.get('command') or ''):
                return True
    return False


def instalar(caminho, modo, define_ambiente):
    if not caminho.exists():
        print(f'  {caminho}: não existe, pulado')
        return
    dados = carregar(caminho)
    if ja_instalado(dados):
        print(f'  {caminho.name}: já instalado')
    else:
        copia = backup(caminho)
        dados.setdefault('hooks', {}).setdefault('UserPromptSubmit', []).append(ENTRADA)
        print(f'  {caminho.name}: hook acrescentado (backup em {copia.name})')
    if define_ambiente:
        dados.setdefault('env', {})['JEV_ROUTER_MODO'] = modo
        print(f'  {caminho.name}: JEV_ROUTER_MODO={modo}')
    gravar(caminho, dados)


def desinstalar(caminho):
    if not caminho.exists():
        return
    dados = carregar(caminho)
    grupos = (dados.get('hooks') or {}).get('UserPromptSubmit')
    if not grupos:
        print(f'  {caminho.name}: nada a remover')
        return
    copia = backup(caminho)
    restantes = []
    for grupo in grupos:
        ganchos = [g for g in (grupo.get('hooks') or []) if MARCA not in (g.get('command') or '')]
        if ganchos:
            restantes.append({**grupo, 'hooks': ganchos})
    if restantes:
        dados['hooks']['UserPromptSubmit'] = restantes
    else:
        dados['hooks'].pop('UserPromptSubmit', None)
    (dados.get('env') or {}).pop('JEV_ROUTER_MODO', None)
    gravar(caminho, dados)
    print(f'  {caminho.name}: hook removido (backup em {copia.name})')


TAREFA = 'JEV-medicao-das-camadas'


def agendar():
    """Tarefa diária do Agendador do Windows: a rotina completa, às 23h30, sem janela."""
    rotina = (RAIZ / 'camadas' / 'rotina.py').as_posix()
    comando = f'cmd /c cd /d "{RAIZ.parent.as_posix()}" && python "{rotina}" >> "{(RAIZ / "estado" / "rotina-tarefa.log").as_posix()}" 2>&1'
    proc = subprocess.run(['schtasks', '/Create', '/F', '/SC', 'DAILY', '/ST', '23:30',
                           '/TN', TAREFA, '/TR', comando], capture_output=True, text=True,
                          encoding='utf-8', errors='replace')
    print((proc.stdout + proc.stderr).strip())
    return proc.returncode


def ver():
    proc = subprocess.run(['schtasks', '/Query', '/TN', TAREFA, '/FO', 'LIST'], capture_output=True,
                          text=True, encoding='utf-8', errors='replace')
    print(f'tarefa agendada {TAREFA}: ' + ('existe' if proc.returncode == 0 else 'não existe (use --agendar)'))
    for caminho in (CLAUDE, CODEX):
        if not caminho.exists():
            print(f'{caminho}: nao existe')
            continue
        dados = carregar(caminho)
        for nome, ganho in GANCHOS.items():
            if ganho.get('so_claude') and caminho != CLAUDE:
                continue
            arquivo = ganho.get('modo_arquivo')
            if not arquivo:
                modo = 'sempre'
            else:
                padrao = arquivo.read_text(encoding='utf-8').strip() if arquivo.exists() else 'sombra'
                modo = (dados.get('env') or {}).get(ganho['variavel'],
                                                    f'{padrao} (de {arquivo.name})')
            print(f'{caminho.name}: {nome:9} instalado={instalado_em(dados, nome)} | '
                  f'modo={modo}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instalar', action='store_true')
    parser.add_argument('--desinstalar', action='store_true')
    parser.add_argument('--ver', action='store_true')
    parser.add_argument('--modo', default='sombra', choices=('sombra', 'ativo'))
    parser.add_argument('--agendar', action='store_true',
                        help='cria a tarefa diária do Windows que roda a rotina completa')
    parser.add_argument('--gancho', default='roteador',
                        choices=tuple(GANCHOS) + ('todos',),
                        help='qual hook instalar ou remover')
    args = parser.parse_args()

    alvos = tuple(GANCHOS) if args.gancho == 'todos' else (args.gancho,)

    if args.desinstalar:
        print('removendo:')
        for nome in alvos:
            if GANCHOS[nome].get('modo_arquivo'):
                GANCHOS[nome]['modo_arquivo'].write_text('sombra' + chr(10), encoding='utf-8')
            for caminho in (CLAUDE, CODEX):
                desinstalar_gancho(caminho, nome)
        return 0
    if args.agendar:
        return agendar()
    if args.instalar:
        print(f'instalando {", ".join(alvos)} em modo {args.modo}:')
        for nome in alvos:
            # So o Claude Code le `env` do settings; no Codex o modo vem do arquivo de modo.
            instalar_gancho(CLAUDE, nome, args.modo, define_ambiente=True)
            instalar_gancho(CODEX, nome, args.modo, define_ambiente=False)
        return 0
    ver()
    return 0


if __name__ == '__main__':
    sys.exit(main())
