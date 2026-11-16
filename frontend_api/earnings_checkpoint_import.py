"""Explicit offline prefix import; no consumer pin override or live adoption.

Existing readers/builders remain byte-identical. A private adapter supplies a
strictly validated old prefix to the ordinary full-graph checkpoint3 builder.
The separate review attests this producer, not a new consumer semantic version.
"""
import hashlib
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace

from frontend_api.earnings_checkpoint import Checkpoint, MAX_BYTES, decode, encode, source_identity
from frontend_api.earnings_checkpoint_build import BuildBudget, publish_candidate
from frontend_api.earnings_checkpoint_v3 import LineageCheckpoint, graph_identity, peers, sources
from frontend_api.history import _stored_json
from frontend_api.earnings_replay import require
from zzz_ops.work_budget import checkpoint, request_scope

ROOT = Path(__file__).resolve().parents[1]
PRODUCER_FILES = ('frontend_api/earnings_checkpoint_import.py', 'scripts/import-earnings-checkpoint.py')
MAX_REVIEW_BYTES = 1024 * 1024
REVIEW_FIELDS = frozenset(('schema', 'kind', 'production_approved', 'approved', 'installed',
    'ready_for_submission', 'transactions_submitted', 'prefix_sha256', 'prefix_schema',
    'prefix_graph_length', 'target_graph_length', 'imported_cursor', 'input_anchor', 'target_anchor',
    'checkpoint_sha256', 'input_semantic_sources', 'output_semantic_sources', 'producer_sources',
    'target_configuration_sha256', 'target_graph', 'authenticated_graph_snapshot', 'appended_handoffs',
    'earliest_served_timestamp', 'raw_retention_required', 'trust', 'adoption'))


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')


def producer_sources():
    return {n: _digest((ROOT/n).read_bytes().replace(b'\r\n', b'\n')) for n in PRODUCER_FILES}


def _read_prefix(config):
    require(isinstance(config, dict) and set(config) == {'path', 'sha256'} and
            isinstance(config['path'], str) and config['path'] and
            isinstance(config['sha256'], str) and re.fullmatch('[0-9a-f]{64}', config['sha256']),
            'Invalid reviewed prefix configuration')
    checkpoint()
    path = Path(config['path'])
    require(path.is_file(), 'Reviewed prefix must be an existing regular file')
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES+1)
    require(len(raw) <= MAX_BYTES and _digest(raw) == config['sha256'],
            'Reviewed prefix bytes or digest differ')
    data = _stored_json(raw.decode('utf-8'))
    require(isinstance(data, dict) and type(data.get('schema')) is int and data['schema'] in (2, 3),
            'Only exact-accounting checkpoint2 or checkpoint3 can be imported')
    checkpoint()
    return raw, data


class _ProjectionView:
    """Pure old-graph decoder view; no installed Projection is edited."""
    def __init__(self, projection, lineage):
        self._projection = projection
        self.lineage = lineage

    def __getattr__(self, name):
        return getattr(self._projection, name)


def _old_engine(engine, full, length):
    tail = full[length-1]
    lineage = (None if length == 1 else
               SimpleNamespace(entries=engine.p.lineage.entries[:length-1]))
    p = _ProjectionView(tail, lineage)
    descriptors = dict(tail.assets)
    for q in full[:length]:
        for asset, descriptor in q.assets.items():
            descriptors.setdefault(asset, descriptor)
    return SimpleNamespace(p=p, profiles=engine.profiles, descriptors=descriptors)


class _ImportedPrefix:
    """Build-local seed capability; never installed on the original engine."""
    def __init__(self, engine, config, raw, data):
        self.engine = engine; self.full = peers(engine); self.schema = data['schema']
        require(engine.checkpoint is None, 'Target engine must not install a competing checkpoint')
        if self.schema == 2:
            length = 1
        else:
            bound = decode(data['identity'])
            require(isinstance(bound, list) and 2 <= len(bound) < len(self.full),
                    'Imported lineage must be a strictly shorter ordered graph')
            length = len(bound)
        require(length < len(self.full), 'Prefix must precede a new authenticated replacement')
        self.length = length; self.old_engine = _old_engine(engine, self.full, length)
        self.original = (Checkpoint(config, self.old_engine) if self.schema == 2 else
                         LineageCheckpoint(config, self.old_engine))
        # Both strict loaders reread the path and require the same externally
        # supplied digest and exact installed semantic sources. No old hash map
        # or caller-provided source migration is accepted.
        require(self.original._raw == raw, 'Reviewed prefix changed while loading')
        self.cursor = 0 if self.schema == 2 else self.original.cursor
        self.digest = self.original.digest; self.anchor = self.original.anchor
        require(self.full[self.cursor].start <= self.anchor['number'],
                'Imported cursor precedes its reviewed deployment anchor')
        self.verified_epochs = None; self.appended = None
        if self.schema == 2:
            self.pair = tuple(self.original.seed().payload['lp_assets'])
        else:
            self.pair = tuple(self.original._section(self.original._active)['lp_assets'])

    def check_anchor(self, current):
        require(current is self.engine.p, 'Offline import target engine changed')
        self.original.check_anchor(self.old_engine.p)

    def replay_start(self, epochs):
        require(len(epochs) == len(self.full) and all(row[0] is p for row, p in zip(epochs, self.full)),
                'Imported prefix authenticated graph differs')
        q, retirement, incoming = epochs[self.cursor]
        # Even the old graph's then-current tail is now a retired predecessor.
        # Its full retirement block cannot be an operating saved cursor.
        require(self.cursor < len(epochs)-1 and self.anchor['number'] < retirement['number'] and
                self.anchor['timestamp'] <= retirement['timestamp'] and
                (incoming is None or incoming[0] <= self.anchor['number']),
                'Imported cursor lies outside its authenticated operating epoch')
        if self.schema == 3:
            mapped = [(p, cutoff, lower) for p, (_, cutoff, lower) in
                      zip(self.original.peers, epochs[:self.length])]
            require(self.original.replay_start(mapped) == self.cursor, 'Imported cursor mapping differs')
        self.check_anchor(self.engine.p)
        at = {'blockHash': self.anchor['hash'], 'requireCanonical': True}
        life = q._verify_deployment(at)
        origin = {'chain_id': self.engine.p.chain, 'vault': self.full[0].contracts['vault'].address}
        require(life['state'] == 'operating' and not life['preparation_active'] and life['origin'] == origin and
                life['predecessor_controller'] == (None if self.cursor == 0 else self.full[self.cursor-1].contracts['access'].address),
                'Imported cursor was not the settled original-identity operating epoch')
        # Candidate construction may intentionally end before the new handoff.
        # Still prove every later deployment uses the same native/fixed-ZZZ book.
        for peer, cutoff, _ in epochs:
            checkpoint()
            lp, _ = peer._admitted({'blockHash': cutoff['hash'], 'requireCanonical': True})
            require(tuple(lp) == self.pair, 'Imported principal currencies differ in the target graph')
        appended = []
        for n in range(self.length-1, len(epochs)-1):
            source, cutoff, _ = epochs[n]; destination, _, activation = epochs[n+1]
            require(activation is not None and activation[0] == cutoff['number'] and
                    activation[1] == self.engine.p.lineage.entries[n].transaction,
                    'Appended handoff boundary differs from the verified graph')
            appended.append(dict(source_controller=source.contracts['access'].address,
                destination_controller=destination.contracts['access'].address,
                retirement_transaction_hash=activation[1], block_number=cutoff['number'],
                block_hash=cutoff['hash'], timestamp=cutoff['timestamp'], handoff_id=activation[2], state_root=activation[3]))
        self.verified_epochs = epochs
        self.appended = appended
        return self.cursor

    def snapshot(self, p, header, block, lp, royalties, **kwargs):
        require(p in self.full, 'Offline prefix consumer is outside the authenticated graph')
        index = self.full.index(p)
        if self.schema == 2 and index == 0:
            self.check_anchor(self.engine.p)
            kwargs['seed'] = self.original.seed()
            return p._history_snapshot(header, block, lp, royalties, **kwargs)
        if self.schema == 3 and index < self.length:
            return self.original.snapshot(self.original.peers[index], header, block, lp, royalties, **kwargs)
        return p._history_snapshot(header, block, lp, royalties, **kwargs)


class _BuildEngine:
    def __init__(self, engine, imported):
        self._engine = engine; self.checkpoint = imported

    def __getattr__(self, name):
        return getattr(self._engine, name)

    def replay_start(self, epochs):
        return self.checkpoint.replay_start(epochs)

    def history_snapshot(self, p, header, block, lp, royalties, **kwargs):
        return self.checkpoint.snapshot(p, header, block, lp, royalties, **kwargs)

    def finish_checkpoint(self):
        self.checkpoint.check_anchor(self.p)


def prepare(engine, number, prefix_config, *, budget=None):
    """Return a NEW standard3 candidate and producer review; never approve them."""
    from frontend_api.earnings_checkpoint_v3 import build
    with request_scope(budget or BuildBudget()):
        require(engine.checkpoint is None, 'Target configuration must not install a checkpoint')
        producer = producer_sources(); semantic = sources(); graph = graph_identity(engine)
        raw_prefix, document = _read_prefix(prefix_config)
        imported = _ImportedPrefix(engine, prefix_config, raw_prefix, document)
        wrapper = _BuildEngine(engine, imported)
        raw = build(wrapper, number)
        require(imported.verified_epochs is not None and imported.appended,
                'Import did not authenticate an appended handoff')
        result = _stored_json(raw.decode('utf-8')); digest = _digest(raw)
        require(result['previous_sha256'] == imported.digest and result['sources'] == semantic,
                'Imported candidate lost prefix or semantic provenance')
        # Strict output-consumer admission before publication; this is an owned
        # temporary file only, never a service configuration or deployed state.
        with tempfile.TemporaryDirectory(prefix='popl-checkpoint-import-') as temporary:
            candidate = Path(temporary)/'candidate.json'; candidate.write_bytes(raw)
            admitted = LineageCheckpoint({'path': str(candidate), 'sha256': digest}, engine)
            admitted.replay_start(imported.verified_epochs)
            admitted.check_anchor(engine.p)
        current_prefix, _ = _read_prefix(prefix_config)
        require(current_prefix == raw_prefix and producer_sources() == producer and sources() == semantic and
                encode(graph_identity(engine)) == encode(graph),
                'Import source, prefix or target graph changed during preparation')
        review = dict(schema=1, kind='popl-offline-checkpoint-prefix-import', production_approved=False,
            approved=False, installed=False, ready_for_submission=False, transactions_submitted=False,
            prefix_sha256=imported.digest, prefix_schema=imported.schema, prefix_graph_length=imported.length,
            target_graph_length=len(imported.full), imported_cursor=imported.cursor,
            input_anchor=dict(imported.anchor), target_anchor=decode(result['anchor']),
            checkpoint_sha256=digest, input_semantic_sources=document['sources'], output_semantic_sources=semantic,
            producer_sources=producer, target_configuration_sha256=engine.p.identity, target_graph=graph,
            authenticated_graph_snapshot=imported.verified_epochs[-1][1], appended_handoffs=imported.appended,
            earliest_served_timestamp=decode(result['anchor'])['timestamp']+86400,
            raw_retention_required=True,
            trust='Explicit operator-reviewed prefix digest and canonical RPC/history checks; not log-completeness or consensus proof.',
            adoption='Independently review candidate and producer manifest; no automatic approval, pin, pruning or restart.')
        review_raw = _canonical(review)
        require(len(review_raw) <= MAX_REVIEW_BYTES, 'Import review exceeds its bounded size')
        checkpoint()
        return raw, review_raw


def output_preflight(output_path, review_path, *, prefix_path=None):
    output, review = Path(output_path), Path(review_path)
    require(output.resolve() != review.resolve(), 'Candidate and review outputs must be distinct')
    if prefix_path is not None:
        prefix = Path(prefix_path).resolve()
        require(prefix not in (output.resolve(), review.resolve()), 'Import outputs must not alias the input prefix')
    for path in (output, review):
        require(path.parent.is_dir(), 'Import output parent directory must already exist')
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        raise FileExistsError('Import output already exists; it was not replaced')


def _review_header(value):
    require(isinstance(value, dict) and set(value) == {'number', 'hash', 'timestamp'} and
            all(type(value[k]) is int and 0 <= value[k] < 1 << 63 for k in ('number', 'timestamp')) and
            isinstance(value['hash'], str) and re.fullmatch('0x[0-9a-f]{64}', value['hash']),
            'Invalid import review anchor')


def _bind_review(result, review):
    """Bind sidecar claims to prepared bytes; this is not new RPC authentication."""
    require(set(review) == REVIEW_FIELDS and review['raw_retention_required'] is True and
            all(type(review[k]) is int for k in ('prefix_schema', 'prefix_graph_length',
                'target_graph_length', 'imported_cursor', 'earliest_served_timestamp')) and
            review['prefix_schema'] in (2, 3) and
            1 <= review['prefix_graph_length'] < review['target_graph_length'] <= 9 and
            (review['prefix_graph_length'] == 1) == (review['prefix_schema'] == 2) and
            0 <= review['imported_cursor'] < review['prefix_graph_length'] and
            all(isinstance(review[k], str) and re.fullmatch('[0-9a-f]{64}', review[k])
                for k in ('prefix_sha256', 'target_configuration_sha256')) and
            review['input_semantic_sources'] == (source_identity(2) if review['prefix_schema'] == 2 else sources()),
            'Invalid import review profile or prefix binding')
    require(set(result) == {'schema', 'sources', 'identity', 'anchor', 'state', 'previous_sha256'},
            'Invalid imported candidate envelope')
    graph = decode(result['identity']); anchor = decode(result['anchor'])
    require(isinstance(graph, list) and len(graph) == review['target_graph_length'] and
            encode(review['target_graph']) == encode(graph) and
            encode(review['target_anchor']) == encode(anchor),
            'Import review graph or target anchor differs from candidate')
    for header in (anchor, review['input_anchor'], review['authenticated_graph_snapshot']):
        _review_header(header)
    snapshot, initial = review['authenticated_graph_snapshot'], review['input_anchor']
    require(initial['number'] <= anchor['number'] <= snapshot['number'] and
            initial['timestamp'] <= anchor['timestamp'] <= snapshot['timestamp'] and
            review['earliest_served_timestamp'] == anchor['timestamp']+86400,
            'Import review retention or anchor ordering differs')
    proofs = review['appended_handoffs']
    require(isinstance(proofs, list) and len(proofs) == len(graph)-review['prefix_graph_length'],
            'Import review appended handoff count differs')
    prior_number, prior_time = initial['number'], initial['timestamp']
    for n, proof in enumerate(proofs, review['prefix_graph_length']-1):
        checkpoint()
        require(isinstance(proof, dict) and set(proof) == {'source_controller', 'destination_controller',
                'retirement_transaction_hash', 'block_number', 'block_hash', 'timestamp', 'handoff_id', 'state_root'} and
                all(isinstance(proof[k], str) and re.fullmatch('0x[0-9a-f]{64}', proof[k]) for k in
                    ('retirement_transaction_hash', 'block_hash', 'handoff_id', 'state_root')) and
                all(type(proof[k]) is int and 0 <= proof[k] < 1 << 63 for k in ('block_number', 'timestamp')) and
                proof['source_controller'] == graph[n]['deployment']['contracts']['access']['address'] and
                proof['destination_controller'] == graph[n+1]['deployment']['contracts']['access']['address'] and
                proof['retirement_transaction_hash'] == graph[n]['retirement_transaction_hash'] and
                prior_number <= proof['block_number'] <= snapshot['number'] and
                prior_time <= proof['timestamp'] <= snapshot['timestamp'],
                'Import review appended handoff identity or order differs')
        prior_number, prior_time = proof['block_number'], proof['timestamp']


def publish(output_path, review_path, raw, review_raw):
    """Exclusive files, not a two-file atomic transaction or approval mechanism.

    Review is published first. A later failure can leave an unapproved sidecar;
    preserve it and use fresh paths after inspection. Never delete another file.
    """
    output_preflight(output_path, review_path)
    require(isinstance(raw, bytes) and len(raw) <= MAX_BYTES and isinstance(review_raw, bytes) and
            len(review_raw) <= MAX_REVIEW_BYTES, 'Invalid import output sizes')
    result = _stored_json(raw.decode('utf-8')); review = _stored_json(review_raw.decode('utf-8'))
    require(_canonical(result) == raw and _canonical(review) == review_raw,
            'Imported outputs must retain their prepared canonical serialization')
    require(isinstance(review, dict) and type(review.get('schema')) is int and review['schema'] == 1 and
            review.get('kind') == 'popl-offline-checkpoint-prefix-import' and
            all(review.get(flag) is False for flag in ('production_approved', 'approved', 'installed', 'ready_for_submission', 'transactions_submitted')) and
            review.get('checkpoint_sha256') == _digest(raw) and review.get('producer_sources') == producer_sources() and
            review.get('output_semantic_sources') == sources(), 'Import review does not authenticate the outputs')
    require(isinstance(result, dict) and type(result.get('schema')) is int and result['schema'] == 3 and
            result.get('sources') == review['output_semantic_sources'] and
            result.get('previous_sha256') == review.get('prefix_sha256') and
            decode(result['anchor']) == review.get('target_anchor'), 'Import candidate identity differs from its review')
    _bind_review(result, review)
    checkpoint()
    publish_candidate(review_path, review_raw)
    checkpoint()
    publish_candidate(output_path, raw)
    checkpoint()
    return _digest(raw), _digest(review_raw)
