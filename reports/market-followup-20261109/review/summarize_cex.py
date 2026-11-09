"""Exact decimal summary of captured public books; prices remain USDT denominated."""
import datetime, decimal, json, pathlib
from decimal import Decimal as D
decimal.getcontext().prec=60
ROOT=pathlib.Path(__file__).resolve().parent
RAW=ROOT/'cex-attempt2'
def read(name):return json.loads((RAW/(name+'.json')).read_text(encoding='utf-8'),parse_float=D)
def text(value):return format(value,'f')
def fill_base(levels,amount):
    remaining=amount;quote=D(0)
    for p,q in levels:
        taken=min(remaining,q);quote+=taken*p;remaining-=taken
        if remaining==0:break
    return {'base':text(amount-remaining),'quote_USDT_gross':text(quote),'complete':remaining==0,
            'weighted_price_USDT':text(quote/(amount-remaining)) if amount!=remaining else None}
def buy_quote(levels,amount):
    remaining=amount;base=D(0)
    for p,q in levels:
        spent=min(remaining,p*q);base+=spent/p;remaining-=spent
        if remaining==0:break
    return {'base':text(base),'quote_USDT_gross':text(amount-remaining),'complete':remaining==0,
            'weighted_price_USDT':text((amount-remaining)/base) if base else None}
result={'qualification':False,'source_token':'0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a',
        'warning':'Exchange supplied USDT books and status only. Not USD sources, onchain adapters, honest/executable depth or independent operator qualification. No orders/deposits/withdrawals made.',
        'captures':'cex-attempt2/cex-capture-manifest.json','books':{}}
for label,body in [('lbank',read('lbank-depth')['data']),('xt',read('xt-depth')['result'])]:
    bids=[(D(p),D(q)) for p,q in body['bids']];asks=[(D(p),D(q)) for p,q in body['asks']]
    assert all(p>0 and q>0 for p,q in bids+asks)
    assert bids==sorted(bids,reverse=True) and asks==sorted(asks)
    bid,ask=bids[0][0],asks[0][0];assert bid<ask
    mid=(bid+ask)/2
    row={'timestamp_ms':body['timestamp'],'timestamp_utc':datetime.datetime.fromtimestamp(body['timestamp']/1000,datetime.timezone.utc).isoformat(),
         'bid_USDT':text(bid),'ask_USDT':text(ask),'mid_USDT':text(mid),
         'spread_bps_lower_denominator':text((ask-bid)/bid*10000),
         'levels_bid':len(bids),'levels_ask':len(asks),
         'displayed_notional_USDT_within_3pct_of_mid':{
             'bids':text(sum(p*q for p,q in bids if p>=mid*D('.97'))),
             'asks':text(sum(p*q for p,q in asks if p<=mid*D('1.03')))},
         'book_only_sell_10000_ZZZ':fill_base(bids,D(10000)),
         'book_only_buy_for_50_USDT':buy_quote(asks,D(50)),
         'fees_included':False,'fills_executed':False}
    result['books'][label]=row
asset=read('lbank-asset')['data'];assert len(asset)==1 and asset[0]['contractInfo'].lower()==result['source_token']
result['lbank_identity_status']=asset[0]
symbol=read('xt-symbol')['result']['symbols'];assert len(symbol)==1
symbol=symbol[0]
assert symbol['chainRelation'][0]['contract'].lower()==result['source_token']
result['xt_identity_status']={k:symbol[k] for k in ('symbol','state','tradingEnabled','openapiEnabled','orderTypes','timeInForces','takerFeeRate','makerFeeRate','chainRelation')}
result['xt_chain_note']='chainRelation.chainId=2403 is exchange metadata; not assumed EVM chain id4663. Official exact-contract listing links Robinhood explorer. Current XT deposit/withdrawal path not checked.'
for label,rows in [('xt',read('xt-trades')['result']),('lbank',read('lbank-trades')['data'])]:
    times=[row['t' if label=='xt' else 'date_ms'] for row in rows]
    result['books'][label]['reported_trade_count']=len(times)
    result['books'][label]['reported_trade_latest_ms']=max(times)
    result['books'][label]['reported_trade_oldest_ms']=min(times)
a,b=[D(result['books'][label]['mid_USDT']) for label in ('lbank','xt')]
result['midpoint_difference_bps_lower_denominator']=text(abs(a-b)/min(a,b)*10000)
result['required_before_custom_price_use']=['Independent, reviewed and funded correctchain oracle publication/adapter with exact static ABI; no such current source discovered here.',
    'Native USD denomination or independently qualified USDT/USD conversion; do not assume USDT=USD.',
    'Common marketmaker, wash activity, manipulation, books versus real fills, venue halts, transferability and outage recovery review.',
    'Source method, upstream/admin/signing/updates, age/freshness/confidence and genuinely independent pair review.']
with (ROOT/'cex-findings.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps(result,indent=2))
