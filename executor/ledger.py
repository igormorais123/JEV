"""Controle financeiro com reserva atomica antes de cada tentativa paga.

Regra de liberacao: gasto liquidado + reservas pendentes + pior custo da proxima
tentativa <= teto global e teto do bloco. Tudo em nanodolares inteiros.
Timeout conserva a reserva; so ha liberacao com evidencia de que nada foi enviado.
"""
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .pricing import PricingError, load_prices, observed_nusd, snapshot_id, worst_case_nusd

SCHEMA_PATH = Path(__file__).resolve().parents[1] / 'planning' / 'schema.sql'
SETTLED_STATUSES = ('success', 'http_error', 'invalid_response')


class BudgetError(Exception):
    """Reserva negada: estouraria o teto global ou o teto do bloco."""


class LedgerStateError(Exception):
    """Transicao de estado invalida para a tentativa."""


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


class Ledger:
    def __init__(self, db_path, experiment_id, prices=None, timeout=30.0):
        self.db_path = str(db_path)
        self.experiment_id = experiment_id
        self.prices = prices if prices is not None else load_prices()
        self.db = sqlite3.connect(self.db_path, timeout=timeout, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode = WAL')
        self.db.execute('PRAGMA busy_timeout = 30000')
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.executescript(SCHEMA_PATH.read_text(encoding='utf-8'))
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS wallet (
              wallet_id TEXT PRIMARY KEY,
              cap_nusd INTEGER NOT NULL CHECK(cap_nusd >= 0),
              declared_at_utc TEXT NOT NULL,
              note TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS budget_blocks (
              block_id TEXT NOT NULL,
              experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
              cap_nusd INTEGER NOT NULL CHECK(cap_nusd >= 0),
              PRIMARY KEY(experiment_id, block_id)
            );
            CREATE TABLE IF NOT EXISTS attempt_budget (
              attempt_id TEXT PRIMARY KEY,
              experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
              block_id TEXT NOT NULL,
              reserved_nusd INTEGER NOT NULL CHECK(reserved_nusd >= 0),
              settled_nusd INTEGER CHECK(settled_nusd >= 0),
              cost_source TEXT,
              -- Identidade precificada na reserva. A liquidacao usa ESTA identidade, nunca
              -- a do braco: senao uma reserva de modelo caro poderia ser liquidada pela
              -- tarifa de um modelo barato e liberar saldo que nao existe.
              priced_provider TEXT,
              priced_model TEXT
            );
            """
        )

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # --- configuracao -------------------------------------------------
    def authorize(self, cap_nusd, hypothesis='executor financeiro', metric='custo por decisao util',
                  seed=20260918, protocol_version='1.0'):
        with self._tx():
            self.db.execute(
                'INSERT OR REPLACE INTO experiments(experiment_id,protocol_version,hypothesis,primary_metric,'
                'decision_rule_json,preregistered_at_utc,seed,budget_cap_nusd,status,amendments_json)'
                ' VALUES(?,?,?,?,?,?,?,?,?,?)',
                (self.experiment_id, protocol_version, hypothesis, metric, '{}', now_utc(), seed,
                 int(cap_nusd), 'running', '[]'),
            )
            self._event(None, 'authorize', int(cap_nusd), {'cap_nusd': int(cap_nusd)})
        return int(cap_nusd)

    def set_block_cap(self, block_id, cap_nusd):
        with self._tx():
            self.db.execute(
                'INSERT OR REPLACE INTO budget_blocks(block_id,experiment_id,cap_nusd) VALUES(?,?,?)',
                (block_id, self.experiment_id, int(cap_nusd)),
            )
        return int(cap_nusd)

    def register_arm(self, arm_id, system_id, provider, model_requested, endpoint=None,
                     config_sha256='0' * 64, rubric_version='1.0', conditions=None):
        with self._tx():
            self.db.execute(
                'INSERT OR REPLACE INTO arms(arm_id,experiment_id,system_id,repo_sha,provider,endpoint,'
                'model_requested,config_sha256,rubric_version,conditions_json) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (arm_id, self.experiment_id, system_id, None, provider, endpoint, model_requested,
                 config_sha256, rubric_version, json.dumps(conditions or {}, ensure_ascii=False)),
            )
        return arm_id

    # --- consulta -----------------------------------------------------
    def committed_nusd(self):
        """Liquidado + reservas abertas deste experimento."""
        row = self.db.execute(
            'SELECT COALESCE(SUM(CASE WHEN settled_nusd IS NULL THEN reserved_nusd ELSE settled_nusd END),0) AS total'
            ' FROM attempt_budget WHERE experiment_id = ?',
            (self.experiment_id,),
        ).fetchone()
        return int(row['total'])

    def wallet_committed_nusd(self):
        """Tudo que ja foi comprometido na base, somando TODOS os experimentos.

        O teto autorizado e da carteira, nao de cada experimento: sem isso, abrir um
        experimento novo abriria um teto novo e o limite global seria ficcao.
        """
        row = self.db.execute(
            'SELECT COALESCE(SUM(CASE WHEN settled_nusd IS NULL THEN reserved_nusd ELSE settled_nusd END),0) AS total'
            ' FROM attempt_budget'
        ).fetchone()
        return int(row['total'])

    def set_wallet_cap(self, cap_nusd, note='teto global autorizado', wallet_id='default'):
        with self._tx():
            self.db.execute(
                'INSERT OR REPLACE INTO wallet(wallet_id,cap_nusd,declared_at_utc,note) VALUES(?,?,?,?)',
                (wallet_id, int(cap_nusd), now_utc(), note),
            )
        return int(cap_nusd)

    def wallet_cap_nusd(self, wallet_id='default'):
        row = self.db.execute('SELECT cap_nusd FROM wallet WHERE wallet_id = ?', (wallet_id,)).fetchone()
        if row is None:
            raise BudgetError('Carteira sem teto declarado; nenhuma chamada paga e autorizada')
        return int(row['cap_nusd'])

    def wallet_available_nusd(self):
        return self.wallet_cap_nusd() - self.wallet_committed_nusd()

    def block_committed_nusd(self, block_id):
        row = self.db.execute(
            'SELECT COALESCE(SUM(CASE WHEN settled_nusd IS NULL THEN reserved_nusd ELSE settled_nusd END),0) AS total'
            ' FROM attempt_budget WHERE experiment_id = ? AND block_id = ?',
            (self.experiment_id, block_id),
        ).fetchone()
        return int(row['total'])

    def cap_nusd(self):
        row = self.db.execute(
            'SELECT budget_cap_nusd FROM experiments WHERE experiment_id = ?', (self.experiment_id,)
        ).fetchone()
        if not row:
            raise BudgetError('Experimento sem autorizacao registrada')
        return int(row['budget_cap_nusd'])

    def available_nusd(self):
        return self.cap_nusd() - self.committed_nusd()

    def open_attempts(self):
        rows = self.db.execute(
            'SELECT a.attempt_id, a.status, b.reserved_nusd, b.block_id FROM attempts a'
            ' JOIN attempt_budget b ON b.attempt_id = a.attempt_id'
            ' WHERE b.experiment_id = ? AND b.settled_nusd IS NULL ORDER BY a.execution_order',
            (self.experiment_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- ciclo de vida da tentativa ------------------------------------
    def reserve(self, arm_id, block_id, provider, model, max_input_tokens, max_output_tokens, *,
                payload_sha256, request_path, runtime_manifest_path, host_id='local',
                evidence_level='live_component', parent_attempt_id=None, batch_group_id=None,
                transport_group_id=None, cache_key=None, attempt_id=None):
        """Reserva o pior custo antes do envio. Sem preco ou sem teto de tokens, nao despacha."""
        worst = worst_case_nusd(self.prices, provider, model, max_input_tokens, max_output_tokens)
        attempt_id = attempt_id or str(uuid.uuid4())
        with self._tx(immediate=True):
            wallet_cap = self.wallet_cap_nusd()
            wallet_committed = self.wallet_committed_nusd()
            if wallet_committed + worst > wallet_cap:
                raise BudgetError(
                    f'Teto da carteira: comprometido {wallet_committed} + pior caso {worst} > '
                    f'teto {wallet_cap} nusd'
                )
            cap = self.cap_nusd()
            committed = self.committed_nusd()
            if committed + worst > cap:
                raise BudgetError(
                    f'Teto do experimento: comprometido {committed} + pior caso {worst} > teto {cap} nusd'
                )
            block = self.db.execute(
                'SELECT cap_nusd FROM budget_blocks WHERE experiment_id = ? AND block_id = ?',
                (self.experiment_id, block_id),
            ).fetchone()
            if block is None:
                raise BudgetError(f'Bloco {block_id} sem teto registrado')
            block_cap = int(block['cap_nusd'])
            block_committed = self.block_committed_nusd(block_id)
            if block_committed + worst > block_cap:
                raise BudgetError(
                    f'Teto do bloco {block_id}: comprometido {block_committed} + pior caso {worst} > {block_cap} nusd'
                )
            order = self.db.execute('SELECT COALESCE(MAX(execution_order),0)+1 AS n FROM attempts').fetchone()['n']
            self.db.execute(
                'INSERT INTO attempts(attempt_id,arm_id,parent_attempt_id,block_id,provider_request_id,model_resolved,'
                'host_id,batch_group_id,transport_group_id,execution_order,evidence_level,payload_sha256,request_path,'
                'response_path,started_at_utc,ended_at_utc,latency_ms,status,error_json,raw_usage_json,input_tokens,'
                'output_tokens,known_cost_nusd,price_snapshot_id,cache_key,runtime_manifest_path)'
                ' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (attempt_id, arm_id, parent_attempt_id, block_id, None, None, host_id, batch_group_id,
                 transport_group_id, order, evidence_level, payload_sha256, request_path, None, None, None,
                 None, 'reserved', None, None, None, None, None, snapshot_id(self.prices), cache_key,
                 runtime_manifest_path),
            )
            self.db.execute(
                'INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,settled_nusd,'
                'cost_source,priced_provider,priced_model) VALUES(?,?,?,?,NULL,NULL,?,?)',
                (attempt_id, self.experiment_id, block_id, worst, provider, model),
            )
            self._event(attempt_id, 'reserve', worst, {
                'provider': provider, 'model': model, 'block_id': block_id,
                'max_input_tokens': max_input_tokens, 'max_output_tokens': max_output_tokens,
            })
        return {'attempt_id': attempt_id, 'reserved_nusd': worst}

    def mark_sent(self, attempt_id):
        with self._tx():
            self._require_status(attempt_id, ('reserved',))
            self.db.execute('UPDATE attempts SET status = ?, started_at_utc = ? WHERE attempt_id = ?',
                            ('sent', now_utc(), attempt_id))

    def mark_timeout(self, attempt_id, error=None):
        """Timeout nao libera reserva: a chamada pode ter sido cobrada."""
        with self._tx():
            self._require_status(attempt_id, ('reserved', 'sent'))
            self.db.execute(
                'UPDATE attempts SET status = ?, ended_at_utc = ?, error_json = ? WHERE attempt_id = ?',
                ('timeout', now_utc(), json.dumps(error or {'kind': 'timeout'}, ensure_ascii=False), attempt_id),
            )

    def cancel_before_send(self, attempt_id, evidence):
        """Unica liberacao permitida: evidencia de que a requisicao nao saiu."""
        if not evidence:
            raise LedgerStateError('Liberacao exige evidencia de nao envio')
        with self._tx():
            row = self._require_status(attempt_id, ('reserved',))
            self.db.execute('UPDATE attempts SET status = ?, ended_at_utc = ? WHERE attempt_id = ?',
                            ('cancelled_before_send', now_utc(), attempt_id))
            self.db.execute('UPDATE attempt_budget SET settled_nusd = 0, cost_source = ? WHERE attempt_id = ?',
                            ('cancelled_before_send', attempt_id))
            self._event(attempt_id, 'release', int(row['reserved_nusd']), {'evidence': evidence})

    def settle(self, attempt_id, *, status='success', usage=None, provider_request_id=None, model_resolved=None,
               response_path=None, latency_ms=None, provider_reported_cost_nusd=None, provider=None, model=None):
        """Liquida a tentativa. Sem usage confiavel, o custo permanece o pior caso reservado."""
        if status not in SETTLED_STATUSES:
            raise LedgerStateError(f'Status de liquidacao invalido: {status}')
        with self._tx(immediate=True):
            row = self._require_status(attempt_id, ('reserved', 'sent', 'timeout'))
            reserved = int(row['reserved_nusd'])
            # A identidade que precificou a reserva e a unica base legitima de liquidacao.
            # Um provider/model passado aqui que divirja dela e recusado, nao aceito.
            if row['priced_provider'] is None or row['priced_model'] is None:
                raise LedgerStateError('Tentativa sem identidade de preco registrada na reserva')
            if provider is not None and provider != row['priced_provider']:
                raise LedgerStateError(
                    f"Provedor da liquidacao ({provider}) difere do reservado ({row['priced_provider']})")
            if model is not None and model != row['priced_model']:
                raise LedgerStateError(
                    f"Modelo da liquidacao ({model}) difere do reservado ({row['priced_model']})")
            provider = row['priced_provider']
            model = row['priced_model']
            input_tokens = output_tokens = None
            if provider_reported_cost_nusd is not None:
                cost = int(provider_reported_cost_nusd)
                source = 'provider_reported'
            elif usage and isinstance(usage.get('input_tokens'), int) and isinstance(usage.get('output_tokens'), int):
                input_tokens = usage['input_tokens']
                output_tokens = usage['output_tokens']
                try:
                    cost = observed_nusd(self.prices, provider, model, input_tokens, output_tokens)
                    source = 'usage_priced'
                except PricingError:
                    cost = reserved
                    source = 'worst_case_no_price'
            else:
                cost = reserved
                source = 'worst_case_no_usage'
            evidence = {'cost_source': source, 'reserved_nusd': reserved}
            if cost > reserved:
                extra = cost - reserved
                evidence['overrun_nusd'] = extra
                if self.wallet_committed_nusd() - reserved + cost > self.wallet_cap_nusd():
                    self.db.execute("UPDATE experiments SET status = 'paused' WHERE experiment_id = ?",
                                    (self.experiment_id,))
                    evidence['paused'] = True
            self._event(attempt_id, 'settle', cost, evidence)
            self.db.execute(
                'UPDATE attempts SET status = ?, ended_at_utc = ?, latency_ms = ?, provider_request_id = ?,'
                ' model_resolved = ?, response_path = ?, raw_usage_json = ?, input_tokens = ?, output_tokens = ?,'
                ' known_cost_nusd = ? WHERE attempt_id = ?',
                (status, now_utc(), latency_ms, provider_request_id, model_resolved, response_path,
                 json.dumps(usage, ensure_ascii=False) if usage is not None else None, input_tokens, output_tokens,
                 cost if source in ('usage_priced', 'provider_reported') else None, attempt_id),
            )
            self.db.execute('UPDATE attempt_budget SET settled_nusd = ?, cost_source = ? WHERE attempt_id = ?',
                            (cost, source, attempt_id))
        return {'attempt_id': attempt_id, 'settled_nusd': cost, 'cost_source': source}

    def retry_of(self, attempt_id, **kwargs):
        """Retry e uma tentativa nova, com reserva propria e pai declarado."""
        row = self.db.execute('SELECT arm_id, block_id FROM attempts WHERE attempt_id = ?', (attempt_id,)).fetchone()
        if not row:
            raise LedgerStateError('Tentativa pai inexistente')
        kwargs.setdefault('arm_id', row['arm_id'])
        kwargs.setdefault('block_id', row['block_id'])
        return self.reserve(parent_attempt_id=attempt_id, **kwargs)

    # --- conciliacao ----------------------------------------------------
    def reconcile(self, provider, observed_usage_nusd, sanitized, key_limit_nusd=None):
        """Registra o extrato do provedor como delta sobre o ultimo snapshot, sem contar duas vezes."""
        blob = json.dumps(sanitized, ensure_ascii=False, sort_keys=True)
        previous = self.db.execute(
            'SELECT usage_nusd FROM provider_snapshots WHERE provider = ?'
            ' ORDER BY captured_at_utc DESC, rowid DESC LIMIT 1',
            (provider,),
        ).fetchone()
        base = int(previous['usage_nusd']) if previous and previous['usage_nusd'] is not None else 0
        delta = int(observed_usage_nusd) - base
        # Se o extrato do provedor ja passou do que o ledger registra, a diferenca e gasto
        # real fora do nosso controle e precisa ocupar o teto agora, senao autorizamos
        # chamadas contra saldo que nao existe mais.
        registrado = self.wallet_committed_nusd()
        excedente = int(observed_usage_nusd) - registrado
        with self._tx():
            self.db.execute(
                'INSERT INTO provider_snapshots(snapshot_id,provider,captured_at_utc,usage_nusd,key_limit_nusd,'
                'sanitized_json,sha256) VALUES(?,?,?,?,?,?,?)',
                (str(uuid.uuid4()), provider, now_utc(), int(observed_usage_nusd), key_limit_nusd, blob,
                 hashlib.sha256(blob.encode('utf-8')).hexdigest()),
            )
            self._event(None, 'reconcile', max(delta, 0), {
                'provider': provider, 'delta_nusd': delta, 'baseline_nusd': base,
                'wallet_committed_nusd': registrado, 'excedente_nao_registrado_nusd': excedente,
            })
            if excedente > 0:
                self.db.execute(
                    'INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,'
                    'settled_nusd,cost_source,priced_provider,priced_model) VALUES(?,?,?,?,?,?,?,?)',
                    (f'extrato:{uuid.uuid4()}', self.experiment_id, 'conciliacao', excedente,
                     excedente, 'provider_statement_excess', provider, None),
                )
                self._event(None, 'historical_commitment', excedente, {
                    'motivo': 'extrato do provedor acima do ledger; diferenca passa a ocupar o teto',
                    'provider': provider})
        return {'delta_nusd': delta, 'excedente_absorvido_nusd': max(excedente, 0),
                'ledger_committed_nusd': self.wallet_committed_nusd()}

    def record_historical_commitment(self, amount_nusd, evidence):
        """Gasto historico que ocupa o teto total sem ter tentativa nesta base."""
        with self._tx():
            self._event(None, 'historical_commitment', int(amount_nusd), evidence)
            self.db.execute(
                'INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,settled_nusd,cost_source)'
                ' VALUES(?,?,?,?,?,?)',
                (f'historical:{uuid.uuid4()}', self.experiment_id, 'historical', int(amount_nusd),
                 int(amount_nusd), 'historical'),
            )
        return int(amount_nusd)

    # --- internos -------------------------------------------------------
    def _require_status(self, attempt_id, allowed):
        row = self.db.execute(
            'SELECT a.status AS status, b.reserved_nusd AS reserved_nusd, b.settled_nusd AS settled_nusd,'
            ' b.priced_provider AS priced_provider, b.priced_model AS priced_model'
            ' FROM attempts a JOIN attempt_budget b ON b.attempt_id = a.attempt_id WHERE a.attempt_id = ?',
            (attempt_id,),
        ).fetchone()
        if row is None:
            raise LedgerStateError('Tentativa sem reserva registrada')
        if row['settled_nusd'] is not None:
            raise LedgerStateError('Tentativa ja liquidada')
        if row['status'] not in allowed:
            raise LedgerStateError(f'Transicao invalida a partir de {row["status"]}')
        return row

    def _event(self, attempt_id, event_type, amount_nusd, evidence):
        self.db.execute(
            'INSERT INTO budget_events(event_id,experiment_id,attempt_id,created_at_utc,event_type,amount_nusd,'
            'evidence_json,parent_event_id) VALUES(?,?,?,?,?,?,?,NULL)',
            (str(uuid.uuid4()), self.experiment_id, attempt_id, now_utc(), event_type, int(amount_nusd),
             json.dumps(evidence, ensure_ascii=False)),
        )

    def _tx(self, immediate=False):
        return _Transaction(self.db, immediate)


class _Transaction:
    def __init__(self, db, immediate):
        self.db = db
        self.immediate = immediate

    def __enter__(self):
        self.db.execute('BEGIN IMMEDIATE' if self.immediate else 'BEGIN')
        return self.db

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.db.execute('ROLLBACK')
        else:
            self.db.execute('COMMIT')
        return False
