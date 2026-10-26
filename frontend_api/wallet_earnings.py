"""Production read path: bounded current-holdings earnings, never wallet tenure.

Replay each epoch once for at most 16 NFTs, preserving each NFT's fractions.
All chunks must share one canonical inventory and block before being summed.
"""
import hashlib
from collections import defaultdict
from types import SimpleNamespace

from frontend_api.earnings_replay import Replay, require
from frontend_api.earnings_prices import value_report
from frontend_api.history import HistoryError, conversion_report, merge_conversions
from frontend_api.portfolio import CHUNK_SIZE
from zzz_ops.abi import address
from zzz_ops.work_budget import checkpoint, expire_at


def read(engine, wallet_address, block_number, offset):
    p = engine.p
    wallet = address(wallet_address)
    if type(block_number) is not int or type(offset) is not int or not 0 <= offset < 1000 or offset % CHUNK_SIZE:
        raise ValueError('Invalid wallet earnings cursor')
    safe, head, _ = p._snapshot()
    require(p.start <= block_number <= safe['number'], 'Earnings block is not confirmed')
    header = p._header(hex(block_number))
    p._fresh(header)
    expire_at(header['timestamp'] + p.max_age, p.clock)
    block = {'blockHash': header['hash'], 'requireCanonical': True}
    life = p._verify_deployment(block)
    lp, royalties = p._admitted(block)
    history = p._history_snapshot(header, block, lp, royalties)
    ids = sorted(i for i, owner in history.owners.items() if owner == wallet)
    count = p._uint('nft', 'balanceOf(address)', wallet, block=block)
    require(count == len(ids) and count <= 1000, 'Earnings inventory differs from canonical balance')
    if offset >= count and not (offset == count == 0):
        raise ValueError('Cursor is outside earnings inventory')
    selected = tuple(ids[offset:offset + CHUNK_SIZE])
    ordinals = {}
    for i in selected:
        require(p._addr('nft', 'ownerOf(uint256)', i, block=block) == wallet, 'Earnings owner differs')
        ordinal = p._uint('nft', 'mintOrdinalOf(uint256)', i, block=block)
        require(ordinal > 0 and p._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=block) == i,
                'Earnings NFT identity differs')
        ordinals[i] = ordinal
    epochs = []
    if p.lineage:
        # Verify receipt pairs, deployment origin, cutoff chronology and anchors once.
        p.lineage.financial(p, header, block, life, history, None, None, verified_epochs=epochs)
    else:
        require(life['predecessor_controller'] is None, 'Complete predecessor history is required')
        epochs = [(p, header, None)]
    model = Replay(header['timestamp'], selected=selected)
    claims = defaultdict(lambda: [0, 0])
    conversions, lp_conversions, provenance = {}, {}, []
    for peer, cutoff, lower in epochs:
        checkpoint()
        at = {'blockHash': cutoff['hash'], 'requireCanonical': True}
        emitters = engine.check_profile(peer, at)
        a, b = peer._admitted(at)
        model.begin(emitters, a, b, lower, fee_intake_version=peer.fee_intake_version)
        replayed = peer._history_snapshot(cutoff, at, a, b, consumer=model, extra_emitters=tuple(emitters.values()))
        model.finish()
        engine.reconcile(peer, model, at, a, b, replayed.provenance['minted_count'])
        for i in selected:
            ordinal = peer._uint('nft', 'mintOrdinalOf(uint256)', i, block=at)
            if i in replayed.owners:
                require(ordinal == ordinals[i] and peer._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=at) == i,
                        'Predecessor earnings identity differs')
                bucket, shares = model.shares.get(i, (0, 0))
                require(peer._uint('vault', 'sharesOf(uint256)', i, block=at) == shares and
                        peer._uint('vault', 'nftBucket(uint256)', i, block=at) == bucket and
                        peer._uint('royalties', 'weightOf(uint256)', i, block=at) == model.weights.get(i, 0),
                        'Selected earnings rights differ from chain')
            else:
                require(ordinal == 0 and ordinals[i] > replayed.provenance['minted_count'],
                        'Missing predecessor NFT contradicts mint order')
            merge_conversions(conversions, replayed.conversions, i)
            merge_conversions(lp_conversions, replayed.lp_conversions, i)
        for (i, asset), amounts in replayed.claims.items():
            if i in ordinals:
                claims[i, asset][0] += amounts[0]
                claims[i, asset][1] += amounts[1]
        provenance.append({'controller': peer.contracts['access'].address, 'history': dict(replayed.provenance),
                           'activation_cutoff': None if lower is None else {'block': lower[0], 'transaction': lower[1]}})
    for i in selected:
        account = SimpleNamespace(nft_id=i, totals=model.account_totals[i], scaled=model.accounts[i],
                                  cohorts=model.cohorts, weights=model.weights)
        financial = {'previously_claimed': {'assets': [dict(asset=a, lp_raw=str(claims[i, a][0]),
                     royalties_raw=str(claims[i, a][1])) for a in engine.descriptors]},
                     'lp_conversions': conversion_report(lp_conversions, i, engine.descriptors, {}),
                     'royalty_conversions': conversion_report(conversions, i, engine.descriptors, {})}
        engine.check_paid(p, account, financial, block, lp, royalties)
    result = model.report(engine.descriptors)
    prices = engine.prices.read(block,timestamp=header['timestamp']) if engine.prices else {
        a: {'available': False, 'usd_per_token_18': None, 'reason': 'price_not_configured'} for a in engine.descriptors}
    value_report(result, engine.descriptors, prices)
    result.update(schema=1, chain_id=p.chain, wallet=wallet, nft_contract=p.contracts['nft'].address,
        inventory_sha256=hashlib.sha256(','.join(map(str, ids)).encode('ascii')).hexdigest(),
        count=count, offset=offset, chunk_size=CHUNK_SIZE, token_ids=list(map(str, selected)),
        next_offset=offset + len(selected) if offset + len(selected) < count else None,
        ownership_scope='Lifetime earnings of NFTs owned at this snapshot, including earlier owners; not personal wallet income.',
        lifecycle=life, provenance=dict(block_number=header['number'], block_hash=header['hash'],
        block_timestamp=header['timestamp'], observed_head=head, confirmations=p.confirmations,
        configuration_sha256=p.identity, epochs=provenance, finality='confirmation_depth_only',
        completeness='Complete configured indexed history and pinned RPC reconciliation; not a log-completeness proof.'))
    for peer, cutoff, _ in epochs:
        require(p._header(hex(cutoff['number'])) == cutoff, 'Earnings epoch changed during replay')
    p._finish(header)
    return result
