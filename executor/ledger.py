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
              priced_model TEXT,
              priced_snapshot_id TEXT
            );
            """
        )
        self._migrar()

    def _migrar(self):
        """Acrescenta colunas novas a bases criadas por versoes anteriores.

        CREATE TABLE IF NOT EXISTS nao altera tabela existente: sem isto, uma base antiga
        continuaria sem as colunas de identidade de preco e quebraria na primeira reserva.
        """
        existentes = {linha['name'] for linha in self.db.execute('PRAGMA table_info(attempt_budget)')}
        for coluna in ('priced_provider', 'priced_model', 'priced_snapshot_id'):
            if coluna not in existentes:
                self.db.execute(f'ALTER TABLE attempt_budget ADD COLUMN {coluna} TEXT')
        colunas_snapshot = {linha['name'] for linha in self.db.execute('PRAGMA table_info(provider_snapshots)')}
        for coluna in ('liquidado_no_instante_nusd', 'excedente_nusd'):
            if coluna not in colunas_snapshot:
                self.db.execute(f'ALTER TABLE provider_snapshots ADD COLUMN {coluna} INTEGER')
        # Versoes anteriores materializavam o ajuste de conciliacao como linha de gasto. Agora
        # o excedente e fato do snapshot: manter as linhas contaria o mesmo dinheiro duas vezes.
        antigas = self.db.execute(
            "SELECT attempt_id, settled_nusd FROM attempt_budget"
            " WHERE cost_source = 'provider_statement_excess'").fetchall()
        for antiga in antigas:
            self.db.execute('DELETE FROM attempt_budget WHERE attempt_id = ?', (antiga['attempt_id'],))
            self._event(None, 'reconcile', int(antiga['settled_nusd'] or 0), {
                'migracao': 'ajuste materializado removido; o excedente passou a ser fato do snapshot',
                'attempt_id': antiga['attempt_id']})

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
        """Tudo comprometido na base, somando TODOS os experimentos, mais o excedente de extrato.

        O teto autorizado e da carteira, nao de cada experimento: sem isso, abrir um
        experimento novo abriria um teto novo e o limite global seria ficcao. O excedente do
        extrato entra aqui como calculo, nao como linha: assim ele encolhe sozinho quando a
        cobranca correspondente passa a ser registrada como tentativa.
        """
        row = self.db.execute(
            'SELECT COALESCE(SUM(CASE WHEN settled_nusd IS NULL THEN reserved_nusd ELSE settled_nusd END),0) AS total'
            ' FROM attempt_budget'
        ).fetchone()
        return int(row['total']) + self.excedente_de_extrato_nusd()

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
            estado = self.db.execute(
                'SELECT status FROM experiments WHERE experiment_id = ?', (self.experiment_id,)).fetchone()
            if estado and estado['status'] == 'paused':
                raise BudgetError('Experimento pausado por estouro anterior; nenhuma reserva nova')
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
                'cost_source,priced_provider,priced_model,priced_snapshot_id)'
                ' VALUES(?,?,?,?,NULL,NULL,?,?,?)',
                (attempt_id, self.experiment_id, block_id, worst, provider, model,
                 snapshot_id(self.prices)),
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
            # A tarifa que vale e a da reserva. Com tabela de precos diferente, liquidar por
            # tokens usaria preco que nao foi o reservado, entao a reserva e conservada.
            snapshot_da_reserva = row['priced_snapshot_id']
            tarifa_compativel = snapshot_da_reserva == snapshot_id(self.prices)
            input_tokens = output_tokens = None
            if provider_reported_cost_nusd is not None:
                cost = int(provider_reported_cost_nusd)
                source = 'provider_reported'
            elif not tarifa_compativel:
                cost = reserved
                source = 'worst_case_price_snapshot_divergente'
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
            evidence = {'cost_source': source, 'reserved_nusd': reserved,
                        'priced_snapshot_id': snapshot_da_reserva}
            if cost > reserved:
                extra = cost - reserved
                evidence['overrun_nusd'] = extra
                # Estado RESULTANTE da liquidacao, na mesma transacao: o comprometido atual
                # ainda conta a reserva, que esta sendo substituida pelo custo real.
                resultante = self.wallet_committed_nusd() - reserved + cost
                if resultante > self.wallet_cap_nusd():
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
    def settled_nusd_total(self, provider=None):
        """Gasto JA LIQUIDADO. E esta a grandeza comparavel com o extrato do provedor.

        O extrato mostra o que foi cobrado; `wallet_committed_nusd` inclui reservas de
        chamadas que ainda nao aconteceram. Comparar os dois seria somar laranja com maca.
        """
        if provider is None:
            linha = self.db.execute(
                'SELECT COALESCE(SUM(settled_nusd),0) AS total FROM attempt_budget'
                ' WHERE settled_nusd IS NOT NULL').fetchone()
        else:
            linha = self.db.execute(
                'SELECT COALESCE(SUM(settled_nusd),0) AS total FROM attempt_budget'
                ' WHERE settled_nusd IS NOT NULL AND priced_provider = ?', (provider,)).fetchone()
        return int(linha['total'])

    def sem_identidade_nusd(self):
        """Liquidado que nao sabemos de qual provedor veio.

        Enquanto existir, nenhuma conciliacao por provedor e confiavel: o valor pode pertencer
        ao provedor conciliado e seria somado duas vezes.
        """
        linha = self.db.execute(
            'SELECT COALESCE(SUM(settled_nusd),0) AS total FROM attempt_budget'
            ' WHERE settled_nusd IS NOT NULL AND priced_provider IS NULL').fetchone()
        return int(linha['total'])

    def excedente_de_extrato_nusd(self):
        """Gasto que o provedor cobrou e o ledger nunca registrou.

        O excedente e ancorado no INSTANTE do snapshot: comparamos o extrato com o que estava
        liquidado naquele momento, e o resultado fica congelado. Calcular contra o liquidado
        de agora abriria um furo: uma chamada nova, feita depois do extrato, reduziria o
        excedente antigo ao ser liquidada e liberaria espaco no teto para gastar de novo o
        mesmo dinheiro. Mantemos o maior excedente ja observado por provedor, porque um
        extrato atrasado nao desfaz uma divergencia que ja foi vista.
        """
        linha = self.db.execute(
            'SELECT COALESCE(SUM(maior),0) AS total FROM ('
            '  SELECT provider, MAX(excedente_nusd) AS maior FROM provider_snapshots'
            '  WHERE excedente_nusd IS NOT NULL GROUP BY provider)').fetchone()
        return int(linha['total'])

    def reconcile(self, provider, observed_usage_nusd, sanitized, key_limit_nusd=None):
        """Grava o extrato do provedor. O excedente nao vira linha: vira conta.

        Comparamos o extrato com o LIQUIDADO daquele provedor, nunca com o total comprometido,
        que inclui reservas de chamadas que ainda nao aconteceram.
        """
        blob = json.dumps(sanitized, ensure_ascii=False, sort_keys=True)
        with self._tx(immediate=True):
            anterior = self.db.execute(
                'SELECT usage_nusd FROM provider_snapshots WHERE provider = ?'
                ' ORDER BY captured_at_utc DESC, rowid DESC LIMIT 1', (provider,)).fetchone()
            base = int(anterior['usage_nusd']) if anterior and anterior['usage_nusd'] is not None else 0
            delta = int(observed_usage_nusd) - base
            liquidado = self.settled_nusd_total(provider)
            excedente = max(int(observed_usage_nusd) - liquidado, 0)
            sem_identidade = self.sem_identidade_nusd()
            self.db.execute(
                'INSERT INTO provider_snapshots(snapshot_id,provider,captured_at_utc,usage_nusd,'
                'key_limit_nusd,sanitized_json,sha256,liquidado_no_instante_nusd,excedente_nusd)'
                ' VALUES(?,?,?,?,?,?,?,?,?)',
                (str(uuid.uuid4()), provider, now_utc(), int(observed_usage_nusd), key_limit_nusd,
                 blob, hashlib.sha256(blob.encode('utf-8')).hexdigest(), liquidado, excedente))
            self._event(None, 'reconcile', max(delta, 0), {
                'provider': provider, 'delta_nusd': delta, 'baseline_nusd': base,
                'extrato_nusd': int(observed_usage_nusd), 'liquidado_do_provedor_nusd': liquidado,
                'excedente_calculado_nusd': excedente,
                'liquidado_sem_identidade_nusd': sem_identidade,
            })
        return {'delta_nusd': delta, 'excedente_nusd': excedente,
                'liquidado_do_provedor_nusd': liquidado,
                'liquidado_sem_identidade_nusd': sem_identidade,
                'ledger_committed_nusd': self.wallet_committed_nusd()}

    def record_historical_commitment(self, amount_nusd, evidence, provider=None):
        """Gasto historico que ocupa o teto sem ter tentativa nesta base.

        O provedor e obrigatorio para que a conciliacao saiba que este gasto ja esta contado:
        sem ele, o extrato do provedor acharia que o valor nao foi registrado e o somaria de novo.
        """
        if not provider:
            raise LedgerStateError(
                'Compromisso historico exige provedor: sem ele a conciliacao contaria o gasto duas vezes')
        with self._tx():
            self._event(None, 'historical_commitment', int(amount_nusd),
                        {**evidence, 'provider': provider})
            self.db.execute(
                'INSERT INTO attempt_budget(attempt_id,experiment_id,block_id,reserved_nusd,'
                'settled_nusd,cost_source,priced_provider,priced_model,priced_snapshot_id)'
                ' VALUES(?,?,?,?,?,?,?,NULL,NULL)',
                (f'historical:{uuid.uuid4()}', self.experiment_id, 'historical', int(amount_nusd),
                 int(amount_nusd), 'historical', provider),
            )
        return int(amount_nusd)

    def regularizar_identidade(self, attempt_id, provider, model, motivo):
        """Da identidade de preco a uma tentativa herdada de base antiga.

        Sem isto, uma tentativa pendente migrada nunca poderia ser liquidada: settle() exige a
        identidade da reserva, e a migracao so cria a coluna vazia.

        A regularizacao NAO escolhe tarifa. O snapshot recebe um marcador proprio que nunca
        coincide com uma tabela de precos real, entao settle() cai no caminho conservador e
        liquida pelo pior caso reservado. Sem isso, bastaria declarar um modelo barato para
        liberar saldo de uma reserva antiga.
        """
        if not provider or not model:
            raise LedgerStateError('Regularizacao exige provedor e modelo declarados')
        with self._tx():
            linha = self.db.execute(
                'SELECT priced_provider, settled_nusd FROM attempt_budget WHERE attempt_id = ?',
                (attempt_id,)).fetchone()
            if linha is None:
                raise LedgerStateError('Tentativa inexistente')
            if linha['priced_provider'] is not None:
                raise LedgerStateError('Tentativa ja tem identidade de preco; regularizar apagaria evidencia')
            self.db.execute(
                'UPDATE attempt_budget SET priced_provider = ?, priced_model = ?, priced_snapshot_id = ?'
                ' WHERE attempt_id = ?', (provider, model, 'regularizado-sem-tarifa', attempt_id))
            self._event(attempt_id, 'reconcile', 0, {'regularizacao': motivo, 'provider': provider,
                                                     'model': model,
                                                     'efeito': 'liquidacao conservadora pelo pior caso'})
        return attempt_id

    # --- internos -------------------------------------------------------
    def _require_status(self, attempt_id, allowed):
        row = self.db.execute(
            'SELECT a.status AS status, b.reserved_nusd AS reserved_nusd, b.settled_nusd AS settled_nusd,'
            ' b.priced_provider AS priced_provider, b.priced_model AS priced_model,'
            ' b.priced_snapshot_id AS priced_snapshot_id'
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
