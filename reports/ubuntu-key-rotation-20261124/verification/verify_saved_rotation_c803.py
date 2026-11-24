"""NEW stdlib-only saved key-rotation vectors, not keeper/test execution.
Binds NEW c803 ROTATION_VECTORS; exact legacy2gwei governance input, no guessed fields.
No RPC, subprocess, signing, journal repair or file writes. JSON result to stdout.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, re, stat

MAX_FILE=16*1024*1024
ACCESS='0xfa26e96e5f11a855d737cff71a19e133d8349e83'
CONFIRMATION='0xb08943c851cd817e36f2040a47038e47ba769ca1'
GOVERNANCE='0x000000000000000000000000000000000000a0a0'
BUCKET=47181787163762592248710325652087236475813397965818762058663276509558631703230
RESET='0x7cd5329f'
SET_KEEPER='0xd1b9e853'
KEEPER_CHANGED='0x4e4109d520c9526f0541c4732fe75bfe81842ffcba4a1a829277abfaeba117da'
OBSERVATION_RESET='0xed377ef7177931bf925f7a5af408042d8f521d3cc984d24f9e401c0e49461fee'

class Refused(ValueError):pass

def need(condition,message):
 if not condition:raise Refused(message)

def uint(value):
 if type(value)is str:
  need(re.fullmatch(r'0|[1-9][0-9]{0,77}',value)is not None,'Invalid decimal integer');value=int(value)
 need(type(value)is int and 0<=value<1<<256,'Invalid unsigned integer');return value

def q(value):
 need(type(value)is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})',value)is not None,'Invalid hexadecimal quantity');return int(value,16)

def addr(value):
 need(type(value)is str and re.fullmatch(r'0x[0-9a-fA-F]{40}',value)is not None,'Invalid address');return value.lower()

def h(value):
 need(type(value)is str and re.fullmatch(r'0x[0-9a-fA-F]{64}',value)is not None and int(value,16)>0,'Invalid nonzero hash');return value.lower()

def word(value):return f'{uint(value):064x}'

def load(path):
 path=Path(path);st=path.lstat();need(stat.S_ISREG(st.st_mode)and not path.is_symlink()and st.st_size<=MAX_FILE,'Input is not a bounded regular JSON file');raw=path.read_bytes();need(len(raw)==st.st_size,'Input changed while reading')
 def pairs(rows):
  result={}
  for key,value in rows:need(key not in result,'Duplicate JSON field');result[key]=value
  return result
 def nonfinite(_):raise Refused('Non-finite JSON')
 return json.loads(raw.decode('utf8','strict'),object_pairs_hook=pairs,parse_constant=nonfinite),{'name':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def inclusion(transaction,receipt,header):
 need(h(transaction['hash'])==h(receipt['transactionHash']),'Transaction/receipt hash mismatch')
 need(h(transaction['blockHash'])==h(receipt['blockHash'])==h(header['hash'])and q(transaction['blockNumber'])==q(receipt['blockNumber'])==q(header['number']),'Canonical inclusion mismatch')
 index=q(receipt['transactionIndex']);need(q(transaction['transactionIndex'])==index,'Transaction index mismatch')
 need(type(header['transactions'])is list and index<len(header['transactions'])and h(header['transactions'][index])==h(transaction['hash']),'Canonical header transaction order mismatch')
 need(addr(receipt['from'])==addr(transaction['from'])and addr(receipt['to'])==addr(transaction['to']),'Receipt endpoints mismatch')
 return index

def setter(row,account,enabled):
 tx=row['transaction'];receipt=row['receipt'];header=row['canonical_header'];index=inclusion(tx,receipt,header)
 need(q(receipt['status'])==1 and addr(tx['from'])==GOVERNANCE and addr(tx['to'])==ACCESS,'Governance role transaction identity differs')
 need(tx['input'].lower()==SET_KEEPER+word(int(account,16))+word(int(enabled))and q(tx['value'])==0,'Role setter calldata differs')
 events=[event for event in receipt['logs']if addr(event['address'])==ACCESS and event.get('topics')and event['topics'][0].lower()==KEEPER_CHANGED]
 need(len(events)==1 and len(events[0]['topics'])==2 and int(events[0]['topics'][1],16)==int(account,16)and events[0]['data'].lower()=='0x'+word(int(enabled)),'Exact KeeperChanged event differs')
 return index

def execution_cost(row):
 tx=row['transaction'];receipt=row['receipt'];header=row['canonical_header'];review=row['pending_intent']['fee_review'];need(type(review.get('schema'))is int and review['schema']==1,'Only this reviewed schema1 fixture is qualified');kind=q(tx.get('type','0x0'));used=q(receipt['gasUsed']);limit=q(tx['gas'])
 need(0<used<=limit<=24000000 and limit==uint(review['gas_limit']),'Gas limit differs from saved24M review')
 if kind==2:
  cap=q(tx['maxFeePerGas']);tip=q(tx['maxPriorityFeePerGas']);base=q(header['baseFeePerGas']);need(tip<=cap and base<=cap,'Invalid canonical type2 envelope');price=min(cap,base+tip)
 elif kind in(0,1):
  cap=q(tx['gasPrice']);price=cap;need(q(receipt['effectiveGasPrice'])==cap,'Legacy receipt price differs from signed gasPrice')
 else:raise Refused('Unsupported transaction fee type')
 need(0<cap<=5000000000 and cap==uint(review['max_fee_per_gas']),'Captured fee cap differs')
 need(review['receipt_fee_policy']=='included'and uint(review['l1_fee_allowance_wei'])==0 and q(receipt.get('l1Fee','0x0'))==0,'Unexpected chain fee semantics')
 value=q(tx['value']);need(value==uint(row['pending_intent']['value'])==0,'Reset must send no native value')
 cost=used*price;maximum=limit*cap
 need(maximum==uint(review['maximum_cost_wei'])and cost<=maximum<=10**16,'Actual/reviewed fee exceeds unchanged bound')
 return {'gas_used':used,'signed_gas_limit':limit,'canonical_price_wei':price,'reported_price_wei':q(receipt['effectiveGasPrice']),'actual_cost_wei':cost,'reviewed_maximum_wei':maximum,'fee_review_schema':review['schema']}

def settled(row,expect_success):
 tx=row['transaction'];receipt=row['receipt'];header=row['canonical_header'];inclusion(tx,receipt,header)
 need(q(receipt['status'])==int(expect_success),'Wrong keeper receipt status')
 need(addr(tx['to'])==CONFIRMATION and tx['input'].lower()==RESET+word(BUCKET)and q(tx['nonce'])==0 and q(tx['chainId'])==4663,'Not the exact onlyKeeper reset job')
 intent=row['pending_intent'];need(h(intent['hash'])==h(tx['hash'])and addr(intent['to'])==CONFIRMATION and intent['data'].lower()==tx['input'].lower()and uint(intent['nonce'])==0,'Saved intent differs from original signed job')
 before=row['state_before'];after=row['state_after'];need(addr(before['sender'])==addr(after['sender'])==addr(tx['from'])and uint(before['chain_id'])==uint(after['chain_id'])==4663,'State identity differs');need(uint(before['next_nonce'])==0 and uint(after['next_nonce'])==1 and after['pending']is None,'Nonce/pending recovery did not advance exactly once')
 anchor=after['receipt_anchor'];need(anchor['hash'].lower()==header['hash'].lower()and uint(anchor['number'])==q(header['number'])and uint(anchor['timestamp'])==q(header['timestamp'])and uint(anchor['nonce'])==0,'Recovered canonical anchor differs')
 confirmed=row['confirmed_head'];need(q(confirmed['number'])-q(header['number'])+1>=12 and q(confirmed['timestamp'])>=q(header['timestamp']),'Insufficient confirmed depth')
 fees=execution_cost(row);day=datetime.datetime.fromtimestamp(q(header['timestamp']),datetime.timezone.utc).date().isoformat();old_spent=before['spent'];new_spent=after['spent'];expected={key:uint(value)for key,value in old_spent.items()};expected[day]=expected.get(day,0)+fees['actual_cost_wei'];need({key:uint(value)for key,value in new_spent.items()}==expected,'Recorded daily spend was reset/copied/double-counted')
 observed=after['last_fee_observation'];need(h(observed['transaction'])==h(tx['hash'])and uint(observed['cost_wei'])==fees['actual_cost_wei']and uint(observed['execution_price_wei'])==fees['canonical_price_wei']and uint(observed['gas_used'])==fees['gas_used'],'Stock fee observation differs')
 if expect_success:
  events=[event for event in receipt['logs']if addr(event['address'])==CONFIRMATION and event.get('topics')and event['topics'][0].lower()==OBSERVATION_RESET]
  need(len(events)==1 and len(events[0]['topics'])==2 and int(events[0]['topics'][1],16)==BUCKET and events[0]['data'].lower()=='0x'+word(5),'New key did not execute exact onlyKeeper reset')
 else:need(receipt['logs']==[],'Reverted old job retained writes/logs')
 return fees

def verify(vectors,result):
 old=vectors['old'];new=vectors['new'];old_address=addr(old['transaction']['from']);new_address=addr(new['transaction']['from']);need(old_address!=new_address and old_address!=GOVERNANCE and new_address!=GOVERNANCE,'Keys must be distinct nongovernance identities')
 revocation_index=setter(vectors['revocation'],old_address,False);grant_index=setter(vectors['grant'],new_address,True)
 old_index=inclusion(old['transaction'],old['receipt'],old['canonical_header']);need(vectors['revocation']['canonical_header']==old['canonical_header']and revocation_index<old_index,'Revocation was not canonically executed before the old pending job')
 need(q(vectors['revocation']['transaction'].get('type','0x0'))==0 and q(vectors['revocation']['transaction']['gasPrice'])==2000000000,'Reviewed c803 governance legacy2gwei ordering input differs')
 old_fees=settled(old,False);new_fees=settled(new,True);need(h(old['transaction']['hash'])!=h(new['transaction']['hash']),'Replacement reused old transaction hash')
 need(q(vectors['grant']['receipt']['blockNumber'])>=q(old['receipt']['blockNumber'])and q(new['receipt']['blockNumber'])>=q(vectors['grant']['receipt']['blockNumber']),'New authority/work predates revocation completion')
 need(new['state_before']['spent']=={}and new['state_before']['pending']is None and new['state_before']['receipt_anchor']is None,'Replacement journal reused previous cost/pending/anchor state')
 need(old['state_before']['pending']['hash']==old['pending_intent']['hash'],'Old recovery did not start with original saved hash')
 role=vectors['role_getters'];need(role['old']==0 and role['new']==1 and role['old_guardian']==role['new_guardian']==0,'Role-read isolation differs')
 need(vectors['old_journal_after_recovery_sha256']==vectors['old_journal_after_new_work_sha256']and re.fullmatch(r'[0-9a-f]{64}',vectors['old_journal_after_recovery_sha256'])is not None,'Replacement work changed original recovered journal')
 need(result.get('success')is True and result.get('source_inputs_preserved')is True and result.get('raw_submission_attempts')==result.get('reviewed_raw_forward_attempts')==2,'Runtime result has failure/resend or changed source')
 need(result.get('public_transactions')==result.get('new_seals')==result.get('old_test_bodies_run')==0,'Runtime scope differs')
 shared_cost=old_fees['actual_cost_wei']+new_fees['actual_cost_wei'];shared_maximum=old_fees['reviewed_maximum_wei']+new_fees['reviewed_maximum_wei'];need(shared_cost<=shared_maximum<=5*10**16,'Combined old/new reviewed fees exceed shared0.05ETH')
 return {'old_sender':old_address,'new_sender':new_address,'canonical_revocation_index':revocation_index,'old_reverted_index':old_index,'new_grant_index':grant_index,'old_fee':old_fees,'new_fee':new_fees,'combined_actual_cost_wei':shared_cost,'combined_reviewed_maximum_wei':shared_maximum,'old_hash_recovered_after_revocation':True,'new_zero_nonce_separate_journal':True,'old_journal_preserved_after_takeover':True,'source_counters_show_two_raw_attempts_only':True,'new_role_false_before_grant':'executed-source assertion only; not separately stored in raw role_getters'}

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--review',required=True);parser.add_argument('--result',required=True);args=parser.parse_args();v,vi=load(args.review);result,ri=load(args.result);proof=verify(v,result)
 print(json.dumps({'schema':1,'stage':'c803_fixture_consistency','status':'passed','proof':proof,'inputs':{'review':vi,'result':ri},'runtime_actions':0,'old_test_bodies_run':0,'production_source_changes':False,'production_approved':False,'limitations':['Exact prescribed c803 projection required; do not invent missing fields.','A same-block revocation-first status0 proves this controlled ordering, not guaranteed public mempool ordering or cancellation.','Saved projection/source counters bind only this finite local case, not off-host fencing, all lifecycle states or a daemon soak.','Daily budgets remain journal-local; the two-key total is checked separately.','Normal Anvil priority enforcement and2gwei governance are controlled fixture inputs, not actual provider-fee or profile2 approval.','C801 node cause remains unknown; only c802 captured exact-32003 priority-above-max error.','Periphery/LP/accounting/claim workloads are not requalified by a reset-only rotation.']},sort_keys=True,indent=2,allow_nan=False));return 0

if __name__=='__main__':
 try:raise SystemExit(main())
 except(Exception)as exc:
  print(json.dumps({'schema':1,'status':'refused','error_type':type(exc).__name__,'reason':str(exc)[:384],'runtime_actions':0,'production_approved':False},sort_keys=True));raise SystemExit(1)
