"""Export real fresh7 DTO handlers against explicit synthetic offline RPC fixtures.

This is a local consumer compatibility artifact, not EVM execution, live data,
provider qualification, signing, or permission to configure a running service.
Existing historical exporters and fixtures retain their original profiles.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from frontend_api.service import Projection, ZERO
from frontend_api.transactions import Transactions, CLAIM_SIGNATURE
from tests_python.test_exact_lp_profile7 import Fresh7API
from tests_python.test_earnings_checkpoint_v2 import Checkpoint2APITests
from tests_python.test_frontend_api import addr, words
from tests_python.test_frontend_transactions import transaction_config
from tests_python.test_native_backend_boundary import native_data
from zzz_ops.abi import keccak256, decode_words, calldata


PROFILE = dict(source_profile=9, accounting_version=7, lp_allocation_version=1,
    custody_version=5, protocol_policy_version=1, governance_version=2,
    fee_intake_version=1, portfolio_version=2, maintenance_policy_version=3,
    rebalance_confirmation_version=3, idle_compounding_version=4,
    lp_routing_version=2, execution_quality_version=1, emergency_version=2,
    pricing_version=2, routing_version=3, review_policy_version=2,
    royalty_settlement_version=4, royalty_reporting_schema=5,
    canonical_domain='ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9')


class RecordedRPC:
    """Record every actual producer request and exact synthetic reply."""
    def __init__(self, inner):
        self.inner = inner
        self.rows = []

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def call(self, method, params=None):
        if any(word in method.lower() for word in ('send', 'sign', 'anvil')):
            raise AssertionError('Exporter may only read or simulate unsigned calls')
        params = [] if params is None else params
        value = self.inner.call(method, params)
        self.rows.append(dict(method=method, params=copy.deepcopy(params), result=copy.deepcopy(value)))
        return value


class SyntheticClaimRPC:
    """Explicit deterministic claim execution/fee fixture; no execution claim.

    Funded balances come from the same strict getter transcript as Projection.
    Only the reviewed router and ABI are recognized; no generic return value.
    """
    def __init__(self, fresh):
        self.fresh = fresh

    def call(self, method, params):
        f = self.fresh
        block = dict(blockHash=f.rpc.hash, requireCanonical=True)
        if method == 'eth_getBlockByHash':
            if params != [f.rpc.hash, False]:
                raise AssertionError('Gas policy must use the monetary block hash')
            return dict(number=hex(f.rpc.head-f.p.confirmations+1), hash=f.rpc.hash,
                        timestamp=hex(f.rpc.header_timestamp), gasLimit=hex(40_000_000))
        if method in ('eth_estimateGas', 'eth_getBalance'):
            if params[-1] != block:
                raise AssertionError('Unsigned gas/balance read must be canonical')
            return hex(100_000 if method == 'eth_estimateGas' else 10**20)
        if method == 'eth_gasPrice':
            return hex(10**9)
        if method == 'eth_call' and 'from' in params[0]:
            tx = params[0]
            prefix = '0x'+keccak256(CLAIM_SIGNATURE.encode()).hex()[:8]
            if params[1] != block or tx['to'] != f.c['claim_router'] or not tx['data'].startswith(prefix):
                raise AssertionError('Only the exact reviewed canonical claim batch is simulated')
            raw = decode_words('0x'+tx['data'][10:])
            count = int(raw[1], 16)
            if int(raw[0], 16) != 32 or not 1 <= count <= 32 or len(raw) != 2+3*count:
                raise AssertionError('Noncanonical synthetic claim payload')
            result = []
            for offset in range(2, len(raw), 3):
                identifier, asset_word, royalty = map(lambda word: int(word, 16), raw[offset:offset+3])
                if royalty not in (0, 1):
                    raise AssertionError('Noncanonical royalty flag')
                asset = '0x'+f'{asset_word:040x}'
                owner = f.rpc.call('eth_call', [dict(to=f.c['nft'], data=native_data('ownerOf(uint256)', identifier)), block])
                if int(owner, 16) != int(tx['from'], 16):
                    raise AssertionError('Synthetic claim owner differs')
                role = 'royalties' if royalty else 'rewards'
                balance = f.rpc.call('eth_call', [dict(to=f.c[role],
                    data=native_data('claimable(uint256,address)', identifier, asset)), block])
                result.append(int(balance, 16))
            return words(32, count, *result)
        return f.rpc.call(method, params)


def source_hashes():
    names = ('frontend_api/service.py', 'frontend_api/portfolio_v7.py',
        'frontend_api/portfolio_v6.py', 'frontend_api/transactions.py',
        'frontend_api/transaction_gas.py', 'frontend_api/claim_planner.py',
        'frontend_api/royalty_reporting.py', 'frontend_api/earnings.py',
        'frontend_api/earnings_exact_lp.py', 'frontend_api/earnings_checkpoint.py',
        'frontend_api/earnings_checkpoint_v2.py', 'frontend_api/wallet_earnings.py',
        'tests_python/test_exact_lp_profile7.py', 'tests_python/test_earnings_checkpoint_v2.py',
        'tests_python/export_source9_website_fixtures.py')
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def detail_case(name):
    owner = unittest.TestCase()
    try:
        f = Fresh7API(owner)
        f.rpc.put(f.c['royalties'], 'mintEndRevision()', values=(1,))
        f.rpc.put(f.c['nft'], 'mintedCount()', values=(444,))
        if name == 'active_single':
            f.rpc.put(f.c['nft'], 'currentLPValue(uint256)', (f.rpc.nft_id,), (1, 1432*10**18))
        elif name in ('active_residual', 'price_unavailable'):
            f.q.secondary = 124
            f.q.secondary_count = 1
            if name == 'price_unavailable':
                f.f.base.outage()
        elif name == 'dormant':
            identifier = f.rpc.nft_id
            for role, method, value in (('vault','nftStatus(uint256)',3),
                    ('vault','nftBucket(uint256)',0),('vault','sharesOf(uint256)',0),
                    ('royalties','weightOf(uint256)',0),('royalties','activationOrdinal(uint256)',0),
                    ('royalties','ticketStart(uint256)',0),('vault','contributionUSD(uint256)',0)):
                f.rpc.put(f.c[role], method, (identifier,), (value,))
            f.rpc.put(f.c['nft'], 'currentLPValue(uint256)', (identifier,), (1,0))
            for role, assets in (('rewards',(ZERO,addr(20))),('royalties',(ZERO,addr(21)))):
                for asset in assets:
                    f.rpc.responses[f.c[role],native_data('claimable(uint256,address)',identifier,asset)] = words(0)
                    if role == 'royalties':
                        f.rpc.responses[f.c[role],native_data('eligibleFor(uint256,address)',identifier,asset)] = words(0)
        elif name.startswith('principal_'):
            identifier = f.rpc.nft_id
            phase = 2 if name == 'principal_allocated' else 3
            paid = name == 'principal_paid'
            f.rpc.put(f.c['access'], 'lpExitStarted()', values=(1,))
            f.rpc.put(f.c['principal_exit'], 'exitPhase()', values=(phase,))
            f.rpc.put(f.c['vault'], 'nftStatus(uint256)', (identifier,), (5,))
            f.q.position[1] = 0
            f.q.position[2] = f.q.position[3] = 0
            f.q.position[7] = 5
            f.rpc.put(f.c['nft'], 'currentLPValue(uint256)', (identifier,), (1,0))
            f.rpc.put(f.c['principal_exit'], 'principalOf(uint256)', (identifier,), (123,456,1,int(paid)))
            f.rpc.put(f.c['principal_exit'], 'claimablePrincipal(uint256)', (identifier,), (0,0) if paid else (123,456))
        recorder = RecordedRPC(f.rpc)
        p = Projection(f.config, recorder, clock=lambda:4000)
        outputs = dict(protocol=p.protocol(), nft=p.nft(str(f.rpc.nft_id)))
        return dict(read_configuration=f.config, profile=PROFILE, pins=f.c,
            codes=f.rpc.codes, projection_identity=p.identity, outputs=outputs,
            rpc_responses=recorder.rows)
    finally:
        owner.doCleanups()


def claim_case(policy):
    owner = unittest.TestCase()
    try:
        f = Fresh7API(owner)
        f.rpc.put(f.c['royalties'], 'mintEndRevision()', values=(1,))
        f.rpc.put(f.c['nft'], 'mintedCount()', values=(444,))
        recorder = RecordedRPC(SyntheticClaimRPC(f))
        p = Projection(f.config, recorder, clock=lambda:4000)
        cfg = transaction_config(p)
        if policy == 2:
            cfg['schema'] = 2
            cfg['fee_policy']['max_gas_limit'] = '40000000'
        service = Transactions(p, cfg)
        request = dict(action='claim', wallet=addr(30), claims=[
            dict(token_id=str(f.rpc.nft_id), asset=ZERO, royalty=False),
            dict(token_id=str(f.rpc.nft_id), asset=ZERO, royalty=True),
            dict(token_id=str(f.rpc.nft_id), asset=addr(21), royalty=True)])
        draft = service.prepare(request)
        plan = service.plan_claims(request)
        return dict(read_configuration=f.config, transaction_configuration=cfg,
            profile=PROFILE, pins=f.c, codes=f.rpc.codes,
            projection_identity=p.identity, request=request,
            outputs=dict(protocol=p.protocol(), nft=p.nft(str(f.rpc.nft_id)),
                         draft=draft, plan=plan), rpc_responses=recorder.rows)
    finally:
        owner.doCleanups()


def earnings_case():
    f = Checkpoint2APITests('runTest')
    try:
        f.setUp()
        recorder = RecordedRPC(f.rpc)
        f.rpc = recorder
        candidate = f.candidate()
        f.install(candidate)
        f.suffix()
        # This earnings scaffold originally exposes only the primary NFT's
        # display getters. Supply each modeled NFT and its actual modeled
        # bucket for the real bounded inventory/collection handlers as well.
        q = f.inner.responses.physical
        q.overrides[f.c['vault'],'poolBucket(bytes32)'] = [f'{5:064x}']
        for role, method in (('vault','group(uint256)'),
                ('strategy','rangeUpdatePending(uint256)'),
                ('portfolio_policy','configurationPending(uint256)')):
            f.inner.responses.selected[f.c[role],calldata(method,5)] = (f.c[role],method,(5,))
        model = f.model()
        for identifier in f.ids:
            weight = model.weights.get(identifier,0)
            for role, method, value in (('nft','traitsReady(uint256)',1),
                    ('nft','rarityOf(uint256)',weight-1 if weight else 0),
                    ('nft','paletteOf(uint256)',24),('nft','patternOf(uint256)',2),
                    ('royalties','activationOrdinal(uint256)',model.activation_order.index(identifier)+1 if weight else 0),
                    ('vault','nftStatus(uint256)',1 if weight else 3),
                    ('vault','contributionUSD(uint256)',100*10**18 if weight else 0)):
                f.put(f.c[role],method,(identifier,),(value,))
            f.put(f.c['nft'],'currentLPValue(uint256)',(identifier,),(1,1432*10**18 if weight else 0))
            f.put(f.c['principal_exit'],'principalOf(uint256)',(identifier,),(0,0,0,0))
            for asset in f.royalties:
                f.put(f.c['royalties'],'eligibleFor(uint256,address)',(identifier,asset),(int(bool(weight)),))
        for asset in f.royalties:
            f.put(f.c['royalties'],'effectiveEligibleCount(address)',(asset,),(len(model.cohorts[asset]),))
        f.put(f.c['royalties'],'mintEndRevision()',values=(1,))
        p = f.projection()
        wallet = addr(32)
        outputs = dict(protocol=p.protocol(), nfts={str(i):p.nft(str(i)) for i in f.ids},
            inventory=p.wallet(wallet), earnings=p.earnings(),
            wallet_summary=p.wallet_summary(wallet,99), collection=p.collection(99),
            nft_earnings={str(i): p.earnings(str(i)) for i in f.ids},
            wallet_earnings=p.wallet_earnings(wallet, 99),
            full_raw_earnings=f.projection(f.full_config()).earnings())
        for key in ('all_time', 'last_24h', 'window', 'event_count'):
            if outputs['earnings'][key] != outputs['full_raw_earnings'][key]:
                raise AssertionError('Actual checkpoint2 and full raw replay differ')
        checkpoint = json.loads(candidate)
        return dict(read_configuration=f.config, profile=PROFILE, pins=f.c,
            codes=f.inner.codes, projection_identity=p.identity,
            outputs=outputs, checkpoint_candidate=checkpoint,
            checkpoint_sha256=hashlib.sha256(candidate).hexdigest(),
            raw_logs=f.rows, rpc_responses=recorder.rows,
            note='Actual SQLite/history/replay and checkpoint2 handlers. Price configuration is absent; USD remains unavailable. Temporary database/artifact paths are inert provenance, not deployment configuration.')
    finally:
        f.doCleanups()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    target = parser.parse_args().output.resolve()
    if target.suffix != '.json':
        raise ValueError('Fixture output must be JSON')
    result = dict(schema=1, kind='source9_website_synthetic_api_fixtures',
        scope='Actual fresh7 Python DTO handlers against explicitly synthetic offline RPC/fees/authorities/venue fixtures. Not live data, EVM execution, provider/market/wallet acceptance, deployment, or service rollout.',
        profile=PROFILE, source_sha256=source_hashes(),
        cases={name:detail_case(name) for name in ('active_single','active_residual','price_unavailable',
            'dormant','principal_allocated','principal_ready','principal_paid')},
        unsupported=['No complete fresh7 Entry3 ActivationTransactions simulation fixture is exported.',
                     'No deployed inventory, marketplace, provider, or public signing is qualified.'])
    for policy in (1, 2):
        result['cases']['claim_policy'+str(policy)] = claim_case(policy)
    result['cases']['checkpoint2_earnings'] = earnings_case()
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(result, indent=2, allow_nan=False)+'\n').encode()
    with target.open('xb') as handle:
        handle.write(raw)
    print(json.dumps(dict(cases=list(result['cases']), path=str(target),
                         sha256=hashlib.sha256(raw).hexdigest())))


if __name__ == '__main__':
    main()
