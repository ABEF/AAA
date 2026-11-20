"""New offline Cast parser controls for the actual frozen report ABI helper."""
from pathlib import Path
import ast
import hashlib
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from zzz_ops.abi import keccak256

SOURCE = ROOT/'reports/pool-lifecycle-20261120/run/run_pool.py'
EXPECTED = '0ba103a4a98e71057c224ca2f5e798311519620625185a217a49850f80885cc9'
TOOLS = Path('C:/Users/Ali/.codex/visualizations/2026/10/14/01a13899-2be7-76f2-a5d0-72e4804c67b9/foundry-v1.4.4')


def main():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED
    tree = ast.parse(raw)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('abi','toolenv')]
    assert {n.name for n in functions} == {'abi','toolenv'}
    namespace = dict(TOOLS=TOOLS, subprocess=subprocess, os=os)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), 'exec'), namespace)
    signature = 'execute(bool,uint256,uint256,uint160)'
    rows = []
    for value in (True, False):
        result = namespace['abi'](signature, value, 37, 99, 4295128740)
        expected = '0x'+keccak256(signature.encode())[:4].hex()+''.join(v.to_bytes(32,'big').hex() for v in (int(value),37,99,4295128740))
        assert result == expected
        rows.append(dict(boolean=value, canonical_argument='true' if value else 'false',
            calldata_bytes=(len(result)-2)//2, exact_independent_words=True,
            calldata_sha256=hashlib.sha256(bytes.fromhex(result[2:])).hexdigest()))
    print(json.dumps(dict(schema=1,kind='two_new_offline_parser_controls_no_RPC',
        driver_sha256=EXPECTED,cast_binary_sha256=hashlib.sha256((TOOLS/'cast.exe').read_bytes()).hexdigest(),
        examples=rows,new_parser_calls=2,network_calls=0,EVM_executed=False,
        production_source_changed=False,unchanged_tests_rerun=False)))


if __name__ == '__main__':
    main()
