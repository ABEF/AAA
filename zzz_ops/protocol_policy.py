"""Explicit Policy1 reads at a caller-pinned block; no RPC, signing or defaults.

Each scoped fingerprint is independently recomputed. A cosmetic or mint revision
does not invalidate an unrelated LP observation or contribution quote.
"""
import re
from zzz_ops.abi import address, keccak256

DOMAINS = {
    'entry': ('entryPolicy()', 'entryFingerprint()', ('minimum_activation_usd_18', 'minimum_growth_usd_18', 'maximum_idle_bps', 'revision'), (128,128,16,64)),
    'maintenance': ('maintenancePolicy()', 'maintenanceFingerprint()', ('maximum_idle_bps', 'revision'), (16,64)),
    'gas': ('gasPolicy()', 'gasFingerprint()', ('payout_gas', 'source_call_gas', 'royalty_sync_gas', 'revision'), (32,32,32,64)),
    'sale': ('salePolicy()', 'saleFingerprint()', ('mint_price_wei', 'recipient', 'pending_recipient', 'revision'), (128,160,160,64)),
    'metadata': ('metadataPolicy()', 'metadataFingerprint()', ('enhanced_usd_18', 'singularity_usd_18', 'revision'), (128,128,64)),
}
VRF_FIELDS=('coordinator','expected_code_hash','key_hash','subscription_id','request_confirmations',
            'callback_gas_limit','native_payment','generation','configured','review_hash')
VRF_WIDTHS=(160,256,256,256,16,32,1,64,1,256)


def observe(read, *, policy, access, domain, code=None, expected_code_hash=None):
    """read(target, signature, *args, count=N) must pin one canonical snapshot."""
    target, controller = address(policy), address(access)
    if domain not in DOMAINS: raise ValueError('Unsupported protocol-policy domain')
    def words(method, count=1):
        result=read(target,method,count=count)
        if not isinstance(result,list) or len(result)!=count or any(not isinstance(w,str) or not re.fullmatch('[0-9a-fA-F]{64}',w) for w in result):
            raise ValueError('Malformed protocol-policy response')
        return [w.lower() for w in result]
    if code is not None:
        raw=code(target)
        if (not isinstance(raw,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+',raw) or
                not isinstance(expected_code_hash,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',expected_code_hash) or
                '0x'+keccak256(bytes.fromhex(raw[2:])).hex()!=expected_code_hash.lower()):
            raise ValueError('Protocol-policy runtime differs')
    if int(words('PROTOCOL_POLICY_VERSION()')[0],16)!=1 or int(words('access()')[0],16)!=int(controller,16):
        raise ValueError('Protocol-policy identity differs')
    binding=read(controller,'protocolPolicy()',count=1)
    if binding!=[f'{int(target,16):064x}']:
        raise ValueError('Controller protocol-policy binding differs')
    getter,fingerprint,names,widths=DOMAINS[domain]
    raw=words(getter,len(names)); values=[int(w,16) for w in raw]
    if any(v>=2**width for v,width in zip(values,widths)) or values[-1]==0:
        raise ValueError('Protocol-policy field exceeds its ABI bound')
    result=dict(zip(names,values))
    if domain=='entry' and (values[0]<10**18 or not 10**18<=values[1]<=values[0] or values[2]>4000):
        raise ValueError('Contribution policy exceeds approved bounds')
    if domain=='maintenance' and values[0]>4000: raise ValueError('Maintenance policy exceeds approved bounds')
    if domain=='gas' and any(not 100000<=v<=1000000 for v in values[:-1]): raise ValueError('Gas policy exceeds approved bounds')
    if domain=='sale':
        if values[0]==0 or values[1]==0: raise ValueError('Mint policy has no price or recipient')
        result['recipient']='0x'+f'{values[1]:040x}'
        result['pending_recipient']='0x'+f'{values[2]:040x}'
    if domain=='metadata' and not 0<values[0]<values[1]: raise ValueError('Metadata thresholds are unordered')
    actual='0x'+words(fingerprint)[0]
    expected='0x'+keccak256(bytes.fromhex(f'{int(target,16):064x}'+''.join(raw))).hex()
    if actual!=expected: raise ValueError('Protocol-policy scoped fingerprint differs')
    return {'version':1,'domain':domain,'policy':target,'fingerprint':actual,**result}


def observe_mint(read, *, policy, access):
    """Authenticate sale AND current VRF generation, excluding cosmetics/gas."""
    target=address(policy);sale=observe(read,policy=target,access=access,domain='sale')
    def words(method,count):
        result=read(target,method,count=count)
        if not isinstance(result,list) or len(result)!=count or any(not isinstance(w,str) or not re.fullmatch('[0-9a-fA-F]{64}',w) for w in result):
            raise ValueError('Malformed mint-policy response')
        return [w.lower() for w in result]
    raw=words('vrfPolicy()',10);values=[int(w,16) for w in raw]
    revision=int(words('vrfRevision()',1)[0],16)
    if any(v>=2**width for v,width in zip(values,VRF_WIDTHS)) or not 0<revision<2**64:
        raise ValueError('Mint randomness policy exceeds ABI precision')
    if (not values[0] or not values[1] or not values[2] or not values[3] or
            not 3<=values[4]<=200 or not 200000<=values[5]<=10000000 or values[8]!=1 or not values[9]):
        raise ValueError('Mint randomness policy is not configured within approved bounds')
    sale_raw=[f'{int(sale[name],16) if isinstance(sale[name],str) else sale[name]:064x}' for name in DOMAINS['sale'][2]]
    fingerprint='0x'+words('mintFingerprint()',1)[0]
    expected='0x'+keccak256(bytes.fromhex(f'{int(target,16):064x}'+''.join(sale_raw)+f'{revision:064x}'+''.join(raw))).hex()
    if fingerprint!=expected:raise ValueError('Combined mint-policy fingerprint differs')
    result=dict(zip(VRF_FIELDS,values))
    result['coordinator']='0x'+f'{values[0]:040x}'
    for index,name in ((1,'expected_code_hash'),(2,'key_hash'),(9,'review_hash')):result[name]='0x'+raw[index]
    result['native_payment']=bool(values[6]);result['configured']=bool(values[8])
    return {'version':1,'policy':target,'fingerprint':fingerprint,'vrf_revision':revision,
            'sale_fingerprint':sale['fingerprint'],'randomness':result}
