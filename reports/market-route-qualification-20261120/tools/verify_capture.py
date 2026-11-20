"""Independent offline wire/data checks. No RPC, signing, tests or adoption.

Usage: python verify_capture.py EVIDENCE_ROOT OUTPUT_JSON
Only retained files and exact Git baseline blobs are read. Runtime equality is
the original source-qualified identity boundary, not independent recompilation.
"""
from fractions import Fraction
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
BASELINE = '73658567cb605b58c992698e2103535e782269dd'
ZERO = '0x' + '0' * 40
ZZZ = '0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
CORE = '0x8366a39cc670b4001a1121b8f6a443a643e40951'
VIEW = '0xf3334192d15450cdd385c8b70e03f9a6bd9e673b'
QUOTER = '0x8dc178efb8111bb0973dd9d722ebeff267c98f94'
SELECTED = '0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
CL = '0x78f3556b67e17df817d51ef5a990cdaf09e8d3a9'
CL2 = '0x5058adee53b04e374d8bedbad634bc4778f50b22'
PYTH = '0x8250f4af4b972684f7b336503e2d6dfedeb1487a'
API3 = '0x3c57b17052bdd5ff75b1f03c5f3afddbcfb8de1c'
ETH_ID = '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace'
STOA = '0x27958279f95225b2a5517e7dd12b6fc0317e5c5d'
WETH = '0x0bd7d308f8e1639fab988df18a8011f41eacad73'
V2 = '0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f'
V3 = '0x1f7d7550b1b028f7571e69a784071f0205fd2efa'
GENESIS = '0xaad15f3d702aaea00caf3e9bb56395efe9127bc3b31b24921abf1eee3409305c'
URL = 'https://robinhood.rpc.pinax.network'
ALLOWED = {'eth_chainId', 'eth_getBlockByNumber', 'eth_getCode', 'eth_getStorageAt', 'eth_call'}
DATA = ['reports/predeployment-qualification-20261113/markets/CAPTURE_PARTIAL.json.gz',
        'reports/market-followup-20261109/routes/v4-state.json']


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        check(key not in out, 'Duplicate JSON field')
        out[key] = value
    return out


def load(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def git_bytes(name):
    return subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)


def pinned(name):
    current = (ROOT / name).read_bytes()
    check(current == git_bytes(name), 'Baseline data/source drift: ' + name)
    return current


def word(v):
    n = int(v, 16) if isinstance(v, str) else v
    return (n % (1 << 256)).to_bytes(32, 'big')


def words(value, count=None):
    check(type(value) is str and value.startswith('0x') and (len(value)-2) % 64 == 0, 'ABI word envelope')
    raw = bytes.fromhex(value[2:])
    out = [int.from_bytes(raw[i:i+32], 'big') for i in range(0, len(raw), 32)]
    check(count is None or len(out) == count, 'ABI word count')
    return out


def hexbytes(value):
    check(type(value) is str and value.startswith('0x') and len(value) % 2 == 0, 'Hex envelope')
    return bytes.fromhex(value[2:])


def rat(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator),
            'decimal': format(value.numerator/value.denominator, '.18g')}


def normalized(response):
    return {'rpc_error': response['error']} if 'error' in response else response['result']


class Wire:
    def __init__(self, path, source_files):
        self.path = path
        self.raw_capture = (path/'CAPTURE.json').read_bytes()
        self.capture = load(self.raw_capture)
        self.wire = load((path/'RPC.json').read_bytes())
        c, w = self.capture, self.wire
        if 'baseline' in c:
            check(c['baseline'] == BASELINE, 'Capture baseline')
        else:
            check(c['phase'] in ['v3-state', 'v3-quotes'], 'Missing capture baseline')
        check(c['public_transactions'] == 0 and c['production_approved'] is False and c['configuration_adopted'] is False, 'Capture scope')
        check(w['endpoint'] == URL and w['read_only'] is True and w['retries'] == 0, 'Transport boundary')
        check((w['maximum_calls'], w['maximum_seconds'], w['actual_start_interval_seconds'], w['maximum_response_bytes']) == (33, 90, 2, 262144), 'Transport ceilings')
        self.rows = w['rows']
        check(0 < len(self.rows) <= 33 and len(self.rows) == c['request_count'], 'Request count')
        self.responses = []
        previous = None
        for i, row in enumerate(self.rows, 1):
            request = row['request']
            check(request['jsonrpc'] == '2.0' and type(request['id']) is int and request['id'] == row['id'] == i, 'Request identity/order')
            check(request['method'] in ALLOWED, 'Non-read RPC')
            check(row.get('http_status') == 200 and 'error_class' not in row, 'Transport failure in qualified phase')
            start, end = row['started_elapsed_seconds'], row['finished_elapsed_seconds']
            check(0 <= start <= end <= 90 and 0 < row['timeout_seconds'] <= 12, 'Request timing bounds')
            check(end-start <= row['timeout_seconds']+0.1, 'Absolute HTTP allowance')
            check(previous is None or start-previous >= 2-1e-6, 'Actual-start pacing')
            previous = start
            name = row['raw_file']
            check(name == f'rpc-{i:02d}.raw', 'Raw path')
            raw = (path/name).read_bytes()
            check(len(raw) == row['raw_bytes'] <= 262144 and sha(raw) == row['raw_sha256'], 'Raw response digest/bound')
            response = load(raw)
            check(response == row['response'], 'Raw versus recorded response')
            check(response['jsonrpc'] == '2.0' and type(response['id']) is int and response['id'] == i and ('result' in response) != ('error' in response), 'Response envelope')
            if 'error' in response:
                check(type(response['error']) is dict and response['error'].get('code') == 3, 'Unexpected provider error')
            self.responses.append(normalized(response))
        check(self.rows[-1]['finished_elapsed_seconds'] <= c['elapsed_seconds'] <= 90, 'Phase elapsed')
        for name, digest in c.get('source_pins', {}).items():
            name = name.replace('\\', '/')
            if name.startswith(('src/', 'zzz_ops/')):
                check(sha(pinned(name)) == digest, 'Captured production pin')
            else:
                check(digest in source_files, 'Missing retained producer bytes for ' + name)
        if 'source_sha256' in c:
            check(c['source_sha256'] in source_files, 'Missing retained secondary producer bytes')
        self.pos = 0

    def take(self, method, params):
        check(self.pos < len(self.rows), 'Missing wire request')
        row = self.rows[self.pos]
        check(row['request']['method'] == method and row['request']['params'] == params, 'Unexpected wire request at ' + str(self.pos+1))
        value = self.responses[self.pos]
        self.pos += 1
        return value

    def done(self):
        check(self.pos == len(self.rows), 'Unconsumed wire requests')

    def call(self, target, signature='', args=(), data=None, gas=500000):
        data = data or '0x' + (keccak(signature.encode())[:4] + b''.join(word(x) for x in args)).hex()
        return self.take('eth_call', [{'to': target, 'data': data, 'gas': hex(gas)}, self.selector])

    def code(self, target, expected=None):
        raw = hexbytes(self.take('eth_getCode', [target, self.selector]))
        row = {'address': target, 'bytes': len(raw), 'keccak256': '0x'+keccak(raw).hex()}
        if expected is not None:
            check(row['keccak256'] == expected, 'Runtime pin mismatch')
            row.update(expected_prior_keccak256=expected, matches_prior_runtime=True)
        return row

    def anchor(self, header, first=False):
        selector = 'latest' if first else hex(int(header['number'], 16))
        check(self.take('eth_getBlockByNumber', [selector, False]) == header, 'Canonical header mismatch')
        self.selector = {'blockHash': header['hash'], 'requireCanonical': True}


def states(w, pools):
    slots = []
    for p in pools:
        check('0x'+keccak(b''.join(word(x) for x in p['key'])).hex() == p['poolId'], 'Pool key digest')
        slot = int.from_bytes(keccak(word(p['poolId'])+word(6)), 'big')
        slots.extend([slot, slot+3])
    values = []
    for begin in range(0, len(slots), 50):
        chunk = slots[begin:begin+50]
        data = '0x'+(keccak(b'extsload(bytes32[])')[:4]+word(32)+word(len(chunk))+b''.join(word(x) for x in chunk)).hex()
        result = words(w.call(CORE, data=data))
        check(result[:2] == [32, len(chunk)] and len(result) == len(chunk)+2, 'Bulk state ABI')
        values.extend(result[2:])
    out = []
    for i, p in enumerate(pools):
        packed, liquidity = values[i*2:i*2+2]
        tick = (packed >> 160) & 0xffffff
        tick = tick-(1 << 24) if tick & (1 << 23) else tick
        slot = dict(sqrtPriceX96=packed & ((1 << 160)-1), tick=tick,
                    protocolFee=(packed >> 184) & 0xffffff, lpFee=(packed >> 208) & 0xffffff)
        check(packed >> 232 == 0 and 0 <= liquidity < 1 << 128 and slot['sqrtPriceX96'] > 0, 'Pool state bounds')
        check(slot['lpFee'] == p['key'][2], 'Static fee changed')
        out.append(dict(poolId=p['poolId'], key=p['key'], slot0=slot, active_liquidity=str(liquidity)))
    return out


def finish(w, header):
    w.anchor(header)
    check(w.capture['final_header'] == header and w.capture['canonical_final_recheck'] is True, 'Published closure differs from raw header')
    w.done()


def registry_keys(value):
    if isinstance(value, dict):
        return {'error': value}
    v = words(value)
    check(v[:1] == [32] and len(v) >= 2 and v[1] <= 64 and len(v) == 2+5*v[1], 'Registry key ABI')
    out = []
    for i in range(v[1]):
        x = v[2+5*i:7+5*i]
        tick = x[3]-(1 << 256) if x[3] >> 255 else x[3]
        check(x[0] < 1 << 160 and x[1] < 1 << 160 and x[2] < 1 << 24 and 0 < tick <= 32767 and x[4] < 1 << 160, 'Registry key widths')
        key = ['0x'+format(x[0], '040x'), '0x'+format(x[1], '040x'), x[2], tick, '0x'+format(x[4], '040x')]
        out.append(dict(key=key, poolId='0x'+keccak(b''.join(word(y) for y in key)).hex(), discovery_only=True))
    return out


def fee(p, direction):
    packed = p['slot0']['protocolFee']
    protocol = packed & 4095 if direction else packed >> 12
    lp = p['slot0']['lpFee']
    check(protocol <= 1000 and lp < 1000000, 'Fee bound')
    return protocol+lp-protocol*lp//1000000


def quote_result(value, pool, direction, amount, gas):
    if isinstance(value, dict):
        error = value['rpc_error']
        raw = hexbytes(error.get('data', '0x'))
        wrapper = keccak(b'UnexpectedRevertBytes(bytes)')[:4]
        if raw[:4] != wrapper:
            return dict(status='unclassified_rpc_revert', data=error.get('data'), inferred_cause=None)
        check(len(raw) >= 68 and int.from_bytes(raw[4:36], 'big') == 32, 'Wrapped error offset')
        length = int.from_bytes(raw[36:68], 'big')
        check(len(raw) == 68+((length+31)//32)*32 and not any(raw[68+length:]), 'Wrapped error padding')
        inner = raw[68:68+length]
        if inner[:4] == keccak(b'NotEnoughLiquidity(bytes32)')[:4]:
            check(len(inner) == 36 and inner[4:] == hexbytes(pool['poolId']), 'Incomplete-input pool identity')
            return dict(status='full_input_not_consumed', wrapped_data='0x'+inner.hex())
        return dict(status='opaque_wrapped_revert' if not inner else 'other_wrapped_revert', wrapped_data='0x'+inner.hex(), inferred_cause=None)
    out, used = words(value, 2)
    check(out > 0 and 0 < used < gas, 'Positive quote output/gas')
    spot = Fraction(pool['slot0']['sqrtPriceX96']**2, 1 << 192)
    expected = amount*spot if direction else amount/spot
    f = fee(pool, direction)
    net = amount*(1000000-f)//1000000
    after_fee = net*spot if direction else net/spot
    return dict(status='positive_full_input_quote', output_raw=str(out), quoter_reported_gas=used,
                own_spot_gross_loss_bps=rat((1-Fraction(out, 1)/expected)*10000),
                own_spot_additional_loss_bps=rat((1-Fraction(out, 1)/after_fee)*10000),
                gross_3pct_screen=out >= expected*Fraction(97,100),
                gross_1pct_screen=out >= expected*Fraction(99,100),
                additional_1pct_screen=out >= after_fee*Fraction(99,100),
                analytical_only=True, post_state_qualified=False, complete_operation_qualified=False)


def v3_state(w, discovery, header, factories):
    check(w.capture['prior_capture_sha256'] == sha(discovery.raw_capture) and w.capture['anchor'] == discovery.capture['anchor'], 'V3 state provenance')
    check('stopped' not in w.capture, 'Incomplete V3 state')
    w.anchor(header)
    rows = []
    for lead in factories:
        if lead['kind'] != 'v3' or isinstance(lead['result'], dict):
            continue
        value = words(lead['result'], 1)[0]
        if not value:
            continue
        check(value < 1 << 160, 'V3 lead address width')
        address = '0x'+format(value,'040x')
        row = dict(address=address, reported_fee=lead['fee'], factory_lead=lead['factory'], qualified=False)
        runtime = w.code(address)
        row['runtime'] = {name:runtime[name] for name in ['bytes','keccak256']}
        for signature in ['factory()','token0()','token1()','fee()','tickSpacing()','liquidity()','slot0()']:
            row[signature] = w.call(address,signature)
        token0,token1 = (words(row[name],1)[0] for name in ['token0()','token1()'])
        check({token0,token1} == {int(ZZZ,16),int(WETH,16)} and token0 < token1, 'V3 fixed-pair token identity/order')
        check(words(row['factory()'],1)[0] == int(lead['factory'],16) and words(row['fee()'],1)[0] == lead['fee'], 'V3 factory/fee reciprocal reads')
        spacing = words(row['tickSpacing()'],1)[0]
        check(0 < spacing < 1 << 23 and words(row['liquidity()'],1)[0] < 1 << 128, 'V3 spacing/liquidity widths')
        slot = words(row['slot0()'],7)
        tick = slot[1]-(1 << 256) if slot[1] >> 255 else slot[1]
        check(0 < slot[0] < 1 << 160 and -(1 << 23) <= tick < 1 << 23 and all(x < 1 << 16 for x in slot[2:5]) and slot[5] < 1 << 8 and slot[6] in [0,1], 'V3 slot0 ABI widths')
        row['balances'] = {}
        for token in [token0,token1]:
            target = '0x'+format(token,'040x')
            value = w.call(target,'balanceOf(address)',(address,))
            words(value,1)
            row['balances'][target] = value
        rows.append(row)
    check(rows == w.capture['pools'], 'Published V3 state rows')
    finish(w,header)
    return rows


def v3_quotes(w, prior, native, header, pools):
    check(w.capture['prior_capture_sha256'] == sha(prior.raw_capture) and
          w.capture['native_capture_sha256'] == sha(native.raw_capture) and
          w.capture['anchor'] == prior.capture['anchor'] and 'stopped' not in w.capture,
          'V3 quote provenance/completion')
    w.anchor(header)
    address = '0x33e885ed0ec9bf04ecfb19341582aadcb4c8a9e7'
    code = w.code(address)
    quoter = dict(address=address,bytes=code['bytes'],keccak256=code['keccak256'],independently_compiled_runtime_verified=False)
    quoter['factory'] = w.call(address,'factory()')
    quoter['WETH9'] = w.call(address,'WETH9()')
    check(words(quoter['factory'],1)[0] == int(V3,16) and words(quoter['WETH9'],1)[0] == int(WETH,16), 'V3 quote factory/WETH identity')
    check(quoter == w.capture['quoter'], 'Published unqualified V3 quoter')
    decimals = w.call(WETH,'decimals()')
    check(decimals == w.capture['weth_decimals'] and words(decimals,1) == [18], 'WETH decimals')
    answer = words(native.capture['feeds']['chainlink_primary']['round'],5)
    eth_decimals = words(native.capture['feeds']['chainlink_primary']['decimals'],1)[0]
    eth = Fraction(answer[1],10**eth_decimals)
    expected = []
    for pool in pools:
        expected += [(pool,WETH,ZZZ,int(n*10**18/eth),n) for n in [5,50]]
        expected += [(pool,ZZZ,WETH,n*10**18,None) for n in [1,100,1000]]
    check(len(expected) == len(w.capture['quotes']), 'V3 quote matrix size')
    summaries = []
    for item,(pool,token_in,token_out,amount,nominal) in zip(w.capture['quotes'],expected):
        pool_fee = pool['reported_fee']
        args = [token_in,token_out,amount,pool_fee,0]
        data = '0x'+(keccak(b'quoteExactInputSingle((address,address,uint256,uint24,uint160))')[:4]+b''.join(word(x) for x in args)).hex()
        value = w.call(address,data=data,gas=500000)
        row = dict(pool=pool['address'],fee_pips=pool_fee,token_in=token_in,token_out=token_out,input_raw=str(amount),
                   nominal_USD_from_single_ETH_round_only=nominal,result=value,gas_ceiling=500000,sqrt_price_limit_x96=0,
                   complete_input_consumption_proved=False,complete_operation_qualified=False)
        check(row == item, 'Published V3 quote input/response')
        summary = {k:row[k] for k in ['pool','fee_pips','token_in','token_out','input_raw','gas_ceiling','complete_input_consumption_proved','complete_operation_qualified']}
        if isinstance(value,dict):
            summary.update(status='rpc_revert',data=value['rpc_error'].get('data'),inferred_cause=None)
        else:
            output,sqrt_after,crossed,gas = words(value,4)
            check(0 < sqrt_after < 1 << 160 and crossed < 1 << 32 and 0 < gas < 500000, 'V3 quote output widths/gas')
            sqrt_before = words(pool['slot0()'],7)[0]
            spot = Fraction(sqrt_before**2,1 << 192)
            ideal = amount*spot if token_in == WETH else amount/spot
            net = amount*(1000000-pool_fee)//1000000
            after_fee = net*spot if token_in == WETH else net/spot
            summary.update(status='positive_quote_full_consumption_unproved' if output else 'zero_output_quote',
                           output_raw=str(output),sqrt_price_after=str(sqrt_after),initialized_ticks_crossed=crossed,
                           quoter_reported_gas=gas,own_spot_gross_loss_bps=rat((1-Fraction(output,1)/ideal)*10000),
                           own_spot_additional_loss_bps=rat((1-Fraction(output,1)/after_fee)*10000),
                           gross_1pct_screen=output >= ideal*Fraction(99,100),additional_1pct_screen=output >= after_fee*Fraction(99,100),
                           analytical_only=True,runtime_behavior_qualified=False)
        summaries.append(summary)
    finish(w,header)
    return summaries


def run(evidence):
    global keccak
    check(sha(pinned('zzz_ops/abi.py')) == '154d92685b6e473bd064880ec15a16a9b8aafa0b9104df671538cf1375a7250d', 'Keccak helper identity')
    sys.path.insert(0, str(ROOT))
    sys.dont_write_bytecode = True
    keccak = importlib.import_module('zzz_ops.abi').keccak256
    raw_prior, raw_pools = (pinned(name) for name in DATA)
    prior = load(gzip.decompress(raw_prior)); inventory = load(raw_pools)
    source_files = {}
    for directory in [evidence, Path(__file__).parent]:
        for path in directory.rglob('*.py'):
            check(path.is_file(), 'Source archive entry')
            source_files.setdefault(sha(path.read_bytes()), []).append(str(path))
    phases = {name: Wire(evidence/name, source_files) for name in ['state', 'state-continuation', 'quotes', 'discovery', 'v3-state', 'v3-quotes']}
    original, continuation, quotes, discovery = (phases[name] for name in ['state', 'state-continuation', 'quotes', 'discovery'])
    header = original.capture['anchor']['header']
    check(original.capture['anchor']['number'] == int(header['number'],16) and original.capture['anchor']['hash'] == header['hash'] and original.capture['anchor']['timestamp'] == int(header['timestamp'],16), 'Anchor fields')
    check(original.take('eth_chainId', []) == '0x1237', 'Chain')
    check(original.take('eth_getBlockByNumber', ['0x0', False])['hash'] == GENESIS, 'Genesis')
    original.anchor(header, first=True)
    runtimes = {name: original.code(address, prior['runtimes'][name]['keccak256']) for name, address in [('core', CORE), ('state_view', VIEW), ('quoter', QUOTER), ('zzz', ZZZ)]}
    check(runtimes == original.capture['runtimes'], 'Published runtime rows')
    pools = states(original, inventory)
    check(all(p['key'][0] == ZERO and p['key'][1] == ZZZ and p['key'][4] == ZERO for p in pools), 'Historical native hookless inventory scope')
    check(pools == original.capture['pools'] and len(pools) == 95, 'Published pool states')
    feeds = {}
    for name, address in [('chainlink_primary', CL), ('chainlink_secondary', CL2)]:
        feeds[name] = dict(address=address, runtime=original.code(address, prior['feeds'][name]['runtime']['keccak256']),
                           aggregator=original.call(address, 'aggregator()'))
    check(feeds == original.capture['feeds'], 'Published feed prefix')
    check(original.capture['stopped']['exception_type'] == 'KeyError' and original.capture['stopped']['provider_stopped'] is False, 'Original setup failure not preserved')
    finish(original, header)
    check(continuation.capture['prior_capture_sha256'] == sha(original.raw_capture), 'Continuation source capture')
    check(continuation.capture['anchor'] == original.capture['anchor'] and continuation.capture['runtimes'] == runtimes and continuation.capture['pools'] == pools, 'Continuation state changed')
    continuation.anchor(header)
    aggregator = '0x'+format(words(feeds['chainlink_primary']['aggregator'],1)[0], '040x')
    check(aggregator == prior['feeds']['chainlink_aggregator']['address'], 'Aggregator target')
    feeds['chainlink_aggregator'] = continuation.code(aggregator, prior['feeds']['chainlink_aggregator']['runtime']['keccak256'])
    feeds['chainlink_primary'].update(round=continuation.call(CL, 'latestRoundData()'), decimals=continuation.call(CL, 'decimals()'))
    for name, address, signature, args in [('pyth', PYTH, 'getPriceUnsafe(bytes32)', (ETH_ID,)), ('api3', API3, 'read()', ())]:
        old = prior['feeds'][name]
        row = dict(address=address, runtime=continuation.code(address, old['runtime']['keccak256']))
        slot = '0x'+word(int.from_bytes(keccak(b'eip1967.proxy.implementation'),'big')-1).hex()
        implementation = continuation.take('eth_getStorageAt', [address, slot, continuation.selector])
        check(implementation == old['implementation_slot'], 'Proxy implementation changed')
        row.update(implementation_slot=implementation, implementation_runtime=continuation.code('0x'+implementation[-40:], old['implementation_runtime']['keccak256']),
                   observation=continuation.call(address, signature, args))
        feeds[name] = row
    check(feeds == continuation.capture['feeds'], 'Published completed feed rows')
    registry_raw = continuation.call(STOA, 'keysFor(address,address)', (WETH, ZZZ))
    registry = dict(address=STOA, raw=registry_raw, decoded=registry_keys(registry_raw), qualified=False)
    check(registry == continuation.capture['stoa_registry'], 'Published registry keys')
    finish(continuation, header)
    for p in [quotes, discovery]:
        check(p.capture['prior_capture_sha256'] == sha(continuation.raw_capture) and p.capture['anchor'] == continuation.capture['anchor'], 'Phase provenance/anchor')
        p.anchor(header)
        check('stopped' not in p.capture, 'Incomplete phase')
    check('stopped' not in continuation.capture, 'Incomplete continuation')
    selected = next(x for x in pools if x['poolId'] == SELECTED)
    main = max((x for x in pools if x['poolId'] != SELECTED and x['key'][2] <= 100000), key=lambda x:int(x['active_liquidity']))
    answer = words(feeds['chainlink_primary']['round'],5); decimals = words(feeds['chainlink_primary']['decimals'],1)[0]
    check(0 < answer[1] < 1 << 255 and 0 < answer[2] <= answer[3] <= int(header['timestamp'],16) and answer[0] <= answer[4] and decimals <= 18, 'Diagnostic ETH sizing round')
    eth = Fraction(answer[1],10**decimals)
    cheap = [x for x in pools if fee(x,False) < 10000 and x['key'][2] < 100000 and 10**12 < x['slot0']['sqrtPriceX96'] < 10**40]
    expected_quotes = []
    for p in cheap:
        expected_quotes += [(p,False,n*10**18,500000) for n in [1,100,1000]]
        expected_quotes.append((p,True,int(5*10**18/eth),500000))
    for p in [selected,main]:
        expected_quotes += [(p,True,int(50*10**18/eth),500000),(p,False,10**18,500000),(p,False,100*10**18,500000)]
    low = next(p for p in cheap if p['key'][2] == 75)
    expected_quotes.append((low,False,10**18,1000000))
    check(len(quotes.capture['quotes']) == len(expected_quotes), 'Diagnostic quote matrix size')
    summaries = []
    for observed, (p,direction,amount,gas) in zip(quotes.capture['quotes'], expected_quotes):
        data = '0x'+(keccak(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))')[:4]+word(32)+b''.join(word(x) for x in p['key'])+word(int(direction))+word(amount)+word(256)+word(0)).hex()
        value = quotes.call(QUOTER, data=data, gas=gas)
        expected = dict(pool_id=p['poolId'], key=p['key'], zero_for_one=direction, input_raw=str(amount), result=value,
                        gas_ceiling=gas, diagnostic_higher_gas_only=gas != 500000, known_fee_pips=fee(p,direction), postspot=None, complete_operation_qualified=False)
        check(observed == expected, 'Published quote response or inputs differ')
        summaries.append(dict(pool_id=p['poolId'], zero_for_one=direction, input_raw=str(amount), gas_ceiling=gas,
                              fee_pips=fee(p,direction), **quote_result(value,p,direction,amount,gas)))
    finish(quotes, header)
    leads = {}
    for name,address in [('v2',V2),('v3',V3),('stoa',STOA),('weth',WETH)]:
        row = discovery.code(address); row['qualified'] = False; leads[name] = row
    check(leads == discovery.capture['unqualified_discovery_runtimes'], 'Unqualified discovery code rows')
    factories = [dict(kind='v2', factory=V2, result=discovery.call(V2,'getPair(address,address)',(WETH,ZZZ)))]
    for f in [100,500,2500,3000,10000]:
        factories.append(dict(kind='v3',factory=V3,fee=f,result=discovery.call(V3,'getPool(address,address,uint24)',(WETH,ZZZ,f))))
    check(factories == discovery.capture['factory_leads'], 'Factory discovery results')
    decoded = registry['decoded']
    extra = [p for p in decoded if p['poolId'] not in {x['poolId'] for x in pools}] if isinstance(decoded,list) else []
    extra_states = states(discovery,extra) if extra else []
    check(extra_states == discovery.capture['additional_v4_states'] and discovery.capture['stoa_registry_available'] == isinstance(decoded,list), 'Registry discovery states')
    finish(discovery, header)
    v3_rows = v3_state(phases['v3-state'],discovery,header,factories)
    v3_quote_rows = v3_quotes(phases['v3-quotes'],phases['v3-state'],continuation,header,v3_rows)
    positive = [x for x in summaries if x['status'] == 'positive_full_input_quote']
    return dict(schema=1, successful=True, verification_kind='new_independent_offline_wire_and_rational_analysis', baseline=BASELINE,
                verifier_sha256=sha(Path(__file__).read_bytes()),
                data_dependencies={name:sha(raw) for name,raw in zip(DATA,[raw_prior,raw_pools])},
                phases={name:dict(capture_sha256=sha(w.raw_capture),requests=len(w.rows),elapsed_seconds=w.capture['elapsed_seconds'],
                                  canonical_header_checked=True,original_failure_preserved=name == 'state') for name,w in phases.items()},
                total_http_requests=sum(len(w.rows) for w in phases.values()), known_native_pools=len(pools),
                original_failed_phase='16call KeyError before missing ETH/secondary/registry reads; no provider retry',
                diagnostic_quote_count=len(summaries), positive_quote_count=len(positive), quote_analysis=summaries,
                cheap_fee_only_count_before_extreme_filter=sum(fee(p,False)<10000 for p in pools),
                cheap_diagnostic_pool_ids=[p['poolId'] for p in cheap],
                excluded_cheap_extreme_pool_ids=[p['poolId'] for p in pools if fee(p,False)<10000 and p not in cheap],
                stoa_discovery_count=len(decoded) if isinstance(decoded,list) else None, extra_v4_states=len(extra_states),
                v3_discovered_pools=len(v3_rows), v3_pool_states=v3_rows,
                v3_quote_count=len(v3_quote_rows), v3_quote_analysis=v3_quote_rows,
                known_largest_raw_L_pool=main['poolId'],
                selected_zzz_per_eth=rat(Fraction(selected['slot0']['sqrtPriceX96']**2,1<<192)),
                known_largest_eth_per_zzz_ratio_to_selected=rat(Fraction(selected['slot0']['sqrtPriceX96']**2,main['slot0']['sqrtPriceX96']**2)),
                production_approved=False, source_or_route_adopted=False, safeguards_or_limits_changed=False,
                limitations=['One provider/finite captured anchor; not global discovery, TVL or provider-completeness proof.',
                             'Pinned runtime identity reuses prior source qualification; no independent recompilation.',
                             'Quotes are finite full-input diagnostics, not actual PoPL swap fractions or marginal deployed LP.',
                             'Own-spot analytical screens are not independently qualified USD bounds or final live-source agreement.',
                             'Native-v4 quotes lack post-state; v3 post-sqrt does not prove complete input consumption or current-profile compatibility.',
                             'No full-operation gas/fees, HTTP production API or operating acceptance.',
                             'Discovery factories/registry/WETH/hook pool remain unqualified and unsupported by current direct native-v4 profile.',
                             'No online probes, transactions, production tests, code changes or adoption by this verifier.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence_root',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    check(not args.output.exists(), 'Output must be a new file')
    result = run(args.evidence_root.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as handle:
        json.dump(result,handle,indent=2,sort_keys=True);handle.write('\n')
    print(json.dumps({key:result[key] for key in ['successful','total_http_requests','known_native_pools','diagnostic_quote_count','positive_quote_count','extra_v4_states','production_approved']}))


if __name__ == '__main__':
    main()
