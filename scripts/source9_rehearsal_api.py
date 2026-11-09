"""Ephemeral source9 API composition for an independently owned local fork.

This module deploys nothing, never signs or sends, and cannot address a public
RPC. All production validators and HTTP DTO handlers run unchanged. The caller
owns the isolated Anvil and its transactions; this module owns only its new
evidence directory, index database and temporary loopback HTTP thread.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sys
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend_api.activation import ActivationTransactions
from frontend_api.activation_server import handler as activation_handler
from frontend_api.portfolio_v6 import ROLES as PORTFOLIO_ROLES
from frontend_api.server import ReadServer, handler as read_handler
from frontend_api.service import Projection, ROLES as BASE_ROLES, ZERO
from frontend_api.transactions import Transactions
from frontend_api.transaction_gas import DEFAULT_GAS_LIMIT, configured_limit
from indexer.monitor import Indexer
from zzz_ops.abi import address, decode_words, keccak256, word
from zzz_ops.price_policy import record as price_record
from zzz_ops.rpc import Rpc

ZERO_HASH = '0x' + '0' * 64
READ_ROLES = (*BASE_ROLES, 'principal_exit', 'rewards_canonical', *PORTFOLIO_ROLES)
ACTIVATION_ROLES = ('pools', 'oracle', 'liquidity', 'strategy', 'fees', 'membership',
    'migration', 'entry', 'activation_assets', 'budget', 'contribution_pricing',
    'balancing_router', 'portfolio_policy', 'lp_balance_math', 'lp_position_executor',
    'protocol_policy', 'rebalance_confirmation')
BROWSER_ROLES = (*READ_ROLES, 'entry', 'oracle', 'activation_assets', 'contribution_pricing', 'fees')
BROWSER_METHODS = frozenset(('eth_chainId', 'eth_blockNumber', 'eth_getBlockByNumber',
    'eth_getCode', 'eth_call', 'eth_estimateGas', 'eth_gasPrice', 'eth_getBalance'))
PROFILE = dict(source_profile=9, accounting_version=7, lp_allocation_version=1,
    custody_version=5, protocol_policy_version=1, royalty_settlement_version=4,
    royalty_reporting_schema=5, pricing_version=2, routing_version=3,
    review_policy_version=2, governance_version=2, fee_intake_version=1,
    portfolio_version=2, maintenance_policy_version=3, rebalance_confirmation_version=3,
    idle_compounding_version=4, lp_routing_version=2, execution_quality_version=1,
    residual_exit_version=1, residual_reinvest_version=1,
    canonical_schema='0x' + keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9').hex(),
    transaction_policy_schema=1)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _quantity(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', value):
        return int(value, 16)
    raise ValueError('Malformed rehearsal RPC quantity')


def _loopback(url):
    parsed = urlsplit(url)
    if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or
            parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.port):
        raise ValueError('An explicitly owned credential-free IPv4 loopback RPC is required')
    return url


def _browser_params(method, params):
    """Exact public read shapes; never forward state overrides or nonce fields."""
    if method in ('eth_chainId', 'eth_blockNumber', 'eth_gasPrice'):
        return params == []
    if method == 'eth_getBlockByNumber':
        return (len(params) == 2 and isinstance(params[0], str) and
            re.fullmatch(r'(?:0x(?:0|[1-9a-f][0-9a-f]*)|latest|safe|finalized)', params[0]) is not None and
            params[1] is False)
    if len(params) != 2:
        return False
    block = params[1]
    if (not isinstance(block, dict) or set(block) != {'blockHash', 'requireCanonical'} or
            block['requireCanonical'] is not True or not isinstance(block['blockHash'], str) or
            re.fullmatch(r'0x[0-9a-f]{64}', block['blockHash']) is None):
        return False
    if method in ('eth_getCode', 'eth_getBalance'):
        return isinstance(params[0], str) and re.fullmatch(r'0x[0-9a-f]{40}', params[0]) is not None
    tx = params[0]
    return (method in ('eth_call', 'eth_estimateGas') and isinstance(tx, dict) and
        not set(tx) - {'from', 'to', 'data', 'value', 'gas', 'gasPrice', 'maxFeePerGas', 'maxPriorityFeePerGas'} and
        isinstance(tx.get('to'), str) and re.fullmatch(r'0x[0-9a-f]{40}', tx['to']) is not None and
        isinstance(tx.get('data'), str) and re.fullmatch(r'0x(?:[0-9a-f]{2})*', tx['data']) is not None)


def _activation_gas_policy(value):
    if value is None:
        return dict(schema=1, limit=DEFAULT_GAS_LIMIT, fee_fields={}, manifest_fields={})
    limit=configured_limit(str(value) if type(value) is int else value)
    return dict(schema=2, limit=limit,
        fee_fields=dict(max_gas_limit=str(limit),max_network_fee_wei=str(10**18)),
        manifest_fields=dict(activation_policy_schema=2))


class Evidence:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=False)
        self.lock = threading.Lock()
        self.counter = 0
        self.stream = (self.directory / 'http.ndjson').open('x', encoding='utf-8')

    def save(self, name, value):
        with (self.directory / name).open('x', encoding='utf-8') as stream:
            stream.write(_json(value) + '\n')

    def http(self, value):
        with self.lock:
            self.stream.write(_json(value) + '\n')
            self.stream.flush()

    def trace(self, params, result=None, error=None):
        with self.lock:
            self.counter += 1
            self.save('trace-%04d.json' % self.counter,
                dict(method='debug_traceCall', params=params,
                     **({'result': result} if error is None else {'error_type': error})))

    def close(self):
        self.stream.close()


class ReadOnlyRPC:
    """Keep the supplied local transport behind the production read allowlist."""
    def __init__(self, transport, evidence):
        self.transport, self.evidence = transport, evidence

    def call(self, method, params=None):
        if method not in Rpc.READ_METHODS:
            raise ValueError('Rehearsal API transport is read-only')
        params = [] if params is None else params
        try:
            target = self.transport.call if hasattr(self.transport, 'call') else self.transport
            result = target(method, params)
        except Exception as exc:
            if method == 'debug_traceCall':
                self.evidence.trace(params, error=type(exc).__name__)
            raise
        if method == 'debug_traceCall':
            self.evidence.trace(params, result)
        # The production Rpc interface returns an integer only for chainId.
        return _quantity(result) if method == 'eth_chainId' else result


class RehearsalAPI:
    def __init__(self, rpc, evidence, read_config, activation_config, transaction_config,
                 projection, activation, transactions, manifest, contracts,
                 indexer=None, index_config=None):
        self.rpc, self.evidence = rpc, evidence
        self.read_config, self.activation_config = read_config, activation_config
        self.transaction_config = transaction_config
        self.projection, self.activation, self.transactions = projection, activation, transactions
        self.manifest, self.contracts = manifest, contracts
        self.indexer, self.index_config = indexer, index_config
        self.owner_thread = threading.get_ident()
        self.closed = False

    def sync_history(self):
        """Call from the owning thread after actual receipts, before browser reads."""
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError('History synchronization requires the rehearsal owner thread')
        blocks = 0
        if self.indexer is not None:
            while True:
                count = self.indexer.step()
                if not count:
                    break
                blocks += count
        return blocks

    def close(self):
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError('History shutdown requires the rehearsal owner thread')
        if not self.closed:
            if self.indexer is not None:
                self.indexer.close()
            self.evidence.close()
            self.closed = True


def build_config(rpc, inventory, *, rpc_url, evidence_dir, confirmations=1,
                 index_history=True, max_age_seconds=120, activation_gas_limit=None):
    """Observe exact new deployment pins; no fixture RPC or verifier replacement.

    Inventory accepts contract aliases policy/protocol_policy,
    canonical/handoff and migration/principal_exit. Fixed helper addresses are
    discovered from their real parent getters. Local feed/VRF substitutions must
    remain explicitly described by the deployment inventory and report.
    """
    _loopback(rpc_url)
    if getattr(rpc, 'rehearsal_owned', False) is not True:
        raise ValueError('The caller must supply its independently owned rehearsal fork transport')
    if getattr(rpc, 'url', rpc_url) != rpc_url:
        raise ValueError('The owned transport and configured local endpoint differ')
    if type(confirmations) is not int or not 1 <= confirmations <= 128:
        raise ValueError('Unsupported confirmation policy')
    if type(max_age_seconds) is not int or not 1 <= max_age_seconds <= 120:
        raise ValueError('Unsupported snapshot age')
    activation_policy=_activation_gas_policy(activation_gas_limit)
    evidence = Evidence(evidence_dir)
    reader = ReadOnlyRPC(rpc, evidence)
    indexer = None
    try:
        chain = reader.call('eth_chainId')
        if chain != 4663:
            raise ValueError('This rehearsal requires the selected chain4663 fork')
        genesis = reader.call('eth_getBlockByNumber', ['0x0', False])['hash'].lower()
        head = reader.call('eth_getBlockByNumber', ['latest', False])
        block = {'blockHash': head['hash'], 'requireCanonical': True}
        c = {name: address(value) for name, value in inventory['contracts'].items()
             if isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]{40}', value)}
        for target, source in (('protocol_policy', 'policy'), ('handoff', 'canonical'),
                               ('principal_exit', 'migration')):
            if target not in c:
                c[target] = c[source]
        c['migration'] = c['principal_exit']

        def read(target, method, *args, count=1):
            # The shared flat codec deliberately refuses zero addresses. Native
            # asset configuration reads have an explicit zero currency identity.
            types = method[method.index('(') + 1:-1].split(',') if args else []
            data = '0x' + keccak256(method.encode()).hex()[:8] + ''.join(
                '0' * 64 if typ == 'address' and value == ZERO else word(value, typ)
                for value, typ in zip(args, types))
            result = decode_words(reader.call('eth_call',
                [{'to': c.get(target, target), 'data': data}, block]))
            if len(result) != count:
                raise ValueError('Unexpected actual rehearsal getter layout')
            return result

        def addr(target, method):
            word = read(target, method)[0]
            if int(word[:24], 16):
                raise ValueError('Noncanonical actual rehearsal address')
            return address('0x' + word[-40:])

        for role, parent, method in (
                ('royalties', 'nft', 'royaltyRewards()'), ('claim_router', 'nft', 'claimRouter()'),
                ('rewards_canonical', 'rewards', 'canonicalModule()'),
                ('vault_canonical', 'vault', 'canonicalModule()'),
                ('entry', 'pools', 'activationEntry()'), ('activation_assets', 'pools', 'activationAssets()'),
                ('budget', 'vault', 'migrationBudget()'), ('contribution_pricing', 'oracle', 'contributionPricing()'),
                ('balancing_router', 'liquidity', 'balancingRouter()'),
                ('portfolio_policy', 'strategy', 'portfolioPolicy()'),
                ('rebalance_confirmation', 'strategy', 'rebalanceConfirmation()'),
                ('lp_balance_math', 'balancing_router', 'balanceMath()'),
                ('lp_position_executor', 'liquidity', 'positionOperator()'),
                ('pool_manager', 'liquidity', 'poolManager()'),
                ('state_view', 'liquidity', 'stateView()'),
                ('position_manager', 'liquidity', 'positionManager()'),
                ('permit2', 'liquidity', 'permit2()')):
            actual = addr(parent, method)
            if role in c and c[role] != actual:
                raise ValueError('Inventory differs from actual immutable helper binding')
            c[role] = actual
        zzz = addr('activation_assets', 'zzz()')
        codes = {}

        def runtime(target):
            if target not in codes:
                value = reader.call('eth_getCode', [target, block])
                if not isinstance(value, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})+', value):
                    raise ValueError('Missing actual rehearsal runtime')
                codes[target] = value.lower()
            return codes[target]

        def pin(target):
            return dict(address=target, code_hash='0x' + keccak256(bytes.fromhex(runtime(target)[2:])).hex())

        # Exact NFT creation, rather than a later seal or an old fork anchor.
        low = int(inventory['deployment_block'])
        high = _quantity(head['number'])
        while low < high:
            middle = (low + high) // 2
            header = reader.call('eth_getBlockByNumber', [hex(middle), False])
            present = reader.call('eth_getCode', [c['nft'],
                {'blockHash': header['hash'], 'requireCanonical': True}]) != '0x'
            if present:
                high = middle
            else:
                low = middle + 1
        anchor = reader.call('eth_getBlockByNumber', [hex(low), False])
        previous = reader.call('eth_getBlockByNumber', [hex(low - 1), False])
        if (reader.call('eth_getCode', [c['nft'], {'blockHash': previous['hash'], 'requireCanonical': True}]) != '0x' or
                reader.call('eth_getCode', [c['nft'], {'blockHash': anchor['hash'], 'requireCanonical': True}]).lower() != runtime(c['nft'])):
            raise ValueError('Fresh NFT creation boundary cannot be authenticated')
        assets = [dict(address=ZERO, code_hash=None, symbol='ETH', decimals=18),
                  dict(address=zzz, code_hash=pin(zzz)['code_hash'], symbol='ZZZ',
                       decimals=int(read(zzz, 'decimals()')[0], 16))]
        config = dict(schema=2, accounting_version=7, custody_version=5,
            fee_intake_version=1, protocol_policy_version=1, chain_id=chain,
            rpc_urls=[rpc_url], deployment_block=low, deployment_block_hash=anchor['hash'],
            confirmations=confirmations, max_block_age_seconds=max_age_seconds,
            contracts={role: pin(c[role]) for role in READ_ROLES}, assets=assets,
            royalty_reporting=dict(schema=5, converter=None))
        index_config = None
        if index_history:
            emitters = sorted({c[role] for role in ('nft', 'vault', 'rewards', 'royalties',
                'handoff', 'fees', 'membership', 'principal_exit')})
            database = str(evidence.directory / 'indexer.sqlite')
            config['history'] = dict(database=database, start_block=low,
                start_parent_hash=previous['hash'], contracts=emitters, max_events=100000)
            index_config = dict(chain_id=chain, rpc_urls=[rpc_url], start_block=low,
                start_parent_hash=previous['hash'], confirmations=confirmations,
                block_chunk=100, max_reorg_depth=256, contracts=emitters, database=database)
            indexer = Indexer(index_config, rpc=reader)
        projection = Projection(config, rpc=reader)
        review = '0x' + keccak256(b'SOURCE9 ISOLATED ANVIL REHEARSAL ONLY: simple local execution gas; no L1/data components; no actual network fee qualification').hex()
        tx = dict(schema=1, chain_id=chain, projection_sha256=projection.identity,
            fee_policy=dict(estimate_includes_all_fees=True, review_hash=review,
                max_gas_price_wei=str(100 * 10**9), max_network_fee_wei=str(10**18)))
        pool = inventory['pool_id'].lower()
        policies = {}
        total = int(read('oracle', 'policyCount()')[0], 16)
        if not 2 <= total <= 64:
            raise ValueError('Unexpected fresh dual-feed policy inventory')
        ordinal_ids = ['0x' + read('oracle', 'policyAt(uint256)', n)[0] for n in range(total)]
        tokens = []
        sources = []
        input_assets = []
        for item in assets:
            target = item['address']
            identifier = '0x' + read('oracle', 'activePolicy(address)', target)[0]
            if ordinal_ids.count(identifier) != 1:
                raise ValueError('Ambiguous actual dual-feed policy ordinal')
            raw = read('oracle', 'policy(bytes32)', identifier, count=14)
            policy = dict(token='0x' + raw[0][-40:])
            for i, role in enumerate(('primary', 'secondary')):
                start = 1 + i * 5
                values = raw[start:start + 5]
                policy[role] = dict(source='0x' + values[0][-40:], expectedCodeHash='0x' + values[1],
                    independenceId='0x' + values[2], maxAge=int(values[3], 16), feedDecimals=int(values[4], 16))
            policy.update(maxDeviationBps=int(raw[11], 16), assetDecimals=int(raw[12], 16), reviewHash='0x' + raw[13])
            captured = price_record(dict(policy_id=identifier, ordinal=ordinal_ids.index(identifier), policy=policy),
                target, item['decimals'], c['oracle'])
            policies[target] = captured
            tokens.append(dict(address=target, code_hash=item['code_hash'], decimals=item['decimals'], price_policy=captured))
            admission = '0x' + read('activation_assets', 'activePolicy(address)', target)[0]
            sources.append(dict(pool_id=pool, source_asset=target, asset_policy_id=admission))
            input_assets.append(dict(symbol=item['symbol'], address=target, decimals=item['decimals'],
                valuation_asset=target, enabled=True, runtime_code=None if target == ZERO else runtime(target),
                price_policy_id=identifier, asset_policy_id=admission))
        keeper = read('strategy', 'keeperRangePolicy(bytes32)', pool, count=7)
        keeper_policy = dict(enabled=bool(int(keeper[0], 16)), narrow_trigger_bps=int(keeper[1], 16),
            widen_trigger_bps=int(keeper[2], 16), minimum_interval_seconds=int(keeper[3], 16),
            configuration_hash='0x' + keeper[5], review_hash='0x' + keeper[6])
        sequencer = '0x' + read('oracle', 'sequencerFeed()')[0][-40:]
        dependencies = {c[role] for role in ('pool_manager', 'state_view', 'position_manager', 'permit2')}
        if sequencer != ZERO:
            dependencies.add(sequencer)
        activation_config = dict(schema=1, routing_version=3, pricing_version=2, review_policy_version=2,
            lp_routing_version=2, portfolio_version=2, execution_quality_version=1,
            maintenance_policy_version=3, rebalance_confirmation_version=3, range_policy_version=1,
            range_policies=[dict(pool_id=pool, orientation=int(read('strategy', 'rangeOrientation(bytes32)', pool)[0], 16),
                keeper=keeper_policy)], contracts={role: pin(c[role]) for role in ACTIVATION_ROLES},
            tokens=tokens, dependencies=[pin(target) for target in sorted(dependencies)], sources=sources,
            sequencer=dict(address=sequencer, policy_id='0x' + read('oracle', 'activeSequencerPolicy()')[0]),
            call_pins=[], storage_pins=[], fee_policy=dict(estimate_includes_all_fees=True,
                review_hash=review, max_gas_price_wei=str(100 * 10**9)))
        activation_config['schema']=activation_policy['schema']
        activation_config['fee_policy'].update(activation_policy['fee_fields'])
        activation = ActivationTransactions(projection, activation_config)
        transactions = Transactions(projection, tx)
        manifest = dict(schema=4, **PROFILE, mode='read-and-prepare', environment='rehearsal', id='0' * 64,
            chain_id=chain, chain_name='PoPL isolated source9 fork', genesis_hash=genesis,
            deployment_block=low, deployment_block_hash=anchor['hash'], confirmations=confirmations,
            max_age_seconds=max_age_seconds, api_prefix='/api', rpc_url=rpc_url,
            projection_sha256=projection.identity, activation_sha256=activation.config.identity,
            transaction_sha256=transactions.config.identity, activation_fee_review=review,
            transaction_fee_review=review, pool_id=pool,
            contracts={role: dict(address=c[role], runtime_code=runtime(c[role])) for role in BROWSER_ROLES},
            input_assets=input_assets, reward_assets=[{key: a[key] for key in ('address', 'symbol', 'decimals')} for a in assets],
            limits=dict(gas=activation_policy['limit'], gas_price_wei=str(100 * 10**9), network_fee_wei=str(10**18),
                native_value_wei=str(1000 * 10**18), contribution_usd_18=str(1000000 * 10**18),
                maximum_contribution_loss_bps=200))
        manifest.update(activation_policy['manifest_fields'])
        manifest['id'] = hashlib.sha256(_json(manifest).encode()).hexdigest()
        for name, value in (('read-config.json', config), ('activation-config.json', activation_config),
                ('transaction-config.json', tx), ('configuration-observation.json', dict(chain_id=chain,
                 snapshot_block=_quantity(head['number']), snapshot_hash=head['hash'],
                 nft_creation_block=low, nft_creation_hash=anchor['hash'], public_transactions=False,
                 production_provider_qualification=False, production_approval=False))):
            evidence.save(name, value)
        if index_config:
            evidence.save('indexer-config.json', index_config)
        result = RehearsalAPI(reader, evidence, config, activation_config, tx, projection,
            activation, transactions, manifest, c, indexer, index_config)
        result.sync_history()
        return result
    except BaseException:
        if indexer is not None:
            indexer.close()
        evidence.close()
        raise


@contextmanager
def startserver(bundle, *, port=0):
    """Serve actual production DTOs plus a smaller browser read-only RPC edge."""
    parent_handler = read_handler(bundle.projection, bundle.transactions)
    activation_post = activation_handler(bundle.projection, bundle.activation).do_POST

    class Handler(parent_handler):
        def _json(self, status, value):
            payload = getattr(self, '_request_payload', None)
            raw = getattr(self, '_request_bytes', None)
            if raw is not None:
                try:
                    candidate = json.loads(raw.decode('utf-8'))
                    allowed = {'action', 'wallet', 'token_id', 'pool_id', 'source_asset',
                        'amount_in', 'slippage_bps', 'claims'}
                    payload = candidate if isinstance(candidate, dict) and not set(candidate) - allowed else {'invalid_body': True}
                except (ValueError, UnicodeError):
                    payload = {'invalid_body': True}
            bundle.evidence.http(dict(kind='api', method=self.command,
                path=getattr(self, '_original_path', self.path), status=status,
                request=payload, response=value))
            super()._json(status, value)

        def _route(self):
            self._original_path = self.path
            if self.path.startswith('/api/v1/'):
                self.path = self.path[4:]
                return True
            return False

        def do_GET(self):
            if self._route():
                super().do_GET()
            else:
                self._json(404, {'error': 'unknown_endpoint'})

        def do_POST(self):
            origin = 'http://127.0.0.1:' + str(self.server.server_address[1])
            if self.headers.get_all('Origin', []) not in ([], [origin]):
                self._json(403, {'error': 'origin_not_allowed'})
                return
            if self.path == '/rpc':
                self._rpc()
                return
            if not self._route():
                self._json(404, {'error': 'unknown_endpoint'})
                return
            handler_self = self
            original = self.rfile

            class CaptureBody:
                def read(self, size=-1):
                    data = original.read(size)
                    handler_self._request_bytes = data
                    return data

                def __getattr__(self, name):
                    return getattr(original, name)

            self.rfile = CaptureBody()
            # Production handlers own parsing, framing, work limits and DTOs.
            if self.path == '/v1/activation/prepare':
                activation_post(self)
            else:
                super().do_POST()

        def _rpc(self):
            port = self.server.server_address[1]
            if (self.headers.get_all('Host', []) != ['127.0.0.1:' + str(port)] or
                    self.headers.get_all('Transfer-Encoding') is not None or self.headers.get_all('Expect') is not None):
                self._json(400, {'error': 'invalid_rpc_request'})
                return
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not re.fullmatch(r'[1-9][0-9]{0,4}', lengths[0]) or int(lengths[0]) > 65536:
                self._json(400, {'error': 'invalid_rpc_request'})
                return
            if self.headers.get_all('Content-Type', []) != ['application/json']:
                self._json(415, {'error': 'application_json_required'})
                return
            request_id = None
            try:
                from frontend_api.activation_server import unique_object, reject_constant
                value = json.loads(self.rfile.read(int(lengths[0])).decode('utf-8'),
                    object_pairs_hook=unique_object, parse_constant=reject_constant)
                if (not isinstance(value, dict) or set(value) - {'jsonrpc', 'id', 'method', 'params'} or
                        value.get('jsonrpc') != '2.0' or type(value.get('id')) is not int or
                        value.get('method') not in BROWSER_METHODS or not isinstance(value.get('params', []), list) or
                        not _browser_params(value['method'], value.get('params', []))):
                    raise ValueError('Unsupported browser RPC request')
                request_id = value['id']
                self.begin_work()
                result = bundle.rpc.call(value['method'], value.get('params', []))
                if value['method'] == 'eth_chainId':
                    result = hex(result)
                response = dict(jsonrpc='2.0', id=request_id, result=result)
            except Exception as exc:
                response = dict(jsonrpc='2.0', id=request_id,
                    error=dict(code=-32600, message='Local read-only RPC unavailable'))
                bundle.evidence.http(dict(kind='browser_rpc_failure', error_type=type(exc).__name__))
            self._request_payload = value if 'value' in locals() else None
            self._json(200, response)

    server = ReadServer(('127.0.0.1', port), Handler, max_connections=16)
    actual_port = server.server_address[1]
    origin = 'http://127.0.0.1:' + str(actual_port)
    manifest = json.loads(_json(bundle.manifest))
    manifest['rpc_url'] = origin + '/rpc'
    manifest['id'] = hashlib.sha256(_json({**manifest, 'id': '0' * 64}).encode()).hexdigest()
    bundle.manifest = manifest
    bundle.evidence.save('website-manifest.json', manifest)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .1}, daemon=True)
    thread.start()
    edge = type('RehearsalEdge', (), dict(origin=origin, port=actual_port,
        manifest=manifest, server=server))()
    try:
        yield edge
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
