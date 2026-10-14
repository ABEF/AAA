"""Read-only JSON-RPC client with endpoint chain checks and bounded retries."""
from __future__ import annotations
import itertools
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

class RpcError(RuntimeError): pass
class WrongChain(RpcError): pass

class Rpc:
    READ_METHODS = frozenset({
        'eth_chainId','eth_blockNumber','eth_call','eth_estimateGas','eth_gasPrice',
        'eth_getBlockByNumber','eth_getBlockByHash','eth_getLogs','eth_getCode',
        'eth_getTransactionByHash','eth_getTransactionReceipt','eth_getTransactionCount',
        'eth_getBalance','eth_feeHistory','eth_maxPriorityFeePerGas','web3_clientVersion',
    })
    def __init__(self, urls: list[str], chain_id: int, *, timeout: float = 10, retries: int = 3):
        if not urls or chain_id <= 0: raise ValueError('RPC URLs and positive chain_id are required')
        for url in urls:
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('localhost','127.0.0.1','::1')):
                raise ValueError('RPC endpoints require HTTPS; HTTP is allowed only on loopback')
            if not parsed.hostname: raise ValueError('Invalid RPC URL')
        self.urls, self.chain_id = urls, chain_id
        self.timeout, self.retries = timeout, retries
        self.active = 0
        self._ids = itertools.count(1)

    @property
    def active_url(self) -> str: return self.urls[self.active]

    def _post(self, url: str, method: str, params: list[Any]) -> Any:
        request_id = next(self._ids)
        raw = json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':params}).encode()
        request = urllib.request.Request(url, data=raw, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=self.timeout) as response:
            data = response.read(8 * 1024 * 1024 + 1)
        if len(data) > 8 * 1024 * 1024: raise RpcError('RPC response exceeded size limit')
        body = json.loads(data)
        if not isinstance(body,dict) or body.get('id') != request_id or body.get('jsonrpc') != '2.0':
            raise RpcError('Malformed JSON-RPC response')
        if 'error' in body:
            error = body['error']
            # Do not include URLs, raw transport headers or credentials in error logs.
            code = error.get('code') if isinstance(error,dict) else None
            raise RpcError(f'{method} returned JSON-RPC error {code}')
        if 'result' not in body: raise RpcError('Missing JSON-RPC result')
        return body['result']

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        if method not in self.READ_METHODS:
            raise RpcError('RPC method is not on the read-only allowlist')
        failure = None
        for attempt in range(max(self.retries, len(self.urls))):
            url = self.active_url
            try:
                actual = int(self._post(url,'eth_chainId',[]),16)
                if actual != self.chain_id: raise WrongChain('RPC chain ID mismatch')
                return actual if method == 'eth_chainId' else self._post(url, method, params or [])
            except (OSError, ValueError, RpcError) as exc:
                failure = exc
                self.active = (self.active + 1) % len(self.urls)
                if attempt + 1 < max(self.retries,len(self.urls)): time.sleep(min(.2 * 2**attempt,1.5))
        raise RpcError(f'{method} failed after bounded retries ({type(failure).__name__})') from failure

    def eth_call(self, to: str, data: str, sender: str | None = None, block: str = 'latest') -> str:
        tx = {'to':to,'data':data}
        if sender: tx['from'] = sender
        return self.call('eth_call',[tx,block])
