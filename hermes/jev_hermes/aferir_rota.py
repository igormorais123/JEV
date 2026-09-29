"""A rota de ferramenta acertou? `python3 jev_hermes/aferir_rota.py [--dias 7]`.

A camada `tema` sugere, no começo do turno, qual categoria de ferramenta é a primeira ação. Aqui a
sugestão é conferida contra o que o Hermes de fato chamou naquela sessão logo depois, lendo
`messages` do `state.db`. Sem isso a rota é opinião: bonita no registro e sem prova de que ajuda.

Três resultados por turno: `acertou` (a primeira ferramenta chamada é da categoria sugerida),
`errou` (chamou outra coisa) e `sem chamada` (o turno terminou em texto — o que, para a rota
`nenhuma`, é o acerto). Casos sem a sessão no banco ficam de fora da conta e são declarados.
"""
import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jev_hermes import camadas, nucleo  # noqa: E402

ESTADO_DO_HERMES = Path('/root/.hermes/state.db')
# qual ferramenta do Hermes pertence a cada rota da camada
FERRAMENTAS_DA_ROTA = {
    'arquivos': {'read_file', 'search_files', 'write_file', 'patch', 'list_files'},
    'terminal': {'terminal', 'process'},
    'web': {'web_search', 'web_extract'},
    'navegador': {'browser_navigate', 'browser_snapshot', 'browser_click', 'browser_console', 'browser_type'},
    'historico': {'session_search'},
    'imagem': {'image_generate', 'vision_analyze'},
    'delegacao': {'delegate_task'},
    'especializada': {'tool_search', 'tool_describe', 'tool_call', 'skill_view', 'skill_manage'},
}


def turnos_com_rota(dias):
    limite = nucleo._agora().timestamp() - dias * 86400
    saida = []
    try:
        texto = (nucleo.ESTADO / 'camadas.jsonl').read_text(encoding='utf-8', errors='replace')
    except OSError:
        return saida
    for linha in texto.splitlines():
        try:
            d = json.loads(linha)
        except ValueError:
            continue
        if d.get('camada') != 'tema' or 'ferramenta' not in d or not d.get('sessao'):
            continue
        try:
            quando = nucleo._agora().fromisoformat(d['em']).timestamp()
        except (KeyError, ValueError):
            continue
        if quando >= limite:
            saida.append(d)
    return saida


def primeira_ferramenta(con, sessao, desde):
    """Primeira ferramenta chamada naquela sessão depois do turno começar.

    Devolve (existe a sessão, nome da ferramenta). Sessão que não está no `state.db` é chamada de
    prova, feita fora do agente: entra como fora da conta, nunca como "o modelo não usou ferramenta".
    """
    if not con.execute('select 1 from messages where session_id like ? limit 1', (f'{sessao}%',)).fetchone():
        return False, None
    linha = con.execute(
        'select tool_name from messages where session_id like ? and timestamp >= ? '
        "and tool_name is not null and tool_name <> '' order by timestamp limit 1",
        (f'{sessao}%', desde)).fetchone()
    return True, (linha[0] if linha else None)


def aferir(dias=7):
    turnos = turnos_com_rota(dias)
    if not turnos:
        return {'turnos': 0}
    placar, por_rota, fora = Counter(), Counter(), 0
    try:
        con = sqlite3.connect(f'file:{ESTADO_DO_HERMES}?mode=ro', uri=True)
    except sqlite3.Error:
        return {'turnos': len(turnos), 'erro': 'state.db indisponível'}
    with con:
        for d in turnos:
            rota = d.get('ferramenta')
            if (d.get('confianca_ferramenta') or 0) < camadas.CORTE_DA_FERRAMENTA:
                placar['abaixo do corte'] += 1
                continue
            quando = nucleo._agora().fromisoformat(d['em']).timestamp()
            real, usada = primeira_ferramenta(con, d['sessao'], quando)
            if not real:
                fora += 1
                continue
            if usada is None:
                resultado = 'acertou' if rota == 'nenhuma' else 'sem chamada'
            elif rota == 'nenhuma':
                resultado = 'errou'
            elif usada in FERRAMENTAS_DA_ROTA.get(rota, set()):
                resultado = 'acertou'
            else:
                resultado = 'errou'
            placar[resultado] += 1
            por_rota[(rota, resultado, usada or '—')] += 1
    decididos = placar['acertou'] + placar['errou']
    return {'turnos': len(turnos), 'fora_da_conta': fora, 'placar': dict(placar),
            'acerto': round(placar['acertou'] / decididos, 3) if decididos else None,
            'por_rota': {f'{r} -> {res} ({u})': q for (r, res, u), q in por_rota.most_common()}}


def main():
    opcoes = argparse.ArgumentParser(description=__doc__)
    opcoes.add_argument('--dias', type=int, default=7)
    escolhas = opcoes.parse_args()
    print(json.dumps(aferir(escolhas.dias), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
