"""Bounded second-provider comparison over real SQLite; no public network."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from frontend_api.history_audit import AuditError, HistoryAudit, main
from indexer.monitor import Indexer
from tests_python.test_frontend_api import configuration, addr
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import Budget, request_scope


def h(n): return '0x'+f'{n:064x}'


class Source:
    def __init__(self, logs):
        self.logs, self.head, self.calls = logs, 30, []
        self.mutate = None

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method == 'eth_chainId': result = hex(31337)
        elif method == 'eth_blockNumber': result = hex(self.head)
        elif method == 'eth_getBlockByNumber':
            n = int(params[0],16)
            result = dict(number=hex(n), hash=h(n), parentHash=h(n-1), timestamp=hex(100+n))
        elif method == 'eth_getLogs':
            low, high = int(params[0]['fromBlock'],16), int(params[0]['toBlock'],16)
            result = [e for e in self.logs if low <= int(e['blockNumber'],16) <= high]
        else: raise AssertionError(method)
        result = copy.deepcopy(result)
        return self.mutate(method, params, result) if self.mutate else result


class HistoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.cfg = configuration()
        self.cfg['deployment_block_hash'] = h(10)
        contracts = [addr(i) for i in (2,3,4,5,7,40,41)]
        self.cfg['history'] = dict(database=str(self.path/'history.sqlite'), start_block=10,
            start_parent_hash=h(9), contracts=contracts, max_events=10000)
        self.cfg['earnings_history'] = dict(schema=1, prices=None, deployments=[dict(controller=addr(1),
            fees=dict(address=addr(40),code_hash=h(40)),membership=dict(address=addr(41),code_hash=h(41)))])
        self.policy = dict(schema=1,rpc_urls=['https://independent.invalid'], provider_id='separate-operator',
            independence_review_sha256='1'*64)
        self.index_cfg = dict(chain_id=31337,start_block=10,start_parent_hash=h(9),
            contracts=contracts,database=str(self.path/'history.sqlite'),rpc_urls=['http://127.0.0.1:8545'])
        self.idx = Indexer(self.index_cfg)
        self.addCleanup(self.idx.close)
        self.events = [self.log(11,0,addr(2)),self.log(12,0,addr(40)),self.log(12,1,addr(5))]
        with self.idx.db:
            for n in range(10,20): self.idx.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',(31337,n,h(n),h(n-1),100+n))
            for event in self.events:self.insert(event)
            self.idx.db.execute('UPDATE cursors SET next_block=20')
        self.rpc = Source(copy.deepcopy(self.events))

    @staticmethod
    def log(block,index,emitter):
        return dict(address=emitter, blockNumber=hex(block), blockHash=h(block), transactionHash=h(1000+block),
            transactionIndex='0x0', logIndex=hex(index), removed=False, topics=[h(70)], data='0x0001')

    def insert(self,event):
        self.idx.db.execute('INSERT INTO logs VALUES(?,?,?,?,?,?,?,?,?)',(31337,int(event['blockNumber'],16),
            event['blockHash'],event['transactionHash'],int(event['logIndex'],16),event['address'],
            'ignored-decoded-cache','{}',json.dumps(event)))

    def run_audit(self,start=10,end=19,config=None,policy=None):
        return HistoryAudit(config or self.cfg,policy or self.policy,self.rpc).run(addr(1),start,end)

    def snapshot(self):
        return {table:self.idx.db.execute('SELECT * FROM '+table+' ORDER BY 1,2').fetchall()
                for table in ('cursors','blocks','logs')}

    def test_matched_raw_history_read_only_and_index_used(self):
        before = self.snapshot()
        result = self.run_audit()
        self.assertEqual(result['status'],'matched')
        self.assertEqual(result['local_logs'],3)
        self.assertEqual(result['local_logs_sha256'],result['rpc_logs_sha256'])
        self.assertEqual(len(result['required_earnings_emitters']),7)
        self.assertEqual(before,self.snapshot())
        plan=str(self.idx.db.execute('EXPLAIN QUERY PLAN SELECT * FROM logs WHERE chain=? AND block_number BETWEEN ? AND ? ORDER BY block_number,log_index',(31337,10,19)).fetchall())
        self.assertIn('block_log_lookup',plan)
        self.assertNotIn('TEMP B-TREE',plan)

    def test_omitted_index_fee_detected(self):
        with self.idx.db:self.idx.db.execute('DELETE FROM logs WHERE address=?',(addr(40),))
        result=self.run_audit()
        self.assertEqual(result['status'],'mismatch')
        self.assertEqual(result['discrepancies']['missing_from_index']['count'],1)

    def test_provider_omission_is_not_claimed_as_proof_of_index_corruption(self):
        self.rpc.logs.pop()
        result=self.run_audit()
        self.assertEqual(result['discrepancies']['absent_from_rpc']['count'],1)
        self.assertEqual(result['status'],'mismatch')

    def test_conflicting_amount_or_topics_detected(self):
        for field,value in [('data','0x0020'),('topics',[h(71)])]:
            with self.subTest(field=field):
                self.rpc.logs=copy.deepcopy(self.events);self.rpc.logs[1][field]=value
                result=self.run_audit()
                self.assertEqual(result['discrepancies']['conflicting']['count'],1)

    def test_unordered_rpc_and_hex_case_are_normalized(self):
        self.rpc.logs.reverse()
        for event in self.rpc.logs:
            for field in ('address','transactionHash','blockHash','data'): event[field]='0x'+event[field][2:].upper()
        self.assertEqual(self.run_audit()['status'],'matched')

    def test_raw_column_disagreement_fails_closed(self):
        with self.idx.db:self.idx.db.execute('UPDATE logs SET address=? WHERE address=?',(addr(4),addr(40)))
        with self.assertRaisesRegex(AuditError,'columns_mismatch'):self.run_audit()

    def test_duplicate_removed_unrequested_and_invalid_rpc_logs(self):
        changes=[lambda logs:logs.append(copy.deepcopy(logs[0])),lambda logs:logs[0].update(removed=True),
                 lambda logs:logs[0].update(address=addr(99)),lambda logs:logs[0].update(logIndex='0x00'),
                 lambda logs:logs[0].update(data='0x0'),lambda logs:logs[0].pop('transactionIndex')]
        for change in changes:
            with self.subTest(change=change):
                self.rpc.logs=copy.deepcopy(self.events);change(self.rpc.logs)
                with self.assertRaises((AuditError,RpcError,KeyError)):self.run_audit()

    def test_wrong_chain_and_insufficient_depth_rejected(self):
        self.rpc.mutate=lambda method,params,result:'0x1' if method=='eth_chainId' else result
        with self.assertRaisesRegex(AuditError,'wrong_chain'):self.run_audit()
        self.rpc.mutate=None;self.rpc.head=29
        with self.assertRaisesRegex(AuditError,'confirmations'):self.run_audit()

    def test_reorg_after_logs_or_lost_depth_fails(self):
        for reorg in (True,False):
            with self.subTest(reorg=reorg):
                self.rpc.calls=[]
                def mutate(method,params,result):
                    after=any(m=='eth_getLogs' for m,_ in self.rpc.calls)
                    if after and reorg and method=='eth_getBlockByNumber':result['hash']=h(999)
                    if after and not reorg and method=='eth_blockNumber':result='0x13'
                    return result
                self.rpc.mutate=mutate
                with self.assertRaises(AuditError):self.run_audit()

    def test_gaps_identity_and_cursor_coverage(self):
        import sqlite3
        for sql in ['DELETE FROM blocks WHERE number=15','UPDATE cursors SET next_block=19',
                    'UPDATE cursors SET config=\'{}\'','UPDATE blocks SET parent=\''+h(999)+'\' WHERE number=15']:
            with self.subTest(sql=sql):
                saved=sqlite3.connect(':memory:');self.idx.db.backup(saved)
                try:
                    with self.idx.db:self.idx.db.execute(sql)
                    with self.assertRaises(AuditError):self.run_audit()
                finally:
                    saved.backup(self.idx.db);saved.close()

    def test_partial_window_is_labelled_not_complete_history(self):
        result=self.run_audit(12,19)
        self.assertEqual(result['from_block'],12)
        self.assertEqual(result['scope'],'one_configured_epoch_window')
        self.assertEqual(result['local_logs'],2)
        self.assertIn('whole-history',result['limitations'])

    def test_empty_window_and_no_price_profile_do_not_invent_usd(self):
        result=self.run_audit(15,19)
        self.assertEqual(result['status'],'matched')
        self.assertEqual(result['local_logs'],0)
        self.assertNotIn('usd',result)

    def test_window_and_event_and_byte_bounds(self):
        for start,end in [(9,19),(10,138),(20,19),(True,19)]:
            with self.subTest(start=start,end=end),self.assertRaises(AuditError):self.run_audit(start,end)
        with patch('frontend_api.history_audit.MAX_LOGS',2),self.assertRaises(AuditError):self.run_audit()
        with patch('frontend_api.history_audit.MAX_BYTES',100),self.assertRaises(AuditError):self.run_audit()

    def test_timeout_uses_shared_budget(self):
        with request_scope(Budget(calls=2)),self.assertRaises(WorkLimit):self.run_audit()

    def test_same_provider_or_missing_review_rejected(self):
        for delta in [dict(rpc_urls=['http://127.0.0.1:9999']),dict(independence_review_sha256='0'*64),dict(provider_id='https://secret')]:
            with self.subTest(delta=delta),self.assertRaises(AuditError):self.run_audit(policy=dict(self.policy,**delta))

    def test_missing_database_never_created(self):
        cfg=copy.deepcopy(self.cfg);cfg['history']['database']=str(self.path/'missing.sqlite')
        import sqlite3
        with self.assertRaises(sqlite3.Error):self.run_audit(config=cfg)
        self.assertFalse((self.path/'missing.sqlite').exists())

    def test_cli_sanitizes_error_and_does_not_overwrite(self):
        cfg=self.path/'config.json';cfg.write_text(json.dumps(self.cfg))
        pol=self.path/'policy.json';pol.write_text(json.dumps(self.policy))
        output=self.path/'report.json'
        args=['--config',str(cfg),'--audit-rpc-config',str(pol),'--controller',addr(1),
              '--from-block','10','--to-block','19','--output',str(output)]
        with patch.object(HistoryAudit,'run',side_effect=RpcError('https://secret.invalid/private-key')),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args),2)
            saved=output.read_bytes();self.assertNotIn(b'secret',saved)
            self.assertEqual(main(args),2);self.assertEqual(output.read_bytes(),saved)
        self.assertEqual(json.loads(saved)['status'],'unavailable')

    def test_seven_emitters_required_and_unknown_controller_rejected(self):
        cfg=copy.deepcopy(self.cfg);cfg['history']['contracts'].remove(addr(41))
        with self.assertRaises(ValueError):self.run_audit(config=cfg)
        with self.assertRaisesRegex(AuditError,'unconfigured_epoch'):
            HistoryAudit(self.cfg,self.policy,self.rpc).run(addr(99),10,19)

    def test_existing_indexer_database_reopen_adds_index_without_cursor_reset(self):
        with self.idx.db:self.idx.db.execute('DROP INDEX block_log_lookup')
        before=self.snapshot()
        reopened=Indexer(self.index_cfg)
        try:
            self.assertEqual(before,self.snapshot())
            self.assertIsNotNone(reopened.db.execute("SELECT name FROM sqlite_master WHERE name='block_log_lookup'").fetchone())
        finally:reopened.close()

    def test_maximum_log_window_and_chunked_empty_blocks(self):
        events=[self.log(12,i,addr(40)) for i in range(10000)]
        with self.idx.db:
            self.idx.db.execute('DELETE FROM logs')
            for event in events:self.insert(event)
            for n in range(20,138):self.idx.db.execute('INSERT INTO blocks VALUES(?,?,?,?,?)',(31337,n,h(n),h(n-1),100+n))
            self.idx.db.execute('UPDATE cursors SET next_block=138')
        self.rpc.logs=events;self.rpc.head=149
        result=self.run_audit(10,137)
        self.assertEqual(result['status'],'matched')
        self.assertEqual(result['local_logs'],10000)
        self.assertEqual(len([1 for method,_ in self.rpc.calls if method=='eth_getLogs']),4)

    def test_predecessor_profile_selects_its_own_database(self):
        import sqlite3
        cfg=copy.deepcopy(self.cfg)
        previous={k:copy.deepcopy(cfg[k]) for k in ('deployment_block','deployment_block_hash','contracts','assets','history')}
        previous['retirement_transaction_hash']=h(700)
        for contract in previous['contracts'].values():contract['address']=addr(int(contract['address'],16)+100)
        previous['history']['contracts']=[addr(int(a,16)+100) for a in previous['history']['contracts']]
        previous['history']['database']=str(self.path/'previous.sqlite')
        db=sqlite3.connect(previous['history']['database']);self.idx.db.backup(db)
        try:
            with db:
                db.execute('DELETE FROM logs')
                db.execute('UPDATE cursors SET config=?',(json.dumps(dict(contracts=previous['history']['contracts'],start=10,parent_hash=h(9)),sort_keys=True),))
        finally:db.close()
        cfg['predecessors']=[previous]
        cfg['earnings_history']['deployments'].insert(0,dict(controller=addr(101),
            fees=dict(address=addr(140),code_hash=h(140)),membership=dict(address=addr(141),code_hash=h(141))))
        self.rpc.logs=[]
        result=HistoryAudit(cfg,self.policy,self.rpc).run(addr(101),10,19)
        self.assertEqual(result['status'],'matched')
        self.assertEqual(result['controller'],addr(101))
        self.assertIn(addr(140),result['required_earnings_emitters'])
        self.assertEqual(result['local_logs'],0)

    def test_cli_protects_database_sidecars_before_rpc(self):
        cfg=self.path/'config.json';cfg.write_text(json.dumps(self.cfg))
        pol=self.path/'policy.json';pol.write_text(json.dumps(self.policy))
        for target in [cfg,pol,Path(str(self.path/'history.sqlite')+'-journal')]:
            with self.subTest(target=target),patch.object(HistoryAudit,'run') as run,contextlib.redirect_stdout(io.StringIO()):
                args=['--config',str(cfg),'--audit-rpc-config',str(pol),'--controller',addr(1),
                      '--from-block','10','--to-block','19','--output',str(target)]
                self.assertEqual(main(args),2)
                run.assert_not_called()
        self.assertFalse(Path(str(self.path/'history.sqlite')+'-journal').exists())

    def test_cli_matched_and_mismatch_receipts_have_distinct_exit_codes(self):
        cfg=self.path/'config.json';cfg.write_text(json.dumps(self.cfg))
        pol=self.path/'policy.json';pol.write_text(json.dumps(self.policy))
        for status,code in [('matched',0),('mismatch',2)]:
            target=self.path/(status+'.json')
            with patch.object(HistoryAudit,'run',return_value=dict(schema=1,status=status)),contextlib.redirect_stdout(io.StringIO()):
                args=['--config',str(cfg),'--audit-rpc-config',str(pol),'--controller',addr(1),
                      '--from-block','10','--to-block','19','--output',str(target)]
                self.assertEqual(main(args),code)
                self.assertEqual(json.loads(target.read_text())['status'],status)
