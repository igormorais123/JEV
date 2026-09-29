#!/usr/bin/env python3
"""Confere se o que roda na VPS é o que está versionado aqui: `python3 infra/conferir_sincronia.py`.

Roda no PC (precisa do alias ssh `hermes`) e compara, arquivo a arquivo, o conteúdo do repositório
com o da VPS, ignorando a diferença de fim de linha do Windows. Sai com código 1 quando algo
diverge, para poder virar passo de rotina.

Existe porque em 22/09/2026 uma camada inteira (a rota de ferramenta em `camadas.py`) foi escrita
direto na VPS e ficou fora do repositório e sem teste: o repositório dizia uma coisa e o Hermes
fazia outra. Divergência não é erro em si — quem edita na VPS pode ter razão —, mas precisa
aparecer no mesmo dia. `--puxar` traz as divergências para cá, para revisar e versionar.
"""
import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAQUINA = 'hermes'
# onde cada pasta do repositório mora na VPS
DESTINOS = {
    'jev_hermes': '/root/.hermes/integrations/jev/jev_hermes',
    'rotinas': '/root/.hermes/scripts',
    'portoes': '/root/.hermes/scripts',
    'plugin': '/root/.hermes/plugins',
    'skill': '/root/.hermes/skills',
}
EXTENSOES = ('.py', '.md', '.json', '.yaml')
CONFERIR_LA = r'''
import hashlib, json, os, sys
saida = {}
for remoto in json.load(sys.stdin):
    if not os.path.exists(remoto):
        saida[remoto] = None
    else:
        with open(remoto, 'rb') as arquivo:
            saida[remoto] = hashlib.md5(arquivo.read().replace(b'\r\n', b'\n')).hexdigest()
print(json.dumps(saida))
'''


def versionados():
    """Só o que o git já rastreia: arquivo novo em edição ainda não é promessa de nada."""
    fim = subprocess.run(['git', '-C', str(RAIZ), 'ls-files'], capture_output=True, text=True)
    return {(RAIZ / linha).resolve() for linha in fim.stdout.splitlines() if linha}


def arquivos():
    """(caminho local, caminho na VPS) de tudo que é publicado."""
    rastreados = versionados()
    for pasta, destino in DESTINOS.items():
        base = RAIZ / pasta
        for caminho in sorted(base.rglob('*')):
            if (caminho.is_file() and caminho.suffix in EXTENSOES
                    and '__pycache__' not in caminho.parts
                    and caminho.resolve() in rastreados):
                dentro = caminho.relative_to(base)
                # rotinas e porteiros são publicados achatados, em /root/.hermes/scripts
                relativo = dentro.name if pasta in ('rotinas', 'portoes') else dentro.as_posix()
                yield caminho, f'{destino}/{relativo}'


def digest(caminho):
    return hashlib.md5(caminho.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def lado_da_diferenca(caminho, md5_remoto):
    """De quem é a versão que está na VPS: da última que commitamos, ou de mais ninguém.

    Com dois agentes mexendo no mesmo repositório, "difere" sozinho não diz nada. Se a VPS é igual
    ao HEAD, a diferença é uma edição local em curso — publique quando terminar. Se não é, a VPS
    tem código que não está versionado: leia antes de sobrescrever.
    """
    relativo = caminho.relative_to(RAIZ.parent).as_posix()
    fim = subprocess.run(['git', '-C', str(RAIZ), 'show', f'HEAD:{relativo}'],
                         capture_output=True)
    if fim.returncode != 0:
        return 'não está no HEAD'
    no_head = hashlib.md5(fim.stdout.replace(b'\r\n', b'\n')).hexdigest()
    return 'edição local ainda não publicada' if no_head == md5_remoto else 'a VPS tem o que não está aqui'


def conferir():
    pares = list(arquivos())
    pedido = json.dumps([remoto for _, remoto in pares])
    # o ssh junta os argumentos e entrega ao shell remoto: o script vai como um único argumento
    comando = 'python3 -c ' + shlex.quote(CONFERIR_LA)
    fim = subprocess.run(['ssh', MAQUINA, comando], input=pedido,
                         capture_output=True, text=True, timeout=120)
    if fim.returncode != 0:
        raise SystemExit(f'ssh falhou: {(fim.stderr or "").strip()[:300]}')
    la = json.loads(fim.stdout)
    iguais, diferem, ausentes = [], [], []
    for local, remoto in pares:
        if la.get(remoto) is None:
            ausentes.append((local, remoto, ''))
        elif la[remoto] == digest(local):
            iguais.append((local, remoto, ''))
        else:
            diferem.append((local, remoto, lado_da_diferenca(local, la[remoto])))
    return iguais, diferem, ausentes


def puxar(pares):
    for local, remoto, _ in pares:
        fim = subprocess.run(['scp', f'{MAQUINA}:{remoto}', str(local)], capture_output=True, text=True)
        if fim.returncode == 0:
            local.write_bytes(local.read_bytes().replace(b'\r\n', b'\n'))
            print(f'  puxado: {local.relative_to(RAIZ)}')
        else:
            print(f'  FALHOU: {remoto} ({(fim.stderr or "").strip()[:120]})')


def main():
    opcoes = argparse.ArgumentParser(description=__doc__)
    opcoes.add_argument('--puxar', action='store_true', help='traz as divergências da VPS para o repositório')
    escolhas = opcoes.parse_args()
    iguais, diferem, ausentes = conferir()
    print(f'{len(iguais)} arquivo(s) iguais ao que roda na VPS.')
    for local, remoto, lado in diferem:
        print(f'DIFERE   {local.relative_to(RAIZ)}  ->  {remoto}  [{lado}]')
    for local, remoto, _ in ausentes:
        print(f'AUSENTE  {local.relative_to(RAIZ)}  ->  {remoto} (versionado aqui, não publicado lá)')
    if diferem and escolhas.puxar:
        trazer = [p for p in diferem if p[2] == 'a VPS tem o que não está aqui']
        print(f'Puxando {len(trazer)} (revise o diff e rode os testes antes de versionar); '
              'edição local em curso fica como está:')
        puxar(trazer)
    return 1 if (diferem or ausentes) else 0


if __name__ == '__main__':
    sys.exit(main())
