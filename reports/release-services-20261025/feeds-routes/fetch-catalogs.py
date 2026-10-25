"""Dated public reference-data downloads; bounded reads, no wallet capability."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
SOURCES = {
    'chainlink': 'https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json',
    'pyth': 'https://pyth.dourolabs.app/v1/symbols',
    'uniswap': 'https://developers.uniswap.org/deployments.json',
}
LIMIT = 8 * 1024 * 1024
class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ValueError('redirect_unreviewed')

opener=urllib.request.build_opener(NoRedirects())
report={'observed_at_utc':datetime.now(timezone.utc).isoformat(), 'release_approved':False,'sources':{}}
for name,url in SOURCES.items():
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'PoPL-readonly-reference/1'})
        with opener.open(req,timeout=15) as stream:
            raw=stream.read(LIMIT+1)
        if len(raw)>LIMIT: raise ValueError('response_limit')
        data=json.loads(raw)
        (OUT/f'{name}-catalog.json').write_bytes(raw)
        report['sources'][name]={'url':url,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'available':True}
        if name=='chainlink':
            rows=data if isinstance(data,list) else data.get('feeds',[])
            selected=[r for r in rows if isinstance(r,dict) and (str(r.get('name','')).upper() in ('ETH / USD','USDG / USD','USDC / USD') or 'ZZZ' in str(r.get('name','')).upper())]
            (OUT/'chainlink-selected.json').write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8')
        if name=='pyth':
            rows=data if isinstance(data,list) else data.get('symbols',[])
            selected=[r for r in rows if isinstance(r,dict) and (str(r.get('symbol','')) in ('Crypto.ETH/USD','Crypto.USDG/USD','Crypto.USDC/USD') or 'ZZZ' in str(r.get('symbol','')).upper())]
            (OUT/'pyth-selected.json').write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8')
        if name=='uniswap':
            selected=[r for r in data['records'] if r.get('chainId')==4663]
            (OUT/'uniswap-selected.json').write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8')
        report['sources'][name]['selected_count']=len(selected)
    except urllib.error.HTTPError as exc:
        report['sources'][name]={'url':url,'available':False,'http_status':exc.code}; exc.close()
    except Exception as exc:
        report['sources'][name]={'url':url,'available':False,'error_type':type(exc).__name__}
(OUT/'catalog-receipt.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
