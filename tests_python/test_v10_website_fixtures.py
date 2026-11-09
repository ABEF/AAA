"""Current V10 consumer fixtures, synthetic offline RPC only."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from tests_python.v10_website_fixture import Current7Activation, USD
from frontend_api.service import ZERO
from tests_python.test_frontend_api import addr
from frontend_api.service import ProjectionError
from tests_python import export_v10_website_fixtures as E
from zzz_ops.abi import decode_words


class V10WebsiteFixturesTests(unittest.TestCase):
    def test_current7_entry3_eth_and_zzz_activation_and_growth(self):
        for increase in (False,True):
            for asset in (ZERO,addr(20)):
                with self.subTest(increase=increase,asset=asset):
                    f=Current7Activation(self,increase=increase,asset=asset)
                    result=f.service.prepare(f.request)
                    self.assertTrue(result['activation_ready'])
                    self.assertEqual(7,result['provenance']['accounting_version'])
                    self.assertEqual(3,result['provenance']['routing_version'])
                    self.assertEqual(300,result['execution_limit_bps'])
                    self.assertEqual(str(f.amount*97//100),result['minimum_deployed_usd_18'])
                    self.assertEqual(str(f.amount*99//100),result['contribution']['marginal_deployed_usd_18'])
                    self.assertEqual(2,f.trace_count)


class V10WebsiteExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exported=E.produce()

    def test_explicit_profile_and_real_handler_requests_are_source_bound(self):
        artifact=self.exported
        self.assertIn('scripts/observe-production-config.py',artifact['source_sha256'])
        self.assertEqual(hashlib.sha256((E.ROOT/'indexer/event_schema.json').read_bytes()).hexdigest(),
            artifact['data_sha256']['indexer/event_schema.json'])
        self.assertEqual(17,len(artifact['cases']))
        self.assertEqual(10,artifact['profile']['source_profile'])
        self.assertEqual(5,artifact['profile']['website_schema'])
        self.assertEqual(2,artifact['profile']['mint_integration_version'])
        for name,case in artifact['cases'].items():
            with self.subTest(case=name):
                self.assertEqual(7,case['read_configuration']['accounting_version'])
                self.assertEqual(2,case['read_configuration']['mint_integration_version'])
                self.assertNotIn('source_profile',case['read_configuration'])
                self.assertNotIn('metadata_renderer',case['read_configuration']['contracts'])
                self.assertNotIn('nft_canonical',case['read_configuration']['contracts'])
                self.assertTrue(case['api_calls'])
                self.assertTrue(all(call['handler'].startswith(('Projection.','Transactions.','ActivationTransactions.')) for call in case['api_calls']))
                self.assertTrue(all(not any(x in row['method'].lower() for x in ('send','sign','anvil')) for row in case['rpc_responses']))
                schema=[row['result'] for row in case['rpc_responses'] if row['method']=='eth_call' and
                    row['params'][0]==dict(to=case['pins']['handoff'],data=E.data('SCHEMA()'))]
                if name!='mint_use_opensea':self.assertTrue(schema);self.assertEqual({E.words(E.V10)},set(schema))
        for name,digest in artifact['source_sha256'].items():
            self.assertEqual(digest,hashlib.sha256((E.ROOT/name).read_bytes()).hexdigest(),name)
        self.assertFalse(any('actual-trace7' in name for name in artifact['source_sha256']))

    def test_all_four_current_entry_drafts_capture300_and_exact_native_value(self):
        for name in ('activation_eth','activation_zzz','growth_eth','growth_zzz'):
            case=self.exported['cases'][name];draft=case['outputs']['draft'];request=case['request']
            with self.subTest(case=name):
                self.assertTrue(draft['activation_ready'])
                self.assertEqual(300,draft['execution_limit_bps'])
                self.assertEqual(300,draft['reviewed_maximum_loss_bps'])
                self.assertEqual(7,draft['provenance']['accounting_version'])
                self.assertEqual(3,draft['provenance']['routing_version'])
                raw=decode_words('0x'+draft['transaction']['data'][10:])
                self.assertEqual(9,len(raw));self.assertEqual(300,int(raw[-2],16))
                self.assertEqual(draft['contribution_policy']['fingerprint'][2:],raw[-1])
                amount=int(request['amount_in'])
                self.assertEqual(str((amount*9700+9999)//10000),draft['minimum_deployed_usd_18'])
                self.assertEqual(str(amount*99//100),draft['contribution']['marginal_deployed_usd_18'])
                self.assertEqual(hex(amount if request['source_asset']==ZERO else 0),draft['transaction']['value'])
                self.assertEqual(2,sum(r['method']=='debug_traceCall' for r in case['rpc_responses']))
                self.assertEqual('/v1/activation/prepare',case['api_calls'][0]['path'])
                self.assertFalse(draft['network_gas']['included_in_execution_loss'])
                self.assertEqual('123',case['expected_unchanged_geometry']['main_lp_token_id'])
                if name.startswith('growth'):self.assertEqual('124',case['expected_unchanged_geometry']['residual_lp_token_id'])

    def test_zzz_approval_is_exact_and_requires_fresh_preparation(self):
        for name in ('activation_zzz_approval','growth_zzz_approval'):
            case=self.exported['cases'][name];draft=case['outputs']['draft'];amount=case['request']['amount_in']
            with self.subTest(case=name):
                self.assertEqual('approval_required',draft['kind'])
                self.assertFalse(draft['activation_ready'])
                self.assertEqual(amount,draft['approval_steps'][0]['amount_raw'])
                self.assertTrue(draft['approval_steps'][0]['reprepare_after_confirmation'])
                self.assertEqual(E.data('approve(address,uint256)',case['pins']['entry'],int(amount)),draft['transaction']['data'])
                self.assertEqual('0x0',draft['transaction']['value'])
                self.assertFalse(any(r['method']=='debug_traceCall' for r in case['rpc_responses']))

    def test_funded_original_currency_claims_and_planner_preserve_owner(self):
        for policy in (1,2):
            case=self.exported['cases']['claim_policy'+str(policy)]
            draft=case['outputs']['draft'];plan=case['outputs']['plan']
            self.assertEqual(3,len(draft['claim_operations']))
            self.assertTrue(all(int(row['view_raw'])>0 and row['view_raw']==row['simulated_raw'] for row in draft['claim_operations']))
            self.assertEqual(addr(30),draft['transaction']['from'])
            self.assertEqual(case['pins']['claim_router'],draft['transaction']['to'])
            self.assertEqual('0x0',draft['transaction']['value'])
            self.assertEqual('in_next_batch',plan['entries'][0]['status'])
            self.assertEqual(2,plan['provenance']['mint_integration_version'])
            self.assertEqual('12000000' if policy==1 else '40000000',draft['simulation']['gas_cap'])
            self.assertEqual([ZERO,ZERO,addr(21)],[row['asset'] for row in draft['claim_operations']])

    def test_history_inventory_and_checkpoint_use_real_replay_not_retagged_seed(self):
        case=self.exported['cases']['checkpoint2_earnings'];out=case['outputs']
        self.assertEqual(2,case['checkpoint_candidate']['schema'])
        self.assertEqual(addr(32),out['inventory']['wallet'])
        self.assertEqual(1,out['inventory']['count'])
        self.assertEqual(out['inventory']['token_ids'],out['wallet_summary']['token_ids'])
        for key in ('all_time','last_24h','window','event_count'):
            self.assertEqual(out['full_raw_earnings'][key],out['earnings'][key])
        self.assertTrue(any(int(row['lp_owner_allocated_raw'])+int(row['lp_collective_allocated_raw'])>0 for row in out['earnings']['all_time']))
        self.assertTrue(any(int(row['royalties_allocated_raw'])>0 for row in out['earnings']['all_time']))
        self.assertIsNone(out['earnings']['all_time_usd_at_current_price_18']['lp_owner_allocated'])
        self.assertEqual(1,sum(nft['position']['status']=='dormant' for nft in out['nfts'].values()))

    def test_unavailable_terminal_and_dormant_cases_keep_distinct_meanings(self):
        cases=self.exported['cases']
        outage=cases['price_unavailable']['outputs']['nft']
        self.assertFalse(outage['position']['current_lp_value']['available'])
        self.assertIsNone(outage['position']['current_lp_value']['raw'])
        self.assertGreater(int(outage['claimable']['lp'][0]['raw']),0)
        dormant=cases['dormant']['outputs']['nft']
        self.assertTrue(all(int(r['raw'])==0 for name in ('lp','royalties') for r in dormant['claimable'][name]))
        for name in ('principal_allocated','principal_ready','principal_paid'):
            self.assertEqual('exited',cases[name]['outputs']['nft']['position']['status'])
        mint=cases['mint_use_opensea']
        self.assertIn('Use OpenSea',mint['outputs']['error']['message'])
        self.assertEqual([],mint['rpc_responses'])

    def test_browser_only_immutable_proofs_use_actual_selectors_and_exclusive_output(self):
        case=self.exported['cases']['active_single'];proof=case['browser_proof']
        methods=[r['params'][0]['data'][:10] for r in proof['rpc_responses'] if r['method']=='eth_call']
        for signature in ('metadataRenderer()','canonicalModule()','access()','nft()','module(bytes32)','moduleAt(uint8)'):
            self.assertIn(E.data(signature,*({'module(bytes32)':('0x'+'1'*64,),'moduleAt(uint8)':(0,)}.get(signature,())))[:10],methods)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'fixture.json';digest=E.publish(target,self.exported)
            self.assertEqual(digest,hashlib.sha256(target.read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):E.publish(target,{'different':True})
            self.assertEqual(digest,hashlib.sha256(target.read_bytes()).hexdigest())
        output=os.environ.get('POPL_V10_FIXTURE_OUTPUT')
        if output:E.publish(output,self.exported)


class V10WebsiteNegativeTests(unittest.TestCase):
    def test_current7_funded_second_epoch_cannot_be_omitted(self):
        f=Current7Activation(self,increase=True)
        original=f.trace
        def incomplete(tx):
            root=original(tx)
            finish=root['calls'][1]['calls'][-1]['calls'][0]
            finish['calls'].pop()
            return root
        f.trace=incomplete
        with self.assertRaisesRegex(ProjectionError,'Historical compound denomination'):
            f.service.prepare(f.request)

    def test_v9_schema_and_lower_current_loss_do_not_create_an_accepted_draft(self):
        f=Current7Activation(self)
        f.put(f.c['handoff'],'SCHEMA()',values=('0x'+E.keccak256(b'ZZZ_CANONICAL_SAME_CHAIN_EXACT_LP_V9').hex(),))
        with self.assertRaisesRegex(ProjectionError,'schema'):f.service.prepare(f.request)
        self.assertEqual(0,f.trace_count)
        g=Current7Activation(self,loss_bps=0)
        with self.assertRaisesRegex(ProjectionError,'execution budget'):g.service.prepare(g.request)


class V10WebsiteRoundtripCompatibilityTests(unittest.TestCase):
    """Producer request/header compatibility, not actual browser acceptance."""
    @classmethod
    def setUpClass(cls):
        cls.cases={}
        for increase in (False,True):
            for asset,symbol in ((ZERO,'eth'),(addr(20),'zzz')):
                name=('growth_' if increase else 'activation_')+symbol
                cls.cases[name]=E.activation_case(increase=increase,asset=asset,residual=increase)
                if symbol=='zzz':cls.cases[name+'_approval']=E.activation_case(increase=increase,
                    asset=asset,approval=True,residual=increase)
        for policy in (1,2):cls.cases['claim_policy'+str(policy)]=E.claim_case(policy)

    def test_contribution_requests_match_shared_website_100bps_review(self):
        for name,case in self.cases.items():
            if not name.startswith(('activation_','growth_')):continue
            with self.subTest(case=name):
                self.assertEqual(100,case['request']['slippage_bps'])
                draft=case['outputs']['draft']
                self.assertEqual(300,draft['execution_limit_bps'])
                if not name.endswith('_approval'):
                    raw=decode_words('0x'+draft['transaction']['data'][10:])
                    self.assertEqual(990,int(raw[4],16))
                    self.assertEqual('0x',case['outputs']['independent_simulation'])

    def test_claim_headers_match_exact_hash_number_timestamp_and_gas_limit(self):
        for policy in (1,2):
            case=self.cases['claim_policy'+str(policy)];draft=case['outputs']['draft'];p=draft['provenance']
            rows=case['rpc_responses']
            number=[r['result'] for r in rows if r['method']=='eth_getBlockByNumber' and
                r['params']==[hex(p['block_number']),False]]
            self.assertTrue(number)
            for header in number:
                self.assertEqual((hex(p['block_number']),p['block_hash'],hex(p['block_timestamp']),hex(40_000_000)),
                    tuple(header[k] for k in ('number','hash','timestamp','gasLimit')))
            hashed=[r['result'] for r in rows if r['method']=='eth_getBlockByHash' and r['params']==[p['block_hash'],False]]
            if policy==2:
                self.assertTrue(hashed)
                for header in hashed:
                    self.assertEqual(tuple(number[0][k] for k in ('number','hash','timestamp','gasLimit')),
                        tuple(header[k] for k in ('number','hash','timestamp','gasLimit')))


if __name__=='__main__':unittest.main()
