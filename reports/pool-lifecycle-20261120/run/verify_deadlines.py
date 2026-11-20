"""Bind actual saved LP call deadlines to reviewed owned-local heads, not wall time."""
from pathlib import Path
import gzip,json
HERE=Path(__file__).resolve().parent
CASE=Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/pool-lifecycle-20261120/run/attempt4')
wire=json.loads(gzip.decompress((CASE/'local-wire.json.gz').read_bytes()))
receipts={row['label']:row for row in json.loads((CASE/'receipts.json').read_bytes())}
records=json.loads((CASE/'deadline-records.json').read_bytes())
labels=['new_current_f6_mint','new_current_f6_increase','new_impossible_minL_actual_rollback','new_current_f6_harvest','new_current_f6_second_harvest','new_current_f6_close']
assert len(records)==len(labels)==6
for label,record in zip(labels,records):
    observed=[row['response'].get('result')for row in wire if row['request']['method']=='eth_getBlockByNumber'and row['request']['params']==['latest',False]]
    matching=[h for h in observed if isinstance(h,dict)and h.get('hash')==record['hash']and h.get('number')==record['block']and int(h['timestamp'],16)==record['timestamp']]
    assert matching and record['deadline']==record['timestamp']+300
    tx=receipts[label]['transaction'];receipt=receipts[label]['receipt']
    assert int(tx['data'][-64:],16)==record['deadline']
    assert int(receipt['blockNumber'],16)==int(record['block'],16)+1
result={'schema':1,'kind':'new_saved_deadline_binding_check_no_execution','LP_operations_bound':6,
    'calldata_last_word_equals_reviewed_deadline':True,'reviewed_head_hash_number_timestamp_match_wire':True,
    'deadline_TTL_seconds':300,'receipt_in_next_owned_block':True,
    'execution_timestamp_independently_recovered':False,
    'execution_guard_acceptance_basis':'Five successful actual contract receipts and one intended Slippage failure under unchanged source deadline guard; receipt timestamps are absent, not fabricated.',
    'network_calls':0,'EVM_tests_rerun':False,'production_approved':False}
with (HERE/'DEADLINE_VERIFICATION.json').open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
