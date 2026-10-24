"""Prepare an isolated $1 local rehearsal; never edit production or broadcast.

Both floor-modified contracts require chain ID 31337 at construction. This is a test
artifact guard, not cryptographic chain authentication or deployment approval.
Only the two gross-activation floors and constructor guards change. Mint price,
governed execution-loss policy, LP ownership and reward rules remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PATCHES = {
    'src/ZZZActivationEntry.sol': (
        ('(!request.increase && grossUSD < 100e18)', '(!request.increase && grossUSD < 1e18)'),
        ('constructor(address controller, address poolRegistry, address assets) ZZZModule(controller) {',
         'constructor(address controller, address poolRegistry, address assets) ZZZModule(controller) {\n'
         '        require(block.chainid == 31337, "LOCAL_REHEARSAL_ONLY");'),
    ),
    'src/ZZZVaultCanonical.sol': (
        ('(activation && inputUSD < 100e18)', '(activation && inputUSD < 1e18)'),
        ('constructor(address controller, address vaultController, uint256 chain) {',
         'constructor(address controller, address vaultController, uint256 chain) {\n'
         '        require(block.chainid == 31337, "LOCAL_REHEARSAL_ONLY");'),
    ),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def transform(name: str, data: bytes) -> bytes:
    if name not in PATCHES:
        return data
    text = data.decode('utf-8')
    for before, after in PATCHES[name]:
        if text.count(before) != 1:
            raise ValueError(f'{name}: reviewed source anchor changed; review before generating')
        text = text.replace(before, after, 1)
    return text.encode('utf-8')


def loss_policy(data: bytes) -> tuple[int, int]:
    """Accept only unique, reviewed decimal-literal uint16 initializers.

    This deliberately does not evaluate Solidity expressions or infer an older
    default. Comments/string literals cannot supply a declaration. Unknown
    declaration syntax needs review before generating any output directory.
    """
    text = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  lambda match: ' ' * len(match.group()), data.decode('utf-8'))
    values = []
    for name, modifiers in (('contributionLossBps','public'), ('MAX_LOSS_BPS','public constant')):
        declarations = []
        for statement in re.split(r'[;{}]', text):
            found = re.search(r'\b'+name+r'\b', statement)
            if found is None: continue
            prefix = statement[:found.start()].strip()
            if (re.fullmatch(r'[A-Za-z_]\w*(?:\s+(?:public|private|internal|constant|immutable))*',prefix) and
                    prefix not in ('return','emit','revert','delete')):
                declarations.append(statement.strip())
        pattern = r'uint16\s+' + r'\s+'.join(modifiers.split()) + r'\s+'+name+r'\s*=\s*(0|[1-9][0-9]{0,4})'
        match = re.fullmatch(pattern,declarations[0]) if len(declarations) == 1 else None
        if match is None:
            raise ValueError('Budget execution-loss declaration changed; review before generating')
        values.append(int(match[1]))
    default, maximum = values
    if not 0 <= default <= maximum <= 1000 or maximum == 0:
        raise ValueError('Budget execution-loss literals have invalid bounds')
    return default, maximum


def validate_destination(root: Path, output: Path) -> Path:
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError('Rehearsal output must be outside and not contain the repository')
    if output.exists():
        raise ValueError('Output must be a new directory; existing artifacts are never overwritten')
    return output


def prepare(root: Path, output: Path, solc: Path) -> dict:
    root = root.resolve()
    output = validate_destination(root, output)
    solc = solc.resolve(strict=True)
    if not solc.is_file():
        raise ValueError('Provide the reviewed local solc 0.8.26 executable')
    inputs = {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted((root/'src').rglob('*.sol'))}
    if 'src/ZZZMigrationBudget.sol' not in inputs:
        raise ValueError('Missing production loss-policy source')
    default_loss, maximum_loss = loss_policy(inputs['src/ZZZMigrationBudget.sol'])
    # Copy only the transitive relative imports of the test fixture, not deployment scripts.
    pending = [root/'test/AtomicActivationIntegration.t.sol']
    while pending:
        path = pending.pop().resolve()
        if not path.is_relative_to(root):
            raise ValueError('Fixture imports must remain inside the repository')
        name = path.relative_to(root).as_posix()
        if name in inputs:
            continue
        raw = path.read_bytes()
        inputs[name] = raw
        for imported in re.findall(r'(?:from\s*|import\s*)[\"\'](\.[^\"\']+)[\"\']', raw.decode('utf-8')):
            pending.append(path.parent/imported)
    fixture_name = 'rehearsal/one-dollar/DollarActivation.t.sol'
    inputs[fixture_name] = (root/fixture_name).read_bytes()
    generated = {name: transform(name, data) for name, data in inputs.items() if name != fixture_name}
    if set(PATCHES) - generated.keys():
        raise ValueError('Missing production floor source')
    generated['test/DollarActivation.t.sol'] = inputs[fixture_name]
    # Check anchors and all inputs before creating output; no half-applied source patches.
    remappings = [f'{alias}={path.as_posix()}/' for alias, path in (
        ('@openzeppelin/contracts/', root/'node_modules/@openzeppelin/contracts'),
        ('@uniswap/v4-core/', root/'node_modules/@uniswap/v4-core'),
        ('@uniswap/v4-periphery/', root/'node_modules/@uniswap/v4-periphery'),
        ('forge-std/', root/'lib/forge-std/src'))]
    config = '\n'.join([
        '# GENERATED LOCAL REHEARSAL ONLY. No signer, RPC or deployment scripts.',
        '[profile.default]', 'src = "src"', 'test = "test"', 'script = "no-deployment-scripts"',
        'out = "out"', 'libs = []', 'chain_id = 31337', f'solc = {json.dumps(solc.as_posix())}',
        'evm_version = "cancun"', 'optimizer = true', 'optimizer_runs = 1',
        'optimizer_details = { yul = false }', 'via_ir = true', 'ffi = false',
        'fs_permissions = []', 'remappings = '+json.dumps(remappings), '',
    ])
    generated['foundry.toml'] = config.encode('utf-8')
    manifest = {
        'schema': 1, 'scope': 'local-only $1 rehearsal; NOT a production build or live deployment',
        'chain_id': 31337, 'minimum_activation_usd18': str(10**18),
        'production_minimum_activation_usd18': str(100*10**18),
        'mint_price_wei': str(5*10**16), 'execution_loss_bps': default_loss,
        'maximum_execution_loss_bps': maximum_loss,
        'execution_loss_scope': 'Generated Budget constructor default, preserved from source; governance and individual test fixtures may select another permitted cap.',
        'gas_separate': True, 'production_sources_modified': False,
        'patched_sources': list(PATCHES), 'solc_sha256': sha(solc.read_bytes()),
        'inputs': {name: sha(data) for name, data in sorted(inputs.items())},
        'generated': {name: sha(data) for name, data in sorted(generated.items())},
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, data in generated.items():
        path = output/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output/'REHEARSAL.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--solc', type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = prepare(ROOT, args.output, args.solc)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Rehearsal preparation refused: {exc}\n')
    print(f'Prepared LOCAL ONLY rehearsal at {args.output.resolve()}')
    print(f'{len(manifest["generated"])} source/configuration files; production untouched.')


if __name__ == '__main__':
    main()
