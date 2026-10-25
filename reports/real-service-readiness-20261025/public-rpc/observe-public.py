"""Explicitly authorized bounded public read probe; no signer or state changes."""
import json,sys
from pathlib import Path
ROOT=Path(r'C:/Users/Ali/Desktop/2.x holas/Oto/zzz-protocol-v2-reviewed/zzz-protocol-v2')
sys.path.insert(0,str(ROOT))
from keeper.probe import probe
from zzz_ops.state import atomic_json
from zzz_ops.rpc import Rpc
OUT=Path(__file__).parent
config={'chain_id':4663,'rpc_urls':['https://rpc.mainnet.chain.robinhood.com','https://robinhood.rpc.pinax.network']}
report=probe(config,'0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a','0x18160ddd',receipt_blocks=2)
report['scope']='User-authorized point-in-time public reads, keeper_v1 only; no independently reviewed genesis/runtime or approval-trace qualification, no signing or sends'
atomic_json(OUT/'public-two-provider-observation.json',report)
print(json.dumps({'compatibility_checks_passed':report['compatibility_checks_passed'],'reference':report.get('reference_block'),
    'endpoints':[{'index':e['index'],'passed':sum(c['ok'] for c in e['checks']),'checks':len(e['checks']),
                 'failures':[c for c in e['checks'] if not c['ok']]} for e in report['endpoints']]}))
