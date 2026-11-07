"""Exact-LP checkpoint2 state; no historical-index conversion or live approval.

The common checkpoint envelope authenticates source/configuration/anchor and
validates royalty4/shared history. This codec retains the original raw LP trees,
including zero rows and nonmonetary high/low phase, without settling them.
"""
from collections import defaultdict
import copy

from frontend_api.earnings_exact_lp import ExactReplay
from frontend_api.earnings_replay import SCALE, require
from frontend_api.history import HistoryError, ZERO
from zzz_ops.abi import address
from zzz_ops.exact_lp import Tree, UINT, Q, LEAVES, MAX_ORDINAL
from zzz_ops.work_budget import checkpoint


FIELDS = {'pair', 'ordinals', 'owner_trees', 'collective_tree', 'direct', 'orphaned'}
TREE_FIELDS = {'weights', 'pending', 'carry', 'outstanding'}
MAX_NODE = LEAVES + MAX_ORDINAL - 1
SHARED_FIELDS = ('mints', 'shares', 'supply', 'members', 'weights', 'owner_index',
                 'collective_index', 'royalty_index', 'royalty_settlement_version')
TRANSIENT_FIELDS = ('pending_share_sync', 'pending_member_sync', 'pending_lp_credit',
                    'pending_exact_allocations', 'deferred', 'pending_recovery',
                    'royalty_custody', 'custody_ids')


def _uint(value):
    return type(value) is int and 0 <= value <= UINT


def _shared(model):
    return {name: getattr(model, name) for name in SHARED_FIELDS}


def _weights(leaves):
    result = defaultdict(int)
    for ordinal, amount in leaves.items():
        checkpoint()
        node = Tree.leaf(ordinal)
        while node:
            result[node] += amount
            require(_uint(result[node]), 'Checkpoint2 LP denominator overflow')
            node >>= 1
    return dict(result)


def _tree(raw, expected):
    require(isinstance(raw, dict) and set(raw) == TREE_FIELDS,
            'Incomplete checkpoint2 LP tree')
    weights = raw['weights']
    require(isinstance(weights, dict) and len(weights) <= MAX_NODE and
            all(type(k) is int and 1 <= k <= MAX_NODE and _uint(v) for k, v in weights.items()),
            'Invalid checkpoint2 LP weight nodes')
    require({k: v for k, v in weights.items() if v} == expected,
            'Checkpoint2 LP tree weights differ from shares or membership')
    outstanding = raw['outstanding']
    require(isinstance(outstanding, list) and len(outstanding) == 2 and all(_uint(v) for v in outstanding),
            'Invalid checkpoint2 LP outstanding books')
    for name in ('pending', 'carry'):
        require(isinstance(raw[name], tuple) and len(raw[name]) == 2,
                'Invalid checkpoint2 LP asset book shape')
    for book in (0, 1):
        checkpoint()
        pending, carry = raw['pending'][book], raw['carry'][book]
        require(isinstance(pending, dict) and len(pending) <= MAX_NODE and
                all(type(k) is int and 1 <= k <= MAX_NODE and _uint(v) and
                    (v == 0 or weights.get(k, 0) > 0) for k, v in pending.items()),
                'Invalid checkpoint2 LP pending nodes')
        require(sum(pending.values()) == outstanding[book],
                'Checkpoint2 LP pending units differ from outstanding')
        require(isinstance(carry, dict) and len(carry) < LEAVES,
                'Invalid checkpoint2 LP phase nodes')
        for node, phase in carry.items():
            require(type(node) is int and 1 <= node < LEAVES and
                    isinstance(phase, tuple) and len(phase) == 2 and
                    type(phase[0]) is int and 0 <= phase[0] < Q and _uint(phase[1]),
                    'Invalid checkpoint2 LP high/low phase')
            weight = weights.get(node, 0)
            require((phase == (0, 0)) if weight == 0 else phase[1] < weight,
                    'Checkpoint2 LP phase denominator differs')
    return _restore_tree(raw)


def validate(exact, shared, lp_assets, accounts):
    """Validate decoded raw state; the common codec validates royalty/history.

    ``accounts=None`` is reserved for restoring already validated shared state
    into a selected NFT/wallet replay. Full artifact validation supplies every
    minted account, including dormant NFTs.
    """
    require(isinstance(exact, dict) and set(exact) == FIELDS,
            'Incomplete checkpoint2 exact LP state')
    require(isinstance(shared, dict) and all(k in shared for k in SHARED_FIELDS),
            'Incomplete checkpoint2 shared LP state')
    pair = exact['pair']
    require(isinstance(pair, tuple) and len(pair) == 2 and pair[0] == ZERO and
            isinstance(pair[1], str) and pair[1] != ZERO and
            isinstance(lp_assets, list) and tuple(lp_assets) == pair,
            'Checkpoint2 requires native ETH and the fixed ZZZ pair')
    try:
        require(address(pair[1]) == pair[1], 'Invalid checkpoint2 fixed ZZZ identity')
    except ValueError as exc:
        raise HistoryError('Invalid checkpoint2 fixed ZZZ identity') from exc
    require(type(shared['royalty_settlement_version']) is int and shared['royalty_settlement_version'] == 4,
            'Checkpoint2 requires original-currency royalty4')
    require(all(isinstance(shared[name], dict) and not any(shared[name].values())
                for name in ('owner_index', 'collective_index', 'royalty_index')),
            'Checkpoint2 cannot reinterpret historical indexed books')
    mints = shared['mints']
    require(isinstance(mints, list) and len(mints) <= MAX_ORDINAL and
            all(_uint(i) and i > 0 for i in mints) and len(set(mints)) == len(mints),
            'Invalid checkpoint2 mint order')
    ordinals = exact['ordinals']
    require(isinstance(ordinals, dict) and all(type(i) is int and type(n) is int for i, n in ordinals.items()) and
            ordinals == {i: n for n, i in enumerate(mints, 1)},
            'Checkpoint2 immutable ordinals differ')
    shares, members, supply = shared['shares'], shared['members'], shared['supply']
    require(isinstance(shares, dict) and isinstance(members, set) and isinstance(supply, dict) and
            all(type(i) is int and i in ordinals for i in shares) and all(type(i) is int for i in members) and
            members == set(shares) and
            isinstance(shared['weights'], dict) and set(shared['weights']) == members and
            all(type(i) is int for i in shared['weights']) and
            all(type(w) is int and 1 <= w <= 3 for w in shared['weights'].values()),
            'Invalid checkpoint2 active LP inventory')
    leaves, totals = {}, defaultdict(int)
    for identifier, item in shares.items():
        require(isinstance(item, tuple) and len(item) == 2 and all(_uint(n) and n > 0 for n in item),
                'Invalid checkpoint2 NFT shares')
        bucket, amount = item
        leaves.setdefault(bucket, {})[ordinals[identifier]] = amount
        totals[bucket] += amount
    require(len(totals) <= 4 and supply == dict(totals) and
            all(_uint(k) and k > 0 and _uint(v) and v > 0 for k, v in supply.items()),
            'Checkpoint2 share denominators differ')
    owners = exact['owner_trees']
    require(isinstance(owners, dict) and len(owners) <= 4 and set(owners) == set(totals) and
            all(type(k) is int for k in owners), 'Checkpoint2 owner tree inventory differs')
    owner_trees = {bucket: _tree(raw, _weights(leaves[bucket])) for bucket, raw in owners.items()}
    collective = _tree(exact['collective_tree'], _weights({ordinals[i]: 1 for i in members}))
    direct = exact['direct']
    require(isinstance(direct, dict) and len(direct) <= 2*MAX_ORDINAL,
            'Invalid checkpoint2 direct credit inventory')
    direct_totals = [0, 0]
    for key, amounts in direct.items():
        require(isinstance(key, tuple) and len(key) == 2 and type(key[0]) is int and key[0] in ordinals and
                key[1] in pair and isinstance(amounts, list) and len(amounts) == 2 and all(_uint(v) for v in amounts) and
                (key[0] in members or amounts == [0, 0]), 'Invalid checkpoint2 direct LP components')
        direct_totals[pair.index(key[1])] += sum(amounts)
    orphaned = exact['orphaned']
    require(isinstance(orphaned, dict) and set(orphaned) <= set(pair) and all(_uint(v) for v in orphaned.values()),
            'Invalid checkpoint2 orphaned LP units')
    for book, asset in enumerate(pair):
        liability = direct_totals[book] + collective.outstanding[book] + sum(t.outstanding[book] for t in owner_trees.values())
        require(_uint(liability + orphaned.get(asset, 0)), 'Checkpoint2 LP backing total overflow')
        for tree in (collective, *owner_trees.values()):
            try:
                amounts = [tree.claimable(book, n) for n in ordinals.values()]
            except ValueError as exc:
                raise HistoryError('Invalid checkpoint2 LP phase allocation') from exc
            require(sum(amounts) == tree.outstanding[book], 'Checkpoint2 LP assigned units differ from outstanding')
    if accounts is not None:
        require(isinstance(accounts, dict) and set(accounts) == set(mints),
                'Incomplete checkpoint2 whole-unit earnings accounts')
        for identifier, account in accounts.items():
            require(type(identifier) is int and isinstance(account, dict), 'Invalid checkpoint2 earnings account')
            for key, amount in account.items():
                require(isinstance(key, tuple) and len(key) == 2 and type(amount) is int and
                        0 <= amount < 1 << 512 and amount % SCALE == 0,
                        'Checkpoint2 exact earnings contain fractional units')
                if key[0] in ('lp_individual', 'lp_collective'):
                    require(key[1] in pair, 'Checkpoint2 LP earnings contain a third currency')


def _restore_tree(raw):
    tree = Tree()
    for name in TREE_FIELDS:
        setattr(tree, name, copy.deepcopy(raw[name]))
    return tree


def capture(model):
    """Capture one complete original-deployment all-NFT exact replay."""
    require(isinstance(model, ExactReplay) and model.track_all and model.lower is None and
            model.fee_intake_version == 1, 'Checkpoint2 needs a complete original exact LP replay')
    model.finish()
    require(not model.frozen and not model.retired and model.pending_lp_transaction is None and
            not any(getattr(model, name) for name in TRANSIENT_FIELDS),
            'Checkpoint2 cannot capture intermediate or canonical state')
    state = dict(pair=tuple(model.pair), ordinals=copy.deepcopy(model.ordinals),
        owner_trees={bucket: copy.deepcopy(tree.__dict__) for bucket, tree in model.owner_trees.items()},
        collective_tree=copy.deepcopy(model.collective_tree.__dict__),
        direct=copy.deepcopy(dict(model.direct)), orphaned=copy.deepcopy(dict(model.lp_orphaned)))
    validate(state, _shared(model), list(model.pair), model.accounts)
    return state


def restore(model, exact):
    """Install independent raw trees after common shared/account restoration."""
    require(isinstance(model, ExactReplay) and model.lower is None and model.started and
            model.fee_intake_version == 1 and not model.owner_trees and
            model.collective_tree.__dict__ == Tree().__dict__ and not model.direct and
            not model.ordinals and not model.lp_orphaned and model.pending_lp_transaction is None and
            not any(getattr(model, name) for name in TRANSIENT_FIELDS),
            'Checkpoint2 target is not a fresh exact LP replay')
    validate(exact, _shared(model), list(model.pair), None)
    model.owner_trees = {bucket: _restore_tree(raw) for bucket, raw in exact['owner_trees'].items()}
    model.collective_tree = _restore_tree(exact['collective_tree'])
    model.direct = defaultdict(lambda: [0, 0], copy.deepcopy(exact['direct']))
    model.ordinals = copy.deepcopy(exact['ordinals'])
    model.lp_orphaned = defaultdict(int, copy.deepcopy(exact['orphaned']))
