"""E4 (pergunta P2): a seleção de fontes preserva as ressalvas necessárias?

Um ranqueador pode acertar a relevância e ainda assim produzir resposta errada, se empurrar
para baixo justamente o trecho que limita a regra geral. Aqui a métrica principal não é nDCG:
é quantas ressalvas necessárias sobrevivem no topo do ranking.

Comparadores congelados antes das chamadas: ordem original do corpus e BM25 simples.

Uso:
    python -m executor.run_e4_ressalvas --execute
"""
import argparse
import json
import math
import random
import re
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .ledger import Ledger
from .pricing import usd_to_nusd
from .runner import dispatch, load_api_key

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'ressalvas-piloto.jsonl'
OUT = ROOT / 'runs' / 'e4-ressalvas'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e4-ressalvas'
BLOCK = 'e4-ressalvas'
PROVIDER = 'openrouter'
MODEL = 'typesafe/jev-1.13'
ARM = 'arm-e4-jev'
TOPO = 3
SEMENTE_ORDEM = 20260918

ESCALA = ['irrelevante', 'tangencial', 'essencial']
INSTRUCOES = ('Avalie o quanto este trecho e necessario para responder corretamente a pergunta. '
              'Um trecho que limita, excetua ou condiciona a regra geral e essencial: sem ele a '
              'resposta fica errada, mesmo que a regra geral esteja presente.')


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                   if unicodedata.category(c) != 'Mn')


def tokens(texto):
    return re.findall(r'[a-z]{3,}', normalizar(texto))


def bm25(consulta, documentos, k1=1.5, b=0.75):
    """BM25 clássico sobre os candidatos da própria consulta."""
    corpo = [tokens(d['text']) for d in documentos]
    tamanhos = [len(c) for c in corpo]
    media = sum(tamanhos) / len(tamanhos)
    n = len(corpo)
    frequencia = Counter()
    for c in corpo:
        for termo in set(c):
            frequencia[termo] += 1
    pontos = []
    for indice, c in enumerate(corpo):
        contagem = Counter(c)
        total = 0.0
        for termo in tokens(consulta):
            if termo not in contagem:
                continue
            idf = math.log(1 + (n - frequencia[termo] + 0.5) / (frequencia[termo] + 0.5))
            tf = contagem[termo]
            total += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * tamanhos[indice] / media))
        pontos.append(total)
    return pontos


def ndcg(ordem, relevancias, k=5):
    ganho = sum((2 ** relevancias[i] - 1) / math.log2(posicao + 2)
                for posicao, i in enumerate(ordem[:k]))
    ideal_ordem = sorted(range(len(relevancias)), key=lambda i: -relevancias[i])
    ideal = sum((2 ** relevancias[i] - 1) / math.log2(posicao + 2)
                for posicao, i in enumerate(ideal_ordem[:k]))
    return ganho / ideal if ideal else 0.0


def avaliar(consultas, ordens):
    ndcgs, ressalvas_no_topo, ressalvas_totais, essenciais_no_topo = [], 0, 0, 0
    for consulta in consultas:
        candidatos = consulta['candidates']
        relevancias = [c['rel'] for c in candidatos]
        ordem = ordens[consulta['query_id']]
        ndcgs.append(ndcg(ordem, relevancias))
        topo = ordem[:TOPO]
        for indice, candidato in enumerate(candidatos):
            if candidato['ressalva']:
                ressalvas_totais += 1
                if indice in topo:
                    ressalvas_no_topo += 1
        essenciais_no_topo += sum(1 for i in topo if candidatos[i]['rel'] == 2)
    return {'ndcg5': round(sum(ndcgs) / len(ndcgs), 4),
            'recall_ressalvas_topo3': round(ressalvas_no_topo / ressalvas_totais, 4),
            'ressalvas_no_topo': ressalvas_no_topo, 'ressalvas_totais': ressalvas_totais,
            'essenciais_no_topo3': essenciais_no_topo}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    consultas = [json.loads(l) for l in CORPUS.read_text(encoding='utf-8').splitlines() if l.strip()]
    # O corpus foi escrito com os candidatos em ordem decrescente de relevancia. Mante-la
    # daria ao braco "ordem de chegada" um nDCG de 0,99 e um teto impossivel de superar.
    # A ordem de apresentacao e embaralhada por consulta, com semente registrada.
    for consulta in consultas:
        random.Random(SEMENTE_ORDEM + int(consulta['query_id'][1:])).shuffle(consulta['candidates'])

    original = {c['query_id']: list(range(len(c['candidates']))) for c in consultas}
    pontos_bm25 = {c['query_id']: bm25(c['query'], c['candidates']) for c in consultas}
    ordem_bm25 = {qid: sorted(range(len(p)), key=lambda i: -p[i]) for qid, p in pontos_bm25.items()}

    print(f"Ordem original: {avaliar(consultas, original)}")
    print(f"BM25:           {avaliar(consultas, ordem_bm25)}")
    if not args.execute:
        print('Simulacao apenas; nada enviado.')
        return

    OUT.mkdir(parents=True, exist_ok=True)
    key, _ = load_api_key()
    pontos_jev, detalhes = {}, []
    with Ledger(DB, EXPERIMENT) as ledger:
        ledger.authorize(usd_to_nusd('5.00'),
                         hypothesis='O Jev preserva no topo do ranking as ressalvas necessarias',
                         metric='recall de ressalvas no top-3 e nDCG@5')
        ledger.set_block_cap(BLOCK, usd_to_nusd('0.10'))
        ledger.register_arm(ARM, 'S02', PROVIDER, MODEL, endpoint='/api/alpha/decisions')
        for consulta in consultas:
            estado = (f"PERGUNTA: {consulta['query']}\n\n" +
                      '\n'.join(f"Trecho {i + 1}: {c['text']}"
                                for i, c in enumerate(consulta['candidates'])))
            perguntas = {f'trecho_{i + 1}': {
                'type': 'score',
                'instructions': f'{INSTRUCOES} Avalie apenas o Trecho {i + 1}.',
                'criteria': ESCALA} for i in range(len(consulta['candidates']))}
            caminho = f"runs/e4-ressalvas/{consulta['query_id']}.json"
            marcador = time.monotonic()
            saida = dispatch(ledger, arm_id=ARM, block_id=BLOCK, provider=PROVIDER, model=MODEL,
                             state=estado, questions=perguntas, request_path=caminho,
                             runtime_manifest_path=caminho, api_key=key)
            respostas = saida.get('answers') or {}
            notas = []
            for i in range(len(consulta['candidates'])):
                resposta = respostas.get(f'trecho_{i + 1}') or {}
                # O tipo score devolve nota continua na escala declarada, nao um rotulo.
                nota = resposta.get('score')
                nota = float(nota) if isinstance(nota, (int, float)) else -1.0
                notas.append((nota, resposta.get('confidence') or 0))
                detalhes.append({'query_id': consulta['query_id'],
                                 'doc_id': consulta['candidates'][i]['doc_id'],
                                 'gold_rel': consulta['candidates'][i]['rel'],
                                 'ressalva': consulta['candidates'][i]['ressalva'],
                                 'jev_score': nota, 'probabilities': resposta.get('probabilities'),
                                 'confidence': resposta.get('confidence')})
            # Desempate pela confiança, mantendo a ordem original como último critério.
            pontos_jev[consulta['query_id']] = sorted(
                range(len(notas)), key=lambda i: (-notas[i][0], -notas[i][1], i))
            print(f"  {consulta['query_id']}: {saida['status']} "
                  f"{round((time.monotonic() - marcador) * 1000)} ms  scores={[round(n, 2) for n, _ in notas]}",
                  flush=True)
        comprometido = ledger.wallet_committed_nusd()
        disponivel = ledger.wallet_available_nusd()

    resultado = {'at': datetime.now(timezone.utc).isoformat(), 'modelo': MODEL, 'topo': TOPO,
                 'original': avaliar(consultas, original),
                 'bm25': avaliar(consultas, ordem_bm25),
                 'jev': avaliar(consultas, pontos_jev),
                 'ordens': {'original': original, 'bm25': ordem_bm25, 'jev': pontos_jev},
                 'detalhes': detalhes,
                 'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel}
    (OUT / 'relatorio.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2),
                                        encoding='utf-8')
    print(f"\n{'braco':10} {'nDCG@5':>8} {'ressalvas no top-3':>20} {'essenciais no top-3':>21}")
    for nome in ('original', 'bm25', 'jev'):
        d = resultado[nome]
        print(f"{nome:10} {d['ndcg5']:>8} "
              f"{str(d['ressalvas_no_topo']) + '/' + str(d['ressalvas_totais']):>20} "
              f"{d['essenciais_no_topo3']:>21}")
    print(f"\nCarteira: comprometido {comprometido / 1e9:.9f} USD | disponivel {disponivel / 1e9:.6f} USD")


if __name__ == '__main__':
    main()
