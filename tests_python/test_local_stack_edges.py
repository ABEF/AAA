"""Adversarial inputs/recovery for the disposable local server, no public RPC."""
import concurrent.futures
import http.client
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tests_python.test_local_stack import lab

ALICE='0x'+'11'*20
BOB='0x'+'22'*20
def envelope(action='mint',revision=0,identifier='a'*32,**kw):
    return dict(operation_id=identifier,revision=revision,payload=dict(action=action,account=ALICE,**kw))

class FakeLab:
    def __init__(self,path):
        self.home=Path(path);self.args=SimpleNamespace(website=None,port=0)
        self.accounts=['admin',ALICE,BOB];self.token='local-session';self.lock=threading.RLock()
        self.receipts=[];self.uncertain=False;self.calls=0
        self.operations=lab.OperationLedger(self.home/'operations.json')
    def action(self,payload):
        self.calls+=1
        self.receipts.append({'receipt':{'transactionHash':'0x'+'ab'*32}})
    def state(self):return {'revision':self.operations.revision,'calls':self.calls}

class OperationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=FakeLab(self.tmp.name)
    def test_bad_shapes_amounts_and_identifiers_never_execute(self):
        values=[None,[],True,1,'100',{}, {'action':[],'account':ALICE},
                {'action':'mint','account':ALICE,'amount':'100'}, {'action':'mint','account':['x']}]
        for amount in ['', '0','99','-100','+100','100.0','1e3','0x100',' 100','100 ','0100','100000','1'*200,100,True,None,[],{},'١٠٠']:
            values.append(dict(action='activate',account=ALICE,id='1',amount=amount))
        for identifier in [1,True,'0','01','-1','1e2','0x1',str(2**256),'9'*200,'<script>',None,[]]:
            values.append(dict(action='claim',account=ALICE,id=identifier))
        for payload in values:
            with self.subTest(payload=payload),self.assertRaises(ValueError):lab.validate_action(payload,[ALICE,BOB])
        self.assertEqual(self.p.calls,0)
    def test_limits_accept_canonical_boundary_values(self):
        for amount in ['100','99999']:
            lab.validate_action(dict(action='activate',account=ALICE,id=str(2**256-1),amount=amount),[ALICE])
    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in [b'{"action":"mint","action":"fund"}',b'{"n":NaN}',b'{"n":Infinity}',b'{"x":{"x":1,"x":2}}',b'\xff',b'{']:
            with self.subTest(raw=raw),self.assertRaises((ValueError,UnicodeError)):lab.parse_payload(raw)
    def test_replay_lost_response_executes_once(self):
        first=self.p.operations.run(envelope(),self.p)
        second=self.p.operations.run(envelope(),self.p)
        self.assertEqual(self.p.calls,1);self.assertTrue(second['replayed'])
        self.assertEqual(first['transactions'],second['transactions'])
        self.assertEqual(json.loads((self.p.home/'operations.json').read_text())['a'*32]['outcome']['status'],'confirmed')
    def test_same_id_different_payload_or_revision_rejected(self):
        self.p.operations.run(envelope(),self.p)
        for change in [envelope('fund'),envelope(revision=1)]:
            with self.assertRaises(lab.LocalConflict):self.p.operations.run(change,self.p)
        self.assertEqual(self.p.calls,1)
    def test_stale_tab_cannot_submit_new_intent(self):
        self.p.operations.run(envelope(),self.p)
        with self.assertRaises(lab.LocalConflict):self.p.operations.run(envelope(identifier='b'*32),self.p)
        self.assertEqual(self.p.calls,1)
    def test_failed_partial_operation_is_not_retried(self):
        def partial(payload):
            self.p.calls+=1;self.p.receipts.append({'receipt':{'transactionHash':'approval'}})
            raise RuntimeError('Entry simulation failed')
        self.p.action=partial
        result=self.p.operations.run(envelope(),self.p)
        self.assertEqual(result['status'],'failed');self.assertEqual(result['transactions'],['approval'])
        self.p.operations.run(envelope(),self.p);self.assertEqual(self.p.calls,1)
    def test_record_capacity_never_evicts_old_operation(self):
        self.p.operations.run(envelope(),self.p)
        self.p.operations.items.update({f'{n:032x}':{} for n in range(255)})
        with self.assertRaises(lab.LocalConflict):self.p.operations.run(envelope(revision=1,identifier='b'*32),self.p)
        self.assertTrue(self.p.operations.run(envelope(),self.p)['replayed'])
    def test_uncertain_submission_blocks_new_actions(self):
        self.p.uncertain=True
        with self.assertRaises(lab.LocalConflict):self.p.operations.run(envelope(),self.p)
        self.assertEqual(self.p.calls,0)
    def test_failed_intent_persistence_precedes_broadcast(self):
        with patch.object(lab,'save',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.p.operations.run(envelope(),self.p)
        self.assertEqual(self.p.calls,0)
        self.assertEqual(self.p.operations.run(envelope(),self.p)['status'],'pending')
    def test_success_is_recorded_before_projection_refresh(self):
        self.p.state=Mock(side_effect=RuntimeError('indexer unavailable'))
        self.assertEqual(self.p.operations.run(envelope(),self.p)['status'],'confirmed')
        self.p.state.assert_not_called()
    def test_record_replace_failure_preserves_previous_evidence(self):
        path=self.p.home/'record.json';lab.save(path,{'old':1})
        with patch.object(Path,'replace',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):lab.save(path,{'new':2})
        self.assertEqual(json.loads(path.read_text()),{'old':1})
        self.assertEqual(list(self.p.home.glob('*.tmp')),[])
    def test_outcome_persistence_failure_blocks_new_submission(self):
        original=lab.save
        count=0
        def write(path,data):
            nonlocal count
            count+=1
            if count==2:raise OSError('disk full')
            original(path,data)
        with patch.object(lab,'save',side_effect=write):
            with self.assertRaises(OSError):self.p.operations.run(envelope(),self.p)
        self.assertEqual(self.p.calls,1);self.assertTrue(self.p.uncertain)
        self.assertEqual(self.p.operations.run(envelope(),self.p)['status'],'confirmed')
        with self.assertRaises(lab.LocalConflict):self.p.operations.run(envelope(revision=1,identifier='b'*32),self.p)
    def test_wrong_chain_client_or_genesis_fails_closed(self):
        for chain,client,genesis in [('0x1','anvil','good'),(hex(lab.CHAIN),'geth','good'),(hex(lab.CHAIN),'anvil','wrong')]:
            p=object.__new__(lab.Lab);p.process=Mock();p.process.poll.return_value=None;p.genesis='good'
            p.rpc=lambda method,params=None:{'eth_chainId':chain,'web3_clientVersion':client,'eth_getBlockByNumber':{'hash':genesis}}[method]
            with self.assertRaises(RuntimeError):p.guard()
    def test_simulation_revert_prevents_broadcast(self):
        p=object.__new__(lab.Lab);p.guard=lambda:None;p.accounts=[ALICE]
        p.rpc=Mock(side_effect=RuntimeError('contract revert'))
        with self.assertRaises(RuntimeError):p.send({'from':ALICE},'test')
        self.assertEqual(p.rpc.call_args.args[0],'eth_call');self.assertEqual(p.rpc.call_count,1)
    def test_gas_and_native_balance_caps_prevent_submission(self):
        for responses in [['0x','0x'+format(29000001,'x')],['0x',hex(100000),hex(100),hex(1)]]:
            p=object.__new__(lab.Lab);p.guard=lambda:None;p.accounts=[ALICE];p.rpc=Mock(side_effect=responses)
            with self.assertRaises(ValueError):p.simulate({'from':ALICE})
            self.assertNotIn('eth_sendTransaction',[c.args[0] for c in p.rpc.call_args_list])
    def test_bad_operation_envelopes_never_execute(self):
        for env in [None,[],{},dict(envelope(),revision=True),dict(envelope(),revision=-1),dict(envelope(),revision='0'),dict(envelope(),operation_id='old'),dict(envelope(),extra=1)]:
            with self.assertRaises(ValueError):self.p.operations.run(env,self.p)
        self.assertEqual(self.p.calls,0)
    def test_wrong_mode_amount_and_balance_do_not_approve(self):
        p=object.__new__(lab.Lab);p.tokens=['token'];p.call=Mock()
        for active,amount,balance,increase in [(1,100,1000,False),(0,100,1000,True),(0,99,1000,False),(0,100,99,False)]:
            p.uint=lambda role,sig,*args:active if role=='vault' else balance*lab.UNIT
            with self.assertRaises(ValueError):p.contribute(ALICE,'1',amount*lab.UNIT,increase)
        p.call.assert_not_called()
    def test_wrong_owner_rejected_before_approval_or_claim(self):
        p=object.__new__(lab.Lab);p.accounts=['admin',ALICE,BOB];p.sync=Mock();p.ids=lambda:['1'];p.addr=lambda *args:BOB;p.call=Mock()
        for action in ['activate','increase','claim','transfer']:
            payload=dict(action=action,account=ALICE,id='1')
            if action in ('activate','increase'):payload['amount']='100'
            with self.assertRaisesRegex(ValueError,'does not own'):p.action(payload)
        p.call.assert_not_called()
    def test_rpc_loss_after_submission_marks_uncertain(self):
        p=object.__new__(lab.Lab);p.home=self.p.home;p.submissions=[];p.receipts=[];p.uncertain=False
        p.simulate=lambda tx:(tx,{})
        p.rpc=Mock(side_effect=['0x123',TimeoutError('response lost')])
        with self.assertRaises(TimeoutError):p.send({'from':ALICE},'test')
        self.assertTrue(p.uncertain)
        self.assertEqual(json.loads((p.home/'submissions.json').read_text())[0]['status'],'uncertain')
    def test_receipt_survives_post_transaction_balance_read_failure(self):
        p=object.__new__(lab.Lab);p.home=self.p.home;p.submissions=[];p.receipts=[];p.uncertain=False
        p.simulate=lambda tx:(tx,{})
        p.rpc=Mock(side_effect=['0x123','0xhash',{'status':'0x1','transactionHash':'0xhash'},TimeoutError('balance unavailable')])
        with self.assertRaises(TimeoutError):p.send({'from':ALICE},'test')
        self.assertEqual(p.receipts[0]['receipt']['transactionHash'],'0xhash')
        self.assertIsNone(p.receipts[0]['native_after']);self.assertFalse(p.uncertain)

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=FakeLab(self.tmp.name)
        self.server=lab.make_server(self.p);self.port=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
    def request(self,raw=None,extra=None,method='POST',path='/action'):
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=10)
        headers={'Origin':f'http://127.0.0.1:{self.port}','X-Local-Token':self.p.token,'Content-Type':'application/json'}
        if extra:headers.update(extra)
        c.request(method,path,raw,headers);r=c.getresponse();data=r.read();c.close();return r.status,json.loads(data)
    def test_strange_wire_inputs_have_no_side_effect(self):
        for raw in ['[]','null','true','42','{}','{"action":"mint","action":"fund"}','{"x":NaN}','[ '*700, '\ufffd']:
            with self.subTest(raw=raw[:40]):self.assertEqual(self.request(raw.encode())[0],400)
        self.assertEqual(self.p.calls,0)
    def test_host_origin_session_encoding_and_body_bounds(self):
        body=json.dumps(envelope()).encode()
        for headers in [{'Host':'evil.test'},{'Origin':'https://evil.test'},{'X-Local-Token':'old'},{'Content-Type':'text/plain'},{'Transfer-Encoding':'chunked'},{'Expect':'100-continue'}]:
            self.assertEqual(self.request(body,headers)[0],403)
        self.assertEqual(self.request(b'x'*2049)[0],400)
        self.assertEqual(self.p.calls,0)
    def test_duplicate_security_headers_rejected(self):
        body=json.dumps(envelope()).encode()
        for header,value in [('Host',f'127.0.0.1:{self.port}'),('Origin',f'http://127.0.0.1:{self.port}'),('X-Local-Token',self.p.token),('Content-Type','application/json'),('Content-Length',str(len(body)))]:
            c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
            c.putrequest('POST','/action',skip_host=True)
            headers={'Host':f'127.0.0.1:{self.port}','Origin':f'http://127.0.0.1:{self.port}','X-Local-Token':self.p.token,'Content-Type':'application/json','Content-Length':str(len(body))}
            for key,val in headers.items():c.putheader(key,val)
            c.putheader(header,value);c.endheaders(body);r=c.getresponse();r.read();c.close()
            self.assertIn(r.status,[400,403])
        self.assertEqual(self.p.calls,0)
    def test_traversal_unknown_path_no_rpc_relay(self):
        for path in ['/../AGENTS.md','/assets/nfts/../../AGENTS.md','/assets/nfts/%2e%2e/file.svg','/rpc']:
            self.assertEqual(self.request(method='GET',path=path)[0],404)
    def test_simultaneous_requests_do_not_queue_second_mutation(self):
        entered=threading.Event();release=threading.Event()
        original=self.p.action
        def slow(payload):entered.set();release.wait(5);original(payload)
        self.p.action=slow;body=json.dumps(envelope()).encode()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            first=pool.submit(self.request,body)
            self.assertTrue(entered.wait(5))
            try:
                self.assertEqual(self.request(body)[0],409)
                self.assertEqual(self.request(method='GET',path='/state')[0],409)
                self.assertEqual(self.request(b'{"action":"stop"}')[0],409)
            finally:release.set()
            self.assertEqual(first.result()[0],200)
        status,replay=self.request(body);self.assertTrue(replay['replayed']);self.assertEqual(self.p.calls,1)
    def test_disconnected_caller_can_recover_same_operation(self):
        body=json.dumps(envelope()).encode()
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        c.request('POST','/action',body,{'Origin':f'http://127.0.0.1:{self.port}','X-Local-Token':self.p.token,'Content-Type':'application/json'})
        # Read headers, then drop the response before using its outcome.
        c.getresponse();c.close()
        _,replay=self.request(body);self.assertTrue(replay['replayed']);self.assertEqual(self.p.calls,1)
    def test_incomplete_body_times_out_without_execution(self):
        with socket.create_connection(('127.0.0.1',self.port),timeout=8) as s:
            s.sendall((f'POST /action HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\nOrigin: http://127.0.0.1:{self.port}\r\nX-Local-Token: {self.p.token}\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{{').encode())
            self.assertIn(b'400',s.recv(4096))
        self.assertEqual(self.p.calls,0)

if __name__=='__main__':unittest.main()
