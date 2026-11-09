"""Deploy current, unmodified PoPL contracts to a caller-owned disposable fork.

There is deliberately no command-line RPC, wallet, key or process-launch API.
The parent rehearsal supplies a guarded local transport and owns its Anvil child.
Production creation objects are reused only after all retained source pins match.
Feeds/VRF and explicit local ERC20 balance funding are controlled test substitutes.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zzz_ops.abi import decode_words, keccak256
from zzz_ops.errors import RpcError

NORMAL = ROOT / 'reports/fee-flow-audit-20261107/contract/normal-final-4de5dcc67c'
FIXTURE_SOURCE = 'test/local/Source9RehearsalFixtures.sol'
CHAIN = 4663
FORK_BLOCK = 96_427_989
FORK_HASH = '0x0ba14c22200dfc717bbd2c8b5b8842329775374d06f46e30c65e273f067ecbc3'
POOL = '0x501122bfd256e408a63bddad901cc19a2512d74b2006f0474a3cf480e94afe1b'
ZERO = '0x' + '0' * 40
ZERO_HASH = '0x' + '0' * 64
UNIT = 10**18
RECEIPT_POLL_SECONDS = 120
RECEIPT_MAX_ATTEMPTS = 600
DEPS = {
    'pool_manager': '0x8366a39cc670b4001a1121b8f6a443a643e40951',
    'position_manager': '0x58daec3116aae6d93017baaea7749052e8a04fa7',
    'state_view': '0xf3334192d15450cdd385c8b70e03f9a6bd9e673b',
    'permit2': '0x000000000022d473030f116ddee9f6b43ac78ba3',
    'zzz': '0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a',
}
UPSTREAM_HASHES = dict(zip(DEPS, (
    '0xbd3881180b547f5fe817545743cfb4343e96b1bc6640dcd70c106b0066e95626',
    '0xc873e135dc9aaec88489cfbad146b4cb49d6a32e0d80326377784b7ba17670b2',
    '0x7d9c591e0956fd89d98feb4ffcfe8bf1f7a62bd485edd979fa21d104b49878a6',
    '0x5208783f52488f7d3493e5e38311ab707c1d75457fe472a19b0b4d57d66a7fca',
    '0x3d5ba33c3a94f655c16348011ff2c72f6ce8085239454ce4a6c4bf284e84a597',
)))
MODULES = {
    'vault': 'ZZZVault', 'nft': 'ZZZNFT', 'liquidity': 'ZZZLiquidityManager',
    'rewards': 'ZZZRewards', 'membership': 'ZZZMembership', 'fees': 'ZZZFeeController',
    'strategy': 'ZZZStrategy', 'compounder': 'ZZZCompounder', 'buyback': 'ZZZBuyback',
    'migration': 'ZZZMigration', 'oracle': 'ZZZOracle', 'pools': 'ZZZPoolRegistry',
    'canonical': 'ZZZCanonicalHandoff', 'nft_canonical': 'ZZZNFTCanonical',
    'vault_canonical': 'ZZZVaultCanonical', 'fees_canonical': 'ZZZFeesCanonical',
}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _save(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


class SubmissionUncertain(RuntimeError):
    """The saved intent must be reconciled; a new submission is forbidden."""


class ReceiptUnresolved(RuntimeError):
    """A known submitted hash remains unresolved, rather than failed."""


def _contracts(objects):
    return objects.get('contracts', objects)


def _object(objects, source, name):
    entry = _contracts(objects)[source][name]
    bytecode = entry.get('evm', {}).get('bytecode', {}).get('object')
    if bytecode is None:
        bytecode = entry.get('bytecode', {}).get('object')
    if not isinstance(bytecode, str) or not re.fullmatch(r'(?:0x)?[a-fA-F0-9]+', bytecode):
        raise ValueError('Missing, linked or malformed creation object: ' + name)
    return bytecode.removeprefix('0x').lower()


def load_production_objects():
    """Load the exact retained normal objects, checking every raw source pin."""
    start = json.loads((NORMAL / 'START.json').read_text(encoding='utf-8'))
    compiler_input = json.loads((NORMAL / 'compiler-input.json').read_text(encoding='utf-8'))
    expected_settings = dict(optimizer={'enabled': True, 'runs': 1, 'details': {'yul': False}},
                             viaIR=True, evmVersion='cancun')
    settings = compiler_input['settings']
    if any(settings.get(k) != v for k, v in expected_settings.items()):
        raise ValueError('Retained compiler settings differ from the reviewed normal profile')
    sources = compiler_input['sources']
    if set(sources) != set(start['source_sha256']):
        raise ValueError('Retained compiler source closure differs from raw source pins')
    current = {}
    for relative, embedded in sources.items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Compiler input source escapes this checkout')
        raw = path.read_bytes()
        current[relative] = _sha(raw)
        if current[relative] != start['source_sha256'][relative]:
            raise ValueError('Current source differs from retained normal object: ' + relative)
        # Solidity input text uses universal-newline normalization. Raw-byte
        # identity is independently enforced against the normal START record.
        if raw.decode('utf-8').replace('\r\n', '\n') != embedded['content'].replace('\r\n', '\n'):
            raise ValueError('Embedded compiler input differs from source: ' + relative)
    output_path = NORMAL / 'compiler-output.json.gz'
    output = json.loads(gzip.decompress(output_path.read_bytes()))
    if any(x.get('severity') == 'error' for x in output.get('errors', [])):
        raise ValueError('Retained normal compiler output contains errors')
    return dict(contracts=output['contracts'], source_validation={
        'normal_record': str(NORMAL.relative_to(ROOT)).replace('\\', '/'),
        'source_sha256': current, 'compiler_input_sha256': _sha((NORMAL / 'compiler-input.json').read_bytes()),
        'compiler_output_gzip_sha256': _sha(output_path.read_bytes()),
        'settings': expected_settings, 'production_runtime_or_source_changed': False,
    })


def _tool_env():
    keep = ('SystemRoot', 'WINDIR', 'SystemDrive', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP',
            'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'PROGRAMDATA', 'HOMEDRIVE', 'HOMEPATH')
    return {key: os.environ[key] for key in keep if key in os.environ}


def compile_fixtures(solc_path, output_dir):
    """Compile only the self-contained test substitutes; no public calls."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    raw = (ROOT / FIXTURE_SOURCE).read_bytes()
    payload = dict(language='Solidity', sources={FIXTURE_SOURCE: {'content': raw.decode('utf-8')}}, settings={
        'optimizer': {'enabled': True, 'runs': 1, 'details': {'yul': False}},
        'viaIR': True, 'evmVersion': 'cancun',
        'outputSelection': {'*': {'*': ['abi', 'evm.bytecode.object', 'evm.deployedBytecode.object', 'metadata']}},
    })
    _save(destination / 'fixture-compiler-input.json', payload)
    run = subprocess.run([str(solc_path), '--standard-json'], input=json.dumps(payload).encode(),
                         capture_output=True, cwd=ROOT, timeout=180, env=_tool_env(),
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    (destination / 'fixture-compiler-stdout.json').write_bytes(run.stdout)
    (destination / 'fixture-compiler-stderr.txt').write_bytes(run.stderr)
    output = json.loads(run.stdout)
    errors = [x for x in output.get('errors', []) if x.get('severity') == 'error']
    _save(destination / 'fixture-compiler-status.json', dict(
        exit_code=run.returncode, errors=errors, fixture_source_sha256=_sha(raw),
        solc_sha256=_sha(Path(solc_path).read_bytes()), settings=payload['settings'],
        no_production_sources_compiled=True))
    if run.returncode or errors:
        raise ValueError('Controlled rehearsal fixture compilation failed; raw output retained')
    output['fixture_source_sha256'] = _sha(raw)
    return output


def _transport(rpc):
    """Require the private ownership assertion supplied by the parent runner."""
    if getattr(rpc, 'rehearsal_owned', False) is not True:
        raise ValueError('A parent-owned disposable Anvil transport is required')
    location = urlsplit(getattr(rpc, 'url', ''))
    if (location.scheme != 'http' or location.hostname not in ('127.0.0.1', '::1') or
            location.username is not None or location.password is not None or location.query or
            location.fragment or location.path not in ('', '/')):
        raise ValueError('The owned rehearsal transport must be uncredentialed loopback HTTP')
    call = rpc if callable(rpc) else getattr(rpc, 'call', None)
    if not callable(call):
        raise ValueError('The owned transport must be callable or expose call(method, params)')
    if int(call('eth_chainId', []), 16) != CHAIN:
        raise ValueError('The owned fork has the wrong chain identity')
    if 'anvil' not in call('web3_clientVersion', []).lower():
        raise ValueError('The owned transport is not an Anvil rehearsal')
    fork_number = getattr(rpc, 'fork_block_number', None)
    fork_hash = getattr(rpc, 'fork_block_hash', None)
    if type(fork_number) is not int or fork_number < FORK_BLOCK or not isinstance(fork_hash, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', fork_hash):
        raise ValueError('The parent must bind an explicit reviewed fork number/hash')
    anchor = call('eth_getBlockByNumber', [hex(fork_number), False])
    if anchor is None or anchor['hash'].lower() != fork_hash.lower():
        raise ValueError('The selected fork anchor does not match the reviewed exact hash')
    return call


class RehearsalDeployment:
    def __init__(self, rpc, objects, fixtures, cast_path, output_dir):
        self.rpc = _transport(rpc)
        self.fork_number = rpc.fork_block_number
        self.fork_hash = rpc.fork_block_hash.lower()
        self.objects, self.fixtures = objects, fixtures
        self.cast = Path(cast_path).resolve()
        if not self.cast.is_file():
            raise ValueError('An explicit offline cast executable is required')
        self.output = Path(output_dir)
        self.output.mkdir(parents=True, exist_ok=True)
        self.receipts = []
        self.pending_submission = None
        self.intent_sequence = 0
        self.contracts = {}
        self.accounts = self.rpc('eth_accounts', [])[:4]
        if len(self.accounts) != 4 or any(self.rpc('eth_getCode', [a, 'latest']) != '0x' for a in self.accounts):
            raise ValueError('Four disposable unlocked empty-code accounts are required')
        self.owner = self.accounts[0]
        self.initial_block = self.rpc('eth_getBlockByNumber', ['latest', False])
        head_number = int(self.initial_block['number'], 16)
        if not self.fork_number <= head_number <= self.fork_number + 12:
            raise ValueError('Deployment requires the pristine owned fork, never an existing lab')
        self.warmup_blocks = []
        parent_hash = self.fork_hash
        for number in range(self.fork_number + 1, head_number + 1):
            block = self.rpc('eth_getBlockByNumber', [hex(number), False])
            if (block is None or int(block['number'], 16) != number or
                    block['parentHash'].lower() != parent_hash or block.get('transactions') != []):
                raise ValueError('Only consecutive empty parent-owned warmup blocks may precede deployment')
            self.warmup_blocks.append({'number': number, 'hash': block['hash'], 'parent_hash': block['parentHash']})
            parent_hash = block['hash'].lower()
        self.txlog = (self.output / 'deployment-transactions.ndjson').open('x', encoding='utf-8', newline='\n')
        _save(self.output / 'deployment-start.json', dict(
            chain_id=CHAIN, fork_block=self.fork_number, fork_hash=self.fork_hash, accounts=self.accounts,
            empty_owned_warmup_blocks=self.warmup_blocks,
            transport='parent-owned disposable loopback Anvil; endpoint deliberately omitted',
            production_source_validation=objects['source_validation'],
            fixture_source_sha256=fixtures.get('fixture_source_sha256'),
            fixtures_only=['correlated USD observations', 'operator-controlled VRF', 'explicit local balance funding'],
            public_transactions=False, existing_lab_changed=False,
        ))

    def encode(self, signature, *args):
        values = ['true' if x is True else 'false' if x is False else str(x) for x in args]
        run = subprocess.run([str(self.cast), 'abi-encode', signature, *values], capture_output=True,
                             cwd=ROOT, env=_tool_env(), timeout=30,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        result = run.stdout.decode('utf-8').strip()
        if run.returncode or not re.fullmatch(r'0x(?:[a-fA-F0-9]{64})*', result):
            raise ValueError('Offline ABI encoding failed: ' + signature)
        return result

    def calldata(self, signature, *args):
        return '0x' + keccak256(signature.encode()).hex()[:8] + self.encode(signature, *args)[2:]

    def read(self, target, signature, *args):
        target = self.contracts.get(target, target)
        return decode_words(self.rpc('eth_call', [{'to': target, 'data': self.calldata(signature, *args)}, 'latest']))

    def addr(self, target, signature, *args):
        values = self.read(target, signature, *args)
        if len(values) != 1 or int(values[0][:24], 16) != 0:
            raise ValueError('Malformed address getter: ' + signature)
        return '0x' + values[0][-40:]

    def code_hash(self, target):
        code = self.rpc('eth_getCode', [target, 'latest'])
        if code == '0x':
            raise ValueError('Expected deployed runtime')
        return '0x' + keccak256(bytes.fromhex(code[2:])).hex()

    def journal(self, event, **fields):
        self.txlog.write(json.dumps(dict(event=event, observed_time_ns=time.time_ns(), **fields), sort_keys=True) + '\n')
        self.txlog.flush()
        os.fsync(self.txlog.fileno())

    def send(self, label, *, target=None, data='0x', value=0, sender=None):
        if self.pending_submission is not None:
            raise SubmissionUncertain('A saved deployment intent/hash requires reconciliation before any new submission')
        transaction = {'from': sender or self.owner, 'data': data, 'value': hex(value)}
        if target is not None:
            transaction['to'] = self.contracts.get(target, target)
        estimate = int(self.rpc('eth_estimateGas', [transaction]), 16)
        gas = (estimate * 120 + 99) // 100
        block = self.rpc('eth_getBlockByNumber', ['latest', False])
        if gas > min(64_000_000, int(block['gasLimit'], 16)):
            raise ValueError('Rehearsal deployment exceeds its explicit block/gas budget: ' + label)
        transaction['gas'] = hex(gas)
        nonce = self.rpc('eth_getTransactionCount', [transaction['from'], 'pending'])
        if not isinstance(nonce, str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', nonce):
            raise ValueError('Malformed pending nonce; no deployment submission attempted')
        transaction['nonce'] = nonce
        self.intent_sequence += 1
        intent_id = 'deployment-' + str(self.intent_sequence).zfill(4)
        intent = dict(intent_id=intent_id, label=label, transaction=transaction, estimate=estimate,
                      reviewed_block_number=block['number'], reviewed_block_hash=block['hash'],
                      data_sha256=_sha(bytes.fromhex(data[2:])), data_bytes=(len(data)-2)//2,
                      transaction_hash=None, state='intent')
        self.pending_submission = intent
        # This exact public unsigned intent and nonce reach durable storage
        # BEFORE the only broadcast. A transport exception proves no outcome.
        self.journal('intent', **intent)
        try:
            txhash = self.rpc('eth_sendTransaction', [transaction])
        except BaseException as exc:
            self.pending_submission['state'] = 'submission_unknown'
            self.journal('submission_unknown', intent_id=intent_id, label=label,
                         error_type=type(exc).__name__, automatic_retry=False)
            raise SubmissionUncertain('Deployment submission outcome is unknown; saved intent retained, no resend') from exc
        if not isinstance(txhash, str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', txhash):
            self.pending_submission['state'] = 'submission_unknown'
            self.journal('submission_unknown', intent_id=intent_id, label=label,
                         error_type='MalformedReturnedHash', automatic_retry=False)
            raise SubmissionUncertain('Deployment returned no usable hash; saved intent retained, no resend')
        self.pending_submission.update(transaction_hash=txhash, state='submitted')
        # Persist the returned hash before ANY receipt read. A crash/read fault
        # cannot erase a possibly mined transaction or trigger another send.
        self.journal('submitted', intent_id=intent_id, label=label, transaction_hash=txhash,
                     automatic_retry=False)
        deadline = time.monotonic() + RECEIPT_POLL_SECONDS
        attempts = 0
        receipt = None
        while attempts < RECEIPT_MAX_ATTEMPTS and time.monotonic() < deadline:
            attempts += 1
            try:
                receipt = self.rpc('eth_getTransactionReceipt', [txhash])
            except RpcError as exc:
                self.journal('receipt_read_error', intent_id=intent_id, label=label,
                             transaction_hash=txhash, attempt=attempts, error_type=type(exc).__name__,
                             retry_same_hash=True, automatic_resubmit=False)
            else:
                if receipt is not None:
                    break
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(.1, remaining))
        if receipt is None:
            self.pending_submission['state'] = 'receipt_unresolved'
            self.journal('receipt_unresolved', intent_id=intent_id, label=label, transaction_hash=txhash,
                         attempts=attempts, polling_seconds=RECEIPT_POLL_SECONDS, automatic_resubmit=False)
            raise ReceiptUnresolved('Deployment receipt is unresolved; submitted hash retained, no resend')
        if (not isinstance(receipt, dict) or receipt.get('transactionHash', '').lower() != txhash.lower() or
                receipt.get('status') not in ('0x0', '0x1') or
                not isinstance(receipt.get('blockNumber'), str) or
                not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', receipt['blockNumber']) or
                not isinstance(receipt.get('blockHash'), str) or
                not re.fullmatch(r'0x[0-9a-fA-F]{64}', receipt['blockHash'])):
            self.journal('receipt_rejected', intent_id=intent_id, label=label, transaction_hash=txhash,
                         attempts=attempts, reason='malformed_or_mismatched_receipt', automatic_resubmit=False)
            raise ReceiptUnresolved('Deployment receipt cannot authenticate the submitted hash; no resend')
        record = dict(intent_id=intent_id, label=label, transaction_hash=txhash, receipt=receipt, estimate=estimate,
                      transaction={k: v for k, v in transaction.items() if k != 'data'},
                      data_sha256=intent['data_sha256'], data_bytes=intent['data_bytes'])
        self.journal('confirmed' if receipt['status'] == '0x1' else 'reverted', **record)
        self.receipts.append(record)
        self.pending_submission = None
        if receipt['status'] != '0x1':
            raise ValueError('Deployment/configuration transaction reverted; authenticated receipt retained: ' + label)
        return receipt

    def deploy(self, role, name, signature='constructor()', args=(), fixture=False):
        source = FIXTURE_SOURCE if fixture else 'src/' + name + '.sol'
        bytecode = _object(self.fixtures if fixture else self.objects, source, name)
        receipt = self.send('deploy:' + role, data='0x' + bytecode + self.encode(signature, *args)[2:])
        deployed = receipt.get('contractAddress')
        if not isinstance(deployed, str) or self.rpc('eth_getCode', [deployed, 'latest']) == '0x':
            raise ValueError('Creation did not produce the expected runtime: ' + role)
        self.contracts[role] = deployed.lower()
        return deployed.lower()

    def call(self, target, signature, *args):
        return self.send('configure:' + target + ':' + signature, target=target,
                         data=self.calldata(signature, *args))

    def bind(self, role):
        self.call('access', 'bind(bytes32,address)', '0x' + keccak256(MODULES[role].encode()).hex(), self.contracts[role])


def deploy(rpc, artifact_objects, fixture_objects, cast_path, output_dir):
    """Return a complete sealed source7 inventory on the owned exact fork.

    ``rpc`` is callable or has ``call(method, params)``, with ``url`` loopback and
    ``rehearsal_owned is True`` set by the parent process owner. It never accepts
    a public endpoint. ``artifact_objects`` comes from load_production_objects;
    ``fixture_objects`` comes from compile_fixtures. Transactions use only the
    four Anvil-owned unlocked accounts, with no private-key handling.
    """
    expected = load_production_objects()
    for source, entries in expected['contracts'].items():
        for name, entry in entries.items():
            if entry.get('evm', {}).get('bytecode', {}).get('object'):
                if _object(artifact_objects, source, name) != _object(expected, source, name):
                    raise ValueError('Supplied production object differs from exact retained normal build: ' + name)
    if fixture_objects.get('fixture_source_sha256') != _sha((ROOT / FIXTURE_SOURCE).read_bytes()):
        raise ValueError('Rehearsal fixture bytecode lacks the current source binding')
    lab = RehearsalDeployment(rpc, expected, fixture_objects, cast_path, output_dir)
    review = '0x' + keccak256(b'SOURCE9 OWNED DISPOSABLE FORK ONLY; NOT PRODUCTION QUALIFICATION').hex()
    try:
        for role, addr in DEPS.items():
            if lab.code_hash(addr) != UPSTREAM_HASHES[role]:
                raise ValueError('Selected real fork dependency runtime differs: ' + role)
        c = lab.contracts
        ac = lab.deploy('access', 'ZZZAccessController', 'constructor(address,address,address)',
                        (lab.owner, lab.accounts[3], lab.owner))
        policy = lab.deploy('policy', 'ZZZProtocolPolicy', 'constructor(address,address)', (ac, lab.owner))
        lab.call('access', 'bindProtocolPolicy(address)', policy)
        budget = lab.deploy('budget', 'ZZZMigrationBudget', 'constructor(address)', (ac,))
        lab.deploy('vault', 'ZZZVault', 'constructor(address,uint256,address)', (ac, CHAIN, budget)); lab.bind('vault')
        lab.deploy('nft', 'ZZZNFT', 'constructor(address,string)', (ac, 'ipfs://SOURCE9-DISPOSABLE-REHEARSAL/')); lab.bind('nft')
        balancer = lab.deploy('lp_balancer', 'ZZZLPBalancer', 'constructor(address,address,address)',
                             (ac, DEPS['pool_manager'], DEPS['state_view']))
        lab.deploy('liquidity', 'ZZZLiquidityManager', 'constructor(address,address,address,address,address,address)',
                   (ac, DEPS['position_manager'], DEPS['state_view'], DEPS['pool_manager'], DEPS['permit2'], balancer)); lab.bind('liquidity')
        for role in ('rewards', 'membership', 'fees'):
            lab.deploy(role, MODULES[role], 'constructor(address)', (ac,)); lab.bind(role)
        portfolio = lab.deploy('portfolio_policy', 'ZZZPortfolioPolicy', 'constructor(address)', (ac,))
        confirmation = lab.deploy('rebalance_confirmation', 'ZZZRebalanceConfirmation', 'constructor(address)', (ac,))
        lab.deploy('strategy', 'ZZZStrategy', 'constructor(address,address,address)', (ac, portfolio, confirmation)); lab.bind('strategy')
        lab.deploy('compounder', 'ZZZCompounder', 'constructor(address)', (ac,)); lab.bind('compounder')
        lab.deploy('buyback', 'ZZZBuyback', 'constructor(address,address,uint256)', (ac, DEPS['zzz'], 10_000*UNIT)); lab.bind('buyback')
        lab.deploy('migration', 'ZZZMigration', 'constructor(address)', (ac,)); lab.bind('migration')
        lab.deploy('oracle', 'ZZZOracle', 'constructor(address,address)', (ac, ZERO)); lab.bind('oracle')
        lab.deploy('pools', 'ZZZPoolRegistry', 'constructor(address)', (ac,)); lab.bind('pools')
        for role, signature, arguments in (
            ('canonical', 'constructor(address)', (ac,)),
            ('nft_canonical', 'constructor(address,address)', (ac, c['nft'])),
            ('vault_canonical', 'constructor(address,address,uint256)', (ac, c['vault'], CHAIN)),
            ('fees_canonical', 'constructor(address,address)', (ac, c['fees'])),
        ):
            lab.deploy(role, MODULES[role], signature, arguments); lab.bind(role)
        lab.deploy('lp_converter', 'ZZZLPRewardConverter', 'constructor(address,address,address)', (ac, c['rewards'], ZERO))
        lab.call('rewards', 'bindConverter(address)', c['lp_converter'])
        getters = {
            'entry': ('pools', 'activationEntry()'), 'activation_assets': ('pools', 'activationAssets()'),
            'royalty_factory': ('access', 'royaltyFactory()'), 'activation_assets_factory': ('access', 'activationAssetsFactory()'),
            'royalty_rewards': ('nft', 'royaltyRewards()'), 'claim_router': ('nft', 'claimRouter()'),
            'metadata': ('nft', 'metadataRenderer()'), 'rewards_canonical': ('rewards', 'canonicalModule()'),
            'contribution_pricing': ('oracle', 'contributionPricing()'),
            'position_operator': ('liquidity', 'positionOperator()'), 'lp_balance_math': ('lp_balancer', 'balanceMath()'),
            'custody_validation': ('migration', 'validation()'), 'lp_v4_executor': ('lp_converter', 'v4Executor()'),
        }
        for role, (parent, getter) in getters.items():
            c[role] = lab.addr(parent, getter)
        c['royalty_factory_part0'] = lab.addr('royalty_factory', 'part0()')
        c['royalty_factory_part1'] = lab.addr('royalty_factory', 'part1()')
        slot0 = lab.read(DEPS['state_view'], 'getSlot0(bytes32)', POOL)
        spot = int(slot0[0], 16)
        if spot <= 0 or int(slot0[3], 16) != 10020:
            raise ValueError('Selected fork pool is uninitialized or has the wrong static LP fee')
        eth_price = 2000*UNIT
        ratio_q96 = spot*spot//(1 << 96)
        zzz_price = eth_price*(1 << 96)//ratio_q96
        feeds = {}
        for role, asset, price in (('eth', ZERO, eth_price), ('zzz', DEPS['zzz'], zzz_price)):
            pair = []
            for suffix in ('a', 'b'):
                pair.append(lab.deploy(role + '_feed_' + suffix, 'Source9RehearsalFeed',
                                       'constructor(int256)', (price,), fixture=True))
            feeds[role] = pair
            policies = ['(' + ','.join((addr, lab.code_hash(addr),
                        '0x' + keccak256(('CORRELATED REHEARSAL ' + role + suffix).encode()).hex(),
                        '86400', '18')) + ')' for suffix, addr in zip(('a', 'b'), pair)]
            lab.call('oracle', 'setDualFeed(address,(address,bytes32,bytes32,uint32,uint8),(address,bytes32,bytes32,uint32,uint8),uint16,bytes32)',
                     asset, *policies, 300, review)
        token_hash = UPSTREAM_HASHES['zzz']
        lab.call('activation_assets', 'configureZZZ(address,bytes32,bytes32)', DEPS['zzz'], token_hash, review)
        lab.call('rewards', 'addAsset(address)', DEPS['zzz'])
        lab.call('migration', 'configureZZZ(address,bytes32,bytes32)', DEPS['zzz'], token_hash, review)
        vrf = lab.deploy('vrf', 'Source9RehearsalVRF', fixture=True)
        lab.call('policy', 'configureRandomness(address,bytes32,bytes32,uint256,uint16,uint32,bool,bytes32)',
                 vrf, lab.code_hash(vrf), '0x' + '0'*63 + '1', 1, 3, 500000, False, review)
        timestamp = int(lab.rpc('eth_getBlockByNumber', ['latest', False])['timestamp'], 16)
        lab.call('nft', 'setMintEnd(uint64)', timestamp + 3650*86400)
        # Explicit admitted pool floor supports the approved $5 growth minimum;
        # ProtocolPolicy independently retains the default $100 activation floor.
        pool_config = '((' + ','.join((ZERO, DEPS['zzz'], '10020', '200', ZERO)) + '),true,true,5000,500,100,200,43200,' + str(5*UNIT) + ',' + str(1_000_000*UNIT) + ')'
        lab.call('pools', 'configureNative(((address,address,uint24,int24,address),bool,bool,uint16,uint16,uint16,uint16,uint32,uint256,uint256))', pool_config)
        lab.call('lp_balancer', 'configureExecutionPools(bytes32[],bytes32)', '[' + POOL + ']', review)
        lab.call('strategy', 'setRangeOrientation(bytes32,uint8)', POOL, 1)
        lab.call('rebalance_confirmation', 'configure(uint32,uint32,bytes32)', 600, 300, review)
        lab.call('access', 'seal()')
        if (int(lab.read('access', 'isSealed()')[0], 16) != 1 or
                int(lab.read('vault', 'ACCOUNTING_VERSION()')[0], 16) != 7 or
                int(lab.read('rewards', 'LP_ALLOCATION_VERSION()')[0], 16) != 1 or
                lab.read('pools', 'contributionPool()')[0] != POOL[2:]):
            raise ValueError('Fresh source7 deployment postconditions failed')
        first = lab.receipts[0]['receipt']
        last = lab.rpc('eth_getBlockByNumber', ['latest', False])
        inventory = dict(schema=1, mode='SOURCE9 OWNED DISPOSABLE FORK REHEARSAL', chain_id=CHAIN,
            fork_block=lab.fork_number, fork_hash=lab.fork_hash, pool_id=POOL, contracts=c, dependencies=DEPS,
            empty_owned_warmup_blocks=lab.warmup_blocks,
            feeds=feeds, fixture_prices={'eth_usd_18': str(eth_price), 'zzz_usd_18': str(zzz_price)},
            accounts=lab.accounts, governance=lab.owner, keeper=lab.accounts[3],
            deployment_block=int(first['blockNumber'], 16), deployment_block_hash=first['blockHash'],
            configured_block=int(last['number'], 16), configured_block_hash=last['hash'],
            receipts=lab.receipts, production_source_validation=expected['source_validation'],
            limits={'activation_gas': 12_000_000, 'deployment_gas_cap': 64_000_000},
            defaults={'activation_usd_18': str(100*UNIT), 'growth_usd_18': str(5*UNIT),
                      'contribution_loss_bps': 200, 'maintenance_loss_bps': 300,
                      'additional_loss_bps': 100, 'hybrid_enabled': False,
                      'confirmation_duration_seconds': 600, 'maximum_observation_gap_seconds': 300},
            production_approved=False, public_transactions=False,
            qualification_exclusions=['independent feeds', 'VRF proofs', 'wallet signing', 'hosting', 'production gas/latency'])
        _save(lab.output / 'deployment-inventory.json', inventory)
        return inventory
    except BaseException as exc:
        _save(lab.output / 'deployment-failure.json', {'error_type': type(exc).__name__,
              'message': str(exc), 'mined_transactions': len(lab.receipts),
              'pending_submission': lab.pending_submission, 'retry_or_reset': False})
        raise
    finally:
        lab.txlog.close()


def fund_zzz(rpc, owner, amount, output_dir):
    """Explicit local balance substitution for one of the four owned accounts.

    Probe mapping slots under a snapshot, revert all probes, then write only the
    independently observed matching slot. No supply, venue, runtime or PoPL books
    are altered. This is local fixture funding, never a mint or economic proof.
    """
    if (not isinstance(owner, str) or not re.fullmatch(r'0x[0-9a-fA-F]{40}', owner) or
            int(owner, 16) == 0 or type(amount) is not int or not 0 < amount <= 100_000_000*UNIT):
        raise ValueError('Explicit bounded funding is restricted to owned disposable accounts')
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    stem = 'fixture-zzz-funding-' + owner.lower()[2:]
    final_path = destination / (stem + '.json')
    intent_path = destination / (stem + '-intent.json')
    journal_path = destination / (stem + '-journal.ndjson')
    if any(path.exists() or path.is_symlink() for path in (final_path, intent_path, journal_path)):
        raise FileExistsError('Existing funding evidence requires manual reconciliation; automatic replay is forbidden')
    reservation = dict(kind='EXPLICIT OWNED FORK TOKEN BALANCE SUBSTITUTE', token=DEPS['zzz'], owner=owner,
                       requested_balance=str(amount), state='reserved_no_mutation_attempted', automatic_replay=False)
    # Open all evidence exclusively and prove it writable BEFORE even validating
    # the RPC. Keep the reserved final descriptor so a late path/open error can
    # never first appear after changing a local token balance.
    with final_path.open('x+', encoding='utf-8', newline='\n') as final_stream, \
            intent_path.open('x', encoding='utf-8', newline='\n') as intent_stream, \
            journal_path.open('x', encoding='utf-8', newline='\n') as journal:
        for stream in (final_stream, intent_stream):
            json.dump(reservation, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())

        def event(name, **fields):
            journal.write(json.dumps(dict(event=name, observed_time_ns=time.time_ns(), owner=owner,
                                           automatic_replay=False, **fields), sort_keys=True) + '\n')
            journal.flush()
            os.fsync(journal.fileno())

        phase = 'reserved_no_mutation_attempted'
        event('evidence_reserved', requested_balance=str(amount))
        try:
            call = _transport(rpc)
            accounts = call('eth_accounts', [])[:4]
            if owner.lower() not in {a.lower() for a in accounts}:
                raise ValueError('Explicit bounded funding is restricted to owned disposable accounts')
            owner_word = owner[2:].lower().rjust(64, '0')
            data = '0x' + keccak256(b'balanceOf(address)').hex()[:8] + owner_word
            before = int(call('eth_call', [{'to': DEPS['zzz'], 'data': data}, 'latest']), 16)
            event('funding_intent', token=DEPS['zzz'], balance_before=str(before), requested_balance=str(amount),
                  fork_block=getattr(rpc, 'fork_block_number', None), fork_hash=getattr(rpc, 'fork_block_hash', None))
            marker = 876543210987654321
            found = None
            for index in range(64):
                phase = 'probe_snapshot'
                event('probe_snapshot_intent', mapping_slot=index)
                snapshot = call('evm_snapshot', [])
                slot = '0x' + keccak256(bytes.fromhex(owner_word + f'{index:064x}')).hex()
                try:
                    phase = 'probe_write'
                    event('probe_write_intent', mapping_slot=index, storage_key=slot, snapshot=snapshot,
                          marker=str(marker))
                    call('anvil_setStorageAt', [DEPS['zzz'], slot, '0x' + f'{marker:064x}'])
                    observed = int(call('eth_call', [{'to': DEPS['zzz'], 'data': data}, 'latest']), 16)
                    event('probe_observed', mapping_slot=index, observed_balance=str(observed))
                    if observed == marker:
                        found = (index, slot)
                finally:
                    phase = 'probe_restore'
                    # Restore the known snapshot even if evidence storage
                    # faults while recording the restoration intent.
                    restored = False
                    try:
                        event('probe_restore_intent', mapping_slot=index, snapshot=snapshot)
                    finally:
                        restored = call('evm_revert', [snapshot])
                    if restored is not True:
                        raise ValueError('Could not restore a local token-balance probe')
                    event('probe_restored', mapping_slot=index, snapshot=snapshot)
                if found is not None:
                    break
            if found is None:
                raise ValueError('Real fork ZZZ balance mapping not identified; no final funding write performed')
            phase = 'final_balance_write'
            event('funding_write_intent', token=DEPS['zzz'], mapping_slot=found[0], storage_key=found[1],
                  balance_before=str(before), requested_balance=str(amount))
            call('anvil_setStorageAt', [DEPS['zzz'], found[1], '0x' + f'{amount:064x}'])
            phase = 'final_balance_verification'
            after = int(call('eth_call', [{'to': DEPS['zzz'], 'data': data}, 'latest']), 16)
            if after != amount:
                raise ValueError('Local token funding did not produce the exact requested balance')
            record = dict(kind='EXPLICIT OWNED FORK TOKEN BALANCE SUBSTITUTE', state='verified',
                          token=DEPS['zzz'], owner=owner, balance_before=str(before), balance_after=str(after),
                          mapping_slot=found[0], storage_key=found[1], automatic_replay=False,
                          production_supply_or_principal_proof=False, runtime_changed=False)
            event('funding_verified', **{key: value for key, value in record.items() if key not in ('owner', 'automatic_replay')})
            # Replace only this invocation's exclusively created reservation;
            # immutable intent and append-only probe/write evidence remain.
            phase = 'final_evidence_write'
            final_stream.seek(0)
            json.dump(record, final_stream, sort_keys=True, indent=2)
            final_stream.write('\n')
            final_stream.truncate()
            final_stream.flush()
            os.fsync(final_stream.fileno())
            return record
        except BaseException as exc:
            event('funding_aborted', phase=phase, error_type=type(exc).__name__,
                  outcome='inspect saved intent/probe/write events; never infer whether funding happened')
            raise
