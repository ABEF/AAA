"""Bounded credential-free public GETs. No provider contact or on-chain mutation."""
import concurrent.futures, datetime, hashlib, json, sys, urllib.error, urllib.request
from pathlib import Path
OUT=Path(__file__).resolve().parent/(sys.argv[1] if len(sys.argv)>1 else 'initial')
OUT.mkdir(exist_ok=True)
SOURCES={
 'pyth-fees':'https://docs.pyth.network/pro/on-chain-fees',
 'pyth-architecture':'https://docs.pyth.network/pro/how-lazer-works',
 'pyth-upgrade':'https://docs.pyth.network/pro/pyth-core-upgrade',
 'pyth-addresses':'https://docs.pyth.network/pro/contract-addresses',
 'pyth-sponsored':'https://docs.pyth.network/pro/sponsored-feeds',
 'chainlink-sequencer':'https://docs.chain.link/data-feeds/l2-sequencer-feeds',
 'chainlink-catalog':'https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json',
 'pyth-symbols':'https://pyth.dourolabs.app/v1/symbols',
 'pyth-hermes-latest-noauth':'https://pyth.dourolabs.app/hermes/v2/updates/price/latest?ids%5B%5D=ff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace&parsed=true',
 'robinhood-oracles':'https://docs.robinhood.com/chain/oracles-and-price-feeds/',
 'api3-market':'https://market.api3.org/robinhood',
 'api3-eth':'https://market.api3.org/robinhood/eth-usd',
 'api3-round-doc':'https://docs.api3.org/dapps/integration/aggregatorv2v3interface.html',
 'api3-integration':'https://docs.api3.org/dapps/integration/contract-integration.html',
 'api3-repo-tree':'https://api.github.com/repos/api3dao/contracts/git/trees/main?recursive=1',
}
class NoRedirects(urllib.request.HTTPRedirectHandler):
 def redirect_request(self, req, fp, code, msg, headers, newurl):
  fp.close(); raise ValueError('unreviewed_redirect')
def run(item):
 name,url=item; row={'url':url,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'PoPL-bounded-readonly-followup/1'})
  try:
   response=urllib.request.build_opener(NoRedirects()).open(req,timeout=12)
  except urllib.error.HTTPError as exc:
   response=exc
  with response:
   raw=response.read(8*1024*1024+1)
   row.update(http_status=response.code,content_type=response.headers.get('Content-Type'),server_date=response.headers.get('Date'))
  if len(raw)>8*1024*1024: raise ValueError('response_limit')
  (OUT/(name+'.raw')).write_bytes(raw)
  row.update(available=row['http_status']==200,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 except Exception as exc: row.update(available=False,error_type=type(exc).__name__)
 return name,row
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: result=dict(pool.map(run,SOURCES.items()))
(OUT/'public-fetches.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
