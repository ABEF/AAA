import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch

SPEC=importlib.util.spec_from_file_location('fork_runner',Path(__file__).resolve().parents[1]/'scripts/run-fork-checks.py')
RUNNER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(RUNNER)
UPSTREAM='https://archive.invalid/path'
def request(method='eth_getStorageAt',request_id=7):
    return json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':['0x'+'11'*20,'0x0','0x344ef1d']}).encode()
def response(request_id=7,**fields):return json.dumps({'jsonrpc':'2.0','id':request_id,**fields}).encode()
class Clock:
    def __init__(self):self.now=100.0;self.waits=[]
    def __call__(self):return self.now
    def sleep(self,seconds):self.waits.append(seconds);self.now+=seconds

class ForkRelayTests(unittest.TestCase):
    def setUp(self):self.clock=Clock();self.calls=[];self.replies=[(200,response(result='0x42'))]
    def post(self,body):
        self.calls.append((self.clock(),body))
        reply=self.replies.pop(0)
        if isinstance(reply,Exception):raise reply
        return reply
    def relay(self,upstream=UPSTREAM):return RUNNER.Relay(upstream,post=self.post,clock=self.clock,sleep=self.clock.sleep)
    def test_forwards_exact_request_block_tag_id_and_result_bytes(self):
        body=request();expected=self.replies[0][1]
        self.assertEqual(self.relay().handle(body),(200,expected));self.assertEqual(self.calls[0][1],body)
        self.assertEqual(json.loads(self.calls[0][1])['params'][-1],'0x344ef1d')
    def test_forwards_string_ids_and_jsonrpc_error_without_retry(self):
        upstream_error=response('abc',error={'code':-32000,'message':'historical state unavailable'})
        self.replies=[(200,upstream_error)]
        self.assertEqual(self.relay().handle(request(request_id='abc')),(200,upstream_error));self.assertEqual(len(self.calls),1)
    def test_confirmed_fork_environment_gas_price_read_is_forwarded(self):
        body=json.dumps({'jsonrpc':'2.0','id':7,'method':'eth_gasPrice','params':[]}).encode()
        self.assertEqual(self.relay().handle(body)[0],200);self.assertEqual(self.calls[0][1],body)
    def test_denies_write_sign_admin_wallet_and_unknown_methods(self):
        relay=self.relay()
        for method in ('eth_sendRawTransaction','eth_sendTransaction','eth_sign','personal_sign','wallet_sendCalls','admin_addPeer','unknown'):
            with self.subTest(method=method):
                status,body=relay.handle(request(method));self.assertEqual(status,403);self.assertEqual(json.loads(body)['id'],7)
                self.assertIn(method,json.loads(body)['error']['message'])
        self.assertFalse(self.calls)
    def test_invalid_method_identifiers_are_never_echoed(self):
        for method in ('https://user:secret@rpc.invalid/path','private value with spaces','x'*65):
            with self.subTest(method=method):
                status,body=self.relay().handle(request(method));self.assertEqual(status,403)
                self.assertNotIn(method.encode(),body);self.assertIn('invalid',json.loads(body)['error']['message'])
    def test_malformed_batch_or_oversized_requests_never_reach_upstream(self):
        for body in (b'broken',b'[]',b'{}',b'\xff',b'x'*(RUNNER.MAX_REQUEST+1),
            json.dumps({'jsonrpc':'2.0','id':True,'method':'eth_call','params':[]}).encode()):
            with self.subTest(length=len(body)):self.assertNotEqual(self.relay().handle(body)[0],200)
        self.assertFalse(self.calls)
    def test_serial_cadence_is_enforced_with_fake_clock(self):
        self.replies=[(200,response(result='0x42'))]*3;relay=self.relay()
        for _ in range(3):self.assertEqual(relay.handle(request())[0],200)
        self.assertEqual([stamp for stamp,_ in self.calls],[100.0,101.25,102.5])
        self.assertEqual(self.clock.waits,[1.25,1.25])
    def test_only_429_retries_are_bounded_and_keep_original_request(self):
        self.replies=[(429,b'limited'),(429,b'limited'),(200,response(result='0x42'))]
        body=request();self.assertEqual(self.relay().handle(body)[0],200)
        self.assertEqual(len(self.calls),3);self.assertTrue(all(sent==body for _,sent in self.calls))
        self.assertEqual(self.clock.waits,[6,12])
    def test_persistent_429_fails_after_three_attempts_without_fallback(self):
        self.replies=[(429,b'limited')]*3
        status,body=self.relay().handle(request());self.assertEqual(status,429);self.assertEqual(len(self.calls),3)
        self.assertIn('three attempts',json.loads(body)['error']['message'])
    def test_http_and_transport_failures_are_not_retried_or_leaked(self):
        for reply in ((500,UPSTREAM.encode()),OSError(UPSTREAM)):
            with self.subTest(reply=type(reply).__name__):
                self.replies=[reply];self.calls=[];status,body=self.relay().handle(request())
                self.assertGreaterEqual(status,400);self.assertNotIn(UPSTREAM.encode(),body);self.assertEqual(len(self.calls),1)
    def test_oversized_malformed_and_wrong_identity_responses_fail(self):
        for reply in (b'x'*(RUNNER.MAX_RESPONSE+1),b'not json',response(8,result='0x42'),response(result='0x42',error={} )):
            with self.subTest(length=len(reply)):
                self.replies=[(200,reply)];self.assertEqual(self.relay().handle(request())[0],502)
    def test_boolean_response_ids_do_not_alias_integer_request_ids(self):
        for request_id,reply_id in ((1,True),(0,False)):
            with self.subTest(request_id=request_id):
                self.replies=[(200,response(reply_id,result='0x42'))]
                self.assertEqual(self.relay().handle(request(request_id=request_id))[0],502)
    def test_rpc_error_containing_upstream_credentials_is_suppressed(self):
        upstream='https://user:privatevalue@archive.invalid/path?key=secret-query'
        self.replies=[(200,response(error={'code':-1,'message':'rejected secret-query'}))]
        status,body=self.relay(upstream).handle(request());self.assertEqual(status,502);self.assertNotIn(b'secret-query',body)
    def test_empty_insecure_invalid_upstream_and_invalid_cadence_are_rejected(self):
        for upstream in (None,'','http://remote.invalid','https://','file:///tmp/archive','https://archive.invalid:bad'):
            with self.subTest(upstream=upstream),self.assertRaises(ValueError):self.relay(upstream)
        for interval in (0,1.0,True,float('nan')):
            with self.subTest(interval=interval),self.assertRaises(ValueError):RUNNER.Relay(UPSTREAM,interval=interval)

# Parser/status tests use historical signature-only data in an isolated TEMP root.
# These empty declarations are unit-test inputs, never runnable fork assertions or
# current candidate qualification. They do not restore a retired repository suite.
HISTORICAL_FORK_UNIT_NAMES = {'test/UniswapV4Fork.t.sol': ['testPinnedSelectedPoolIdentityAndZeroCoreFees',
                              'testCurrentRegistryRejectsSelectedNativeAndHookedPool',
                              'testRealPositionMintIncreaseAndApprovalReset',
                              'testRealSwapFeeCollectionAndPositionBurn',
                              'testActualTokenTransferBurnAndNativeWrapRoundTrip',
                              'testActualETHUSDFeedIsPositiveAndCurrentAtPinnedBlock',
                              'testRealNativeAndZZZPaymentsFundNFTClaimsWithoutChangingLP',
                              'testRealSharedPoolEntryUsesOneLPAndPostSwapSharePricing',
                              'testRealSharedPoolRebalanceChangesOneLPAndPreservesAllShares'],
 'test/NativePoolFork.t.sol': ['testSelectedNativeAccountingKeepsRealPoolKey',
                               'testSelectedNativeMintIncreaseAndClose',
                               'testSelectedNativeBothSwapDirectionsUseNetOutput',
                               'testSelectedNativeSwapAccruesActualLPFeesWithoutCreatorPayments',
                               'testSelectedNativePrefundsCannotBecomePrincipalOrFees',
                               'testSelectedNativeReopenAtAnotherRangeKeepsPoolIdentity',
                               'testSelectedNativeChangedRuntimeDisablesAdmissionAndAccounting',
                               'testSelectedNativeNoLongerDependsOnPonsHookOrItsPayoutSettings',
                               'testSelectedNativeProtocolFeeObservationDoesNotTrapCustody',
                               'testSelectedNativeReportedWrapperImplementationChangeFailsClosed',
                               'testSelectedNativeWrapperAdminOwnershipChangeFailsClosed',
                               'testSelectedNativeReviewedWrapperUpgradeRestoresSameAssetAndCustody',
                               'testSelectedNativeReviewedRenouncedWrapperAdminRestoresCustody',
                               'testSelectedNativeEntryETHActivationBindsOriginalOwnerAndGrossBudget',
                               'testSelectedNativeEntryZZZActivationDeploysAtLeastNinetyNinePercent',
                               'testSelectedNativeEntryNativeAndZZZTopUpsPreserveOneLPAndMarginalBudget',
                               'testSelectedNativeEntryFailedLiquidityGuardRollsBackOwnerFundsAndVenue',
                               'testSelectedNativeTwoNFTsShareOneLPAndFundedRewards',
                               'testSelectedNativeOneBucketRebalancePreservesBothNFTShares',
                               'testSelectedNativeApprovedRangeUpdateUsesRealTriggerAndPreservesClaims',
                               'testSelectedNativeDisabledSourceVaultMigrationRetainsPriceGuard',
                               'testSelectedNativeStaleOracleBlocksVaultExitUntilReviewedFeedReplacement',
                               'testSelectedNativePausedParkingWorksWithStaleFeedsAndBrokenCreatorInbox',
                               'testSelectedNativeParkingMinimaExcludeCompoundAndUnattributedVaultDonations',
                               'testSelectedNativeParkedResumeRequiresFreshFeedsAndPreservesAttachedShares',
                               'testSelectedNativeRejectsHookDynamicWrongTokenAndUninitializedMarkets',
                               'testSelectedNativeMoveFundsToWETHAndNewNativeFeeTierKeepsRights',
                               'testSelectedNativeExitToRegularAddressConvertsOnlyPrincipalToZZZ',
                               'testSelectedNativeRawExitWorksWithoutFeedOrEnabledPool']}

class HistoricalForkInventoryFixture(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='popl-historical-fork-unit-')
        self.addCleanup(temporary.cleanup)
        fixture_root=Path(temporary.name)
        for source,names in HISTORICAL_FORK_UNIT_NAMES.items():
            target=fixture_root/source;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text('// Historical parser fixture; not executable qualification.\n'+
                'contract HistoricalInventory {\n'+
                ''.join('function '+name+'() public {}\n' for name in names)+'}\n',encoding='utf-8')
        root_patch=patch.object(RUNNER,'ROOT',fixture_root)
        root_patch.start();self.addCleanup(root_patch.stop)

class ForkProcessTests(HistoricalForkInventoryFixture):
    def setUp(self):
        super().setUp()
        self.servers=[];self.commands=[];self.spawn_failure=False
        self.code=9;self.output='';self.stderr=''
    def server(self,relay):
        outer=self
        class FakeServer:
            url='http://127.0.0.1:12345'
            started=False;closed=False
            def start(self):self.started=True
            def close(self):self.closed=True
        result=FakeServer();outer.servers.append(result);return result
    def spawn(self,command,**kwargs):
        self.commands.append((command,kwargs))
        if '--version' in command:
            return subprocess.CompletedProcess(command,0,'forge Version: 1.4.4-v1.4.4\nCommit SHA: '+RUNNER.FORGE_COMMIT+'\n','')
        if self.spawn_failure:raise OSError('upstream secret must not enter runner logs')
        return subprocess.CompletedProcess(command,self.code,self.output,self.stderr)
    def test_exit_code_and_loopback_fork_environment_are_forwarded_then_closed(self):
        code=RUNNER.run_fork(UPSTREAM,forge='/reviewed/forge',run=self.spawn,server_factory=self.server)
        self.assertEqual(code,9);self.assertTrue(self.servers[0].started);self.assertTrue(self.servers[0].closed)
        command,options=self.commands[-1]
        self.assertEqual(command,['/reviewed/forge','test','--match-contract','^(UniswapV4ForkTest|NativePoolForkTest)$','--threads','1','--no-storage-caching','-vvv','--json'])
        self.assertEqual(options['env']['ROBINHOOD_RPC_URL'],self.servers[0].url)
        self.assertEqual(options['env']['RUN_ROBINHOOD_FORK_TESTS'],'true')
        self.assertTrue(options['capture_output']);self.assertTrue(options['text'])
    def test_successful_complete_run_forwards_both_streams_and_checks_inventory(self):
        self.code=0;self.output=json.dumps(complete_results());self.stderr='compiler diagnostic\n'
        stdout=io.StringIO();stderr=io.StringIO()
        with patch.object(sys,'stdout',stdout),patch.object(sys,'stderr',stderr):
            code=RUNNER.run_fork(UPSTREAM,run=self.spawn,server_factory=self.server)
        self.assertEqual(code,0);self.assertTrue(self.servers[0].closed)
        self.assertIn(self.output,stdout.getvalue());self.assertIn('38 successful source tests, zero skips',stdout.getvalue())
        self.assertEqual(stderr.getvalue(),self.stderr)
    def test_filtered_green_run_is_rejected_and_relay_closed(self):
        self.code=0;results=complete_results();results[RUNNER.FORK_SUITES[1]]['test_results'].popitem()
        self.output=json.dumps(results)
        with patch.dict('os.environ',{'FOUNDRY_MATCH_TEST':'only_one_test','ROBINHOOD_ARCHIVE_RPC_URL':UPSTREAM,
                'ETH_RPC_URL':'https://other.invalid','ETH_RPC_HEADERS':'secret','ETH_RPC_JWT_SECRET':'secret'}), \
                patch.object(sys,'stdout',io.StringIO()),self.assertRaises(ValueError):
            RUNNER.run_fork(UPSTREAM,run=self.spawn,server_factory=self.server)
        self.assertTrue(self.servers[0].closed)
        environment=self.commands[-1][1]['env']
        for name in ('ROBINHOOD_ARCHIVE_RPC_URL','ETH_RPC_URL','ETH_RPC_HEADERS','ETH_RPC_JWT_SECRET'):
            self.assertNotIn(name,environment)
    def test_subprocess_failure_always_closes_relay(self):
        self.spawn_failure=True
        with self.assertRaises(OSError):RUNNER.run_fork(UPSTREAM,run=self.spawn,server_factory=self.server)
        self.assertTrue(self.servers[0].closed)
    def test_unpinned_forge_never_starts_relay(self):
        run=lambda command,**kwargs:subprocess.CompletedProcess(command,0,'forge Version: 1.5.0\n','')
        with self.assertRaises(ValueError):RUNNER.run_fork(UPSTREAM,run=run,server_factory=self.server)
        self.assertFalse(self.servers)
    def test_main_preserves_forge_failure_exit_status(self):
        with patch.object(sys,'argv',['run-fork-checks.py','--upstream',UPSTREAM]),patch.object(RUNNER,'run_fork',return_value=9):
            self.assertEqual(RUNNER.main(),9)
    def test_main_reports_incomplete_results_as_failure_without_private_exception(self):
        stderr=io.StringIO()
        with patch.object(sys,'argv',['run-fork-checks.py','--upstream',UPSTREAM]), \
                patch.object(RUNNER,'run_fork',side_effect=ValueError('private upstream value')),patch.object(sys,'stderr',stderr):
            self.assertEqual(RUNNER.main(),1)
        self.assertIn('both selected suites',stderr.getvalue());self.assertNotIn('private upstream value',stderr.getvalue())

def complete_results():
    return {suite:{'test_results':{name+'()':{'status':'Success'}
        for name in RUNNER.expected_tests(suite.split(':',1)[0])}} for suite in RUNNER.FORK_SUITES}

class RetiredForkQualificationTests(unittest.TestCase):
    def test_missing_native_fixture_blocks_before_relay_forge_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'test/UniswapV4Fork.t.sol'
            source.parent.mkdir();source.write_text('contract HistoricalInventory {}',encoding='utf-8')
            run=Mock();relay=Mock();server=Mock();errors=io.StringIO()
            with patch.object(RUNNER,'ROOT',root),patch.object(sys,'stderr',errors):
                code=RUNNER.run_fork(UPSTREAM,run=run,relay_factory=relay,server_factory=server)
            self.assertEqual(code,2)
            run.assert_not_called();relay.assert_not_called();server.assert_not_called()
            self.assertIn('Fork qualification blocked',errors.getvalue())
            self.assertIn('test/NativePoolFork.t.sol',errors.getvalue())
            self.assertIn('No RPC or Forge process was started',errors.getvalue())
            self.assertNotIn(UPSTREAM,errors.getvalue())
    def test_cli_blocks_missing_current_source_before_initializing_transport_or_forge(self):
        with tempfile.TemporaryDirectory() as directory:
            errors=io.StringIO()
            with patch.object(RUNNER,'ROOT',Path(directory)), \
                    patch.object(sys,'argv',['run-fork-checks.py','--upstream',UPSTREAM]), \
                    patch.object(sys,'stderr',errors), \
                    patch.object(RUNNER.Relay,'__init__') as relay, \
                    patch.object(RUNNER.RelayServer,'__init__') as server, \
                    patch.object(RUNNER.shutil,'which') as which, \
                    patch.object(RUNNER.urllib.request,'urlopen') as network:
                self.assertEqual(RUNNER.main(),2)
            relay.assert_not_called();server.assert_not_called()
            which.assert_not_called();network.assert_not_called()
            self.assertIn('Fork qualification blocked',errors.getvalue())
            self.assertNotIn(UPSTREAM,errors.getvalue())

class ForkCoverageTests(HistoricalForkInventoryFixture):
    def test_historical_signature_fixtures_only_validate_parser_and_status_rules(self):
        old=RUNNER.expected_tests('test/UniswapV4Fork.t.sol');native=RUNNER.expected_tests('test/NativePoolFork.t.sol')
        self.assertEqual(len(old),9);self.assertEqual(len(native),29)
        self.assertIn('testRealSharedPoolRebalanceChangesOneLPAndPreservesAllShares',old)
        self.assertIn('testSelectedNativeReviewedRenouncedWrapperAdminRestoresCustody',native)
    def test_complete_unskipped_exact_suites_succeed_with_windows_paths(self):
        results={key.replace('/','\\'):value for key,value in complete_results().items()}
        self.assertEqual(RUNNER.verify_fork_results(json.dumps(results)),38)
    def test_missing_or_similarly_named_native_suite_cannot_pass(self):
        for replacement in (None,'test/NativePoolFork.t.sol:NativePoolForkTestDisabled'):
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):
                results=complete_results();native=results.pop(RUNNER.FORK_SUITES[1])
                if replacement:results[replacement]=native
                RUNNER.verify_fork_results(json.dumps(results))
    def test_zero_exit_with_any_skipped_failed_or_setup_only_native_result_is_rejected(self):
        for status in ('Skipped','Failure',None):
            with self.subTest(status=status),self.assertRaises(ValueError):
                results=complete_results();tests=results[RUNNER.FORK_SUITES[1]]['test_results']
                tests[next(iter(tests))]['status']=status
                RUNNER.verify_fork_results(json.dumps(results))
        results=complete_results();results[RUNNER.FORK_SUITES[1]]['test_results']={'setUp()':{'status':'Skipped'}}
        with self.assertRaises(ValueError):RUNNER.verify_fork_results(json.dumps(results))
    def test_partial_empty_extra_and_overloaded_test_results_are_rejected(self):
        for mode in ('partial','empty','extra','overloaded'):
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                results=complete_results();tests=results[RUNNER.FORK_SUITES[1]]['test_results']
                if mode=='partial':tests.popitem()
                elif mode=='empty':tests.clear()
                elif mode=='extra':tests['testUnknown()']={'status':'Success'}
                else:tests[next(iter(tests)).replace('()','(uint256)')]={'status':'Success'}
                RUNNER.verify_fork_results(json.dumps(results))
    def test_missing_or_malformed_json_results_are_rejected(self):
        for output in (None,'No tests to run!','{}','[]','null'):
            with self.subTest(output=output),self.assertRaises(ValueError):RUNNER.verify_fork_results(output)
        for value in (None,{}, {'test_results':[]}, {'test_results':{'testMissing()':None}}):
            with self.subTest(value=value),self.assertRaises(ValueError):
                results=complete_results();results[RUNNER.FORK_SUITES[1]]=value
                RUNNER.verify_fork_results(json.dumps(results))
    def test_inventory_ignores_commented_and_quoted_function_declarations(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'Example.sol'
            source.write_text('''// function testComment() public {}\n/* function testBlock() public {} */
                string constant S="function testQuoted()";
                function testActual() public {} function testFuzz(uint256 value) public {}''',encoding='utf-8')
            with patch.object(RUNNER,'ROOT',Path(directory)):
                self.assertEqual(RUNNER.expected_tests('Example.sol'),{'testActual','testFuzz'})
                for text in ('contract Empty {}','function testSame() public {} function testSame(uint256) public {}'):
                    source.write_text(text,encoding='utf-8')
                    with self.assertRaises(ValueError):RUNNER.expected_tests('Example.sol')

if __name__=='__main__':unittest.main()
