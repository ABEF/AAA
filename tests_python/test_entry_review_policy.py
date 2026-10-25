"""Signed maximum/profile boundaries using synthetic RPC/trace fixtures only."""
import copy
import unittest
from unittest.mock import patch

from frontend_api.activation import ActivationTransactions
from frontend_api import activation_trace as T
from frontend_api.service import Projection, ProjectionError
from tests_python.test_dual_price_integration import DualActivationRPC, install, DualCompositionRPC, gate_fixture
from tests_python.test_frontend_api import configuration, words, addr
from tests_python import test_production_v2 as G
from zzz_ops import production_v2 as P, production_observer as O
from zzz_ops.abi import calldata, decode_words


class EntryReviewPolicyTests(unittest.TestCase):
    def service(self, **options):
        rpc=install(DualActivationRPC(**options));cfg=configuration();cfg['accounting_version']=2
        p=Projection(cfg,rpc,clock=lambda:1000)
        return rpc,p,ActivationTransactions(p,rpc.config)

    def test_prepared_calldata_binds_captured_cap_and_explicit_profile(self):
        for loss in (0,100,200,1000):
            with self.subTest(loss=loss):
                rpc,p,service=self.service(loss=loss)
                if loss==0:
                    # Fully lossless synthetic output, not fabricated permission
                    # to accept a nonzero loss under the zero cap.
                    values=list(rpc.economics);values[4]=values[2]+100*10**18;rpc.economics=tuple(values)
                result=service.prepare(rpc.request)
                tx=result['transaction'];values=decode_words('0x'+tx['data'][10:])
                self.assertEqual(tx['data'][:10],T.selector(T.EXECUTE_REVIEWED))
                self.assertEqual(len(values),10);self.assertEqual(int(values[-1],16),loss)
                self.assertEqual(result['execution_limit_bps'],loss)
                self.assertEqual(result['reviewed_maximum_loss_bps'],loss)
                self.assertEqual(result['provenance']['review_policy_version'],1)

    def test_old_or_implicit_dual_activation_profile_cannot_prepare_even_approval(self):
        for value in (None,0,True,2,'1'):
            rpc,p,service=self.service();config=copy.deepcopy(rpc.config);rpc.allowance=0
            if value is None:config.pop('review_policy_version')
            else:config['review_policy_version']=value
            before=len(rpc.calls)
            with self.assertRaisesRegex(ValueError,'review|Reviewed'):
                ActivationTransactions(p,config)
            self.assertEqual(len(rpc.calls),before)

    def test_wrong_or_unavailable_version_getters_fail_before_approval(self):
        for role,method in (('entry','REVIEW_POLICY_VERSION()'),('contribution_pricing','ENTRY_REVIEW_VERSION()')):
            for answer in (None,0,2):
                rpc,p,service=self.service();rpc.allowance=0
                if answer is None:rpc.responses[rpc.pins[role],calldata(method)]='0x'
                else:rpc.put(rpc.pins[role],method,values=(answer,))
                with self.assertRaises((ProjectionError,AssertionError)):
                    service.prepare(rpc.request)
                self.assertFalse(any(m=='debug_traceCall' for m,_ in rpc.calls))

    def test_trace_cannot_drop_change_or_relabel_reviewed_initializer(self):
        def alter(root):
            frame=root['calls'][0];values=decode_words('0x'+frame['input'][10:]);values[-1]=f'{1000:064x}'
            frame['input']=frame['input'][:10]+''.join(values)
        def legacy(root):
            frame=root['calls'][0];frame['input']=T.selector(T.BEGIN_ENTRY)+frame['input'][10:-64]
        for mutation in (alter,legacy):
            rpc,p,service=self.service();rpc.trace_mutation=mutation
            with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_codec_has_no_implicit_profile_or_maximum_fallback(self):
        args=(1,'0x'+'11'*32,O.ZERO,100,'0x'+'00'*32,0,1,1000,False)
        for maximum in (None,True,-1,1001,2**16):
            with self.assertRaises(ValueError):T.request_data(*args,review_policy_version=1,maximum_loss_bps=maximum)
        with self.assertRaises(ValueError):T.request_data(*args,maximum_loss_bps=100)
        for version in (True,2,'1'):
            with self.assertRaises(ValueError):T.request_data(*args,review_policy_version=version,maximum_loss_bps=100)

    def test_explicit_legacy_profile_keeps_its_original_selector_and_response_shape(self):
        from tests_python.test_frontend_activation import ActivationRPC
        rpc=ActivationRPC();p=Projection(configuration(),rpc,clock=lambda:1000)
        result=ActivationTransactions(p,rpc.config).prepare(rpc.request)
        self.assertEqual(result['transaction']['data'][:10],T.selector(T.EXECUTE))
        self.assertNotIn('reviewed_maximum_loss_bps',result)
        self.assertNotIn('review_policy_version',result['provenance'])
        self.assertNotIn('Review-policy 1',result['scope'])

    def test_production_inventory_requires_exact_current_review_bindings(self):
        valid=gate_fixture();self.assertTrue(P.validate(valid,now=G.NOW)['ready'])
        for value in (None,0,True,2):
            config=copy.deepcopy(valid)
            if value is None:config.pop('review_policy_version')
            else:config['review_policy_version']=value
            self.assertFalse(P.validate(config,now=G.NOW)['ready'])
        for role,getter in (('activation_entry','REVIEW_POLICY_VERSION'),('contribution_pricing','ENTRY_REVIEW_VERSION')):
            config=copy.deepcopy(valid);config['chains'][0]['helpers'][role]['observed_bindings'][getter]=0
            self.assertFalse(P.validate(config,now=G.NOW)['ready'])

    def test_observer_reads_versions_and_does_not_reuse_missing_success(self):
        from tests_python.test_production_observer import RUNTIME
        deps={role:(target,RUNTIME) for role,(target,_hash) in P.NATIVE_DEPENDENCIES.items()}
        with patch.object(P,'NATIVE_DEPENDENCIES',deps),patch.object(G,'HASH',RUNTIME):
            config=gate_fixture();rpc=DualCompositionRPC(config)
            target=config['chains'][0]['helpers']['activation_entry']['address']
            rpc.bad=lambda contract,data:contract==target and data==T.selector('REVIEW_POLICY_VERSION()')
            result=O.observe(config,rpc);helper=result['chains'][0]['helpers']['activation_entry']
            self.assertIsNone(helper['observed_bindings']['REVIEW_POLICY_VERSION'])
            self.assertFalse(result['chains'][0]['observation']['complete'])
            self.assertFalse(P.validate(result,now=G.NOW)['ready'])


if __name__=='__main__':unittest.main()
