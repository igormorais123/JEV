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


def ver():
    for caminho in (CLAUDE, CODEX):
        if not caminho.exists():
            print(f'{caminho}: não existe')
            continue
        dados = carregar(caminho)
        arquivo = (RAIZ / 'modo.txt')
        padrao = arquivo.read_text(encoding='utf-8').strip() if arquivo.exists() else 'sombra'
        modo = (dados.get('env') or {}).get('JEV_ROUTER_MODO', f'{padrao} (do modo.txt)')
        print(f'{caminho.name}: instalado={ja_instalado(dados)} | modo={modo}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--instalar', action='store_true')
    parser.add_argument('--desinstalar', action='store_true')
    parser.add_argument('--ver', action='store_true')
    parser.add_argument('--modo', default='sombra', choices=('sombra', 'ativo'))
    args = parser.parse_args()

    if args.desinstalar:
        gravar_modo('sombra')
        print('removendo:')
        for caminho in (CLAUDE, CODEX):
            desinstalar(caminho)
        return 0
    if args.instalar:
        if not HOOK.exists():
            print(f'hook não encontrado em {HOOK}', file=sys.stderr)
            return 1
        gravar_modo(args.modo)
        print(f'instalando em modo {args.modo}:')
        # Só o Claude Code lê `env` do settings; no Codex o modo vem do ambiente do processo.
        instalar(CLAUDE, args.modo, define_ambiente=True)
        instalar(CODEX, args.modo, define_ambiente=False)
        return 0
    ver()
    return 0


if __name__ == '__main__':
    sys.exit(main())
