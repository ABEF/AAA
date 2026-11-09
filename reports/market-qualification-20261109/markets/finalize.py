from discover import *
from fractions import Fraction
import hashlib,datetime
if __name__=='__main__':
    dependencies=json.loads((ROOT/'wrapper-control-decoded.json').read_text(encoding='utf-8'))
    init_responses=json.loads((ROOT/'v4-initialize-bounded-02-response.raw').read_text(encoding='utf-8'))
    if len(init_responses)!=11 or any('error'in x or not isinstance(x.get('result'),list) for x in init_responses):raise ValueError('incomplete initialization discovery')
    source_records=json.loads((ROOT/'verified-source-manifest.json').read_text(encoding='utf-8'))
    for label,key in [('wrapper-implementation','implementation_runtime_keccak256'),('wrapper-admin','admin_runtime_keccak256')]:
        obj=json.loads((ROOT/('explorer-'+label+'-01-response.raw')).read_text(encoding='utf-8'))
        rawcode=bytes.fromhex(obj['deployed_bytecode'].removeprefix('0x'))
        if '0x'+keccak256(rawcode).hex()!=dependencies[key]:raise ValueError('dependency source code mismatch')
        folder=ROOT/'verified-flat'/label;folder.mkdir(parents=True,exist_ok=False)
        for index,item in enumerate([{'file_path':obj['file_path'],'source_code':obj['source_code']}]+obj.get('additional_sources',[])):
            pp=pathlib.PurePosixPath(item['file_path'])
            if pp.is_absolute() or '..' in pp.parts:raise ValueError('unsafe source path')
            target=folder/(str(index).zfill(3)+'.sol')
            raw=item['source_code'].encode('utf-8')
            with target.open('xb') as f:f.write(raw)
            source_records.append({'path':str(target.relative_to(ROOT)).replace('\\','/'),'original_file_path':item['file_path'],'sha256':hashlib.sha256(raw).hexdigest()})
    put('verified-source-manifest-final.json',source_records)
    # Validate v3 identities against the official factory query and pool getters.
    v3=json.loads((ROOT/'v3-state-decoded.json').read_text(encoding='utf-8'))
    for p in v3:
        for sig,expected in [('token0()',int(W,16)),('token1()',int(Z,16)),('fee()',p['fee']),('factory()',int(F,16))]:
            if int(p['reads'][sig]['result'],16)!=expected:raise ValueError('v3 pool identity mismatch')
    pools=json.loads((ROOT/'v4-hookless-state.json').read_text(encoding='utf-8'))
    discovered=json.loads((ROOT/'v4-discovered-pools.json').read_text(encoding='utf-8'))
    rows=json.loads((ROOT/'quotes-decoded.json').read_text(encoding='utf-8'))
    selected=next(x for x in pools if x['poolId'].startswith('0x501122'))
    feed=json.loads((ROOT/'quote-sizing.json').read_text(encoding='utf-8'))
    ratio=Fraction(selected['slot0']['sqrtPriceX96']**2,2**192)
    ethprice=Fraction(feed['chainlink_eth_usd'])
    ranks={label:[{'version':x['version'],'poolId':x.get('poolId'),'pool':x.get('pool'),'amountIn':x['amountIn'],'amountOut':x['amountOut'],'loss_bps_vs_own_spot':x['loss_bps_vs_own_spot'],'loss_bps_vs_selected_spot':x['loss_bps_vs_selected_spot']} for x in sorted([r for r in rows if r['label']==label and 'amountOut'in r],key=lambda r:r['amountOut'],reverse=True)] for label in ['zzz1','zzz1000','zzz10000','nominal_100usd_eth_half','nominal_100usd_zzz_half_at_selected_spot','nominal_5usd_eth_half','nominal_5usd_zzz_half_at_selected_spot']}
    final=rpc('anchor-final-recheck-02',[('eth_getBlockByNumber',[A['number'],False])])
    if final[0]['result']['hash']!=A['hash']:raise ValueError('anchor no longer canonical')
    report={
        'kind':'bounded read-only market qualification candidate; not production approval',
        'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'chainId':4663,'block_number':int(A['number'],16),'block_hash':A['hash'],'block_timestamp':int(A['timestamp'],16),
        'fixed_token':Z,'native_currency':'ETH','selected_pool':selected,
        'discovery_scope':{'v4':'All Initialize logs on the officially registered single core, native ETH/fixed ZZZ, block0..anchor in11 bounded<=10M block reads;102events; decoded PoolKeys recomputed. Not all chains/factories/pairs/hooked/multihop venues.', 'v4_total':len(discovered),'v4_hookless_static_fee_le_100000':len(pools),'v4_active_liquidity_nonzero':sum(bool(x['liquidity']) for x in pools),'v4_lowfee_le_10000_zero_active_L':sum(x['key'][2]<=10000 and x['liquidity']==0 for x in pools),'v3':'Official factory getPool for only fee100,250,500,1000,3000,10000; three nonzero addresses. Not exhaustive custom factory/fee discovery.'},
        'quotes':{'calls':len(rows),'successes':sum('amountOut'in x for x in rows),'reverts':sum('error'in x['response'] for x in rows),'gas_cap_each_eth_call':2000000,'all_quotes_eth_call_only':True,'ranked_by_exact_output':ranks},
        'prices':{'ETH_USD_sizing_candidate':feed,'selected_spot_ZZZ_per_ETH_exact':str(ratio),'selected_spot_derived_ZZZ_USD_exact':str(ethprice/ratio),'selected_spot_derived_ZZZ_USD_display':float(ethprice/ratio),'independent_ZZZ_USD':None,'dual_source_qualification':False},
        'conclusions':[
            'No tested candidate establishes default1% ZZZ-to-ETH conversion qualification. The low-fee native pools fail full-input quotes; both cheaper v3 pools fail quotes. The live v3 1% pool exceeds1% own-spot loss at every positive tested size, with additional selected-spot disagreement.',
            'Selected pool reverse full-fill capacity is directionally exhausted near tick125600. Verified quoter error specifically means actual input delta differs from requested. 1rawweiZZZ returns0ETH,1e6rawZZZ fails; upper tick net removes all current activeL. This is a pinned direction/size observation, not a claim no future reverse trade is possible.',
            'Native10018 is a candidate alternative execution venue, not a proposed LP destination or admitted route. Its exact output can beat selected in ETH-to-ZZZ direction, but its spot differs materially. Existing independent reference/venue guards must decide admissibility; no feed or loss cap was weakened.',
            'Pool-level exact swap quotes do not prove entrant marginal LP, main geometry, residual handling or operation gas. Owned-fork end-to-end preparation must verify those separately without synthetic depth or false independent feeds.',
            'v3 candidates are conversion-only for existing contracts and require preseal wrapper binding plus explicit reviewed proxy implementation/admin/admin-owner pins. Current automatic fresh7 worker is native-v4-only; no backend rollout is implied.',
            'WETH proxy unwrap source is ordinary aeWETH withdrawTo burning caller balance and sending native ETH; bridge mint disabled, gateway burn separate. Upgrade authority remains an external dependency risk.'
        ],
        'failures_preserved':['Initial unbounded-range eth_getLogs rejected by10M-block provider limit; original request/response retained.','First local state script rejected >32 batch before RPC; followup batches<=32 and original source retained.','Four urllib explorer requests403; originals retained, system HTTP retries200 explicitly decoded/re-encodedUTF8.','Quote reverts all retained as negative evidence; no retry with relaxed guards.','First wrapper dependency source extraction exceeded Windows path length; original partial extracted directory retained. Final flattened numbered sources preserve original paths in source manifest.'],
        'independent_core_diagnostic':{'origin':'Sibling owned-fork agent observed this separately; see original fork artifacts, not duplicate local proof.', 'original_paths':['../fork/attempt3/direct-reverse-1.json','../fork/attempt3/direct-reverse-1000000000000000000.json'],'reported_exact_1_ZZZ_request_core_deltas':{'native_output_wei':1,'ZZZ_input_raw':388557},'reported_1_raw_ZZZ_request_core_deltas':{'native_output_wei':0,'ZZZ_input_raw':1},'meaning':'Actual normal LPBalancer rejects partial fill or zero output; no guard weakened.'},
        'limitations':['No transactions, keys, deployment, services, source/docs edits, preexistingAnvil/journals/sites or pausedheartbeat changes.','Explorer-reported verified source/deployed bytes match pinned runtime hashes; independent source recompilation was not performed.','Captured liquidity L is not USD TVL or depth. Exact output depends on amount,direction,ticks and block.','ETH reference is one observed Chainlink feed, age5540seconds at anchor, not a qualified two-source price. ZZZ USD derived from selected pool is not independent.','No guarantee of global best execution, honest RPC, uptime, current block finality beyond canonical pinned rechecks, target gas suitability or MEV resistance.']
    }
    put('MARKET_FINDINGS.json',report)
    records=[]
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.name!='market-evidence-manifest.json':
            raw=path.read_bytes();records.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    put('market-evidence-manifest.json',{'sha256_algorithm':'SHA-256','source_scope':'read-only external evidence only; source HEAD99a01e97887156be0d31b61d453df4e29eb8a055 inspected, no source edits','files':records})
    raw=(ROOT/'market-evidence-manifest.json').read_bytes()
    print(json.dumps({'files':len(records),'bytes':sum(x['bytes'] for x in records),'manifest_sha256':hashlib.sha256(raw).hexdigest(),'derived_ZZZ_USD':report['prices']['selected_spot_derived_ZZZ_USD_display'],'verified_source_files':len(source_records)}))
