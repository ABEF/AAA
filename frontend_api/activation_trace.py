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
CONFIGURABLE_RESULT = 'contributionResult(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint32)'
VALUE = 'value(address,uint256)'
MINT = 'mint(bytes32,int24,int24,uint256,uint256,uint128,uint256)'
INCREASE = 'increase(bytes32,uint256,uint256,uint256,uint128,uint256)'
SOURCE = '0x' + keccak256(b'SourceContributed(address,uint256,bytes32,address,uint256,uint256,address,uint256,bool)').hex()
SHARES = '0x' + keccak256(b'SharesAdded(uint256,uint256,uint256,uint256)').hex()
VERIFIED = '0x' + keccak256(b'ContributionVerified(uint256,uint256,uint256,uint256,uint256,uint256,uint160,bytes32)').hex()
BEGIN_ENTRY = 'beginEntry(uint256,bytes32,address,uint256)'
BEGIN_PRICING = 'begin(uint256,uint256,uint256,uint256,uint32)'
FINISH_PRICING = 'finish(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint32)'
NAV_PRICING = 'contributionNav(uint256)'
VALIDATE_PRICING = 'validateContribution(uint256,uint256,uint256,uint256,uint128,bool)'
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


def static_data(signature, *values):
    return selector(signature)+''.join(f'{int(v,16) if isinstance(v,str) else v:064x}' for v in values)


def pricing_witness(root,vault,check,pins,req,gross,economics,verify_historical):
    """Match the native dual-price phase machine; never reinterpret old traces."""
    helper=pins['contribution_pricing'];budget=pins['budget'];bucket=req['bucket']
    input_usd,supply,incumbent_nav,incumbent_deployed,deployed,idle,limits=economics
    if check.get('type')!='CALL':raise ProjectionError('Dual-price result must execute its authenticated phase transition')
    begun=child(root,pins['entry'],helper,BEGIN_ENTRY,'CALL')
    if (begun['input'].lower()!=static_data(BEGIN_ENTRY,req['id'],req['pool'],req['source'],req['amount']) or
            int(words(begun.get('output'),1)[0],16)!=gross):
        raise ProjectionError('Original source was not captured before external contribution calls')
    changing=[x for x in root.get('calls',[]) if x.get('type') not in ('STATICCALL',)]
    ended=child(root,pins['entry'],helper,'endEntry()','CALL')
    if not changing or changing[0] is not begun or changing[-1] is not ended or ended.get('output','0x')!='0x':
        raise ProjectionError('Contribution pricing does not bracket all Entry callbacks')
    validation=child(vault,pins['vault'],budget,VALIDATE_PRICING,'CALL')
    packed=req['_contribution_amount0'] | (req['_contribution_amount1'] << 128)
    expected=static_data(VALIDATE_PRICING,req['id'],bucket,gross,packed,req['minimum_lp'],int(not req['increase']))
    if validation['input'].lower()!=expected:
        raise ProjectionError('Raw contribution amounts differ from the captured pricing context')
    admitted=words(validation.get('output'),3)
    if (_address_word(admitted[0],native=True)!=req['token0'] or _address_word(admitted[1],native=True)!=req['token1'] or int(admitted[2],16)!=limits):
        raise ProjectionError('Captured source pair or execution policy differs')
    begin=child(validation,budget,helper,BEGIN_PRICING,'CALL')
    if begin['input'].lower()!=static_data(BEGIN_PRICING,req['id'],bucket,packed,gross,limits) or begin.get('output','0x')!='0x':
        raise ProjectionError('Budget did not authenticate the exact contribution pricing context')
    finish=child(check,budget,helper,FINISH_PRICING,'CALL')
    if finish['input'].lower()!=selector(FINISH_PRICING)+check['input'][10:].lower() or finish.get('output')!=check.get('output'):
        raise ProjectionError('Pricing result differs from the Vault accounting result')
    calls=vault.get('calls',[])
    navs=[x for x in calls if x.get('from','').lower()==pins['vault'] and x.get('to','').lower()==budget and
        x.get('input','').lower().startswith(selector(NAV_PRICING))]
    if len(navs)!=3:raise ProjectionError('Missing bounded contribution NAV phases')
    nav_values=[]
    for frame in navs:
        successful(frame)
        nested=child(frame,budget,helper,NAV_PRICING,'CALL')
        if (frame.get('type')!='CALL' or frame['input'].lower()!=calldata(NAV_PRICING,bucket) or
                nested['input'].lower()!=frame['input'].lower() or nested.get('output')!=frame.get('output')):
            raise ProjectionError('Contribution NAV phase differs from its immutable helper')
        nav_values.append([int(w,16) for w in words(frame.get('output'),2)])
    mint_calls=[x for x in calls if x.get('from','').lower()==pins['vault'] and x.get('to','').lower()==pins['liquidity'] and
        x.get('input','')[:10].lower() in (selector(MINT),selector(INCREASE))]
    if len(mint_calls)!=1:raise ProjectionError('Ambiguous LP deployment inside pricing phases')
    index=lambda frame:next(i for i,item in enumerate(calls) if item is frame)
    order=[index(x) for x in [validation,*navs,check]]
    if not order[0]<order[1]<order[2]<index(mint_calls[0])<order[3]<order[4]:
        raise ProjectionError('Contribution pricing phases are reordered')
    buckets=[x for x in calls if x.get('from','').lower()==pins['vault'] and x.get('to','').lower()==budget and
        x.get('input','').lower().startswith(selector('valueBucket(uint256,uint256,uint256)'))]
    if len(buckets)!=(2 if supply else 1):raise ProjectionError('Missing exact incumbent compound valuation')
    values=[]
    for frame in buckets:
        successful(frame)
        args=words('0x'+frame['input'][10:],3)
        nested=child(frame,budget,helper,'valueBucket(uint256,uint256,uint256)','STATICCALL')
        if (frame.get('type')!='STATICCALL' or int(args[0],16)!=bucket or nested['input'].lower()!=frame['input'].lower() or nested.get('output')!=frame.get('output')):
            raise ProjectionError('Compound valuation differs from the captured price vector')
        values.append(int(words(frame.get('output'),1)[0],16))
    if not index(mint_calls[0])<index(buckets[-1])<index(navs[2]) or supply and not index(navs[0])<index(buckets[0])<index(navs[1]):
        raise ProjectionError('Incumbent compound values are outside their captured phases')
    fresh=values[0] if supply else 0;late=values[-1]
    if (incumbent_deployed!=nav_values[1][0]+nav_values[0][1]+fresh or
            incumbent_nav!=incumbent_deployed+late or [deployed,idle]!=nav_values[-1]):
        raise ProjectionError('Incremental LP accounting includes repricing or incumbent assets')
    initial={};final={};epoch=None
    for frame in finish.get('calls',[]):
        if frame.get('from','').lower()!=helper:continue
        if frame.get('to','').lower()==budget and frame.get('input','')[:10].lower()==selector('compositionEpoch(uint256)'):
            successful(frame)
            if epoch is not None or frame.get('type')!='STATICCALL' or frame['input'].lower()!=calldata('compositionEpoch(uint256)',bucket):
                raise ProjectionError('Invalid historical compound epoch boundary')
            epoch=int(words(frame.get('output'),1)[0],16)
            if epoch>=2**64:raise ProjectionError('Historical compound epoch exceeds uint64')
        if frame.get('to','').lower()!=pins['fees'] or frame.get('input','')[:10].lower()!=selector('compoundBalance(uint256,address)'):
            continue
        successful(frame);args=words('0x'+frame['input'][10:],2);token=_address_word(args[1],native=True)
        amount=int(words(frame.get('output'),1)[0],16);phase=initial if epoch is None else final
        if frame.get('type')!='STATICCALL' or int(args[0],16)!=bucket or token in phase:
            raise ProjectionError('Invalid historical compound observation')
        phase[token]=amount
    if (bool(supply)!=(epoch is not None) or epoch==0 and final or not supply and final):
        raise ProjectionError('Historical compound denomination does not match the captured epoch')
    expected={token:amount for token,amount in initial.items() if token not in (req['token0'],req['token1'])}
    if epoch and final!=expected:
        raise ProjectionError('Historical compound changed between marking and share issuance')
    historical=[(token,amount,None) for token,amount in final.items() if amount]
    historical_value=0
    if historical:
        if verify_historical is None:raise ProjectionError('Historical dual-price compound is unreviewed')
        historical_value=verify_historical(historical)
        if type(historical_value) is not int or historical_value<0:raise ProjectionError('Invalid historical compound value')
    recorded=event(finish,helper,VERIFIED,['0x'+f'{req["id"]:064x}','0x'+f'{bucket:064x}'],6)
    lo,upper,marginal,net,spot,basis_hash=map(lambda w:int(w,16),recorded)
    issued,actual_net=map(lambda w:int(w,16),words(check.get('output'),2))
    if (lo!=gross or upper!=req['upper_input_usd'] or marginal!=deployed-incumbent_deployed or net!=actual_net or
            not 0<spot<2**160 or basis_hash==0):
        raise ProjectionError('Contribution verification event differs from measured LP and original source bounds')
    # Each later guard must observe the same source/pair policy and rounds as
    # the independently reviewed preparation snapshot, never a callback price.
    stack=[begun,begin,*navs,finish,ended];observed=set()
    while stack:
        frame=stack.pop();stack.extend(frame.get('calls',[]))
        if frame.get('from','').lower()!=helper or frame.get('to','').lower()!=pins['oracle'] or frame.get('input','')[:10].lower()!=selector('priceBounds(address)'):
            continue
        successful(frame);asset=_address_word(words('0x'+frame['input'][10:],1)[0],native=True)
        if asset in req['reviewed_price_bounds']:
            expected=req['reviewed_price_bounds'][asset]
            if frame.get('type')!='STATICCALL' or words(frame.get('output'),3)!=[f'{expected["lower"]:064x}',f'{expected["upper"]:064x}',expected['fingerprint'][2:]]:
                raise ProjectionError('Captured price or policy fingerprint changed during execution')
            observed.add(asset)
    if not set(req['reviewed_price_bounds'])<=observed:
        raise ProjectionError('Original source and pool price fingerprints are missing')
    return historical_value,upper


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
    dual_pricing = req.get('pricing_version',1)==2
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
    if req.get('route_kind') == 2:
        converted=child(root,pins['entry'],req['v4_executor'],'execute(bytes32,uint256,uint256,uint256)','CALL')
        expected=calldata('execute(bytes32,uint256,uint256,uint256)',req['route'],req['amount'],req['minimum_out'],req['deadline'])
        if (converted['input'].lower()!=expected or int(words(converted.get('output'),1)[0],16)!=acquired or
                _quantity(converted.get('value','0x0'))!=(req['amount'] if req['source']==ZERO else 0)):
            raise ProjectionError('Typed v4 child call differs from exact reviewed conversion')
    a0, a1 = (acquired, 0) if req['output'] == req['token0'] else (0, acquired)
    if dual_pricing:
        if a0>=2**128 or a1>=2**128:raise ProjectionError('Contribution amount exceeds packed raw-asset bounds')
        req['_contribution_amount0']=a0;req['_contribution_amount1']=a1
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
                  x.get('input','')[:10].lower() in (selector(RESULT),selector(LEGACY_RESULT),selector(CONFIGURABLE_RESULT))]
    if len(candidates)!=1 or candidates[0].get('type')!=('CALL' if dual_pricing else 'STATICCALL'):
        raise ProjectionError('Missing or ambiguous reviewed contribution result')
    check = successful(candidates[0])
    configurable = req.get('routing_version',1)==2
    if configurable != (check['input'][:10].lower()==selector(CONFIGURABLE_RESULT)):
        raise ProjectionError('Contribution result differs from explicit execution-policy profile')
    current = check['input'][:10].lower()!=selector(LEGACY_RESULT)
    values = words('0x'+check['input'][10:],8 if current else 7)
    if current:
        if int(values[0],16)!=req['bucket']:
            raise ProjectionError('Contribution result uses a different bucket')
        values=values[1:]
    input_usd, supply, incumbent_nav, incumbent_deployed, deployed, idle, slippage = [
        int(x, 16) for x in values]
    packed_limits=slippage
    loss=req.get('execution_loss_bps',100)
    if configurable:
        if slippage >= 2**32 or slippage >> 16 != loss:
            raise ProjectionError('Contribution execution-loss snapshot differs from reviewed policy')
        slippage &= 65535
    if not 0 <= loss <= (1000 if configurable else 100):
        raise ProjectionError('Invalid reviewed contribution loss cap')
    upper_input=gross
    if dual_pricing:
        if not current or not configurable:raise ProjectionError('Dual pricing requires the current bounded execution-policy profile')
        historical_value,upper_input=pricing_witness(root,vault,check,pins,req,gross,
            (input_usd,supply,incumbent_nav,incumbent_deployed,deployed,idle,packed_limits),verify_historical)
    else:
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
    floor = upper_input - upper_input * loss // 10000
    if (input_usd != gross or slippage != max_slippage or not 0 < slippage <= 200 or
            deployed < incumbent_deployed + floor or net != deployed + idle - incumbent_nav or
            net < floor or net < upper_input * (10000 - slippage) // 10000 or
            idle > (deployed + idle) * 500 // 10000 or deployed == 0 or
            supply and incumbent_nav == 0):
        raise ProjectionError('Simulated contribution violates its original-source execution budget')
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
