"""Verify explicitly selected local rehearsal artifacts offline; never use RPC.

Pass --campaign DIR --inputs PLAN.json --output NEW.json. The plan names an
inventory, before {state,snapshot}, four ordered steps {name,action,asset,token_id,
consumer,executed,state,snapshot}, optional approval reviews, and http_logs.
Each executed record must contain its real mined transaction (or a step may
name mined_transaction). Missing evidence is a failure, never an inferred zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from zzz_ops.abi import decode_words, keccak256

ZERO = '0x' + '0'*40
UNIT = 10**18
READ_METHODS = {'eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber', 'eth_getCode',
                'eth_call', 'eth_estimateGas', 'eth_gasPrice', 'eth_getBalance'}
ENTRY_SIGNATURE = 'executeReviewed((uint256,bytes32,address,uint256,uint128,uint256,bool),uint16,bytes32)'


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def raw(value):
    require(isinstance(value, str) and re.fullmatch(r'(?:0|[1-9][0-9]{0,77})', value), 'Missing or malformed exact decimal integer')
    return int(value)


def quantity(value):
    require(isinstance(value, str) and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})', value), 'Missing or malformed RPC quantity')
    return int(value, 16)


def digest(value):
    require(isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{64}', value), 'Missing or malformed hash')
    return value.lower()


def address(value):
    require(isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{40}', value), 'Missing or malformed address')
    return value.lower()


def abi_words(value, count):
    try:
        result = decode_words(value)
    except (ValueError, TypeError):
        raise EvidenceError('Malformed evidence ABI words') from None
    require(len(result) == count, 'Unexpected evidence ABI word count')
    return [int(x, 16) for x in result]


def topic(signature):
    return '0x' + keccak256(signature.encode()).hex()


def receipt_event(receipt, emitter, signature, indexed, data_count):
    found = [row for row in receipt['logs'] if address(row['address']) == address(emitter)
             and row.get('topics', [])[:1] == [topic(signature)]]
    require(len(found) == 1, 'Missing or ambiguous actual receipt event: ' + signature)
    event = found[0]
    require(event.get('removed') is False and digest(event['transactionHash']) == digest(receipt['transactionHash']),
            'Receipt event is removed or belongs to another transaction')
    require(event['topics'][1:] == ['0x' + f'{x:064x}' for x in indexed], 'Receipt event indexed identity differs')
    return abi_words(event['data'], data_count)


def gas_review(dto, *, schema=2):
    require(dto['schema'] == schema, 'Activation DTO schema differs from the explicit selected policy')
    fee = dto['network_gas']
    estimate, suggested, price = (raw(fee[key]) for key in ('estimated_units', 'suggested_limit', 'price_wei'))
    require(estimate >= 21000 and price > 0 and fee['includes_all_network_components'] is True and
            fee['included_in_execution_loss'] is False and fee['wallet_must_refresh'] is True,
            'Incomplete or nonseparate execution gas review')
    padded = (estimate*120 + 99)//100
    if schema == 2:
        configured, confirmed, effective = (raw(fee[key]) for key in ('configured_gas_limit', 'confirmed_block_gas_limit', 'effective_gas_limit'))
        require(21000 <= configured <= 64_000_000 and 21000 <= confirmed < 1 << 64 and
                effective == min(configured, confirmed) and fee['policy_schema'] == 2 and
                fee['full_twenty_percent_headroom'] is True and suggested == padded <= effective,
                'Gas policy2 lacks exact full20% headroom or confirmed-block bound')
    else:
        require(schema == 1 and suggested == min(12_000_000, padded) and estimate <= 12_000_000,
                'Historical approval gas policy differs')
    require(raw(fee['suggested_limit_cost_wei']) == suggested*price and raw(fee['estimated_fee_wei']) == estimate*price,
            'Gas cost arithmetic differs')
    return suggested, price


def state_rows(state):
    require(state['schema'] == 1 and state['accounting_version'] == 7 and state['chain_id'] == 4663 and
            state['simulation'] is False and state['public_transactions'] is False,
            'Raw witness is not the explicit actual local accounting7 profile')
    require(type(state['block_number']) is int and state['block_number'] > 0, 'Missing raw witness block number')
    digest(state['block_hash'])
    rows = {row['token_id']: row for row in state['rows']}
    require(len(rows) == 2 == len(state['rows']), 'Expected exactly two distinct witnessed NFTs')
    for identifier, row in rows.items():
        raw(identifier); address(row['owner'])
        group = abi_words('0x' + ''.join(row['group_words']), 8)
        require(raw(row['main_id']) == group[1] and raw(row['idle0']) == group[2] and
                raw(row['idle1']) == group[3] and raw(row['last_rebalance']) == group[6],
                'Raw witness aliases differ from actual Position words')
        if raw(row['shares_raw']) == 0:
            require(raw(row['bucket_id']) == 0 and raw(row['main_id']) == 0 and raw(row['contribution_usd_18']) == 0,
                    'Dormant raw state has principal rights')
        else:
            require(raw(row['bucket_id']) > 0 and group[7] == 1 and raw(row['main_liquidity_raw']) > 0 and
                    raw(row['secondary_id']) == 0 and len(row['main_ticks_words']) == 2,
                    'Active raw state lacks actual main liquidity or expected single-leg identity')
            abi_words('0x' + ''.join(row['physical_amounts_words']), 2)
        require(abi_words('0x' + ''.join(row['current_lp_value_words']), 2)[0] == 1, 'Current NFT LP value is unavailable')
        for key in ('wallet_eth_wei', 'wallet_zzz_raw', 'entry_allowance_raw', 'total_shares'):
            raw(row[key])
    return rows


class Bundle:
    def __init__(self, campaign):
        self.root = Path(campaign).resolve()
        require(self.root.is_dir(), 'Campaign evidence directory is missing')
        self.hashes = {}

    def path(self, relative):
        require(isinstance(relative, str) and not Path(relative).is_absolute(), 'Evidence plan must use campaign-relative files')
        path = (self.root/relative).resolve()
        require(path.is_relative_to(self.root) and path.is_file(), 'Required campaign evidence file is missing or escapes its root')
        data = path.read_bytes()
        require(len(data) <= 128*1024*1024, 'Evidence input exceeds offline bound')
        self.hashes[relative] = hashlib.sha256(data).hexdigest()
        return path

    def read(self, relative):
        return json.loads(self.path(relative).read_text(encoding='utf-8-sig'))


def api_snapshot(snapshot, rows):
    require(isinstance(snapshot, list) and len(snapshot) == 2, 'Complete two-NFT API snapshot is missing')
    by_id = {item['nft']['token_id']: item for item in snapshot}
    require(set(by_id) == set(rows), 'API snapshot and raw witness select different NFTs')
    for identifier, row in rows.items():
        item = by_id[identifier]; nft = item['nft']; position = nft['position']
        require(nft['schema'] == 2 and nft['chain_id'] == 4663 and nft['traits_ready'] is True and
                address(nft['owner']) == address(row['owner']) and position['shares_raw'] == row['shares_raw'] and
                position['bucket_id'] == row['bucket_id'] and
                position['cumulative_gross_contribution_usd_18'] == row['contribution_usd_18'],
                'Actual API ownership/share/contribution state differs from raw witness')
        active = raw(row['shares_raw']) > 0
        require(position['activated'] is active and position['status'] == ('active' if active else 'dormant'),
                'Actual API activation state differs from raw witness')
        require(position['current_lp_value']['available'] is True and
                raw(position['current_lp_value']['raw']) == int(row['current_lp_value_words'][1], 16),
                'API NFT LP valuation differs from raw getter')
        require(item['metadata']['image'] == row['metadata']['image'] and
                item['metadata']['lp_value_usd_18'] == row['metadata']['lp_value_usd_18'],
                'Actual metadata differs between API snapshot and raw witness')
        evolution = [a['value'] for a in row['metadata']['attributes'] if a['trait_type'] == 'Evolution']
        require(len(evolution) == 1 and evolution[0].lower() == position['evolution'], 'Actual artwork evolution differs from API')
        require(nft['provenance']['accounting_version'] == 7 and nft['provenance']['eip1898_require_canonical'] is True,
                'Actual API snapshot profile/canonical provenance is missing')
    return by_id


def consumer_case(report, identifier, action, asset):
    require(report['passed'] is True and report['actual_http_rpc'] is True and report['actual_clock'] is True and
            report['signing_enabled'] is False and report['transactions_submitted'] == 0 and
            report['production_approved'] is False and report['forbidden_operation_attempted'] is False and
            report['website_source']['unchanged_during_run'] is True, 'Actual website read/unsigned-only consumer proof failed')
    require(set(report['rpc_method_counts']) <= READ_METHODS and report['rpc_method_counts'].get('eth_call', 0) > 0 and
            report['http_method_counts'].get('POST /v1/activation/prepare', 0) > 0,
            'Consumer did not use actual allowed HTTP/RPC review paths')
    matches = [row for row in report['cases'] if row['intent']['id'] == identifier and
               row['intent']['action'] == action and row['intent']['asset'] == asset]
    require(len(matches) == 1 and matches[0]['passed'] is True and matches[0]['outcome'] == 'accepted' and
            matches[0]['expected_rejection'] is False and matches[0]['signing_enabled'] is False,
            'Expected actual positive website review is missing')
    case = matches[0]
    require(case['draft']['signing_enabled'] is False and 'nonce' not in case['draft']['transaction'], 'Website returned signing or nonce capability')
    return case


def mined_transaction(executed, selected, bundle):
    mined = bundle.read(selected['mined_transaction']) if 'mined_transaction' in selected else executed['transaction']
    tx = executed['draft']['transaction']; receipt = executed['receipt']
    require(quantity(receipt['status']) == 1 and digest(receipt['transactionHash']) == digest(mined['hash']) and
            digest(receipt['blockHash']) == digest(mined['blockHash']) and
            quantity(receipt['blockNumber']) == quantity(mined['blockNumber']), 'Actual mined transaction/receipt identity differs')
    require(address(mined['from']) == address(tx['from']) == address(receipt['from']) and
            address(mined['to']) == address(tx['to']) == address(receipt['to']) and
            mined['input'].lower() == tx['data'].lower() and quantity(mined['value']) == quantity(tx['value']) and
            quantity(mined['chainId']) == quantity(tx['chainId']) == 4663,
            'Actual executed calldata/value/caller differs from the unsigned review')
    require(quantity(receipt['gasUsed']) <= quantity(mined['gas']) <= raw(executed['draft']['network_gas']['gas_limit']) and
            quantity(receipt['effectiveGasPrice']) <= raw(executed['draft']['network_gas']['gas_price_wei']),
            'Actual execution exceeded the reviewed gas or gas-price budget')
    return receipt


def backend_dto(selected, draft, http, bundle):
    matches = [x['response'] for x in http if x.get('status') == 200 and x.get('method') == 'POST' and
               x.get('path', '').endswith('/v1/activation/prepare') and isinstance(x.get('response'), dict) and
               x['response'].get('transaction') == draft['transaction'] and
               x['response'].get('provenance', {}).get('block_hash') == draft['provenance']['block_hash']]
    dto = bundle.read(selected['backend']) if 'backend' in selected else (matches[0] if matches else None)
    require(dto is not None and dto['transaction'] == draft['transaction'], 'Exact actual raw HTTP activation DTO is missing')
    return dto


def verify(campaign, plan):
    b = Bundle(campaign); inventory = b.read(plan['inventory'])
    require(inventory['chain_id'] == 4663 and inventory['public_transactions'] is False and inventory['production_approved'] is False,
            'Inventory is not an explicit unapproved disposable fork')
    contracts = inventory['contracts']; zzz = inventory['dependencies']['zzz']
    rows = state_rows(b.read(plan['before']['state']))
    before_state = b.read(plan['before']['state'])
    snapshots = api_snapshot(b.read(plan['before']['snapshot']), rows)
    require(all(raw(row['shares_raw']) == 0 and row['metadata']['royalty_activated'] is False for row in rows.values()),
            'Read/review stage already changed activation or artwork')
    require(all(item['nft']['position']['evolution'] == 'dormant' for item in snapshots.values()), 'Pre-execution artwork was upgraded')
    steps = plan['steps']
    require([(s['action'], s['asset']) for s in steps] == [('activate', 'ETH'), ('activate', 'ZZZ'), ('increase', 'ETH'), ('increase', 'ZZZ')],
            'Explicit four-operation order is required')
    require(steps[0]['token_id'] == steps[2]['token_id'] and steps[1]['token_id'] == steps[3]['token_id'] and
            steps[0]['token_id'] != steps[1]['token_id'] and {s['token_id'] for s in steps} == set(rows),
            'ETH and ZZZ operations do not select the same two distinct NFTs')
    http = []
    for name in plan.get('http_logs', []):
        http.extend(json.loads(line) for line in b.path(name).read_text(encoding='utf-8').splitlines() if line)
    approvals = []
    for selected in plan.get('approvals', []):
        executed = b.read(selected['executed']); draft = executed['draft']
        case = consumer_case(b.read(selected['consumer']), draft['intent']['id'], draft['requested_action'], 'ZZZ')
        require(case['draft'] == draft and draft['action'] == 'approve' and draft['source']['asset'] == zzz,
                'Approval review/execution identity differs')
        receipt = mined_transaction(executed, selected, b)
        amount = raw(draft['source']['amount_raw'])
        expected = '0x095ea7b3' + contracts['entry'][2:].rjust(64, '0') + f'{amount:064x}'
        require(draft['transaction']['data'] == expected, 'ZZZ approval is not exact Entry-only allowance')
        approved = receipt_event(receipt, zzz, 'Approval(address,address,uint256)',
                                 [int(draft['transaction']['from'], 16), int(contracts['entry'], 16)], 1)
        require(approved == [amount], 'Actual ZZZ approval amount differs')
        if 'quote' in case:
            require(raw(case['quote']['raw']) == amount, 'Quoted activation approval amount differs')
        approval_state = b.read(selected['state']); approval_rows = state_rows(approval_state)
        approved_row = approval_rows[draft['intent']['id']]
        require(approval_state['block_number'] == quantity(receipt['blockNumber']) and
                raw(approved_row['entry_allowance_raw']) == amount and approved_row['owner'] == draft['transaction']['from'],
                'Actual post-approval allowance/current owner differs from the exact selected amount')
        if draft['requested_action'] == 'activate':
            require(raw(approved_row['shares_raw']) == 0 and raw(approved_row['main_id']) == 0 and
                    approved_row['metadata']['royalty_activated'] is False and
                    approved_row['metadata']['image'] == rows[draft['intent']['id']]['metadata']['image'],
                    'Approval prematurely activated LP or upgraded dormant artwork')
        else:
            earlier = [(b.read(step['state'])['block_number'], step['state']) for step in steps
                       if b.read(step['state'])['block_number'] < approval_state['block_number']]
            require(bool(earlier), 'Pre-growth-approval LP state witness is missing')
            prior_approval = state_rows(b.read(max(earlier)[1]))
            require(all(approval_rows[n]['shares_raw'] == prior_approval[n]['shares_raw'] and
                        approval_rows[n]['contribution_usd_18'] == prior_approval[n]['contribution_usd_18'] and
                        approval_rows[n]['main_id'] == prior_approval[n]['main_id'] and
                        approval_rows[n]['main_liquidity_raw'] == prior_approval[n]['main_liquidity_raw'] and
                        approval_rows[n]['metadata']['image'] == prior_approval[n]['metadata']['image'] for n in approval_rows),
                    'Growth approval changed LP/shares/contribution or artwork before Entry execution')
        schema = selected['policy_schema']  # Historical policy1 approval is explicit, never inferred.
        approval_gas, approval_price = gas_review(backend_dto(selected, draft, http, b), schema=schema)
        require(raw(draft['network_gas']['gas_limit']) == approval_gas and
                raw(draft['network_gas']['gas_price_wei']) == approval_price, 'Actual approval gas review differs')
        approvals.append((draft, receipt))
    results = []; geometry = None; previous_state = before_state
    for index, selected in enumerate(steps):
        identifier = selected['token_id']; previous = rows; owner = previous[identifier]['owner']
        report = b.read(selected['consumer']); case = consumer_case(report, identifier, selected['action'], selected['asset'])
        draft = case['draft']; executed = b.read(selected['executed'])
        require(executed['draft'] == draft and draft['action'] == selected['action'] and address(draft['transaction']['from']) == owner,
                'Executed review differs from the actual consumer/current owner')
        receipt = mined_transaction(executed, selected, b)
        dto = backend_dto(selected, draft, http, b)
        gas, price = gas_review(dto)
        require(raw(draft['network_gas']['gas_limit']) == gas and raw(draft['network_gas']['gas_price_wei']) == price,
                'Normalized review gas differs from raw full-headroom policy2')
        q = abi_words('0x' + draft['transaction']['data'][10:], 9)
        require(draft['transaction']['data'][:10] == '0x' + keccak256(ENTRY_SIGNATURE.encode()).hex()[:8] and
                q[0] == int(identifier) and q[1] == int(inventory['pool_id'], 16) and
                q[2] == int(ZERO if selected['asset'] == 'ETH' else zzz, 16) and q[3] == raw(draft['source']['amount_raw']) and
                q[4] > 0 and q[6] == int(selected['action'] == 'increase') and q[7] == 200 and
                q[8] == int(draft['expected_contribution_policy'], 16), 'Actual Entry3 tuple or captured loss/policy differs')
        amount = q[3]; source_value = raw(draft['source']['value_usd_18']); upper = raw(draft['source_upper_usd_18']); required = upper-upper*200//10000
        proof = dto['contribution']
        require(raw(dto['minimum_deployed_usd_18']) == required == raw(draft['minimum_deployed_usd_18']) and
                raw(proof['marginal_deployed_usd_18']) >= required and raw(proof['lp_liquidity_added_raw']) >= q[4] and
                raw(proof['shares_added_raw']) > 0 and raw(draft['simulated_lp_added_usd_18']) == raw(proof['marginal_deployed_usd_18']),
                'Positive actual HTTP marginal LP/share proof is missing')
        if selected['action'] == 'activate':
            require(source_value >= 100*UNIT, 'Activation source is below the governed100USD floor')
            if 'quote' in case: require(raw(case['quote']['raw']) == amount, 'Exact activation quote amount differs')
        else:
            require(source_value >= 5*UNIT, 'Growth source is below the governed5USD floor')
        new_state = b.read(selected['state']); rows = state_rows(new_state)
        snapshot = api_snapshot(b.read(selected['snapshot']), rows)
        require(set(rows) == set(previous) and all(rows[n]['owner'] == previous[n]['owner'] for n in rows), 'NFT current owner changed unexpectedly')
        row = rows[identifier]; prior = previous[identifier]
        require(previous_state['block_number'] < quantity(receipt['blockNumber']) <= new_state['block_number'],
                'Execution receipt is not between the recorded before/after states')
        require(raw(row['shares_raw']) > raw(prior['shares_raw']) and
                raw(row['contribution_usd_18'])-raw(prior['contribution_usd_18']) == source_value and
                raw(row['main_liquidity_raw']) > (raw(prior['main_liquidity_raw']) if raw(prior['main_id']) else 0) and
                address(row['main_owner']) == address(contracts['vault']), 'Execution did not create/increase actual Vault-owned LP/shares')
        other = next(n for n in rows if n != identifier)
        require(rows[other]['shares_raw'] == previous[other]['shares_raw'] and
                rows[other]['contribution_usd_18'] == previous[other]['contribution_usd_18'], 'Another NFT funded the entrant or gained shares')
        if index == 0: require(raw(rows[other]['shares_raw']) == 0 and snapshot[other]['nft']['position']['evolution'] == 'dormant', 'First entry activated the other NFT')
        current_geometry = (row['main_id'], row['main_ticks_words'], row['last_rebalance'], row['group_words'][5])
        if geometry is None: geometry = current_geometry
        require(current_geometry == geometry, 'Contribution replaced/recentered LP or reset its adjustment clock')
        require(raw(row['total_shares']) == sum(raw(x['shares_raw']) for x in rows.values()), 'Whole-unit aggregate shares differ')
        if selected['action'] == 'activate': require(int(row['current_lp_value_words'][1], 16) > 98*UNIT, 'Actual attached activation value does not exceed98USD')
        if selected['asset'] == 'ZZZ':
            require(raw(prior['wallet_zzz_raw'])-raw(row['wallet_zzz_raw']) == amount and raw(row['entry_allowance_raw']) == 0,
                    'Exact ZZZ input was not spent once or Entry allowance remained')
            require(any(a['transaction']['from'] == owner and raw(a['source']['amount_raw']) == amount and
                        quantity(r['blockNumber']) < quantity(receipt['blockNumber']) for a, r in approvals),
                    'Matching actual exact ZZZ approval is missing')
        # NFT owners perform only the explicitly recorded approval/Entry calls
        # in these intervals. Operator seed/funding costs are separate accounts.
        for owned_id, owned in rows.items():
            who = address(owned['owner'])
            expected_cost = 0
            if who == address(draft['transaction']['from']):
                expected_cost += quantity(receipt['gasUsed'])*quantity(receipt['effectiveGasPrice']) + quantity(draft['transaction']['value'])
            for approved, approval_receipt in approvals:
                if (address(approved['transaction']['from']) == who and
                        previous_state['block_number'] < quantity(approval_receipt['blockNumber']) <= new_state['block_number']):
                    expected_cost += quantity(approval_receipt['gasUsed'])*quantity(approval_receipt['effectiveGasPrice'])
            require(raw(previous[owned_id]['wallet_eth_wei'])-raw(owned['wallet_eth_wei']) == expected_cost,
                    'NFT owner native balance delta differs from exact contribution plus actual separate gas')
            expected_zzz = amount if who == address(owner) and selected['asset'] == 'ZZZ' else 0
            require(raw(previous[owned_id]['wallet_zzz_raw'])-raw(owned['wallet_zzz_raw']) == expected_zzz,
                    'NFT owner ZZZ delta differs from its own exact recorded input')
        source = receipt_event(receipt, contracts['entry'],
            'SourceContributed(address,uint256,bytes32,address,uint256,uint256,address,uint256,bool)',
            [int(owner, 16), int(identifier), int(inventory['pool_id'], 16)], 6)
        require(source == [q[2], amount, source_value, q[2], amount, q[6]], 'Actual source receipt differs from prepared original units')
        shares = receipt_event(receipt, contracts['vault'], 'SharesAdded(uint256,uint256,uint256,uint256)',
                               [int(identifier), raw(row['bucket_id'])], 2)
        require(shares[0] == raw(row['shares_raw'])-raw(prior['shares_raw']), 'Actual shares receipt differs from persisted whole shares')
        verified = receipt_event(receipt, contracts['contribution_pricing'],
            'ContributionVerified(uint256,uint256,uint256,uint256,uint256,uint256,uint160,bytes32)',
            [int(identifier), raw(row['bucket_id'])], 6)
        require(verified[0] == source_value and verified[1] == upper and verified[2] >= required and verified[3] == shares[1],
                'Actual marginal-deployment receipt does not preserve captured source floors')
        require(new_state['entry'] == before_state['entry'], 'Entry prefunds/balances were consumed or left behind')
        results.append(dict(name=selected['name'], transaction_hash=receipt['transactionHash'],
            actual_lp_token_id=row['main_id'], actual_liquidity_raw=row['main_liquidity_raw'],
            shares_added_raw=str(shares[0]), actual_marginal_deployed_usd_18=str(verified[2]),
            state_block=new_state['block_number'], artwork_evolution=snapshot[identifier]['nft']['position']['evolution']))
        previous_state = new_state
    return dict(passed=True, scope='Offline consistency verification of explicitly recorded actual local artifacts; no RPC or production acceptance',
                operations=results, files_sha256=b.hashes, signing_enabled=False, public_transactions=False,
                production_approved=False, offline_checks_are_not_evm_reexecution=True,
                limitations=['Controlled feeds/VRF and separately seeded external depth remain local substitutes',
                             'Recorded receipts/API consistency does not qualify actual market depth, providers, wallets, hosting or independent audit'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', required=True)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        output = Path(args.output).open('x', encoding='utf-8')
    except OSError:
        parser.exit(2, 'Evidence output must be a new writable file.\n')
    try:
        plan_path = Path(args.inputs)
        plan = json.loads(plan_path.read_text(encoding='utf-8-sig'))
        report = verify(args.campaign, plan)
        report['plan_sha256'] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        status = 0
    except (KeyError, ValueError, TypeError, OSError, IndexError) as exc:
        report = dict(passed=False, error_type=type(exc).__name__, message=str(exc),
                      scope='Required evidence is missing, malformed or inconsistent; no values were guessed')
        status = 1
    with output:
        json.dump(report, output, indent=2)
        output.write('\n')
    return status


if __name__ == '__main__':
    raise SystemExit(main())
