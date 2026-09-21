"""Leitura seletiva: o agente pergunta, o Jev diz quais trechos entram no contexto.

    python integracao/camadas/ler.py --pergunta "onde a reserva é liquidada?" \
        executor/ledger.py executor/shared.py:100-220 laboratorio/nucleo.py
    python integracao/camadas/ler.py --pergunta "onde a reserva é liquidada?" --rg "reserv" --raiz executor

Com `--rg PADRAO`, os candidatos vêm do ripgrep: cada arquivo com casamento vira blocos de
80 linhas ao redor das linhas casadas (casamentos próximos se fundem), até 32 blocos.

Cada arquivo (ou intervalo `arquivo:inicio-fim`) vira blocos de ~80 linhas; o Jev classifica
todos contra a pergunta, em paralelo, e o comando imprime só os blocos escolhidos, com número
de linha, mais uma linha por bloco descartado dizendo classe e confiança. É a ferramenta
para quando há vários candidatos e ler todos custaria milhares de tokens do modelo caro.

Regras vindas das medições:
- Mostra até `--k` blocos (padrão 3). A R26 derrubou o k = 1: com a resposta dividida em dois
  trechos, mandar um só acerta 6 de 80. Quem sabe que a resposta é de fonte única passa
  `--k 1`; quem não sabe, fica com 3.
- Todo bloco `essencial` entra, mesmo além de k, porque deixar um essencial fora custa mais
  do que os tokens dele.
- Qualquer falha devolve a lista completa de blocos sem texto e diz que falhou: o agente lê
  como leria sem a ferramenta. Nada é omitido em silêncio.
- Cada uso é registrado em `estado/camadas.jsonl` (camada `ler`) com bytes totais e bytes
  devolvidos, para que a economia seja medida e não suposta.
"""
import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from camadas import nucleo  # noqa: E402

MAXIMO_DE_BLOCOS = 32
LINHAS_POR_BLOCO = 80
ORDEM = {'essencial': 3, 'complementar': 2, 'incerto': 1, 'irrelevante': 0}


def candidatos_de(especificacoes, raiz):
    blocos = []
    for spec in especificacoes:
        caminho, intervalo = spec, None
        if ':' in spec and '-' in spec.rsplit(':', 1)[-1]:
            caminho, intervalo = spec.rsplit(':', 1)
        arquivo = (raiz / caminho).resolve()
        linhas = arquivo.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
        if intervalo:
            a, b = (int(x) for x in intervalo.split('-'))
            a, b = max(1, a), min(len(linhas), b)
        else:
            a, b = 1, len(linhas)
        trecho = linhas[a-1:b]
        for i, j in nucleo.dividir_em_blocos(trecho, LINHAS_POR_BLOCO, MAXIMO_DE_BLOCOS) or []:
            blocos.append({'arquivo': str(arquivo), 'nome': Path(caminho).name,
                           'inicio': a + i - 1, 'fim': a + j - 1,
                           'texto': ''.join(trecho[i-1:j])})
    if not 1 <= len(blocos) <= MAXIMO_DE_BLOCOS:
        raise ValueError(f'{len(blocos)} blocos; o máximo é {MAXIMO_DE_BLOCOS}. '
                         'Passe intervalos menores (arquivo:inicio-fim).')
    return blocos


LINHAS_AO_REDOR = 40


def candidatos_do_rg(padrao, raiz, maximo=MAXIMO_DE_BLOCOS):
    """Blocos ao redor dos casamentos do ripgrep, arquivo a arquivo, na ordem do rg."""
    import re
    import subprocess
    saida = subprocess.run(['rg', '-n', '--no-heading', '--color', 'never', padrao, '.'],
                           cwd=str(raiz), capture_output=True, text=True, encoding='utf-8',
                           errors='replace').stdout
    por_arquivo = {}
    for linha in saida.splitlines():
        m = re.match(r'^(?P<arquivo>.+?):(?P<n>\d+):', linha)
        if m:
            por_arquivo.setdefault(m['arquivo'], []).append(int(m['n']))
    blocos = []
    for arquivo, numeros in por_arquivo.items():
        caminho = (raiz / arquivo).resolve()
        try:
            linhas = caminho.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True)
        except OSError:
            continue
        intervalos = []
        for n in sorted(numeros):
            a, b = max(1, n - LINHAS_AO_REDOR), min(len(linhas), n + LINHAS_AO_REDOR)
            if intervalos and a <= intervalos[-1][1] + 1:
                intervalos[-1][1] = max(intervalos[-1][1], b)
            else:
                intervalos.append([a, b])
        for a, b in intervalos:
            blocos.append({'arquivo': str(caminho), 'nome': Path(arquivo).name, 'inicio': a,
                           'fim': b, 'texto': ''.join(linhas[a-1:b])})
            if len(blocos) >= maximo:
                return blocos
    if not blocos:
        raise ValueError(f'o rg não achou "{padrao}" em {raiz}')
    return blocos


def selecionar(pergunta, blocos, k, *, transporte=None, tempo_total=25.0):
    inicio = time.time()
    estados = [nucleo.estado_do_trecho(
        pergunta, f"ARQUIVO {b['nome']}, linhas {b['inicio']}-{b['fim']}:", b['texto'])
        for b in blocos]
    resultados = nucleo.classificar_em_paralelo(
        estados, nucleo.PERGUNTA_DE_CONTEXTO, origem='camada-ler',
        tempo_total=tempo_total, transporte=transporte)
    resumo = nucleo.resumo_das_chamadas(resultados)
    total = sum(len(b['texto']) for b in blocos)
    saida = {'pergunta': pergunta[:200], 'blocos': len(blocos), 'k': k,
             'caracteres_total': total, **resumo,
             'latencia_ms': round((time.time() - inicio) * 1000)}
    if resumo['falha']:
        return {**saida, 'acao': 'tudo', 'selecionados': list(range(len(blocos))),
                'classes': [], 'caracteres_devolvidos': total, 'tokens_evitados_estimados': 0}
    classes = []
    for i, (respostas, _) in enumerate(resultados):
        classe, confianca = nucleo.escolha(respostas, 'relevancia')
        classes.append({'i': i, 'classe': classe, 'confianca': confianca})
    ordenados = sorted(classes, key=lambda c: (ORDEM.get(c['classe'], -1), c['confianca'] or 0),
                       reverse=True)
    escolhidos = [c['i'] for c in ordenados[:k]]
    escolhidos += [c['i'] for c in ordenados[k:] if c['classe'] == 'essencial']
    escolhidos = sorted(set(escolhidos))
    devolvidos = sum(len(blocos[i]['texto']) for i in escolhidos)
    return {**saida, 'acao': 'selecionar', 'selecionados': escolhidos, 'classes': classes,
            'caracteres_devolvidos': devolvidos,
            'tokens_evitados_estimados': nucleo.tokens(total - devolvidos)}


def imprimir(blocos, decisao, como_json):
    if como_json:
        print(json.dumps({**decisao, 'trechos': [
            {**{k: v for k, v in blocos[i].items() if k != 'texto'}, 'texto': blocos[i]['texto']}
            for i in decisao['selecionados']]}, ensure_ascii=False))
        return
    por_indice = {c['i']: c for c in decisao['classes']}
    if decisao['acao'] == 'tudo':
        print(f"[jev/ler] falhou ({decisao['falha']}); leia os arquivos normalmente.")
        return
    print(f"[jev/ler] {decisao['blocos']} blocos classificados, {len(decisao['selecionados'])} "
          f"devolvidos, ~{decisao['tokens_evitados_estimados']} tokens evitados "
          f"(4 caracteres por token, estimativa). Custo Jev US$ {nucleo.dec(decisao['custo_usd'], 6)}.")
    for i in decisao['selecionados']:
        b, c = blocos[i], por_indice[i]
        print(f"\n=== {b['nome']} linhas {b['inicio']}-{b['fim']} "
              f"[{c['classe']} {nucleo.dec(c['confianca'])}] ({b['arquivo']}) ===")
        for n, linha in enumerate(b['texto'].splitlines(), b['inicio']):
            print(f'{n:6d}\t{linha}')
    fora = [i for i in range(len(blocos)) if i not in decisao['selecionados']]
    if fora:
        print('\n--- não devolvidos (peça por intervalo se precisar) ---')
        for i in fora:
            b, c = blocos[i], por_indice[i]
            print(f"{b['nome']}:{b['inicio']}-{b['fim']}  {c['classe']} {nucleo.dec(c['confianca'])}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--pergunta', required=True)
    parser.add_argument('--raiz', default='.', type=Path)
    parser.add_argument('--k', type=int, default=3)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--rg', help='padrão do ripgrep; os candidatos vêm dos casamentos')
    parser.add_argument('arquivos', nargs='*', help='arquivo ou arquivo:inicio-fim')
    args = parser.parse_args(argv)
    if not args.rg and not args.arquivos:
        parser.error('passe arquivos ou --rg')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    raiz = args.raiz.resolve()
    blocos = candidatos_do_rg(args.rg, raiz) if args.rg else candidatos_de(args.arquivos, raiz)
    decisao = selecionar(args.pergunta, blocos, max(1, args.k))
    nucleo.registrar('ler', **{k: v for k, v in decisao.items() if k != 'classes'},
                     arquivos=sorted({b['arquivo'] for b in blocos}), rg=args.rg)
    imprimir(blocos, decisao, args.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())
