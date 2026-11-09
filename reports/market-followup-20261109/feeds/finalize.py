"""Finalize offline evidence. No network or repository writes."""
import datetime,decimal,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from zzz_ops.abi import keccak256
P=Path(__file__).resolve().parent;D=decimal.Decimal
def read(n):return json.loads((P/n).read_text(encoding='utf8'))
def save(n,v):(P/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def words(s):return[int(s[i:i+64],16)for i in range(2,len(s),64)]
def addr(n):return'0x'+f'{n:040x}'
def array(s):
 w=words(s);o=w[0]//32;return[addr(n)for n in w[o+1:o+1+w[o]]]
def w(n):return int(n).to_bytes(32,'big')
R=read('anchor-reads.json');F=read('followup-reads.json');C=read('final-controls.json');CL=read('chainlink-controls.json');out=read('decoded-findings.json')
clowners=array(F['reads']['chainlink-owner']['getOwners()']);apiowners=array(F['reads']['api3-safe']['getOwners()']);tx=array(CL['reads']['getTransmitters()'])
# getGuardianSet returns one dynamic tuple(address[],uint32).
gs=words(F['reads']['pyth-wormhole']['guardianSet']);base=gs[0]//32;off=base+gs[base]//32;routers=[addr(n)for n in gs[off+1:off+1+gs[off]]]
out['literal_public_address_overlap']={'chainlink_admin_owners':clowners,'api3_admin_owners':apiowners,'chainlink_transmitters':tx,'pyth_verifier_keys':routers,
 'chainlink_admin_vs_api3_admin':sorted(set(clowners)&set(apiowners)),'chainlink_admin_vs_pyth_keys':sorted(set(clowners)&set(routers)),'api3_admin_vs_pyth_keys':sorted(set(apiowners)&set(routers)),
 'interpretation':'No address equality is not proof of independent people, organizations, infrastructure or markets. Safe modules/guards/delegates and real-world operator provenance remain unqualified.'}
out['chainlink']['transmitter_count']=len(tx)
out['chainlink']['transmitters_getter']='getTransmitters()'
out['chainlink']['old_transmitters_call_failure']='Wrong ABI getter retained in anchor-rpc.json; not treated as missing or zero reporters.'
out['chainlink']['controls']={k:v for k,v in CL['reads'].items()if k!='getTransmitters()'}
out['chainlink']['source_evidence']={'source_manifest':'../review/chainlink-source-match.json','source':'../review/ChainlinkDualAggregator.explorer.sol','status':'Explorer partial verification with exact explorer-runtime/on-chain-runtime equality; not independent recompilation or full source verification.'}
mapped=json.loads((P.parent/'review/chainlink-config-map-findings.json').read_text(encoding='utf8'));config=mapped['rows'][0]
current_digest='0x'+R['reads']['chainlink-aggregator']['latestConfigDetails()'][-64:]
out['chainlink']['current_config']={'event':config,'digest_matches_shared_anchor':config['configDigest']==current_digest,'transmitters_match_current_getter':config['transmitters']==tx,'source_report_signature_count_f_plus_1':config['f']+1,'evidence':'../review/chainlink-config-map-findings.json','block_number_scope':'ConfigSet block.number is the Arbitrum ancestor-chain height, not the RPC L2 block number. The mapped L2 event is33090. Original empty unmapped lookup is retained and is not evidence of absent configuration.','scope':'Exact public keys and f do not establish actual node organizations, exchange/vendor independence or full operating qualification.'}
out['literal_public_address_overlap']['chainlink_report_signers']=config['signers']
out['literal_public_address_overlap']['chainlink_report_signers_vs_pyth_keys']=sorted(set(config['signers'])&set(routers))
out['literal_public_address_overlap']['chainlink_report_signers_vs_api3_admin']=sorted(set(config['signers'])&set(apiowners))
out['pyth']['implementation']={'address':F['reads']['pyth-implementation']['address'],**{k:v for k,v in F['reads']['pyth-implementation']['runtime'].items()if k!='raw'}}
out['pyth']['governance_source']={'chain_id':1,'emitter':'0x5635979a221c34931e32620b9293a463065555ea71fe97cd6237ade875b12e9e','raw':R['reads']['pyth-core']['governanceDataSource()']}
out['pyth']['verifier']={'address':F['reads']['pyth-wormhole']['address'],'guardian_set_index':int(F['reads']['pyth-wormhole']['getCurrentGuardianSetIndex()'],16),'keys':routers,'key_count':len(routers),'governance_chain_id':int(F['reads']['pyth-wormhole']['governanceChainId()'],16),'governance_contract':F['reads']['pyth-wormhole']['governanceContract()'],'wormhole_domain_chain_id':int(F['reads']['pyth-wormhole']['chainId()'],16),'quorum_getter_result':C['reads']['pyth-quorum-5'],'documented_architecture_quorum':'3 of 5 routers; independently proving exact verifier implementation/quorum remains open.'}
out['pyth']['fees_scope']='Live zero fee storage getters agree with current official docs. No authenticated signed update, actual getUpdateFee(packet), paid data access, updater funding, submission gas or lifecycle recovery was qualified; reads used 500000 gas ceilings, not actual gas measurements.'
offers=read('api3-pricing/api3-eth-offers.raw');offerrows=[]
for leaf in offers['leaves']:
 name,chain,params,duration,price=leaf['value'];par=bytes.fromhex(params[2:]);encoded=bytes.fromhex(name[2:])+w(chain)+w(160)+w(duration)+w(price)+w(len(par))+par
 h=keccak256(keccak256(encoded))
 for ph in leaf['proof']:
  peer=bytes.fromhex(ph[2:]);h=keccak256(min(h,peer)+max(h,peer))
 nums=words(params)
 offerrows.append({'duration_seconds':int(duration),'duration_days':str(D(duration)/86400),'price_parameter_wei':price,'price_parameter_ETH':str(D(price)/10**18),'update_parameters_raw':params,'deviation_percent':str(D(nums[0])*100/D(10**8)),'deviation_reference':str(nums[1]),'heartbeat_seconds':nums[2],'merkle_proof_valid':('0x'+h.hex())==offers['merkleRoot']})
out['api3']['candidate_source_commit']='bd8b08d7aa2203c5f3f103d4600b3b9f39d30e1c'
out['api3']['ETH/USD']['proxy_implementation']={k:v for k,v in C['reads']['api3-implementation'].items()if k!='code'}
out['api3']['ETH/USD']['admin_slot']=C['reads']['api3-admin-slot']
out['api3']['ETH/USD']['owner_forwarder']=F['reads']['api3-forwarder']['address']
out['api3']['ETH/USD']['forwarder_owner']=F['reads']['api3-safe']['address']
out['api3']['ETH/USD']['owner_safe_threshold']=4
out['api3']['ETH/USD']['owner_safe_owner_count']=len(apiowners)
out['api3']['offers']={'source':'https://api3dao.github.io/data-feeds/market/dapi-pricing/4663/ETH-USD.json','root':offers['merkleRoot'],'onchain_root_at_anchor':C['reads']['api3-pricing-root-at-anchor'],'root_matches_shared_anchor':offers['merkleRoot']==C['reads']['api3-pricing-root-at-anchor'],'rows':offerrows,'selected_or_purchased':False,
 'scope':'Published price parameters in sponsor-wallet funding offers. Final purchase payment also depends on sponsor balance, queued subscriptions/readiness and transaction gas; no payable call simulated or made. No operating heartbeat or deviation selected.'}
out['api3']['catalog']=read('api3-catalog-extracted.json')
out['api3']['independence_scope']='Catalog provider labels are availability metadata, not the actual activated ETH reporter/market set. No active ETH binding means no actual ETH source set at this anchor. New immutable read-only adapter, upstream pins, provider/control review and funded liveness would be separate work.'
base=read('api3-base-retry.json'); basewords=words(base['reads']['server_base'])
out['api3']['ETH/USD']['catalog_base_feed']={'id':base['feed_id'],'provider':base['provider'],'canonical_recheck':base['canonical_recheck'],'raw_value':str(basewords[0]),'timestamp':basewords[1],'interpretation':'No initialized underlying price observation at shared anchor, not a zero USD price. Registry details are empty.','raw_evidence':'api3-base-retry.json','management_literal_evidence':'api3-management-selected.json'}
out['api3']['ETH/USD']['management_mapping_verification']=read('api3-mapping-proof.json')
out['research_provider_limits']={'official_public_RPC':'Initial canonical state reads succeeded. By2026-11-09T20:16:17UTC the exact anchor header remained readable but the state returned historical-state-unavailable.','official_failure_evidence':'api3-base-rpc.json','alternate_public_pinax_retry':'Chain4663, exact shared header and hash selector checked; three API3 base reads succeeded with canonical header recheck. This bounded success is not archive/provider availability qualification.'}
fresh=read('fresh-secondary-reads.json');fa=fresh['secondary_anchor'];cw=words(fresh['reads']['chainlink_primary']);pw=words(fresh['reads']['pyth_ETH']);bw=words(fresh['reads']['api3_server_base'])
out['separately_labeled_fresh_liveness']={'evidence':'fresh-secondary-reads.json','anchor':fa,'canonical_recheck':fresh['canonical_recheck'],'api3_base_initialized':bw[1]!=0,'api3_base_timestamp':bw[1],'api3_registry_details_empty':fresh['reads']['api3_registry_details']=='0x'+f'{32:064x}'+f'{0:064x}','chainlink_round_id':str(cw[0]),'chainlink_answer_raw':str(cw[1]),'chainlink_updated_at':cw[3],'chainlink_age_seconds':fa['block_timestamp']-cw[3],'pyth_price_raw':str(pw[0]),'pyth_publish_time':pw[3],'pyth_age_seconds':fa['block_timestamp']-pw[3],'scope':'Contemporary liveness evidence only, never substituted for the original shared anchor or used to qualify market execution.'}
for source,name in [('approved-public/chainlink-catalog.raw','chainlink'),('approved-public/pyth-symbols.raw','pyth')]:
 data=read(source);rows=data if isinstance(data,list)else data.get('symbols',data.get('feeds',[]));matches=[x for x in rows if 'ZZZ'in str(x.get('name','')).upper()or'ZZZ'in str(x.get('symbol','')).upper()or'7dbf38976f6d3b9c529e7d9484a71898b409ee6a'in json.dumps(x).lower()]
 out.setdefault('fixed_ZZZ_catalog_checks',{})[name]={'row_count':len(rows),'matches':matches,'source':source,'scope':'No match in this retrieved public catalog; custom/private services and alternative naming remain unresolved.'}
out['fixed_ZZZ_catalog_checks']['api3']={'row_count':out['api3']['catalog']['row_count'],'matches':out['api3']['catalog']['ZZZ_matches'],'ZZZ_USD_offer_http_status':404,'ZZZ_USD_name_onchain_unset':True,'computed_ZZZ_USD_proxy_code_empty':True}
out['fixed_ZZZ_catalog_checks']['other_market_leads']='See ../review/cex-findings.json for exact-token LBank/XT upstream leads. CEX ticker books are not on-chain USD feeds and do not establish independent publishers, USDT/USD conversion, suitable depth or PoPL ABI compatibility.'
out['liveness']={'chainlink_correct_chain_uptime_feed':None,'source':'https://docs.chain.link/data-feeds/l2-sequencer-feeds','status':'Robinhood absent from official supported list; docs state no expansion to additional networks. Live progressing blocks/readable current price do not substitute for reviewed sequencer outage/grace and upstream controls.'}
out['status']={'source_existence':'Chainlink ETH reference and inactive API3 ETH proxy exist; Pyth Core exists with stale stored ETH.','actual_release_admission':'BLOCKED','ETH_pair':'BLOCKED by stale Pyth and spread above300bps; API3 inactive/ABI-incompatible for direct use.','fixed_ZZZ_pair':'BLOCKED: no two independently qualified correct-token USD sources established.','production_approval':False,'changes':'External evidence only. No repository source/config, chain update, funds, deployment, signing, provider contact or service changes.'}
out['primary_links']={'pyth_fees':'https://docs.pyth.network/pro/on-chain-fees','pyth_auth':'https://docs.pyth.network/pro/pyth-core-upgrade','pyth_architecture':'https://docs.pyth.network/pro/how-lazer-works','pyth_addresses':'https://docs.pyth.network/pro/contract-addresses','pyth_sponsored':'https://docs.pyth.network/pro/sponsored-feeds','api3_rounds':'https://docs.api3.org/dapps/integration/aggregatorv2v3interface.html','api3_market':'https://market.api3.org/robinhood','api3_source':'https://github.com/api3dao/contracts/tree/bd8b08d7aa2203c5f3f103d4600b3b9f39d30e1c','chainlink_uptime':out['liveness']['source']}
out['checks']={'exact_integer_300bps':abs(int(out['chainlink']['answer_raw'])*10**10-int(out['pyth']['price_raw'])*10**10)*10000<=min(int(out['chainlink']['answer_raw'])*10**10,int(out['pyth']['price_raw'])*10**10)*300,'all_5_offer_proofs_pass':all(x['merkle_proof_valid']for x in offerrows),'all_canonical_rechecks_pass':all([R['canonical_recheck'],F['canonical_recheck'],C['canonical_recheck'],CL['canonical_recheck'],base['canonical_recheck']])}
save('FEED_FINDINGS.json',out)
print(json.dumps({'status':out['status'],'checks':out['checks'],'literal_admin_owner_overlap':out['literal_public_address_overlap']['chainlink_admin_vs_api3_admin'],'api3_offers':offerrows},indent=2))
