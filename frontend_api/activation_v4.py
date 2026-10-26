"""Strict explicit typed-v4 route observation, at the preparation's pinned block.

No router fallback, raw calldata, hook or LP-pool admission is inferred here.
"""
from frontend_api.activation_config import NATIVE_ASSET_CODE_HASH
from frontend_api.service import ProjectionError, ZERO, _address_word
from zzz_ops.abi import keccak256
from zzz_ops.tick_math import decode_slot0

DOMAIN = keccak256(b'ZZZ_TYPED_V4_ROUTE_V1')


def route_output(p, cfg, req, pins, block):
    route = req['route']; helper = pins['v4_executor']; entry = pins['entry']
    if not 0 < req['amount'] < 2**127:
        raise ProjectionError('Typed v4 input exceeds signed settlement bounds')
    data = p._call(entry, 'v4Route(bytes32)', route, block=block, words=14)
    if (data != p._call(helper, 'route(bytes32)', route, block=block, words=14) or
            data != p._call(helper, 'validate(bytes32)', route, block=block, words=14)):
        raise ProjectionError('Typed v4 route validation differs from its descriptor')
    identity = DOMAIN + p.chain.to_bytes(32, 'big') + int(helper, 16).to_bytes(32, 'big') + int(entry, 16).to_bytes(32, 'big')
    if '0x' + keccak256(identity + bytes.fromhex(''.join(data))).hex() != route:
        raise ProjectionError('Typed v4 domain or policy identity changed')
    source, output, a0, a1 = [_address_word(x, native=True) for x in data[:4]]
    fee, spacing = int(data[4], 16), int(data[5], 16)
    hook = _address_word(data[6], native=True)
    manager, state = map(_address_word, data[7:9])
    if (source != req['source'] or output not in (req['token0'], req['token1']) or
            source == output or a0 >= a1 or {source, output} != {a0, a1} or hook != ZERO or
            fee >= 1_000_000 or not 1 <= spacing <= 32767 or int(data[13], 16) == 0):
        raise ProjectionError('Typed v4 route differs from its reviewed directed pair')
    for target, digest in zip((source, output, manager, state), data[9:13]):
        expected = (NATIVE_ASSET_CODE_HASH if target == ZERO else
                    cfg.tokens[target]['code_hash'] if target in cfg.tokens else cfg.dependencies.get(target))
        if expected is None or expected != '0x' + digest:
            raise ProjectionError('Unreviewed typed v4 dependency')
        if target != ZERO: p._code(target, expected, block)
    if _address_word(p._call(state, 'poolManager()', block=block)[0]) != manager:
        raise ProjectionError('Typed v4 state view binding changed')
    pool = '0x' + keccak256(bytes.fromhex(''.join(data[2:7]))).hex()
    slot = p._call(state, 'getSlot0(bytes32)', pool, block=block, words=4)
    try:
        decode_slot0(slot, expected_fee=fee)
    except ValueError as exc:
        raise ProjectionError('Typed v4 pool has invalid or contradictory slot0') from exc
    req['v4_executor'] = helper
    return output
