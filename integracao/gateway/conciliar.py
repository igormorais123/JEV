"""Concilia o gasto do jev-gateway com o livro-caixa e resume o que ele decidiu.

    python integracao/gateway/conciliar.py            # importa o gasto novo e imprime o resumo
    python integracao/gateway/conciliar.py --relatorio # só o resumo por cliente e por dia, sem gravar

O jev-gateway (https://github.com/vinilana/jev-gateway) é um proxy local que, a cada turno do Codex
ou do Claude Code que carrega ferramentas, pergunta ao Jev qual ferramenta chamar. Ele tem chave e
transporte próprios, fora de `executor/shared.py`; sem este conciliador o gasto dele não entraria
na carteira única de `runs/ledger.sqlite3`. O gateway registra uma linha JSON por requisição em
`~/.jev-gateway/<cliente>.log`, com os tokens de entrada da chamada ao Jev; este módulo lê as linhas
novas, precifica pelo mesmo `executor/pricing.py` do resto do estudo e anexa a `integracao/gastos.jsonl`,
o arquivo que o livro-caixa já importa. O gateway não registra os tokens de saída: o valor gravado é
um piso, declarado como tal no campo `custo_fonte`.

Quando a carteira fica abaixo de RESERVA_MINIMA_USD, o conciliador desliga o roteamento nos gateways
em execução (`--routing off`): eles continuam medindo tokens, mas param de chamar o Jev.
"""
import argparse
import hashlib
import json
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from executor import credenciais, shared  # noqa: E402
from executor.ledger import Ledger  # noqa: E402
from executor.pricing import load_prices, observed_nusd, usd_to_nusd  # noqa: E402

PASTA_DO_GATEWAY = Path.home() / '.jev-gateway'
CLIENTES = ('claude', 'codex', 'opencode', 'gemini')
ESTADO = RAIZ / 'integracao' / 'estado' / 'gateway-conciliado.json'
GASTOS = RAIZ / 'integracao' / 'gastos.jsonl'
RESERVA_MINIMA_USD = '0.25'
PROVEDOR = 'typesafe'  # o gateway foi configurado com a chave da TypeSafe (~/.jev-gateway/.env)
MODELO = credenciais.PROVEDORES[PROVEDOR]['modelo']


def eventos_do_log(caminho):
    """Uma lista de (número da linha, evento) com as linhas de rota que chamaram o Jev."""
    eventos = []
    if not caminho.exists():
        return eventos
    for numero, linha in enumerate(caminho.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        if not linha.startswith('{'):
            continue
        try:
            evento = json.loads(linha)
        except ValueError:
            continue
        if evento.get('event') == 'route':
            eventos.append((numero, evento))
    return eventos


def custo_nusd(evento, precos):
    tokens = ((evento.get('jev') or {}).get('inputTokens'))
    if not isinstance(tokens, int) or tokens <= 0:
        return 0
    return observed_nusd(precos, PROVEDOR, MODELO, tokens, 0)


def linha_de_gasto(cliente, numero, evento, precos):
    """A linha que `integracao/gastos.jsonl` recebe: sem attempt_id, o livro-caixa a conta como gasto."""
    nusd = custo_nusd(evento, precos)
    if nusd <= 0:
        return None
    jev = evento.get('jev') or {}
    momento = evento.get('time') or datetime.now(timezone.utc).isoformat()
    return {'dia': momento[:10], 'em': momento[:19], 'custo_usd': nusd / 1e9, 'origem': 'jev-gateway',
            'cliente': cliente, 'linha': numero, 'modo': evento.get('mode'), 'ferramenta': evento.get('tool'),
            'tokens_entrada': jev.get('inputTokens'), 'latencia_jev_ms': jev.get('latencyMs'),
            'modelo': MODELO, 'provedor': PROVEDOR, 'custo_reportado': False,
            'custo_fonte': 'tokens de entrada do log do gateway x tabela executor/pricing.py; saida nao registrada (piso)',
            'evidence_level': 'live_component'}


def _ler_estado():
    try:
        return json.loads(ESTADO.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def _assinatura(caminho):
    primeira = caminho.read_text(encoding='utf-8', errors='replace').split('\n', 1)[0]
    return hashlib.sha256(primeira.encode()).hexdigest()[:16]


def novas_linhas(pasta=PASTA_DO_GATEWAY, estado=None):
    """Linhas de gasto ainda não anexadas, e o estado atualizado para gravar depois."""
    estado = dict(_ler_estado() if estado is None else estado)
    precos = load_prices()
    linhas = []
    for cliente in CLIENTES:
        log = pasta / f'{cliente}.log'
        if not log.exists():
            continue
        marca = estado.get(cliente) or {}
        assinatura = _assinatura(log)
        lidas = marca.get('linhas', 0) if marca.get('assinatura') == assinatura else 0  # arquivo novo: recomeça
        total = 0
        for numero, evento in eventos_do_log(log):
            total = numero
            if numero <= lidas:
                continue
            linha = linha_de_gasto(cliente, numero, evento, precos)
            if linha:
                linhas.append(linha)
        estado[cliente] = {'assinatura': assinatura, 'linhas': max(lidas, total)}
    return linhas, estado


def anexar(linhas, arquivo=GASTOS):
    with arquivo.open('a', encoding='utf-8') as saida:
        for linha in linhas:
            saida.write(json.dumps(linha, ensure_ascii=False) + '\n')


def importar_no_livro_caixa(db_path=shared.DB, legacy_paths=shared.LEGACY):
    """Mesma sequência de `shared.ask`, sem chamada: autoriza, importa, devolve o saldo."""
    with Ledger(db_path, 'shared-router', prices=load_prices()) as ledger:
        if ledger.wallet_cap_nusd() > usd_to_nusd('5'):
            raise shared.BudgetError('Wallet exceeds authorized total')
        ledger.authorize(usd_to_nusd(shared.CAPS['router']))
        shared.import_legacy(ledger, legacy_paths)
        return {'teto_usd': ledger.wallet_cap_nusd() / 1e9,
                'comprometido_usd': ledger.wallet_committed_nusd() / 1e9,
                'disponivel_usd': ledger.wallet_available_nusd() / 1e9}


def desligar_roteamento(clientes=('claude', 'codex')):
    """`jev-<cliente> --routing off` para cada gateway em execução; falha silenciosa se não houver."""
    desligados = []
    for cliente in clientes:
        try:
            saida = subprocess.run([f'jev-{cliente}', '--routing', 'off'], capture_output=True, text=True,
                                   timeout=20, shell=sys.platform == 'win32')
        except (OSError, subprocess.TimeoutExpired):
            continue
        if saida.returncode == 0 and 'routing off' in saida.stdout:
            desligados.append(cliente)
    return desligados


def relatorio(pasta=PASTA_DO_GATEWAY):
    """Por cliente e por dia: turnos, modos, taxa em que o Jev decidiu, latência e tokens."""
    precos = load_prices()
    linhas = []
    for cliente in CLIENTES:
        por_dia = defaultdict(list)
        for _, evento in eventos_do_log(pasta / f'{cliente}.log'):
            por_dia[(evento.get('time') or '')[:10]].append(evento)
        for dia, eventos in sorted(por_dia.items()):
            modos = Counter(e.get('mode') for e in eventos)
            jev = [e['jev'] for e in eventos if e.get('jev')]
            uso = [e['usage'] for e in eventos if e.get('usage')]
            decididos = sum(v for m, v in modos.items() if m in ('forced', 'direct', 'hint', 'none'))
            linhas.append({
                'cliente': cliente, 'dia': dia, 'turnos': len(eventos), 'modos': dict(modos),
                'jev_decidiu': round(decididos / len(eventos), 3) if eventos else None,
                'chamadas_jev': len(jev),
                'latencia_jev_mediana_ms': statistics.median(j['latencyMs'] for j in jev) if jev else None,
                'tokens_jev': sum(j.get('inputTokens') or 0 for j in jev),
                'custo_jev_piso_usd': round(sum(custo_nusd(e, precos) for e in eventos) / 1e9, 6),
                'llm_entrada': sum(u.get('input') or 0 for u in uso), 'llm_cache': sum(u.get('cached') or 0 for u in uso),
                'llm_saida': sum(u.get('output') or 0 for u in uso),
                'duracao_mediana_ms': statistics.median(e['durationMs'] for e in eventos if e.get('durationMs')) if any(e.get('durationMs') for e in eventos) else None,
            })
    return linhas


def conciliar():
    linhas, estado = novas_linhas()
    if linhas:
        anexar(linhas)
    carteira = importar_no_livro_caixa()
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding='utf-8')
    resultado = {'linhas_novas': len(linhas), 'custo_novo_usd': round(sum(l['custo_usd'] for l in linhas), 6),
                 **carteira, 'roteamento_desligado': []}
    if carteira['disponivel_usd'] < float(RESERVA_MINIMA_USD):
        resultado['roteamento_desligado'] = desligar_roteamento()
    return resultado


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--relatorio', action='store_true', help='só o resumo, sem tocar no livro-caixa')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
    if args.relatorio:
        linhas = relatorio()
        if args.json:
            print(json.dumps(linhas, ensure_ascii=False))
            return 0
        for l in linhas:
            print(f"[jev-gateway] {l['cliente']} {l['dia']}: {l['turnos']} turnos, Jev decidiu {l['jev_decidiu']:.0%} "
                  f"({', '.join(f'{m} {n}' for m, n in sorted(l['modos'].items()))}); Jev {l['chamadas_jev']} chamadas, "
                  f"mediana {l['latencia_jev_mediana_ms']} ms, {l['tokens_jev']} tokens, piso US$ {l['custo_jev_piso_usd']:.6f}; "
                  f"LLM entrada {l['llm_entrada']} (cache {l['llm_cache']}), saída {l['llm_saida']}")
        if not linhas:
            print('[jev-gateway] nenhum log em', PASTA_DO_GATEWAY)
        return 0
    resultado = conciliar()
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False))
        return 0
    print(f"[jev-gateway] {resultado['linhas_novas']} chamada(s) nova(s) do Jev, US$ {resultado['custo_novo_usd']:.6f} anexado(s) "
          f"ao livro-caixa; carteira: US$ {resultado['comprometido_usd']:.4f} de {resultado['teto_usd']:.2f} comprometidos, "
          f"US$ {resultado['disponivel_usd']:.4f} disponíveis.")
    if resultado['roteamento_desligado']:
        print('ATENÇÃO: carteira abaixo da reserva; roteamento desligado em:', ', '.join(resultado['roteamento_desligado']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
