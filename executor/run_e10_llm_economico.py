"""E10: o braço do LLM econômico, que faltava desde o plano original.

O estudo inteiro comparou o Jev contra uma regra congelada que eu mesmo escrevi. A décima
terceira rodada de revisão adversarial apontou que esse é o comparador mais fácil de vencer que
existe, e que a pergunta P1 do plano — *vale um LLM especializado aqui, ou qualquer classificador
de linguagem resolve?* — seguia sem metade da resposta.

Aqui um LLM genérico e barato (`meta-llama/llama-3.1-8b-instruct`) recebe **as mesmas instruções
e os mesmos critérios congelados do E1**, no conjunto de confirmação, que é a partição de teste.
Nenhum prompt foi afinado contra estes 40 casos.

Pré-registro: `planning/preregistro-E10-llm-economico.md`, escrito antes da primeira chamada.

Uso:
    python -m executor.run_e10_llm_economico             # mostra o custo e não envia nada
    python -m executor.run_e10_llm_economico --execute
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .analise import bootstrap_cluster
from .ledger import Ledger
from .pricing import load_prices, usd_to_nusd, worst_case_nusd
from .run_e1_triagem import CRITERIOS, INSTRUCOES, resumo
from .runner import (http_transport, load_api_key, payload_sha256, reported_cost_nusd,
                     reservation_output_tokens, reservation_tokens, usage_from)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-confirmacao.jsonl'
OUT = ROOT / 'runs' / 'e10-llm-economico'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e10-llm-economico'
BLOCK = 'e10-llm-economico'
PROVIDER = 'openrouter'
MODEL = 'meta-llama/llama-3.1-8b-instruct'
ARM = 'arm-e10-llm-economico'
CHAT_URL = 'https://openrouter.ai/api/v1/chat/completions'
CLASSES = tuple(CRITERIOS)
# O pre-registro fixa este teto, e e ele que torna a reserva de saida verificavel.
MAX_TOKENS = 64


def carregar():
    return [json.loads(linha) for linha in CORPUS.read_text(encoding='utf-8').splitlines()
            if linha.strip()]


def prompt(texto):
    criterios = '\n'.join(f'- {classe}: {desc}' for classe, desc in CRITERIOS.items())
    return (INSTRUCOES + '\n\nClasses possiveis:\n' + criterios + '\n\nMensagem:\n'
            + texto + '\n\n'
            'Responda SOMENTE com um objeto JSON no formato '
            '{"acao": "<uma das classes>", "confianca": <numero entre 0 e 1>}. '
            'Nenhum texto fora do JSON.')


def payload(texto):
    return {'model': MODEL, 'max_tokens': MAX_TOKENS, 'temperature': 0,
            'response_format': {'type': 'json_object'},
            'messages': [{'role': 'user', 'content': prompt(texto)}]}


def interpretar(corpo):
    """Extrai a classe e a confiança. Resposta malformada é ERRO, nunca descarte.

    O pré-registro é explícito: descartar resposta malformada do comparador e não do Jev seria
    fraudar a comparação. Aqui uma resposta que não respeita o contrato devolve `None`, e `None`
    nunca é igual ao gabarito.
    """
    escolhas = corpo.get('choices') or []
    if not escolhas:
        return None, None, 'sem choices'
    conteudo = ((escolhas[0].get('message') or {}).get('content') or '').strip()
    try:
        dados = json.loads(conteudo)
    except ValueError:
        return None, None, 'json invalido: ' + conteudo[:80]
    acao = dados.get('acao')
    if acao not in CLASSES:
        return None, None, 'classe fora do contrato: ' + repr(acao)
    confianca = dados.get('confianca')
    if not isinstance(confianca, (int, float)) or not 0 <= confianca <= 1:
        confianca = None
    return acao, confianca, None


def executar(casos, key, precos):
    entrada = reservation_tokens(precos, PROVIDER, MODEL)
    saida_max = reservation_output_tokens(precos, PROVIDER, MODEL)
    OUT.mkdir(parents=True, exist_ok=True)
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(
            usd_to_nusd('5.00'),
            hypothesis='Um LLM generico e barato acerta tanto quanto o Jev na triagem',
            metric='acuracia pareada sobre o conjunto de confirmacao')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.30'))
        ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/v1/chat/completions')
        cabecalhos = {'Authorization': 'Bearer ' + key,
                      'Content-Type': 'application/json',
                      'User-Agent': 'jev-lab/1.0'}
        for caso in casos:
            caminho = 'runs/e10-llm-economico/' + caso['case_id'] + '.json'
            corpo = payload(caso['text'])
            reserva = ledger.reserve(arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                                     max_input_tokens=entrada, max_output_tokens=saida_max,
                                     payload_sha256=payload_sha256(corpo), request_path=caminho,
                                     runtime_manifest_path=caminho,
                                     evidence_level='live_component')
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
                caso['llm_erro'] = 'http ' + str(status) + ': ' + str(resposta.get('error'))[:160]
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
            marca = 'ok  ' if caso['llm'] == caso['gold'] else 'ERRO'
            print('  ' + caso['case_id'] + ': ' + marca + ' gold=' + caso['gold'].ljust(11)
                  + ' llm=' + str(caso['llm']), flush=True)
        return ledger.wallet_committed_nusd(), ledger.wallet_available_nusd()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    casos = carregar()
    precos = load_prices()
    entrada = reservation_tokens(precos, PROVIDER, MODEL)
    saida_max = reservation_output_tokens(precos, PROVIDER, MODEL)
    pior = worst_case_nusd(precos, PROVIDER, MODEL, entrada, saida_max)

    if not args.execute:
        print(str(len(casos)) + ' chamadas a ' + MODEL + '.')
        print('Reserva do pior caso: ' + str(entrada) + ' tokens de entrada, '
              + str(saida_max) + ' de saida.')
        print('US$ %.9f por chamada, US$ %.9f no total.'
              % (pior / 1e9, pior * len(casos) / 1e9))
        print('Nada enviado.')
        return

    comprometido, disponivel = executar(casos, load_api_key()[0], precos)

    # O Jev nao e reexecutado: as respostas dele vem do E7, os mesmos 40 casos.
    e7 = json.loads((ROOT / 'runs' / 'e7-confirmacao' / 'relatorio.json').read_text(
        encoding='utf-8'))
    do_jev = {c['case_id']: c['jev'] for c in e7['casos']}
    for caso in casos:
        caso['jev'] = do_jev.get(caso['case_id'])

    d_llm, d_jev = resumo('llm', casos), resumo('jev', casos)
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
    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(),
        'modelo': MODEL, 'comparado_com': e7['modelo'],
        'preregistro': 'planning/preregistro-E10-llm-economico.md',
        'corpus': str(CORPUS.relative_to(ROOT)),
        'max_tokens': MAX_TOKENS,
        'llm': d_llm, 'jev': d_jev, 'pareada': pareada,
        'so_jev_acerta': so_jev, 'so_llm_acerta': so_llm,
        'mcnemar_discordancias': len(so_jev) + len(so_llm),
        'respostas_invalidas': [c['case_id'] for c in casos if c.get('llm') is None],
        'casos': casos,
        'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel,
    }
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print('\nLLM economico %d/%d (%.4f)' % (d_llm['acertos'], d_llm['casos_programados'],
                                            d_llm['acuracia_sobre_programados']))
    print('Jev (do E7)   %d/%d (%.4f)' % (d_jev['acertos'], d_jev['casos_programados'],
                                          d_jev['acuracia_sobre_programados']))
    print('Diferenca pareada %+.4f, IC95 [%.4f; %.4f]'
          % (pareada['diferenca_observada'], pareada['ic95'][0], pareada['ic95'][1]))
    print('So o Jev acerta: %d | so o LLM acerta: %d' % (len(so_jev), len(so_llm)))
    print('Respostas invalidas do LLM: %d' % len(relatorio['respostas_invalidas']))
    print('Carteira: %.9f USD comprometidos' % (comprometido / 1e9))


if __name__ == '__main__':
    main()
