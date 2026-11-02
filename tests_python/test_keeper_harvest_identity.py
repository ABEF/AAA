"""Price-independent harvest identity proofs; inert providers and temp journals."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from keeper.monitor import Keeper
from keeper.operation_review import PinnedReads, Review, review
from tests_python.test_keeper_operation_review import ReportRPC
from tests_python.test_keeper_portfolio_policy import PortfolioRPC
from tests_python.test_keeper_policy_v6 import PolicyRPC
from zzz_ops.position import decode_position
from zzz_ops.rpc import RpcError


class KeeperHarvestIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)

    def fixture(self, kind):
        rpc=kind(Path(self.tmp.name)/(kind.__name__+'.json'))
        keeper=Keeper(rpc.cfg,rpc=rpc)
        header=rpc.call('eth_getBlockByNumber',['latest',False])
        position=decode_position(rpc.read(rpc.contracts['vault'],'group(uint256)',7,count=8),
            keeper.accounting_version)
        keeper.rpc=PinnedReads(rpc,header)
        return rpc,keeper,Review(keeper,header,False,simulate=False),position

    def test_main_packed_identity_cannot_be_ignored(self):
        for kind in (ReportRPC,PortfolioRPC,PolicyRPC):
            for fault in ('pool_prefix','subscriber_flag','packed_ticks'):
                rpc,keeper,report,position=self.fixture(kind);original=rpc.read
                def read(target,signature,*args,count=1):
                    values=list(original(target,signature,*args,count=count))
                    if target==rpc.posm and signature=='getPoolAndPositionInfo(uint256)' and args==(123,):
                        packed=int(values[5],16)
                        packed=(packed^(1<<200) if fault=='pool_prefix' else
                            (packed&~255)|2 if fault=='subscriber_flag' else packed^(1<<8))
                        values[5]=f'{packed:064x}'
                    return values
                rpc.read=read
                with self.subTest(profile=keeper.accounting_version,fault=fault),self.assertRaises((ValueError,RpcError)):
                    report.harvest_custody(position)

    def test_residual_ticks_must_match_manager_not_themselves(self):
        for kind in (PortfolioRPC,PolicyRPC):
            rpc,keeper,report,position=self.fixture(kind)
            rpc.secondary=124;rpc.secondary_count=1;original=rpc.read
            def read(target,signature,*args,count=1):
                values=list(original(target,signature,*args,count=count))
                if target==rpc.contracts['liquidity'] and signature=='ticks(uint256)' and args==(124,):
                    values[0]=f'{rpc.aux_ticks[0]+10:064x}'
                return values
            rpc.read=read
            with self.subTest(profile=keeper.accounting_version),self.assertRaises((ValueError,RpcError)):
                report.harvest_custody(position)

    def test_matching_but_impossible_geometry_is_rejected(self):
        for kind in (ReportRPC,PortfolioRPC,PolicyRPC):
            for lower,upper in ((100,-100),(-99,100),(-887280,887280),(2**24-100,100)):
                rpc,keeper,report,position=self.fixture(kind);rpc.lower=lower;rpc.upper=upper
                with self.subTest(profile=keeper.accounting_version,ticks=(lower,upper)),self.assertRaises((ValueError,RpcError)):
                    report.harvest_custody(position)

    def test_healthy_both_leg_geometry_needs_no_market_read(self):
        for kind in (ReportRPC,PortfolioRPC,PolicyRPC):
            rpc,keeper,report,position=self.fixture(kind)
            if kind is not ReportRPC:rpc.secondary=124;rpc.secondary_count=1
            original=rpc.read
            def read(target,signature,*args,count=1):
                if signature=='getSlot0(bytes32)':raise AssertionError('Harvest must not read market prices')
                return original(target,signature,*args,count=count)
            rpc.read=read
            with self.subTest(profile=keeper.accounting_version),patch('subprocess.run') as signer:
                result=report.harvest_custody(position)
                self.assertTrue(result['allowed']);signer.assert_not_called()
                self.assertEqual({'tick_lower':rpc.lower,'tick_upper':rpc.upper},result['main_ticks'])
                if kind is not ReportRPC:self.assertEqual(rpc.aux_ticks[0],result['physical_legs'][1]['tick_lower'])
                self.assertFalse(keeper.path.exists())

    def test_source6_report_preserves_harvest_through_price_fault(self):
        rpc,keeper,_,_=self.fixture(PolicyRPC);rpc.secondary=124;rpc.secondary_count=1
        keeper.save();before=keeper.path.read_bytes()
        rpc.code_overrides[rpc.contracts['state_view']]='0x6001'
        with patch('subprocess.run') as signer:
            result=review(rpc.cfg,[7],rpc=rpc,now=lambda:rpc.now)
        rows={row['operation']:row for row in result['operations']}
        self.assertEqual('observed_eligible',rows['harvest']['state'])
        self.assertEqual('unavailable',rows['compound']['state'])
        self.assertEqual(1,result['profile']['protocol_policy_version'])
        self.assertEqual(2,len(rows['harvest']['checks']['physical_custody']['value']['physical_legs']))
        self.assertEqual(before,keeper.path.read_bytes());signer.assert_not_called()
        self.assertNotIn('PRIVATE-ENDPOINT',json.dumps(result))


if __name__=='__main__':unittest.main()
