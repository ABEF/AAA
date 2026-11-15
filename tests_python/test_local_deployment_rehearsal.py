"""New isolated launcher/closed-workflow checks; no node, provider or old suites."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('local_deployment_rehearsal',ROOT/'scripts/rehearse-local-deployment.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

class LocalDeploymentRehearsalTests(unittest.TestCase):
    def test_wire_record_freezes_exact_serialized_request(self):
        class Process:
            def poll(self):return None
        class Response:
            status=200
            def __init__(self,request):self.request=request
            def read(self,maximum):return json.dumps({'jsonrpc':'2.0','id':self.request['id'],'result':'0x'if self.request['method']=='eth_call'else {'field':'original'}}).encode()
        class Connection:
            def request(self,method,path,body,headers):self.sent=body
            def getresponse(self):return Response(json.loads(self.sent))
        node=M.Node(Path('anvil.exe'),Path('unused'),{'alloc':{}});node.proc=Process();node.connection=Connection()
        tx={'from':M.SENDER,'data':'0x1234','gas':hex(M.CAP)}
        node.wire('eth_call',[tx,'latest']);sent=json.loads(node.connection.sent)
        tx['gas']='0x1';tx['nonce']='0x0';tx['gasPrice']='0x2'
        self.assertEqual(node.records[0]['request'],sent)
        self.assertEqual(node.records[0]['request']['params'][0]['gas'],hex(M.CAP))
        self.assertNotIn('nonce',node.records[0]['request']['params'][0])
        returned=node.wire('eth_getBlockByNumber',['latest',False]);returned['field']='changed'
        self.assertEqual(node.records[1]['response']['result'],{'field':'original'})

    def test_seal_and_wrong_target_refused_before_rpc(self):
        class NeverRPC:
            def guard(self):raise AssertionError('Must reject before RPC')
        case=M.Rehearsal(NeverRPC(),None,Path('.'));case.addresses={'access':M.SENDER,'protocol_policy':M.GUARDIAN}
        with self.assertRaisesRegex(ValueError,'closed allowlist'):case.transaction('seal',M.data('seal()'),M.SENDER)
        payload=M.data('bindProtocolPolicy(address)',('address',),(M.GUARDIAN,))
        with self.assertRaisesRegex(ValueError,'closed allowlist'):case.transaction('wrong',payload,M.KEEPER)

    def test_initcode_bound_refused_before_rpc(self):
        case=M.Rehearsal(None,None,Path('.'))
        with self.assertRaisesRegex(ValueError,'EIP3860'):case.transaction('create:oversize','0x'+'00'*49153)

    def test_existing_owned_folder_never_modified(self):
        with tempfile.TemporaryDirectory()as directory:
            folder=Path(directory)/'existing';folder.mkdir();marker=folder/'rpc-records.json.gz';marker.write_bytes(b'preserve')
            node=M.Node(Path('anvil.exe'),folder,{'alloc':{}})
            with self.assertRaises(FileExistsError):node.__enter__()
            self.assertEqual(marker.read_bytes(),b'preserve');self.assertEqual(sorted(x.name for x in folder.iterdir()),['rpc-records.json.gz'])

    def test_pid_guard_refuses_wrong_listener_without_rpc(self):
        class Process:
            pid=123
            def poll(self):return None
        node=M.Node(Path('anvil.exe'),Path('unused'),{'alloc':{}});node.proc=Process();node.owner=lambda:{456}
        node.wire=lambda *a,**k:self.fail('No RPC before owner proof')
        with self.assertRaisesRegex(ValueError,'exact child PID'):node.mutate('anvil_impersonateAccount',[M.SENDER])

    def test_mutation_method_and_disposable_sender_are_closed(self):
        node=M.Node(Path('anvil.exe'),Path('unused'),{'alloc':{}});node.guard=lambda:None
        node.wire=lambda *a,**k:self.fail('Invalid mutation must never reach RPC')
        with self.assertRaisesRegex(ValueError,'fixed disposable'):node.mutate('anvil_impersonateAccount',[M.KEEPER])
        with self.assertRaisesRegex(ValueError,'closed deployment'):node.mutate('anvil_setCode',[])

    def test_literal_dependency_dispatch_and_environment(self):
        code=M.selector_getters({'poolManager()':M.P.NATIVE['pool_manager'],'permit2()':M.P.NATIVE['permit2']})
        self.assertEqual(len(code),88);self.assertEqual(code[12:15],bytes.fromhex('61001e'))
        self.assertEqual(code[30:33],bytes.fromhex('5b5073'));self.assertEqual(code[59:62],bytes.fromhex('5b5073'))
        with patch.dict(M.os.environ,{'PRIVATE_KEY':'not-forwarded','RPC_URL':'not-forwarded','ANVIL_IP_ADDR':'not-forwarded'}):
            cleaned=M.env(Path('anvil.exe'));self.assertFalse({'PRIVATE_KEY','RPC_URL','ANVIL_IP_ADDR'}&cleaned.keys())

if __name__=='__main__':unittest.main()
