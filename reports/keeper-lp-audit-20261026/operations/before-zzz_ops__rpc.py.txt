"""Read-only JSON-RPC client with endpoint chain checks and bounded retries."""
from __future__ import annotations
import itertools
import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any
from zzz_ops.work_budget import checkpoint, consume, timeout
from zzz_ops.errors import RpcError, RemoteRPCError, WorkLimit

class WrongChain(RpcError): pass

class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        fp.close()
        raise RpcError('RPC redirects are not permitted; configure the reviewed endpoint explicitly')

class Rpc:
    READ_METHODS = frozenset({
        'eth_chainId','eth_blockNumber','eth_call','eth_estimateGas','eth_gasPrice',
        'eth_getBlockByNumber','eth_getBlockByHash','eth_getLogs','eth_getCode','eth_getStorageAt',
        'eth_getTransactionByHash','eth_getTransactionReceipt','eth_getTransactionCount',
        'eth_getBalance','eth_feeHistory','eth_maxPriorityFeePerGas','web3_clientVersion','debug_traceCall',
    })
    def __init__(self, urls: list[str], chain_id: int, *, timeout: float = 10, retries: int = 3):
        if not isinstance(urls,list) or not 1 <= len(urls) <= 8 or type(chain_id) is not int or chain_id <= 0:
            raise ValueError('One to eight RPC URLs and positive integer chain_id are required')
        if type(retries) is not int or not 1 <= retries <= 10 or type(timeout) not in (int,float) or not 0 < timeout <= 60:
            raise ValueError('RPC retries/timeouts exceed supported bounds')
        for url in urls:
            if not isinstance(url,str): raise ValueError('RPC URL must be text')
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('localhost','127.0.0.1','::1')):
                raise ValueError('RPC endpoints require HTTPS; HTTP is allowed only on loopback')
            if not parsed.hostname: raise ValueError('Invalid RPC URL')
        self.urls, self.chain_id = urls, chain_id
        self.timeout, self.retries = timeout, retries
        self.active = 0
        self._ids = itertools.count(1)
        # Per-client policy only: never install or mutate urllib's global opener.
        self._opener = urllib.request.build_opener(_RejectRedirects())

    @property
    def active_url(self) -> str: return self.urls[self.active]

    def _read_http(self, url: str, raw: bytes) -> bytes:
        """Transport hook; response identity, limits and budgets stay in _post."""
        request = urllib.request.Request(url, data=raw, headers={'Content-Type':'application/json'})
        try:
            with self._opener.open(request,timeout=timeout(self.timeout)) as response:
                return response.read(8 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            # Error responses own sockets too; release them before bounded retry.
            exc.close()
            # Other 3xx codes also fail closed without exposing the Location/URL.
            if 300 <= exc.code < 400:
                raise RpcError('RPC redirects are not permitted; configure the reviewed endpoint explicitly') from None
            raise

    def _post(self, url: str, method: str, params: list[Any]) -> Any:
        consume('posts')
        request_id = next(self._ids)
        raw = json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':params}).encode()
        data = self._read_http(url, raw)
        checkpoint()
        if len(data) > 8 * 1024 * 1024: raise RpcError('RPC response exceeded size limit')
        body = json.loads(data)
        if not isinstance(body,dict) or type(body.get('id')) is not int or body.get('id') != request_id or body.get('jsonrpc') != '2.0':
            raise RpcError('Malformed JSON-RPC response')
        if 'error' in body:
            error = body['error']
            # Do not include URLs, raw transport headers or credentials in error logs.
            code = error.get('code') if isinstance(error,dict) else None
            if type(code) is not int: code = None
            message=error.get('message') if isinstance(error,dict) else None
            reason='invalid_params' if code == -32602 else 'rate_limited' if code == -32005 else 'unclassified'
            # Recognize only explicit missing-block responses. A timeout, generic
            # rejection or unsupported hash-parameter error proves no capability.
            if code in (-32000,-32001) and isinstance(message,str) and len(message)<=512 and re.fullmatch(
                    r'(?:header not found|block not found|unknown block|unknown block hash|block hash not found)'
                    r'(?:[: ]+0x[0-9a-fA-F]{64})?[.!]?',message.strip(),re.I):
                reason='unavailable_block'
            raise RemoteRPCError(method,code,reason)
        if 'result' not in body: raise RpcError('Missing JSON-RPC result')
        return body['result']

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        if method not in self.READ_METHODS:
            raise RpcError('RPC method is not on the read-only allowlist')
        failure = None
        for attempt in range(max(self.retries, len(self.urls))):
            checkpoint()
            url = self.active_url
            try:
                actual = int(self._post(url,'eth_chainId',[]),16)
                if actual != self.chain_id: raise WrongChain('RPC chain ID mismatch')
                return actual if method == 'eth_chainId' else self._post(url, method, params or [])
            except WorkLimit:
                raise
            except (OSError, ValueError, TypeError, http.client.HTTPException, RpcError) as exc:
                failure = exc
                self.active = (self.active + 1) % len(self.urls)
                if attempt + 1 < max(self.retries,len(self.urls)):
                    time.sleep(timeout(min(.2 * 2**attempt,1.5)))
                    checkpoint()
        raise RpcError(f'{method} failed after bounded retries ({type(failure).__name__})') from failure

    def eth_call(self, to: str, data: str, sender: str | None = None, block: str | dict = 'latest') -> str:
        tx = {'to':to,'data':data}
        if sender: tx['from'] = sender
        return self.call('eth_call',[tx,block])
