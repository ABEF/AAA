"""Virtual normal-settings codegen probe; never edits production source files."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True,type=Path);p.add_argument('--stage',required=True)
    p.add_argument('--unchecked-preview',action='store_true');p.add_argument('--omit-view-total-check',action='store_true')
    p.add_argument('--fold-credit',action='store_true')
    p.add_argument('--addmod-cursor',action='store_true');p.add_argument('--bounded-host-cursor',action='store_true')
    p.add_argument('--omit-take-total-check',action='store_true');p.add_argument('--bounded-open-at',action='store_true')
    p.add_argument('--reuse-opening-read',action='store_true')
    p.add_argument('--trim-weight-zero',action='store_true');p.add_argument('--unconditional-leaf-delete',action='store_true')
    a=p.parse_args();stage=a.evidence/a.stage;stage.mkdir(parents=True,exist_ok=False)
    v=a.evidence.parents[1];normal=v/'test-seal-deep-review-20261117/normal-final-2'
    template=normal/'compiler-input.json';old_output=normal/'compiler-output.json';solc=v/'toolchain-0.8.26/solc.exe'
    data=json.loads(template.read_text(encoding='utf-8-sig'))
    paths=list((ROOT/'src').rglob('*.sol'))+[ROOT/'test/fixtures/Q03ComplementAllocation.sol']
    before={x.relative_to(ROOT).as_posix():sha(x)for x in paths}
    for path in paths:
        name=path.relative_to(ROOT).as_posix()
        if name.startswith('src/'):data['sources'][name]={'content':path.read_text(encoding='utf-8-sig')}
    library=(ROOT/'src/libraries/ExactRoyaltyAllocation.sol').read_text()
    candidate=(ROOT/'test/fixtures/Q03ComplementAllocation.sol').read_text()
    candidate=candidate.replace('library Q03ComplementAllocation','library ExactRoyaltyAllocation')
    candidate=candidate[:candidate.index('    function _validate(')]+library[library.index('    /// @notice Preview a pending allocation'):]
    # Reuse the existing error in this SIZE-ONLY variant to avoid a new ABI selector.
    candidate=candidate.replace('    error InvalidOutstanding();\n','').replace('revert InvalidOutstanding()','revert InvalidAllocation()')
    if a.fold_credit:
        start=candidate.index('        unchecked {\n            uint256 quotient')
        end=candidate.index('\n    }\n\n    function addRange',start)
        folded='''        unchecked {
            uint256 quotient=amount/weight;
            uint256 remainder=amount%weight;
            nextCursor=cursor+remainder;
            if(nextCursor>=weight) nextCursor-=weight;
            uint256 delta=1;
            if(remainder>weight/2) {
                ++quotient;
                remainder=weight-remainder;
                cursor=nextCursor;
                delta=type(uint256).max;
            }
            if(quotient!=0) _add(book,1,weight,quotient);
            uint256 first=remainder<weight-cursor?remainder:weight-cursor;
            if(first!=0) _add(book,cursor+1,cursor+first,delta);
            uint256 wrapped=remainder-first;
            if(wrapped!=0) _add(book,1,wrapped,delta);
        }'''
        candidate=candidate[:start]+folded+candidate[end:]
    if a.addmod_cursor:
        candidate=candidate.replace('            nextCursor=cursor+remainder;\n            if(nextCursor>=weight) nextCursor-=weight;',
            '            nextCursor=addmod(cursor,remainder,weight);')
    if a.unchecked_preview:
        start=candidate.index('        uint256 count = _overlap(')
        end=candidate.index('\n    }\n\n    function _overlap',start)
        candidate=candidate[:start]+'        unchecked {\n'+candidate[start:end]+'\n        }'+candidate[end:]
        candidate=candidate.replace('        return end-start+1;','        unchecked { return end-start+1; }')
    if a.omit_view_total_check:
        candidate=candidate.replace('        if(amount > book.outstanding) revert InvalidAllocation();','',1)
    if a.omit_take_total_check:
        start=candidate.index('    function takeTicket(')
        candidate=candidate[:start]+candidate[start:].replace('        if(amount > book.outstanding) revert InvalidAllocation();','',1)
    if a.trim_weight_zero:
        candidate=candidate.replace('weight == 0 || weight > MAX_TICKETS || cursor >= weight',
            'weight > MAX_TICKETS || cursor >= weight')
    if a.unconditional_leaf_delete:
        old_lines='            uint256 leaf = book.pending[node];\n            amount = leaf + carry;\n            if(leaf != 0) delete book.pending[node];'
        if old_lines not in candidate:raise ValueError('Expected final leaf block absent')
        candidate=candidate.replace(old_lines,'            amount = book.pending[node] + carry;\n            delete book.pending[node];')
    data['sources']['src/libraries/ExactRoyaltyAllocation.sol']={'content':candidate}
    if a.bounded_host_cursor:
        host=data['sources']['src/ZZZRoyaltyRewards.sol']['content']
        old_line='        uint256 afterCursor = allocationBooks[asset][unit].credit(amount,weight/unit,beforeCursor/unit)*unit;'
        new_line='        uint256 units = allocationBooks[asset][unit].credit(amount,weight/unit,beforeCursor/unit);\n        uint256 afterCursor;\n        unchecked { afterCursor = units*unit; }'
        if old_line not in host:raise ValueError('Expected cursor multiplication source absent')
        data['sources']['src/ZZZRoyaltyRewards.sol']['content']=host.replace(old_line,new_line)
    if a.bounded_open_at:
        host=data['sources']['src/ZZZRoyaltyRewards.sol']['content']
        old_line='        return mintEnd == 0 ? 0 : uint256(mintEnd) + ACTIVATION_WINDOW;'
        new_line='        unchecked { return mintEnd == 0 ? 0 : uint256(mintEnd) + ACTIVATION_WINDOW; }'
        if old_line not in host:raise ValueError('Expected uint64 opening calculation absent')
        data['sources']['src/ZZZRoyaltyRewards.sol']['content']=host.replace(old_line,new_line)
    if a.reuse_opening_read:
        host=data['sources']['src/ZZZRoyaltyRewards.sol']['content']
        old_line='        emit MintEndConfigured(end, uint256(end) + ACTIVATION_WINDOW);'
        if old_line not in host:raise ValueError('Expected opening event calculation absent')
        data['sources']['src/ZZZRoyaltyRewards.sol']['content']=host.replace(old_line,'        emit MintEndConfigured(end, royaltiesOpenAt());')
    selected={
        'src/ZZZRoyaltyRewards.sol':'ZZZRoyaltyRewards',
        'src/ZZZRoyaltyFactory.sol':'ZZZRoyaltyFactory',
        'src/ZZZNFT.sol':'ZZZNFT',
        'src/ZZZAccessController.sol':'ZZZAccessController',
    }
    fields=['evm.bytecode.object','evm.deployedBytecode.object','abi','storageLayout']
    data['settings']['outputSelection']={name:{contract:fields}for name,contract in selected.items()}
    input_path=stage/'compiler-input.json';input_path.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
    start={'template_sha256':sha(template),'baseline_output_sha256':sha(old_output),'solc_sha256':sha(solc),
        'virtual_input_sha256':sha(input_path),'current_source_sha256':before,
        'variants':{'unchecked_preview':a.unchecked_preview,'omit_view_total_check':a.omit_view_total_check,'fold_credit':a.fold_credit,
            'addmod_cursor':a.addmod_cursor,'bounded_host_cursor':a.bounded_host_cursor,
            'omit_take_total_check':a.omit_take_total_check,'bounded_open_at':a.bounded_open_at,'reuse_opening_read':a.reuse_opening_read,
            'trim_weight_zero':a.trim_weight_zero,'unconditional_leaf_delete':a.unconditional_leaf_delete},
        'settings_except_output_selection':{k:v for k,v in data['settings'].items()if k!='outputSelection'},
        'scope':'four selected normal-settings sizes with virtual library override; not full normal gates, not tested production bytecode'}
    (stage/'START.json').write_text(json.dumps(start,indent=2)+'\n')
    allow={'SYSTEMROOT','WINDIR','PATH','PATHEXT','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','COMSPEC'}
    env={k:v for k,v in os.environ.items()if k.upper()in allow};t=time.monotonic()
    with input_path.open('rb')as source,(stage/'compiler-output.json').open('wb')as output,(stage/'stderr.log').open('wb')as error:
        r=subprocess.run([str(solc),'--standard-json'],stdin=source,stdout=output,stderr=error,env=env,check=False)
    out=json.loads((stage/'compiler-output.json').read_text(encoding='utf-8-sig'));base=json.loads(old_output.read_text(encoding='utf-8-sig'))
    errors=[x for x in out.get('errors',[])if x['severity']=='error'];sizes=[]
    if not errors:
        for name,contract in selected.items():
            code=out['contracts'][name][contract];prior=base['contracts'][name][contract]
            runtime=len(code['evm']['deployedBytecode']['object'])//2;creation=len(code['evm']['bytecode']['object'])//2
            sizes.append({'contract':contract,'runtime':runtime,'creation':creation,
                'runtime_headroom':24576-runtime,'creation_headroom_before_constructor_arguments':49152-creation,
                'baseline_runtime':len(prior['evm']['deployedBytecode']['object'])//2,
                'baseline_creation':len(prior['evm']['bytecode']['object'])//2,'abi_identical':code['abi']==prior['abi']})
    after={n:sha(ROOT/n)for n in before}
    result={'returncode':r.returncode,'elapsed_seconds':time.monotonic()-t,'compiler_errors':errors,'sizes':sizes,
        'production_and_experimental_files_unchanged':before==after,'source_after_sha256':after,
        'output_sha256':sha(stage/'compiler-output.json'),
        'fit_selected_bytecode_only':not errors and all(x['runtime_headroom']>=0 and x['creation_headroom_before_constructor_arguments']>=0 for x in sizes)}
    (stage/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='source_after_sha256'}))
    return 0 if not errors and before==after else 1
if __name__=='__main__':raise SystemExit(main())
