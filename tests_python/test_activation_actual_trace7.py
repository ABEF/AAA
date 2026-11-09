"""Literal source-bound Entry3 trace regression; no RPC or transaction replay."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import unittest

from frontend_api.activation_trace import FINISH_PRICING, measure, selector
from frontend_api.service import ProjectionError
from zzz_ops.abi import calldata, decode_words


ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests_python/fixtures/source9-entry3-actual-trace7.json.gz'
SHA256='893b369933f5946ada87a6cf6fc845f7489d9361ac55ffac7f3c954cda95cf6f'


class ActualEntry3Trace7Tests(unittest.TestCase):
    def setUp(self):
        self.fixture=json.loads(gzip.decompress(FIXTURE.read_bytes()))
        self.call=self.fixture['actual_trace_call']
        self.root=self.call['result'];self.pins=self.fixture['pins']
        self.request={k:v for k,v in copy.deepcopy(self.fixture['request']).items() if not k.startswith('_')}
        stack=[self.root];found=[]
        while stack:
            frame=stack.pop();stack.extend(frame.get('calls',[]))
            if frame.get('to')==self.pins['contribution_pricing'] and frame.get('input','')[:10]==selector(FINISH_PRICING):
                found.append(frame)
        self.assertEqual(1,len(found));self.finish=found[0]
        self.epochs=[frame for frame in self.finish['calls'] if frame.get('to')==self.pins['budget'] and
            frame.get('input','')[:10]==selector('compositionEpoch(uint256)')]
        self.assertEqual(1,len(self.epochs))

    def measured(self):
        return measure(self.root,self.call['params'][0],self.pins,self.request,
            self.fixture['gross_usd_18'],self.fixture['max_slippage_bps'])

    def test_actual_raw_trace_and_production_source_scope_are_frozen(self):
        self.assertEqual(SHA256,hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(56,len(self.fixture['contract_source_sha256']))
        for name,digest in self.fixture['contract_source_sha256'].items():
            self.assertEqual(digest,hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),name)
        self.assertNotIn('error',self.root)
        self.assertEqual(0,int(decode_words('0x'+self.finish['input'][10:])[2],16))
        self.assertEqual(0,int(self.epochs[0]['output'],16))

    def test_actual_new_bucket_epoch_zero_preserves_exact_marginal_lp_and_shares(self):
        self.assertEqual(self.fixture['expected_measurement'],self.measured())
        self.assertGreater(self.fixture['expected_measurement']['marginal_deployed_usd_18'],98*10**18)
        self.assertEqual(11204520,self.fixture['expected_measurement']['simulation_gas_used'])

    def test_missing_actual_epoch_witness_cannot_be_treated_as_zero(self):
        self.finish['calls'].remove(self.epochs[0])
        with self.assertRaises(ProjectionError):self.measured()

    def test_duplicate_epoch_witness_is_not_a_fresh_bucket_phase(self):
        self.finish['calls'].append(copy.deepcopy(self.epochs[0]))
        with self.assertRaises(ProjectionError):self.measured()

    def test_nonzero_epoch_without_incumbent_shares_is_rejected(self):
        self.epochs[0]['output']='0x'+f'{1:064x}'
        with self.assertRaises(ProjectionError):self.measured()

    def test_wrong_epoch_bucket_cannot_supply_the_historical_boundary(self):
        self.epochs[0]['input']=calldata('compositionEpoch(uint256)',self.request['bucket']+1)
        with self.assertRaises(ProjectionError):self.measured()

    def test_epoch_must_be_successful_static_and_canonical_uint64(self):
        original=copy.deepcopy(self.epochs[0])
        for mutation in ({'type':'CALL'},{'output':'0x'},{'output':'0x'+f'{2**64:064x}'},
                {'error':'execution reverted'}):
            with self.subTest(mutation=mutation):
                self.epochs[0].clear();self.epochs[0].update(original);self.epochs[0].update(mutation)
                with self.assertRaises(ProjectionError):self.measured()

    def test_new_bucket_cannot_invent_historical_compound_after_epoch_zero(self):
        self.finish['calls'].append(dict(type='STATICCALL',**{'from':self.pins['contribution_pricing']},
            to=self.pins['fees'],input=calldata('compoundBalance(uint256,address)',self.request['bucket'],self.request['token1']),
            output='0x'+f'{1:064x}'))
        with self.assertRaises(ProjectionError):self.measured()


if __name__=='__main__':unittest.main()
