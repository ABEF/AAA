"""Opt-in loopback activation preparation. No signing or broadcast capabilities."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from frontend_api.activation import ActivationTransactions, ActivationInputError
from frontend_api.server import ReadServer, handler as read_handler
from frontend_api.service import Projection, UnknownNFT


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Duplicate JSON key')
        result[key]=value
    return result


def reject_constant(_):
    raise ValueError('Nonfinite JSON value')


def handler(projection, preparer):
    class Handler(read_handler(projection)):
        def do_POST(self):
            port=self.server.server_address[1]
            hosts=self.headers.get_all('Host',[])
            if len(hosts)!=1 or hosts[0] not in (f'127.0.0.1:{port}',f'localhost:{port}'):
                self._json(400,{'error':'invalid_host'});return
            if self.path!='/v1/activation/prepare':
                self._json(404,{'error':'unknown_endpoint'});return
            if self.headers.get_all('Transfer-Encoding') is not None or self.headers.get_all('Expect') is not None:
                self._json(400,{'error':'unsupported_request_framing'});return
            lengths=self.headers.get_all('Content-Length',[])
            if len(lengths)!=1 or not re.fullmatch(r'0|[1-9][0-9]{0,4}',lengths[0]):
                self._json(400,{'error':'invalid_content_length'});return
            length=int(lengths[0])
            if length>16384:
                self._json(413,{'error':'request_body_too_large'});return
            types=self.headers.get_all('Content-Type',[])
            if len(types)!=1 or types[0].lower() not in ('application/json','application/json; charset=utf-8'):
                self._json(415,{'error':'application_json_required'});return
            try:
                raw=self.rfile.read(length)
                if len(raw)!=length:raise ValueError('Incomplete JSON')
                payload=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_object,parse_constant=reject_constant)
                # This endpoint accepts a flat object of seven scalar fields.
                if not isinstance(payload,dict) or any(isinstance(v,(list,dict)) for v in payload.values()):
                    raise ValueError('Expected flat request')
            except (OSError,ValueError,RecursionError):
                self._json(400,{'error':'invalid_json_body'});return
            try:result=preparer.prepare(payload)
            except ActivationInputError:self._json(400,{'error':'invalid_activation_request'})
            except UnknownNFT:self._json(404,{'error':'nft_not_minted'})
            except Exception:
                # Do not expose RPC errors, endpoints, credentials or request data.
                self._json(503,{'error':'activation_preparation_unavailable'})
            else:self._json(200,result)
    return Handler


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True)
    parser.add_argument('--activation-config',required=True)
    parser.add_argument('--port',type=int,default=8788)
    args=parser.parse_args()
    if not 1024<=args.port<=65535:parser.error('port must be between 1024 and 65535')
    try:
        p=Projection(json.loads(Path(args.config).read_text(encoding='utf-8')))
        preparer=ActivationTransactions(p,json.loads(Path(args.activation_config).read_text(encoding='utf-8')))
    except Exception:parser.exit(1,'Invalid reviewed deployment/activation configuration.\n')
    with ReadServer(('127.0.0.1',args.port),handler(p,preparer)) as server:
        print(json.dumps({'event':'activation_preparation_started','port':args.port,'chain_id':p.chain}),flush=True)
        try:server.serve_forever(poll_interval=.5)
        except KeyboardInterrupt:pass


if __name__=='__main__':main()
