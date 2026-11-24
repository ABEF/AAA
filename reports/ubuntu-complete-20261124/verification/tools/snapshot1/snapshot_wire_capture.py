"""Private fixture capture: byte-exact successful getCode deduplication only."""
import hashlib
import json
import re

CAPTURE_BYTES=64*1024*1024
RESPONSE_BYTES=16*1024*1024
CODEC='eth_getCode-quoted-ascii-v1'


def need(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _result_span(raw,response):
    """Locate the sole top-level result, respecting JSON strings and nesting."""
    text=raw.decode('utf-8');decoder=json.JSONDecoder();size=len(text)
    def ws(at):
        while at<size and text[at] in ' \t\r\n':at+=1
        return at
    at=ws(0);need(at<size and text[at]=='{','Code response object differs');at=ws(at+1);spans=[]
    while at<size and text[at]!='}':
        key,end=decoder.raw_decode(text,at);need(type(key)is str,'Code response key differs')
        at=ws(end);need(at<size and text[at]==':','Code response separator differs');start=ws(at+1)
        value,end=decoder.raw_decode(text,start)
        if key=='result':spans.append((start,end,value))
        at=ws(end);need(at<size and text[at]in ',}','Code response member boundary differs')
        if text[at]=='}':break
        at=ws(at+1)
    need(at<size and text[at]=='}' and ws(at+1)==size and len(spans)==1,'Code response result cardinality differs')
    start,end,value=spans[0]
    need(type(value)is str and re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',value)is not None,'Code response hex literal differs')
    literal='"'+value+'"';quoted=literal.encode('ascii')
    need(text[start:end]==literal and raw.count(quoted)==1,'Code response requires one exact quoted result match')
    need(json.loads(raw)==response and response.get('result')==value,'Code response envelope differs')
    return text[:start],text[end:],literal


def reconstruct_code_response(record,blobs):
    """Reconstruct and authenticate the original HTTP response body bytes."""
    fields={'request','response_sha256','response','response_codec','result_blob_sha256','response_raw_prefix','response_raw_suffix'}
    need(type(record)is dict and set(record)==fields and record['response_codec']==CODEC,'Code capture schema differs')
    request=record['request'];envelope=record['response'];pin=record['result_blob_sha256']
    need(type(request)is dict and request.get('method')=='eth_getCode' and type(request.get('id'))is int,'Code capture request differs')
    need(type(envelope)is dict and 'result'not in envelope and 'error'not in envelope and
         envelope.get('jsonrpc')=='2.0' and type(envelope.get('id'))is int and envelope['id']==request['id'],'Code capture envelope identity differs')
    need(type(pin)is str and re.fullmatch(r'[0-9a-f]{64}',pin)is not None and pin in blobs,'Code result blob missing')
    literal=blobs[pin]
    need(type(literal)is str and re.fullmatch(r'"0x(?:[0-9a-fA-F]{2})*"',literal)is not None,'Code result blob literal differs')
    quoted=literal.encode('ascii');need(sha(quoted)==pin,'Code result blob hash differs')
    prefix=record['response_raw_prefix'];suffix=record['response_raw_suffix']
    need(type(prefix)is str and type(suffix)is str,'Code capture raw envelope differs')
    raw=prefix.encode('utf-8')+quoted+suffix.encode('utf-8')
    need(len(raw)<=RESPONSE_BYTES and sha(raw)==record['response_sha256'],'Code capture raw response hash/bound differs')
    response=json.loads(raw);expected={**envelope,'result':json.loads(literal)}
    need(response==expected,'Code capture decoded envelope differs')
    actual_prefix,actual_suffix,actual_literal=_result_span(raw,response)
    need((actual_prefix,actual_suffix,actual_literal)==(prefix,suffix,literal),'Code capture result position differs')
    return raw


class WireCapture:
    def __init__(self):
        self.records=[];self.blobs={};self.retained=len(encode(self.document()))
    def document(self):return dict(schema=2,records=self.records,result_blobs=self.blobs)
    def add(self,request,response,raw):
        params=request.get('params')if type(request)is dict else None
        snapshot_response=(type(request)is dict and request.get('method')=='anvil_dumpState'and
                           type(params)is list and len(params)==1 and params[0]is True)
        response_limit=32*1024*1024 if snapshot_response else RESPONSE_BYTES
        need(len(raw)<=response_limit,'Local snapshot response exceeds32MiB'if snapshot_response else 'Local response exceeds16MiB')
        need(len(self.records)<6000,'Existing finite construction work bound')
        frozen_request=json.loads(encode(request));frozen_response=json.loads(encode(response))
        need(len(encode(frozen_request))<=128*1024 and json.loads(raw)==frozen_response,'Capture request/response differs')
        record=dict(request=frozen_request,response_sha256=sha(raw),response=frozen_response)
        pin=None;literal=None;new_blob=False
        if request['method']=='eth_getCode' and 'result'in response and 'error'not in response:
            prefix,suffix,literal=_result_span(raw,response);pin=sha(literal.encode('ascii'))
            envelope=dict(frozen_response);del envelope['result']
            record.update(response=envelope,response_codec=CODEC,result_blob_sha256=pin,
                          response_raw_prefix=prefix,response_raw_suffix=suffix)
            new_blob=pin not in self.blobs
            if not new_blob:need(self.blobs[pin]==literal,'Code result blob collision differs')
            available={**self.blobs,pin:literal}
            need(reconstruct_code_response(record,available)==raw,'Code capture byte reconstruction differs')
        elif request['method']=='anvil_dumpState' and 'result'in response:
            value=response['result'];record['response']=dict(jsonrpc='2.0',id=request['id'],
                result_hex_characters=len(value),result_utf8_sha256=sha(value.encode()))
        delta=len(encode(record))+(1 if self.records else 0)
        if new_blob:delta+=len(encode({pin:literal}))-2+(1 if self.blobs else 0)
        need(self.retained+delta<=CAPTURE_BYTES,'Construction wire capture bound')
        if new_blob:self.blobs[pin]=literal
        self.records.append(record);self.retained+=delta
        return record
    def encoded(self):
        raw=encode(self.document())
        need(len(raw)==self.retained and self.retained<=CAPTURE_BYTES,'Construction wire capture accounting differs')
        return raw


def verify_wire_capture(document):
    """Offline verification for the new persisted private-fixture wire format."""
    need(type(document)is dict and set(document)=={'schema','records','result_blobs'} and document['schema']==2,'Wire capture document differs')
    records=document['records'];blobs=document['result_blobs'];encoded_bytes=len(encode(document))
    need(type(records)is list and len(records)<=6000 and type(blobs)is dict and encoded_bytes<=CAPTURE_BYTES,'Wire capture bound differs')
    used=set();deduplicated=0
    for record in records:
        if 'response_codec'in record:
            reconstruct_code_response(record,blobs);used.add(record['result_blob_sha256']);deduplicated+=1
    need(used==set(blobs),'Wire capture unreferenced blob differs')
    return dict(records=len(records),deduplicated_code_responses=deduplicated,unique_code_blobs=len(blobs),encoded_bytes=encoded_bytes)
