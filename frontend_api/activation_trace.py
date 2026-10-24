"""Decode only the reviewed Entry/Vault/manager call path from a bounded trace.

RPC traces are observations, not execution proofs. Never infer new LP from a
before/after bucket NAV: repricing and incumbent compound would contaminate it.
"""
from __future__ import annotations

from frontend_api.service import ProjectionError, ZERO, _address_word, _quantity
from zzz_ops.abi import address, calldata, decode_words, keccak256

EXECUTE = 'execute((uint256,bytes32,address,uint256,bytes32,uint256,uint128,uint256,bool))'
LEGACY_RESULT = 'contributionResult(uint256,uint256,uint256,uint256,uint256,uint256,uint16)'
RESULT = 'contributionResult(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint16)'
VALUE = 'value(address,uint256)'
MINT = 'mint(bytes32,int24,int24,uint256,uint256,uint128,uint256)'
INCREASE = 'increase(bytes32,uint256,uint256,uint256,uint128,uint256)'
SOURCE = '0x' + keccak256(b'SourceContributed(address,uint256,bytes32,address,uint256,uint256,address,uint256,bool)').hex()
SHARES = '0x' + keccak256(b'SharesAdded(uint256,uint256,uint256,uint256)').hex()
MAX_FRAMES = 8192


def selector(signature):
    return '0x' + keccak256(signature.encode()).hex()[:8]


def words(raw, length):
    result = decode_words(raw)
    if len(result) != length:
        raise ProjectionError('Unexpected activation ABI length')
    return result


def request_data(identifier, pool, source, amount, route, minimum_out, minimum_lp, deadline, increase):
    # One STATIC tuple has no dynamic offset. Zero source is native ETH.
    values = (identifier, int(pool, 16), int(source, 16), amount, int(route, 16),
              minimum_out, minimum_lp, deadline, int(increase))
    if any(type(x) is not int or not 0 <= x < 2**256 for x in values) or not 0 < minimum_lp < 2**128:
        raise ValueError('Invalid Entry tuple')
    return selector(EXECUTE) + ''.join(f'{x:064x}' for x in values)


def successful(frame):
    if not isinstance(frame, dict) or frame.get('error') or frame.get('revertReason'):
        raise ProjectionError('Activation simulation reverted or has an invalid frame')
    return frame


def child(frame, caller, target, signature, kind):
    matches = [x for x in frame.get('calls', []) if x.get('from', '').lower() == caller and
               x.get('to', '').lower() == target and x.get('input', '').lower().startswith(selector(signature))]
    if len(matches) != 1 or matches[0].get('type') != kind:
        raise ProjectionError('Missing or ambiguous reviewed activation call')
    return successful(matches[0])


def event(frame, emitter, topic, indexed, count):
    found = [x for x in frame.get('logs', []) if x.get('address', '').lower() == emitter and
             x.get('topics', [None])[:1] == [topic]]
    if len(found) != 1:
        raise ProjectionError('Missing or ambiguous contribution event')
    item = found[0]
    if item.get('removed', False) is not False or item.get('topics') != [topic] + indexed:
        raise ProjectionError('Contribution event identity mismatch')
    return words(item.get('data'), count)


def measure(trace, tx, pins, request, gross, max_slippage, verify_historical=None):
    """Return contract-checked marginal deployment, share issuance and LP units."""
    root = successful(trace)
    stack = [(root, 0)]; count = 0
    while stack:
        frame, depth = stack.pop(); count += 1
        if not isinstance(frame, dict) or depth > 64 or count > MAX_FRAMES:
            raise ProjectionError('Activation trace exceeds its bound')
        children = frame.get('calls', [])
        logs = frame.get('logs', [])
        if not isinstance(children, list) or not isinstance(logs, list) or len(logs) > 4096:
            raise ProjectionError('Malformed activation trace')
        if any(not isinstance(x, dict) for x in children + logs):
            raise ProjectionError('Malformed activation trace item')
        for key in ('from', 'to', 'input', 'output', 'type'):
            if key in frame and not isinstance(frame[key], str):
                raise ProjectionError('Malformed activation trace field')
        for log in logs:
            if (not isinstance(log.get('address'), str) or not isinstance(log.get('topics'), list) or
                    any(not isinstance(t, str) for t in log['topics'])):
                raise ProjectionError('Malformed activation trace log')
        stack.extend((x, depth + 1) for x in children)
    if (root.get('type') != 'CALL' or root.get('from', '').lower() != tx['from'] or
            root.get('to', '').lower() != tx['to'] or root.get('input', '').lower() != tx['data'] or
            _quantity(root.get('value', '0x0')) != int(tx['value'], 16) or root.get('output', '0x') != '0x'):
        raise ProjectionError('Trace is not the exact unsigned Entry operation')
    gas_used = _quantity(root.get('gasUsed'))
    if not 0 < gas_used <= int(tx['gas'], 16):
        raise ProjectionError('Invalid simulated gas use')
    req = request
    native_profile = req.get('accounting_version', 1) == 2
    topic_word = lambda n: '0x' + f'{n:064x}'
    source = event(root, pins['entry'], SOURCE,
                   [topic_word(int(tx['from'], 16)), topic_word(req['id']), req['pool']], 6)
    if (_address_word(source[0], native=True) != req['source'] or int(source[1], 16) != req['amount'] or
            int(source[2], 16) != gross or _address_word(source[3], native=native_profile) != req['output'] or
            int(source[5], 16) != int(req['increase'])):
        raise ProjectionError('Source event differs from authenticated original input')
    acquired = int(source[4], 16)
    if acquired == 0 or acquired < req['minimum_out']:
        raise ProjectionError('Invalid converted output')
    if req['route'] == '0x' + '0' * 64 and acquired != req['amount']:
        raise ProjectionError('Direct input did not preserve its exact amount')
    a0, a1 = (acquired, 0) if req['output'] == req['token0'] else (0, acquired)
    signature = ('increase(uint256,uint256,uint256,uint128,uint256)' if req['increase'] else
                 'activate(uint256,bytes32,uint256,uint256,uint128,uint256)')
    args = ((req['id'], a0, a1, req['minimum_lp'], req['deadline']) if req['increase'] else
            (req['id'], req['pool'], a0, a1, req['minimum_lp'], req['deadline']))
    vault = child(root, pins['entry'], pins['vault'], signature, 'CALL')
    if vault['input'].lower() != calldata(signature, *args) or vault.get('output', '0x') != '0x':
        raise ProjectionError('Vault did not receive the exact owner contribution')
    if native_profile and _quantity(vault.get('value', '0x0')) != (a0 if req['token0'] == ZERO else 0):
        raise ProjectionError('Vault child call does not carry the exact declared native contribution')
    candidates = [x for x in vault.get('calls', []) if x.get('from','').lower()==pins['vault'] and
                  x.get('to','').lower()==pins['budget'] and
                  x.get('input','')[:10].lower() in (selector(RESULT),selector(LEGACY_RESULT))]
    if len(candidates)!=1 or candidates[0].get('type')!='STATICCALL':
        raise ProjectionError('Missing or ambiguous reviewed contribution result')
    check = successful(candidates[0])
    current = check['input'][:10].lower()==selector(RESULT)
    values = words('0x'+check['input'][10:],8 if current else 7)
    if current:
        if int(values[0],16)!=req['bucket']:
            raise ProjectionError('Contribution result uses a different bucket')
        values=values[1:]
    input_usd, supply, incumbent_nav, incumbent_deployed, deployed, idle, slippage = [
        int(x, 16) for x in values]
    # In the pinned current Budget implementation these direct Oracle.value
    # calls are exclusively historicalCompoundValue's non-current currencies.
    # Nested oracle calls from other modules never form part of this witness.
    historical=[];seen=set()
    for call in check.get('calls',[]):
        if call.get('from','').lower()!=pins['budget'] or call.get('to','').lower()!=pins['oracle']:
            continue
        successful(call)
        if not current or not supply or call.get('type')!='STATICCALL' or call.get('input','')[:10].lower()!=selector(VALUE):
            raise ProjectionError('Unexpected historical compound valuation call')
        token_raw,amount_raw=words('0x'+call['input'][10:],2)
        token=_address_word(token_raw,native=native_profile);amount=int(amount_raw,16)
        if token in seen or token in (req['token0'],req['token1']) or amount==0:
            raise ProjectionError('Invalid historical compound currency')
        seen.add(token);value=int(words(call.get('output'),1)[0],16)
        historical.append((token,amount,value))
    historical_value=sum(item[2] for item in historical)
    if historical_value+incumbent_nav>=2**256:
        raise ProjectionError('Historical compound valuation overflow')
    if historical:
        if verify_historical is None:raise ProjectionError('Historical compound feeds are not reviewed')
        verify_historical(historical)
    issued, net = [int(x, 16) for x in words(check.get('output'), 2)]
    floor = gross - gross // 100
    if (input_usd != gross or slippage != max_slippage or not 0 < slippage <= 200 or
            deployed < incumbent_deployed + floor or net != deployed + idle - incumbent_nav or
            net < floor or net < gross * (10000 - slippage) // 10000 or
            idle > (deployed + idle) * 500 // 10000 or deployed == 0 or
            supply and incumbent_nav == 0):
        raise ProjectionError('Simulated contribution violates its original-source 1% budget')
    expected_shares = supply * net // (incumbent_nav + historical_value) if supply else net
    if issued != expected_shares or issued == 0 or issued + supply > 10**36:
        raise ProjectionError('Invalid contribution share issuance')
    share_event = event(vault, pins['vault'], SHARES,
                        [topic_word(req['id']), topic_word(req['bucket'])], 2)
    if [int(x, 16) for x in share_event] != [issued, net]:
        raise ProjectionError('Share event differs from contract accounting')
    # The one mint/increase performed by _put has its own isolated PosM reads.
    # Reads made by harvest/NAV elsewhere in Vault must never be used here.
    create = req['old_lp_id'] == 0
    method = MINT if create else INCREASE
    mint = child(vault, pins['vault'], pins['liquidity'], method, 'CALL')
    params = words('0x' + mint['input'][10:], 7 if create else 6)
    if (params[0] != req['pool'][2:] or int(params[-2], 16) != req['minimum_lp'] or
            int(params[-1], 16) != req['deadline'] or not create and int(params[1], 16) != req['old_lp_id']):
        raise ProjectionError('LP mint/increase parameters differ from the Entry request')
    if native_profile:
        amount0_slot = 3 if create else 2
        expected_value = int(params[amount0_slot], 16) if req['token0'] == ZERO else 0
        if _quantity(mint.get('value', '0x0')) != expected_value:
            raise ProjectionError('LP child call does not carry the exact declared native budget')
    output = words(mint.get('output'), 3 if create else 2)
    lp_id = int(output[0], 16) if create else req['old_lp_id']
    target_call = calldata('getPositionLiquidity(uint256)', lp_id)
    readings = [x for x in mint.get('calls', []) if x.get('from', '').lower() == pins['liquidity'] and
                x.get('to', '').lower() == pins['position_manager'] and x.get('input', '').lower() == target_call]
    if lp_id == 0 or len(readings) != (1 if create else 2):
        raise ProjectionError('LP liquidity delta is missing or ambiguous')
    values = []
    for x in readings:
        successful(x)
        if x.get('type') != 'STATICCALL':
            raise ProjectionError('Invalid LP measurement call')
        value = int(words(x.get('output'), 1)[0], 16)
        if value >= 2**128:
            raise ProjectionError('LP units exceed uint128')
        values.append(value)
    added = values[-1] - (0 if create else values[0])
    if added < req['minimum_lp'] or added <= 0:
        raise ProjectionError('LP units do not meet the requested minimum')
    return {'source_usd_18': gross, 'required_deployed_usd_18': floor,
            'marginal_deployed_usd_18': deployed - incumbent_deployed,
            'net_contribution_usd_18': net, 'shares_added_raw': issued,
            'lp_liquidity_added_raw': added, 'lp_token_id': lp_id,
            'converted_amount_raw': acquired, 'simulation_gas_used': gas_used}
