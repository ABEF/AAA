"""Source-bound F6 construction campaign on two new PID-owned local nodes.

Reuses the maintained constructor runner unchanged. No RPC/key/signing/nonce
input, seal call, operating configuration, existing node or public endpoint.
The second small fixture separates bootstrap from governance; its calls only
simulate permissions and are recorded separately from success-only main wire.
"""
from __future__ import annotations
import argparse,gzip,hashlib,http.client,importlib.util,json,re,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('f6_existing_construction',ROOT/'scripts/rehearse-local-deployment.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
GOV='0x000000000000000000000000000000000000a0a3'
OUTSIDER='0x000000000000000000000000000000000000a0a4'
BUILD='activation-final-six-20261118'
ANVIL_SHA='d438383b871c726407ecc5829279bea44ceac63a712be9e010813ca0a15434b6'
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def resolve(value,roles):return roles[value[1:]] if isinstance(value,str) and value.startswith('@') else value
def encode(types,values):
    require(len(types)==len(values),'Static ABI arity differs');parts=[]
    for typ,value in zip(types,values):
        if typ=='address':
            require(type(value)is str and re.fullmatch('0x[0-9a-f]{40}',value)is not None,'Static address differs');raw=bytes.fromhex(value[2:]).rjust(32,b'\0')
        elif typ=='bool':
            require(type(value)is bool,'Static boolean differs');raw=int(value).to_bytes(32,'big')
        elif typ=='bytes32':
            require(type(value)is str and re.fullmatch('0x[0-9a-f]{64}',value)is not None,'Static hash differs');raw=bytes.fromhex(value[2:])
        else:
            require(re.fullmatch(r'uint(?:8|16|32|64|128|256)',typ)is not None,'Unsupported static type')
            number=int(value);require(type(value)is not bool and 0<=number<1<<int(typ[4:]),'Static unsigned amount differs');raw=number.to_bytes(32,'big')
        parts.append(raw)
    return b''.join(parts)
def calldata(signature,types,values):return '0x'+(M.keccak256(signature.encode())[:4]+encode(types,values)).hex()
def before_sources(artifacts):
    paths=['scripts/rehearse-local-deployment.py','zzz_ops/deployment_plan.py','zzz_ops/abi.py']
    return {p:sha(ROOT/p)for p in paths}
def save_stage(out,artifacts,pins,dependencies,kind):
    M.save(out/'dependencies.json',dependencies)
    M.save(out/'source-stage.json',{'tool_sources_sha256':pins,'request_capture':'immutable_serialized_request_and_response_snapshot','accepted_build_profile':artifacts.profile,'accepted_build_files_sha256':artifacts.file_pins,'source_sha256':artifacts.source_pins,'campaign':kind,'campaign_source_sha256':sha(__file__)})
def rolemap(case,distinct=False):
    return {'bootstrap':M.SENDER,'governance':GOV if distinct else M.SENDER,'keeper':M.KEEPER,'guardian':M.GUARDIAN,'payee':M.PAYEE,'outsider':OUTSIDER,**case.addresses}
def abi_check(artifacts,contract,signature,types):
    candidates=[x for x in artifacts.contract(contract)[1]['abi']if x.get('type')=='function'and x['name']==signature.split('(',1)[0]and tuple(v['type']for v in x['inputs'])==tuple(types)]
    require(len(candidates)==1 and signature==candidates[0]['name']+'('+','.join(types)+')','Probe differs from current ABI')
    require(signature!='seal()','No seal call permitted')
def headers(node,receipts):
    nums=sorted({int(row['receipt']['blockNumber'],16)for row in receipts})
    require(nums==list(range(1,len(receipts)+1)),'Expected isolated automined receipt sequence')
    rows=[node.wire('eth_getBlockByNumber',[hex(n),False])for n in nums]
    head=node.wire('eth_getBlockByNumber',['latest',False])
    require(head['hash']==rows[-1]['hash'],'Unexpected transaction after closed construction')
    return {'schema':1,'chain_id':M.CHAIN,'genesis_hash':node.anchor,'headers':rows,'closing_head':head}

def full_graph(binary,out,artifacts,pins):
    out.mkdir(exist_ok=False);initial,dependencies=M.genesis();save_stage(out,artifacts,pins,dependencies,'unchanged_full_graph')
    with M.Node(binary,out/'node',initial)as node:
        case=M.Rehearsal(node,artifacts,out);result=case.run()
        addresses={x['role']:x['address']for x in load(out/'instances.json')}
        manifest=load(HERE/'DEFAULT_READS.json');reads=[]
        rows=manifest['cases'];require(1<=len(rows)<=200,'Bounded default read list required')
        node.guard();head=node.wire('eth_getBlockByNumber',['latest',False]);tag=head['number']
        for row in rows:
            role=row['role'];target=addresses[role];types=row.get('types',[]);values=[resolve(v,addresses)for v in row.get('values',[])]
            signature=row['signature'];contract=next(x['contract']for x in load(out/'instances.json')if x['role']==role)
            abi_check(artifacts,contract,signature,types)
            payload=calldata(signature,types,values)
            response=node.wire('eth_call',[{'to':target,'data':payload},tag])
            wanted=row.get('expected_return')
            if wanted is None:wanted='0x'+encode(row['expected_types'],row['expected_values']).hex()
            require(response.lower()==wanted.lower(),'Unexpected default: '+row['id'])
            reads.append({'id':row['id'],'role':role,'target':target,'signature':signature,'types':types,'values':values,'calldata':payload,'block':tag,'actual':response,'expected':wanted})
        require(node.wire('eth_getBlockByNumber',['latest',False])['hash']==head['hash'],'Read-only defaults changed chain')
        M.save(out/'DEFAULT_OBSERVATIONS.json',{'schema':1,'manifest_sha256':sha(HERE/'DEFAULT_READS.json'),'block_hash':head['hash'],'observations':reads,'production_ready':False})
        M.save(out/'MAIN_HEADERS.json',headers(node,case.receipts))
        artifacts.check_sources();require(before_sources(artifacts)==pins,'Maintained source changed during execution')
        M.save(out/'SOURCE_UNCHANGED.json',pins);M.save(out/'RESULT.json',result)
    return result

def state(case,tag):
    roles=rolemap(case,True);a=case.addresses;rows={}
    for row in load(HERE/'AUTHORITY_CASES.json')['state_checks']:
        role=row['target_role'];values=[resolve(v,roles)for v in row['values']]
        contract='ZZZAccessController'if role=='access'else'ZZZProtocolPolicy'
        abi_check(case.artifacts,contract,row['signature'],row['types'])
        actual=case.node.wire('eth_call',[{'to':a[role],'data':calldata(row['signature'],row['types'],values)},tag])
        if row.get('require_nonzero'):
            require(len(actual)==66 and int(actual,16)!=0,'Nonzero authority state expected: '+row['id'])
        else:
            expected='0x'+encode(row['return_types'],[resolve(v,roles)for v in row['return_values']]).hex()
            require(actual==expected,'Authority initial/final state differs: '+row['id'])
        rows[row['id']]=actual
    return rows

def control_fixture(binary,out,artifacts,pins):
    out.mkdir(exist_ok=False);initial,dependencies=M.genesis();save_stage(out,artifacts,pins,dependencies,'distinct_roles_three_transaction_fixture')
    with M.Node(binary,out/'node',initial)as node:
        case=M.Rehearsal(node,artifacts,out)
        case.inputs={'governance':GOV,'keeper':M.KEEPER,'guardian':M.GUARDIAN,'mint_recipient':M.PAYEE}
        for role,name,refs in M.P.TOP[:2]:
            require(role in ('access','protocol_policy'),'Control fixture graph differs')
            obj=artifacts.contract(name)[1];payload='0x'+obj['evm']['bytecode']['object']+M.P.encode_constructor(M.P.TYPES[name],case.arguments(refs)).hex()
            case.addresses[role]=case.transaction('create:'+role,payload)
            if role=='access':case.factory_addresses=[case.getter(case.addresses['access'],x)for x in ('royaltyFactory()','activationAssetsFactory()')]
        case.transaction('bind:protocol_policy',M.data('bindProtocolPolicy(address)',('address',),(case.addresses['protocol_policy'],)),case.addresses['access'])
        require(len(case.receipts)==3,'Only three local control-fixture transactions')
        roles=rolemap(case,True);manifest=load(HERE/'AUTHORITY_CASES.json');require(1<=len(manifest['cases'])<=60,'Bounded permission cases required')
        head=node.wire('eth_getBlockByNumber',['latest',False]);tag=head['number'];before=state(case,tag);nonces=case.nonces();records=[];results=[]
        connection=http.client.HTTPConnection('127.0.0.1',node.port,timeout=10)
        try:
            for row in manifest['cases']:
                node.guard();from_=roles[row['from_role']];target=case.addresses[row['target_role']];types=row.get('types',[]);values=[resolve(v,roles)for v in row.get('values',[])]
                contract='ZZZAccessController'if row['target_role']=='access'else'ZZZProtocolPolicy'
                abi_check(artifacts,contract,row['signature'],types)
                require(row['signature'].split('(',1)[0]in ('setKeeper','setGuardian','setPaused','proposeGovernance','acceptGovernance','setRoyaltyBalanceGas'),'Closed authority selector list')
                tx={'from':from_,'to':target,'value':'0x0','gas':'0x1e8480','gasPrice':'0x0','data':calldata(row['signature'],types,values)}
                request={'jsonrpc':'2.0','id':len(records)+1,'method':'eth_call','params':[tx,tag]};raw_request=json.dumps(request,sort_keys=True,separators=(',',':')).encode('ascii')
                connection.request('POST','/',raw_request,{'Content-Type':'application/json'});reply=connection.getresponse();raw=reply.read(16385)
                require(reply.status==200 and len(raw)<=16384,'Unbounded/failed permission reply');response=json.loads(raw)
                require(response.get('jsonrpc')=='2.0'and type(response.get('id'))is int and response['id']==request['id'],'Permission response identity differs')
                record={'case_id':row['id'],'request':json.loads(raw_request),'response':response,'http_status':reply.status,'response_sha256':hashlib.sha256(raw).hexdigest(),'response_raw_hex':raw.hex(),'request_sha256':hashlib.sha256(raw_request).hexdigest()};records.append(record)
                if 'expected_error'in row:
                    error=response.get('error');require(row['expected_error']=='0x82b42900','Only exact Unauthorized review')
                    require('result'not in response and type(error)is dict and type(error.get('code'))is int and error['code']==3 and error.get('data')==row['expected_error'],'Expected exact Unauthorized revert: '+row['id'])
                else:require('error'not in response and response.get('result')==row['expected_return'],'Unexpected authority success result: '+row['id'])
                require(state(case,tag)==before and case.nonces()==nonces,'Permission simulation mutated state/nonces')
                require(node.wire('eth_getBlockByNumber',['latest',False])['hash']==head['hash'],'Permission simulation mined/changed chain')
                results.append({'id':row['id'],'expected_error':row.get('expected_error'),'expected_return':row.get('expected_return'),'state_unchanged':True,'nonce_unchanged':True})
        finally:
            connection.close();M.save(out/'AUTHORITY_WIRE.json',records)
        for proof in case.creates.values():require(len(bytes.fromhex(proof['input'][2:]))<=49152 and len(bytes.fromhex(proof['output'][2:]))<=24576,'Control fixture normal size bound')
        M.save(out/'CONTROL_HEADERS.json',headers(node,case.receipts));M.save(out/'INITIAL_FINAL_STATE.json',{'schema':1,'roles':roles,'block':tag,'block_hash':head['hash'],'state_before':before,'state_after':state(case,tag),'nonces_before':nonces,'nonces_after':case.nonces()})
        M.save(out/'CREATE_PROOFS.json',case.creates);M.save(out/'SOURCE_UNCHANGED.json',pins)
        summary={'schema':1,'status':'distinct_unsealed_authority_fixture_passed','build_profile':BUILD,'receipts':3,'instances':len(case.creates),'cases':len(results),'manifest_sha256':sha(HERE/'AUTHORITY_CASES.json'),'role_addresses':roles,'results':results,'sealed':False,'production_ready':False,'public_transactions':0,'zero_value_only':True}
        M.save(out/'RESULT.json',summary);artifacts.check_sources()
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--anvil',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(args.anvil.is_file()and sha(args.anvil)==ANVIL_SHA,'Reviewed Anvil executable differs')
    require(not args.output.exists(),'Exclusive new campaign directory required')
    for name in ('DEFAULT_READS.json','AUTHORITY_CASES.json'):require((HERE/name).is_file(),'Reviewed cases missing')
    artifacts=M.P.Artifacts(build_profile=BUILD);pins=before_sources(artifacts)
    campaign_pins={name:sha(HERE/name)for name in ('run_campaign.py','DEFAULT_READS.json','AUTHORITY_CASES.json')}
    names={row[0]:row[1]for row in M.P.TOP}
    names.update({row[0]:row[1]for row in M.P.INTERNAL})
    for row in load(HERE/'DEFAULT_READS.json')['cases']:abi_check(artifacts,names[row['role']],row['signature'],row['types'])
    authority=load(HERE/'AUTHORITY_CASES.json');require(authority['roles']=={'bootstrap':M.SENDER,'governance':GOV,'keeper':M.KEEPER,'guardian':M.GUARDIAN,'payee':M.PAYEE,'outsider':OUTSIDER},'Reviewed disposable roles differ')
    for row in authority['cases']+authority['state_checks']:abi_check(artifacts,'ZZZAccessController'if row['target_role']=='access'else'ZZZProtocolPolicy',row['signature'],row['types'])
    args.output.mkdir(parents=True,exist_ok=False)
    try:
        full=full_graph(args.anvil,args.output/'full-graph',artifacts,pins)
        control=control_fixture(args.anvil,args.output/'control-fixture',artifacts,pins)
        require(before_sources(artifacts)==pins,'Maintained source changed')
        require({name:sha(HERE/name)for name in campaign_pins}==campaign_pins,'Campaign/cases changed during execution')
        M.save(args.output/'CAMPAIGN.json',{'schema':1,'source_baseline':'2891f6b29691449d6667d36b9c678a0746ce5d80','build_profile':BUILD,'full':full,'control':control,'campaign_source_sha256':sha(__file__),'production_ready':False,'sealing_attempted':False,'existing_nodes_contacted':False})
        print(json.dumps({'status':'completed','full_receipts':44,'full_instances':39,'control_receipts':3,'authority_cases':control['cases'],'production_ready':False}));return 0
    except Exception as exc:
        M.save(args.output/'FAILED.json',{'failure_type':type(exc).__name__,'reason':str(exc)if type(exc)is ValueError else 'Unexpected error; retain full bounded evidence','production_ready':False,'sealing_attempted':False});raise
if __name__=='__main__':raise SystemExit(main())
