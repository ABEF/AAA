"""Bounded original-currency claim planning; never signs or queues transactions.

Only the returned next batch is a draft. Refused or unassessed entries remain in
the selection, and must be planned again against confirmed state after a claim.
An opaque EVM refusal identifies no faulty token, financial inequality or payout.
"""
from __future__ import annotations

import copy
import json
import re

from frontend_api.service import ProjectionError, _bool, _quantity
from frontend_api.transactions import (DRAFT_LIFETIME, MAX_CLAIMS,
    MAX_SNAPSHOT_AGE, SIMULATION_GAS_LIMIT, TransactionInputError, _parse)
from zzz_ops.abi import keccak256
from zzz_ops.errors import RemoteRPCError, RpcError, WorkLimit
from zzz_ops.work_budget import bounded_request, checkpoint, expire_at

MAX_TRIALS = 10  # One additional, fresh preparation is reserved for publication.
MAX_METADATA = 512

# Successful identity/admission reads at ONE canonical block only. These
# settings may change across blocks; nothing is cached across requests/blocks.
# Ownership, balances, lifecycle, heads, simulations, estimates and fee prices
# are deliberately absent. The ordinary preparer rereads their final values.
_IDENTITY = (
    'access()', 'nft()', 'royalties()', 'royaltyRewards()', 'claimRouter()',
    'canonicalChainId()', 'ACCOUNTING_VERSION()', 'GOVERNANCE_VERSION()',
    'CUSTODY_VERSION()', 'SCHEMA()', 'migrationBudget()', 'vault()',
    'portfolioPolicy()', 'strategy()', 'rebalanceConfirmation()',
    'balancingRouter()', 'liquidityManager()', 'balanceMath()', 'balancer()',
    'poolManager()', 'stateView()', 'positionOperator()', 'positionManager()',
    'permit2()', 'protocolPolicy()', 'MAINTENANCE_POLICY_VERSION()',
    'REBALANCE_CONFIRMATION_VERSION()', 'IDLE_COMPOUNDING_VERSION()',
    'EMERGENCY_REBALANCE_VERSION()', 'PORTFOLIO_VERSION()',
    'PROTOCOL_POLICY_VERSION()', 'LP_ROUTING_VERSION()',
    'LP_BALANCE_MATH_VERSION()', 'LP_POSITION_EXECUTOR_VERSION()',
    'assetCount()', 'assets(uint256)', 'decimals()', 'module(bytes32)',
)
_SELECTORS = {'0x'+keccak256(s.encode()).hex()[:8]: 74 if '(' in s and
              not s.endswith('()') else 10 for s in _IDENTITY}


def _opaque_execution(error, method):
    """Recognize sanitized execution refusal, never raw provider message text.

    -32000 can describe several execution refusals, so its cause remains
    unclassified. A successful smaller/final simulation supplies the evidence.
    Transport, rate, parameter, internal and missing-block errors are not probes.
    """
    seen, found = set(), False
    for _ in range(8):
        if error is None:
            return found
        if id(error) in seen:
            return False
        seen.add(id(error))
        if isinstance(error, WorkLimit):
            raise error
        if isinstance(error, (OSError, TimeoutError)):
            return False
        if isinstance(error, RemoteRPCError):
            if error.method != method or error.reason != 'unclassified' or error.code not in (3, -32000):
                return False
            found = True
        error = error.__cause__
    return False


def _bounded_quantity(value):
    if not isinstance(value, str) or len(value) > 66:
        return None
    try:
        return _quantity(value)
    except ProjectionError:
        return None


class _SnapshotReads:
    def __init__(self, rpc, block, targets):
        self.rpc, self.block, self.targets = rpc, block, targets
        self.cache, self.failures, self.trial = {}, [], {}
        self.global_error = None

    def assert_available(self):
        if self.global_error is not None:
            raise ProjectionError('Claim planning dependency is unavailable') from self.global_error

    def _cacheable(self, method, params):
        if len(params) != 2 or params[-1] != self.block:
            return False
        if method == 'eth_getCode':
            return params[0] in self.targets
        if method != 'eth_call' or not isinstance(params[0], dict) or set(params[0]) != {'to', 'data'}:
            return False
        tx = params[0]; data = tx.get('data')
        return (tx.get('to') in self.targets and isinstance(data, str) and
                _SELECTORS.get(data[:10]) == len(data))

    def call(self, method, params=None):
        checkpoint()
        params = params or []
        cacheable = self._cacheable(method, params)
        key = (method, json.dumps(params, sort_keys=True, separators=(',', ':')))
        if cacheable and key in self.cache:
            return copy.deepcopy(self.cache[key])
        execution = method == 'eth_estimateGas' or (method == 'eth_call' and
            params and isinstance(params[0], dict) and 'from' in params[0])
        try:
            value = self.rpc.call(method, params)
        except RpcError as error:
            self.failures.append((method, execution, error))
            if not _opaque_execution(error, method):
                self.global_error = error
            if execution:
                self.trial['error'] = (method, error)
            raise
        if method in ('eth_estimateGas', 'eth_gasPrice', 'eth_getBalance'):
            self.trial[method] = _bounded_quantity(value)
        if cacheable and len(self.cache) < MAX_METADATA and isinstance(value, str):
            valid = (re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', value) if method == 'eth_getCode'
                     else re.fullmatch(r'0x[0-9a-fA-F]{64}', value))
            if valid and len(value) <= 128*1024:
                self.cache[key] = value
        checkpoint()
        return value

    def eth_call(self, target, data, sender=None, block='latest'):
        tx = {'to': target, 'data': data}
        if sender:
            tx['from'] = sender
        return self.call('eth_call', [tx, block])


def _budget_refusal(reads, config):
    estimate = reads.trial.get('eth_estimateGas')
    if estimate is None or estimate < 21000:
        return False
    if estimate > SIMULATION_GAS_LIMIT:
        return True
    price = reads.trial.get('eth_gasPrice')
    if price is None or not 0 < price <= config.max_price:
        return False
    cost = min(SIMULATION_GAS_LIMIT, (estimate*120+99)//100)*price
    return cost > config.max_fee or (reads.trial.get('eth_getBalance') is not None and
                                    reads.trial['eth_getBalance'] < cost)


class ClaimPlanner:
    def __init__(self, transactions):
        self.transactions = transactions

    @bounded_request
    def plan(self, payload):
        action, owner, claims = _parse(payload)
        if action != 'claim':
            raise TransactionInputError('Claim planning requires an explicit claim selection')
        original = self.transactions.projection
        header, head, block = original._snapshot()
        self.transactions._fresh(header)
        expire_at(header['timestamp']+min(original.max_age, MAX_SNAPSHOT_AGE), original.clock)
        p = copy.copy(original)
        reads = _SnapshotReads(original.rpc, block,
            {c.address for c in p.contracts.values()} | set(p.assets))
        p.rpc = reads
        p._snapshot = lambda: (copy.deepcopy(header), head, copy.deepcopy(block))
        lifecycle = p._verify_deployment(block)
        health = {}
        lp_assets, royalty_assets = p._admitted(block, asset_health=health)
        # The ordinary read adapter isolates optional metadata faults. A known
        # transport/global refusal still invalidates the whole plan, not a token.
        for method, _execution, error in reads.failures:
            if not _opaque_execution(error, method):
                raise ProjectionError('Claim planning dependency is unavailable') from error
        opening = True
        schema = getattr(p.royalty_reporting, 'schema', 0)
        if schema in (4, 5) and any(c.royalty for c in claims):
            if p._uint('royalties', 'ROYALTY_SETTLEMENT_VERSION()', block=block) != schema-1:
                raise ProjectionError('Claim planning royalty profile differs')
            opening = _bool(p._call(p.contracts['royalties'].address, 'royaltiesOpen()', block=block)[0])

        entries, ownership, eligible = [], {}, []
        for index, claim in enumerate(claims):
            checkpoint()
            row = dict(selection_index=index, token_id=str(claim.token_id), asset=claim.asset,
                royalty=claim.royalty, status='unassessed', reason=None, view_raw=None)
            entries.append(row)
            if claim.asset not in (royalty_assets if claim.royalty else lp_assets):
                row.update(status='blocked', reason='asset_not_admitted_to_ledger'); continue
            descriptor = p.assets[claim.asset]
            row.update(symbol=descriptor.symbol, decimals=descriptor.decimals)
            if not health[claim.asset]:
                row.update(status='unavailable', reason='currency_verification_unavailable'); continue
            if claim.token_id not in ownership:
                ordinal = p._uint('nft', 'mintOrdinalOf(uint256)', claim.token_id, block=block)
                if ordinal == 0:
                    ownership[claim.token_id] = 'nft_not_minted'
                else:
                    if ordinal > 1000 or p._uint('nft', 'tokenAtOrdinal(uint256)', ordinal, block=block) != claim.token_id:
                        raise ProjectionError('Claim planning NFT identity is inconsistent')
                    if p._addr('nft', 'ownerOf(uint256)', claim.token_id, block=block) != owner:
                        ownership[claim.token_id] = 'wallet_not_current_owner'
                    else:
                        weight = p._uint('royalties', 'weightOf(uint256)', claim.token_id, block=block) if p.accounting_version in (3,4,5,6) else None
                        if weight is not None and weight > 3:
                            raise ProjectionError('Claim planning activation weight is inconsistent')
                        ownership[claim.token_id] = weight
            state = ownership[claim.token_id]
            if isinstance(state, str):
                row.update(status='blocked', reason=state); continue
            if claim.royalty and not opening:
                row.update(status='blocked', reason='royalty_window_not_open'); continue
            try:
                amount = p._uint('royalties' if claim.royalty else 'rewards', 'claimable(uint256,address)',
                                 claim.token_id, claim.asset, block=block)
            except WorkLimit:
                raise
            except RpcError as error:
                if not _opaque_execution(error, 'eth_call'):
                    raise
                row.update(status='unavailable', reason='claim_view_execution_refused_unclassified'); continue
            row['view_raw'] = str(amount)
            if amount == 0:
                row.update(status='zero', reason='no_claimable_balance_at_snapshot'); continue
            if state == 0:
                raise ProjectionError('Inactive NFT has a funded reward entitlement')
            row.update(status='pending', reason='requires_simulation')
            eligible.append(index)

        prepared = copy.copy(self.transactions)
        prepared.projection = p
        attempts, best = [], []
        low, high, size = 1, len(eligible), len(eligible)
        while eligible and low <= high and len(attempts) < MAX_TRIALS:
            selected = eligible[:size]
            reads.trial = {}
            request = dict(action='claim', wallet=owner,
                claims=[dict(token_id=entries[i]['token_id'], asset=entries[i]['asset'], royalty=entries[i]['royalty']) for i in selected])
            try:
                prepared.prepare(request)
            except WorkLimit:
                raise
            except (RpcError, TransactionInputError) as error:
                reads.assert_available()
                execution_error = reads.trial.get('error')
                opaque = execution_error is not None and _opaque_execution(execution_error[1], execution_error[0])
                resource = _budget_refusal(reads, prepared.config)
                if not opaque and not resource:
                    raise
                reason = 'execution_refused_unclassified' if opaque else 'reviewed_execution_budget_exceeded'
                attempts.append(dict(selection_indices=selected, outcome='unresolved' if opaque else 'over_budget', reason=reason))
                high = size-1
                if size == 1:
                    entries[selected[0]].update(status='unavailable' if opaque else 'blocked', reason=reason)
                    eligible = eligible[1:]
                    low, high, best = 1, len(eligible), []
            else:
                reads.assert_available()
                attempts.append(dict(selection_indices=selected, outcome='simulated'))
                best, low = selected, size+1
            size = (low+high+1)//2

        draft = None
        if best:
            # Revalidate the ONLY published batch after all failed trials. Owners,
            # balances, lifecycle, canonicality, expiry and fee reads are fresh.
            draft = prepared.prepare(dict(action='claim', wallet=owner,
                claims=[dict(token_id=entries[i]['token_id'], asset=entries[i]['asset'], royalty=entries[i]['royalty']) for i in best]))
            reads.assert_available()
            for index in best:
                entries[index].update(status='in_next_batch', reason='fresh_exact_batch_simulation_succeeded')
        for index in eligible:
            if index not in best:
                entries[index].update(status='unassessed', reason='replan_after_confirmation' if best else 'planning_attempt_limit')
        p._finish(header)
        now = self.transactions._fresh(header)
        expires = draft['expires_at'] if draft else min(now+DRAFT_LIFETIME, header['timestamp']+min(p.max_age,MAX_SNAPSHOT_AGE))
        if expires <= now:
            raise ProjectionError('Claim plan expires before publication')
        remaining = [dict(token_id=r['token_id'],asset=r['asset'],royalty=r['royalty'],
            selection_index=r['selection_index'],status=r['status'],reason=r['reason']) for r in entries if r['status'] not in ('zero','in_next_batch')]
        return dict(schema=1,kind='unsigned_claim_plan',wallet=owner,chain_id=p.chain,
            next_batch=draft,entries=entries,remaining_claims=remaining,
            prepared_at=now,expires_at=expires,lifecycle=lifecycle,
            planning=dict(maximum_selection=MAX_CLAIMS,maximum_trials=MAX_TRIALS,
                trial_count=len(attempts),attempts=attempts,final_batch_revalidated=draft is not None,
                batch_optimality_guaranteed=False,simulation_gas_cap=str(SIMULATION_GAS_LIMIT)),
            provenance=dict(block_number=header['number'],block_hash=header['hash'],
                block_timestamp=header['timestamp'],observed_head=head,configuration_sha256=p.identity,
                transaction_configuration_sha256=self.transactions.config.identity,
                accounting_version=p.accounting_version,custody_version=p.custody_version,
                royalty_reporting_schema=schema or None,
                eip1898_require_canonical=True,protocol_finalized=False),
            replan_after_confirmation=True,automatic_submission=False,production_approved=False,
            scope='Only next_batch is an executable unsigned review. Remaining entries are not transactions or diagnosed token faults. '
                  'After confirmation, replan remaining claims against new confirmed ownership and balances. '
                  'No signing, broadcasting, resend, queued future transaction or cross-currency sum is performed.')
