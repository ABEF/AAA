"""Bounded failure facts for the new isolated snapshot1 profile only."""
from pathlib import Path
import hashlib,time,traceback
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def failure(exc):
    facts=[];tb=exc.__traceback__
    while tb:
        frame=tb.tb_frame
        if frame.f_code.co_name=='wire' and Path(frame.f_code.co_filename).name=='snapshot_node.py':
            local=frame.f_locals;response=local.get('response');q=local.get('q',{});raw=local.get('raw')
            row={'file':'snapshot_node.py','function':'wire','line':tb.tb_lineno,
                 'read_bytes':local.get('size') if type(local.get('size'))is int else None,
                 'raw_bytes':len(raw)if type(raw)is bytes else None,
                 'request_id':q.get('id')if type(q)is dict and type(q.get('id'))is int else None,
                 'response_limit_bytes':local.get('response_limit')if type(local.get('response_limit'))is int else None,
                 'HTTP_status':response.status if response is not None else None,
                 'declared_content_length':response.getheader('Content-Length')if response is not None else None,
                 'deadline_elapsed':time.monotonic()>=local['end']if type(local.get('end'))in(int,float)else None}
            decoded=local.get('r')
            if type(decoded)is dict:row.update(response_id_type=type(decoded.get('id')).__name__,response_id_matches=type(decoded.get('id'))is int and decoded.get('id')==row['request_id'],RPC_error_present='error'in decoded)
            facts.append(row)
        tb=tb.tb_next
    message=str(exc);allowed={'Owned HTTP status differs','Local response deadline','Local response exceeds16MiB','Local snapshot response exceeds32MiB','Decompressed state exceeds128MiB','Local response identity differs','Construction wire capture bound','Capture request/response differs','Owned RPC refused anvil_dumpState','Malformed owned state encoding','Compressed export bound'}
    return {'error_class':type(exc).__name__,'fixed_guard_message':message if message in allowed else None,'message_sha256':sha(message.encode()),'original_wire_frame_facts':facts,
            'traceback_frames':[{'file':Path(f.filename).name,'function':f.name,'line':f.lineno}for f in traceback.extract_tb(exc.__traceback__)[-8:]]}
