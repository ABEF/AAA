"""Explicit bounded wallet earnings: one currency axis, all original live proofs.

Ordinary ownership/summary pages remain16 IDs. Each aggregate response covers
at most four currencies and binds the complete current-owner inventory; the
client must still assemble and verify all independent ownership pages.
"""
import hashlib
from collections import defaultdict
from copy import deepcopy
from types import SimpleNamespace

from frontend_api.canonical_cache import scope
from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.earnings_prices import value_report
from frontend_api.earnings_replay import require, royalty_profile
from frontend_api.history import HistoryError, conversion_report, merge_conversions
from frontend_api.portfolio import CHUNK_SIZE
from frontend_api.read_batch import prefetch_accounts
from frontend_api.service import ProjectionError
from frontend_api.wallet_earnings import asset_page
from zzz_ops.abi import address
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import checkpoint, expire_at


def _merge_selected(target, source, selected):
    # Iterate each historical conversion once, instead of rescanning it for
    # every current holding. The existing merge owns raw amount/last-row rules.
    for key, value in source.items():
        checkpoint()
        if key[0] in selected:
            merge_conversions(target.setdefault(key[0], {}), {key: value}, key[0])


def _earnings(engine, wallet, header, block, life, history, ids, assets, lp, royalties, head):
    p = engine.p
    descriptors = {a: engine.descriptors[a] for a in assets['selected_asset_ids']}
    ordinals = {}
    selected = set(ids)
    # Native/ZZZ and selected royalties use the same typed raw getters. Each
    # helper invocation stays bounded; the surrounding normal request budget,
    # canonical raw-cache bounds and final checks remain in force.
    for offset in range(0, len(ids), CHUNK_SIZE):
        checkpoint()
        chunk = ids[offset:offset + CHUNK_SIZE]
        prefetch_accounts(p, block, chunk, lp, sorted(a for a in royalties if a in descriptors))
        for identifier in chunk:
            require(p._addr('nft', 'ownerOf(uint256)', identifier, block=block) == wallet,
                    'Aggregate earnings owner differs')
            ordinal = p._uint('nft', 'mintOrdinalOf(uint256)', identifier, block=block)
            require(0 < ordinal <= history.provenance['minted_count'] and
                    p._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=block) == identifier,
                    'Aggregate earnings NFT identity differs')
            ordinals[identifier] = ordinal
    epochs = []
    histories = {p.contracts['access'].address: history}
    if p.lineage:
        p.lineage.financial(p, header, block, life, history, None, None, verified_epochs=epochs,
                            history_reader=engine.history_snapshot, verified_histories=histories)
    else:
        require(life['predecessor_controller'] is None, 'Complete predecessor history is required')
        epochs = [(p, header, None)]
    model = ExactReplay(header['timestamp'], wallet_ids=ids, tracked_assets=tuple(descriptors))
    claims = defaultdict(lambda: [0, 0])
    conversions, lp_conversions, provenance = {}, {}, []
    start = engine.replay_start(epochs)
    for index, (peer, cutoff, lower) in enumerate(epochs):
        checkpoint()
        require(peer.accounting_version == 7, 'Aggregate earnings requires explicit exact LP lineage')
        at = {'blockHash': cutoff['hash'], 'requireCanonical': True}
        emitters = engine.check_profile(peer, at)
        a, b = peer._admitted(at)
        prefix = index < start
        if prefix:
            replayed = histories[peer.contracts['access'].address]
        else:
            begin_lower = None if index == start and getattr(engine.checkpoint, 'lineage_checkpoint', False) else lower
            model.begin(emitters, a, b, begin_lower, fee_intake_version=peer.fee_intake_version,
                        royalty_settlement_version=royalty_profile(peer))
            replayed = engine.history_snapshot(peer, cutoff, at, a, b, consumer=model,
                                              extra_emitters=tuple(emitters.values()))
            model.finish()
            engine.reconcile(peer, model, at, a, b, replayed.provenance['minted_count'])
        for offset in range(0, len(ids), CHUNK_SIZE):
            checkpoint()
            chunk = ids[offset:offset + CHUNK_SIZE]
            prefetch_accounts(peer, at, chunk, a, sorted(asset for asset in b if asset in descriptors))
            for identifier in chunk:
                ordinal = peer._uint('nft', 'mintOrdinalOf(uint256)', identifier, block=at)
                if identifier in replayed.owners:
                    require(ordinal == ordinals[identifier] and
                            peer._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=at) == identifier,
                            'Aggregate predecessor identity differs')
                    if not prefix:
                        require(ordinal == model.ordinals.get(identifier),
                                'Aggregate NFT ordinal differs from complete mint history')
                        bucket, shares = model.shares.get(identifier, (0, 0))
                        require(peer._uint('vault', 'sharesOf(uint256)', identifier, block=at) == shares and
                                peer._uint('vault', 'nftBucket(uint256)', identifier, block=at) == bucket and
                                peer._uint('royalties', 'weightOf(uint256)', identifier, block=at) == model.weights.get(identifier, 0),
                                'Aggregate earnings rights differ from chain')
                        require(peer._uint('rewards', 'rewardBucket(uint256)', identifier, block=at) == bucket,
                                'Aggregate exact LP bucket differs')
                        for asset in a:
                            actual = tuple(int(w, 16) for w in peer._call(peer.contracts['rewards'].address,
                                'claimableComponents(uint256,address)', identifier, asset, block=at, words=2))
                            require(actual == model.components(identifier, asset), 'Aggregate exact LP components differ')
                else:
                    require(ordinal == 0 and ordinals[identifier] > replayed.provenance['minted_count'],
                            'Aggregate predecessor mint history differs')
        _merge_selected(conversions, replayed.conversions, selected)
        _merge_selected(lp_conversions, replayed.lp_conversions, selected)
        for (identifier, asset), amounts in replayed.claims.items():
            if identifier in selected:
                claims[identifier, asset][0] += amounts[0]
                claims[identifier, asset][1] += amounts[1]
        provenance.append({'controller': peer.contracts['access'].address, 'history': dict(replayed.provenance),
                           'activation_cutoff': None if lower is None else {'block': lower[0], 'transaction': lower[1]}})
    for identifier in ids:
        checkpoint()
        account = SimpleNamespace(nft_id=identifier, totals=model.account_totals[identifier], scaled=model.accounts[identifier],
            cohorts=model.cohorts, weights=model.weights, activation_order=model.activation_order,
            royalty_opening=model.royalty_opening, initial_royalty_allocations=model.initial_royalty_allocations,
            ticket_offsets=model.ticket_offsets, royalty_cursors=model.royalty_cursors)
        financial = {'previously_claimed': {'assets': [dict(asset=a, lp_raw=str(claims[identifier, a][0]),
                     royalties_raw=str(claims[identifier, a][1])) for a in descriptors]},
                     'lp_conversions': conversion_report(lp_conversions.get(identifier, {}), identifier, engine.descriptors, {}),
                     'royalty_conversions': conversion_report(conversions.get(identifier, {}), identifier, engine.descriptors, {})}
        engine.check_paid(p, account, financial, block, [a for a in lp if a in descriptors],
                          [a for a in royalties if a in descriptors])
    result = model.report(descriptors)
    prices = (engine.prices.read(block, timestamp=header['timestamp'], selected=tuple(descriptors)) if engine.prices else {
        a: {'available': False, 'usd_per_token_18': None, 'reason': 'price_not_configured'} for a in descriptors})
    value_report(result, descriptors, prices)
    result.update(schema=1, chain_id=p.chain, wallet=wallet, nft_contract=p.contracts['nft'].address,
        scope='wallet', token_ids=list(map(str, ids)), count=len(ids),
        inventory_sha256=hashlib.sha256(','.join(map(str, ids)).encode('ascii')).hexdigest(),
        ownership_scope='Lifetime earnings of NFTs owned at this snapshot, including earlier owners; not personal wallet income.',
        lifecycle=deepcopy(life), **assets,
        provenance=dict(block_number=header['number'], block_hash=header['hash'], block_timestamp=header['timestamp'],
                        observed_head=head, confirmations=p.confirmations, configuration_sha256=p.identity,
                        epochs=provenance, finality='confirmation_depth_only', protocol_finalized=False,
                        eip1898_require_canonical=True, accounting_version=7,
                        completeness='Complete configured indexed history and pinned live NFT reconciliation; not a log-completeness proof.'))
    for peer, cutoff, _ in epochs:
        require(p._header(hex(cutoff['number'])) == cutoff, 'Aggregate earnings epoch changed')
    return result


def read(p, wallet_address, block_number, asset_offset=0):
    if p.accounting_version != 7 or getattr(p, 'wallet_read_batch', 0) != 1 or p.earnings_history is None:
        raise HistoryError('Reviewed aggregate wallet read profile is not configured')
    wallet = address(wallet_address)
    if type(block_number) is not int or not p.start <= block_number < 1 << 63:
        raise ValueError('Invalid aggregate wallet block')
    engine = p.earnings_history
    assets = asset_page(engine, asset_offset)
    with scope([p]):
        safe, head, _ = p._snapshot()
        require(block_number <= safe['number'], 'Aggregate wallet block is not confirmed')
        header = p._header(hex(block_number))
        p._fresh(header)
        expire_at(header['timestamp'] + p.max_age, p.clock)
        block = {'blockHash': header['hash'], 'requireCanonical': True}
        life = p._verify_deployment(block)
        # Identity may remain independently available when a royalty currency
        # fails. The complete earnings branch repeats strict asset admission.
        lp, royalties = p._admitted(block, asset_health={})
        history = engine.history_snapshot(p, header, block, lp, royalties)
        ids = tuple(sorted(i for i, owner in history.owners.items() if owner == wallet))
        count = p._uint('nft', 'balanceOf(address)', wallet, block=block)
        require(count == len(ids) and count <= 1000, 'Aggregate inventory differs from canonical balance')
        require(history.provenance['available'] is True and history.provenance['through_block'] == block_number and
                history.provenance['block_hash'] == header['hash'] and history.provenance['minted_count'] >= count,
                'Aggregate ownership history differs')
        earnings = None
        try:
            lp, royalties = p._admitted(block)
            earnings = _earnings(engine, wallet, header, block, life, history, ids, assets, lp, royalties, head)
        except (WorkLimit, ProjectionError, HistoryError):
            raise
        except RpcError:
            # No partially verified financial data escapes. The caller must
            # independently assemble ownership/summary before using this wire.
            pass
        engine.finish_checkpoint()
        p._finish(header)
        return dict(schema=1, kind='fixed_block_wallet_earnings_page', available=True,
            chain_id=p.chain, wallet=wallet, nft_contract=p.contracts['nft'].address,
            count=count, token_ids=list(map(str, ids)), verified_count=count if earnings is not None else 0,
            complete=earnings is not None, inventory_sha256=hashlib.sha256(','.join(map(str, ids)).encode('ascii')).hexdigest(),
            **assets, earnings=earnings, earnings_error=None if earnings is not None else 'earnings_unavailable',
            history=deepcopy(dict(history.provenance)), lifecycle=deepcopy(life),
            provenance=dict(block_number=header['number'], block_hash=header['hash'], block_timestamp=header['timestamp'],
                            observed_head=head, confirmations=p.confirmations, configuration_sha256=p.identity,
                            finality='confirmation_depth_only', protocol_finalized=False,
                            eip1898_require_canonical=True, accounting_version=7))
