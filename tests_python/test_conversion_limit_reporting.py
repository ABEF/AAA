"""Explicit converter-generation reporting; no missing-getter fallback."""
import copy
import unittest
from unittest.mock import patch

from frontend_api.service import Projection, ProjectionError
from tests_python.test_frontend_api import MockRPC, configuration, addr, words
from tests_python.test_royalty_reporting import profile
from zzz_ops.abi import calldata
from zzz_ops.errors import RpcError


class ConversionLimitReportingTests(unittest.TestCase):
    def setUp(self):
        self.rpc=MockRPC();self.cfg=profile(configuration(),self.rpc)
        self.cfg['royalty_reporting']['schema']=2
        self.rpc.put(addr(90),'MAX_LOSS_BPS()',values=(1000,))
        self.rpc.put(addr(90),'conversionLossBps()',values=(100,))

    def read(self):
        return Projection(self.cfg,self.rpc,clock=lambda:1000).nft(str(self.rpc.nft_id))['royalty_reporting']

    def test_explicit_schema_two_reads_current_governed_limit_and_hard_ceiling(self):
        for cap in (0,100,250,1000):
            self.rpc.put(addr(90),'conversionLossBps()',values=(cap,));result=self.read()
            self.assertEqual(result['schema'],2);converter=result['converter']
            self.assertTrue(converter['available']);self.assertEqual(converter['maximum_execution_loss_bps'],cap)
            self.assertEqual(converter['hard_maximum_execution_loss_bps'],1000)
            self.assertEqual(converter['loss_policy'],'governed');self.assertTrue(converter['gas_separate'])
            self.assertIsNone(converter['next_execution_at'])

    def test_schema_one_cannot_describe_new_governed_converter_as_fixed_one_percent(self):
        self.cfg['royalty_reporting']['schema']=1
        result=self.read()['converter'];self.assertFalse(result['available'])
        self.assertNotIn('maximum_execution_loss_bps',result)

    def test_schema_two_does_not_accept_historical_fixed_module(self):
        self.rpc.put(addr(90),'MAX_LOSS_BPS()',values=(100,))
        self.assertFalse(self.read()['converter']['available'])

    def test_missing_operating_getter_is_unavailable_not_a_default_cap(self):
        original=self.rpc.call
        def fail(method,args):
            if method=='eth_call' and args[0]['to']==addr(90) and args[0]['data']==calldata('conversionLossBps()'):
                raise RpcError('missing getter')
            return original(method,args)
        with patch.object(self.rpc,'call',side_effect=fail):result=self.read()['converter']
        self.assertFalse(result['available']);self.assertEqual(result['reason'],'converter_verification_unavailable')
        self.assertNotIn('maximum_execution_loss_bps',result)

    def test_oversized_cap_or_malformed_getter_rejects(self):
        self.rpc.put(addr(90),'conversionLossBps()',values=(1001,))
        self.assertFalse(self.read()['converter']['available'])
        self.rpc.responses[addr(90),calldata('conversionLossBps()')]=words(100,200)
        self.assertFalse(self.read()['converter']['available'])

    def test_unknown_schema_and_boolean_schema_are_rejected(self):
        for schema in (True,0,3,'2'):
            cfg=copy.deepcopy(self.cfg);cfg['royalty_reporting']['schema']=schema
            with self.assertRaises(ValueError):Projection(cfg,self.rpc,clock=lambda:1000)


if __name__=='__main__':unittest.main()
