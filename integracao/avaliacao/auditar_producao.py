"""Movimento 1 — o roteador em produção: o que ele decidiu sobre os meus próprios pedidos.

Todas as avaliações anteriores do roteador usaram amostra extraída do histórico e gabarito
escrito por mim depois. Esta é a primeira vez que se olha o que ele fez **em produção**, no
hook instalado, decidindo sobre pedidos reais no momento em que eles aconteceram.

O registro em `integracao/decisoes.jsonl` guarda o SHA-256 do pedido, nunca o texto — foi uma
decisão de privacidade tomada antes de instalar. Isso custa caro agora: para saber se a decisão
foi certa é preciso recuperar o texto, e o único lugar onde ele existe é o transcript da sessão.
Este script recasa os dois pelo hash, sem nunca gravar o texto de volta.

    python integracao/avaliacao/auditar_producao.py
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

DECISOES = RAIZ / 'integracao' / 'decisoes.jsonl'
DESTINO = RAIZ / 'integracao' / 'avaliacao' / 'producao.json'
TRANSCRITOS = Path.home() / '.claude' / 'projects'


def marca(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


def pedidos_do_historico(limite_de_arquivos=2000):
    """Todo texto que já foi um pedido de usuário, indexado por hash.

    Não sei qual transformação o hook aplicou antes de hashear, então indexo várias formas do
    mesmo texto e deixo o casamento decidir. O que não casar fica de fora da amostra e entra no
    denominador como 'sem texto' -- nunca como acerto.
    """
    indice = {}
    arquivos = sorted(TRANSCRITOS.rglob('*.jsonl'), key=lambda p: p.stat().st_mtime,
                      reverse=True)[:limite_de_arquivos]
    for arquivo in arquivos:
        try:
            conteudo = arquivo.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for linha in conteudo.splitlines():
            if '"user"' not in linha:
                continue
            try:
                evento = json.loads(linha)
            except ValueError:
                continue
            if evento.get('type') != 'user':
                continue
            conteudo_msg = (evento.get('message') or {}).get('content')
            if isinstance(conteudo_msg, list):
                brutos = [p.get('text', '') for p in conteudo_msg if isinstance(p, dict)]
                brutos.append('\n'.join(b for b in brutos if b))
            elif isinstance(conteudo_msg, str):
                brutos = [conteudo_msg]
            else:
                continue
            for bruto in brutos:
                if not bruto or not bruto.strip():
                    continue
                # O hook recebe só o `prompt`; o transcript costuma anexar system-reminders e
                # saída de comando local ao mesmo turno. Indexo o texto inteiro e também o que
                # sobra antes de cada anexo, porque de fora não dá para saber qual dos dois
                # gerou o hash.
                formas = {bruto, bruto.strip()}
                for corte in ('<system-reminder>', '<local-command-stdout>', '<command-name>'):
                    if corte in bruto:
                        formas.add(bruto.split(corte)[0].strip())
                for forma in formas:
                    if forma:
                        indice.setdefault(marca(forma), forma)
    return indice


def main():
    linhas = [json.loads(l) for l in DECISOES.read_text(encoding='utf-8').splitlines() if l.strip()]
    tema = [l for l in linhas if 'tema' in l]
    print(f'{len(linhas)} decisões registradas, {len(tema)} na política de tema atual')

    indice = pedidos_do_historico()
    print(f'{len(indice):,} hashes de pedido no histórico local')

    casados, orfaos = [], 0
    for linha in tema:
        texto = indice.get(linha.get('pedido_sha256'))
        if texto is None:
            orfaos += 1
            continue
        casados.append({'texto': texto, **{k: linha.get(k) for k in
                                           ('tema', 'confianca', 'sugere', 'risco', 'cache',
                                            'latencia_ms', 'custo_usd', 'em')}})

    print(f'casaram {len(casados)}; sem texto recuperável: {orfaos}')

    resultado = {
        'decisoes_totais': len(linhas),
        'na_politica_de_tema': len(tema),
        'com_texto_recuperado': len(casados),
        'sem_texto': orfaos,
        'temas': Counter(l['tema'] for l in tema).most_common(),
        'sugeriu': sum(1 for l in tema if l.get('sugere')),
        'latencia_ms': sorted(l['latencia_ms'] for l in linhas if l.get('latencia_ms')),
        'custo_usd': round(sum(l.get('custo_usd') or 0 for l in linhas), 8),
        'amostra': casados,
    }
    DESTINO.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'gravado em {DESTINO.relative_to(RAIZ)}')

    for caso in casados:
        primeira = caso['texto'].splitlines()[0][:96]
        print(f"   {caso['tema']:12} {caso['confianca']:<5} "
              f"{'SUGERIU' if caso['sugere'] else '-      '} {primeira}")


if __name__ == '__main__':
    main()
