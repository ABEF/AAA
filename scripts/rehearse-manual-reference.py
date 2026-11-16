"""Current same-reference manual qualification on a NEW owned local chain only.

This narrow wrapper preserves the pinned recovery launcher's PID/loopback,
transport, budgets, actual production CLI, wall clock and once-only submission.
It accepts only the three reviewed guarded reference-swap fixture cases.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
BASE_SHA256='fabaf02efa8654efa3d3e4c606749d2632a20b09af1a2eb12e7553583119851e'
ROOT=Path(__file__).resolve().parents[1]
base=Path(__file__).with_name('rehearse-manual-recovery.py')
if hashlib.sha256(base.read_bytes()).hexdigest()!=BASE_SHA256:raise ValueError('Reviewed base launcher source differs')
spec=importlib.util.spec_from_file_location('manual_recovery_base',base);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
CHANGED=('ZZZContributionPricing','ZZZMigrationBudget','ZZZCustodyValidation','ZZZLiquidityManager','ZZZLPBalanceMath','ZZZLPBalancer')
ALLOWED={'active-c14':('C',1),'active-d14':('D',1),'parked-d14':('D',2)}
def walk(frame):
 yield frame
 for child in frame.get('calls',[]):yield from walk(child)
def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('exports','host-artifact','anvil','python','output'):parser.add_argument('--'+name,required=True,type=Path)
 parser.add_argument('--case',required=True,choices=tuple(ALLOWED));parser.add_argument('--new-review-deadline-seconds',type=int)
 args=parser.parse_args(argv);b.require(not args.output.exists(),'Evidence output must be new')
 artifact=json.loads(args.host_artifact.read_bytes());metadata=artifact['metadata'];metadata=json.loads(metadata) if isinstance(metadata,str) else metadata
 pins={name:hashlib.sha256((ROOT/'src'/(name+'.sol')).read_bytes()).hexdigest() for name in CHANGED}
 for name in CHANGED:
  source='src/'+name+'.sol';b.require(metadata['sources'][source]['keccak256']=='0x'+b.keccak256((ROOT/source).read_bytes().replace(b'\r\n',b'\n')).hex(),'Compiled current source profile differs')
 cases=b.parse_export(args.exports,args.host_artifact);case=next((row for row in cases if row['label']==args.case),None)
 b.require(case is not None and case['reference_rejection'] is None,'Current fixture must not contain the retired expected-rejection behavior')
 selected=case['selection'];expected_action,expected_schema=ALLOWED[args.case]
 b.require(selected['action']==expected_action and selected['schema']==expected_schema and selected['checks']=='14','Only explicit current guarded14 cases are admitted')
 b.require(int(selected['amountIn'])>0 and int(selected['minimumOut'])>0 and int(selected['minimumLiquidity'])>1,'Meaningful original swap and LP floors are required')
 token=case['asset']['address'];key=[0,int(token,16),500,10,0]
 reference='0x'+b.keccak256(bytes.fromhex(''.join(f'{word:064x}' for word in key))).hex()
 b.require(selected['swapPool']==reference and case['reference_quote']['swap_and_lp_floors_feasible'],'Fixture must select its actual reviewed reference venue with feasible original floors')
 command=[]
 for name in ('exports','host_artifact','anvil','python','output'):command+=['--'+name.replace('_','-'),str(getattr(args,name))]
 command+=['--case',args.case]
 if args.new_review_deadline_seconds is not None:command+=['--new-review-deadline-seconds',str(args.new_review_deadline_seconds)]
 # No production Reader/CLI/clock/signing behavior is patched by this wrapper.
 code=b.main(command);b.require(code==0,'The unchanged actual preparation/execution failed')
 folder=args.output/args.case/'manual';review=json.loads((folder/'review.json').read_bytes());trace=json.loads((folder/'receipt-trace.json').read_bytes())
 frames=list(walk(trace));bindings=case['bindings'];values=review['arguments']
 quote_selector='0x'+b.keccak256(b'quoteSwap(bytes32,bool,uint256)').hex()[:8]
 quotes=[frame for frame in frames if frame.get('to')==bindings['balancing_router']['address'] and frame.get('input','').startswith(quote_selector) and not frame.get('error')]
 b.require(len(quotes)==1,'Included transaction must obtain exactly one explicit actual-core quote')
 quote=quotes[0];inputs=b.decode_words('0x'+quote['input'][10:]);output=b.decode_words(quote['output'])
 b.require(len(inputs)==3 and len(output)==6 and int(inputs[0],16)==int(reference,16) and bool(int(inputs[1],16))==values['zeroForOne'] and int(inputs[2],16)==int(values['amountIn']),'Quote changed selected pool/direction/amount')
 swap_selector='0x'+b.keccak256(b'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)').hex()[:8]
 swaps=[frame for frame in frames if frame.get('from')==bindings['liquidity']['address'] and frame.get('to')==bindings['pool_manager']['address'] and frame.get('input','').startswith(swap_selector) and not frame.get('error')]
 b.require(len(swaps)==1,'Actual Manager must execute exactly one selected reference swap')
 swap=swaps[0];data=b.decode_words('0x'+swap['input'][10:]);b.require([int(word,16) for word in data[:5]]==key,'Actual core swap used another venue')
 delta=int(b.decode_words(swap['output'])[0],16);raw0=(delta>>128)&((1<<128)-1);raw1=delta&((1<<128)-1)
 signed=lambda value:value-(1<<128) if value>=1<<127 else value
 spent,received=(signed(raw0),signed(raw1)) if values['zeroForOne'] else (signed(raw1),signed(raw0))
 b.require(-spent==int(values['amountIn']) and received==int(output[0],16) and received>=int(values['minimumOut']),'Actual exact output differs from the proven quote or original floor')
 before_selector='0x'+b.keccak256(b'beforeSwap(address,address,bytes32,(uint160,int24,uint24,uint24,uint128))').hex()[:8]
 armed=[frame for frame in frames if frame.get('to')==bindings['oracle']['address'] and frame.get('input','').startswith(before_selector) and not frame.get('error')]
 b.require(len(armed)==1 and b.decode_words('0x'+armed[0]['input'][10:])[-5:]==output[1:],'Oracle was not armed with the exact actual-core quoted full state')
 after_selector='0x'+b.keccak256(b'afterSwap()').hex()[:8]
 b.require(any(frame.get('to')==bindings['oracle']['address'] and frame.get('input','').startswith(after_selector) and not frame.get('error') for frame in frames),'Exact after-swap proof did not execute')
 b.require(pins=={name:hashlib.sha256((ROOT/'src'/(name+'.sol')).read_bytes()).hexdigest() for name in CHANGED},'Current production source changed during qualification')
 result={'schema':1,'reference_swap_accepted':True,'source_sha256':pins,'base_launcher_sha256':BASE_SHA256,'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'exact_original_input_output_and_lp_floors_retained':True,'exact_one_actual_core_swap':True,'quoted_output_equals_actual_output':True,
  'quoted_full_state_armed_and_after_swap_validated':True,'selected_reference_pool':reference,'actual_output':str(received),'minimum_output':values['minimumOut'],
  'minimum_liquidity':values['minimumLiquidity'],'quotation_full_state_words':output[1:],'actual_receipt_sha256':hashlib.sha256((folder/'receipt.json').read_bytes()).hexdigest(),
  'compiler_source_line_endings':'Foundry LF normalization; raw SHA256 separately pinned',
  'scope':'Controlled current-contract owned-loopback receipt; not live market/provider/fees or release acceptance.'}
 b.save(args.output/'REFERENCE_ACCEPTANCE.json',result);print(json.dumps({'reference_swap_accepted':True,'case':args.case,'actual_output':str(received)}));return 0
if __name__=='__main__':raise SystemExit(main())
