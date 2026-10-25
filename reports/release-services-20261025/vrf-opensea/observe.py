"""User-authorized read-only dated integration candidate observation.

No proof/service/product approval is inferred from deployed bytecode.
"""
import datetime, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256
from zzz_ops.rpc import Rpc
from zzz_ops.work_budget import request_scope, Budget, BudgetedRPC
from zzz_ops.state import atomic_json

OUT = Path(__file__).parent
ADDRESSES = {
    'rh_vrf_coordinator': '0x1637195a674630e475acd18b3d27b13c0eefdac1',
    'rh_vrf_subscription': '0x3fbfe73935b729c6a30ae6060d5708215b3633f5',
    'rh_vrf_verifier': '0x035299fe87211f35f5f36fbba67919f9545ddd16',
    'seadrop_candidate_not_network_approved': '0x00005ea00ac477b1030ce78506496e8c2de24bf5',
}
IMPLEMENTATION = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc'
# Derive standardized slots locally rather than rely on an abbreviated constant.
ADMIN = hex(int.from_bytes(keccak256(b'eip1967.proxy.admin'), 'big') - 1)
rpc = BudgetedRPC(Rpc(['https://robinhood.rpc.pinax.network'],4663,timeout=6,retries=1))
report = {'schema':1,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'chain_id':4663,'endpoint':'documented_public_pinax','checks':[],
          'qualification':False,'public_transactions':False,'scope':'One public provider only; no independent runtime/source/proof review or product acceptance.'}

def read(name, method, params):
    try:
        value = rpc.call(method, params)
        report['checks'].append({'name':name,'ok':True})
        return value
    except Exception as exc:
        chain = []
        current = exc
        for _ in range(4):
            if current is None: break
            item = {'type':type(current).__name__}
            code = getattr(current,'code',None)
            if type(code) is int: item['code'] = code
            reason = getattr(current,'reason',None)
            if reason in ('unavailable_block','rate_limited','invalid_params','unclassified'): item['reason'] = reason
            chain.append(item)
            current = current.__cause__
        report['checks'].append({'name':name,'ok':False,'error_chain':chain})
        return None

with request_scope(Budget(seconds=60,calls=20,posts=40)):
    genesis = read('genesis','eth_getBlockByNumber',['0x0',False])
    head = read('head','eth_getBlockByNumber',['latest',False])
    if isinstance(genesis,dict) and isinstance(head,dict):
        number = max(0,int(head['number'],16)-12)
        block = read('confirmed_header','eth_getBlockByNumber',[hex(number),False])
        if isinstance(block,dict):
            ref = {'blockHash':block['hash'],'requireCanonical':True}
            report['genesis_hash'] = genesis['hash']
            report['reference'] = {k:block[k] for k in ('number','hash','timestamp')}
            report['addresses'] = {}
            for role,address in ADDRESSES.items():
                code = read(role+'.runtime','eth_getCode',[address,ref])
                item = report['addresses'][role] = {'address':address}
                if isinstance(code,str) and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',code):
                    raw = bytes.fromhex(code[2:]); item.update(runtime_bytes=len(raw),runtime_keccak256='0x'+keccak256(raw).hex(),runtime_sha256=hashlib.sha256(raw).hexdigest())
                    if raw: (OUT/(role+'.runtime.txt')).write_text(code+'\n',encoding='utf8')
                for slot_name,slot in (('implementation',IMPLEMENTATION),('admin',ADMIN)):
                    item[slot_name+'_slot'] = read(role+'.'+slot_name,'eth_getStorageAt',[address,slot,ref])
            final = read('reference_recheck','eth_getBlockByNumber',[hex(number),False])
            report['reference_rechecked'] = isinstance(final,dict) and final.get('hash') == block['hash']
atomic_json(OUT/'observation.json',report)
print(json.dumps({'passed':sum(c['ok'] for c in report['checks']),'checks':len(report['checks']),
                  'reference':report.get('reference'),'code_bytes':{k:v.get('runtime_bytes') for k,v in report.get('addresses',{}).items()},
                  'reference_rechecked':report.get('reference_rechecked',False),'qualification':False}))
