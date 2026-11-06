"""Retained actual-v4 producer vectors exercise the fresh6 math and hash wire."""
import json
from pathlib import Path
import unittest

from zzz_ops.abi import keccak256
from zzz_ops.physical_portfolio import physical_amounts,portfolio_fingerprints

ROOT=Path(__file__).resolve().parents[1]


class ResidualProducerVectorTests(unittest.TestCase):
    def test_actual_unfilled_and_mixed_outputs_match_independent_python_consumer(self):
        data=json.loads((ROOT/'reports/residual-lifecycle-20261106/actual-physical-vectors.json').read_text())
        self.assertTrue(data['successful_evm_method'])
        self.assertTrue(data['python_export_does_not_compute_expected_hashes_or_principal'])
        self.assertEqual(2,len(data['vectors']))
        identities=[];prices=[]
        for v in data['vectors']:
            with self.subTest(phase=v['phase']):
                encoded=bytes.fromhex(v['encoded_static_tuple'][2:])
                self.assertEqual(25*32,len(encoded))
                raw=bytes.fromhex(v['raw_event']['data'][2:])
                self.assertEqual(32,int.from_bytes(raw[:32],'big'))
                self.assertEqual(len(encoded),int.from_bytes(raw[32:64],'big'))
                self.assertEqual(encoded,raw[64:])
                self.assertEqual('0x'+keccak256(data['event_signature'].encode()).hex(),v['raw_event']['topics'][0])
                self.assertEqual(v['phase'],int(v['raw_event']['topics'][1],16))
                ws=[encoded[i:i+32] for i in range(0,len(encoded),32)]
                self.assertEqual(1,int.from_bytes(ws[0],'big'))
                for i,key in ((1,'executor'),(2,'position_manager'),(3,'vault')):
                    self.assertEqual(b'\0'*12,ws[i][:12]);self.assertEqual(v[key],'0x'+ws[i][12:].hex())
                self.assertEqual(v['pool_id'],'0x'+ws[4].hex())
                self.assertEqual(v['pool_id'],'0x'+keccak256(b''.join(ws[20:25])).hex())
                price=int.from_bytes(ws[11],'big');self.assertEqual(price,int(v['sqrt_price_x96']));prices.append(price)
                parsed=[]
                for key,indices in (('main',(5,7,9,14,15)),('secondary',(6,8,10,16,17))):
                    item=v[key];ii,pi,li,a0,a1=indices
                    identifier=int.from_bytes(ws[ii],'big');info=int.from_bytes(ws[pi],'big');liquidity=int.from_bytes(ws[li],'big')
                    self.assertEqual(identifier,int(item['id']));self.assertEqual(info,int(item['position_info'],16));self.assertEqual(liquidity,int(item['liquidity']))
                    ticks=[(info>>shift)&((1<<24)-1) for shift in (8,32)]
                    ticks=[t-(1<<24) if t>=(1<<23) else t for t in ticks]
                    self.assertEqual(item['ticks'],ticks)
                    expected=[int.from_bytes(ws[a0],'big'),int.from_bytes(ws[a1],'big')]
                    self.assertEqual(expected,list(map(int,item['principal_raw'])))
                    self.assertEqual(expected,physical_amounts(price,ticks,liquidity))
                    parsed.append((identifier,info,liquidity))
                stable,execution=portfolio_fingerprints(executor=v['executor'],position_manager=v['position_manager'],vault=v['vault'],pool=v['pool_id'],main=parsed[0],secondary=parsed[1])
                self.assertEqual(stable,'0x'+ws[18].hex());self.assertEqual(stable,v['stable_hash'])
                self.assertEqual(execution,'0x'+ws[19].hex());self.assertEqual(execution,v['execution_hash'])
                identities.append((stable,execution))
                amounts=list(map(int,v['secondary']['principal_raw']))
                self.assertTrue(any(a==0 for a in amounts) if v['phase']==0 else all(a>0 for a in amounts))
        self.assertNotEqual(prices[0],prices[1]);self.assertEqual(identities[0],identities[1])


if __name__=='__main__':unittest.main()
