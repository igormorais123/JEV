"""E3: relação afirmação/evidência em três classes, com o contraste que mais custa caro.

Testa se o modelo distingue o que o documento afirma do que ele apenas menciona: agendado
contra pago, proposto contra aprovado, citado contra endossado, ausente contra negativo.
Comparador: regra ingênua por palavra-chave, congelada aqui.

Uso:
    python -m executor.run_e3_evidencia --execute
"""
import argparse
import json
import re
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger
from .pricing import usd_to_nusd
from .run_e1_triagem import macro_f1, wilson
from .runner import dispatch, load_api_key

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'evidencia-piloto.jsonl'
OUT = ROOT / 'runs' / 'e3-evidencia'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e3-evidencia'
BLOCK = 'e3-evidencia'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-e3-jev'

CRITERIOS = {
    'suportado': 'O documento afirma o fato alegado, de forma direta e verificada.',
    'contradito': 'O documento afirma o contrario do fato alegado, ou o nega dentro do escopo que declara cobrir.',
    'nao_informado': ('O documento nao decide a alegacao: trata de outro assunto, fala de intencao, proposta, '
                      'agendamento, estimativa, condicao ainda nao verificada, escopo parcial, ou apenas menciona '
                      'a posicao de um terceiro.'),
}
INSTRUCOES = ('Use apenas o documento fornecido, nada de conhecimento externo. Decida a relacao entre o '
              'documento e a alegacao. Agendar nao e pagar; propor nao e aprovar; citar nao e endossar; '
              'falta de informacao nao e negacao. Se o documento nao decide a alegacao, responda nao_informado.')

# Comparador ingenuo, congelado antes das chamadas: procura a palavra central da alegacao no documento.
NEGACOES = [r'\bnao\b', r'\bnenhum', r'rejeit', r'cancel', r'divergimos', r'nao foi', r'nao se sustenta']


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                   if unicodedata.category(c) != 'Mn')


def regra_simples(state, claim):
    documento = normalizar(state)
    palavras = [p for p in re.findall(r'[a-z]{5,}', normalizar(claim))]
    encontrou = any(p[:5] in documento for p in palavras)
    if not encontrou:
        return 'nao_informado'
    if any(re.search(p, documento) for p in NEGACOES):
        return 'contradito'
    return 'suportado'


def carregar():
    return [json.loads(l) for l in CORPUS.read_text(encoding='utf-8').splitlines() if l.strip()]


def resumo(casos, chave):
    pares = [(c['gold'], c[chave]) for c in casos if c.get(chave)]
    acertos = sum(1 for g, p in pares if g == p)
    familias = defaultdict(list)
    for c in casos:
        if c.get(chave):
            familias[c['family']].append(c['gold'] == c[chave])
    perfeitas = sum(1 for v in familias.values() if all(v))
    # Erro grave: dizer suportado ou contradito quando o documento nao decide, ou o inverso.
    graves = sum(1 for c in casos if c.get(chave) and
                 ((c['gold'] == 'nao_informado') != (c[chave] == 'nao_informado')))
    return {'n': len(pares), 'acertos': acertos,
            'acuracia': round(acertos / len(pares), 4) if pares else None,
            'macro_f1': round(macro_f1_3(pares), 4),
            'familias_sem_erro': perfeitas, 'n_familias': len(familias),
            'ic95_familias': [round(x, 4) for x in wilson(perfeitas, len(familias))],
            'erros_graves_nao_informado': graves,
            'erros': [{'case_id': c['case_id'], 'family': c['family'], 'gold': c['gold'],
                       'pred': c[chave], 'state': c['state'], 'claim': c['claim']}
                      for c in casos if c.get(chave) and c[chave] != c['gold']]}


def macro_f1_3(pares):
    f1s = []
    for classe in CRITERIOS:
        tp = sum(1 for g, p in pares if g == classe and p == classe)
        fp = sum(1 for g, p in pares if g != classe and p == classe)
        fn = sum(1 for g, p in pares if g == classe and p != classe)
        if tp + fp + fn == 0:
            continue
        precisao = tp / (tp + fp) if tp + fp else 0.0
        revocacao = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * precisao * revocacao / (precisao + revocacao) if precisao + revocacao else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    casos = carregar()
    for c in casos:
        c['regra'] = regra_simples(c['state'], c['claim'])
    print(f"Regra ingenua: {resumo(casos, 'regra')['acertos']}/{len(casos)}")
    if not args.execute:
        print('Simulacao apenas; nada enviado.')
        return

    OUT.mkdir(parents=True, exist_ok=True)
    key, _ = load_api_key()
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='O Jev distingue o que o documento afirma do que ele apenas menciona',
                         metric='acuracia em tres classes e erro grave de nao_informado')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.25'))
        ledger.register_arm(ARM, 'S01', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
        for c in casos:
            caminho = f"runs/e3-evidencia/{c['case_id']}.json"
            estado = f"DOCUMENTO: {c['state']}\n\nALEGACAO: {c['claim']}"
            inicio = time.monotonic()
            saida = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                             state=estado,
                             questions={'relacao': {'type': 'choice', 'instructions': INSTRUCOES,
                                                    'criteria': CRITERIOS}},
                             request_path=caminho, runtime_manifest_path=caminho, api_key=key)
            resposta = (saida.get('answers') or {}).get('relacao') or {}
            c['jev'] = resposta.get('choice')
            c['jev_confidence'] = resposta.get('confidence')
            c['jev_attempt_id'] = saida['attempt_id']
            c['jev_cost_nusd'] = saida.get('settled_nusd')
            c['latency_ms'] = round((time.monotonic() - inicio) * 1000, 1)
            marca = 'ok ' if c['jev'] == c['gold'] else 'ERRO'
            print(f"  {c['case_id']}: {marca} gold={c['gold']:14} jev={str(c['jev']):14} "
                  f"conf={c['jev_confidence']}")
        comprometido, disponivel = ledger.committed_nusd(), ledger.available_nusd()

    relatorio = {'at': datetime.now(timezone.utc).isoformat(), 'modelo': MODEL,
                 'corpus': str(CORPUS.relative_to(ROOT)),
                 'regra': resumo(casos, 'regra'), 'jev': resumo(casos, 'jev'),
                 'ledger_committed_nusd': comprometido, 'available_nusd': disponivel, 'casos': casos}
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"\n{'':8} {'acur':>6} {'macroF1':>8} {'fam':>6} {'graves':>7}")
    for nome in ('regra', 'jev'):
        d = relatorio[nome]
        print(f"{nome:8} {d['acuracia']:>6} {d['macro_f1']:>8} "
              f"{str(d['familias_sem_erro']) + '/' + str(d['n_familias']):>6} "
              f"{d['erros_graves_nao_informado']:>7}")
    print(f"\nCusto do bloco: {comprometido / 1e9:.9f} USD | disponivel: {disponivel / 1e9:.6f} USD")


if __name__ == '__main__':
    main()
