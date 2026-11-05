"""Fresh review identity only; no RPC, signing or historical-policy reinterpretation."""
import re

from zzz_ops.abi import keccak256, word

DOMAIN='0x'+keccak256(b'ZZZ_MINT_POLICY_WITH_ROYALTY_END_V2').hex()


def fingerprint(core_policy,nft,royalties,mint_end,mint_end_revision):
    """Hash six static ABI words exactly as the fresh Vault companion does."""
    if not isinstance(core_policy,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',core_policy):
        raise ValueError('Invalid core mint policy')
    for value in (mint_end,mint_end_revision):
        if type(value) is not int or not 0 <= value < 2**64:
            raise ValueError('Invalid mint-end review value')
    encoded=''.join([word(DOMAIN,'bytes32'),word(core_policy,'bytes32'),
                     word(nft,'address'),word(royalties,'address'),
                     word(mint_end,'uint64'),word(mint_end_revision,'uint64')])
    return '0x'+keccak256(bytes.fromhex(encoded)).hex()
