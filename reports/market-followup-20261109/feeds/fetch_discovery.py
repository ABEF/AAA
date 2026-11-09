"""Fixed public source URLs only, credential-free read-only fetch evidence."""
import concurrent.futures, datetime, hashlib, json, urllib.error, urllib.request
from pathlib import Path
OUT=Path(__file__).resolve().parent/'discovery'; OUT.mkdir(exist_ok=True)
PIN='bd8b08d7aa2203c5f3f103d4600b3b9f39d30e1c'
BASE='https://raw.githubusercontent.com/api3dao/contracts/'+PIN+'/'
SOURCES={
 'api3-chain':BASE+'data/chains/robinhood.json',
 'api3-addresses':BASE+'deployments/addresses.json',
 'api3-proxy-source':BASE+'contracts/api3-server-v1/proxies/Api3ReaderProxyV1.sol',
 'api3-factory-source':BASE+'contracts/api3-server-v1/proxies/Api3ReaderProxyV1Factory.sol',
 'api3-market-source':BASE+'contracts/api3-server-v1/Api3MarketV2.sol',
 'api3-registry-artifact':BASE+'deployments/robinhood/AirseekerRegistry.json',
 'api3-server-artifact':BASE+'deployments/robinhood/Api3ServerV1.json',
 'api3-factory-artifact':BASE+'deployments/robinhood/Api3ReaderProxyV1Factory.json',
 'api3-market-artifact':BASE+'deployments/robinhood/Api3MarketV2.json',
 'api3-js':'https://market.api3.org/assets/api3-B0P4kasb.js',
 'api3-index-js':'https://market.api3.org/assets/index-Cd5M3xxk.js',
 'pyth-getters-source':'https://raw.githubusercontent.com/pyth-network/pyth-crosschain/main/target_chains/ethereum/contracts/contracts/pyth/PythGetters.sol',
 'explorer-chainlink':'https://robinhoodchain.blockscout.com/api/v2/smart-contracts/0x6091E64eb7138EEF066a80FD3A0d7427B91f2721',
 'explorer-pyth':'https://robinhoodchain.blockscout.com/api/v2/smart-contracts/0x66e9cba5529824a03b5bc9931d9c63637101d0f7',
}
class NoRedirects(urllib.request.HTTPRedirectHandler):
 def redirect_request(self, req, fp, code, msg, headers, newurl):
  fp.close(); raise ValueError('unreviewed_redirect')
def run(item):
 name,url=item; row={'url':url,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'PoPL-bounded-readonly-followup/1'})
  try: response=urllib.request.build_opener(NoRedirects()).open(req,timeout=15)
  except urllib.error.HTTPError as exc: response=exc
  with response:
   raw=response.read(16*1024*1024+1)
   row.update(http_status=response.code,content_type=response.headers.get('Content-Type'),server_date=response.headers.get('Date'))
  if len(raw)>16*1024*1024: raise ValueError('response_limit')
  with (OUT/(name+'.raw')).open('xb') as stream: stream.write(raw)
  row.update(available=row['http_status']==200,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 except Exception as exc: row.update(available=False,error_type=type(exc).__name__)
 return name,row
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: result=dict(pool.map(run,SOURCES.items()))
(OUT/'fetches.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
