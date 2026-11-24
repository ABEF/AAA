"""NEW snapshot1 capture/decode checks; no Node, network, compiler or old test bodies."""
from pathlib import Path
import hashlib
import importlib.util
import sys
import unittest

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

class SnapshotProfileChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(HERE))
        cls.capture=load('snapshot_wire_capture',HERE/'snapshot_wire_capture.py')
        cls.driver=load('snapshot_driver_for_new_checks',HERE/'replay_snapshot_profile.py')
        cls.node=load('snapshot_node_for_new_checks',HERE/'snapshot_node.py')
        cls.limit=16*1024*1024
        target=2*cls.limit
        empty={'jsonrpc':'2.0','id':1,'result':'0x'}
        available=target-len(cls.capture.encode(empty))
        cls.response={'jsonrpc':'2.0','id':1,'result':'0x'+'00'*(available//2)}
        raw=cls.capture.encode(cls.response)
        cls.raw=raw+b' '*(target-len(raw))
        if len(cls.raw)!=target:raise AssertionError('Large response fixture size differs')

    def test_exact_true_dump_accepts_32m_and_retains_only_authenticated_metadata(self):
        c=self.capture.WireCapture();q={'jsonrpc':'2.0','id':1,'method':'anvil_dumpState','params':[True]}
        record=c.add(q,self.response,self.raw)
        self.assertEqual(len(c.records),1)
        self.assertNotIn('result',record['response'])
        self.assertEqual(record['response']['result_hex_characters'],len(self.response['result']))
        self.assertEqual(record['response_sha256'],hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(len(c.encoded()),c.retained)
        self.assertLess(c.retained,4096)
        self.assertEqual(self.capture.verify_wire_capture(c.document())['records'],1)
        self.assertEqual(self.capture.CAPTURE_BYTES,64*1024*1024)

    def test_true_dump_over_32m_refuses_atomically_before_recording(self):
        c=self.capture.WireCapture();initial=c.retained
        q={'jsonrpc':'2.0','id':1,'method':'anvil_dumpState','params':[True]}
        with self.assertRaisesRegex(ValueError,'Local snapshot response exceeds32MiB'):
            c.add(q,self.response,self.raw+b' ')
        self.assertEqual(c.records,[]);self.assertEqual(c.blobs,{})
        self.assertEqual(c.retained,initial)

    def test_every_other_method_or_parameter_form_keeps_16m_ceiling(self):
        marker=object()
        variants=[('anvil_dumpState',marker),('anvil_dumpState',None),('anvil_dumpState',[]),
                  ('anvil_dumpState',[False]),('anvil_dumpState',[1]),('anvil_dumpState',(True,)),
                  ('anvil_dumpState',[True,True]),('eth_call',[True])]
        for method,params in variants:
            with self.subTest(method=method,form=repr(params)if params is not marker else 'omitted'):
                q={'jsonrpc':'2.0','id':1,'method':method}
                if params is not marker:q['params']=params
                c=self.capture.WireCapture();initial=c.retained
                with self.assertRaisesRegex(ValueError,'Local response exceeds16MiB'):
                    c.add(q,self.response,self.raw)
                self.assertEqual(c.records,[]);self.assertEqual(c.retained,initial)

    def test_large_snapshot_does_not_bypass_existing_request_bound(self):
        c=self.capture.WireCapture();initial=c.retained
        q={'jsonrpc':'2.0','id':1,'method':'anvil_dumpState','params':[True],'padding':'x'*(128*1024)}
        with self.assertRaisesRegex(ValueError,'Capture request/response differs'):
            c.add(q,self.response,self.raw)
        self.assertEqual(c.records,[]);self.assertEqual(c.blobs,{})
        self.assertEqual(c.retained,initial)

    def test_strict_decoder_accepts_empty_uppercase_and_mixed_hex_values(self):
        for value,expected in [('0x',b''),('0x00',b'\x00'),('0xAaFf01',b'\xaa\xff\x01'),('0xabcdef',b'\xab\xcd\xef')]:
            with self.subTest(value=value):self.assertEqual(self.driver.decode_dump_hex(value),expected)

    def test_strict_decoder_refuses_wrong_types_prefixes_odd_digits_and_invalid_unicode(self):
        class StringSubclass(str):pass
        values=[None,False,1,b'0x00',StringSubclass('0x00'),'00','0X00','0x0','0xzz','0x+0','0x００','0x☃☃']
        for value in values:
            with self.subTest(kind=type(value).__name__,short=repr(value)):
                with self.assertRaisesRegex(ValueError,'Malformed owned state encoding'):
                    self.driver.decode_dump_hex(value)

    def test_strict_decoder_rejects_all_ascii_whitespace_accepted_by_fromhex(self):
        for whitespace in [' ','\t','\n','\r','\v','\f']:
            for value in ['0x'+whitespace*2,'0x00'+whitespace*2,'0x00'+whitespace*2+'11']:
                with self.subTest(whitespace=repr(whitespace),length=len(value)):
                    with self.assertRaisesRegex(ValueError,'Malformed owned state encoding'):
                        self.driver.decode_dump_hex(value)

    def test_strict_decoder_preserves_exact_16m_compressed_limit_and_refuses_overflow(self):
        value='0x'+'00'*self.limit
        decoded=self.driver.decode_dump_hex(value)
        self.assertEqual(len(decoded),self.limit)
        self.assertEqual(decoded[:4],b'\x00'*4);self.assertEqual(decoded[-4:],b'\x00'*4)
        del decoded
        with self.assertRaisesRegex(ValueError,'Compressed export bound'):
            self.driver.decode_dump_hex(value+'00')

    def test_new_node_composes_new_capture_while_original_capture_identity_stays_original(self):
        self.assertIs(self.node.WireCapture,self.capture.WireCapture)
        self.assertEqual(self.capture.RESPONSE_BYTES,self.limit)
        self.assertEqual(self.node.LIMIT,self.limit)
        self.assertEqual(self.driver.LIMIT,self.limit)
        self.assertEqual(self.driver.EXPANDED_STATE_LIMIT,128*1024*1024)
        old=hashlib.sha256((HERE/'wire_capture.py').read_bytes()).hexdigest()
        self.assertEqual(old,'07a5fd2f578d2c244d73e12e8004d6209c3103ff46da34aa72ecae445a28e566')
        self.assertEqual(self.driver.ORIGINAL_CAPTURE_SHA,old)
        self.assertEqual(self.driver.CAPTURE_SHA,hashlib.sha256((HERE/'snapshot_wire_capture.py').read_bytes()).hexdigest())

if __name__=='__main__':unittest.main(verbosity=2)
