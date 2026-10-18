"""Metadata notifications share the keeper's guarded transaction lifecycle."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from zzz_ops.abi import calldata, keccak256
from zzz_ops.rpc import RpcError

SENDER = '0x'+'11'*20
ACCESS = '0x'+'22'*20
VAULT = '0x'+'33'*20
NFT = '0x'+'44'*20
TX_HASH = '0x'+'ef'*32
TOKENS = [int('ab'*32,16),int('cd'*32,16),int('89'*32,16)]


def words(*values):
    return '0x'+''.join(f'{int(value):064x}' for value in values)


class MetadataRpc:
    active_url = 'https://rpc.invalid'

    def __init__(self):
        self.now = int(time.time())
        self.head = 100
        self.blocks = {}
        self.ids = TOKENS[:2]
        self.reverse = {}
        self.stages = {token:(True,2) for token in TOKENS}
        self.ready = {token:True for token in TOKENS}
        self.overrides = {}
        self.code = {}
        self.calls = []
        self.tx = self.receipt = None
        self.paused = True
        self.preparing = False
        self.canonical_state = 0
        self.simulation_error = False
        self.after_evolution = None
        self.signatures = ('access()','module(bytes32)','canonicalChainId()','MAX_SUPPLY()',
            'MAX_METADATA_REFRESH_BATCH()','mintedCount()','tokenAtOrdinal(uint256)',
            'mintOrdinalOf(uint256)','traitsReady(uint256)','evolution(uint256)',
            'paused()','preparationActive()','canonicalState()','isSealed()','keepers(address)','bucketCount()')
        self.selectors = {'0x'+keccak256(signature.encode()).hex()[:8]:signature for signature in self.signatures}

    def block_hash(self,number):
        return self.blocks.get(number,'0x'+f'{number:064x}')

    def call(self,method,params):
        self.calls.append((method,copy.deepcopy(params)))
        if method == 'eth_getBlockByNumber':
            number = self.head if params[0] == 'latest' else int(params[0],16)
            return {'number':hex(number),'timestamp':hex(self.now),'hash':self.block_hash(number)}
        if method == 'eth_getCode': return self.code.get(params[0],'0x6000')
        if method == 'eth_estimateGas': return '0x3e8'
        if method == 'eth_gasPrice': return '0x2'
        if method == 'eth_getTransactionCount': return '0x7'
        if method == 'eth_getBalance': return hex(10**18)
        if method == 'eth_getTransactionReceipt': return self.receipt
        if method == 'eth_getTransactionByHash': return self.tx
        if method != 'eth_call': raise AssertionError(method)
        tx = params[0]
        if 'from' in tx:
            if self.simulation_error: raise RpcError('simulation failed')
            return '0x'
        data,target = tx['data'],tx['to']
        signature = self.selectors.get(data[:10])
        if signature is None: raise AssertionError(data)
        if signature in self.overrides: return self.overrides[signature]
        args = [int(data[offset:offset+64],16) for offset in range(10,len(data),64)]
        if signature == 'access()': return words(int(ACCESS,16))
        if signature == 'module(bytes32)':
            return words(int(NFT if args[0] == int.from_bytes(keccak256(b'ZZZNFT'),'big') else VAULT,16))
        if signature == 'canonicalChainId()': return words(1)
        if signature == 'MAX_SUPPLY()': return words(1000)
        if signature == 'MAX_METADATA_REFRESH_BATCH()': return words(50)
        if signature == 'mintedCount()': return words(len(self.ids))
        if signature == 'tokenAtOrdinal(uint256)': return words(self.ids[args[0]-1])
        if signature == 'mintOrdinalOf(uint256)':
            return words(self.reverse.get(args[0],self.ids.index(args[0])+1))
        if signature == 'traitsReady(uint256)': return words(self.ready[args[0]])
        if signature == 'evolution(uint256)':
            result = words(*self.stages[args[0]])
            if self.after_evolution: self.after_evolution()
            return result
        return words({'paused()':int(self.paused),'preparationActive()':int(self.preparing),'canonicalState()':self.canonical_state,'isSealed()':1,'keepers(address)':1,'bucketCount()':0}[signature])

    def eth_call(self,to,data):
        return self.call('eth_call',[{'to':to,'data':data},'latest'])


class MetadataKeeperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rpc = MetadataRpc()
        self.config = {'chain_id':1,'sender':SENDER,'contracts':{'access':ACCESS,'vault':VAULT,
            'strategy':ACCESS,'fees':ACCESS,'compounder':ACCESS,'buyback':ACCESS,'pools':ACCESS},
            'state_path':str(Path(self.tmp.name)/'keeper.json'),'confirmations':2,
            'max_gas_limit':100000,'max_gas_price_wei':100,'max_transaction_cost_wei':1000000,
            'max_daily_cost_wei':10000000,'metadata_refresh':{'enabled':True,'nft':NFT}}
        self.config['code_hashes'] = {key:'0x'+keccak256(bytes.fromhex('6000')).hex()
            for key in (*self.config['contracts'],'nft')}
        self.keeper = Keeper(self.config,rpc=self.rpc)
        self.log = patch('keeper.monitor.log')
        self.log.start()
        self.addCleanup(self.log.stop)

    def live(self):
        self.keeper.live = True
        self.keeper.state['next_nonce'] = 7
        self.keeper.state['receipt_anchor'] = {'number':self.rpc.head-3,'hash':self.rpc.block_hash(self.rpc.head-3),'timestamp':self.rpc.now,'nonce':6}
        self.keeper.cast = '/mock/cast'
        self.keeper.keystore = Path('/mock/key')
        self.keeper.password = Path('/mock/password')

    def submit(self):
        self.live()
        with patch('keeper.monitor.subprocess.run',return_value=subprocess.CompletedProcess([],0,TX_HASH,'')):
            self.assertTrue(self.keeper._refresh_metadata())
        return self.keeper.state['pending']

    def receipt(self,success=True,block=100):
        pending = self.keeper.state['pending']
        self.rpc.head = block+1
        self.rpc.receipt = {'transactionHash':TX_HASH,'blockNumber':hex(block),'blockHash':self.rpc.block_hash(block),
            'status':hex(int(success)),'gasUsed':'0x64','effectiveGasPrice':'0x2',
            'from':SENDER,'to':pending['to'],'transactionIndex':'0x0'}
        self.rpc.tx = {'hash':TX_HASH,'from':SENDER,'to':pending['to'],'nonce':'0x7',
            'input':pending['data'],'value':'0x0','blockNumber':hex(block),
            'blockHash':self.rpc.block_hash(block),'transactionIndex':'0x0','gas':'0x3e8'}

    def confirmed_baseline(self):
        self.submit()
        self.receipt()
        self.assertFalse(self.keeper.poll_pending())
        self.keeper.live = False

    def capture(self):
        with patch.object(self.keeper,'submit',return_value=False) as submit:
            self.assertFalse(self.keeper._refresh_metadata())
        return submit

    def collection(self,count):
        self.rpc.ids = [int.from_bytes(keccak256(f'fairness NFT {ordinal}'.encode()),'big')
            for ordinal in range(1,count+1)]
        self.rpc.ready = {token:True for token in self.rpc.ids}
        self.rpc.stages = {token:(True,2) for token in self.rpc.ids}

    def acknowledged_scan(self):
        self.rpc.head += 1
        self.live()
        def sign(*args,**kwargs):
            state = json.loads(self.keeper.path.read_text())
            payload = state['pending']['metadata_observation']
            self.assertEqual(state['metadata_refresh']['cursor'],payload['last_ordinal'] % len(self.rpc.ids)+1)
            return subprocess.CompletedProcess([],0,TX_HASH,'')
        with patch('keeper.monitor.subprocess.run',side_effect=sign):
            self.assertTrue(self.keeper._refresh_metadata())
        payload = copy.deepcopy(self.keeper.state['pending']['metadata_observation'])
        self.receipt(block=self.rpc.head)
        self.assertFalse(self.keeper.poll_pending())
        self.keeper.live = False
        return payload

    def test_disabled_by_default_preserves_legacy_state_shape(self):
        config = copy.deepcopy(self.config)
        del config['metadata_refresh']
        keeper = Keeper(config,rpc=self.rpc)
        self.assertFalse(keeper.metadata_enabled)
        self.assertNotIn('metadata_refresh',keeper.state)
        self.assertFalse(keeper._refresh_metadata())
        self.assertEqual(self.rpc.calls,[])

    def test_dry_run_does_not_mark_notified_or_sign(self):
        with patch('keeper.monitor.subprocess.run') as signer:
            self.assertFalse(self.keeper._refresh_metadata())
        signer.assert_not_called()
        self.assertIsNone(self.keeper.state['pending'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.assertEqual(json.loads(self.keeper.path.read_text())['metadata_refresh']['notified'],{})

    def test_hashed_ids_are_discovered_but_calldata_contains_ordinals(self):
        submit = self.capture()
        args = submit.call_args.args
        self.assertEqual(args,('nft','refreshMetadataRange(uint256,uint256)',(1,2),'metadata:1:2'))
        payload = submit.call_args.kwargs['metadata_observation']
        self.assertEqual([record['token_id'] for record in payload['records']],[str(token) for token in self.rpc.ids])
        self.assertEqual(payload['observed_number'],99)
        self.assertEqual(payload['observed_hash'],self.rpc.block_hash(99))

    def test_all_metadata_getters_use_one_confirmed_block(self):
        self.capture()
        getters = [params for method,params in self.rpc.calls if method == 'eth_call']
        self.assertTrue(getters)
        self.assertTrue(all(params[1] == '0x63' for params in getters))

    def test_controller_module_vault_and_chain_bindings_fail_closed(self):
        for signature,invalid in (('access()',0),('module(bytes32)',0),('canonicalChainId()',2),
                ('isSealed()',0),('MAX_SUPPLY()',999),('MAX_METADATA_REFRESH_BATCH()',51)):
            with self.subTest(signature=signature):
                self.rpc.overrides[signature] = words(invalid)
                with patch.object(self.keeper,'submit') as submit, self.assertRaises(RpcError):
                    self.keeper._refresh_metadata()
                submit.assert_not_called()
                self.rpc.overrides.clear()

    def test_live_nft_runtime_hash_is_checked_outside_contract_map(self):
        self.assertNotIn('nft',self.keeper.contracts)
        self.live()
        self.rpc.code[NFT] = '0x6001'
        with self.assertRaises(ValueError): self.keeper._validate_code_hashes()
        with self.assertRaises(RpcError): self.keeper._refresh_metadata()

    def test_missing_nft_runtime_hash_rejected_in_live_mode(self):
        self.live()
        del self.config['code_hashes']['nft']
        with self.assertRaises(ValueError): self.keeper._refresh_metadata()

    def test_round_robin_cursor_progresses_without_false_success(self):
        self.rpc.ids = TOKENS[:]
        self.config['metadata_refresh']['max_per_cycle'] = 1
        self.keeper = Keeper(self.config,rpc=self.rpc)
        for ordinal in (1,2,3,1):
            submit = self.capture()
            self.assertEqual(submit.call_args.args[2],(ordinal,ordinal))
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})

    def test_configured_refresh_range_limit_is_respected(self):
        self.rpc.ids = TOKENS[:]
        self.keeper.metadata_batch = 2
        submit = self.capture()
        self.assertEqual(submit.call_args.args[2],(1,2))
        self.assertEqual(len(submit.call_args.kwargs['metadata_observation']['records']),2)

    def test_smaller_notification_batches_cannot_starve_unnotified_tail(self):
        self.collection(100)
        self.keeper.metadata_batch = 10
        notified = set()
        for _ in range(10):
            for ordinal in (1,51):
                token = self.rpc.ids[ordinal-1]
                self.rpc.stages[token] = (True,3 if self.rpc.stages[token][1] == 2 else 2)
            payload = self.acknowledged_scan()
            notified.update(record['ordinal'] for record in payload['records'])
        self.assertEqual(notified,set(range(1,101)))

    def test_wrapping_scan_cannot_starve_low_ordinals_behind_changing_prefix(self):
        self.collection(100)
        self.keeper.state['metadata_refresh']['cursor'] = 98
        notified = set()
        for _ in range(3):
            token = self.rpc.ids[97]
            self.rpc.stages[token] = (True,3 if self.rpc.stages[token][1] == 2 else 2)
            payload = self.acknowledged_scan()
            notified.update(record['ordinal'] for record in payload['records'])
        self.assertEqual(notified,set(range(1,101)))

    def test_invalid_flags_and_scan_limits_are_rejected(self):
        cases = (('enabled',1),('enabled','false'),('maximum_count',1001),('max_per_cycle',51),
            ('max_refresh_batch',51),('maximum_observation_age_blocks',10001),('max_per_cycle',True),
            ('maximum_count',0),('max_refresh_batch',0),('maximum_observation_age_blocks',0))
        for field,value in cases:
            with self.subTest(field=field,value=value):
                config = copy.deepcopy(self.config)
                config['metadata_refresh'][field] = value
                with self.assertRaises(ValueError): Keeper(config,rpc=self.rpc)

    def test_corrupt_minted_count_or_extra_abi_word_rejected(self):
        for response in (words(1001),words(1,2),'0x1'):
            with self.subTest(response=response):
                self.rpc.overrides['mintedCount()'] = response
                with self.assertRaises((RpcError,ValueError)): self.keeper._refresh_metadata()

    def test_corrupt_evolution_and_boolean_words_rejected(self):
        for response in (words(1),words(1,2,3),words(2,1),words(1,4),words(0,0)):
            with self.subTest(response=response):
                self.rpc.overrides['evolution(uint256)'] = response
                with self.assertRaises((RpcError,ValueError)): self.keeper._refresh_metadata()
        self.rpc.overrides.clear()
        self.rpc.overrides['traitsReady(uint256)'] = words(2)
        with self.assertRaises(RpcError): self.keeper._refresh_metadata()

    def test_wrong_ordinal_or_duplicate_token_id_rejected(self):
        self.rpc.reverse[self.rpc.ids[0]] = 2
        with self.assertRaises(RpcError): self.keeper._refresh_metadata()
        self.rpc.reverse.clear()
        self.rpc.ids[1] = self.rpc.ids[0]
        with self.assertRaises(RpcError): self.keeper._refresh_metadata()

    def test_empty_collection_has_no_notification(self):
        self.rpc.ids = []
        self.capture().assert_not_called()
        self.assertEqual(self.keeper.state['metadata_refresh']['cursor'],1)

    def test_success_updates_baseline_only_after_matching_confirmed_receipt(self):
        self.submit()
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.assertTrue(self.keeper.poll_pending())
        self.receipt()
        self.rpc.head = 100
        self.assertTrue(self.keeper.poll_pending())
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.rpc.head = 101
        self.assertFalse(self.keeper.poll_pending())
        saved = self.keeper.state['metadata_refresh']['notified']
        self.assertEqual(set(saved),{'1','2'})
        self.assertEqual(saved['1']['observed_number'],100)
        self.assertEqual(saved['1']['notification_number'],100)

    def test_receipt_snapshot_prevents_return_to_trigger_stage_from_being_suppressed(self):
        self.rpc.stages[TOKENS[0]] = (True,1)
        self.confirmed_baseline()
        self.rpc.head = 102
        self.rpc.stages[TOKENS[0]] = (True,2)
        pending = self.submit()
        original_payload = copy.deepcopy(pending['metadata_observation'])
        self.rpc.stages[TOKENS[0]] = (True,3)
        self.receipt(block=102)
        self.assertFalse(self.keeper.poll_pending())
        self.assertEqual(pending['metadata_observation'],original_payload)
        self.assertEqual(self.keeper.state['metadata_refresh']['notified']['1']['stage'],3)
        self.rpc.stages[TOKENS[0]] = (True,2)
        self.rpc.head = 104
        self.keeper.live = False
        self.assertEqual(self.capture().call_args.args[2],(1,1))

    def test_invalidated_trigger_forgets_prior_fingerprint_before_retry(self):
        self.confirmed_baseline()
        self.rpc.head = 102
        self.rpc.stages[TOKENS[0]] = (True,3)
        self.submit()
        self.rpc.stages[TOKENS[0]] = (True,1)
        self.receipt(block=102)
        self.rpc.head = 500
        self.assertFalse(self.keeper.poll_pending())
        self.assertNotIn('1',self.keeper.state['metadata_refresh']['notified'])
        self.rpc.stages[TOKENS[0]] = (True,2)
        self.keeper.live = False
        self.assertEqual(self.capture().call_args.args[2],(1,1))

    def test_corrupt_receipt_snapshot_retains_pending_without_false_checkpoint(self):
        self.confirmed_baseline()
        baseline = copy.deepcopy(self.keeper.state['metadata_refresh']['notified'])
        self.rpc.stages[TOKENS[0]] = (True,3)
        self.submit()
        self.receipt()
        self.rpc.overrides['evolution(uint256)'] = words(1)
        with self.assertRaises(RpcError): self.keeper.poll_pending()
        self.assertIsNotNone(self.keeper.state['pending'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],baseline)

    def test_pending_observations_are_durable_before_signer(self):
        self.live()
        def sign(*args,**kwargs):
            state = json.loads(self.keeper.path.read_text())
            self.assertIsNone(state['pending']['hash'])
            self.assertEqual(state['pending']['metadata_observation']['records'][0]['token_id'],str(TOKENS[0]))
            self.assertEqual(state['metadata_refresh']['notified'],{})
            return subprocess.CompletedProcess([],0,TX_HASH,'')
        with patch('keeper.monitor.subprocess.run',side_effect=sign):
            self.assertTrue(self.keeper._refresh_metadata())

    def test_unchanged_stage_and_availability_skip_notification(self):
        self.confirmed_baseline()
        self.capture().assert_not_called()

    def test_stage_increase_and_decrease_trigger_only_changed_range(self):
        self.confirmed_baseline()
        for stage in (1,3):
            with self.subTest(stage=stage):
                self.rpc.stages[TOKENS[1]] = (True,stage)
                self.assertEqual(self.capture().call_args.args[2],(2,2))

    def test_availability_change_triggers_refresh_even_with_same_stage(self):
        self.rpc.stages[TOKENS[0]] = (True,1)
        self.confirmed_baseline()
        self.rpc.stages[TOKENS[0]] = (False,1)
        self.assertEqual(self.capture().call_args.args[2],(1,1))

    def test_trait_reveal_change_is_observed_without_evolution_change(self):
        self.rpc.stages[TOKENS[0]] = (True,0)
        self.rpc.ready[TOKENS[0]] = False
        self.confirmed_baseline()
        self.rpc.ready[TOKENS[0]] = True
        self.assertEqual(self.capture().call_args.args[2],(1,1))

    def test_reverted_transaction_retries_without_advancing_baseline(self):
        self.submit()
        self.receipt(False)
        self.assertFalse(self.keeper.poll_pending())
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.keeper.live = False
        self.assertEqual(self.capture().call_args.args[2],(1,2))

    def test_simulation_failure_preserves_empty_notified_baseline(self):
        self.rpc.simulation_error = True
        with self.assertRaises(RpcError): self.keeper._refresh_metadata()
        self.assertIsNone(self.keeper.state['pending'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})

    def test_gas_and_cost_rejections_do_not_notify_or_sign(self):
        for field in ('max_gas_limit','max_gas_price_wei','max_transaction_cost_wei','max_daily_cost_wei'):
            with self.subTest(field=field):
                previous = self.config[field]
                self.config[field] = 1
                with patch('keeper.monitor.subprocess.run') as signer:
                    self.assertFalse(self.keeper._refresh_metadata())
                signer.assert_not_called()
                self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
                self.assertIsNone(self.keeper.state['pending'])
                self.config[field] = previous

    def test_ambiguous_broadcast_blocks_resubmission_and_keeps_snapshots(self):
        self.live()
        with patch('keeper.monitor.subprocess.run',side_effect=subprocess.TimeoutExpired('cast',90)) as sign:
            with self.assertRaises(subprocess.TimeoutExpired): self.keeper._refresh_metadata()
            self.assertIsNone(self.keeper.state['pending']['hash'])
            self.assertTrue(self.keeper.poll_pending())
            self.assertFalse(self.keeper._refresh_metadata())
            self.assertEqual(sign.call_count,1)
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})

    def test_wrong_transaction_identity_never_applies_snapshots(self):
        self.submit()
        self.receipt()
        self.rpc.tx['input'] = calldata('refreshMetadataRange(uint256,uint256)',2,2)
        with self.assertRaises(RpcError): self.keeper.poll_pending()
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.assertIsNotNone(self.keeper.state['pending'])

    def test_receipt_reorg_retains_pending_and_empty_baseline(self):
        self.submit()
        self.receipt()
        self.rpc.receipt['blockHash'] = '0x'+'99'*32
        self.assertTrue(self.keeper.poll_pending())
        self.assertIsNotNone(self.keeper.state['pending'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})

    def test_receipt_reorg_during_confirmation_keeps_pending(self):
        self.submit()
        self.receipt()
        original = self.rpc.call
        def call(method,params):
            result = original(method,params)
            if method == 'eth_getTransactionByHash': self.rpc.blocks[100] = '0x'+'99'*32
            return result
        self.rpc.call = call
        with self.assertRaises(RpcError): self.keeper.poll_pending()
        self.assertIsNotNone(self.keeper.state['pending'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.assertEqual(self.keeper.state['spent'],{})

    def test_reorg_after_metadata_candidate_preserves_all_state(self):
        self.submit();self.receipt()
        before = copy.deepcopy(self.keeper.state)
        disk = self.keeper.path.read_text()
        original = self.keeper._confirm_metadata
        def confirm(*args):
            records = original(*args)
            self.rpc.blocks[100] = '0x'+'99'*32
            return records
        with patch.object(self.keeper,'_confirm_metadata',side_effect=confirm):
            with self.assertRaises(RpcError): self.keeper.poll_pending()
        self.assertEqual(self.keeper.state,before)
        self.assertEqual(self.keeper.path.read_text(),disk)

    def test_confirmation_depth_lost_after_metadata_candidate_preserves_all_state(self):
        self.submit();self.receipt()
        before = copy.deepcopy(self.keeper.state)
        disk = self.keeper.path.read_text()
        original = self.keeper._confirm_metadata
        def confirm(*args):
            records = original(*args)
            self.rpc.head = 100
            return records
        with patch.object(self.keeper,'_confirm_metadata',side_effect=confirm):
            self.assertTrue(self.keeper.poll_pending())
        self.assertEqual(self.keeper.state,before)
        self.assertEqual(self.keeper.path.read_text(),disk)

    def test_failed_metadata_checkpoint_retains_baseline_pending_and_costs(self):
        self.submit();self.receipt()
        before = copy.deepcopy(self.keeper.state)
        disk = self.keeper.path.read_text()
        with patch.object(self.keeper,'save',side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.keeper.poll_pending()
        self.assertEqual(self.keeper.state,before)
        self.assertEqual(self.keeper.path.read_text(),disk)

    def test_observation_reorg_after_submission_does_not_apply_baseline(self):
        self.submit()
        self.receipt()
        self.rpc.blocks[99] = '0x'+'99'*32
        self.assertFalse(self.keeper.poll_pending())
        self.assertIsNone(self.keeper.state['pending'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})

    def test_simultaneous_observation_and_receipt_reorg_keeps_pending(self):
        self.submit()
        self.receipt()
        original = self.rpc.call
        def call(method,params):
            if method == 'eth_getBlockByNumber' and params[0] == '0x63':
                self.rpc.blocks.update({99:'0x'+'99'*32,100:'0x'+'98'*32})
            return original(method,params)
        self.rpc.call = call
        with self.assertRaises(RpcError): self.keeper.poll_pending()
        self.assertIsNotNone(self.keeper.state['pending'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.assertEqual(self.keeper.state['spent'],{})

    def test_observation_reorg_during_scan_fails_before_submission(self):
        self.rpc.after_evolution = lambda:self.rpc.blocks.update({99:'0x'+'99'*32})
        with patch.object(self.keeper,'submit') as submit, self.assertRaises(RpcError):
            self.keeper._refresh_metadata()
        submit.assert_not_called()
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})

    def test_old_observation_confirmation_is_retried(self):
        self.submit()
        self.receipt()
        self.rpc.head = 500
        self.assertFalse(self.keeper.poll_pending())
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.assertIsNone(self.keeper.state['pending'])

    def test_later_reorg_of_confirmed_baseline_triggers_new_notification(self):
        self.confirmed_baseline()
        self.rpc.blocks[100] = '0x'+'99'*32
        self.assertEqual(self.capture().call_args.args[2],(1,2))

    def test_changed_nft_or_identity_rejected_without_resetting_pending(self):
        self.submit()
        before = self.keeper.path.read_text()
        config = copy.deepcopy(self.config)
        config['metadata_refresh']['nft'] = SENDER
        with self.assertRaises(ValueError): Keeper(config,rpc=self.rpc)
        self.assertEqual(self.keeper.path.read_text(),before)
        data = json.loads(before)
        data['metadata_refresh']['identity']['chain_id'] = 2
        self.keeper.path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): Keeper(self.config,rpc=self.rpc)

    def test_disabling_feature_still_reconciles_existing_pending_snapshot(self):
        self.submit()
        self.receipt()
        config = copy.deepcopy(self.config)
        config['metadata_refresh'] = {'enabled':False}
        self.keeper = Keeper(config,rpc=self.rpc)
        self.assertFalse(self.keeper.metadata_enabled)
        self.assertFalse(self.keeper.poll_pending())
        self.assertEqual(set(self.keeper.state['metadata_refresh']['notified']),{'1','2'})
        self.assertFalse(self.keeper._refresh_metadata())

    def test_disabling_feature_preserves_ambiguous_pending_and_deployment_identity(self):
        self.submit()
        self.keeper.state['pending']['hash'] = None
        self.keeper.save()
        config = copy.deepcopy(self.config)
        config['metadata_refresh'] = {'enabled':False}
        self.keeper = Keeper(config,rpc=self.rpc)
        self.assertEqual(self.keeper.metadata_nft,NFT)
        self.assertTrue(self.keeper.poll_pending())
        self.assertIsNotNone(self.keeper.state['pending']['metadata_observation'])
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})

    def test_restart_preserves_bounded_metadata_cursor(self):
        self.config['metadata_refresh']['max_per_cycle'] = 1
        self.keeper = Keeper(self.config,rpc=self.rpc)
        self.assertEqual(self.capture().call_args.args[2],(1,1))
        self.keeper = Keeper(self.config,rpc=self.rpc)
        self.assertEqual(self.capture().call_args.args[2],(2,2))

    def test_corrupt_persisted_baseline_is_rejected_without_reset(self):
        self.confirmed_baseline()
        self.keeper.state['metadata_refresh']['notified']['1']['notification_number'] = '100'
        self.keeper.save()
        before = self.keeper.path.read_text()
        with self.assertRaises(ValueError): Keeper(self.config,rpc=self.rpc)
        self.assertEqual(self.keeper.path.read_text(),before)

    def test_tampered_pending_range_cannot_commit_other_snapshots(self):
        self.submit()
        self.receipt()
        self.keeper.state['pending']['data'] = calldata('refreshMetadataRange(uint256,uint256)',2,2)
        self.rpc.tx['input'] = self.keeper.state['pending']['data']
        with self.assertRaises(ValueError): self.keeper.poll_pending()
        self.assertEqual(self.keeper.state['metadata_refresh']['notified'],{})
        self.assertEqual(self.keeper.state['spent'],{})

    def test_metadata_notifications_remain_available_during_strategy_pause(self):
        self.rpc.paused = True
        with patch.object(self.keeper,'submit',return_value=True) as submit:
            self.keeper.cycle()
        self.assertEqual(submit.call_args.args[0],'nft')

    def test_metadata_priority_alternates_with_pool_maintenance(self):
        with patch.object(self.keeper,'_refresh_metadata',return_value=True) as metadata, \
             patch.object(self.keeper,'_bucket_batch',return_value=[]) as pools:
            self.keeper.cycle()
            pools.assert_not_called()
            self.keeper.cycle()
            pools.assert_called_once()
            self.assertEqual(metadata.call_count,2)


if __name__ == '__main__': unittest.main()
