"""Reviewed epoch-cursor earnings, not a migration codec or trusted total cache.

One cumulative exact replay is restored at an operating full-block cursor. Older
local histories remain separate payout books; later handoffs/events stay raw.
Every request still authenticates the complete configured lineage on chain.
"""
from collections import defaultdict
import hashlib
import json
from types import MappingProxyType, SimpleNamespace

from frontend_api.earnings_checkpoint import (Checkpoint, MAX_BYTES, SHARED, Seed,
    decode, encode, identity, source_identity)
from frontend_api.earnings_replay import COLLECTION, require, royalty_profile
from frontend_api.history import HistorySnapshot, _stored_json, _hash
from zzz_ops.work_budget import checkpoint

SOURCES = ('frontend_api/earnings_checkpoint_v3.py', 'frontend_api/lineage.py')
STATE_FIELDS = {'cursor', 'active', 'completed'}


class _Standalone:
    """Static codec view only; never mutate or replace a live Projection."""
    lineage = None

    def __init__(self, projection):
        self._projection = projection

    def __getattr__(self, name):
        return getattr(self._projection, name)


def view(engine, peer):
    return SimpleNamespace(p=_Standalone(peer), profiles=engine.profiles,
                           descriptors=engine.descriptors)


def peers(engine):
    p = engine.p
    require(p.lineage is not None, 'Checkpoint3 requires the complete configured lineage')
    result = [e.projection for e in p.lineage.entries] + [p]
    require(2 <= len(result) <= 9 and all(q.accounting_version == 7 and
            q.custody_version == 5 and q.fee_intake_version == 1 and
            royalty_profile(q) == 4 for q in result),
            'Checkpoint3 requires exact accounting7/custody5/royalty4 throughout')
    return result


def sources():
    from frontend_api.earnings_checkpoint import ROOT
    return {**source_identity(2), **{n: hashlib.sha256((ROOT/n).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                                  for n in SOURCES}}


def graph_identity(engine):
    result = []
    for index, peer in enumerate(peers(engine)):
        result.append(dict(deployment=identity(view(engine, peer)),
            mint_integration_version=peer.mint_integration_version,
            execution_price_version=peer.execution_price_version,
            retirement_transaction_hash=(engine.p.lineage.entries[index].transaction
                                         if index < len(engine.p.lineage.entries) else None)))
    return result


def _bind_graph(bound, engine):
    current = graph_identity(engine)
    require(isinstance(bound, list) and len(bound) == len(current), 'Checkpoint lineage graph differs')
    for index, (saved, actual) in enumerate(zip(bound, current)):
        require(isinstance(saved, dict) and set(saved) == set(actual) and
                isinstance(saved.get('deployment'), dict), 'Invalid checkpoint epoch identity')
        # Only the current epoch may acquire new reviewed asset descriptors.
        # Existing meanings, every retired epoch and all other fields are exact.
        prior = dict(saved['deployment']); latest = dict(actual['deployment'])
        assets = prior.pop('assets'); new_assets = latest.pop('assets')
        require(encode(prior) == encode(latest) and isinstance(assets, dict) and
                (encode(assets) == encode(new_assets) if index < len(current)-1 else
                 all(encode(new_assets.get(a)) == encode(d) for a, d in assets.items())) and
                all(encode(saved[k]) == encode(actual[k]) for k in actual if k != 'deployment'),
                'Checkpoint deployment order/profile/source identities changed')


def _header(anchor, peer):
    require(isinstance(anchor, dict) and set(anchor) == {'number', 'hash', 'timestamp'} and
            type(anchor['number']) is int and peer.history.start <= anchor['number'] < 1 << 63 and
            type(anchor['timestamp']) is int and 0 <= anchor['timestamp'] < 1 << 63,
            'Invalid checkpoint epoch anchor')
    _hash(anchor['hash'])


def history_data(history):
    return dict(owners=dict(history.owners), claims=dict(history.claims),
        conversions={k: (*v[:3], dict(v[3])) for k, v in history.conversions.items()},
        lp_conversions={k: (*v[:3], dict(v[3])) for k, v in history.lp_conversions.items()},
        provenance=dict(history.provenance))


def history_object(data):
    return HistorySnapshot(MappingProxyType(data['owners']), MappingProxyType(data['claims']),
        MappingProxyType(data['provenance']), MappingProxyType(data['conversions']),
        MappingProxyType(data['lp_conversions']))


def capture_payload(model, emitters, lp, royalties, history):
    from frontend_api.earnings_checkpoint_v2 import _capture_epoch
    return dict(shared={name: getattr(model, name) for name in SHARED},
        accounts=model.accounts, collection={k: v for k, v in model.totals.items() if k[0] in COLLECTION},
        emitters=emitters, lp_assets=sorted(lp), royalty_assets=sorted(royalties),
        history=history_data(history), exact_lp=_capture_epoch(model))


def combine_histories(histories):
    """Each local epoch contributes paid/conversion amounts once, never income."""
    claims = defaultdict(lambda: [0, 0]); conversions = {}; lp_conversions = {}
    for history in histories:
        for key, amounts in history.claims.items():
            checkpoint()
            claims[key][0] += amounts[0]; claims[key][1] += amounts[1]
        for target, rows in ((conversions, history.conversions), (lp_conversions, history.lp_conversions)):
            for key, row in rows.items():
                checkpoint()
                old = target.get(key)
                if old is None:
                    target[key] = row
                else:
                    last = max((old[3], row[3]), key=lambda x: (x['block_number'], x['log_index']))
                    target[key] = tuple(old[n] + row[n] for n in range(3)) + (last,)
    last = histories[-1]
    return HistorySnapshot(last.owners, MappingProxyType({k: tuple(v) for k, v in claims.items()}),
        last.provenance, MappingProxyType(conversions), MappingProxyType(lp_conversions))


class LineageCheckpoint:
    lineage_checkpoint = True

    def __init__(self, config, engine):
        from pathlib import Path
        import re
        require(isinstance(config, dict) and set(config) == {'path', 'sha256'} and
                isinstance(config['path'], str) and config['path'] and
                isinstance(config['sha256'], str) and re.fullmatch('[0-9a-f]{64}', config['sha256']),
                'Invalid reviewed earnings checkpoint configuration')
        self.digest = config['sha256']; self.engine = engine; self.peers = peers(engine)
        try:
            with Path(config['path']).open('rb') as f:
                raw = f.read(MAX_BYTES + 1)
            require(len(raw) <= MAX_BYTES and hashlib.sha256(raw).hexdigest() == self.digest,
                    'Earnings checkpoint bytes differ from the reviewed configuration pin')
            data = _stored_json(raw.decode('utf-8'))
            require(isinstance(data, dict) and set(data) == {'schema', 'sources', 'identity', 'anchor', 'state', 'previous_sha256'} and
                    type(data['schema']) is int and data['schema'] == 3,
                    'Checkpoint3 is required for predecessor lineage; historical schemas cannot be reinterpreted')
            require(data['sources'] == sources(), 'Earnings checkpoint semantic source changed')
            bound = decode(data['identity']); _bind_graph(bound, engine)
            anchor = decode(data['anchor']); state = decode(data['state'])
            require(isinstance(state, dict) and set(state) == STATE_FIELDS and type(state['cursor']) is int and
                    0 <= state['cursor'] < len(self.peers), 'Invalid checkpoint epoch cursor')
            index = state['cursor']; peer = self.peers[index]
            _header(anchor, peer)
            require(peer.start <= anchor['number'], 'Checkpoint cursor precedes the reviewed deployment anchor')
            require(isinstance(state['completed'], list) and len(state['completed']) == index,
                    'Checkpoint omits completed predecessor histories')
            Checkpoint._validate(state['active'], anchor, view(engine, peer))
            from frontend_api.earnings_checkpoint import validate_history_payload
            previous = None
            for n, item in enumerate(state['completed']):
                checkpoint()
                q = self.peers[n]
                require(isinstance(item, dict) and set(item) == {'anchor', 'history', 'lp_assets', 'royalty_assets'},
                        'Invalid completed checkpoint epoch')
                _header(item['anchor'], q)
                require(item['anchor']['number'] <= anchor['number'] and
                        item['anchor']['timestamp'] <= anchor['timestamp'] and
                        (previous is None or previous <= item['anchor']['number']),
                        'Checkpoint completed epoch chronology differs')
                previous = item['anchor']['number']
                require(isinstance(item['history'], dict) and isinstance(item['history'].get('owners'), dict),
                        'Incomplete checkpoint local history')
                ids = list(item['history']['owners'])
                require(len(ids) <= 1000 and all(type(i) is int and 0 < i < 1 << 256 for i in ids),
                        'Invalid checkpoint completed NFT inventory')
                validate_history_payload(item['history'], item['anchor'], view(engine, q), ids)
                for field, maximum in (('lp_assets', 2), ('royalty_assets', 65)):
                    assets = item[field]
                    require(isinstance(assets, list) and len(assets) <= maximum and len(set(assets)) == len(assets) and
                            all(a in q.assets for a in assets), 'Invalid checkpoint completed currency inventory')
                require(item['lp_assets'] == state['active']['lp_assets'] and
                        '0x'+'0'*40 in item['royalty_assets'], 'Checkpoint exact currency identity differs')
                for (_, asset), amounts in item['history']['claims'].items():
                    require((not amounts[0] or asset in item['lp_assets']) and
                            (not amounts[1] or asset in item['royalty_assets']),
                            'Checkpoint completed claim currency was not admitted to its ledger')
                for field, admitted in (('lp_conversions', item['lp_assets']), ('conversions', item['royalty_assets'])):
                    require(all(asset in admitted for _, asset in item['history'][field]),
                            'Checkpoint completed conversion currency was not admitted to its ledger')
            prior = data['previous_sha256']
            require(prior is None or isinstance(prior, str) and re.fullmatch('[0-9a-f]{64}', prior),
                    'Invalid previous checkpoint identity')
            self._raw = raw; self.anchor = MappingProxyType(anchor); self.cursor = index
            # Immutable section bytes, not shared mutable replay maps. Ordinary
            # history reads need only one local payout book, never all LP trees.
            dump = lambda value: json.dumps(encode(value), separators=(',', ':'), allow_nan=False).encode('utf-8')
            self._active = dump(state['active'])
            local = state['completed'] + [{k: state['active'][k] for k in
                                         ('history', 'lp_assets', 'royalty_assets')}]
            self._local = tuple(dump(item) for item in local)
            self._bounds = tuple(dump({'chain': row['deployment']['chain'],
                                      'history': row['deployment']['history']}) for row in bound[:index+1])
            self._completed_anchors = tuple(MappingProxyType(dict(item['anchor'])) for item in state['completed'])
        except (OSError, UnicodeError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
            from frontend_api.history import HistoryError
            raise HistoryError('Lineage earnings checkpoint is unavailable or malformed') from None

    @staticmethod
    def _section(raw):
        return decode(_stored_json(raw.decode('utf-8')))

    def check_anchor(self, current):
        require(current is self.engine.p, 'Checkpoint consumer deployment changed')
        require(self.peers[self.cursor]._header(hex(self.anchor['number'])) == dict(self.anchor),
                'Earnings checkpoint anchor is no longer canonical; preserve evidence and rebuild')

    def replay_start(self, epochs):
        require(len(epochs) == len(self.peers) and all(row[0] is p for row, p in zip(epochs, self.peers)),
                'Checkpoint authenticated epoch graph differs')
        for index, (peer, cutoff, incoming) in enumerate(epochs):
            if index < self.cursor:
                require(cutoff == self._completed_anchors[index], 'Checkpoint retirement anchor differs')
            elif index == self.cursor:
                require(self.anchor['number'] <= cutoff['number'] and self.anchor['timestamp'] <= cutoff['timestamp'] and
                        (incoming is None or incoming[0] <= self.anchor['number']) and
                        (index == len(epochs)-1 or self.anchor['number'] < cutoff['number']),
                        'Checkpoint cursor is outside its operating epoch')
        self.check_anchor(self.engine.p)
        return self.cursor

    def snapshot(self, p, header, block, lp, royalties, **kwargs):
        require(p in self.peers, 'Checkpoint history consumer is outside the reviewed graph')
        index = self.peers.index(p)
        if index > self.cursor:
            return p._history_snapshot(header, block, lp, royalties, **kwargs)
        local_bound = self._section(self._bounds[index])
        item = self._section(self._local[index])
        if index < self.cursor:
            require(kwargs.get('consumer') is None, 'Completed checkpoint epochs cannot restore earnings twice')
            require(header == item['anchor'], 'Checkpoint retired cutoff differs from the authenticated handoff')
            payload = {k: item[k] for k in ('lp_assets', 'royalty_assets')}
            history = history_object(item['history']); anchor = item['anchor']
        else:
            payload = (self._section(self._active) if kwargs.get('consumer') is not None else
                       {k: item[k] for k in ('lp_assets', 'royalty_assets')})
            history = history_object(item['history']); anchor = dict(self.anchor)
            require(header['number'] >= anchor['number'], 'Requested history precedes checkpoint')
        kwargs['seed'] = Seed(self.digest, anchor, local_bound, payload, history, 2)
        return p._history_snapshot(header, block, lp, royalties, **kwargs)


def build(engine, number):
    """Build one same-graph cursor; actual publication remains exclusive/reviewed."""
    from frontend_api.earnings_checkpoint_build import confirmed_head, reconcile_accounts
    from frontend_api.earnings_exact_lp import ExactReplay
    all_peers = peers(engine); p = engine.p
    require(type(number) is int and all_peers[0].history.start <= number < 1 << 63, 'Invalid checkpoint block')
    bound = graph_identity(engine); pinned_sources = sources()
    safe = confirmed_head(p); at_safe = {'blockHash': safe['hash'], 'requireCanonical': True}
    life = p._verify_deployment(at_safe)
    epochs, proofs = p.lineage.verify(p, safe, at_safe, life)
    require(number <= safe['number'], 'Checkpoint block is not confirmed')
    index = max(n for n, (_, _, lower) in enumerate(epochs) if lower is None or lower[0] <= number)
    peer = all_peers[index]; anchor = p._header(hex(number)); at = {'blockHash': anchor['hash'], 'requireCanonical': True}
    require(peer.start <= number, 'Checkpoint cursor precedes its deployment')
    cursor_life = peer._verify_deployment(at)
    require(cursor_life['state'] == 'operating' and not cursor_life['preparation_active'],
            'Checkpoint cursor requires an operating, settled epoch')
    require((index == 0 and cursor_life['predecessor_controller'] is None) or
            (index > 0 and cursor_life['predecessor_controller'] == all_peers[index-1].contracts['access'].address),
            'Checkpoint cursor predecessor differs from authenticated lineage')
    start = engine.replay_start(epochs)
    require(start <= index, 'Checkpoint cannot move before its reviewed cursor')
    if engine.checkpoint is not None:
        require(engine.checkpoint.anchor['number'] <= number, 'Checkpoint cannot move before its reviewed anchor')
    model = ExactReplay(anchor['timestamp'], track_all=True)
    histories = []; completed = []; active = None
    for n, (q, cutoff, incoming) in enumerate(epochs[:index+1]):
        checkpoint()
        cutoff = anchor if n == index else cutoff
        block = {'blockHash': cutoff['hash'], 'requireCanonical': True}
        lp, royalties = q._admitted(block, historical_descriptors=True); emitters = engine.check_profile(q, block)
        if n >= start:
            model.begin(emitters, lp, royalties, None if n == start and engine.checkpoint is not None else incoming,
                        fee_intake_version=1, royalty_settlement_version=4)
            history = engine.history_snapshot(q, cutoff, block, lp, royalties, consumer=model,
                                              extra_emitters=tuple(emitters.values()))
            model.finish(); engine.reconcile(q, model, block, lp, royalties, history.provenance['minted_count'])
            histories.append(history)
            if n == index:
                # Retired royalty books deliberately retain accounting after
                # sending their backing; live pending/claimable views may revert.
                # Reconcile lifetime paid amounts against the OPERATING cursor.
                reconcile_accounts(engine, q, model, block, lp, royalties, history,
                                   paid_history=combine_histories(histories))
        else:
            history = engine.history_snapshot(q, cutoff, block, lp, royalties)
            histories.append(history)
        if n < index:
            completed.append(dict(anchor=cutoff, history=history_data(history),
                                  lp_assets=sorted(lp), royalty_assets=sorted(royalties)))
        else:
            active = capture_payload(model, emitters, lp, royalties, history)
            Checkpoint._validate(active, anchor, view(engine, q))
    require(p._header(hex(number)) == anchor, 'Checkpoint anchor changed during construction')
    final = confirmed_head(p)
    require(safe['number'] <= final['number'], 'Checkpoint graph confirmation depth retreated')
    again_life = p._verify_deployment(at_safe)
    again_epochs, again_proofs = p.lineage.verify(p, safe, at_safe, again_life)
    require(epochs == again_epochs and proofs == again_proofs, 'Checkpoint handoff graph changed during construction')
    engine.finish_checkpoint()
    require(sources() == pinned_sources and encode(graph_identity(engine)) == encode(bound),
            'Checkpoint semantic source or graph changed during construction')
    state = encode(dict(cursor=index, active=active, completed=completed))
    # Enforce the same aggregate tagged node/depth bounds before any file write.
    decode(state)
    data = dict(schema=3, sources=pinned_sources, identity=encode(bound), anchor=encode(anchor), state=state,
                previous_sha256=None if engine.checkpoint is None else engine.checkpoint.digest)
    raw = (json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')
    require(len(raw) <= MAX_BYTES, 'Checkpoint exceeds the reviewed artifact size bound')
    return raw
