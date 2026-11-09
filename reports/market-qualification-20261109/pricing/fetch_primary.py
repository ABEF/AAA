"""Bounded public primary-source GETs only; no credentials or wallet access."""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

OUT = Path(__file__).resolve().parent
SOURCES = {
    'chainlink-catalog': 'https://reference-data-directory.vercel.app/feeds-robinhood-mainnet.json',
    'pyth-symbols': 'https://pyth.dourolabs.app/v1/symbols',
    'pyth-addresses': 'https://docs.pyth.network/pro/contract-addresses',
    'pyth-sponsored': 'https://docs.pyth.network/pro/sponsored-feeds',
    'chainlink-sequencer': 'https://docs.chain.link/data-feeds/l2-sequencer-feeds',
    'redstone-push': 'https://app.redstone.finance/push-feeds',
    'redstone-pull': 'https://app.redstone.finance/pull-feeds',
}
LIMIT = 8 * 1024 * 1024


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        fp.close()
        raise ValueError('unreviewed_redirect')


def fetch(item):
    name, url = item
    record = {'url': url, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        opener = urllib.request.build_opener(NoRedirects())
        req = urllib.request.Request(url, headers={'User-Agent': 'PoPL-read-only-market-research/1'})
        with opener.open(req, timeout=15) as response:
            raw = response.read(LIMIT+1)
            record.update(http_status=response.status,
                content_type=response.headers.get('Content-Type'), server_date=response.headers.get('Date'))
        if len(raw) > LIMIT:
            raise ValueError('response_limit')
        with (OUT/(name+'.raw')).open('xb') as stream:
            stream.write(raw)
        record.update(available=True, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if name in ('chainlink-catalog', 'pyth-symbols'):
            data = json.loads(raw)
            rows = data if isinstance(data, list) else data.get('symbols', data.get('feeds', []))
            eth = [r for r in rows if isinstance(r, dict) and
                   (r.get('name') == 'ETH / USD' or r.get('symbol') == 'Crypto.ETH/USD')]
            zzz = [r for r in rows if isinstance(r, dict) and
                   ('ZZZ' in str(r.get('name', '')).upper() or
                    'ZZZ' in str(r.get('symbol', '')).upper() or
                    '7dbf38976f6d3b9c529e7d9484a71898b409ee6a' in json.dumps(r).lower())]
            record.update(row_count=len(rows), eth_matches=len(eth), zzz_matches=len(zzz))
            with (OUT/(name+'-selected.json')).open('x', encoding='utf-8') as stream:
                json.dump({'ETH_USD': eth, 'ZZZ_matches': zzz}, stream, indent=2)
                stream.write('\n')
    except urllib.error.HTTPError as error:
        record.update(available=False, http_status=error.code)
        error.close()
    except Exception as error:
        record.update(available=False, error_type=type(error).__name__)
    record['completed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return name, record


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = dict(pool.map(fetch, SOURCES.items()))
    with (OUT/'primary-fetches-2.json').open('x', encoding='utf-8') as stream:
        json.dump({'sources': records, 'qualification': False}, stream, indent=2)
        stream.write('\n')
    print(json.dumps(records, indent=2))
