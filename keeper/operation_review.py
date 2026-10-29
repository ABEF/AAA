"""Bounded, read-only LP operation observations; never a worker or transaction plan."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import time

from keeper.monitor import Keeper, CONFIRMATION_CLEARS, CONFIRMATION_RESETS, rpc_hash, rpc_quantity
from zzz_ops.abi import address, calldata, decode_words, keccak256
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.position import decode_position
from zzz_ops.rpc import Rpc
from zzz_ops.state import integer
from zzz_ops.work_budget import Budget, BudgetedRPC, request_scope

MAX_BUCKETS = 4
MAX_CALLS = 512
MAX_SECONDS = 25
ACTIONS = ('rebalance', 'compound', 'harvest')


class ReadOnlyKeeper(Keeper):
    """Future accidental use of a mutation boundary must fail before disk/signing."""
    def save(self): raise RuntimeError('Operation review cannot save state')
    def submit(self, *args, **kwargs): raise RuntimeError('Operation review cannot submit')
    def _validate_signer(self): raise RuntimeError('Operation review cannot load a signer')
    def poll_pending(self): raise RuntimeError('Operation review cannot reconcile transactions')
    def initialize_state(self): raise RuntimeError('Operation review cannot initialize state')


class PinnedReads:
    def __init__(self, rpc, header):
        self.rpc, self.header = rpc, header
        self.block = {'blockHash': rpc_hash(header['hash'], 'review hash'), 'requireCanonical': True}

    def call(self, method, params=None):
        params = copy.deepcopy(params or [])
        if method == 'eth_getBlockByNumber' and params == ['latest', False]:
            return copy.deepcopy(self.header)
        if method in ('eth_call', 'eth_estimateGas'):
            if len(params) == 1: params.append(self.block)
            elif len(params) == 2: params[1] = self.block
            else: raise RpcError('Unsupported review read')
        elif method in ('eth_getCode', 'eth_getBalance'):
            if len(params) != 2: raise RpcError('Unsupported review read')
            params[1] = self.block
        elif method not in ('eth_chainId', 'eth_getBlockByNumber', 'eth_gasPrice'):
            raise RpcError('Operation review only permits read methods')
        return self.rpc.call(method, params)

    def eth_call(self, target, data):
        return self.call('eth_call', [{'to': target, 'data': data}, self.block])


def _header(raw):
    if not isinstance(raw, dict): raise RpcError('Review header unavailable')
    return {'number': rpc_quantity(raw.get('number'), 'review number'),
            'hash': rpc_hash(raw.get('hash'), 'review hash'),
            'timestamp': rpc_quantity(raw.get('timestamp'), 'review timestamp', minimum=1)}


def _attempt(function, reason):
    try: return {'available': True, 'value': function(), 'reason': None}
    except WorkLimit: raise
    except (RpcError, ValueError, TypeError, KeyError):
        return {'available': False, 'value': None, 'reason': reason}


def _row(action, bucket):
    return dict(operation=action, bucket_id=str(bucket), state='unavailable', reasons=[], checks={},
                simulation={'state': 'not_requested', 'reason': None},
                service_schedule={'available': False, 'next_execution_at': None,
                    'reason': 'No worker schedule identity or future inclusion is inferred.'})


def _set(row, state, reason):
    row.update(state=state, reasons=[reason])
    return row


class Review:
    def __init__(self, keeper, header, journal_available, *, simulate):
        self.k, self.header, self.journal = keeper, header, journal_available
        self.stamp = rpc_quantity(header['timestamp'], 'review timestamp', minimum=1)
        self.simulate = simulate
        self.pins = set()
        self._execution = None
        self._budget = None

    def read(self, role, signature, *args, count=1):
        target = self.k.contracts[role] if role in self.k.contracts else address(role)
        values = decode_words(self.k.rpc.eth_call(target, self.k._calldata(signature, *args)))
        if len(values) != count: raise RpcError('Review getter ABI differs')
        return [value.lower() for value in values]

    def uint(self, role, signature, *args):
        return int(self.read(role, signature, *args)[0], 16)

    def flag(self, role, signature, *args):
        value = self.uint(role, signature, *args)
        if value not in (0, 1): raise RpcError('Review boolean is malformed')
        return bool(value)

    def pin(self, role, target=None):
        if role in self.pins: return
        target = target or self.k.contracts[role]
        expected = self.k.config.get('code_hashes', {}).get(role)
        code = self.k.rpc.call('eth_getCode', [target, 'latest'])
        if (not isinstance(expected, str) or re.fullmatch(r'0x[0-9a-fA-F]{64}', expected) is None or
                not isinstance(code, str) or re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', code) is None or
                '0x' + keccak256(bytes.fromhex(code[2:])).hex() != expected.lower()):
            raise RpcError('Review runtime pin differs')
        self.pins.add(role)

    def bucket(self, bucket):
        words = self.read('vault', 'group(uint256)', bucket, count=8)
        position = decode_position(words, self.k.accounting_version)
        if position['status'] == 'none': return position, None, None
        if (self.uint('vault', 'bucketTotalShares(uint256)', bucket) == 0 or
                self.uint('vault', 'poolBucket(bytes32)', position['pool_id']) != bucket or
                position['status'] == 'active' and position['lp_token_id'] == 0):
            raise RpcError('Review bucket custody differs')
        config = self.read('pools', 'get(bytes32)', position['pool_id'], count=14)
        if ('0x' + keccak256(bytes.fromhex(''.join(config[:5]))).hex() != position['pool_id'] or
                self.read('pools', 'accounting(bytes32)', position['pool_id'], count=14) != config or
                any(int(config[n], 16) not in (0, 1) for n in (5, 6)) or
                not 600 <= int(config[11], 16) <= 604800 or position['last_rebalance'] > self.stamp):
            raise RpcError('Review pool identity or timing differs')
        tokens = ['0x' + word[-40:] for word in config[:2]]
        if int(config[0], 16) != 0 or not 0 < int(config[1], 16) < 2**160:
            raise RpcError('Review requires actual native ETH and fixed ZZZ accounting')
        return position, config, tokens

    def market(self, position, config, bucket):
        from keeper.compound_policy import observe
        return observe(self.read, lambda target: self.k.rpc.call('eth_getCode', [target, 'latest']),
            contracts=self.k.contracts, code_hashes=self.k.config.get('code_hashes', {}), bucket=bucket)

    def harvest_custody(self, position):
        # Manager.collect checks owner and PoolKey, without a market/price read.
        self.pin('liquidity')
        manager = self.k.contracts['liquidity']
        module = '0x'+keccak256(b'ZZZLiquidityManager').hex()
        if (self.uint('liquidity','access()')!=int(self.k.contracts['access'],16) or
                self.uint('access','module(bytes32)',module)!=int(manager,16)):
            raise RpcError('Harvest Manager binding differs')
        posm = self.uint('liquidity','positionManager()')
        if not 0 < posm < 2**160: raise RpcError('Harvest position manager is malformed')
        posm = '0x'+f'{posm:040x}';lp = position['lp_token_id']
        owner = self.uint(posm,'ownerOf(uint256)',lp)
        if not 0 < owner < 2**160: raise RpcError('Harvest LP owner is malformed')
        physical = self.read(posm,'getPoolAndPositionInfo(uint256)',lp,count=6)
        key = [int(word,16) for word in physical[:5]]
        spacing = key[3]-2**256 if key[3]>=2**255 else key[3]
        if (any(key[n]>=2**160 for n in (0,1,4)) or key[2]>=2**24 or not -(2**23)<=spacing<2**23):
            raise RpcError('Harvest PoolKey ABI is malformed')
        pool = '0x'+keccak256(bytes.fromhex(''.join(physical[:5]))).hex()
        reasons = ([] if owner==int(self.k.contracts['vault'],16) else ['lp_owner_mismatch']) + (
            [] if pool==position['pool_id'] else ['lp_pool_identity_mismatch'])
        return {'allowed': not reasons, 'reasons': reasons, 'position_manager': posm,
            'owner': '0x'+f'{owner:040x}', 'pool_id': pool,
            'scope': 'Pinned Manager binding and PosM custody only; no slot0, range, price or earned-fee inference.'}

    def execution(self):
        # Request-local only: every reused observation has this one pinned hash.
        if self._execution is None:
            self._execution = (_attempt(lambda: self.k._lp_routing_snapshot(self.header), 'lp_execution_capability_unavailable')
                if self.k.lp_routing_version == 1 else {'available': False, 'value': None, 'reason': 'lp_execution_profile_unconfigured'})
        return self._execution

    def budget(self):
        if self._budget is None:
            target = self.k._compound_budget(3)
            if self.uint(target, 'access()') != int(self.k.contracts['access'], 16):
                raise RpcError('Review Budget controller differs')
            self._budget = target
        return self._budget

    def financial(self, config):
        def maintenance():
            budget = self.budget()
            loss = self.uint(budget, 'maintenanceLossBps()')
            if not 0 <= loss <= 1000: raise RpcError('Review maintenance loss is malformed')
            return {'budget': budget, 'runtime_code_hash': self.k.config['code_hashes']['idle_compounding_budget'],
                    'compound_capability_version': 3, 'maintenance_loss_bps': loss}
        execution = self.execution()
        quality = (execution['value']['metadata'].get('execution_quality') if execution['available'] else None)
        fee,width,trigger,deviation,slip = [int(config[n],16) for n in (2,7,8,9,10)]
        if (not 100 <= width <= 5000 or not 100 <= trigger < width or
                not 1 <= slip <= 1000 or not 1 <= deviation <= 500 or deviation >= width or
                not 0 <= fee <= 100000 or fee >= slip*100 or
                int(config[12],16)==0 or int(config[13],16)<int(config[12],16)):
            raise RpcError('Review pool financial policy is malformed')
        return {'pool_policy': {'max_slippage_bps': slip, 'max_spot_deviation_bps': deviation},
                'maintenance_policy': _attempt(maintenance, 'maintenance_loss_policy_unavailable'),
                'execution_quality': {'available': quality is not None, 'value': quality,
                    'reason': None if quality is not None else 'quality_profile_unconfigured_or_unavailable'},
                'post_deployment_idle_ceiling': {'bps': 500, 'source': 'fixed_source_rule_not_a_measured_margin'},
                'measured_margins': {'available': False, 'retained_usd': None, 'swap_margin_bps': None,
                    'aggregate_margin_bps': None, 'reason': 'Independent price/trace valuation was not measured by this report.'}}

    def schedule(self, row, item, key, interval):
        if not self.journal:
            return _set(row, 'unavailable', 'journal_unavailable')
        recorded = self.k.state['last'].get(key)
        last = 0 if recorded is None else recorded
        if type(last) is not int or last < 0 or last > self.stamp:
            return _set(row, 'unavailable', 'receipt_clock_invalid')
        row['checks']['local_interval'] = {'last_success_at': recorded, 'interval_seconds': interval,
            'worker_effective_last': last, 'worker_next_due_at': last+interval,
            'source': 'local_receipt_journal' if recorded is not None else 'no_success_record_worker_default_zero'}
        return _set(row, 'not_due', 'local_interval') if self.stamp < last+interval else _set(row, 'observed_eligible', 'evaluated_view_prerequisites_satisfied')

    def simulate_action(self, row, item, bucket):
        if not self.simulate: return
        required_caps = ('max_gas_limit', 'max_gas_price_wei', 'max_transaction_cost_wei', 'max_daily_cost_wei')
        if any(self.k.config.get(key) is None for key in required_caps):
            row['checks']['gas'] = {'available': False, 'value': None, 'reason': 'gas_caps_unconfigured'}
            _set(row, 'unconfigured', 'gas_caps_unconfigured'); return
        action = row['operation']
        target, signature, args = ('vault', 'collectFees(uint256,uint256)', (bucket, self.stamp+180))
        if action != 'harvest':
            minimum = integer(item.get('minimum_liquidity', 1), 'minimum_liquidity', minimum=1)
            if minimum >= 2**128: raise ValueError('Invalid minimum liquidity')
            target = 'vault' if action == 'rebalance' else 'compounder'
            signature = 'rebalance(uint256,uint128,uint256)' if action == 'rebalance' else 'compound(uint256,uint128,uint256)'
            args = (bucket, minimum, self.stamp+180)
        self.pin(target)
        tx = {'from': self.k.sender, 'to': self.k.contracts[target], 'value': '0x0',
              'data': self.k._calldata(signature, *args), 'gas': hex(integer(self.k.config['max_gas_limit'], 'max_gas_limit', minimum=1))}
        row['simulation'] = {'state': 'unavailable', 'reason': 'simulation_failed_unclassified',
            'transaction': tx, 'block': self.k.rpc.block, 'scope': 'Discarded fixed typed call; no nonce, signature, state override or inclusion guarantee.'}
        try:
            result = self.k.rpc.call('eth_call', [tx, self.k.rpc.block])
            if result != '0x': raise RpcError('Unexpected operation simulation ABI')
        except WorkLimit: raise
        except (RpcError, ValueError, TypeError):
            _set(row, 'unavailable', 'simulation_failed_unclassified'); return
        row['simulation'].update(state='succeeded', reason=None)
        def gas():
            estimate = rpc_quantity(self.k.rpc.call('eth_estimateGas', [tx, self.k.rpc.block]), 'review gas', minimum=1)
            price = rpc_quantity(self.k.rpc.call('eth_gasPrice', []), 'review gas price')
            padded = (estimate*125+99)//100
            allowance = integer(self.k.config.get('l1_fee_allowance_wei', 0), 'l1_fee_allowance_wei')
            return dict(estimated_units=estimate, padded_units=padded, price_wei=price,
                        l1_fee_allowance_wei=allowance, maximum_estimated_cost_wei=padded*price+allowance,
                        price_scope='current_RPC_suggestion_not_hash_pinned', gas_scope='estimate_not_actual_paid_fee')
        observed = _attempt(gas, 'gas_estimate_or_price_unavailable')
        row['checks']['gas'] = observed
        if not observed['available']:
            _set(row, 'unavailable', observed['reason']); return
        g = observed['value']; cfg = self.k.config
        caps = {name: integer(cfg[name], name, minimum=1) for name in
                ('max_gas_limit', 'max_gas_price_wei', 'max_transaction_cost_wei', 'max_daily_cost_wei')}
        g['configured_caps'] = caps
        blockers = [name for name, value in (('gas_limit_cap', g['padded_units'] > caps['max_gas_limit']),
            ('gas_price_cap', g['price_wei'] > caps['max_gas_price_wei']),
            ('transaction_cost_cap', g['maximum_estimated_cost_wei'] > caps['max_transaction_cost_wei'])) if value]
        funding = _attempt(lambda: rpc_quantity(self.k.rpc.call('eth_getBalance',
            [self.k.sender,self.k.rpc.block]), 'review native gas balance'), 'native_gas_balance_unavailable')
        row['checks']['native_gas_funding'] = {'available': funding['available'],
            'balance_wei': funding['value'], 'required_estimated_max_wei': g['maximum_estimated_cost_wei'],
            'reason': funding['reason'], 'scope': 'Pinned native gas funding only; no key, transfer or asset ledger.'}
        if funding['available'] and funding['value'] < g['maximum_estimated_cost_wei']:
            blockers.append('insufficient_native_gas_balance')
        day = dt.datetime.fromtimestamp(self.stamp, dt.timezone.utc).date().isoformat()
        recorded_spent = self.k.state['spent'].get(day) if self.journal else None
        spent = self.k.state['spent'].get(day, 0) if self.journal else None
        g['journal_spent_today_wei'] = spent
        g['journal_spent_source'] = ('recorded' if recorded_spent is not None else
            'no_day_entry_worker_default_zero' if self.journal else 'unavailable')
        if spent is not None and int(spent)+g['maximum_estimated_cost_wei'] > caps['max_daily_cost_wei']:
            blockers.append('daily_cost_cap')
        fee_unconfigured = (self.k.fee_policy == 'unverified' or
            self.k.fee_policy == 'separate_l1_fee' and self.k.config.get('l1_fee_allowance_wei') is None)
        fee_reason = 'network_fee_semantics_unverified' if self.k.fee_policy == 'unverified' else 'l1_fee_allowance_unconfigured'
        row['checks']['network_fee_policy'] = {'state': 'unconfigured' if fee_unconfigured else 'configured',
            'receipt_fee_policy': self.k.fee_policy, 'reason': fee_reason if fee_unconfigured else None}
        if blockers: row.update(state='blocked', reasons=blockers+([fee_reason] if fee_unconfigured else []))
        elif fee_unconfigured: _set(row, 'unconfigured', fee_reason)
        elif not funding['available']: _set(row, 'unavailable', funding['reason'])
        elif spent is None: _set(row, 'unavailable', 'daily_spend_unavailable')
        elif row['state'] == 'observed_eligible': _set(row, 'simulated', 'typed_simulation_and_estimate_succeeded')

    def operations(self, bucket, controls):
        rows = [_row(action, bucket) for action in ACTIONS]
        reset = self.k.state.get(CONFIRMATION_RESETS,{}).get(str(bucket),False) if self.journal else None
        clear = self.k.state.get(CONFIRMATION_CLEARS,{}).get(str(bucket)) if self.journal else None
        local = {'available': self.journal, 'reset_required': reset,
            'clear_ack_present': clear is not None if self.journal else None,
            'awaiting_healthy_read': clear['awaiting_healthy_read'] if clear is not None else None,
            'scope': 'Validated journal status only; no reset, acknowledgement adoption or future worker time is inferred.'}
        def complete():
            for row in rows:
                row['checks']['local_confirmation_coordination'] = local
                if row['operation']!='harvest' and reset is True:
                    row['checks']['pre_service_reset'] = {'state':row['state'],'reasons':list(row['reasons']),
                        'scope':'Evaluated view and interval status before the saved worker reset gate.'}
                    prior = list(row['reasons']) if row['state']=='blocked' else []
                    row.update(state='blocked',reasons=prior+['confirmation_reset_required'])
            return rows
        item = {**self.k.maintenance, **self.k.overrides.get(str(bucket), {})}
        data = _attempt(lambda: self.bucket(bucket), 'bucket_or_pool_unavailable')
        for row in rows: row['checks']['bucket'] = data
        if not data['available']: return complete()
        position, config, tokens = data['value']
        if position['status'] != 'active':
            for row in rows:_set(row,'not_needed','no_active_lp')
            return complete()
        market = _attempt(lambda: self.market(position, config, bucket), 'physical_range_unavailable')
        if market['available'] and any(market['value'].get(key)!=position[key]
                for key in ('pool_id','lp_token_id','last_rebalance')):
            # A proven same-hash contradiction is not an optional market outage.
            raise RpcError('Physical observation contradicts the selected bucket snapshot')
        custody = _attempt(lambda: self.harvest_custody(position), 'harvest_custody_unavailable')
        financial = _attempt(lambda: self.financial(config), 'financial_policy_unavailable')
        for row in rows:
            action = row['operation']
            if action != 'harvest': row['checks']['financial_limits'] = financial
            if action in ('compound', 'harvest') and item.get(action, True) is False:
                _set(row, 'unconfigured', 'job_disabled'); continue
            row['checks']['controls'] = controls
            if not controls['available']:
                _set(row, 'unavailable', controls['reason']); continue
            c = controls['value']
            # collectFees is permissionless and remains available during the
            # preparation announcement while canonicalState is still operating.
            required = ('pending_recovery', 'paused', 'canonical_locked', 'lp_exit_started', 'not_sealed') + (
                ('preparation_active',) if action != 'harvest' else ())
            blockers = [key for key in required if c[key] is True]
            authorization = c['keeper_authorization']
            row['checks']['authority'] = {'contract_permission': 'permissionless' if action == 'harvest' else 'keeper',
                'contract_authorized': True if action == 'harvest' else authorization['value'],
                'worker_requires_keeper': True, 'worker_authorization': authorization}
            if not authorization['available']:
                _set(row, 'unavailable', authorization['reason']); continue
            if not authorization['value']: blockers.append('worker_sender_not_authorized')
            if blockers: row.update(state='blocked', reasons=blockers); continue
            if action == 'harvest':
                row['checks']['physical_custody'] = custody
                if not custody['available']: _set(row,'unavailable',custody['reason']); continue
                if not custody['value']['allowed']:
                    row.update(state='blocked',reasons=custody['value']['reasons']); continue
                interval = integer(item.get('harvest_interval_seconds', 3600), 'harvest_interval_seconds', minimum=1)
                self.schedule(row, item, f'harvest:{bucket}', interval)
                if row['state'] == 'not_due': continue
            else:
                row['checks']['physical_range'] = market
                if action == 'rebalance':
                    earliest = position['last_rebalance']+int(config[11], 16)
                    row['checks']['hard_interval'] = {'last_rebalance_at': position['last_rebalance'], 'earliest_at': earliest}
                if not market['available']:
                    _set(row, 'not_due' if action == 'rebalance' and self.stamp < earliest else 'unavailable',
                         'hard_rebalance_interval' if action == 'rebalance' and self.stamp < earliest else market['reason']); continue
                if not int(config[6], 16):
                    _set(row, 'blocked', 'pool_operations_disabled'); continue
                m = market['value']
                if action == 'rebalance':
                    needed = not m['in_range'] or m['range_update_pending']
                    row['checks']['raw_market_condition'] = {'needed': needed, 'source': 'physical_range_and_explicit_width'}
                    if not needed: _set(row, 'not_needed', 'physical_range_inside_and_no_width_change'); continue
                    if self.stamp < earliest: _set(row, 'not_due', 'hard_rebalance_interval'); continue
                    raw = _attempt(lambda: self.flag('strategy', 'needsRebalance(uint256)', bucket), 'raw_condition_unavailable')
                    row['checks']['onchain_raw_condition'] = raw
                    if not raw['available']: _set(row, 'unavailable', raw['reason']); continue
                    if raw['value'] is not True: _set(row, 'unavailable', 'raw_condition_contradicts_observed_market'); continue
                    if self.k.rebalance_confirmation.version in (1, 2):
                        confirmation = _attempt(lambda: self.k.rebalance_confirmation.status(bucket), 'confirmation_unavailable')
                        row['checks']['confirmation'] = confirmation
                        if not confirmation['available']: _set(row, 'unavailable', confirmation['reason']); continue
                        v = confirmation['value']
                        if not v['manual'] and v['maximum_gap_seconds'] == 0:
                            _set(row, 'unconfigured', 'confirmation_stopped'); continue
                        if not v['ready']:
                            reason = ('reference_disagreement' if v.get('reference_exit_required') and v.get('physical_exit_side') != v.get('reference_exit_side') else
                                'confirmation_not_started' if v['first_seen'] == 0 else
                                'confirmation_identity_changed' if v['identity'] != v['observation_identity'] or v['side'] != v['observation_side'] else
                                'confirmation_observation_stale' if self.stamp-v['last_seen'] > v['maximum_gap_seconds'] else 'confirmation_accumulating')
                            _set(row, 'blocked' if reason in ('reference_disagreement','confirmation_identity_changed','confirmation_observation_stale') else 'not_due', reason); continue
                    _set(row, 'observed_eligible', 'evaluated_view_prerequisites_satisfied')
                else:
                    if not m['allowed']:
                        _set(row, 'blocked', m['status']); continue
                    reserves = _attempt(lambda: [self.uint('fees', 'compoundBalance(uint256,address)', bucket, t) for t in tokens], 'compound_reserves_unavailable')
                    row['checks']['compound_reserves'] = reserves
                    thresholds = item.get('compound_thresholds')
                    if thresholds is None or any(t not in thresholds for t in tokens):
                        _set(row, 'unconfigured', 'currency_thresholds_missing'); continue
                    if not reserves['available']: _set(row, 'unavailable', reserves['reason']); continue
                    amounts = [a+(position['idle'+str(n)] if item.get('compound_idle', False) else 0) for n, a in enumerate(reserves['value'])]
                    row['checks']['compound_trigger'] = {'tokens': tokens, 'amounts': list(map(str, amounts)), 'thresholds': {t: str(thresholds[t]) for t in tokens}}
                    if not any(a >= integer(thresholds[t], 'threshold', minimum=1) for t, a in zip(tokens, amounts)):
                        _set(row, 'not_needed', 'below_currency_thresholds'); continue
                    interval = item.get('compound_interval_seconds', 0)
                    self.schedule(row, item, f'compound:{bucket}', integer(interval, 'compound_interval_seconds'))
                    if row['state'] == 'not_due': continue
                    def clock():
                        budget = self.budget()
                        last = self.uint(budget, 'lastCompound(uint256)', bucket)
                        seconds = self.uint(budget, 'compoundInterval(bytes32)', position['pool_id'])
                        if last >= 2**64 or last > self.stamp or not 600 <= seconds <= 604800:
                            raise RpcError('Invalid shared compound interval')
                        return {'last_compound_at': last, 'interval_seconds': seconds,
                                'earliest_at': max(last, position['last_rebalance'])+seconds}
                    chain_clock = _attempt(clock, 'onchain_compound_interval_unavailable')
                    row['checks']['onchain_compound_interval'] = chain_clock
                    if not chain_clock['available']: _set(row, 'unavailable', chain_clock['reason']); continue
                    if self.stamp < chain_clock['value']['earliest_at']: _set(row, 'not_due', 'onchain_compound_interval'); continue
                    ready = _attempt(lambda: self.k._compound_ready(bucket), 'compound_guard_unavailable')
                    row['checks']['onchain_compound_ready'] = ready
                    if not ready['available']: _set(row, 'unavailable', ready['reason']); continue
                    if not ready['value']: _set(row, 'blocked', 'onchain_compound_not_ready_unclassified'); continue
            if action != 'harvest':
                if not financial['available'] or not financial['value']['maintenance_policy']['available']:
                    _set(row, 'unavailable', 'financial_policy_unavailable'); continue
                execution = self.execution()
                row['checks']['lp_execution'] = execution
                if not execution['available']:
                    _set(row, 'unconfigured' if self.k.lp_routing_version == 0 else 'unavailable', execution['reason']); continue
            if not self.journal:
                _set(row, 'unavailable', 'journal_unavailable'); continue
            if action!='harvest' and reset is True:
                row['simulation']={'state':'not_requested','reason':'confirmation_reset_required'}
                continue
            simulated = _attempt(lambda: self.simulate_action(row, item, bucket), 'typed_simulation_or_caps_unavailable')
            if not simulated['available']: _set(row, 'unavailable', simulated['reason'])
        return complete()


def review(config, buckets, *, rpc=None, simulate=False, now=None):
    """At most four explicit bucket IDs; no journal creation or worker scheduling."""
    if (not isinstance(buckets, (list, tuple)) or not 1 <= len(buckets) <= MAX_BUCKETS or
            any(type(b) is not int or not 0 < b < 2**256 for b in buckets) or len(set(buckets)) != len(buckets)):
        raise ValueError('Select one through four distinct uint256 buckets')
    if type(simulate) is not bool: raise ValueError('Simulation selection must be boolean')
    path = Path(config.get('state_path', 'var/keeper.json'))
    original = path.read_bytes() if path.is_file() else None
    keeper = ReadOnlyKeeper(copy.deepcopy(config), live=False, rpc=rpc)
    if (path.read_bytes() if path.is_file() else None) != original:
        raise RpcError('Journal changed during review construction')
    base = dict(schema=1, kind='keeper_operation_review', read_only=True, production_approved=False,
        profile={name: getattr(keeper, name) for name in ('accounting_version', 'maintenance_policy_version', 'lp_routing_version', 'execution_quality_version')},
        configuration_sha256=keeper.configuration_sha256,
        configuration_reviewed_for_live_use=config.get('reviewed_for_live_use') is True,
        journal={'available': original is not None, 'sha256': hashlib.sha256(original).hexdigest() if original is not None else None},
        health_file_used=False, other_operations=[{'operation': name, 'state': 'unsupported', 'reason': 'outside_this_report_scope'} for name in
            ('lp_conversion', 'royalty_conversion', 'buyback', 'metadata', 'principal_delivery', 'claims', 'activation')],
        limitations=['Selected LP operations only; no signing, nonce reconciliation, schedule mutation or execution approval.',
            'Unknown simulation/estimate failures never identify a specific price, route, slippage or selector cause.',
            'Work budget is cooperative; standalone DNS/socket stalls still need external supervision.'])
    base['profile'].update(fee_intake_version=keeper.fee_intake_version,
                           rebalance_confirmation_version=keeper.rebalance_confirmation.version)
    if keeper.accounting_version != 4 or keeper.maintenance_policy_version != 2:
        return dict(base, ok=True, provenance=None, operations=[_set(_row(a, b), 'unsupported', 'explicit_historical_profile') for b in buckets for a in ACTIONS])
    clock = time.time if now is None else now
    with request_scope(Budget(seconds=MAX_SECONDS, calls=MAX_CALLS, posts=1024)):
        raw = BudgetedRPC(rpc or Rpc(config['rpc_urls'], keeper.chain, timeout=5, retries=2))
        if raw.call('eth_chainId', []) != keeper.chain: raise RpcError('Review chain differs')
        header = raw.call('eth_getBlockByNumber', ['latest', False]); anchor = _header(header)
        if not -30 <= clock()-anchor['timestamp'] <= 600: raise RpcError('Review snapshot is stale or future')
        keeper.rpc = PinnedReads(raw, header)
        report = Review(keeper, header, original is not None, simulate=simulate)
        def controls():
            for role in ('access', 'vault', 'strategy', 'pools', 'fees'): report.pin(role)
            keeper._validate_accounting_version()
            canonical=report.uint('access','canonicalState()')
            if not 0<=canonical<5: raise RpcError('Unknown canonical lifecycle state')
            return dict(pending_recovery=bool(keeper.state.get('pending')) if original is not None else None,
                paused=report.flag('access', 'paused()'), preparation_active=report.flag('access', 'preparationActive()'),
                canonical_locked=canonical != 0,
                lp_exit_started=keeper.lp_exit_started(),
                keeper_authorization=_attempt(lambda: report.flag('access', 'keeperAuthorized(address)', keeper.sender), 'keeper_authorization_unavailable'),
                not_sealed=not report.flag('access', 'isSealed()'))
        observed_controls = _attempt(controls, 'core_controls_or_profile_unavailable')
        operations = [row for bucket in buckets for row in report.operations(bucket, observed_controls)]
        if _header(raw.call('eth_getBlockByNumber', [hex(anchor['number']), False])) != anchor or raw.call('eth_chainId', []) != keeper.chain:
            raise RpcError('Review canonical anchor changed')
        if not -30 <= clock()-anchor['timestamp'] <= 600: raise RpcError('Review snapshot expired')
        if (path.read_bytes() if path.is_file() else None) != original: raise RpcError('Journal changed during review')
        return dict(base, ok=True, provenance={**anchor, 'finality': 'latest_canonical_only', 'eip1898_require_canonical': True},
                    operations=operations, work_budget={'seconds': MAX_SECONDS, 'rpc_calls': MAX_CALLS, 'posts': 1024})
