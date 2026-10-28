"""Inert recorded-confirmation reads; no transactions, signer or live provider."""
import copy
import unittest

from frontend_api.activation import ActivationTransactions
from frontend_api.service import ProjectionError
from tests_python.test_execution_quality_profile import quality_service
from tests_python.test_liquidity_context_policy2 import market
from tests_python.test_frontend_api import addr
from zzz_ops.abi import calldata

IDENTITY='0x'+'ab'*32
ZERO_HASH='0x'+'00'*32


def setup_confirmation(*,gap=300,first=90,last=800,ready=True,manual=False,raw=True):
    rpc,projection,_=quality_service()
    helper=addr(93);rpc.codes[helper]='0x600093';rpc.pins['rebalance_confirmation']=helper
    rpc.config['rebalance_confirmation_version']=1
    rpc.config['contracts']['rebalance_confirmation']=dict(address=helper,code_hash=rpc.digest(helper))
    for role in ('strategy','budget'):
        rpc.put(rpc.pins[role],'REBALANCE_CONFIRMATION_VERSION()',values=(1,))
    rpc.put(rpc.pins['strategy'],'rebalanceConfirmation()',values=(helper,))
    values={'REBALANCE_CONFIRMATION_VERSION()':1,'MAX_DURATION()':604800,
        'access()':rpc.pins['access'],'strategy()':rpc.pins['strategy'],
        'duration()':900,'maxObservationGap()':gap,'policyRevision()':2,
        'reviewHash()':IDENTITY if gap else ZERO_HASH}
    for signature,value in values.items():rpc.put(helper,signature,values=(value,))
    market(rpc,120 if raw and not manual else 0,pending=manual,eligible=raw)
    condition=(0,ZERO_HASH,1) if manual else (2,IDENTITY,0) if raw else (0,ZERO_HASH,0)
    rpc.put(helper,'condition(uint256)',(rpc.bucket,),condition)
    rpc.put(helper,'observations(uint256)',(rpc.bucket,),
        (IDENTITY,first,last,2) if first else (ZERO_HASH,0,0,0))
    rpc.put(helper,'ready(uint256)',(rpc.bucket,),(int(ready),))
    rpc.put(rpc.pins['strategy'],'rebalanceReady(uint256)',(rpc.bucket,),(int(ready),))
    return rpc,projection,ActivationTransactions(projection,rpc.config)


class ConfirmationAPITests(unittest.TestCase):
    def test_raw_due_and_fifteen_minute_sampled_ready_are_separate(self):
        rpc,_p,service=setup_confirmation()
        result=service.prepare(rpc.request)
        c=result['liquidity_context'];proof=c['rebalance_confirmation']
        self.assertTrue(c['rebalance']['raw_eligible_at_snapshot'])
        self.assertTrue(c['rebalance']['eligible_at_snapshot'])
        self.assertEqual('ready',proof['status'])
        self.assertEqual(900,proof['duration_seconds'])
        self.assertFalse(proof['continuous_price_proof'])
        self.assertEqual(1,result['provenance']['rebalance_confirmation_version'])
        self.assertIsNone(c['rebalance']['expected_execution_at'])

    def test_live_window_reports_remaining_time_without_promising_execution(self):
        rpc,_p,service=setup_confirmation(first=400,last=800,ready=False)
        result=service.prepare(rpc.request)['liquidity_context']
        self.assertEqual('confirmation_pending',result['rebalance']['status'])
        self.assertTrue(result['rebalance']['raw_eligible_at_snapshot'])
        self.assertFalse(result['rebalance']['eligible_at_snapshot'])
        # The reviewed snapshot is timestamp990; the RPC wall clock is1000.
        self.assertEqual(310,result['rebalance_confirmation']['seconds_remaining'])
        self.assertIn('further timely observations',result['rebalance']['explanation'])

    def test_unconfigured_policy_is_not_invented_as_a_confirmed_buffer(self):
        rpc,_p,service=setup_confirmation(gap=0,first=0,last=0,ready=False)
        c=service.prepare(rpc.request)['liquidity_context']
        self.assertEqual('confirmation_unconfigured',c['rebalance']['status'])
        self.assertFalse(c['rebalance_confirmation']['configured'])

    def test_stale_or_replaced_record_does_not_announce_eligibility(self):
        for replaced in (False,True):
            with self.subTest(replaced=replaced):
                rpc,_p,service=setup_confirmation(last=500,ready=False)
                if replaced:rpc.put(rpc.pins['rebalance_confirmation'],'observations(uint256)',
                    (rpc.bucket,),('0x'+'cd'*32,100,800,2))
                c=service.prepare(rpc.request)['liquidity_context']
                self.assertEqual('confirmation_not_started' if replaced else 'confirmation_stale',c['rebalance']['status'])
                self.assertFalse(c['rebalance']['eligible_at_snapshot'])
                self.assertIsNone(c['rebalance_confirmation']['earliest_confirmation_at'])

    def test_manual_range_exception_remains_explicit(self):
        rpc,_p,service=setup_confirmation(gap=0,first=0,last=0,manual=True)
        c=service.prepare(rpc.request)['liquidity_context']
        self.assertEqual('manual_range_exception',c['rebalance_confirmation']['status'])
        self.assertTrue(c['rebalance']['eligible_at_snapshot'])
        self.assertTrue(c['rebalance']['range_update_pending'])

    def test_inside_range_does_not_reuse_an_old_outside_timer(self):
        rpc,_p,service=setup_confirmation(raw=False,ready=False)
        c=service.prepare(rpc.request)['liquidity_context']
        self.assertEqual('raw_not_due',c['rebalance_confirmation']['status'])
        self.assertEqual('waiting_for_range_exit',c['rebalance']['status'])
        self.assertFalse(c['rebalance']['eligible_at_snapshot'])

    def test_fabricated_early_or_stale_readiness_is_rejected(self):
        for first,last in ((400,800),(100,500)):
            with self.subTest(first=first,last=last):
                rpc,_p,service=setup_confirmation(first=first,last=last,ready=True)
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_policy_binding_versions_and_half_window_bound_are_checked(self):
        cases=(('strategy','REBALANCE_CONFIRMATION_VERSION()',0),
            ('budget','REBALANCE_CONFIRMATION_VERSION()',2),
            ('rebalance_confirmation','strategy()',addr(999)),
            ('rebalance_confirmation','access()',addr(999)),
            ('rebalance_confirmation','MAX_DURATION()',604801),
            ('rebalance_confirmation','duration()',59),
            ('rebalance_confirmation','maxObservationGap()',451),
            ('rebalance_confirmation','policyRevision()',1<<64),
            ('rebalance_confirmation','reviewHash()',ZERO_HASH))
        for role,signature,value in cases:
            with self.subTest(role=role,signature=signature,value=value):
                rpc,_p,service=setup_confirmation();rpc.put(rpc.pins[role],signature,values=(value,))
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_contradictory_helper_strategy_and_direction_reads_fail_closed(self):
        for method,values in (('condition(uint256)',(1,IDENTITY,0)),
                ('condition(uint256)',(0,ZERO_HASH,1)),('ready(uint256)',(0,)),
                ('observations(uint256)',(IDENTITY,800,700,2)),
                ('observations(uint256)',(IDENTITY,100,1001,2))):
            with self.subTest(method=method):
                rpc,_p,service=setup_confirmation()
                rpc.put(rpc.pins['rebalance_confirmation'],method,(rpc.bucket,),values)
                with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_confirmation_reads_use_one_canonical_block(self):
        rpc,_p,service=setup_confirmation();service.prepare(rpc.request)
        reads=[params for method,params in rpc.calls if method=='eth_call' and
            params[0]['to']==rpc.pins['rebalance_confirmation']]
        self.assertGreater(len(reads),8)
        self.assertTrue(all(params[1]=={'blockHash':rpc.hash,'requireCanonical':True} for params in reads))

    def test_missing_read_never_falls_back_to_raw_eligibility(self):
        rpc,_p,service=setup_confirmation()
        rpc.responses[rpc.pins['rebalance_confirmation'],calldata('ready(uint256)',rpc.bucket)]='0x'
        with self.assertRaises(ProjectionError):service.prepare(rpc.request)

    def test_old_explicit_profile_never_probes_confirmation_getters(self):
        rpc,_p,service=quality_service();service.prepare(rpc.request)
        selector=calldata('rebalanceConfirmation()')
        self.assertFalse(any(method=='eth_call' and params[0]['data']==selector for method,params in rpc.calls))

    def test_bad_or_incomplete_configuration_profile_is_rejected(self):
        for version in (True,None,2,'1'):
            with self.subTest(version=version):
                rpc,p,_service=setup_confirmation();rpc.config['rebalance_confirmation_version']=version
                with self.assertRaises(ValueError):ActivationTransactions(p,rpc.config)
        rpc,p,_service=setup_confirmation();del rpc.config['contracts']['rebalance_confirmation']
        with self.assertRaises(ValueError):ActivationTransactions(p,rpc.config)

    def test_common_reader_requires_canonical_abi_words_from_every_caller(self):
        from zzz_ops.rebalance_confirmation import observe
        for malformed in ('1',' 1','0x'+'0'*63+'1','0'*63,1,True,None,'g'*64):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(ValueError,'Malformed rebalance-confirmation word'):
                    observe(lambda *args,**kw:[malformed],strategy=addr(1),budget=addr(2),
                            confirmation=addr(3),access=addr(4))

    def test_paused_activation_stops_before_any_confirmation_read(self):
        from frontend_api.activation import ActivationInputError
        rpc,_p,service=setup_confirmation();rpc.put(rpc.pins['access'],'paused()',values=(1,))
        with self.assertRaises(ActivationInputError):service.prepare(rpc.request)
        self.assertFalse(any(method=='eth_call' and params[0]['to']==rpc.pins['rebalance_confirmation']
                             for method,params in rpc.calls))
