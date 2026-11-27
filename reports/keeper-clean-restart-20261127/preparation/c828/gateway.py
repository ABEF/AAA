"""Fixed c828 RPC gate: one actual source submission, never another send."""
import sys
sys.dont_write_bytecode=True
import hashlib,http.client,json,os,re,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import shared as S

LOCK=threading.Lock()
SENDS={'eth_sendRawTransaction','eth_sendTransaction','eth_sign','eth_signTransaction','personal_sendTransaction'}


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        identifier=None
        try:
            self.connection.settimeout(20);length=int(self.headers.get('Content-Length','0'))
            S.need(0<length<=131072,'gateway_request_bound');body=self.rfile.read(length)
            S.need(len(body)==length,'gateway_exact_body');query=S.decode(body)
            S.need(type(query)is dict and query.get('jsonrpc')=='2.0'and type(query.get('id'))is int,'gateway_envelope')
            identifier=query['id'];method=query.get('method')
            S.need(type(method)is str,'gateway_method_type')
            if set(query)=={'jsonrpc','id','method'}and method in S.READ_METHODS:query=dict(query,params=[])
            S.need(set(query)=={'jsonrpc','id','method','params'}and type(query['params'])is list,'gateway_params')
            with LOCK,S.budget()as state:
                if method in SENDS:
                    state['transaction_method_attempts']+=1
                    S.need(method=='eth_sendRawTransaction'and state['raw_attempts']==0
                        and not(S.ROOT/'control/SOURCE_FENCED.json').exists(),'no_additional_transaction')
                    state['raw_attempts']+=1
                    config_raw=S.read(S.ACTOR/'config.json',65536);config=S.decode(config_raw)
                    pending=S.value(S.ACTOR/'state.json')['pending']
                    S.need(type(pending)is dict and pending['hash']is None and pending['nonce']==0
                        and pending['key']=='harvest:'+str(S.BUCKET)and pending['value']==0
                        and pending['to']==config['contracts']['vault'],'source_durable_intent')
                    S.need(len(query['params'])==1 and type(query['params'][0])is str
                        and re.fullmatch('0x(?:[0-9a-fA-F]{2})+',query['params'][0])is not None,'raw_encoding')
                    review=pending['fee_review'];S.need(review['schema']==1 and review['receipt_fee_policy']=='included'
                        and 0<review['gas_limit']<=24000000 and 0<review['max_fee_per_gas']<=5000000000
                        and review['l1_fee_allowance_wei']==0 and review['maximum_cost_wei']==review['gas_limit']*review['max_fee_per_gas']
                        and review['maximum_cost_wei']<=10000000000000000,'source_fee_limits')
                    S.need(sum(int(item)for item in S.value(S.ACTOR/'state.json')['spent'].values())+review['maximum_cost_wei']<=50000000000000000,'source_day_limit')
                    # A durable reservation precedes any possible node write.
                    S.commit_budget(state)
                    S.save('BEFORE_RAW_SUBMISSION.json',{'configuration_sha256':S.sha(config_raw),'intent':pending,
                        'signature_material_retained':False})
                else:S.need(method in S.READ_METHODS,'gateway_method')
                connection=http.client.HTTPConnection('127.0.0.1',19626,timeout=20)
                try:
                    body=S.enc(query);connection.request('POST','/',body,{'Content-Type':'application/json'})
                    response=connection.getresponse();S.need(response.status==200,'gateway_HTTP');raw=response.read(2097153)
                    S.need(len(raw)<=2097152,'gateway_response_bound');answer=S.decode(raw)
                    S.need(type(answer)is dict and answer.get('jsonrpc')=='2.0'and type(answer.get('id'))is int
                        and answer['id']==identifier and('result'in answer)!=('error'in answer),'gateway_response_identity')
                    if method=='eth_sendRawTransaction':
                        S.need('error'not in answer and re.fullmatch('0x[0-9a-f]{64}',answer['result'])is not None,'node_accepted_hash')
                        state['raw_forwarded']+=1;state['accepted_hash']=answer['result']
                        S.commit_budget(state)
                        # Check the actual node transaction after acceptance. It
                        # remains unmined until the separately fenced driver.
                        state['RPC_requests']+=1;S.need(state['RPC_requests']<=S.MAX_RPC,'shared_budget');S.commit_budget(state)
                        check={'jsonrpc':'2.0','id':state['RPC_requests'],'method':'eth_getTransactionByHash','params':[answer['result']]}
                        verify=http.client.HTTPConnection('127.0.0.1',19626,timeout=20)
                        try:
                            verify.request('POST','/',S.enc(check),{'Content-Type':'application/json'})
                            checked=verify.getresponse();S.need(checked.status==200,'accepted_transaction_HTTP')
                            checked_raw=checked.read(2097153);S.need(len(checked_raw)<=2097152,'accepted_transaction_bound')
                            checked=S.decode(checked_raw);S.need(type(checked)is dict and checked.get('jsonrpc')=='2.0'
                                and type(checked.get('id'))is int and checked['id']==check['id']
                                and('result'in checked)!=('error'in checked)and'error'not in checked,'accepted_transaction_RPC')
                            transaction=checked['result']
                            S.need(transaction['hash']==answer['result']and transaction['blockNumber']is None
                                and transaction['from'].lower()==config['sender']and transaction['to'].lower()==pending['to']
                                and transaction['input']==pending['data']and int(transaction['nonce'],16)==pending['nonce']
                                and int(transaction['value'],16)==pending['value']and int(transaction['chainId'],16)==4663
                                and int(transaction['gas'],16)==review['gas_limit']and int(transaction['type'],16)==2
                                and int(transaction['maxFeePerGas'],16)==review['max_fee_per_gas']
                                and 0<=int(transaction['maxPriorityFeePerGas'],16)<=review['max_fee_per_gas'],'accepted_transaction_envelope')
                        finally:verify.close()
                        state['accepted_transaction_verified']=True;S.commit_budget(state)
                        S.save('NODE_ACCEPTED.json',{'hash':answer['result'],'actual_Anvil_forward':True,
                            'configuration_sha256':S.sha(config_raw),'raw_signature_retained':False})
                finally:connection.close()
        except Exception as exc:
            answer={'jsonrpc':'2.0','id':identifier,'error':{'code':-32070,'message':'Fixed c828 gateway refused','data':type(exc).__name__}}
        payload=S.enc(answer);S.need(len(payload)<=2097152,'gateway_output_bound')
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)))
        self.end_headers();self.wfile.write(payload)


if __name__=='__main__':
    S.namespace_guard()
    server=ThreadingHTTPServer(('127.0.0.1',19627),Handler);server.daemon_threads=True;server.serve_forever(poll_interval=.1)
