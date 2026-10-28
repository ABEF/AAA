"""Actual conversion workers reject malformed/unconfirmed temporal cutoffs."""
import copy
import unittest
from unittest.mock import patch

from tests_python import test_keeper_conversion_integrity as fixtures
from zzz_ops.abi import calldata, keccak256


class ConversionHeaderIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.ConversionBooleanIntegrityTests('runTest')

    def malformed(self,keeper,rpc,worker,tag,field,value,*,missing=False):
        before=copy.deepcopy(keeper.state)
        original=rpc.call
        def call(method,params):
            result=original(method,params)
            if method=='eth_getBlockByNumber' and params[0]==tag:
                if field is None:return value
                result=dict(result)
                if missing:result.pop(field,None)
                else:result[field]=value
            return result
        with patch.object(rpc,'call',side_effect=call),patch.object(keeper,'submit') as submit, \
                patch('keeper.monitor.log') as log:
            self.assertFalse(keeper._convert_rewards(worker))
        submit.assert_not_called()
        self.assertEqual(1,keeper.blocked_actions)
        self.assertEqual(worker.key+'_deferred',log.call_args.args[0])
        # Reject malformed admission before cursor advancement as well as funds.
        self.assertEqual(before,keeper.state)
        self.assertIsNone(keeper.state['pending'])

    def test_latest_header_requires_canonical_object_number_timestamp_hash(self):
        for profile in fixtures.PROFILES:
            for lp in (False,True):
                for field,value in ((None,None),('number',True),('number',100),('number','0x064'),
                        ('timestamp',None),('timestamp',True),('timestamp',0),('timestamp','0x0'),
                        ('hash',None),('hash','0x'+'0'*64)):
                    with self.subTest(profile=profile,lp=lp,field=field,value=value), \
                            self.f.lab(profile,lp) as (keeper,rpc,worker):
                        self.malformed(keeper,rpc,worker,'latest',field,value)

    def test_confirmed_header_requires_canonical_object_number_timestamp_hash(self):
        for profile in fixtures.PROFILES:
            for lp in (False,True):
                for field,value in ((None,None),('number',True),('number','0x63'),
                        ('timestamp',None),('timestamp',True),('timestamp',100000),('timestamp','0x0'),
                        ('hash',None),('hash','0x'+'0'*64)):
                    with self.subTest(profile=profile,lp=lp,field=field,value=value), \
                            self.f.lab(profile,lp) as (keeper,rpc,worker):
                        self.malformed(keeper,rpc,worker,'0x62',field,value)

    def test_missing_confirmed_timestamp_defers_before_advancing_cursor(self):
        with self.f.lab('v4_native') as (keeper,rpc,worker):
            self.malformed(keeper,rpc,worker,'0x62','timestamp',None,missing=True)

    def test_confirmed_cutoff_cannot_be_future_relative_to_latest(self):
        for profile in fixtures.PROFILES:
            for lp in (False,True):
                with self.subTest(profile=profile,lp=lp),self.f.lab(profile,lp) as (keeper,rpc,worker):
                    self.malformed(keeper,rpc,worker,'0x62','timestamp',hex(rpc.now+1))

    def test_fresh_head_must_retain_confirmation_depth_and_timestamp_order(self):
        for profile in fixtures.PROFILES:
            for lp in (False,True):
                for latest in ((98,100000),(100,99999)):
                    with self.subTest(profile=profile,lp=lp,latest=latest), \
                            self.f.lab(profile,lp) as (keeper,rpc,worker), \
                            patch.object(keeper,'_head',return_value=latest),patch.object(keeper,'submit') as submit, \
                            patch('keeper.monitor.log') as log:
                        self.assertFalse(keeper._convert_rewards(worker))
                        submit.assert_not_called();self.assertEqual(1,keeper.blocked_actions)
                        self.assertEqual(worker.key+'_deferred',log.call_args.args[0])
                        self.assertIsNone(keeper.state['pending'])

    def test_healthy_workers_keep_exact_floors_and_existing_rpc_work(self):
        for profile in fixtures.PROFILES:
            for lp in (False,True):
                with self.subTest(profile=profile,lp=lp),self.f.lab(profile,lp) as (keeper,rpc,worker), \
                        patch.object(keeper,'submit',return_value=False) as submit:
                    self.assertFalse(worker.scan_once())
                    args=submit.call_args.args[2]
                    expected=(29701 if lp else 19801) if profile=='v4_native' else (29700 if lp else 19800)
                    self.assertEqual((rpc.asset,[1,2,3] if lp else [1,2],rpc.route,expected,100180),args)
                    self.assertEqual({'maximum_cost':expected//100},submit.call_args.kwargs)
                    # One deliberate extra head check after the price quote.
                    self.assertEqual(6,len([1 for method,_ in rpc.calls if method=='eth_getBlockByNumber']))
                    self.assertEqual(0,keeper.blocked_actions)

    def post_quote(self,keeper,rpc,worker,late_head):
        from keeper.royalties import native_quote
        quoted=False;original=rpc.call
        amount=300 if worker.lp else 200
        data=native_quote(rpc.asset,amount) if worker.native_v4 else calldata('quote(address,address,uint256)',
            rpc.asset,keeper.contracts[worker.wrapper],amount)
        def call(method,params):
            nonlocal quoted
            result=original(method,params)
            if method=='eth_call' and params[0]['to']==keeper.contracts['oracle'] and params[0]['data']==data:
                quoted=True
            return result
        return patch.object(rpc,'call',side_effect=call),patch.object(keeper,'_head',
            side_effect=lambda:late_head if quoted else (100,rpc.now))

    def test_post_quote_head_must_retain_depth_and_fresh_nonfuture_cutoff(self):
        for profile in fixtures.PROFILES:
            for lp in (False,True):
                for late in ((98,100000),(100,100301),(100,99999)):
                    with self.subTest(profile=profile,lp=lp,late=late),self.f.lab(profile,lp) as (keeper,rpc,worker):
                        quote,head=self.post_quote(keeper,rpc,worker,late)
                        with quote,head,patch.object(keeper,'submit',return_value=False) as submit,patch('keeper.monitor.log'):
                            self.assertFalse(keeper._convert_rewards(worker))
                        submit.assert_not_called();self.assertEqual(1,keeper.blocked_actions)
                        self.assertIsNone(keeper.state['pending'])

    def test_valid_post_quote_head_refreshes_deadline_at_exact_age_boundary(self):
        for lp in (False,True):
            for late in ((101,100007),(101,100300)):
                with self.subTest(lp=lp,late=late),self.f.lab('v4_native',lp) as (keeper,rpc,worker):
                    quote,head=self.post_quote(keeper,rpc,worker,late)
                    with quote,head,patch.object(keeper,'submit',return_value=False) as submit:
                        self.assertFalse(worker.scan_once())
                    self.assertEqual(late[1]+180,submit.call_args.args[2][-1])
                    self.assertEqual(0,keeper.blocked_actions)

    def test_low_amount_path_keeps_one_fresh_head_read_without_quote(self):
        with self.f.lab('v4_native') as (keeper,rpc,worker):
            worker.routes[0]['minimum_source_units']=1000
            original=keeper._head
            with patch.object(keeper,'_head',side_effect=original) as head,patch.object(keeper,'submit') as submit:
                self.assertFalse(worker.scan_once())
            self.assertEqual(1,head.call_count);submit.assert_not_called()
            self.assertEqual(4,len([1 for method,_ in rpc.calls if method=='eth_getBlockByNumber']))

    def test_existing_300_second_age_boundary_is_exact(self):
        for age in (300,301):
            with self.subTest(age=age),self.f.lab('v4_native') as (keeper,rpc,worker):
                original=rpc.call
                def call(method,params):
                    result=original(method,params)
                    return {**result,'timestamp':hex(rpc.now-age)} if method=='eth_getBlockByNumber' and params[0]=='0x62' else result
                with patch.object(rpc,'call',side_effect=call),patch.object(keeper,'submit',return_value=False) as submit, \
                        patch('keeper.monitor.log'):
                    self.assertFalse(keeper._convert_rewards(worker))
                self.assertEqual(age==300,submit.called)
                self.assertEqual(int(age==301),keeper.blocked_actions)

    def test_healthy_disabled_paths_do_not_add_fresh_head_dependency(self):
        for profile in fixtures.PROFILES:
            for lp in (False,True):
                for signature in ('enabled()','routeEnabled(bytes32)'):
                    with self.subTest(profile=profile,lp=lp,signature=signature), \
                            self.f.lab(profile,lp) as (keeper,rpc,worker), \
                            patch.object(keeper,'_head',side_effect=AssertionError('disabled path')) as fresh, \
                            patch.object(keeper,'submit') as submit:
                        args=() if signature=='enabled()' else (rpc.route,)
                        rpc.values[keeper.contracts[worker.converter],calldata(signature,*args)]=0
                        self.assertFalse(worker.scan_once())
                        submit.assert_not_called();fresh.assert_not_called()
                        self.assertEqual(2,len([1 for method,_ in rpc.calls if method=='eth_getBlockByNumber']))

    def test_malformed_conversion_snapshot_does_not_block_independently_due_harvest(self):
        from keeper.royalties import RoyaltyAutomation
        from tests_python import test_keeper_harvest_isolation as harvest
        from tests_python import test_typed_v4_conversion_keeper as native
        h=harvest.KeeperHarvestIsolationTests('runTest');h.setUp();self.addCleanup(h.doCleanups)
        n=native.TypedV4ConversionKeeperTests('runTest');n.setUp();self.addCleanup(n.doCleanups)
        k,rpc=h.k,h.rpc;n.rpc.now=rpc.now;h.f.rebalance=False
        names=('royalties','royalty_converter','royalty_nft','oracle','royalty_v4_executor')
        for name in names:
            k.contracts[name]=n.cfg['contracts'][name];k.config.setdefault('code_hashes',{})[name]=n.cfg['code_hashes'][name]
        k.config['royalty_conversion']=copy.deepcopy(n.cfg['royalty_conversion'])
        for name,signature in (('royalties','canonicalController()'),('royalty_converter','access()'),('royalty_nft','access()')):
            n.rpc.values[k.contracts[name],calldata(signature)]=int(k.contracts['access'],16)
        module_values={calldata('module(bytes32)','0x'+keccak256(key.encode()).hex()):int(k.contracts[name],16)
            for key,name in (('ZZZNFT','royalty_nft'),('ZZZOracle','oracle'))}
        n.rpc.canonical_access=k.contracts['access']
        original=rpc.call
        def call(method,params):
            if method=='eth_getBlockByNumber' and params[0]=='0x62':
                return {**original(method,params),'timestamp':None}
            if method=='eth_getCode' and params[0] in {k.contracts[name] for name in names}:
                return n.rpc.call(method,params)
            if method=='eth_call' and 'from' not in params[0]:
                if params[0]['to'] in {k.contracts[name] for name in names}:return n.rpc.call(method,params)
                if params[0]['to']==k.contracts['access'] and params[0]['data'] in module_values:
                    return '0x'+f'{module_values[params[0]["data"]]:064x}'
            return original(method,params)
        k.royalties=RoyaltyAutomation(k);k.state['conversion_turn']=1
        with patch.object(rpc,'call',side_effect=call),patch.object(k,'submit',return_value=True) as submit, \
                patch('keeper.monitor.time.time',side_effect=lambda:rpc.now),patch('keeper.monitor.log'):
            k.cycle()
        submit.assert_called_once_with('vault','collectFees(uint256,uint256)',(7,rpc.now+180),'harvest:7')
        self.assertEqual(1,k.blocked_actions);self.assertIsNone(k.state['pending'])


if __name__=='__main__':unittest.main()
