"""E11: o desempate entre o Jev e o LLM econômico, em corpus novo e pré-registrado.

O E10 não separou de zero na partição de teste; o E10b, decidido depois, separou no piloto e nas
20 famílias somadas. A evidência ficou dividida por dois motivos: poder baixo e uma análise
escolhida depois de ver a outra. Este experimento resolve os dois — 60 casos novos em 20
famílias, com a regra de decisão congelada em `planning/preregistro-E11-desempate.md` antes de o
corpus existir.

Os dois braços recebem as MESMAS instruções e critérios congelados do E1. Nenhum é reexecutado.

Uso:
    python -m executor.run_e11_desempate            # custo do pior caso, sem enviar nada
    python -m executor.run_e11_desempate --execute
"""
import argparse
import json
import time
from datetime import datetime, timezone
from math import comb
from pathlib import Path

from .analise import bootstrap_cluster
from .ledger import Ledger
from .pricing import load_prices, usd_to_nusd, worst_case_nusd
from .run_e1_triagem import CRITERIOS, INSTRUCOES, resumo
from .run_e10_llm_economico import interpretar, payload as payload_chat
from .run_e10_llm_economico import CHAT_URL, MODEL as MODELO_BARATO
from .runner import (dispatch, http_transport, load_api_key, payload_sha256, reported_cost_nusd,
                     reservation_output_tokens, reservation_tokens, usage_from)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-desempate.jsonl'
OUT = ROOT / 'runs' / 'e11-desempate'
# Cada caso e gravado aqui assim que responde. A primeira execucao do E11 perdeu 120 chamadas
# pagas porque a analise quebrou no fim e nada tinha sido persistido: o `request_path` que o
# dispatch registra no livro-caixa e so um rotulo, ninguem escreve aquele arquivo.
BRUTO = OUT / 'respostas.jsonl'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e11-desempate'
BLOCK = 'e11-desempate'
PROVIDER = 'openrouter'
MODELO_JEV = 'typesafe/jev-1.13'
ARM_JEV = 'arm-e11-jev'
ARM_BARATO = 'arm-e11-llm-economico'


def carregar():
    return [json.loads(linha) for linha in CORPUS.read_text(encoding='utf-8').splitlines()
            if linha.strip()]


def gravar(caso):
    """Acrescenta o caso respondido ao bruto, na hora. Perder dado pago e inaceitavel."""
    OUT.mkdir(parents=True, exist_ok=True)
    with BRUTO.open('a', encoding='utf-8') as arquivo:
        arquivo.write(json.dumps(caso, ensure_ascii=False) + chr(10))


def recuperar():
    """Reconstroi os casos a partir do bruto, para reanalisar sem gastar nada."""
    if not BRUTO.exists():
        return None
    por_id = {}
    for linha in BRUTO.read_text(encoding='utf-8').splitlines():
        if linha.strip():
            caso = json.loads(linha)
            por_id.setdefault(caso['case_id'], {}).update(caso)
    return list(por_id.values()) or None


def mcnemar_exato(b, c):
    """Bilateral, sem aproximação: com poucas discordâncias o qui-quadrado não vale."""
    n = b + c
    if not n:
        return 1.0
    cauda = sum(comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * cauda)


def braco_jev(casos, ledger, key):
    for caso in casos:
        caminho = 'runs/e11-desempate/jev-' + caso['case_id'] + '.json'
        marcador = time.monotonic()
        saida = dispatch(ledger, arm_id=ARM_JEV, block_id=BLOCK, provider=PROVIDER,
                         model=MODELO_JEV, state=caso['text'],
                         questions={'acao': {'type': 'choice', 'instructions': INSTRUCOES,
                                             'criteria': CRITERIOS}},
                         request_path=caminho, runtime_manifest_path=caminho, api_key=key)
        resposta = (saida.get('answers') or {}).get('acao') or {}
        caso['jev'] = resposta.get('choice')
        caso['jev_confidence'] = resposta.get('confidence')
        caso['jev_status'] = saida['status']
        caso['jev_attempt_id'] = saida['attempt_id']
        caso['jev_cost_nusd'] = saida.get('settled_nusd')
        caso['jev_latency_ms'] = round((time.monotonic() - marcador) * 1000, 1)
        gravar(caso)
        marca = 'ok  ' if caso['jev'] == caso['gold'] else 'ERRO'
        print('  jev   ' + caso['case_id'] + ': ' + marca + ' gold='
              + caso['gold'].ljust(11) + ' -> ' + str(caso['jev']), flush=True)


def braco_barato(casos, ledger, key, precos):
    entrada = reservation_tokens(precos, PROVIDER, MODELO_BARATO)
    saida_max = reservation_output_tokens(precos, PROVIDER, MODELO_BARATO)
    cabecalhos = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                  'User-Agent': 'jev-lab/1.0'}
    for caso in casos:
        caminho = 'runs/e11-desempate/llm-' + caso['case_id'] + '.json'
        corpo = payload_chat(caso['text'])
        reserva = ledger.reserve(arm_id=ARM_BARATO, block_id=BLOCK, provider=PROVIDER,
                                 model=MODELO_BARATO, max_input_tokens=entrada,
                                 max_output_tokens=saida_max,
                                 payload_sha256=payload_sha256(corpo), request_path=caminho,
                                 runtime_manifest_path=caminho, evidence_level='live_component')
        attempt_id = reserva['attempt_id']
        ledger.mark_sent(attempt_id)
        marcador = time.monotonic()
        status, resposta = http_transport(CHAT_URL, cabecalhos, corpo, 60.0)
        uso = usage_from(resposta)
        reportado = reported_cost_nusd(resposta)
        if status != 200:
            liquidado = ledger.settle(attempt_id, status='http_error', usage=uso,
                                      provider_reported_cost_nusd=reportado,
                                      provider_request_id=resposta.get('id'))
            caso['llm'] = None
            caso['llm_erro'] = 'http ' + str(status)
        else:
            acao, confianca, erro = interpretar(resposta)
            liquidado = ledger.settle(attempt_id, status='success', usage=uso,
                                      provider_reported_cost_nusd=reportado,
                                      provider_request_id=resposta.get('id'),
                                      model_resolved=resposta.get('model'))
            caso['llm'] = acao
            caso['llm_confidence'] = confianca
            caso['llm_erro'] = erro
        caso['llm_attempt_id'] = attempt_id
        caso['llm_cost_nusd'] = liquidado.get('settled_nusd')
        caso['llm_latency_ms'] = round((time.monotonic() - marcador) * 1000, 1)
        gravar(caso)
        marca = 'ok  ' if caso['llm'] == caso['gold'] else 'ERRO'
        print('  llm   ' + caso['case_id'] + ': ' + marca + ' gold='
              + caso['gold'].ljust(11) + ' -> ' + str(caso['llm']), flush=True)


def leitura(ic):
    """A regra congelada no pré-registro, aplicada sem margem de interpretação."""
    if ic[0] > 0:
        return ('vantagem-do-jev',
                'o IC95 está inteiramente acima de zero: há evidência de que o Jev supera um LLM '
                'econômico nesta tarefa')
    if ic[1] < 0:
        return ('vantagem-do-comparador',
                'o IC95 está inteiramente abaixo de zero: o comparador barato é melhor')
    return ('sem-evidencia-de-vantagem',
            'o IC95 contém zero: não há evidência de vantagem, e a recomendação passa a ser o '
            'classificador mais barato que passe no critério de erro grave')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--so-analisar', action='store_true',
                        help='refaz a analise a partir de runs/e11-desempate/respostas.jsonl')
    args = parser.parse_args()
    casos = carregar()
    precos = load_prices()
    pior_jev = worst_case_nusd(precos, PROVIDER, MODELO_JEV,
                               reservation_tokens(precos, PROVIDER, MODELO_JEV),
                               reservation_output_tokens(precos, PROVIDER, MODELO_JEV))
    pior_barato = worst_case_nusd(precos, PROVIDER, MODELO_BARATO,
                                  reservation_tokens(precos, PROVIDER, MODELO_BARATO),
                                  reservation_output_tokens(precos, PROVIDER, MODELO_BARATO))
    total = (pior_jev + pior_barato) * len(casos)

    if not args.execute:
        print('%d casos, 2 bracos = %d chamadas.' % (len(casos), 2 * len(casos)))
        print('Pior caso: Jev US$ %.9f + comparador US$ %.9f por caso.'
              % (pior_jev / 1e9, pior_barato / 1e9))
        print('Pior caso total: US$ %.9f. Nada enviado.' % (total / 1e9))
        return

    if args.so_analisar:
        casos = recuperar()
        if not casos:
            raise SystemExit('nao ha bruto em runs/e11-desempate/respostas.jsonl')
        comprometido = disponivel = None
        print('Reanalisando %d casos do bruto, sem nenhuma chamada.' % len(casos))
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        key = load_api_key()[0]
        comprometido, disponivel = executar_os_dois(casos, key, precos)

    _analisar(casos, comprometido, disponivel)


def executar_os_dois(casos, key, precos):
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='O Jev e um LLM generico barato acertam igualmente a triagem',
                         metric='diferenca pareada de acuracia em corpus novo de 20 familias')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.60'))
        ledger.register_arm(ARM_JEV, 'S01', PROVIDER, MODELO_JEV,
                            endpoint='/api/alpha/decisions')
        ledger.register_arm(ARM_BARATO, 'S01', PROVIDER, MODELO_BARATO,
                            endpoint='/api/v1/chat/completions')
        braco_jev(casos, ledger, key)
        braco_barato(casos, ledger, key, precos)
        return ledger.wallet_committed_nusd(), ledger.wallet_available_nusd()


def _analisar(casos, comprometido, disponivel):
    d_jev, d_llm = resumo('jev', casos), resumo('llm', casos)
    clusters = {}
    for caso in casos:
        clusters.setdefault(caso['family'], []).append(
            (1 if caso.get('jev') == caso['gold'] else 0,
             1 if caso.get('llm') == caso['gold'] else 0))
    pareada = bootstrap_cluster(clusters)
    so_jev = [c['case_id'] for c in casos
              if c.get('jev') == c['gold'] and c.get('llm') != c['gold']]
    so_llm = [c['case_id'] for c in casos
              if c.get('llm') == c['gold'] and c.get('jev') != c['gold']]
    p_mcnemar = mcnemar_exato(len(so_jev), len(so_llm))
    chave, frase = leitura(pareada['ic95'])

    graves = {}
    for campo in ('jev', 'llm'):
        falsos = [c['case_id'] for c in casos
                  if c.get(campo) == 'cancelar' and c['gold'] != 'cancelar']
        perdidos = [c['case_id'] for c in casos
                    if c['gold'] == 'cancelar' and c.get(campo) != 'cancelar']
        graves[campo] = {'falso_cancelar': falsos, 'cancelar_perdido': perdidos}

    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(),
        'preregistro': 'planning/preregistro-E11-desempate.md',
        'corpus': str(CORPUS.relative_to(ROOT)),
        'modelo': MODELO_JEV, 'comparador': MODELO_BARATO,
        'jev': d_jev, 'llm': d_llm, 'pareada': pareada,
        'so_jev_acerta': so_jev, 'so_llm_acerta': so_llm,
        'mcnemar_discordancias': len(so_jev) + len(so_llm),
        'mcnemar_p_exato': round(p_mcnemar, 4),
        'erro_grave': graves,
        'respostas_invalidas_do_comparador': [c['case_id'] for c in casos if c.get('llm') is None],
        'respostas_invalidas_do_jev': [c['case_id'] for c in casos if c.get('jev') is None],
        'leitura': chave, 'leitura_texto': frase,
        'casos': casos,
        'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel,
    }
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print('\nJev        %d/%d (%.4f)' % (d_jev['acertos'], d_jev['casos_programados'],
                                         d_jev['acuracia_sobre_programados']))
    print('Comparador %d/%d (%.4f)' % (d_llm['acertos'], d_llm['casos_programados'],
                                       d_llm['acuracia_sobre_programados']))
    print('Diferenca pareada %+.4f, IC95 [%.4f; %.4f] sobre %d familias'
          % (pareada['diferenca_observada'], pareada['ic95'][0], pareada['ic95'][1],
             pareada['n_familias']))
    print('So o Jev acerta: %d | so o comparador: %d | McNemar exato p = %.4f'
          % (len(so_jev), len(so_llm), p_mcnemar))
    print('Erro grave -- Jev: %d falso-cancelar | comparador: %d'
          % (len(graves['jev']['falso_cancelar']), len(graves['llm']['falso_cancelar'])))
    print('\nLEITURA PRE-REGISTRADA: %s\n  %s' % (chave, frase))
    print('Carteira: %.9f USD comprometidos' % (comprometido / 1e9))


if __name__ == '__main__':
    main()
