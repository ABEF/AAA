import unittest
from unittest.mock import Mock
from types import SimpleNamespace
from scripts.local_inputs import input_for, input_tx, EMPTY, ZERO
from scripts.local_wallet import LocalWallet, UNIT
from tests_python import test_local_wallet as fixtures
A=fixtures.A

class InputsTests(unittest.TestCase):
    def setUp(self):
        fixtures.WalletTests.setUp(self)
        self.lab.input_assets=[dict(symbol=s,address=a,decimals=d,route_id=r,enabled=True) for s,a,d,r in
            [('ZZZ','zzz',18,EMPTY),('USDG','usdg',6,'route-g'),('USDC','usdc',6,'route-c'),('ETH',ZERO,18,EMPTY)]]
        self.lab.weth='wrapper'

    # Existing generic-input cases are covered by WalletTests, not inherited here.
    def test_four_input_routes_bind_decimals_source_and_exact_approval(self):
        self.lab.uint.side_effect=lambda role,sig,*args: 0 if sig in ('nftBucket(uint256)','allowance(address,address)') else 100000*UNIT
        for symbol,address,precision in [('ZZZ','zzz',18),('USDG','usdg',6),('USDC','usdc',6)]:
            draft=self.wallet.prepare(dict(action='activate',account=A,id='1',amount='100',asset=symbol))
            self.assertEqual(draft['transaction']['to'],address)
            self.assertEqual(draft['approval_raw'],str(100*10**precision))
            self.assertEqual(draft['contribution_asset'],symbol)
            self.assertEqual(draft['minimum_lp_usd_18'],str(99*UNIT))
        self.lab.send.assert_not_called()

    def test_native_wrap_is_separate_and_does_not_activate(self):
        self.lab.uint.return_value=0
        payload=dict(action='activate',account=A,id='1',amount='100',asset='ETH')
        wrapped=self.wallet.prepare(payload)
        self.assertEqual(wrapped['action'],'wrap');self.assertEqual(wrapped['transaction']['to'],'wrapper')
        self.assertEqual(int(wrapped['transaction']['value'],16),100*UNIT)
        self.wallet.execute(dict(account=A,draft_id=wrapped['draft_id']))
        self.lab.uint.side_effect=lambda role,sig,*args: 100*UNIT if sig=='balanceOf(address)' else 0
        approval=self.wallet.prepare(payload)
        self.assertEqual(approval['action'],'approve');self.assertEqual(approval['transaction']['to'],'wrapper')
        self.assertEqual(len(self.lab.send.call_args_list),1)

    def test_wrong_asset_no_silent_fallback_or_native_alias(self):
        for symbol in ['WETH','OTHER','usdc','',None]:
            if symbol is None:continue # omitted means the explicit legacy/default fixture selection
            with self.assertRaises(ValueError):input_for(self.lab,symbol)
        self.lab.input_assets[0]['enabled']=False
        with self.assertRaises(ValueError):input_for(self.lab,'ZZZ')

    def test_nonzero_allowance_resets_then_exact_amount(self):
        self.lab.uint.side_effect=lambda role,sig,*args: 0 if sig=='nftBucket(uint256)' else 1 if sig=='allowance(address,address)' else 1000*UNIT
        draft=self.wallet.prepare(dict(action='activate',account=A,id='1',amount='100',asset='USDG'))
        self.assertEqual(draft['approval_raw'],'0')
        self.lab.encode.assert_called_with('approve(address,uint256)','entry',0)

    def test_conversion_has_decimal_aware_amount_and_nonzero_minimum(self):
        input_tx(self.lab,A,'1',100,False,'USDC')
        data=self.lab.encode.call_args.args[1]
        self.assertIn(',usdc,100000000,route-c,99000000000000000000,',data)
