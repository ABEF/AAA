"""Exercise only the fresh loopback browser lab, never a public RPC/signing key."""
import argparse
import json
import os
from pathlib import Path
import time
import secrets
import urllib.request
import urllib.error

def _write_evidence(handle,result):
    encoded=json.dumps(result,indent=2,allow_nan=False)+'\n'
    handle.seek(0);handle.write(encoded);handle.truncate()
    handle.flush();os.fsync(handle.fileno())


def run(port,output):
    # Own a new evidence file before any lab request, not after side effects.
    # A competing writer or a dangling symlink is refused by exclusive creation.
    result={'scope':'isolated Anvil local fixture, not Uniswap/Robinhood qualification',
            'status':'in_progress'}
    with Path(output).open('x',encoding='utf-8') as handle:
        _write_evidence(handle,result)
        try:
            result=_exercise(port)
            result['status']='passed'
            return result
        except Exception as error:
            result['status']='failed';result['error_type']=type(error).__name__
            raise
        finally:
            _write_evidence(handle,result)


def _exercise(port):
    base=f'http://127.0.0.1:{port}'
    def request(path,payload=None,token=None,origin=True):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Local-Token']=token
        if origin:headers['Origin']=base
        data=None if payload is None else json.dumps(payload).encode()
        with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers=headers),timeout=180) as response:return json.load(response)
    token=request('/session')['token'];state=request('/state');alice,bob=state['accounts'];checks=[]
    def check(value,message):
        if not value:raise AssertionError(message)
        checks.append(message);print('PASS '+message,flush=True)
    def operation(payload,revision=None,identifier=None):
        return dict(operation_id=identifier or secrets.token_hex(16),revision=state['revision'] if revision is None else revision,payload=payload)
    def post(action,account=alice,**fields):
        outcome=request('/action',operation(dict(action=action,account=account,**fields)),token)
        if outcome['status']!='confirmed':raise AssertionError(outcome)
        return request('/state')
    def byid(s,identifier):return next(n for n in s['nfts'] if n['token_id']==identifier)
    def total(n,scope):return sum(int(a['raw']) for a in n['claimable'][scope])
    def rejected(payload,**options):
        try:request('/action',payload,**options)
        except urllib.error.HTTPError as error:return error.code
        return 200
    check([n['position']['evolution'] for n in state['nfts']]==['dormant','enhanced','enhanced','singularity'],'four seeded confirmed NFT states')
    check(state['earnings']['all_time_usd_at_current_price_18']['lp_processed']==str(100*10**18),'100 funded LP fee units indexed')
    check(rejected({'action':'mint','account':alice})==403,'missing session rejected before local submission')
    check(rejected({'action':'mint','account':alice},token=token,origin=False)==403,'foreign/missing origin rejected')
    check(rejected({'action':'withdraw','account':alice},token=token)==400,'unsupported action rejected')
    state=post('mint');new=state['nfts'][-1];identifier=new['token_id']
    check(new['position']['status']=='dormant' and new['position']['current_lp_value']['raw']=='0','prepared mint creates no LP')
    state=post('activate',id=identifier,amount='100');n=byid(state,identifier);bucket=n['position']['bucket_id'];lp=n['position']['local_custody']['lp_token_id']
    check(n['position']['activated'] and int(n['position']['current_lp_value']['raw'])>=99*10**18,'100 contribution activates with 99% minimum retained')
    check(total(n,'lp')==0 and total(n,'royalties')==0,'activation gets no retroactive funded fees or royalties')
    before=int(n['position']['current_lp_value']['raw']);state=post('increase',id=identifier,amount='100');n=byid(state,identifier)
    check(n['position']['bucket_id']==bucket and n['position']['local_custody']['lp_token_id']==lp,'top-up retains shared bucket and physical LP')
    check(int(n['position']['current_lp_value']['raw'])>=before+99*10**18,'top-up increases confirmed NFT LP value')
    state=post('fund');n=byid(state,identifier);old_lp=n['position']['local_custody']['lp_token_id'];fees=(total(n,'lp'),total(n,'royalties'))
    check(all(fees),'both funded income streams become claimable')
    state=post('rebalance');n=byid(state,identifier)
    check(n['position']['local_custody']['lp_token_id']!=old_lp,'governed range change and eligible rebalance replace physical LP')
    check((total(n,'lp'),total(n,'royalties'))==fees,'rebalance preserves previously accrued LP and royalty claims')
    state=post('transfer',id=identifier);n=byid(state,identifier)
    check(n['owner']==bob and (total(n,'lp'),total(n,'royalties'))==fees,'transfer carries unclaimed LP and royalty rights to buyer')
    outcome=request('/action',operation({'action':'claim','account':alice,'id':identifier}),token)
    check(outcome['status']=='failed' and not outcome['transactions'],'former owner cannot claim')
    state=request('/state')
    state=post('claim',account=bob,id=identifier);n=byid(state,identifier)
    check(total(n,'lp')==0 and total(n,'royalties')==0,'prepared combined claim pays both current-owner balances')
    paid=n['previously_claimed']['assets'];lp_paid=sum(int(a['lp_raw']) for a in paid);royalty_paid=sum(int(a['royalties_raw']) for a in paid)
    check((lp_paid,royalty_paid)==fees,'indexed lifetime totals include both payouts')
    state=post('fund');state=post('claim',account=bob,id=identifier);n=byid(state,identifier)
    check(sum(int(a['lp_raw']) for a in n['previously_claimed']['assets'])>lp_paid and sum(int(a['royalties_raw']) for a in n['previously_claimed']['assets'])>royalty_paid,'second claim accumulates rather than overwrites lifetime totals')
    check(state['earnings']['all_time_usd_at_current_price_18']['lp_processed']==str(300*10**18),'claims and rebalance do not double-count gross fee history')
    check(state['earnings']['all_time_usd_at_current_price_18']['royalties_received'] is None,'unconfigured ETH USD price remains unavailable')
    # New adversarial integration scope: replay the same request after discarding
    # its response, and prove rejected inputs leave no approval/financial receipt.
    old_count=len(state['nfts']);intent=operation({'action':'mint','account':alice})
    first=request('/action',intent,token);replayed=request('/action',intent,token);state=request('/state')
    check(first['status']=='confirmed' and replayed['replayed'] and len(state['nfts'])==old_count+1,'replayed mint executes exactly once on Anvil')
    check(rejected(dict(intent,payload={'action':'fund','account':alice}),token=token)==409,'same operation ID cannot change its meaning')
    check(rejected(operation({'action':'fund','account':alice},revision=intent['revision']),token=token)==409,'stale tab action rejected before funding')
    dormant=state['nfts'][-1]['token_id'];active=state['nfts'][1]['token_id'];receipt_hashes=[r['hash'] for r in state['transactions']]
    for amount in ['-100','0','99','100.5','1e3','0x100','100000',' 100','00100']:
        check(rejected(operation({'action':'activate','account':alice,'id':dormant,'amount':amount}),token=token)==400,'invalid amount rejected without approval: '+amount)
    for payload,title in [
        ({'action':'activate','account':alice,'id':active,'amount':'100'},'repeat activation'),
        ({'action':'increase','account':alice,'id':dormant,'amount':'100'},'top-up of dormant NFT'),
        ({'action':'activate','account':alice,'id':dormant,'amount':'99999'},'insufficient contribution balance'),
        ({'action':'claim','account':alice,'id':dormant},'empty claim'),
        ({'action':'transfer','account':bob,'id':dormant},'wrong-owner transfer'),
        ({'action':'claim','account':alice,'id':str(2**255)},'nonexistent NFT'),
    ]:
        outcome=request('/action',operation(payload),token)
        check(outcome['status']=='failed' and not outcome['transactions'],title+' leaves no transaction')
        state=request('/state')
    check([r['hash'] for r in state['transactions']]==receipt_hashes,'all rejected integration inputs preserve receipt history')
    result={'scope':'isolated Anvil local fixture, not Uniswap/Robinhood qualification','checks':checks,'snapshot':state,'observed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8890);parser.add_argument('--output',required=True)
    args=parser.parse_args();run(args.port,args.output)
