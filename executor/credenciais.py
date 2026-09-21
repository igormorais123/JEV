"""Onde qualquer instância desta máquina acha as chaves do Jev, e qual provedor prefere.

Ordem de leitura, para cada variável: ambiente > `.env` do projeto > `~/.secrets/jev.env`
(o cofre privado da máquina, fora de qualquer repositório) > `~/.secrets/keys.env` (só a
OpenRouter, que já morava lá). O valor nunca é registrado, impresso nem devolvido em log:
esta função entrega a chave a quem vai usá-la e mais ninguém.

Provedores:
- `typesafe`: `https://api.typesafe.ai/v1/systemone`, modelo `jev-1.13.0`, chave
  `TYPESAFE_API_KEY`. Só tem o Jev, menos superfície. O E5 mediu, nos mesmos 40 casos:
  mesma resposta nos 40, latência p50 de 755 ms contra 396 ms, custo 12% maior.
- `openrouter`: `https://openrouter.ai/api/alpha/decisions`, modelo `typesafe/jev-1.13`,
  chave `OPENROUTER_API_KEY`. Devolve o custo cobrado em `usage.cost`.

A preferência vem de `JEV_PROVEDOR` (ambiente ou arquivos, na mesma ordem); sem ela, é
`typesafe` se a chave existir, senão `openrouter`.
"""
import os
from pathlib import Path

PROJETO = Path(__file__).resolve().parents[1]
COFRE = Path.home() / '.secrets' / 'jev.env'
COFRE_ANTIGO = Path.home() / '.secrets' / 'keys.env'

PROVEDORES = {
    'typesafe': {'url': 'https://api.typesafe.ai/v1/systemone', 'modelo': 'jev-1.13.0',
                 'variavel': 'TYPESAFE_API_KEY'},
    'openrouter': {'url': 'https://openrouter.ai/api/alpha/decisions', 'modelo': 'typesafe/jev-1.13',
                   'variavel': 'OPENROUTER_API_KEY'},
}

ARQUIVOS = (PROJETO / '.env', COFRE, COFRE_ANTIGO)


def _do_arquivo(caminho, nome):
    try:
        linhas = caminho.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return None
    for linha in linhas:
        if linha.strip().startswith(f'{nome}='):
            valor = linha.split('=', 1)[1].strip().strip('"').strip("'")
            if valor:
                return valor
    return None


def valor(nome, arquivos=ARQUIVOS):
    """Devolve (valor, origem) ou (None, None). A origem é um rótulo, nunca o valor."""
    if os.environ.get(nome):
        return os.environ[nome], 'ambiente'
    for caminho in arquivos:
        achado = _do_arquivo(caminho, nome)
        if achado:
            return achado, caminho.name
    return None, None


def provedor(arquivos=ARQUIVOS):
    """O provedor a usar: a preferência declarada, ou o primeiro com chave."""
    escolhido, _ = valor('JEV_PROVEDOR', arquivos)
    escolhido = (escolhido or '').strip().lower()
    if escolhido in PROVEDORES and valor(PROVEDORES[escolhido]['variavel'], arquivos)[0]:
        return escolhido
    for nome in ('typesafe', 'openrouter'):
        if valor(PROVEDORES[nome]['variavel'], arquivos)[0]:
            return nome
    return 'openrouter'


def chave(nome_do_provedor, arquivos=ARQUIVOS):
    """A chave do provedor, ou RuntimeError sem o valor de nada."""
    variavel = PROVEDORES[nome_do_provedor]['variavel']
    achado, origem = valor(variavel, arquivos)
    if not achado:
        raise RuntimeError(f'{variavel} ausente: ambiente, .env do projeto e {COFRE}')
    return achado, origem


def situacao(arquivos=ARQUIVOS):
    """Para diagnóstico: quais chaves existem e de onde, sem nenhum valor."""
    return {nome: {'chave': valor(p['variavel'], arquivos)[1] or 'ausente', 'modelo': p['modelo']}
            for nome, p in PROVEDORES.items()} | {'preferido': provedor(arquivos)}


if __name__ == '__main__':
    import json
    print(json.dumps(situacao(), ensure_ascii=False, indent=1))
