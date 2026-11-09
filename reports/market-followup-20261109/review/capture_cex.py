"""Bounded unauthenticated primary-source GETs; no trading, keys or chain writes."""
import concurrent.futures, datetime, hashlib, json, pathlib, urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent / 'cex-attempt2'
ROOT.mkdir(exist_ok=False)
URLS = {
    'xt-listing': 'https://xtsupport.zendesk.com/hc/en-us/articles/62111344876825-XT-Announcement-on-the-Launching-ZZZ-ZZZ',
    'xt-old-symbol-distinction': 'https://xtsupport.zendesk.com/hc/en-us/articles/62113392379417-XT-Announcement-on-Renaming-of-ZZZ-to-ZZZOLD',
    'lbank-listing': 'https://www.lbank.com/support/articles/2096098424263802880',
    'lbank-asset': 'https://api.lbank.info/v2/assetConfigs.do?assetCode=zzz',
    'lbank-depth': 'https://api.lbank.info/v2/depth.do?symbol=zzz_usdt&size=60',
    'lbank-accuracy': 'https://api.lbank.info/v2/accuracy.do?symbol=zzz_usdt',
    'lbank-trades': 'https://api.lbank.info/v2/trades.do?symbol=zzz_usdt&size=10',
    'xt-symbol': 'https://sapi.xt.com/v4/public/symbol?symbol=zzz_usdt',
    'xt-depth': 'https://sapi.xt.com/v4/public/depth?symbol=zzz_usdt&limit=100',
    'xt-trades': 'https://sapi.xt.com/v4/public/trade/recent?symbol=zzz_usdt&limit=10',
    'xt-time': 'https://sapi.xt.com/v4/public/time',
}

class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ValueError('unreviewed_redirect')

def fetch(item):
    label, url = item
    row = {'label':label, 'url':url, 'method':'GET', 'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    req = urllib.request.Request(url, headers={'User-Agent':'PoPL-readonly-market-review/1','Accept':'application/json,text/html'})
    try:
        with urllib.request.build_opener(NoRedirects()).open(req, timeout=15) as response:
            raw = response.read(2*1024*1024+1)
            row.update(status=response.status, content_type=response.headers.get('Content-Type'), http_date=response.headers.get('Date'))
        if len(raw)>2*1024*1024: raise ValueError('response_limit')
    except urllib.error.HTTPError as error:
        raw=error.read(8192);row.update(status=error.code,error_type='HTTPError');error.close()
    except Exception as error:
        raw=b'';row.update(error_type=type(error).__name__,error=str(error)[:500])
    with (ROOT/(label+'.raw')).open('xb') as out: out.write(raw)
    row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    if raw and row.get('status')==200:
        try:
            parsed=json.loads(raw)
            with (ROOT/(label+'.json')).open('x',encoding='utf-8') as out:json.dump(parsed,out,indent=2);out.write('\n')
            row['decoded_json']=True
        except ValueError:row['decoded_json']=False
    return row

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor: rows=list(executor.map(fetch, URLS.items()))
with (ROOT/'cex-capture-manifest.json').open('x',encoding='utf-8') as out:json.dump(rows,out,indent=2);out.write('\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ('url',)} for r in rows],indent=2))
