from collect import *
def main():
 pools=read('v4-state.json');quotes=read('quotes.json');caps=read('small-capacity-quotes.json');chosen=[]
 for r in quotes:
  if r['version']!=4:continue
  pid=r['poolId'];lab=r['label']
  if(pid==SELECTED and r['zeroForOne'])or(pid.startswith('0x9fa185')and lab in['nominal_100usd_eth_half','nominal_5usd_eth_half','nominal_100usd_zzz_half','nominal_5usd_zzz_half','zzz1','zzz1000']):chosen.append(r)
 for r in caps:
  if r.get('amountOut',0)>0:chosen.append(r)
 calls=[]
 for r in chosen:
  m,p=v4call(r['key'],r['zeroForOne'],r['amountIn']);p[0]['gas']=hex(200000);calls.append((m,p))
 res=batch('quote-gas200k',calls,16);out=[]
 for r,response in zip(chosen,res):
  row={k:r[k]for k in('poolId','label','amountIn','zeroForOne','amountOut')if k in r};row['gas_cap']=200000;row['response']=response
  if'result'in response:row['amountOut200k']=vals(response)[0];row['matches_2M_quote']=row['amountOut200k']==r['amountOut'];assert row['matches_2M_quote']
  out.append(row)
 put('gas-budget-probes.json',{'warning':'Official quoter gas-capped read-only probes only.200k matches the Balancer engineering subcall budget but the production quoteCandidate has a different wrapper/callback path. This does not establish complete-operation, converter, transaction, provider or cost acceptance. Gas-priced economics also need a reviewed network-fee ceiling and real entitlement sizes.','rows':out})
 canonical('canonical-final')
 print(json.dumps({'calls':len(out),'success':sum('amountOut200k'in x for x in out),'same_output':sum(x.get('matches_2M_quote',False)for x in out)}))
if __name__=='__main__':main()
