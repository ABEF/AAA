"""Explicit local/legacy Position codecs; never guess a profile from row length."""
import re

LEGACY_STATUS = ('none', 'active', 'outbound', 'remote', 'inbound', 'dormant', 'parked')
LOCAL_STATUS = ('none', 'active', 'outbound', 'dormant', 'parked')
HOLDER_EXIT_STATUS = LOCAL_STATUS + ('exited',)
COMMON = ('pool_id', 'lp_token_id', 'idle0', 'idle1', 'deposit_usd', 'center_x96', 'last_rebalance', 'status_code')


def position_word_count(version):
    if type(version) is not int or version not in (1, 2, 3, 4):
        raise ValueError('Unsupported Position profile')
    return 8 if version in (3, 4) else 15


def status_name(version, code):
    position_word_count(version)
    statuses = HOLDER_EXIT_STATUS if version == 4 else LOCAL_STATUS if version == 3 else LEGACY_STATUS
    if type(code) is not int or not 0 <= code < len(statuses):
        raise ValueError('Unsupported Position status')
    return statuses[code]


def decode_position(words, version):
    if not isinstance(words, list) or len(words) != position_word_count(version) or any(
            not isinstance(w, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', w) for w in words):
        raise ValueError('Unexpected Position ABI')
    values = [int(w, 16) for w in words]
    if values[5] >= 1 << 160 or values[6] >= 1 << 64:
        raise ValueError('Noncanonical Position precision')
    result = dict(zip(COMMON, values[:8]))
    result['pool_id'] = '0x' + words[0].lower()
    result['status'] = status_name(version, values[7])
    if version not in (3, 4):
        result.update(home_chain=values[8], location_chain=values[13])
        for name, index in (('home_vault', 9), ('home_receiver', 10),
                            ('home_token0', 11), ('home_token1', 12), ('location_vault', 14)):
            if values[index] >= 1 << 160:
                raise ValueError('Noncanonical legacy Position address')
            result[name] = '0x' + words[index][-40:].lower()
    return result


def is_local_position(position, version, chain, vault):
    position_word_count(version)
    if version in (3, 4):
        # The authenticated V3 Vault has no satellite/remote position mode.
        # This does not replace caller runtime, chain or module binding checks.
        return True
    return (position['home_chain'] == chain == position['location_chain'] and
            position['home_vault'] == vault == position['location_vault'])
