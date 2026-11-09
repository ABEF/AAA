# SPDX-License-Identifier: MIT
# Exact-input arithmetic port of Uniswap v4-core SwapMath/SqrtPriceMath/TickBitmap.
# Copyright 2023 Universal Navigation Inc. Original MIT source licenses retained
# under reports/market-qualification-20261109/markets/verified-sources/core/.
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from collect import *
Q=1<<96
def ceildiv(a,b):return(a+b-1)//b
def amount0(a,b,L,up):
 if a>b:a,b=b,a
 return ceildiv(ceildiv((L<<96)*(b-a),b),a)if up else((L<<96)*(b-a)//b)//a
def amount1(a,b,L,up):
 if a>b:a,b=b,a
 return ceildiv(L*(b-a),Q)if up else L*(b-a)//Q
def signed(x):return x-(1<<256)if x>=(1<<255)else x
def liquidity_capture():
 quotes=read('quotes.json');pools=read('v4-state.json');ids={r['poolId']for r in quotes if r['version']==4 and 'amountOut'in r}
 chosen=[p for p in pools if p['poolId']in ids];calls=[];requests=[]
 for p in chosen:
  center=(p['slot0']['tick']//p['key'][3])>>8
  for wp in range(center-1,center+2):requests.append((p['poolId'],wp));calls.append(call(S,'getTickBitmap(bytes32,int16)',p['poolId'],wp))
 res=batch('tick-bitmaps',calls)
 words={};ticks=[]
 for(pid,wp),r in zip(requests,res):
  assert'result'in r;bitmap=vals(r)[0];words.setdefault(pid,{})[str(wp)]=bitmap
  spacing=next(p['key'][3]for p in chosen if p['poolId']==pid)
  for bit in range(256):
   if bitmap>>bit&1:t=(wp*256+bit)*spacing;ticks.append((pid,t))
 assert len(ticks)<=250,'bounded tick capture exceeded'
 res=batch('tick-info',[call(S,'getTickInfo(bytes32,int24)',pid,t)for pid,t in ticks]);infos={}
 for(pid,t),r in zip(ticks,res):
  assert'result'in r;v=vals(r);infos.setdefault(pid,{})[str(t)]={'liquidityGross':v[0],'liquidityNet':signed(v[1]),'response':r}
 put('tick-state.json',{'anchor':PIN,'bitmap_word_radius':1,'scope':'Only pools with official successful quote responses, current and adjacent words; absent captured words remain unknown.','bitmaps':words,'ticks':infos})
 # Complete the gap pool screening at actual operation sizes; its fee is4%, not a cheap venue.
 gap=next(p for p in pools if p['poolId'].startswith('0x667a9f'))
 vectors=read('sizing.json')['vectors'];more=[x for x in vectors if x['label']not in('tiny_eth','tiny_zzz','zzz1')]
 res=batch('gap-operation-quotes',[v4call(gap['key'],v['zeroForOne'],v['amountIn'])for v in more],16)
 out=[]
 for v,r in zip(more,res):
  out.append({**v,'poolId':gap['poolId'],'key':gap['key'],'response':r,'amountOut':vals(r)[0]if'result'in r else None})
 put('gap-operation-quotes.json',out)
 print(json.dumps({'bitmap_reads':len(requests),'tick_info_reads':len(ticks),'gap_operation_success':sum(r['amountOut']is not None for r in out)}))
def nexttick(tick,spacing,zero,words):
 c=tick//spacing
 if zero:
  wp=c>>8;bit=c&255
  if str(wp)not in words:raise KeyError('uncaptured bitmap '+str(wp))
  masked=words[str(wp)]&((1<<(bit+1))-1);initialized=bool(masked);n=c-(bit-(masked.bit_length()-1)if initialized else bit)
 else:
  c+=1;wp=c>>8;bit=c&255
  if str(wp)not in words:raise KeyError('uncaptured bitmap '+str(wp))
  masked=words[str(wp)]&(((1<<256)-1)^((1<<bit)-1));initialized=bool(masked);lsb=(masked&-masked).bit_length()-1;n=c+(lsb-bit if initialized else 255-bit)
 return min(887272,max(-887272,n*spacing)),initialized
def swap(p,zfo,amount,tstate):
 price=p['slot0']['sqrtPriceX96'];tick=p['slot0']['tick'];L=p['liquidity'];protocol=p['slot0']['protocolFee'];prot=protocol&4095 if zfo else protocol>>12;lp=p['slot0']['lpFee'];fee=prot+lp-prot*lp//1000000
 left=amount;output=0;path=[];pid=p['poolId'];limit=4295128740 if zfo else 1461446703485210103287273052203988822378723970341
 try:
  for iteration in range(256):
   if not left or price==limit:break
   nt,initialized=nexttick(tick,p['key'][3],zfo,tstate['bitmaps'][pid]);endpoint=sqrt_price_at_tick(nt);target=max(endpoint,limit)if zfo else min(endpoint,limit)
   less=left*(1000000-fee)//1000000;need=amount0(target,price,L,True)if zfo else amount1(price,target,L,True)
   start=price
   if less>=need:
    price=target;spent=need;feepaid=ceildiv(spent*fee,1000000-fee)
   else:
    spent=less;price=ceildiv((L<<96)*price,(L<<96)+spent*price)if zfo else price+(spent<<96)//L;feepaid=left-spent
   out=amount1(price,start,L,False)if zfo else amount0(start,price,L,False);output+=out;left-=spent+feepaid
   path.append({'tickBefore':tick,'sqrtBefore':start,'L':L,'nextTick':nt,'initialized':initialized,'sqrtAfter':price,'input':spent,'fee':feepaid,'output':out,'remaining':left})
   if price==endpoint:
    if initialized:
     info=tstate['ticks'][pid][str(nt)];net=info['liquidityNet'];L+=-net if zfo else net;assert L>=0
    tick=nt-1 if zfo else nt
   elif price!=start:
    # Exact floor tick by integer endpoints, preserving downward-crossed boundary semantics above.
    lo=-887272;hi=887272
    while lo+1<hi:
     mid=(lo+hi)//2
     if sqrt_price_at_tick(mid)<=price:lo=mid
     else:hi=mid
    tick=lo
  else:raise ValueError('iteration bound reached')
  return{'status':'complete'if left==0 else'partial_limit','amountOut':output,'amountConsumed':amount-left,'remaining':left,'sqrtAfter':price,'tickAfter':tick,'liquidityAfter':L,'combined_fee_pips':fee,'path':path}
 except(KeyError,ZeroDivisionError)as x:return{'status':'capture_bound','error':str(x),'amountOut':output,'amountConsumed':amount-left,'remaining':left,'sqrtAfter':price,'tickAfter':tick,'liquidityAfter':L,'combined_fee_pips':fee,'path':path}
def replay():
 pools={p['poolId']:p for p in read('v4-state.json')};tstate=read('tick-state.json');rows=[]
 for quote in read('quotes.json'):
  if quote['version']!=4 or quote['poolId']not in tstate['bitmaps']:continue
  sim=swap(pools[quote['poolId']],quote['zeroForOne'],quote['amountIn'],tstate)
  row={k:v for k,v in quote.items()if k!='response'};row['replay']=sim
  if'amountOut'in quote:
   row['official_output_exact_match']=sim['status']=='complete'and sim['amountOut']==quote['amountOut']
   if sim['status']!='capture_bound':assert row['official_output_exact_match'],(row['poolId'],row['label'],quote['amountOut'],sim['amountOut'],sim['status'])
  rows.append(row)
 put('replay.json',rows);print(json.dumps({'rows':len(rows),'successful_output_exact_matches':sum(r.get('official_output_exact_match',False)for r in rows),'capture_bounds':sum(r['replay']['status']=='capture_bound'for r in rows)}))
if __name__=='__main__':{'capture':liquidity_capture,'replay':replay}[sys.argv[1]]()
