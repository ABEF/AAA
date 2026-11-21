"""Independent eager rational-phase replay of the saved Entry baseline only.

No RPC, EVM, tests, production pending/carry getters or source mutation.
Uses the declared 1024-leaf rounding rule, not the engine's lazy carry folds.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import hashlib
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from zzz_ops.abi import keccak256

ARCHIVE_SHA='e56b8d78aba465c673aa0379e6a4214860189e935c133dafc7da8c46aa99d2ff'
ZZZ='0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
ZERO='0x'+'0'*40
Q=1<<128

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    assert not a.output.exists()
    folder=ROOT/'reports/pool-integration-20261120/entry'
    manifest=json.loads((folder/'EVIDENCE_MANIFEST.json').read_bytes())
    raw=(folder/'evidence.zip').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==manifest['sha256']==ARCHIVE_SHA
    inputs={}
    with zipfile.ZipFile(folder/'evidence.zip')as archive:
        def load(name):
            raw=archive.read(name);row=manifest['members'][name]
            assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
            inputs[name]=row
            return json.loads(raw)
        instances=load('attempt1/construction/instances.json')
        rows=load('attempt1/ALL_SETUP_SCENARIO_RECEIPTS.json')
        states=load('attempt1/STATES.json')
    roles={row['role']:row['address'].lower()for row in instances}
    weights=[defaultdict(int),defaultdict(int)]
    phase=defaultdict(lambda:[0,0]);earned=defaultdict(int)
    ids={int(nft):i+1 for i,nft in enumerate(states[0]['ids'])}
    credited=defaultdict(int);events=0;checkpoints=[]
    def topic(sig):return '0x'+keccak256(sig.encode()).hex()
    credit=topic('PoolRewardsCredited(uint256,address,uint256,uint256)')
    share=topic('ShareWeightSynchronized(uint256,uint256,uint256,uint256,uint256,uint256)')
    member=topic('CollectiveWeightSynchronized(uint256,uint256,uint256,uint256,uint256)')
    def words(raw):return[int(raw[i:i+64],16)for i in range(2,len(raw),64)]
    def set_weight(kind,ordinal,weight):
        leaf=1024+ordinal-1
        if weights[kind][leaf]==weight:return
        weights[kind][leaf]=weight
        node=leaf//2
        while node:
            old=weights[kind][node]
            new=weights[kind][node*2]+weights[kind][node*2+1]
            weights[kind][node]=new
            for asset in range(2):
                key=(kind,asset,node);high,low=phase[key]
                phase[key]=[high,low*new//old if old and new else 0]
            node//=2
    def distribute(kind,asset,amount,node=1):
        if not amount:return
        if node>=1024:
            earned[kind,asset,node-1023]+=amount
            return
        total=weights[kind][node]
        assert total>0
        whole,remainder=divmod(amount*weights[kind][node*2],total)
        high,low=phase[kind,asset,node]
        extra,rest=divmod(remainder*Q+high*total+low,total*Q)
        left=whole+extra
        assert 0<=left<=amount
        phase[kind,asset,node]=list(divmod(rest,total))
        distribute(kind,asset,left,node*2)
        distribute(kind,asset,amount-left,node*2+1)
    for row in rows:
        for log in row['receipt']['logs']:
            if log['address'].lower()!=roles['rewards']or not log['topics']:continue
            signature=log['topics'][0];values=words(log['data'])
            if signature==credit:
                asset_address='0x'+log['topics'][2][-40:]
                assert asset_address in(ZERO,ZZZ)
                asset=int(asset_address==ZZZ)
                distribute(0,asset,values[0]);distribute(1,asset,values[1])
                credited[0,asset]+=values[0];credited[1,asset]+=values[1];events+=1
            elif signature==share:
                ordinal,previous,new,total=values
                assert ids[int(log['topics'][1],16)]==ordinal
                assert weights[0][1023+ordinal]==previous
                set_weight(0,ordinal,new)
                assert weights[0][1]==total
            elif signature==member:
                ordinal,previous,new,total=values
                assert ids[int(log['topics'][1],16)]==ordinal
                assert weights[1][1023+ordinal]==previous
                set_weight(1,ordinal,new)
                assert weights[1][1]==total
        if row['label'].startswith('new_'):
            after,=[s for s in states if s['label']==row['label']+':after']
            expected=[[earned[0,asset,ordinal]+earned[1,asset,ordinal]for ordinal in(1,2)]for asset in(0,1)]
            assert expected[0]==after['lp_claim_ETH']
            assert expected[1]==after['lp_claim_ZZZ']
            assert [weights[0][1024],weights[0][1025]]==after['shares']
            assert weights[1][1]==after['eligible_total']
            checkpoints.append({'label':row['label'],'claimable_ETH':list(map(str,expected[0])),'claimable_ZZZ':list(map(str,expected[1])),'shares':list(map(str,after['shares'])),'eligible':after['eligible_total']})
    for kind in range(2):
        for asset in range(2):
            assert credited[kind,asset]==sum(earned[kind,asset,i]for i in(1,2))
    result={'schema':1,'passed':True,'kind':'new_independent_offline_baseline_eager_replay','prior_archive_sha256':ARCHIVE_SHA,'archive_members':inputs,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'pool_credit_events_replayed':events,'checkpoints':checkpoints,'final_components':{'personal_ETH':[str(earned[0,0,i])for i in(1,2)],'collective_ETH':[str(earned[1,0,i])for i in(1,2)],'personal_ZZZ':[str(earned[0,1,i])for i in(1,2)],'collective_ZZZ':[str(earned[1,1,i])for i in(1,2)]},'independently_derived_nonzero_phase':{','.join(map(str,key)):list(map(str,val))for key,val in sorted(phase.items())if any(val)},'no_production_phase_pending_or_accrued_getter_used':True,'existing_Entry_execution_repeated':False,'unchanged_tests_run':False,'network_or_EVM_calls':0,'production_approved':False}
    with a.output.open('x',encoding='utf8',newline='\n')as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps({'passed':True,'credit_events':events,'checkpoints':len(checkpoints),'source_sha256':result['source_sha256'],'output':str(a.output)}))

if __name__=='__main__':main()
