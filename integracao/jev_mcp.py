"""Minimal MCP stdio server: no dependencies, no shell execution, no secret in config."""
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from executor.assist import evaluate, RUBRICS
from executor.shared import DB
from integracao.apoio import judge, status
from integracao.seletores import select, tool_definition, route, route_definition


TOOLS = [
    route_definition(),
    tool_definition('tool'),
    tool_definition('skill'),
    {'name': 'jev_status', 'description': 'Verifica credencial e presenca do livro-caixa, sem rede ou gasto.',
     'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    {'name': 'jev_judge',
     'description': 'Julgamentos semanticos fechados: categorias de documentos, intencao, tema, '
                    'duplicidade semantica, relevancia, atributos e rubricas. Ate 8 perguntas '
                    'independentes sobre o mesmo estado em uma chamada. Use para lotes e trabalho '
                    'repetitivo; regras exatas ficam em codigo. Obrigatorio incerto em cada pergunta. '
                    'Envia o estado ao provedor configurado, cobra na carteira compartilhada. '
                    'Nao enviar segredos nem material privado sem autorizacao. Nao autoriza acoes.',
     'inputSchema': {'type': 'object', 'properties': {
         'state': {'type': 'string', 'minLength': 1, 'maxLength': 60000},
         'questions': {'type': 'array', 'minItems': 1, 'maxItems': 8, 'items': {
             'type': 'object', 'properties': {
                 'id': {'type': 'string', 'pattern': '^[a-zA-Z][a-zA-Z0-9_]{0,47}$'},
                 'instructions': {'type': 'string', 'minLength': 1, 'maxLength': 2000},
                 'choices': {'type': 'object', 'minProperties': 2, 'maxProperties': 12,
                             'required': ['incerto'],
                             'additionalProperties': {'type': 'string', 'minLength': 1, 'maxLength': 1000}}},
             'required': ['id', 'instructions', 'choices'], 'additionalProperties': False}}},
         'required': ['state', 'questions'], 'additionalProperties': False}},
    {'name': 'jev_assist',
     'description': 'Classificacao assistida barata de log, suporte por evidencia ou relevancia de trecho. '
                    'Use para subtarefas fechadas em volume, nao para escolher esforco/modelo. '
                    'Envia texto sanitizado ao provedor configurado. Nao enviar dados privados sem autorizacao. '
                    'Resposta nao autoriza acao. Evidencia sobre codigo ainda experimental.',
     'inputSchema': {'type': 'object', 'properties': {
         'task': {'type': 'string', 'enum': list(RUBRICS)}, 'state': {'type': 'string', 'maxLength': 60000}},
         'required': ['task', 'state'], 'additionalProperties': False}},
    {'name': 'jev_rank_context',
     'description': 'Ordena ate 8 trechos para uma pergunta; devolve TODOS os candidatos com IDs. '
                    'Preserve as fontes, ressalvas e instrucoes obrigatorias. Nao e filtro de seguranca.',
     'inputSchema': {'type': 'object', 'properties': {
         'query': {'type': 'string', 'maxLength': 4000},
         'candidates': {'type': 'array', 'minItems': 1, 'maxItems': 8,
                        'items': {'type': 'object', 'properties': {
                            'id': {'type': 'string'}, 'text': {'type': 'string', 'maxLength': 16000}},
                            'required': ['id', 'text'], 'additionalProperties': False}}},
         'required': ['query', 'candidates'], 'additionalProperties': False}},
    {'name': 'jev_metrics', 'description': 'Metricas locais reais do JEV; nenhuma chamada paga.',
     'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    {'name': 'jev_record_review',
     'description': 'Registra avaliacao posterior de uma tentativa existente. Nao confundir '
                    'gabarito do assistente com validacao humana independente.',
     'inputSchema': {'type': 'object', 'properties': {
         'attempt_id': {'type': 'string'}, 'expected_choice': {'type': 'string'},
         'reviewer_kind': {'type': 'string', 'enum': ['human', 'assistant', 'deterministic_check']},
         'evidence': {'type': 'string', 'maxLength': 1000}},
         'required': ['attempt_id', 'expected_choice', 'reviewer_kind', 'evidence'],
         'additionalProperties': False}},
]


def metrics():
    from executor.shared import active_runtime
    runtime = active_runtime(require_fresh=False)
    db_path = runtime['db_path'] if runtime else DB
    if not db_path.is_file():
        return {'available': False, 'reason': 'missing_wallet', 'astra_savings_measured': None}
    with sqlite3.connect(f'file:{db_path.as_posix()}?mode=ro', uri=True) as connection:
        rows = connection.execute('SELECT receipt_json FROM shared_decisions').fetchall()
        receipts = [json.loads(row[0]) for row in rows]
        live = [r for r in receipts if r['evidence_level'] == 'live_component']
        priced = [r for r in live if r.get('cost_source') == 'usage_priced']
        return {'live_calls': len(live), 'usage_priced_cost_usd': sum(r['settled_nusd'] for r in priced) / 1e9,
                'priced_calls': len(priced), 'reported_cost_usd': sum(r['custo_usd'] for r in live if r['custo_usd'] is not None),
                'unknown_cost_calls': sum(r['custo_usd'] is None and r.get('cost_source') != 'usage_priced' for r in live),
                'status': {s:sum(r['status']==s for r in live) for s in {r['status'] for r in live}},
                'astra_savings_measured': None,
                'note': 'Chamadas de componente; nao prova economia ou qualidade de ponta a ponta.'}


def call(name, arguments):
    if name == 'jev_route':
        if set(arguments) - {'task', 'tools', 'skills', 'required_tool_id', 'required_skill_id'}:
            raise ValueError('Invalid route arguments')
        return route(**arguments)
    if name in ('jev_select_tool', 'jev_select_skill'):
        if set(arguments) - {'task', 'candidates', 'required_id'} or not {'task', 'candidates'} <= set(arguments):
            raise ValueError('Invalid selector arguments')
        return select(name.rsplit('_', 1)[-1], **arguments)
    if name == 'jev_status':
        if arguments:
            raise ValueError('No arguments expected')
        return status()
    if name == 'jev_judge':
        if set(arguments) != {'state', 'questions'}:
            raise ValueError('Invalid arguments')
        return judge(**arguments)
    if name == 'jev_assist':
        if set(arguments) != {'task', 'state'} or not isinstance(arguments['state'], str) or len(arguments['state']) > 60000:
            raise ValueError('Invalid arguments')
        return evaluate(**arguments)
    if name == 'jev_rank_context':
        candidates = arguments['candidates']
        if (not isinstance(arguments['query'], str) or len(arguments['query']) > 4000 or
            not 1 <= len(candidates) <= 8 or len({r['id'] for r in candidates}) != len(candidates) or
            any(not isinstance(r['text'], str) or len(r['text']) > 16000 for r in candidates)):
            raise ValueError('Invalid or duplicate candidates')
        scores = {'essencial':3, 'complementar':2, 'incerto':1, 'irrelevante':0}
        rows = []
        for candidate in candidates:
            result = evaluate('context', f"PERGUNTA: {arguments['query']}\nTRECHO:\n{candidate['text']}")
            rows.append({'id': candidate['id'], **result})
        rows.sort(key=lambda r: (scores.get(r['choice'], -1), r['confidence'] or 0), reverse=True)
        return {'candidates': rows, 'discarded': [], 'mode': 'assistive', 'autonomous': False}
    if name == 'jev_metrics':
        return metrics()
    if name == 'jev_record_review':
        if (arguments['reviewer_kind'] not in ('human', 'assistant', 'deterministic_check') or
            not isinstance(arguments['evidence'], str) or not 1 <= len(arguments['evidence']) <= 1000):
            raise ValueError('Invalid review')
        from integracao.jev_router.redacao import limpar
        from datetime import datetime, timezone
        from executor.shared import active_runtime
        runtime = active_runtime(require_fresh=False)
        db_path = runtime['db_path'] if runtime else DB
        if not db_path.is_file():
            raise ValueError('Missing wallet')
        with sqlite3.connect(db_path) as connection:
            if not connection.execute('SELECT 1 FROM shared_decisions WHERE attempt_id=?',
                                      (arguments['attempt_id'],)).fetchone():
                raise ValueError('Unknown attempt')
            connection.execute('CREATE TABLE IF NOT EXISTS shared_reviews '
                               '(id INTEGER PRIMARY KEY, attempt_id TEXT, reviewed_at TEXT, '
                               'expected_choice TEXT, reviewer_kind TEXT, evidence TEXT)')
            connection.execute('INSERT INTO shared_reviews(attempt_id,reviewed_at,expected_choice,reviewer_kind,evidence) '
                               'VALUES(?,?,?,?,?)', (arguments['attempt_id'], datetime.now(timezone.utc).isoformat(),
                               arguments['expected_choice'], arguments['reviewer_kind'], limpar(arguments['evidence'])[0]))
        return {'recorded': True}
    raise ValueError('Unknown tool')


def handle(request):
    method = request.get('method')
    if 'id' not in request:
        return None
    response = {'jsonrpc': '2.0', 'id': request['id']}
    if method == 'initialize':
        response['result'] = {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}},
                              'serverInfo': {'name': 'jev-assist', 'version': '1.0.0'}}
    elif method == 'ping':
        response['result'] = {}
    elif method == 'tools/list':
        response['result'] = {'tools': TOOLS}
    elif method == 'tools/call':
        try:
            params = request['params']
            result = call(params['name'], params.get('arguments', {}))
            response['result'] = {'content': [{'type': 'text', 'text': json.dumps(result, ensure_ascii=False)}],
                                  'isError': False}
        except Exception as error:
            response['result'] = {'content': [{'type': 'text', 'text': json.dumps({
                'status': 'abstain', 'error_type': type(error).__name__,
                'next': 'Continue no fluxo normal; nao repetir chamada automaticamente.'})}], 'isError': True}
    else:
        response['error'] = {'code': -32601, 'message': 'Method not found'}
    return response


def main():
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line)
            response = handle(request)
        except (ValueError, TypeError, AttributeError):
            response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}
        if response is not None:
            sys.stdout.buffer.write((json.dumps(response, ensure_ascii=False)+'\n').encode())
            sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
