"""E12: a replicação do desempate com 30 famílias novas e quatro comparadores econômicos.

É o item 1 da seção 10 do relatório final. O E11 comparou o Jev contra **um** LLM barato em 20
famílias e a conclusão dependeu de qual gabarito era usado. Aqui são 90 casos novos em 30
famílias e quatro comparadores de quatro fornecedores diferentes, com a regra de decisão
congelada em `planning/preregistro-E12-replicacao.md` antes de o corpus existir.

A regra congelada é hostil ao Jev de propósito: só há `vantagem-do-jev` se o IC95 da diferença
pareada separar de zero contra **todos** os quatro comparadores, e se essa leitura sobreviver aos
três gabaritos — o do autor, o oficial adjudicado e o do anotador independente.

Uso:
    python -m executor.run_e12_replicacao              # custo do pior caso, sem enviar nada
    python -m executor.run_e12_replicacao --execute
    python -m executor.run_e12_replicacao --so-analisar  # reanalisa o bruto, sem gastar
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .analise import bootstrap_cluster, limite_superior_erro
from .gabarito import adjudicado, do_anotador_local
from .ledger import Ledger
from .pricing import load_prices, usd_to_nusd, worst_case_nusd
from .run_e1_triagem import CRITERIOS, INSTRUCOES, resumo
from .run_e10_llm_economico import CHAT_URL, MAX_TOKENS, interpretar, prompt
from .run_e11_desempate import mcnemar_exato
from .runner import (dispatch, http_transport, load_api_key, payload_sha256, reported_cost_nusd,
                     reservation_output_tokens, reservation_tokens, usage_from)

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'data' / 'corpus' / 'triagem-replicacao.jsonl'
OUT = ROOT / 'runs' / 'e12-replicacao'
# Gravado caso a caso, como no E11: a primeira execucao daquele experimento perdeu 120 chamadas
# pagas porque a analise quebrou no fim e nada tinha sido persistido.
BRUTO = OUT / 'respostas.jsonl'
DB = ROOT / 'runs' / 'ledger.sqlite3'
EXPERIMENT = 'exp-e12-replicacao'
BLOCK = 'e12-replicacao'
PROVIDER = 'openrouter'
MODELO_JEV = 'typesafe/jev-1.13'
ARM_JEV = 'arm-e12-jev'

# Os quatro comparadores declarados no pre-registro, com o campo em que a resposta de cada um e
# gravada. A ordem aqui e a ordem de execucao, e ela nao muda depois de a primeira chamada sair.
COMPARADORES = [
    ('c1', 'meta-llama/llama-3.1-8b-instruct'),
    ('c2', 'mistralai/mistral-nemo'),
    ('c3', 'google/gemma-3-12b-it'),
    ('c4', 'openai/gpt-oss-20b'),
]


def carregar():
    return [json.loads(linha) for linha in CORPUS.read_text(encoding='utf-8').splitlines()
            if linha.strip()]


def gravar(caso):
    OUT.mkdir(parents=True, exist_ok=True)
    with BRUTO.open('a', encoding='utf-8') as arquivo:
        arquivo.write(json.dumps(caso, ensure_ascii=False) + chr(10))


def recuperar():
    """Reconstroi os casos a partir do bruto, que e append-only.

    Uma linha com `<braco>_anulado_pela_emenda_3` apaga as respostas daquele braco no acumulado:
    e assim que a Emenda 3 tira da ANALISE as chamadas feitas sob um teto de saida que impedia o
    modelo de responder. Sem isso, `update` preservaria os campos antigos e a reexecucao acharia
    que aqueles casos ja tinham resposta.
    """
    if not BRUTO.exists():
        return None
    por_id = {}
    for linha in BRUTO.read_text(encoding='utf-8').splitlines():
        if not linha.strip():
            continue
        caso = json.loads(linha)
        acumulado = por_id.setdefault(caso['case_id'], {})
        # A anulacao vale para o que veio ANTES dela, nunca para o que vem na mesma linha. A
        # primeira versao disto apagava tambem a resposta da reexecucao, porque a marca viajava
        # junto no registro e era aplicada depois do update: nove chamadas ja pagas do c4
        # sumiram da analise sem que nada acusasse.
        for marca in [k for k in caso if k.endswith('_anulado_pela_emenda_3')]:
            braco = marca.split('_', 1)[0]
            for campo in [k for k in list(acumulado)
                          if k == braco or k.startswith(braco + '_')]:
                if campo != marca:
                    acumulado.pop(campo)
        acumulado.update(caso)
    return list(por_id.values()) or None


# Emenda 3: o teto de saida e parametro de transporte, e um modelo que raciocina antes de
# responder gasta saida no raciocinio. Com 64 tokens o c4 devolvia conteudo vazio, o que media o
# teto e nao o modelo. Quem nao aparece aqui usa o teto do E10.
TETO_DE_SAIDA = {'c4': 256}


def payload_chat(modelo, texto, chave=None):
    return {'model': modelo, 'max_tokens': TETO_DE_SAIDA.get(chave, MAX_TOKENS),
            'temperature': 0,
            'response_format': {'type': 'json_object'},
            'messages': [{'role': 'user', 'content': prompt(texto)}]}


def braco_jev(casos, ledger, key):
    for caso in casos:
        caminho = 'runs/e12-replicacao/jev-' + caso['case_id'] + '.json'
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
        print('  jev  ' + caso['case_id'] + ': ' + marca + ' gold='
              + caso['gold'].ljust(11) + ' -> ' + str(caso['jev']), flush=True)


def braco_comparador(chave, modelo, casos, ledger, key, precos):
    entrada = reservation_tokens(precos, PROVIDER, modelo)
    saida_max = reservation_output_tokens(precos, PROVIDER, modelo)
    cabecalhos = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                  'User-Agent': 'jev-lab/1.0'}
    arm = 'arm-e12-' + chave
    for caso in casos:
        # Resposta nova cancela a anulacao anterior daquele braco: quem foi reexecutado sob o
        # teto novo tem resposta valida, e a marca da Emenda 3 nao pode segui-lo.
        caso.pop(chave + '_anulado_pela_emenda_3', None)
        caminho = 'runs/e12-replicacao/' + chave + '-' + caso['case_id'] + '.json'
        corpo = payload_chat(modelo, caso['text'], chave)
        reserva = ledger.reserve(arm_id=arm, block_id=BLOCK, provider=PROVIDER, model=modelo,
                                 max_input_tokens=entrada, max_output_tokens=saida_max,
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
                                      provider_request_id=resposta.get('id'),
                                      http_status=status)
            caso[chave] = None
            caso[chave + '_erro'] = 'http ' + str(status) + ': ' + str(resposta.get('error'))[:160]
        else:
            acao, confianca, erro = interpretar(resposta)
            liquidado = ledger.settle(attempt_id, status='success', usage=uso,
                                      provider_reported_cost_nusd=reportado,
                                      provider_request_id=resposta.get('id'),
                                      model_resolved=resposta.get('model'))
            caso[chave] = acao
            caso[chave + '_confidence'] = confianca
            caso[chave + '_erro'] = erro
        caso[chave + '_attempt_id'] = attempt_id
        caso[chave + '_cost_nusd'] = liquidado.get('settled_nusd')
        caso[chave + '_latency_ms'] = round((time.monotonic() - marcador) * 1000, 1)
        gravar(caso)
        marca = 'ok  ' if caso[chave] == caso['gold'] else 'ERRO'
        print('  ' + chave.ljust(4) + ' ' + caso['case_id'] + ': ' + marca + ' gold='
              + caso['gold'].ljust(11) + ' -> ' + str(caso[chave]), flush=True)


def falha_de_transporte(erro):
    """Erro que impediu o modelo de responder, e que por isso não é resposta dele.

    Emenda 1 do pré-registro, escrita durante a execução e antes de qualquer análise: HTTP 429,
    HTTP 5xx e timeout são falhas de transporte e são repetidos; JSON inválido e classe fora do
    contrato são erro do comparador e não são repetidos.
    """
    if not erro:
        return False
    return (erro.startswith('http 429') or erro.startswith('http 5')
            or 'timeout' in erro.lower())


def repescar(casos, ledger, key, precos, tentativas_max=3, pausa=6.0):
    """Refaz as chamadas que morreram no transporte, com espaçamento, até o teto da Emenda 1."""
    pendentes = 0
    for chave, modelo in COMPARADORES:
        for tentativa in range(2, tentativas_max + 1):
            alvos = [c for c in casos
                     if c.get(chave) is None and falha_de_transporte(c.get(chave + '_erro'))]
            if not alvos:
                break
            print('\n-- repescagem %d/%d de %s: %d caso(s)'
                  % (tentativa, tentativas_max, chave, len(alvos)), flush=True)
            for caso in alvos:
                time.sleep(pausa)
                caso[chave + '_tentativas_transporte'] = tentativa
                braco_comparador(chave, modelo, [caso], ledger, key, precos)
        ainda = [c['case_id'] for c in casos
                 if c.get(chave) is None and falha_de_transporte(c.get(chave + '_erro'))]
        if ainda:
            pendentes += len(ainda)
            print('  %s: %d caso(s) seguem sem resposta apos %d tentativas e contam como erro: %s'
                  % (chave, len(ainda), tentativas_max, ', '.join(ainda)), flush=True)
    return pendentes


def fundir_com_o_corpus():
    """O corpus com o que ja foi respondido por cima, para retomar sem perder nada.

    A execucao morreu no meio do quarto brace por um defeito meu — um comparador devolveu uma
    LISTA de objetos e o interpretador so previa objeto. As 361 chamadas ja pagas estao no bruto,
    e refaze-las seria gastar de novo e, pior, reexecutar bracos que o pre-registro congela.
    """
    respondidos = {c['case_id']: c for c in (recuperar() or [])}
    casos = []
    for caso in carregar():
        caso.update(respondidos.get(caso['case_id'], {}))
        casos.append(caso)
    return casos


def faltantes(casos, chave):
    """Casos em que aquele braco nunca chegou a ser chamado."""
    return [c for c in casos if not c.get(chave + '_attempt_id')]


def completar(casos, ledger, key, precos):
    """Chama so o que falta, brace a brace, e nunca o que ja tem tentativa registrada."""
    pendentes = faltantes(casos, 'jev')
    if pendentes:
        print('-- jev: %d caso(s) faltando' % len(pendentes), flush=True)
        braco_jev(pendentes, ledger, key)
    for chave, modelo in COMPARADORES:
        pendentes = faltantes(casos, chave)
        if not pendentes:
            continue
        print('')
        print('-- %s: %s (%d caso(s) faltando)' % (chave, modelo, len(pendentes)), flush=True)
        braco_comparador(chave, modelo, pendentes, ledger, key, precos)


def gabaritos(casos):
    """Os três gabaritos do estudo, caso a caso, para este corpus.

    O do autor vem do próprio corpus; o oficial é o do autor com os casos em disputa
    substituídos pela adjudicação cega; o do anotador independente vem do E8. Quando a
    adjudicação ou a anotação ainda não existem, o gabarito correspondente é omitido em vez de
    cair silenciosamente no do autor — um gabarito ausente não é um gabarito que concorda.
    """
    do_autor = {c['case_id']: c['gold'] for c in casos}
    saida = {'autor': do_autor}
    local = do_anotador_local()
    anotado = bool(local) and all(c['case_id'] in local for c in casos)
    if anotado:
        saida['anotador local'] = {c['case_id']: local[c['case_id']] for c in casos}
    oficial, procedencia = adjudicado()
    divergem = [c['case_id'] for c in casos
                if anotado and local[c['case_id']] != c['gold']]
    # O gabarito oficial deste corpus so existe quando ha um segundo anotador sobre ELE e, se os
    # dois divergirem, quando a divergencia passou pelo terceiro juiz cego. `adjudicado()` cobre
    # o estudo inteiro e devolveria o gold do autor para casos que ninguem adjudicou: isso e um
    # gabarito ausente se passando por gabarito que concorda.
    adjudicado_aqui = (OUT / 'adjudicacao.json').exists()
    procedencia = dict(procedencia)
    procedencia['corpus_tem_segundo_anotador'] = anotado
    procedencia['casos_em_que_os_anotadores_divergem'] = sorted(divergem)
    procedencia['corpus_adjudicado'] = adjudicado_aqui
    if anotado and (not divergem or adjudicado_aqui):
        saida['oficial'] = {c['case_id']: oficial.get(c['case_id'], {}).get('gold', c['gold'])
                            for c in casos}
    return saida, procedencia


def comparar(casos, gold, chave):
    """Diferença pareada Jev x um comparador, sob um gabarito, com tudo que a regra pede."""
    clusters = {}
    for caso in casos:
        alvo = gold[caso['case_id']]
        clusters.setdefault(caso['family'], []).append(
            (1 if caso.get('jev') == alvo else 0, 1 if caso.get(chave) == alvo else 0))
    pareada = bootstrap_cluster(clusters)
    so_jev = [c['case_id'] for c in casos
              if c.get('jev') == gold[c['case_id']] and c.get(chave) != gold[c['case_id']]]
    so_outro = [c['case_id'] for c in casos
                if c.get(chave) == gold[c['case_id']] and c.get('jev') != gold[c['case_id']]]
    return {'pareada': pareada, 'so_jev': so_jev, 'so_comparador': so_outro,
            'mcnemar_p_exato': round(mcnemar_exato(len(so_jev), len(so_outro)), 4),
            'separa_de_zero': pareada['ic95'][0] > 0,
            'separa_contra_o_jev': pareada['ic95'][1] < 0}


COBERTURA_MINIMA = 0.90


def cobertura_dos_bracos(casos):
    """Emenda 2: braço com cobertura abaixo de 90% é incompleto e sai da leitura primária.

    O critério foi escrito antes de qualquer acurácia ser calculada, justamente para que a
    decisão de manter ou tirar um braço não dependesse de quanto ele acertou.
    """
    saida = {}
    for chave, modelo in COMPARADORES:
        validas = sum(1 for c in casos if c.get(chave))
        cobertura = round(validas / len(casos), 4) if casos else 0.0
        saida[chave] = {'modelo': modelo, 'respostas_validas': validas,
                        'casos_programados': len(casos), 'cobertura': cobertura,
                        'minimo_exigido': COBERTURA_MINIMA,
                        'entra_na_leitura': cobertura >= COBERTURA_MINIMA}
    return saida


def leitura(comparacoes):
    """A regra congelada no pré-registro, aplicada sem margem de interpretação.

    Interseção-união: só há vantagem se TODOS os intervalos separarem acima de zero. Basta um
    comparador barato empatar para que a leitura não seja favorável ao Jev.
    """
    if any(c['separa_contra_o_jev'] for c in comparacoes.values()):
        quais = sorted(k for k, c in comparacoes.items() if c['separa_contra_o_jev'])
        return ('vantagem-do-comparador',
                'o IC95 esta inteiramente abaixo de zero contra ' + ', '.join(quais)
                + ': o comparador barato e melhor')
    if all(c['separa_de_zero'] for c in comparacoes.values()):
        return ('vantagem-do-jev',
                'os IC95 dos quatro comparadores estao inteiramente acima de zero: ha evidencia '
                'de que o Jev supera a classe "LLM generico e barato" nesta tarefa')
    faltam = sorted(k for k, c in comparacoes.items() if not c['separa_de_zero'])
    return ('sem-evidencia-de-vantagem',
            'o IC95 contem zero contra ' + ', '.join(faltam) + ': nao ha evidencia de vantagem '
            'sobre todos os comparadores, e a recomendacao passa a ser o classificador mais '
            'barato que passe no criterio de erro grave')


def erro_grave(casos, gold, campos):
    saida = {}
    for campo in campos:
        falsos = [c['case_id'] for c in casos
                  if c.get(campo) == 'cancelar' and gold[c['case_id']] != 'cancelar']
        perdidos = [c['case_id'] for c in casos
                    if gold[c['case_id']] == 'cancelar' and c.get(campo) != 'cancelar']
        nao_cancelar = sum(1 for c in casos if gold[c['case_id']] != 'cancelar')
        cancelar = sum(1 for c in casos if gold[c['case_id']] == 'cancelar')
        saida[campo] = {
            'falso_cancelar': falsos, 'cancelar_perdido': perdidos,
            'limite_superior_falso_cancelar': limite_superior_erro(len(falsos), nao_cancelar),
            'limite_superior_cancelar_perdido': limite_superior_erro(len(perdidos), cancelar),
        }
    return saida


def custo_liquidado(attempt_ids):
    """Le o custo no livro-caixa, e nao o que o caso guardou na hora da chamada.

    As 76 chamadas do c3 recusadas por limite de taxa foram liquidadas pelo pior caso e depois
    RETIFICADAS para zero contra o extrato do provedor, que mostrava que nada havia sido
    cobrado. O numero gravado dentro do caso e o de antes da retificacao: publica-lo daria um
    custo por mil classificacoes quase cem vezes maior do que o real, no braco em que o provedor
    recusou mais chamadas. O livro-caixa e a fonte; o caso e so um eco do instante.
    """
    import sqlite3
    if not attempt_ids or not DB.exists():
        return {}
    con = sqlite3.connect(DB)
    try:
        marcas = ','.join('?' * len(attempt_ids))
        linhas = con.execute(
            'SELECT attempt_id, settled_nusd FROM attempt_budget WHERE attempt_id IN (' + marcas
            + ')', list(attempt_ids)).fetchall()
    finally:
        con.close()
    return {a: c for a, c in linhas if c is not None}


def custo_por_mil(casos, campos):
    saida = {}
    for campo in campos:
        ids = [c.get(campo + '_attempt_id') for c in casos if c.get(campo + '_attempt_id')]
        liquidado = custo_liquidado(ids)
        validos = [liquidado[a] for a in ids if a in liquidado]
        if not validos:
            saida[campo] = None
            continue
        saida[campo] = {'chamadas_liquidadas': len(validos),
                        'custo_total_nusd': sum(validos),
                        'fonte': 'runs/ledger.sqlite3 (attempt_budget.settled_nusd)',
                        'custo_por_mil_classificacoes_usd': round(
                            sum(validos) / len(validos) * 1000 / 1e9, 6)}
    return saida


def registrar_bracos(ledger):
    ledger.authorize(usd_to_nusd('5.00'),
                     hypothesis='O Jev e um LLM generico barato acertam igualmente a triagem',
                     metric='diferenca pareada de acuracia contra quatro comparadores, '
                            'em corpus novo de 30 familias')
    ledger.set_block_cap(BLOCK, usd_to_nusd('0.80'))
    ledger.register_arm(ARM_JEV, 'S01', PROVIDER, MODELO_JEV, endpoint='/api/alpha/decisions')
    for chave, modelo in COMPARADORES:
        ledger.register_arm('arm-e12-' + chave, 'S01', PROVIDER, modelo,
                            endpoint='/api/v1/chat/completions')


def executar_todos(casos, key, precos):
    with Ledger(DB, EXPERIMENT) as ledger:
        registrar_bracos(ledger)
        braco_jev(casos, ledger, key)
        for chave, modelo in COMPARADORES:
            print('\n-- ' + chave + ': ' + modelo, flush=True)
            braco_comparador(chave, modelo, casos, ledger, key, precos)
        return ledger.wallet_committed_nusd(), ledger.wallet_available_nusd()


def analisar(casos, comprometido, disponivel):
    campos = ['jev'] + [chave for chave, _ in COMPARADORES]
    mapas, procedencia = gabaritos(casos)
    cobertura = cobertura_dos_bracos(casos)
    na_leitura = [chave for chave, bloco in cobertura.items() if bloco['entra_na_leitura']]
    por_gabarito = {}
    for nome, gold in mapas.items():
        comparacoes = {chave: comparar(casos, gold, chave) for chave, _ in COMPARADORES}
        chave_leitura, frase = leitura({k: v for k, v in comparacoes.items() if k in na_leitura})
        por_gabarito[nome] = {
            'acuracia': {campo: round(sum(1 for c in casos
                                          if c.get(campo) == gold[c['case_id']]) / len(casos), 4)
                         for campo in campos},
            'comparacoes': comparacoes,
            'leitura': chave_leitura, 'leitura_texto': frase,
            'erro_grave': erro_grave(casos, gold, campos),
        }

    leituras = {nome: bloco['leitura'] for nome, bloco in por_gabarito.items()}
    if 'oficial' in leituras:
        principal = leituras['oficial']
    else:
        principal = leituras['autor']
    if len(set(leituras.values())) > 1:
        veredito = 'depende-do-gabarito'
        veredito_texto = ('as leituras divergem entre os gabaritos ('
                          + '; '.join(n + ': ' + v for n, v in sorted(leituras.items()))
                          + '), e o pre-registro manda reportar a divergencia em vez de '
                            'escolher a leitura mais favoravel')
    else:
        veredito = principal
        veredito_texto = por_gabarito[max(leituras, key=lambda n: n == 'oficial')]['leitura_texto']

    relatorio = {
        'at': datetime.now(timezone.utc).isoformat(),
        'preregistro': 'planning/preregistro-E12-replicacao.md',
        'corpus': str(CORPUS.relative_to(ROOT)).replace(chr(92), '/'),
        'modelo': MODELO_JEV,
        'comparadores': {chave: modelo for chave, modelo in COMPARADORES},
        'casos_programados': len(casos),
        'familias': len({c['family'] for c in casos}),
        'resumo': {campo: resumo(campo, casos) for campo in campos},
        'gabaritos_disponiveis': sorted(mapas),
        'cobertura_dos_bracos': cobertura,
        'bracos_na_leitura': na_leitura,
        'bracos_incompletos': [c for c in cobertura if c not in na_leitura],
        'adjudicacao': procedencia,
        'por_gabarito': por_gabarito,
        'leitura_por_gabarito': leituras,
        'veredito': veredito, 'veredito_texto': veredito_texto,
        'custo': custo_por_mil(casos, campos),
        'respostas_invalidas': {campo: [c['case_id'] for c in casos if not c.get(campo)]
                                for campo in campos},
        'falhas_de_transporte': {
            chave: {'sem_resposta_apos_repescagem': [
                        c['case_id'] for c in casos
                        if c.get(chave) is None and falha_de_transporte(c.get(chave + '_erro'))],
                    'casos_repescados': sorted(
                        c['case_id'] for c in casos if c.get(chave + '_tentativas_transporte'))}
            for chave, _ in COMPARADORES},
        'casos': casos,
        'wallet_committed_nusd': comprometido, 'wallet_available_nusd': disponivel,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'relatorio.json').write_text(json.dumps(relatorio, ensure_ascii=False, indent=2),
                                        encoding='utf-8')

    print('')
    for nome, bloco in por_gabarito.items():
        print('gabarito ' + nome + ':')
        for campo in campos:
            print('  %-4s %.4f' % (campo, bloco['acuracia'][campo]))
        for chave, _ in COMPARADORES:
            c = bloco['comparacoes'][chave]
            print('  jev - %s: %+.4f IC95 [%.4f; %.4f] McNemar p=%.4f'
                  % (chave, c['pareada']['diferenca_observada'], c['pareada']['ic95'][0],
                     c['pareada']['ic95'][1], c['mcnemar_p_exato']))
        print('  LEITURA: ' + bloco['leitura'])
    print('\nVEREDITO PRE-REGISTRADO: ' + veredito + '\n  ' + veredito_texto)
    if comprometido is not None:
        print('Carteira: %.9f USD comprometidos' % (comprometido / 1e9))
    return relatorio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--so-analisar', action='store_true',
                        help='refaz a analise a partir de runs/e12-replicacao/respostas.jsonl')
    parser.add_argument('--continuar', action='store_true',
                        help='chama so os casos que nenhum braco chegou a responder')
    parser.add_argument('--repescar', action='store_true',
                        help='refaz so as chamadas que morreram no transporte (Emenda 1)')
    args = parser.parse_args()
    precos = load_prices()

    if args.so_analisar:
        casos = recuperar()
        if not casos:
            raise SystemExit('nao ha bruto em runs/e12-replicacao/respostas.jsonl')
        print('Reanalisando %d casos do bruto, sem nenhuma chamada.' % len(casos))
        analisar(casos, None, None)
        return

    if args.repescar or args.continuar:
        casos = fundir_com_o_corpus()
        key = load_api_key()[0]
        with Ledger(DB, EXPERIMENT) as ledger:
            registrar_bracos(ledger)
            if args.continuar:
                completar(casos, ledger, key, precos)
            pendentes = repescar(casos, ledger, key, precos)
            comprometido = ledger.wallet_committed_nusd()
            disponivel = ledger.wallet_available_nusd()
        print('')
        print('Casos ainda sem resposta por falha de transporte: %d' % pendentes)
        analisar(casos, comprometido, disponivel)
        return

    casos = carregar()
    pior_jev = worst_case_nusd(precos, PROVIDER, MODELO_JEV,
                               reservation_tokens(precos, PROVIDER, MODELO_JEV),
                               reservation_output_tokens(precos, PROVIDER, MODELO_JEV))
    piores = [(chave, modelo,
               worst_case_nusd(precos, PROVIDER, modelo,
                               reservation_tokens(precos, PROVIDER, modelo),
                               reservation_output_tokens(precos, PROVIDER, modelo)))
              for chave, modelo in COMPARADORES]

    if not args.execute:
        print('%d casos, %d bracos = %d chamadas.'
              % (len(casos), 1 + len(COMPARADORES), len(casos) * (1 + len(COMPARADORES))))
        print('Pior caso por chamada: jev US$ %.9f' % (pior_jev / 1e9))
        for chave, modelo, pior in piores:
            print('  %-3s %-40s US$ %.9f' % (chave, modelo, pior / 1e9))
        total = (pior_jev + sum(p for _, _, p in piores)) * len(casos)
        print('Pior caso total: US$ %.9f. Nada enviado.' % (total / 1e9))
        return

    OUT.mkdir(parents=True, exist_ok=True)
    key = load_api_key()[0]
    comprometido, disponivel = executar_todos(casos, key, precos)
    analisar(casos, comprometido, disponivel)


if __name__ == '__main__':
    main()
