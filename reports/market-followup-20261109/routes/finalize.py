from collect import *
from fractions import Fraction
import ast
def main():
 findings=read('ROUTE_FINDINGS.json');gas=read('gas-budget-probes.json')['rows'];matrix=read('route-matrix.json');quotes=read('quotes.json')
 findings['quotes']['gas200k_rechecks']=len(gas);findings['quotes']['gas200k_success']=sum('amountOut200k'in r for r in gas);findings['quotes']['all_quote_calls_including_gas_rechecks']=findings['quotes']['all_quote_calls']+len(gas)
 findings['quotes']['gas200k_failure_detail']='Alternative10018 nominal100USD reverse half also fails at2M with decoded NotEnoughLiquidity; at200k original wrapped empty revert is preserved, not relabelled.'
 basefee=int(ANCHOR['header']['baseFeePerGas'],16);cost=basefee*21000
 passes=[r for r in matrix['rows']if not r['zeroForOne']and r['conditional_conversion_floor_only']]
 maxout=max(r['amountOut']for r in passes)
 economy={'anchor_base_fee_per_gas_wei':basefee,'transaction_intrinsic_gas_lower_bound':21000,'intrinsic_base_fee_lower_bound_wei':cost,'largest_observed_conditional_1percent_floor_passing_reverse_output_wei':maxout,'intrinsic_basefee_cost_to_largest_passing_output':str(Fraction(cost,maxout)),'boundary':'Arithmetic diagnostic at captured header basefee only, not a transaction fee quote, actual fee paid, production cost selection or target-gas acceptance. Actual conversion requires more than intrinsic gas, and fee/basefee/timing/provider terms can change. Worker converts whole selected NFT entitlements, not arbitrary input fractions.'}
 findings['economy_diagnostic']=economy
 findings['public_market_scope']='External market read-only quote depth only. No PoPL deployed LP was closed or withdrawn; postwithdrawal remaining-depth behavior and future dominant-PoPL liquidity are not qualified.'
 findings['partial_fill_semantics']={'path':'reports/market-qualification-20261109/markets/verified-sources/quoter/src/pkgs/v4-periphery/src/base/BaseV4Quoter.sol','line':54,'meaning':'Compares signed amountSpecifiedActual against exact requested amountSpecified, reverting NotEnoughLiquidity(poolId) if unequal. Positive quote output alone still needs full converter guards.'}
 findings['cheap_zero_active_failure_classes']={'decoded_incomplete_input':sum(r.get('failure_class')=='not_enough_liquidity_wrapped'for r in quotes if r.get('L')==0 and r.get('key',[0,0,10001])[2]<=10000),'other_preserved_errors':sum(r.get('failure_class')=='preserved_error'for r in quotes if r.get('L')==0 and r.get('key',[0,0,10001])[2]<=10000),'no_inference':'Other errors are retained without claiming proven global absent liquidity.'}
 put('ROUTE_FINDINGS_FINAL.json',findings);put('gas-economy.json',economy)
 old=(ROOT/'ROUTES.md').read_text();old=old.replace('There are **673 official quote calls**:','The initial size/capacity capture contains **673 official quote calls**:')
 old+='\nThe final200,000-gas official-quoter recheck adds23calls:22outputs exactly match the earlier2M-gas quotes, including all selected native ETH vectors and13 positive capacity probes. The remaining100USD reverse-half alternative quote was already incomplete-input at2M; its200k wrapped empty error is retained. Same-budget official-quoter success does not qualify the distinct production Balancer wrapper/callback path, full transaction or converter gas. Total quote calls including these overlapping rechecks: **696**.\n\n'
 old+='At the captured block basefee **'+str(basefee)+'wei/gas**, even21,000 intrinsic gas costs **'+str(cost)+'wei** before any conversion execution. The largest observed reverse output passing the correlated1% floor is **'+str(maxout)+'wei**, about'+f'{cost/maxout:.2f}'+'times smaller than that intrinsic-only basefee cost. This arithmetic is not an actual fee quote or paid cost, and no operating fee ceiling was selected. Actual keeper conversion uses whole selected NFT entitlements, not arbitrary slices manufactured from these input vectors.\n\n'
 old+='These are external market quote depths. No PoPL deployed LP was withdrawn, and the evidence does not qualify remaining external depth after a future PoPL close or a future LP that dominates the market. Full-input semantics are authenticated in retained BaseV4Quoter.sol lines54–56: signed actual specified delta must equal the exact request or NotEnoughLiquidity is thrown. Empty-active-L cheap candidates retain191 decoded incomplete-input errors and19 other errors; the latter are not silently converted into proven no-liquidity findings.\n\n'
 old+='Use **ROUTE_FINDINGS_FINAL.json**, **ROUTES_FINAL.md** and **final-manifest.json** as the final evidence pointers. Earlier derived findings/manifests remain intact as intermediate snapshots.\n'
 with(ROOT/'ROUTES_FINAL.md').open('x',encoding='utf-8',newline='\n')as f:f.write(old)
 sources=read('source-pins.json');paths=['reports/market-qualification-20261109/markets/verified-sources/quoter/src/pkgs/v4-periphery/src/base/BaseV4Quoter.sol','reports/market-qualification-20261109/markets/verified-sources/quoter/src/pkgs/v4-periphery/src/lens/V4Quoter.sol']
 for s in paths:sources.append({'path':s,'bytes':(REPO/s).stat().st_size,'sha256':hashlib.sha256((REPO/s).read_bytes()).hexdigest()})
 put('source-pins-final.json',sources)
 # Independent parse/hash verification, no repeat network or production test suite.
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 for p in ROOT.glob('*.json'):json.loads(p.read_text(encoding='utf-8'))
 for source in sources:assert hashlib.sha256((REPO/source['path']).read_bytes()).hexdigest()==source['sha256']
 put('final-manifest.json',[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(ROOT.iterdir())if p.is_file()and p.name!='final-manifest.json'])
 for item in read('final-manifest.json'):
  raw=(ROOT/item['path']).read_bytes();assert len(raw)==item['bytes']and hashlib.sha256(raw).hexdigest()==item['sha256']
 print(json.dumps({'final_manifest_payloads':len(read('final-manifest.json')),'all_quote_calls_including_overlapping_gas_rechecks':findings['quotes']['all_quote_calls_including_gas_rechecks'],'gas_recheck_success':findings['quotes']['gas200k_success'],'source_pins':len(sources),'intrinsic_basefee_lower_bound_wei':cost,'largest_conditional_passing_reverse_output_wei':maxout}))
if __name__=='__main__':main()
