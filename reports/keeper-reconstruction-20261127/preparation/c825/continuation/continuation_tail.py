# Appended to the preserved, byte-identical f102 c825 coordinator under a
# non-main name. No installer or alternate worker is introduced.
import math

PRESERVED_CONTROLLER_SHA='f102550ea30927350c5b815fda020ccf4ea6a23fae00379668af8ccba351f10e'
PASSED_NEGATIVE_SHA='ad5813b9433039f5cf35925988bc673833b4b5c7f7a237d3e8a5ca21d9d0390d'
PASSED_NEGATIVE_BYTES=3714
STRICT_DECODE=decode


def continuation_decode(raw):
    if len(raw)!=PASSED_NEGATIVE_BYTES or sha(raw)!=PASSED_NEGATIVE_SHA:return STRICT_DECODE(raw)
    def duration(number):
        value=float(number);need(math.isfinite(value)and value>=0,'negative_duration');return value
    parsed=json.loads(raw,object_pairs_hook=unique,parse_float=duration,parse_constant=invalid)
    allowed={('elapsed_seconds',),('calls',0,'elapsed_seconds')};found=set();stack=[(parsed,())];visited=0
    while stack:
        value,path=stack.pop();visited+=1;need(visited<=2048 and len(path)<=16,'negative_result_shape')
        if type(value)is float:need(path in allowed,'negative_float_path');found.add(path)
        elif type(value)is dict:stack.extend((child,(*path,key))for key,child in value.items())
        elif type(value)is list:stack.extend((child,(*path,index))for index,child in enumerate(value))
    need(found==allowed and type(parsed)is dict,'negative_duration_fields')
    need(parsed['success']is True and parsed['unsigned']is True and parsed['mode']=='negative'
        and parsed['readiness_approved']is False and parsed['production_approved']is False
        and parsed['native_refusal_before_restore']is True,'negative_success_flags')
    need(type(parsed['calls'])is list and len(parsed['calls'])==1,'negative_call_count');call=parsed['calls'][0]
    need(call['script']=='keeper-recovery.py'and call['action']=='verify'and type(call['returncode'])is int
        and call['returncode']==1 and call['expected_refusal']is True and call['python_flags']==['-I','-S','-B']
        and call['parsed']['fixed_native_refusal']=='invalid_input'and call['parsed']['restoration_outputs_absent']is True,'negative_native_binding')
    isolation=parsed['isolation'];need(isolation['root_directory_is_new']is True and isolation['host_opt_mounted']is False
        and isolation['original_operating_state_absent']is True and isolation['source_files_verified']==41
        and isolation['original_source13_19_unchanged']is True,'negative_isolation_binding')
    return parsed


def continuation_main():
    continuation_sha=sys.argv[sys.argv.index('--controller-sha256')+1]
    need(re.fullmatch('[0-9a-f]{64}',continuation_sha)is not None and continuation_sha!=PRESERVED_CONTROLLER_SHA,'continuation_source_pin')
    globals()['ACTIVE_CONTROLLER_SHA']=PRESERVED_CONTROLLER_SHA
    globals()['decode']=continuation_decode
    identity=owned()
    need(identity['controller_sha256']==PRESERVED_CONTROLLER_SHA,'preserved_controller_identity')
    negative=read(LAB/'negative-root/reconstruction/runtime/RESULT.json',32768,65534)
    need(len(negative)==PASSED_NEGATIVE_BYTES and sha(negative)==PASSED_NEGATIVE_SHA,'passed_negative_external_pin')
    continuation_decode(negative)
    need(not(LAB/'START-complete.json').exists()and not(LAB/'CONTINUATION_REVIEW.json').exists(),'no_continuation_restart')
    need(properties(UNIT_BASE+'-complete.service').get('LoadState')=='not-found','complete_unit_exists')
    review={'schema':1,'kind':'popl-c825-complete-only-continuation-review','unsigned':True,
        'readiness_approved':False,'production_approved':False,'canonical_state_verified':False,
        'preserved_controller_sha256':PRESERVED_CONTROLLER_SHA,'continuation_sha256':continuation_sha,
        'worker_sha256':WORKER_SHA,'passed_negative_result_sha256':PASSED_NEGATIVE_SHA,
        'passed_negative_result_bytes':PASSED_NEGATIVE_BYTES,
        'only_relaxed_paths':['elapsed_seconds','calls[0].elapsed_seconds'],
        'durations_must_be_finite_and_nonnegative':True,'other_decode_inputs_use_preserved_strict_parser':True,
        'only_action':'start-complete','installer_called':False,'LAB_ID_rewritten':False,
        'worker_or_negative_or_complete_inputs_rewritten':False,'negative_native_call_repeated':False,
        'original_start_function_and_all_guards_retained':True}
    write(LAB/'CONTINUATION_REVIEW.json',enc(review),0o600)
    answer=start(argparse.Namespace(mode='complete'))
    answer.update(continuation_review_sha256=sha(enc(review)),preserved_controller_sha256=PRESERVED_CONTROLLER_SHA,
        continuation_sha256=continuation_sha,passed_negative_result_sha256=PASSED_NEGATIVE_SHA)
    print(json.dumps(answer,sort_keys=True))


try:continuation_main()
except Exception as exc:
    code=str(exc)if type(exc)is ValueError and re.fullmatch('[a-z_]{1,64}',str(exc))is not None else None
    print(json.dumps({'refused':True,'error_type':type(exc).__name__,'refusal_code':code,
        'scope':'fixed_c825_complete_only_continuation'}));raise SystemExit(1)from None
