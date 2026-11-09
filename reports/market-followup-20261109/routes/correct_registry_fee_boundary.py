from collect import *
def main():
 findings=read('ROUTE_FINDINGS_FINAL.json');matrix=read('route-matrix-final.json');bands=read('common-reference-bands.json');states=read('v4-state.json')
 strict={p['poolId']:p['key'][2]<100000 for p in states}
 assert sum(strict.values())==70
 exact=[p for p in states if p['key'][2]==100000];assert len(exact)==1 and exact[0]['liquidity']==0
 findings['states']['principal_fee_compatible']=70
 findings['states']['strict_registry_principal_fee_admission_candidates']=70
 findings['states']['inclusive_balancer_fee_ceiling_filter_count']=71
 findings['states']['not_principal_admissible_by_fee_count']=25
 findings['states']['exact_100000_fee_inactive_pool']=exact[0]['poolId']
 findings['registry_fee_boundary_correction']={'reason':'Registry rejects key.fee >= maxSlippageBps*100 and maxSlippageBps<=1000. Therefore fee100000 is excluded despite Balancer _pool allowing fee<=100000.','strict_registry_filter':'fee<100000','inclusive_balancer_filter':'fee<=100000','earlier_final_snapshots':'Retained unchanged. Earlier71-compatible labels described the inclusive Balancer filter, not strict Registry admission.','active_principal_count_unchanged':8,'selected_destination':'Selected501122… remains principal LP destination; choosing a different destination is a separate unreviewed decision.'}
 for row in matrix['rows']:
  if row['version']==4:
   row['inclusive_balancer_fee_ceiling_compatible']=row['key'][2]<=100000
   row['principal_fee_compatible']=strict[row['poolId']]
   row['strict_registry_principal_fee_admission_candidate']=strict[row['poolId']]
   row['principal_admission_at_prior_200bps_swap_setting']=strict[row['poolId']]and row['key'][2]<20000
 for row in bands['rows']:
  row['inclusive_balancer_fee_ceiling_compatible']=row['key'][2]<=100000
  row['principal_fee_compatible']=strict[row['poolId']]
  row['strict_registry_principal_fee_admission_candidate']=strict[row['poolId']]
 bands['scope']='Selected501122… remains the principal LP destination. Bands compare ordinary balancing execution venues against that target; another destination requires a separate unreviewed decision.'
 assert sum(row['L']>0 and row['principal_fee_compatible']for row in bands['rows'])==8
 put('ROUTE_FINDINGS_FINAL_v2.json',findings);put('route-matrix-final-v2.json',matrix);put('common-reference-bands-v2.json',bands)
 text=(ROOT/'ROUTES_WITH_BANDS.md').read_text()
 text=text.replace('The95 hookless static v4 states include24 conversion-only fee tiers above the principal10% fee ceiling, six of them active but previously unmeasured. These six are not described as newly funded.','Of95 hookless static v4 states,70 pass the strict principal fee admission filter(fee<100000pips);25 do not(one at exactly100000 plus24 above it). The earlier inclusive Balancer fee-ceiling filter retained71; that count did not establish Registry admission. Six of the24 above10% are active but previously unmeasured, not newly funded.')
 text+='\nPrecision correction after independent review: Registry rejects `key.fee >= maxSlippageBps*100` while `maxSlippageBps<=1000`, so exactly100000pips is excluded from ordinary principal admission. The inactive exact10% pool is `'+exact[0]['poolId']+'`. Current counts are70strict principal fee candidates/25nonadmissible by fee/95total. The eight active principal candidates and selected+07ee2b common-reference result are unchanged. Selected501122… remains the LP destination throughout this analysis; changing destination would be a separate unreviewed decision. Use finalv2 findings/matrix/reference-band files and current README; previous final artifacts remain explicit snapshots.\n'
 with(ROOT/'ROUTES_FINAL_v2.md').open('x',encoding='utf-8',newline='\n')as f:f.write(text)
 with(ROOT/'README.previous-final.md').open('x',encoding='utf-8',newline='\n')as f:f.write((ROOT/'README.md').read_text())
 readme='''# Route evidence entry points

Final narrative: [ROUTES_FINAL_v2.md](ROUTES_FINAL_v2.md).
Final findings/counts: [ROUTE_FINDINGS_FINAL_v2.json](ROUTE_FINDINGS_FINAL_v2.json).
Direction/size/venue matrix: [route-matrix-final-v2.json](route-matrix-final-v2.json).
Necessary principal shared-reference admission bands: [common-reference-bands-v2.json](common-reference-bands-v2.json).
200k gas probes: [gas-budget-probes.json](gas-budget-probes.json).
Economic lower-bound arithmetic: [gas-economy.json](gas-economy.json).
Exact source pins: [source-pins-final.json](source-pins-final.json).
Complete current package integrity: [PACKAGE_MANIFEST_v2.json](PACKAGE_MANIFEST_v2.json).

Current strict Registry fee candidates:70(fee<100000pips),25not principal-admissible by fee(one exact100000 plus24above),95static hookless total. The earlier71 count is only the inclusive Balancer fee-ceiling filter. Eight active principal candidates and the selected+07ee2b necessary common-reference result are unchanged. Selected501122… remains LP destination; another destination is a separate unreviewed decision.

696 official quote calls include23 overlapping gas-budget rechecks; these are not696 distinct full operations.673 initial quote calls are646main,11gap follow-ups and16capacity probes. Full operation acceptance remains unavailable. No new RPC calls were needed for the fee-boundary correction. This package makes no production configuration or public transaction change. Earlier derived narrative/manifests, including README.previous-final.md, remain explicit snapshots.

Current earned conversion accepts only fixedZZZ -> nativeETH. Matrix numeric1% comparators for ETH -> ZZZ are explicitly not applicable as conversion eligibility; native principal balancing can use both directions. V3/WETH remains separate optional manual earned conversion and cannot be acquired after binding with wrapperzero. Fresh7 automation remains native-v4-only.
'''
 (ROOT/'README.md').write_text(readme,encoding='utf-8',newline='\n')
 put('PACKAGE_MANIFEST_v2.json',[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(ROOT.iterdir())if p.is_file()and p.name!='PACKAGE_MANIFEST_v2.json'])
 for row in read('PACKAGE_MANIFEST_v2.json'):
  raw=(ROOT/row['path']).read_bytes();assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
 print(json.dumps({'strict_registry_fee_candidates':70,'inclusive_balancer_filter':71,'nonprincipal_by_fee':25,'active_principal':8,'exact_boundary_pool':exact[0]['poolId'],'package_payloads':len(read('PACKAGE_MANIFEST_v2.json'))}))
if __name__=='__main__':main()
