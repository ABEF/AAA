from collect import *
def main():
 matrix=read('route-matrix.json')
 for r in matrix['rows']:
  r['earned_conversion_current_direction_compatible']=not r['zeroForOne']
  r['fresh7_automated_earned_conversion_venue_direction_compatible']=r['version']==4 and not r['zeroForOne']
  if r['zeroForOne']:r['conditional_conversion_floor_only']=None;r['conversion_floor_scope']='Not applicable: current earned route requires fixedZZZ input and nativeETH output. Numeric1% comparator is retained only as arithmetic.'
 put('route-matrix-final.json',matrix)
 text='''# Route evidence entry points

Final narrative: [ROUTES_WITH_BANDS.md](ROUTES_WITH_BANDS.md).
Final findings/counts: [ROUTE_FINDINGS_FINAL.json](ROUTE_FINDINGS_FINAL.json).
Direction/size/venue matrix: [route-matrix-final.json](route-matrix-final.json).
Necessary principal shared-reference admission bands: [common-reference-bands.json](common-reference-bands.json).
200k gas probes: [gas-budget-probes.json](gas-budget-probes.json).
Economic lower-bound arithmetic: [gas-economy.json](gas-economy.json).
Exact source pins: [source-pins-final.json](source-pins-final.json).
Complete package integrity: [PACKAGE_MANIFEST.json](PACKAGE_MANIFEST.json).

696 official quote calls include23 overlapping gas-budget rechecks; these are not696 distinct full operations.673 initial quote calls are646 main,11 gap follow-ups and16 capacity probes. Full operation acceptance remains unavailable. This package makes no production configuration or public transaction change. Earlier derived narrative/manifests remain explicit intermediate snapshots.

Current earned conversion accepts only fixedZZZ -> nativeETH. Matrix numeric1% comparators for ETH -> ZZZ are explicitly not applicable as conversion eligibility; native principal balancing can use both directions. V3/WETH remains separate optional manual earned conversion and cannot be acquired after binding with wrapperzero. Fresh7 automation remains native-v4-only.
'''
 with(ROOT/'README.md').open('x',encoding='utf-8',newline='\n')as f:f.write(text)
 put('PACKAGE_MANIFEST.json',[{'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in sorted(ROOT.iterdir())if p.is_file()and p.name!='PACKAGE_MANIFEST.json'])
 for r in read('PACKAGE_MANIFEST.json'):
  raw=(ROOT/r['path']).read_bytes();assert len(raw)==r['bytes']and hashlib.sha256(raw).hexdigest()==r['sha256']
 print(json.dumps({'package_payloads':len(read('PACKAGE_MANIFEST.json')),'matrix_rows':len(matrix['rows'])}))
if __name__=='__main__':main()
