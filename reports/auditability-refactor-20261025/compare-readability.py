"""Read-only source-token comparison against archived compiler inputs.

This does not compile or execute Solidity and is not a formal equivalence proof.
It permits only reviewed parameter/local aliases, named numeric constants,
comments/whitespace and formatting block wrappers. Compiler layout and executed
behavior evidence remain separate.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re

EXTERNAL = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9')
ROOT = Path(__file__).resolve().parents[2]
LEX = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_$][A-Za-z0-9_$]*|0x[0-9a-fA-F]+|[0-9]+|[^\s]')
VAULT_ALIASES = {
    '_registerBucket': {'bucketId':'bucket'}, '_reserve': {'bucketId':'bucket'},
    '_tokens': {'bucketId':'id'}, '_requireOwner': {'nftId':'id'}, '_active': {'bucketId':'id'},
    '_idle': {'bucketId':'id'}, '_valueBucket': {'bucketId':'bucket'}, '_put': {'bucketId':'id'},
    '_nav': {'bucketId':'bucket'}, '_join': {'nftId':'id','bucketId':'bucket'},
    '_allocate': {'bucketId':'id'}, '_harvest': {'bucketId':'id'}, '_harvestVenue': {'bucketId':'id'},
    '_pullCompound': {'bucketId':'id'}, '_close': {'bucketId':'id'}, '_balanceUsing': {'bucketId':'id'},
    '_idleValue': {'bucketId':'id'}, '_unwind': {'bucketId':'id'}, '_migrationCheckpoint': {'bucketId':'id'},
    '_redeploy': {'bucketId':'id'}, '_movePool': {'bucketId':'id'}}
MIGRATION_ALIASES = {'plan':'q','requestData':'r','vault':'v','position':'p',
                     'balance0Before':'b0','balance1Before':'b1'}
CANONICAL_CONSTANTS = {**{'PHASE_'+name:str(index) for index,name in enumerate((
    'IDLE','EXPORTING','IMPORTED_AWAITING_BACKING','RETIRED','IMPORTING',
    'ACTIVE_REPLACEMENT','ABORTING','CANCELLED_IMPORT','SETTLING'))},
    **{'STATE_'+name:str(index) for index,name in enumerate(('OPERATING','FROZEN','IMPORTING','RETIRED','CANCELLED'))},
    **{'DOMAIN_'+name:str(index) for index,name in enumerate(('NFT','VAULT','MEMBERSHIP','LP_REWARDS','ROYALTIES','FEES'))}}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def tokens(source):
    return [m.group() for m in LEX.finditer(source) if not m.group().startswith(('//','/*'))]


def boundary(items, start, opening, closing):
    depth=1; index=start+1
    while depth:
        if index>=len(items): raise ValueError('Unbalanced source tokens')
        depth+=(items[index]==opening)-(items[index]==closing);index+=1
    return index


def functions(source):
    items=tokens(source);result={}
    for index,kind in enumerate(items):
        if kind not in ('function','constructor','receive','modifier'):continue
        named=kind in ('function','modifier')
        name=items[index+1] if named else kind
        paren=index+2 if named else index+1
        if items[paren]!='(':continue
        close=boundary(items,paren,'(',')')
        body=close
        while items[body] not in ('{',';'):body+=1
        if items[body]==';':continue
        end=boundary(items,body,'{','}')
        if name in result:raise ValueError('Unexpected overloaded function')
        result[name]={'tokens':items[index:end],'header':items[index:body],
                      'parameters':items[paren+1:close-1]}
    return result


def normalize(items, aliases):
    return [aliases.get(t,t) for t in items if t not in ('{','}')]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-input',type=Path,default=EXTERNAL/'architecture-pruning-20261025/solidity/source-build-input.json')
    p.add_argument('--candidate-input',type=Path,default=EXTERNAL/'auditability-refactor-20261025/solidity/source-build-input.json')
    p.add_argument('--output-name',default='readability-body-comparison')
    a=p.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,80}',a.output_name):raise ValueError('Invalid evidence stem')
    destination=Path(__file__).resolve().parent/(a.output_name+'.json')
    if destination.exists():raise ValueError('Keep prior evidence; choose a fresh stem')
    before=json.loads(a.baseline_input.read_text());after=json.loads(a.candidate_input.read_text())
    rows=[]
    for contract,expected in (('ZZZVault',53),('ZZZMigration',26),('ZZZCanonicalHandoff',25)):
        path='src/'+contract+'.sol';old=before['sources'][path]['content'];new=after['sources'][path]['content']
        first,last=functions(old),functions(new)
        constants={}
        if contract=='ZZZCanonicalHandoff':
            constants=dict(re.findall(r'uint8\s+private\s+constant\s+(\w+)\s*=\s*(\d+)\s*;',new))
            if constants!=CANONICAL_CONSTANTS:raise ValueError('Unexpected canonical constant values')
        methods=[]
        for name,value in first.items():
            other=last.get(name);aliases={}
            if contract=='ZZZVault':
                aliases=VAULT_ALIASES.get(name,{})
                if aliases and 'private' not in other['header']:raise ValueError('Public parameter rename not permitted')
            elif contract=='ZZZMigration':
                aliases=dict(MIGRATION_ALIASES)
                if name=='_receive':aliases.update(token0='t0',token1='t1',amount0='a0',amount1='a1',minimumLiquidity='minimum')
                if name=='_close':aliases.update(planId='id')
            else:aliases=constants
            x=normalize(value['tokens'],{});y=normalize(other['tokens'],aliases) if other else []
            methods.append({'name':name,'equal_after_declared_normalization':x==y,
                'aliases_used':{key:replacement for key,replacement in aliases.items() if other and key in other['tokens']},
                'baseline_normalized_token_sha256':sha(json.dumps(x,separators=(',',':')).encode()),
                'candidate_normalized_token_sha256':sha(json.dumps(y,separators=(',',':')).encode())})
        rows.append({'path':path,'contract':contract,'baseline_function_count':len(first),'candidate_function_count':len(last),
            'expected_count':expected,'same_function_names':set(first)==set(last),
            'exact_current_source_equals_compiled_input':(ROOT/path).read_text(encoding='utf-8-sig')==new,
            'baseline_content_sha256':sha(old.encode()),'candidate_content_sha256':sha(new.encode()),
            'private_constant_values':constants,'function_bodies':methods,
            'all_compared_bodies_equal':len(first)==len(last)==expected and set(first)==set(last) and all(m['equal_after_declared_normalization'] for m in methods)})
    report={'scope':'Read-only token comparisons of already-archived production source inputs; no compiler, Solidity/Python tests, chain, RPC or services run.',
        'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'comparison_script_sha256':sha(Path(__file__).read_bytes()),
        'baseline_input_sha256':sha(a.baseline_input.read_bytes()),'candidate_input_sha256':sha(a.candidate_input.read_bytes()),
        'objects':rows,'all_readability_comparisons_match':all(r['all_compared_bodies_equal'] and r['exact_current_source_equals_compiled_input'] for r in rows),
        'limits':['Explicit identifier aliases and private constant literals are recorded per body; public ABI names are not changed by this normalization.',
            'Comments/whitespace and brace-only formatting wrappers are excluded. Token equality is additional static evidence, not a formal control-flow/equivalence proof.',
            'The earlier intermediate duplicate _join parameter was repaired before compilation. These frozen inputs keep NFT and bucket argument domains distinct.',
            'Compiler wire ABI, recursive storage, executable and normal size comparisons plus changed-path execution evidence are separate.']}
    destination.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'all_readability_comparisons_match':report['all_readability_comparisons_match'],
        'objects':[{k:r[k] for k in ('contract','baseline_function_count','candidate_function_count','all_compared_bodies_equal','exact_current_source_equals_compiled_input')} for r in rows]},indent=2))
    return 0 if report['all_readability_comparisons_match'] else 1


if __name__=='__main__':raise SystemExit(main())
