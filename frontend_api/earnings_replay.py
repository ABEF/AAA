"""Exact indexed-earnings replay. No price estimates, writes or transaction signing."""
from collections import defaultdict

from frontend_api.history import HistoryError, _topic_address
from zzz_ops.abi import decode_words, keccak256
from zzz_ops.work_budget import checkpoint

SCALE = 10**36
ZERO = '0x' + '0'*40

# Only these exact events from their pinned emitters affect accounting.
SPECS = {
 ('nft', 'Transfer(address,address,uint256)'): (3, 0),
 ('vault', 'SharesAdded(uint256,uint256,uint256,uint256)'): (2, 2),
 ('membership', 'MembershipActivated(uint256)'): (1, 0),
 ('rewards', 'PoolRewardsCredited(uint256,address,uint256,uint256)'): (2, 2),
 ('fees', 'FeesAllocated(uint256,address,uint256,uint256)'): (2, 2),
 ('fees', 'MembershipDustSettled(uint256,address,uint256)'): (2, 1),
 ('royalties', 'AssetAdded(address,uint256)'): (1, 1),
 ('royalties', 'Activated(uint256,uint256)'): (1, 1),
 ('royalties', 'RoyaltyAssetDeferred(uint256,address)'): (2, 0),
 ('royalties', 'RoyaltyEligibilityRecovered(address,uint256,uint256)'): (1, 2),
 ('royalties', 'RoyaltiesReceived(address,uint256,bool)'): (1, 2),
 ('handoff', 'Frozen(bytes32,address)'): (2, 0),
 ('handoff', 'Aborted(bytes32)'): (1, 0),
 ('handoff', 'Retired(bytes32,address,bytes32)'): (2, 1),
 ('handoff', 'Activated(bytes32,address,bytes32)'): (2, 1),
}
TOPICS = {(role, '0x'+keccak256(sig.encode()).hex()): (sig.split('(')[0], *layout)
          for (role, sig), layout in SPECS.items()}
COLLECTION = ('lp_processed', 'lp_owner_allocated', 'lp_collective_allocated',
              'lp_compounding_allocated', 'lp_buyback_allocated', 'lp_collective_quarantined',
              'royalties_received', 'royalties_allocated', 'royalties_quarantined')
NFT = ('lp_individual', 'lp_collective', 'royalties')


def require(condition, message):
    if not condition:
        raise HistoryError(message)


class Replay:
    def __init__(self, timestamp, nft_id=None, *, selected=None):
        require(selected is None or (nft_id is None and isinstance(selected, tuple) and
                len(selected) <= 16 and len(set(selected)) == len(selected) and
                all(type(i) is int and 0 < i < 2**256 for i in selected)), 'Invalid earnings selection')
        self.timestamp, self.nft_id = timestamp, nft_id
        self.selected = selected if selected is not None else (() if nft_id is None else (nft_id,))
        self.group = selected is not None
        self.accounts = {i: defaultdict(int) for i in self.selected}
        self.account_totals = {i: defaultdict(int) for i in self.selected}
        self.mints = []
        self.minted = set()
        self.shares = {}
        self.supply = defaultdict(int)
        self.members = set()
        self.weights = {}
        self.activation_order = []
        self.cohorts = {}
        self.deferred = defaultdict(set)
        self.pending_recovery = {}
        self.owner_index = defaultdict(int)
        self.collective_index = defaultdict(int)
        self.royalty_index = defaultdict(int)
        self.fee_dust = defaultdict(int)
        self.scaled = defaultdict(int)
        self.totals = defaultdict(int)
        self.day = defaultdict(int)
        self.events = 0
        self.last_timestamp = -1
        self.frozen = self.retired = False

    def begin(self, emitters, lp_assets, royalty_assets, lower=None):
        self.roles = {value: key for key, value in emitters.items()}
        self.lp_assets, self.royalty_assets = set(lp_assets), set(royalty_assets)
        self.lower, self.started = lower, lower is None
        if lower is not None:
            require(self.retired, 'Previous earnings epoch was not retired')
            require(all(cohort == set(self.weights) for cohort in self.cohorts.values()),
                    'Canonical royalty cutoff left deferred eligibility')
            # Import reconstructs activation ordinals in NFT mint order.
            self.activation_order = [i for i in self.mints if i in self.weights]
        self.frozen = self.retired = False

    def add(self, metric, asset, amount, timestamp):
        require(amount >= 0, 'Negative financial allocation')
        self.totals[metric, asset] += amount
        if self.timestamp - 86400 < timestamp <= self.timestamp:
            self.day[metric, asset] += amount

    def earn(self, metric, asset, scaled, timestamp, identifier):
        checkpoint()
        key = metric, asset
        account = self.accounts[identifier]
        old = account[key]
        account[key] += scaled
        # Attribute a whole raw unit when carried fractions first make it payable.
        earned = account[key]//SCALE - old//SCALE
        self.account_totals[identifier][key] += earned
        self.add(metric, asset, earned, timestamp)
        if not self.group:
            self.scaled[key] = account[key]

    def __call__(self, emitter, topics, data, block, block_hash, timestamp, transaction, log_index):
        checkpoint()
        role = self.roles.get(emitter)
        spec = TOPICS.get((role, topics[0].lower()))
        if spec is None:
            return
        name, indexed, words = spec
        require(len(topics) == indexed+1, 'Unexpected earnings event topics')
        values = decode_words(data)
        require(len(values) == words, 'Unexpected earnings event data')
        t = [int(x, 16) for x in topics[1:]]
        d = [int(x, 16) for x in values]
        if not self.started:
            if role == 'handoff' and name == 'Activated':
                number, tx, handoff, root = self.lower
                require((block, transaction, topics[1].lower(), '0x'+values[0]) == (number, tx, handoff, root),
                        'Earnings epoch activation differs from verified retirement')
                self.started = True
            # Import Transfers/backing/constructor prefunds are not new earnings.
            return
        require(not self.retired, 'Economic events follow canonical retirement')
        require(self.last_timestamp <= timestamp <= self.timestamp, 'Earnings chronology is inconsistent')
        self.last_timestamp = timestamp
        self.events += 1
        if role == 'handoff':
            if name == 'Frozen':
                require(not self.frozen, 'Repeated canonical freeze')
                self.frozen = True
            elif name == 'Aborted':
                require(self.frozen and not self.pending_recovery, 'Invalid canonical abort chronology')
                self.frozen = False
            elif name == 'Retired':
                require(self.frozen and not self.pending_recovery, 'Retirement lacks settled cutoff')
                self.retired = True
            else:
                raise HistoryError('Unexpected successor activation in earnings epoch')
        elif role == 'nft':
            sender, recipient = _topic_address(topics[1]), _topic_address(topics[2])
            identifier = t[2]
            if sender == ZERO:
                require(identifier not in self.minted and len(self.mints) < 1000 and recipient != ZERO,
                        'Duplicate/invalid earnings mint')
                self.minted.add(identifier); self.mints.append(identifier)
            else:
                require(identifier in self.minted and recipient != ZERO, 'Invalid earnings transfer')
        elif role == 'membership':
            require(t[0] in self.minted and t[0] not in self.members, 'Repeated/unknown collective activation')
            self.members.add(t[0])
        elif role == 'vault':
            identifier, bucket = t
            require(identifier in self.minted and bucket != 0 and d[0] > 0 and d[1] > 0,
                    'Invalid earnings share addition')
            previous, shares = self.shares.get(identifier, (bucket, 0))
            require(previous == bucket, 'Unsupported NFT bucket reassignment')
            self.shares[identifier] = bucket, shares+d[0]
            self.supply[bucket] += d[0]
            require(len(self.supply) <= 4, 'Earnings bucket bound exceeded')
        elif role == 'rewards':
            bucket, asset = t[0], _topic_address(topics[2])
            require(asset in self.lp_assets and self.supply[bucket] > 0 and sum(d) > 0,
                    'LP allocation lacks admitted asset/shares')
            personal, collective = d
            owner_delta = personal*SCALE//self.supply[bucket]
            self.owner_index[bucket, asset] += owner_delta
            self.add('lp_owner_allocated', asset, personal, timestamp)
            self.add('lp_collective_allocated' if self.members else 'lp_collective_quarantined', asset, collective, timestamp)
            shared_delta = collective*SCALE//len(self.members) if self.members else 0
            self.collective_index[asset] += shared_delta
            for identifier in self.selected:
                own_bucket, shares = self.shares.get(identifier, (0, 0))
                self.earn('lp_individual', asset, shares*owner_delta if own_bucket == bucket else 0, timestamp, identifier)
                self.earn('lp_collective', asset, shared_delta if identifier in self.members else 0, timestamp, identifier)
        elif role == 'fees':
            bucket, asset = t[0], _topic_address(topics[2])
            require(asset in self.lp_assets and self.supply[bucket] > 0, 'Unreviewed LP revenue currency/bucket')
            key = bucket, asset
            if name == 'FeesAllocated':
                distributed, dust = d
                require(distributed % 20 == 0 and dust < 20, 'Invalid fee allocation rounding')
                self.add('lp_processed', asset, distributed+dust-self.fee_dust[key], timestamp)
                self.fee_dust[key] = dust
                self.add('lp_compounding_allocated', asset, distributed//20, timestamp)
                self.add('lp_buyback_allocated', asset, distributed//20, timestamp)
            else:
                require(d[0] == self.fee_dust[key] and 0 < d[0] < 20, 'Invalid carried fee dust')
                self.fee_dust[key] = 0
        else:
            self.royalty(name, topics, t, d, timestamp, transaction)

    def royalty(self, name, topics, t, d, timestamp, transaction):
        if name == 'AssetAdded':
            asset = _topic_address(topics[1])
            require(asset in self.royalty_assets and asset not in self.cohorts, 'Duplicate/unreviewed royalty admission')
            self.cohorts[asset] = set(self.weights)
            # Constructor/admission prefunds are quarantined, not earned receipts.
        elif name == 'RoyaltyAssetDeferred':
            identifier, asset = t[0], _topic_address(topics[2])
            require(identifier in self.minted and identifier not in self.weights and asset != ZERO and asset in self.cohorts,
                    'Invalid deferred royalty activation')
            require(asset not in self.deferred[identifier], 'Repeated deferred asset')
            self.deferred[identifier].add(asset)
        elif name == 'Activated':
            identifier, weight = t[0], d[0]
            require(identifier in self.minted and identifier not in self.weights and 1 <= weight <= 3,
                    'Invalid royalty activation')
            deferred = self.deferred.pop(identifier, set())
            for asset, cohort in self.cohorts.items():
                if asset not in deferred:
                    require(cohort == set(self.weights), 'Healthy activation omitted royalty recovery')
                    cohort.add(identifier)
            self.weights[identifier] = weight
            self.activation_order.append(identifier)
        elif name == 'RoyaltyEligibilityRecovered':
            asset = _topic_address(topics[1]); first, last = d
            require(asset in self.cohorts and first == len(self.cohorts[asset])+1 and last == len(self.activation_order)
                    and first <= last and asset not in self.pending_recovery, 'Invalid royalty recovery prefix')
            require(self.cohorts[asset] == set(self.activation_order[:first-1]), 'Non-prefix royalty cohort')
            if self.frozen:
                # canonicalSettle emits recovery BEFORE RoyaltiesReceived, although
                # the latter used the OLD eligible weight. Normal sync reverses it.
                self.pending_recovery[asset] = transaction
            else:
                self.cohorts[asset] = set(self.weights)
        else:
            asset = _topic_address(topics[1]); amount, eligible = d
            require(asset in self.cohorts and eligible in (0, 1), 'Unknown royalty currency/eligibility')
            cohort = self.cohorts[asset]
            supply = sum(self.weights[i] for i in cohort)
            require(bool(eligible) == bool(supply), 'Royalty receipt has inconsistent cohort weight')
            self.add('royalties_received', asset, amount, timestamp)
            self.add('royalties_allocated' if eligible else 'royalties_quarantined', asset, amount, timestamp)
            delta = amount*SCALE//supply if supply else 0
            self.royalty_index[asset] += delta
            for identifier in self.selected:
                self.earn('royalties', asset, delta*self.weights[identifier] if identifier in cohort else 0, timestamp, identifier)
            if asset in self.pending_recovery:
                require(self.pending_recovery.pop(asset) == transaction, 'Royalty cutoff recovery crossed transactions')
                self.cohorts[asset] = set(self.weights)

    def finish(self):
        require(self.started and not self.deferred and not self.pending_recovery, 'Incomplete earnings epoch')
        require(set(self.weights) == self.members == set(self.shares), 'Activation/share/membership events are incomplete')
        require(set(self.cohorts) == self.royalty_assets, 'Royalty admission history is incomplete')

    def report(self, descriptors):
        fields = NFT if self.group or self.nft_id is not None else COLLECTION
        def period(amounts):
            return [{'asset': asset, 'symbol': d.symbol, 'decimals': d.decimals,
                     **{name+'_raw': str(amounts[name, asset]) for name in fields}}
                    for asset, d in sorted(descriptors.items())]
        return {'available': True, 'scope': 'wallet_chunk' if self.group else 'collection' if self.nft_id is None else 'nft',
                'all_time': period(self.totals), 'last_24h': period(self.day),
                'window': {'after_timestamp_exclusive': max(-1, self.timestamp-86400),
                           'through_timestamp_inclusive': self.timestamp},
                'event_count': self.events, 'clock': 'on-chain processing/allocation time',
                'rounding': 'Exact 1e36 ledger indexes; NFT whole units enter the period when carried fractions cross one raw unit.',
                'unprocessed_revenue_included': False, 'claims_and_conversions_are_income': False}
