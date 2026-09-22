"""O conciliador do jev-gateway: lê só linhas de rota com chamada ao Jev, precifica pela tabela local,
não conta a mesma linha duas vezes e recomeça quando o log é outro arquivo."""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from executor.pricing import load_prices  # noqa: E402
from integracao.gateway import conciliar  # noqa: E402

ROTA = {'event': 'route', 'time': '2026-09-22T03:26:04.000Z', 'path': '/v1/messages', 'tools': 133, 'mode': 'hint',
        'tool': 'Glob', 'confidence': 0.98, 'status': 200, 'durationMs': 5724,
        'usage': {'input': 111875, 'output': 153, 'cached': 0, 'cacheWrite': 0, 'reasoning': 0},
        'jev': {'choice': 'Glob', 'confidence': 0.98, 'latencyMs': 2016, 'inputTokens': 20055}}
SEM_JEV = {'event': 'route', 'time': '2026-09-22T03:26:10.000Z', 'path': '/v1/messages', 'tools': 0,
           'mode': 'passthrough', 'reason': 'no tools', 'status': 200, 'durationMs': 900}


def escrever(pasta, cliente, eventos, prefixo=''):
    linhas = [prefixo] if prefixo else []
    linhas += [json.dumps(e) for e in eventos]
    (pasta / f'{cliente}.log').write_text('\n'.join(linhas) + '\n', encoding='utf-8')


def test_precifica_pela_tabela_local_e_ignora_turno_sem_jev(tmp_path):
    escrever(tmp_path, 'claude', [ROTA, SEM_JEV], prefixo='router listening on 8789')
    linhas, estado = conciliar.novas_linhas(pasta=tmp_path, estado={})
    assert len(linhas) == 1
    linha = linhas[0]
    preco = load_prices()['models']['typesafe:jev-1.13.0']['input_nusd_per_million_tokens']
    assert linha['custo_usd'] == -(-20055 * preco // 1_000_000) / 1e9
    assert linha['origem'] == 'jev-gateway' and linha['cliente'] == 'claude' and linha['modo'] == 'hint'
    assert 'attempt_id' not in linha and linha['custo_reportado'] is False and 'piso' in linha['custo_fonte']
    assert estado['claude']['linhas'] == 3


def test_nao_conta_duas_vezes_e_recomeca_em_arquivo_novo(tmp_path):
    escrever(tmp_path, 'codex', [ROTA])
    primeiras, estado = conciliar.novas_linhas(pasta=tmp_path, estado={})
    de_novo, estado = conciliar.novas_linhas(pasta=tmp_path, estado=estado)
    assert len(primeiras) == 1 and de_novo == []
    escrever(tmp_path, 'codex', [ROTA, ROTA])  # mais uma linha no mesmo arquivo
    novas, estado = conciliar.novas_linhas(pasta=tmp_path, estado=estado)
    assert len(novas) == 1 and novas[0]['linha'] == 2
    escrever(tmp_path, 'codex', [ROTA], prefixo='outro cabeçalho')  # arquivo recriado: assinatura muda
    recomeco, _ = conciliar.novas_linhas(pasta=tmp_path, estado=estado)
    assert len(recomeco) == 1


def test_relatorio_por_cliente_e_dia(tmp_path):
    escrever(tmp_path, 'claude', [ROTA, SEM_JEV, {**ROTA, 'mode': 'passthrough', 'reason': 'low confidence'}])
    (linha,) = conciliar.relatorio(pasta=tmp_path)
    assert linha['cliente'] == 'claude' and linha['dia'] == '2026-09-22' and linha['turnos'] == 3
    assert linha['modos'] == {'hint': 1, 'passthrough': 2} and linha['jev_decidiu'] == round(1 / 3, 3)
    assert linha['chamadas_jev'] == 2 and linha['tokens_jev'] == 40110 and linha['llm_saida'] == 306
