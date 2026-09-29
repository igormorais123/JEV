"""Bounded semantic judgments through the existing wallet; no separate paid client."""
import json
import re
import sqlite3

from executor import shared, credenciais
from integracao.jev_router.redacao import limpar


def status():
    result = {'credentials': credenciais.situacao(), 'paid_ready': False}
    try:
        runtime = shared.active_runtime(require_fresh=False)
    except Exception as error:
        return {**result, 'reason': 'invalid_runtime_profile', 'error_type': type(error).__name__}
    db_path = runtime['db_path'] if runtime else shared.DB
    result.update(wallet_exists=db_path.is_file(), profile='typesafe-local-20260921' if runtime else 'historical')
    if not result['wallet_exists']:
        return {**result, 'reason': 'missing_wallet',
                'next': 'Recuperar runs/ledger.sqlite3 atualizado do outro PC; não criar saldo novo.'}
    try:
        with sqlite3.connect(f'file:{db_path.as_posix()}?mode=ro', uri=True) as db:
            cap = db.execute("SELECT cap_nusd FROM wallet WHERE wallet_id='default'").fetchone()
        result['wallet_cap_usd'] = cap[0] / 1e9 if cap else None
        from executor.ledger import Ledger
        with Ledger(db_path, 'shared-' + (runtime['consumer'] if runtime else 'tools'),
                    prices=runtime['prices'] if runtime else None) as ledger:
            committed = ledger.wallet_committed_nusd()
            result['committed_usd'] = committed / 1e9
            result['remaining_usd'] = ledger.wallet_available_nusd() / 1e9
        if runtime:
            try:
                shared.active_runtime()
                credenciais.chave(runtime['provider'])
                price = runtime['prices']['models']['typesafe:jev-1.13.0']
                worst = shared.worst_case_nusd(runtime['prices'], 'typesafe', 'jev-1.13.0',
                                               price['context_length'], price['max_completion_tokens'])
                result['next_call_reservation_usd'] = worst / 1e9
                result['paid_ready'] = cap[0] - committed >= worst
                result['reason'] = 'ready' if result['paid_ready'] else 'insufficient_reservable_balance'
            except Exception as error:
                result.update(reason='runtime_check_failed', error_type=type(error).__name__)
        else:
            result['reason'] = 'wallet_present_requires_runtime_budget_and_price_checks'
        result['note'] = 'Prontidão local; reserva atômica final ocorre em cada chamada. Não testa a API.'
    except sqlite3.Error:
        result['reason'] = 'wallet_unreadable'
    return result


def judge(state, questions):
    if not isinstance(state, str) or not 1 <= len(state) <= 60000:
        raise ValueError('Invalid state')
    if not isinstance(questions, list) or not 1 <= len(questions) <= 8:
        raise ValueError('Use one to eight independent questions')
    rubric = {}
    for q in questions:
        if not isinstance(q, dict) or set(q) != {'id', 'instructions', 'choices'}:
            raise ValueError('Invalid question')
        identity = q['id']
        if not isinstance(identity, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]{0,47}', identity) or identity in rubric:
            raise ValueError('Invalid or duplicate question ID')
        if not isinstance(q['instructions'], str) or not 1 <= len(q['instructions']) <= 2000:
            raise ValueError('Invalid instructions')
        choices = q['choices']
        if not isinstance(choices, dict) or not 2 <= len(choices) <= 12 or 'incerto' not in choices:
            raise ValueError('Two to twelve choices, including incerto, required')
        if any(not isinstance(k, str) or not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]{0,47}', k)
               or not isinstance(v, str) or not 1 <= len(v) <= 1000 for k, v in choices.items()):
            raise ValueError('Invalid choice')
        rubric[identity] = {'type': 'choice', 'instructions': q['instructions'], 'criteria': choices}
    clean_state, masked = limpar(state)
    clean_rubric = json.loads(limpar(json.dumps(rubric, ensure_ascii=False))[0])
    answers, receipt = shared.ask(clean_state, clean_rubric, consumer='tools')
    return {'answers': answers, 'receipt': receipt, 'masked_state': masked,
            'mode': 'assistive', 'autonomous': False,
            'note': 'Confidence não mede verdade nem autoriza ação. Revisar a fonte e manter todos os IDs.'}
