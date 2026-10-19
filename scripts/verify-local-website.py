"""Exercise the website's typed confirmation API on a fresh disposable lab."""
import argparse
import json
from pathlib import Path
import secrets
import urllib.request
import urllib.error

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    if not 1024<=args.port<=65535:raise ValueError('Invalid local port')
    base=f'http://127.0.0.1:{args.port}'
    result={'scope':'owned local Anvil website API; no public assets','assertions':[],'operations':[]}
    token=None
    def request(path,body=None):
        headers={'Content-Type':'application/json','Origin':base}
        if token:headers['X-Local-Token']=token
        req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body else None,headers=headers)
        with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
    def check(condition,label):
        if not condition:raise AssertionError(label)
        result['assertions'].append(label)
    def prepare(action,account,**extra):return request('/prepare',{'action':action,'account':account,**extra})
    def execute(draft):
        envelope={'operation_id':secrets.token_hex(16),'revision':draft['revision'],
                  'payload':{'action':'execute','account':draft['account'],'draft_id':draft['draft_id']}}
        outcome=request('/action',envelope)
        result['operations'].append({'draft':draft,'outcome':outcome})
        check(outcome['status']=='confirmed' and not outcome['uncertain'],draft['action']+' confirmed with receipts')
        check(request('/action',envelope).get('replayed') is True,'identical '+draft['action']+' operation recovered without execution')
        return outcome
    try:
        token=request('/session')['token']
        s=request('/state');a,b=s['accounts'];check(len(s['nfts'])==4,'fresh fixture has four NFTs')
        dormant=next(n for n in s['nfts'] if not n['position']['activated']);identifier=dormant['token_id']
        p=prepare('activate',a,id=identifier,amount='100');check(p['action']=='approve','activation first prepares only exact approval')
        check(p['minimum_lp_usd_18']==str(99*10**18),'99% contribution floor disclosed independently from gas')
        check(int(p['network_gas']['max_cost_wei'])>0,'network gas quote separate and nonzero')
        execute(p)
        s=request('/state');check(not next(n for n in s['nfts'] if n['token_id']==identifier)['position']['activated'],'approval does not activate NFT')
        p=prepare('activate',a,id=identifier,amount='100');check(p['action']=='activate','second confirmation executes Entry')
        execute(p)
        s=request('/state');n=next(n for n in s['nfts'] if n['token_id']==identifier)
        check(n['position']['activated'] and int(n['position']['current_lp_value']['raw'])>=99*10**18,'activation adds actual LP')
        check(all(int(row['raw'])==0 for scope in ('lp','royalties') for row in n['claimable'][scope]),'activation grants no historical fees')
        old_lp=int(n['position']['current_lp_value']['raw'])
        p=prepare('increase',a,id=identifier,amount='100');check(p['action']=='approve','top-up requires a new exact allowance after consumption');execute(p)
        execute(prepare('increase',a,id=identifier,amount='100'))
        s=request('/state');n=next(n for n in s['nfts'] if n['token_id']==identifier)
        check(int(n['position']['current_lp_value']['raw'])>=old_lp+99*10**18,'top-up increases same NFT on-chain value')
        check(n['traits']==dormant['traits'],'activation and top-up preserve revealed traits')
        claim_target=next(n for n in s['nfts'] if any(int(r['raw']) for r in n['claimable']['royalties']))
        stale=prepare('claim',a,id=claim_target['token_id'])
        execute(prepare('transfer',a,id=claim_target['token_id']))
        envelope={'operation_id':secrets.token_hex(16),'revision':s['revision'],
                  'payload':{'action':'execute','account':a,'draft_id':stale['draft_id']}}
        try:request('/action',envelope)
        except urllib.error.HTTPError as error:check(error.code==409,'old owner confirmation invalidated by revision change')
        else:raise AssertionError('stale owner confirmation accepted')
        p=prepare('claim',b,id=claim_target['token_id'])
        check(any(r['royalty'] for r in p['claims']) and any(not r['royalty'] for r in p['claims']),'buyer inherits both claim streams')
        execute(p)
        execute(prepare('claim_all',a))
        before=len(s['nfts']);execute(prepare('mint',b))
        s=request('/state');check(len(s['nfts'])==before+1,'mint creates one actual NFT')
        check(all(int(r['raw'])==0 for n in s['nfts'] for scope in ('lp','royalties') for r in n['claimable'][scope]),'bounded claim-all and buyer claim consume funded balances')
        claimed=next(n for n in s['nfts'] if n['token_id']==claim_target['token_id'])
        check(claimed['owner']==b and any(int(r['royalties_raw']) for r in claimed['previously_claimed']['assets']),'lifetime royalty claims and ownership retained')
        check(s['earnings']['all_time_usd_at_current_price_18']['royalties_received'] is None,'missing ETH price remains unavailable')
        result['final_snapshot']=s
        result['status']='passed'
    except Exception as error:
        result['status']='failed';result['error']=str(error)
        raise
    finally:
        Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print(result['status'],len(result['assertions']),'assertions')

if __name__=='__main__':main()
