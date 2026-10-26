# SPDX-License-Identifier: MIT
"""Exact v4 TickMath endpoints and internally consistent initialized slot0.

The endpoint calculation ports getSqrtPriceAtTick from @uniswap/v4-core 1.0.2,
src/libraries/TickMath.sol (MIT). No floating-point price approximation is used.
Actual slot0.tick is preserved, including v4's exact downward-boundary state.

Copyright 2023 Universal Navigation Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import re

MIN_TICK = -887272
MAX_TICK = 887272
MIN_SQRT = 4295128739
MAX_SQRT = 1461446703485210103287273052203988822378723970342

# Q128.128 inverse sqrt constants, in increasing bit order; each multiplication
# truncates exactly as the installed Solidity library before reciprocal/round-up.
_FACTORS = (
    0xfffcb933bd6fad37aa2d162d1a594001,
    0xfff97272373d413259a46990580e213a,
    0xfff2e50f5f656932ef12357cf3c7fdcc,
    0xffe5caca7e10e4e61c3624eaa0941cd0,
    0xffcb9843d60f6159c9db58835c926644,
    0xff973b41fa98c081472e6896dfb254c0,
    0xff2ea16466c96a3843ec78b326b52861,
    0xfe5dee046a99a2a811c461f1969c3053,
    0xfcbe86c7900a88aedcffc83b479aa3a4,
    0xf987a7253ac413176f2b074cf7815e54,
    0xf3392b0822b70005940c7a398e4b70f3,
    0xe7159475a2c29b7443b29c7fa6e889d9,
    0xd097f3bdfd2022b8845ad8f792aa5825,
    0xa9f746462d870fdf8a65dc1f90e061e5,
    0x70d869a156d2a1b890bb3df62baf32f7,
    0x31be135f97d08fd981231505542fcfa6,
    0x9aa508b5b7a84e1c677de54f3e99bc9,
    0x5d6af8dedb81196699c329225ee604,
    0x2216e584f5fa1ea926041bedfe98,
    0x48a170391f7dc42444e8fa2,
)


def sqrt_price_at_tick(tick):
    """Return v4's rounded-up Q64.96 sqrt endpoint for an exact integer tick."""
    if type(tick) is not int or not MIN_TICK <= tick <= MAX_TICK:
        raise ValueError('Invalid TickMath tick')
    absolute = abs(tick)
    ratio = 1 << 128
    for bit, factor in enumerate(_FACTORS):
        if absolute & (1 << bit):
            ratio = (ratio * factor) >> 128
    if tick > 0:
        ratio = ((1 << 256) - 1) // ratio
    return (ratio + (1 << 32) - 1) >> 32


def validate_slot0(price, tick, protocol_fee, lp_fee, *, expected_fee=None):
    """Validate actual v4 stored fields, not a PoolKey's dynamic-fee flag.

    At an exact downward crossing, Pool.swap stores tickNext-1 while retaining
    sqrtAtTick(tickNext). Hence the upper endpoint is inclusive here; callers
    must use the original stored tick for active-range membership.
    """
    if any(type(value) is not int for value in (price, tick, protocol_fee, lp_fee)):
        raise ValueError('Noncanonical slot0 integer')
    if not MIN_SQRT <= price < MAX_SQRT or not MIN_TICK <= tick < MAX_TICK:
        raise ValueError('Uninitialized or out-of-domain slot0')
    if not sqrt_price_at_tick(tick) <= price <= sqrt_price_at_tick(tick + 1):
        raise ValueError('Inconsistent slot0 sqrt price and tick')
    if not 0 <= protocol_fee < 1 << 24 or (protocol_fee & 0xfff) > 1000 or protocol_fee >> 12 > 1000:
        raise ValueError('Invalid directional slot0 protocol fee')
    if not 0 <= lp_fee <= 1_000_000:
        raise ValueError('Invalid stored slot0 LP fee')
    if expected_fee is not None and (type(expected_fee) is not int or lp_fee != expected_fee):
        raise ValueError('Stored slot0 LP fee differs from the reviewed static fee')
    return price, tick, protocol_fee, lp_fee


def decode_slot0(words, *, expected_fee=None):
    """Decode canonical uint160/int24/uint24/uint24 static ABI words."""
    if (not isinstance(words, (tuple, list)) or len(words) != 4 or
            any(not isinstance(word, str) or re.fullmatch(r'[0-9a-fA-F]{64}', word) is None
                for word in words)):
        raise ValueError('Malformed slot0 ABI')
    price, tick, protocol, fee = (int(word, 16) for word in words)
    if tick >= 1 << 255:
        tick -= 1 << 256
    # TickMath's narrower interval also rejects non-sign-extended int24 words.
    return validate_slot0(price, tick, protocol, fee, expected_fee=expected_fee)
