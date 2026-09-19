"""E5 (pergunta P6): OpenRouter contra TypeSafe direto, nos mesmos casos.

O plano pedia comparar os dois transportes com o mesmo modelo, mesmo host e chamadas
intercaladas, para que uma eventual deriva do serviço não caia em cima de um só braço.

Uso:
    python -m executor.run_e5_provedores --execute
"""
import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger
from .pricing import usd_to_nusd
from .run_e1_triagem import CRITERIOS, INSTRUCOES, carregar
from .runner import (TransportTimeout, dispatch, load_api_key, reservation_output_tokens,
                     reservation_tokens)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'e5-provedores'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e5-provedores'
BLOCK = 'e5-provedores'
DIRETO_URL = 'https://api.typesafe.ai/v1/systemone'

BRACOS = {
    'openrouter': {'provider': 'openrouter', 'model': 'typesafe/jev-1.13', 'arm': 'arm-e5-openrouter',
                   'env': 'OPENROUTER_API_KEY'},
    'typesafe': {'provider': 'typesafe', 'model': 'jev-1.13.0', 'arm': 'arm-e5-typesafe',
                 'env': 'TYPESAFE_API_KEY'},
}


def carregar_chave(nome):
    if nome == 'OPENROUTER_API_KEY':
        return load_api_key()[0]
    for linha in (ROOT / '.env').read_text(encoding='utf-8').splitlines():
        if linha.startswith(f'{nome}='):
            return linha.split('=', 1)[1].strip()
    raise RuntimeError(f'{nome} ausente no .env local')


def transporte_direto(url, headers, body, timeout):
    """Mesma assinatura do transporte padrão, apontando para o endpoint oficial."""
    requisicao = urllib.request.Request(DIRETO_URL, data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
                                        headers=headers, method='POST')
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return resposta.status, json.loads(resposta.read().decode('utf-8'))
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read().decode('utf-8'))
        except (ValueError, OSError):
            return erro.code, {}
    except TimeoutError as erro:
        raise TransportTimeout(str(erro)) from erro
    except urllib.error.URLError as erro:
        if isinstance(erro.reason, TimeoutError):
            raise TransportTimeout(str(erro)) from erro
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--casos', type=int, default=40)
    args = parser.parse_args()
    casos = carregar()[:args.casos]

    if not args.execute:
        from .pricing import load_prices, worst_case_nusd
        precos = load_prices()
        for nome, braco in BRACOS.items():
            tokens = reservation_tokens(precos, braco['provider'], braco['model'])
            saida = reservation_output_tokens(precos, braco['provider'], braco['model'])
            pior = worst_case_nusd(precos, braco['provider'], braco['model'], tokens, saida)
            print(f"{nome:11} reserva por chamada {pior / 1e9:.9f} USD "
                  f"({tokens} entrada, {saida} saida)")
        print(f'{len(casos)} casos x 2 bracos = {len(casos) * 2} chamadas. Nada enviado.')
        return

    OUT.mkdir(parents=True, exist_ok=True)
    chaves = {nome: carregar_chave(braco['env']) for nome, braco in BRACOS.items()}
    resultados = []
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='Os dois transportes entregam a mesma decisao a custo e latencia diferentes',
                         metric='concordancia, custo por decisao e latencia')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.50'))
        for nome, braco in BRACOS.items():
            ledger.register_arm(braco['arm'], 'S01', braco['provider'], braco['model'],
                                endpoint=DIRETO_URL if nome == 'typesafe' else '/api/alpha/decisions')
        for indice, caso in enumerate(casos):
            registro = {'case_id': caso['case_id'], 'family': caso['family'], 'gold': caso['gold']}
            # Alterna qual transporte vai primeiro, para nao dar sempre a mesma vez a um deles.
            ordem = list(BRACOS) if indice % 2 == 0 else list(reversed(list(BRACOS)))
            for nome in ordem:
                braco = BRACOS[nome]
                caminho = f"runs/e5-provedores/{nome}-{caso['case_id']}.json"
                marcador = time.monotonic()
                saida = dispatch(ledger, arm_id=braco['arm'], block_id=BLOCK,
                                 provider=braco['provider'], model=braco['model'],
                                 state=caso['text'],
                                 questions={'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                                     'criteria': CRITERIOS}},
                                 request_path=caminho, runtime_manifest_path=caminho,
                                 api_key=chaves[nome],
                                 transport=transporte_direto if nome == 'typesafe' else None)
                elapsed = round((time.monotonic() - marcador) * 1000, 1)
                resposta = (saida.get('answers') or {}).get('acao') or {}
                registro[nome] = {
                    'pred': resposta.get('choice'), 'confidence': resposta.get('confidence'),
                    'status': saida['status'], 'latency_ms': elapsed,
                    'cost_nusd': saida.get('settled_nusd'), 'cost_source': saida.get('cost_source'),
                    'attempt_id': saida['attempt_id'],
                }
            iguais = registro['openrouter']['pred'] == registro['typesafe']['pred']
            registro['concordam'] = iguais
            resultados.append(registro)
            print(f"  {caso['case_id']}: {'=' if iguais else 'DIVERGE'} "
                  f"or={registro['openrouter']['pred']}/{registro['openrouter']['latency_ms']}ms "
                  f"ts={registro['typesafe']['pred']}/{registro['typesafe']['latency_ms']}ms", flush=True)
        comprometido = ledger.wallet_committed_nusd()
        disponivel = ledger.wallet_available_nusd()

    resumo = {}
    for nome in BRACOS:
        validos = [r for r in resultados if r[nome]['pred']]
        acertos = sum(1 for r in validos if r[nome]['pred'] == r['gold'])
        latencias = sorted(r[nome]['latency_ms'] for r in resultados)
        custos = [r[nome]['cost_nusd'] or 0 for r in resultados]
        resumo[nome] = {
            'respostas_validas': len(validos), 'casos': len(resultados), 'acertos': acertos,
            'acuracia': round(acertos / len(validos), 4) if validos else None,
            'latencia_p50_ms': statistics.median(latencias),
            'latencia_p95_ms': latencias[int(len(latencias) * 0.95) - 1],
            'custo_total_nusd': sum(custos),
            'custo_por_decisao_nusd': round(sum(custos) / len(resultados), 1),
        }
    concordancia = sum(1 for r in resultados if r['concordam'])
    relatorio = {'at': datetime.now(timezone.utc).isoformat(), 'resumo': resumo,
                 'concordancia': concordancia, 'casos': len(resultados),
                 'taxa_concordancia': round(concordancia / len(resultados), 4),
                 'divergencias': [r for r in resultados if not r['concordam']],
                 'resultados': resultados,
                 'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel}
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print(f"\n{'braco':11} {'acur':>6} {'p50ms':>7} {'p95ms':>7} {'nusd/decisao':>13}")
    for nome, d in resumo.items():
        print(f"{nome:11} {d['acuracia']:>6} {d['latencia_p50_ms']:>7.0f} {d['latencia_p95_ms']:>7.0f} "
              f"{d['custo_por_decisao_nusd']:>13}")
    print(f"\nConcordancia entre transportes: {concordancia}/{len(resultados)} "
          f"({relatorio['taxa_concordancia']:.1%})")
    print(f"Carteira: {comprometido / 1e9:.9f} USD comprometidos | {disponivel / 1e9:.6f} USD disponiveis")


if __name__ == '__main__':
    main()
