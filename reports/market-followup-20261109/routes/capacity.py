from replay import *
def capture():
 pools=read('v4-state.json');rows=[];calls=[]
 for prefix in['0x501122','0x19820d','0x07ee2b']:
  p=next(p for p in pools if p['poolId'].startswith(prefix))
  amounts=[1,388556,388557,388558]if prefix=='0x501122'else[10**n for n in range(12,18)]
  for amount in amounts:
   rows.append({'poolId':p['poolId'],'key':p['key'],'label':'capacity_'+str(amount),'zeroForOne':False,'amountIn':amount});calls.append(v4call(p['key'],False,amount))
 res=batch('small-capacity-quotes',calls,16);tstate=read('tick-state.json')
 for row,r in zip(rows,res):
  row['response']=r;p=next(p for p in pools if p['poolId']==row['poolId']);row['replay']=swap(p,False,row['amountIn'],tstate)
  if'result'in r:
   row['amountOut']=vals(r)[0];row['official_output_exact_match']=row['replay']['status']=='complete'and row['replay']['amountOut']==row['amountOut'];assert row['official_output_exact_match']
 put('small-capacity-quotes.json',rows);canonical('canonical-after-capacity');print(json.dumps({'rows':len(rows),'success':sum('amountOut'in x for x in rows)}))
if __name__=='__main__':capture()
