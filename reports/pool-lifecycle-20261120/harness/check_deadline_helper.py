"""Exercise the new fixture deadline helper offline, not the Solidity EVM."""
from pathlib import Path
import ast
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT/'reports/pool-lifecycle-20261120/run/run_pool.py'
EXPECTED = '500d6cf389830184fe3658857b534f37ecd332346f81714eb42005fac92afab1'


def main():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED
    tree = ast.parse(raw)
    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'deadline']
    assert len(functions) == 1
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), 'exec'), namespace)
    calls = []
    class FakeNode:
        pending = None
        def call(self, method, params):
            calls.append((method, params))
            if method == 'evm_mine':
                return '0x0'
            assert method == 'eth_getBlockByNumber' and params == ['latest', False]
            return {'timestamp':'0x3e8','number':'0x1','hash':'0x'+'ab'*32}
    node = FakeNode()
    records = []
    namespace.update(n=node, deadline_records=records)
    value = namespace['deadline']()
    assert value == 1300
    assert calls == [('evm_mine', []), ('eth_getBlockByNumber', ['latest', False])]
    assert records == [{'block':'0x1','hash':'0x'+'ab'*32,'timestamp':1000,'deadline':1300,'TTL_seconds':300,'owned_empty_block_refresh':True}]
    calls.clear()
    node.pending = '0x'+'cd'*32
    try:
        namespace['deadline']()
    except AssertionError:
        pass
    else:
        raise AssertionError('Pending work must block local clock refresh')
    assert calls == [] and len(records) == 1
    guard = ROOT/'src/base/ZZZModule.sol'
    guarded = guard.read_bytes()
    assert b'if (deadline < block.timestamp || deadline > block.timestamp + 10 minutes) revert Expired();' in guarded
    print(json.dumps(dict(schema=1, kind='new_offline_fixture_helper_controls_not_EVM',
        driver_sha256=EXPECTED, helper_AST_sha256=hashlib.sha256(ast.dump(functions[0],include_attributes=False).encode()).hexdigest(),
        guard_source_sha256=hashlib.sha256(guarded).hexdigest(), new_controls=2,
        fresh_header_TTL300=True, pending_prevents_clock_change=True,
        Solidity_rule='now <= deadline <= now+600; original+3600 refused',
        network_calls=0, real_processes=0, actual_EVM_acceptance=False, unchanged_tests_rerun=False)))


if __name__ == '__main__':
    main()
