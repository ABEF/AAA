"""Public API3 product offers and code verification sources; no purchase or subscription."""
from pathlib import Path
SOURCE=Path(__file__).resolve().with_name('fetch_discovery.py')
exec(compile(SOURCE.read_text().split('with concurrent.futures.ThreadPoolExecutor',1)[0],str(SOURCE),'exec'))
OUT=Path(__file__).resolve().parent/'api3-pricing';OUT.mkdir(exist_ok=True)
SOURCES={
 'api3-eth-offers':'https://api3dao.github.io/data-feeds/market/dapi-pricing/4663/ETH-USD.json',
 'api3-zzz-offers':'https://api3dao.github.io/data-feeds/market/dapi-pricing/4663/ZZZ-USD.json',
 'sourcify-chainlink':'https://repo.sourcify.dev/contracts/full_match/4663/0x6091E64eb7138EEF066a80FD3A0d7427B91f2721/metadata.json',
 'sourcify-pyth':'https://repo.sourcify.dev/contracts/full_match/4663/0x66e9cba5529824a03b5bc9931d9c63637101d0f7/metadata.json',
}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: result=dict(pool.map(run,SOURCES.items()))
(OUT/'fetches.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
