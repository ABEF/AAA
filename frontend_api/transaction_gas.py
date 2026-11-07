"""Reviewed unsigned-preparation gas policy; no signing or automatic widening."""
from dataclasses import dataclass
import re

from frontend_api.service import ProjectionError, _hash, _quantity

DEFAULT_GAS_LIMIT = 12_000_000
# Service resource bound, not a statement about any chain/provider limit.
# Changing backend software remains possible after contract sealing.
MAX_REVIEWED_GAS_LIMIT = 64_000_000


def configured_limit(value):
    if (not isinstance(value, str) or re.fullmatch(r'[1-9][0-9]{0,7}', value) is None or
            not 21000 <= int(value) <= MAX_REVIEWED_GAS_LIMIT):
        raise ValueError('Reviewed gas limit must be a decimal string between21000 and64000000')
    return int(value)


@dataclass(frozen=True)
class GasReview:
    configured: int
    effective: int
    block_limit: int | None = None


def observe(projection, header, limit):
    """Bind the effective cap to the SAME confirmed hash as monetary reads."""
    raw = projection.rpc.call('eth_getBlockByHash', [header['hash'], False])
    try:
        if not isinstance(raw, dict):
            raise ValueError('Missing header')
        if (_hash(raw['hash']) != header['hash'] or _quantity(raw['number']) != header['number'] or
                _quantity(raw['timestamp']) != header['timestamp']):
            raise ValueError('Header identity differs')
        block_limit = _quantity(raw['gasLimit'])
        if not 21000 <= block_limit < 1 << 64:
            raise ValueError('Invalid block gas limit')
    except (KeyError, TypeError, ValueError, ProjectionError) as exc:
        raise ProjectionError('Confirmed block gas policy is unavailable or inconsistent') from exc
    return GasReview(limit, min(limit, block_limit), block_limit)
