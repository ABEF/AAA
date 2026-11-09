from pathlib import Path
import hashlib,json,sys
E=Path(__file__).resolve().parent
OLD=E.parents[1]/'opensea-integration-20261109-1579186/normal-final-05f7ac32db'
NEW=E/'normal-final-a864bb33d5'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def strip_cbor(v):
    raw=bytes.fromhex(v)
    if not raw:return raw
    length=int.from_bytes(raw[-2:],'big')
    metadata=raw[-2-length:-2]
    # Exact normal0.8.26 IPFS+solc CBOR trailer; no code/pushdata/middle metadata normalization.
    if length!=51 or metadata[:9]!=bytes.fromhex('a26469706673582212') or metadata[9]!=0x20 or metadata[-11:]!=bytes.fromhex('64736f6c634300081a'):
        raise ValueError('unexpected CBOR metadata trailer')
    return raw[:-2-length]
def differences(a,b,path=''):
    if type(a)!=type(b):return [(path,a,b)]
    if isinstance(a,dict):
        if a.keys()!=b.keys():return [(path+'.keys',list(a),list(b))]
        result=[]
        for k in a:result+=differences(a[k],b[k],path+'.'+k)
        return result
    if isinstance(a,list):
        if len(a)!=len(b):return [(path+'.length',len(a),len(b))]
        result=[]
        for i,(x,y) in enumerate(zip(a,b)):result+=differences(x,y,path+'['+str(i)+']')
        return result
    return [] if a==b else [(path,a,b)]
ai,bi=load(OLD/'compiler-input.json'),load(NEW/'compiler-input.json')
ao,bo=load(OLD/'compiler-output.json'),load(NEW/'compiler-output.json')
ag,bg=load(OLD/'production-size-gates.json'),load(NEW/'production-size-gates.json')
assert ag['all_pass'] and bg['all_pass'] and ai['settings']==bi['settings']
assert set(ai['sources'])==set(bi['sources']) and len(bi['sources'])==90
changed=[p for p in ai['sources'] if ai['sources'][p]!=bi['sources'][p]]
assert changed==['src/ZZZMigrationBudget.sol'],changed
before=ai['sources'][changed[0]]['content'];after=bi['sources'][changed[0]]['content']
assert before.replace('uint16 public contributionLossBps = 200;','uint16 public contributionLossBps = 300;',1)==after
ast=[]
for p in ao['sources']:ast+=differences(ao['sources'][p]['ast'],bo['sources'][p]['ast'],p)
# Inspect the literal subtree exactly; all other AST bytes/IDs/source spans stay equal.
def find_decl(node):
    if isinstance(node,dict):
        if node.get('nodeType')=='VariableDeclaration' and node.get('name')=='contributionLossBps' and node.get('stateVariable'):return node
        for value in node.values():
            found=find_decl(value)
            if found:return found
    if isinstance(node,list):
        for value in node:
            found=find_decl(value)
            if found:return found
    return None
olddecl=find_decl(ao['sources'][changed[0]]['ast']);newdecl=find_decl(bo['sources'][changed[0]]['ast'])
assert olddecl and newdecl and olddecl['id']==newdecl['id']
newliteral=newdecl['value'];oldliteral=olddecl['value']
assert oldliteral['value']=='200' and newliteral['value']=='300'
saved=newdecl['value'];newdecl['value']=olddecl['value']
assert all(ao['sources'][p]['ast']==bo['sources'][p]['ast'] for p in ao['sources'])
newdecl['value']=saved
abi_diffs=[];storage_diffs=[];runtime_rows=[];creation_rows=[]
for p,contracts in ao['contracts'].items():
    assert set(contracts)==set(bo['contracts'][p])
    for n,old in contracts.items():
        new=bo['contracts'][p][n];label=p+':'+n
        if old['abi']!=new['abi']:abi_diffs.append(label)
        if old['storageLayout']!=new['storageLayout']:storage_diffs.append(label)
        for key,rows in [('deployedBytecode',runtime_rows),('bytecode',creation_rows)]:
            oldhex=old['evm'][key]['object'];newhex=new['evm'][key]['object']
            if not oldhex and not newhex:continue
            abody=strip_cbor(oldhex);bbody=strip_cbor(newhex)
            rows.append({'contract':label,'raw_equal':oldhex==newhex,'body_equal_after_only_exact_C​​BOR_tail_removal':abody==bbody,'old_bytes':len(oldhex)//2,'new_bytes':len(newhex)//2,'old_raw_sha256':sha(bytes.fromhex(oldhex)),'new_raw_sha256':sha(bytes.fromhex(newhex)),'old_body_sha256':sha(abody),'new_body_sha256':sha(bbody)})
assert not abi_diffs and not storage_diffs
assert all(x['body_equal_after_only_exact_C​​BOR_tail_removal'] for x in runtime_rows)
creation_changes=[x for x in creation_rows if not x['body_equal_after_only_exact_C​​BOR_tail_removal']]
assert [x['contract'] for x in creation_changes]==['src/ZZZMigrationBudget.sol:ZZZMigrationBudget'],creation_changes
assert ag['royalty_creation_code_hash']==bg['royalty_creation_code_hash'] and ag['factory_data_gates']==bg['factory_data_gates']
for x,y in zip(ag['gates'],bg['gates']):assert all(x[k]==y[k] for k in ['name','runtime','creation','minimum_args','runtime_margin','static_argument_bytes','constructor_types','maximum_total_argument_bytes'])
record={'scope':'Authorized constructor default change only: contribution200bps to300bps. Not behavior-preserving economics and not old-runtime upgrade.',
 'old_normal':str(OLD),'new_normal':str(NEW),'normal_settings_equal':True,'closed_source_count':90,'only_changed_source':changed,
 'only_source_literal_change':True,'full_AST_difference_fields':ast,'all_AST_other_than_this_initializer_literal_equal':True,'initializer_before':oldliteral,'initializer_after':newliteral,
 'ABI_differences':abi_diffs,'storage_layout_differences':storage_diffs,'runtime_objects':runtime_rows,'creation_objects':creation_rows,
 'only_creation_executable_change':['src/ZZZMigrationBudget.sol:ZZZMigrationBudget'],
 'all_normal_object_size_bounds_equal':True,'royalty_creation_code_hash_unchanged':ag['royalty_creation_code_hash'],
 'both_Factory_data_runtime_and_exact_initcode_gates_identical':True,
 'metadata_rule':'Strip only exact final51-byte normal0.8.26 IPFS/solc CBOR map plus its2-byte length. No inner metadata stripping, arbitrary byte normalization, instruction reordering or comparison-rule change.',
 'limitations':['New deployment initial contribution policy changes to3%; governance setters and captured caller/venue/idle/oracle/maintenance/conversion limits retain code and ABI.','Raw metadata/runtime hashes can change and must be pinned as new identities.','No deployment, proxy upgrade, live setting update, source test rerun, target-gas or production approval is implied.']}
with (E/'CONSTRUCTOR_DEFAULT_EQUIVALENCE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'sources':90,'runtime_objects':len(runtime_rows),'runtime_bodies_equal':True,'AST_diff_fields':len(ast),'ABI_diffs':abi_diffs,'storage_diffs':storage_diffs,'only_creation_body_change':creation_changes[0]['contract'],'Factory_payload_and_data_gates_equal':True}))
