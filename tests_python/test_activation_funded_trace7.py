"""Funded fresh7 decoding from retained actual source9 Entry3 call bytes.

The historical campaign used200bps, controlled feeds/VRF and added external
depth. Its original trace is never rewritten or relabelled as current300-bps
execution or qualified market evidence. Mutations below are synthetic hostile
RPC observations. This runs only the current profile7 decoder, with no RPC/EVM.
"""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import unittest
import zipfile

from frontend_api import activation_trace as T
from frontend_api.service import ProjectionError,ZERO
from tests_python.test_activation_actual_trace7 import (
    FIXTURE,SHA256,ORIGINAL_NORMAL,ORIGINAL_NORMAL_SHA256)
from zzz_ops.abi import calldata,decode_words

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'reports/source9-actual-entry-20261109/campaign-evidence.zip'
ARCHIVE_SHA256='903c0e572d26daaaff2ad78a27396d8b59062dda9d0249270ae6a783f553333c'
ENTRIES={
    'api-fixed-2/trace-0006.json':'7255e839c764cd4024c82f411c4b94ce5beedd4c571b63c52a7dcfdedc003c5d',
    'consumer-eth-growth-final.json':'18401669f23c764c3a7defafb6439e8c2cba62ef2682b786239bec3f7ce641d9',
    'inventory-4.json':'50586ac241a69ef9d26030e389440a1860a494f10b998ec19d453b33f480aa39',
}


class FundedEntry3Trace7Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()!=ARCHIVE_SHA256:
            raise AssertionError('Historical actual campaign archive changed')
        if hashlib.sha256(FIXTURE.read_bytes()).hexdigest()!=SHA256:
            raise AssertionError('Original profile/pin fixture changed')
        with zipfile.ZipFile(ARCHIVE)as archive:
            cls.records={}
            for name,expected in ENTRIES.items():
                raw=archive.read(name)
                if hashlib.sha256(raw).hexdigest()!=expected:
                    raise AssertionError('Historical actual funded entry changed: '+name)
                cls.records[name]=json.loads(raw)
        cls.original=json.loads(gzip.decompress(FIXTURE.read_bytes()))

    def setUp(self):
        self.call=copy.deepcopy(self.records['api-fixed-2/trace-0006.json'])
        self.root=self.call['result'];self.pins=self.original['pins']
        self.draft=self.records['consumer-eth-growth-final.json']['cases'][0]['draft']
        self.request={k:v for k,v in copy.deepcopy(self.original['request']).items()if not k.startswith('_')}
        q=[int(word,16)for word in decode_words('0x'+self.call['params'][0]['data'][10:])]
        self.assertEqual(9,len(q))
        self.request.update(id=q[0],pool='0x'+f'{q[1]:064x}',source='0x'+f'{q[2]:040x}',
            amount=q[3],minimum_lp=q[4],deadline=q[5],increase=bool(q[6]),
            maximum_loss_bps=q[7],expected_contribution_policy='0x'+f'{q[8]:064x}',
            old_lp_id=int(self.draft['liquidity_context']['lp_token_id']),
            execution_loss_bps=self.draft['execution_limit_bps'],
            upper_input_usd=int(self.draft['source_upper_usd_18']))
        self.gross=int(self.draft['source']['value_usd_18'])
        stack=[self.root];found=[]
        while stack:
            frame=stack.pop();stack.extend(frame.get('calls',[]))
            if frame.get('to')==self.pins['contribution_pricing']and frame.get('input','')[:10]==T.selector(T.FINISH_PRICING):
                found.append(frame)
        self.assertEqual(1,len(found));self.finish=found[0]
        self.epochs=[frame for frame in self.finish['calls']if frame.get('to')==self.pins['budget']and
            frame.get('input','')[:10]==T.selector('compositionEpoch(uint256)')]
        self.assertEqual(2,len(self.epochs))
        self.assertGreater(int(decode_words('0x'+self.finish['input'][10:])[2],16),0)

    def measure(self):
        return T.measure(self.root,self.call['params'][0],self.pins,self.request,
            self.gross,self.original['max_slippage_bps'])

    def test_actual_funded_source_scope_and_two_zero_epochs_are_preserved(self):
        self.assertEqual(ORIGINAL_NORMAL_SHA256,hashlib.sha256(ORIGINAL_NORMAL.read_bytes()).hexdigest())
        source=json.loads(ORIGINAL_NORMAL.read_text())['source_sha256']
        self.assertEqual(source,self.records['inventory-4.json']['production_source_validation']['source_sha256'])
        self.assertEqual(7,self.request['accounting_version'])
        self.assertTrue(self.request['increase']);self.assertEqual(200,self.request['execution_loss_bps'])
        self.assertEqual([0,0],[int(frame['output'],16)for frame in self.epochs])
        result=self.measure()
        self.assertEqual(60*10**18,result['source_usd_18'])
        self.assertEqual(int(self.draft['minimum_deployed_usd_18']),result['required_deployed_usd_18'])
        self.assertEqual(int(self.draft['simulated_lp_added_usd_18']),result['marginal_deployed_usd_18'])
        self.assertEqual(10569067,result['simulation_gas_used'])
        self.assertGreater(result['shares_added_raw'],0)
        self.assertGreaterEqual(result['lp_liquidity_added_raw'],self.request['minimum_lp'])

    def test_missing_second_epoch_cannot_reuse_first_phase(self):
        self.finish['calls'].remove(self.epochs[1])
        with self.assertRaisesRegex(ProjectionError,'Historical compound denomination'):self.measure()

    def test_duplicate_second_epoch_cannot_create_a_third_phase(self):
        self.finish['calls'].append(copy.deepcopy(self.epochs[1]))
        with self.assertRaisesRegex(ProjectionError,'historical compound epoch boundary'):self.measure()

    def test_second_epoch_change_cannot_cross_share_issuance(self):
        self.epochs[1]['output']='0x'+f'{1:064x}'
        with self.assertRaisesRegex(ProjectionError,'historical compound epoch boundary'):self.measure()

    def test_second_epoch_requires_exact_bucket_static_success_and_uint64(self):
        original=copy.deepcopy(self.epochs[1])
        for mutation in({'input':calldata('compositionEpoch(uint256)',self.request['bucket']+1)},
                {'type':'CALL'},{'output':'0x'},{'output':'0x'+f'{2**64:064x}'},{'error':'execution reverted'}):
            with self.subTest(mutation=mutation):
                self.epochs[1].clear();self.epochs[1].update(original);self.epochs[1].update(mutation)
                with self.assertRaises((ProjectionError,ValueError)):self.measure()

    def test_equal_nonzero_epochs_are_an_explicit_synthetic_funded_witness(self):
        # A same-pair custody composition can advance the epoch without adding
        # another payout currency. This is a synthetic derivative, not a newly
        # observed epoch1 execution of the historical campaign.
        for frame in self.epochs:frame['output']='0x'+f'{1:064x}'
        result=self.measure()
        self.assertEqual(int(self.draft['simulated_lp_added_usd_18']),result['marginal_deployed_usd_18'])

    def test_misordered_historical_observation_cannot_precede_first_epoch(self):
        for frame in self.epochs:frame['output']='0x'+f'{1:064x}'
        forged={'type':'STATICCALL','from':self.pins['contribution_pricing'],'to':self.pins['fees'],
            'input':calldata('compoundBalance(uint256,address)',self.request['bucket'],'0x'+'0'*36+'beef'),
            'output':'0x'+f'{0:064x}'}
        self.finish['calls'].insert(self.finish['calls'].index(self.epochs[0]),forged)
        with self.assertRaisesRegex(ProjectionError,'Invalid historical compound observation'):self.measure()

    def test_current_pair_observation_cannot_be_relabelled_historical(self):
        for frame in self.epochs:frame['output']='0x'+f'{1:064x}'
        forged={'type':'STATICCALL','from':self.pins['contribution_pricing'],'to':self.pins['fees'],
            'input':T.static_data('compoundBalance(uint256,address)',self.request['bucket'],ZERO),
            'output':'0x'+f'{0:064x}'}
        self.finish['calls'].insert(self.finish['calls'].index(self.epochs[0])+1,forged)
        with self.assertRaisesRegex(ProjectionError,'Invalid historical compound observation'):self.measure()


if __name__=='__main__':unittest.main()
