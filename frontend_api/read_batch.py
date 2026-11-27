"""Opt-in bounded read aggregation, never a deployment or signing path.

The pinned constructor executes only fixed STATICCALL getters. eth_call with no
destination returns finite ABI records as ephemeral runtime bytes; no persistent
code, transaction, state override or caller-supplied program is used. Normal
Projection getters still decode and authenticate every seeded response.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

from frontend_api.canonical_cache import batch_rpc, cached, prefetch
from zzz_ops.abi import address, calldata, keccak256
from zzz_ops.work_budget import checkpoint

ZERO = '0x'+'0'*40
MAX_IDS = 16
ACCOUNTS_PER_BATCH = 3
MAX_ROYALTY_ASSETS = 4
CALL_GAS = 24_000_000
PLAIN_GAS = 50_000
LP_GAS = 500_000
ROYALTY_GAS = 1_000_000
MAX_INITCODE_BYTES = 49_152
MAX_RETURN_BYTES = 24_576
MAGIC = keccak256(b'POPL_WALLET_STATIC_READ_BATCH_V1')
SOURCE_SHA256 = '7230cfb3f72c818a0cb8f2289c19b7924d6b05222df4d5cf09ee6946c6b56700'
CREATION_SHA256 = '6f8ba510e07f808f74358817a744b1d73bf9f0512e54a43cd92eef46e443c044'
ARTIFACT_SHA256 = 'e528d6ae3ef71c435ad3a451c0918ce66a0d90ba4fabd7e4a16dcc769814908b'
FILES = ('frontend_api/read_batch/WalletReadBatch.sol',
         'frontend_api/read_batch/WalletReadBatch.json')


def _fail(message):
    # Runtime import avoids changing Projection construction/import ordering.
    from frontend_api.service import ProjectionError
    raise ProjectionError(message)


@lru_cache(maxsize=1)
def _creation():
    """Authenticate finite checked-in data; it is not user configuration."""
    root = Path(__file__).resolve().parents[1]
    try:
        with (root/FILES[0]).open('rb') as handle:
            source = handle.read(32*1024+1)
        with (root/FILES[1]).open('rb') as handle:
            raw = handle.read(64*1024+1)
    except OSError:
        _fail('Read-only batch source or artifact is unavailable')
    if (len(source)>32*1024 or len(raw)>64*1024 or
            hashlib.sha256(source).hexdigest()!=SOURCE_SHA256 or
            hashlib.sha256(raw).hexdigest()!=ARTIFACT_SHA256):
        _fail('Read-only batch source or artifact differs')
    artifact = json.loads(raw)
    encoded = artifact['creation_bytecode']
    if type(encoded) is not str or re.fullmatch(r'0x(?:[0-9a-f]{2})+',encoded) is None:
        _fail('Read-only batch artifact is malformed')
    code = bytes.fromhex(encoded[2:])
    if (hashlib.sha256(code).hexdigest()!=CREATION_SHA256 or len(code)>MAX_INITCODE_BYTES or
            artifact['source_sha256']!=SOURCE_SHA256 or artifact['creation_sha256']!=CREATION_SHA256 or
            artifact['compiler']!='0.8.26+commit.8a97fa7a'):
        _fail('Read-only batch compiler binding differs')
    return code


def _word(value):
    return int(value).to_bytes(32,'big')


def _address(value, *, native=False):
    return ZERO if native and value==ZERO else address(value)


def _arguments(modules, ids, lp_assets, royalty_assets):
    """Canonical ABI(address[4],uint256[],address[2],address[])."""
    head = b''.join(_word(int(a,16)) for a in modules)
    ids_tail = _word(len(ids))+b''.join(_word(i) for i in ids)
    head += _word(256)
    head += b''.join(_word(int(a,16)) for a in lp_assets)
    head += _word(256+len(ids_tail))
    return head+ids_tail+_word(len(royalty_assets))+b''.join(_word(int(a,16)) for a in royalty_assets)


def _data(signature, identifier, asset=None):
    # The tiny static codec excludes native address0 generally; only this fixed
    # address argument is replaced with the actual zero ABI word.
    if asset is None:
        return calldata(signature,identifier)
    if asset==ZERO:
        return calldata(signature,identifier,'0x'+'0'*39+'1')[:-64]+'0'*64
    return calldata(signature,identifier,asset)


def _parse(raw, modules, ids, lp_assets, royalty_assets, arguments, chain):
    rows = len(ids)*(11+len(royalty_assets))
    length = 128+rows*96
    if (length>MAX_RETURN_BYTES or type(raw) is not str or len(raw)!=2+length*2 or
            re.fullmatch(r'0x[0-9a-fA-F]+',raw) is None):
        _fail('Read-only batch result length or encoding differs')
    result = bytes.fromhex(raw[2:])
    words = [int.from_bytes(result[i:i+32],'big') for i in range(0,len(result),32)]
    if (result[:32]!=MAGIC or words[1]!=chain or result[64:96]!=keccak256(arguments) or words[3]!=rows):
        _fail('Read-only batch result identity differs')
    cursor = 4
    entries = []

    def take(target, data, expected_words):
        nonlocal cursor
        checkpoint()
        status, first, second = words[cursor:cursor+3]
        cursor += 3
        if status==2:
            _fail('Read-only batch getter ABI differs')
        if status not in (0,1) or status==0 and (first or second) or expected_words==1 and second:
            _fail('Read-only batch getter status differs')
        value = None if status==0 else '0x'+''.join(f'{v:064x}' for v in (first,second)[:expected_words])
        if data is not None:
            entries.append((target,data,value))
        return status,first

    nft,vault,royalties,rewards = modules
    for identifier in ids:
        take(nft,_data('ownerOf(uint256)',identifier),1)
        status,ordinal = take(nft,_data('mintOrdinalOf(uint256)',identifier),1)
        if status==1:
            take(nft,_data('tokenAtOrdinal(uint256)',ordinal),1)
        else:
            skipped = words[cursor:cursor+3]
            cursor += 3
            if skipped != [0,0,0]:
                _fail('Read-only batch failed ordinal has an unexpected dependent reply')
        for target,signature in ((vault,'sharesOf(uint256)'),(vault,'nftBucket(uint256)'),
                                 (royalties,'weightOf(uint256)'),(rewards,'rewardBucket(uint256)')):
            take(target,_data(signature,identifier),1)
        for asset in lp_assets:
            take(rewards,_data('claimableComponents(uint256,address)',identifier,asset),2)
        for asset in lp_assets:
            take(rewards,_data('claimable(uint256,address)',identifier,asset),1)
        for asset in royalty_assets:
            take(royalties,_data('claimable(uint256,address)',identifier,asset),1)
    if cursor!=len(words):
        _fail('Read-only batch result has trailing rows')
    return entries


def _account_cached(p,block,modules,identifier,lp_assets,royalty_assets):
    """No side marker: completeness comes from bounded exact getter records."""
    nft,vault,royalties,rewards = modules
    queries = [(nft,_data('ownerOf(uint256)',identifier)),
               (nft,_data('mintOrdinalOf(uint256)',identifier))]
    found,ordinal = cached(p,block,*queries[-1])
    if not found:
        return False
    if ordinal is not None:
        if type(ordinal) is not str or re.fullmatch(r'0x[0-9a-fA-F]{64}',ordinal) is None:
            _fail('Read-only cached ordinal ABI differs')
        queries.append((nft,_data('tokenAtOrdinal(uint256)',int(ordinal,16))))
    queries += [(target,_data(signature,identifier)) for target,signature in
                ((vault,'sharesOf(uint256)'),(vault,'nftBucket(uint256)'),
                 (royalties,'weightOf(uint256)'),(rewards,'rewardBucket(uint256)'))]
    queries += [(rewards,_data(signature,identifier,asset)) for signature in
                ('claimableComponents(uint256,address)','claimable(uint256,address)') for asset in lp_assets]
    queries += [(royalties,_data('claimable(uint256,address)',identifier,asset)) for asset in royalty_assets]
    return all(cached(p,block,target,data)[0] for target,data in queries)


def prefetch_accounts(p, block, ids, lp_assets, royalty_assets):
    """Seed at most16 account proofs, using fixed groups of at most3 accounts.

    An inner failure remains a failed normal getter. No fallback reads, hidden
    retry, new request budget or unbounded retention occurs. Provider support
    for canonical creation eth_call and actual call gas needs qualification.
    """
    checkpoint()
    if (not isinstance(ids,(tuple,list)) or not 1<=len(ids)<=MAX_IDS or
            any(type(i) is not int or not 0<i<2**256 for i in ids) or
            any(a>=b for a,b in zip(ids,ids[1:]))):
        raise ValueError('Invalid read-only batch NFT selection')
    if (type(block) is not dict or set(block)!={'blockHash','requireCanonical'} or
            block['requireCanonical'] is not True or type(block['blockHash']) is not str or
            re.fullmatch(r'0x[0-9a-fA-F]{64}',block['blockHash']) is None):
        raise ValueError('Read-only batch requires a canonical block hash')
    if (not isinstance(lp_assets,(tuple,list)) or len(lp_assets)!=2 or lp_assets[0]!=ZERO or
            not isinstance(royalty_assets,(tuple,list)) or len(royalty_assets)>MAX_ROYALTY_ASSETS):
        raise ValueError('Invalid read-only batch currencies')
    pair = (ZERO,_address(lp_assets[1]))
    currencies = tuple(_address(a,native=True) for a in royalty_assets)
    if list(currencies)!=sorted(set(currencies)) or any(a not in p.assets for a in pair+currencies):
        raise ValueError('Read-only batch currencies differ from reviewed descriptors')
    modules = tuple(_address(p.contracts[role].address) for role in ('nft','vault','royalties','rewards'))
    if len(set(modules))!=4 or type(p.chain) is not int or p.chain<=0:
        raise ValueError('Invalid read-only batch module identity')
    captured = deepcopy(block)
    transport = batch_rpc(p)
    creation = _creation()
    batches = 0
    missing = tuple(i for i in ids if not _account_cached(p,captured,modules,i,pair,currencies))
    for start in range(0,len(missing),ACCOUNTS_PER_BATCH):
        group = missing[start:start+ACCOUNTS_PER_BATCH]
        arguments = _arguments(modules,group,pair,currencies)
        code = creation+arguments
        if len(code)>MAX_INITCODE_BYTES:
            _fail('Read-only batch initcode exceeds its bound')
        raw = transport.call('eth_call',[{'from':ZERO,'value':'0x0','gas':hex(CALL_GAS),'data':'0x'+code.hex()},deepcopy(captured)])
        checkpoint()
        entries = _parse(raw,modules,group,pair,currencies,arguments,p.chain)
        prefetch(p,captured,entries)
        batches += 1
    return batches
