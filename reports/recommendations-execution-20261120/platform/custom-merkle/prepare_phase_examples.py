"""New current-source TEAM/ALLOWLIST examples; offline review is not onboarding.

Read the retained illustrative public example only as the source-bound manifest
input. Rebuild it through the maintained CLI, independently encode two new phase
calls, then invoke that CLI's offline mint reviewer. No signer or network is used.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import zipfile

ROOT = Path(__file__).resolve().parents[4]
OLD_ARCHIVE = ROOT / 'reports/readiness-advance-20261120/evidence.zip'
OLD_ARCHIVE_SHA256 = 'eee6b0df53065e00af171f2faa1c13c5a7a165974c48a2bfea19b561e03ee143'
OLD_INPUT_SHA256 = '973dfbce3565e884eba04c1a6488533bc36b2efc4a26b103c847368a9b9d049d'
MODULE_SHA256 = '01f86be5db2a2d8102b51e1d7fe3a4aae451d53cce7726dfbf3f32e064047480'
ABI_SHA256 = 'b64b0900ed04920443dd266b668961570cb6b7b38a1146ed3f6499e772b5c360'
MAX_BYTES = 8 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exclusive_json(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')
    require(len(raw) <= MAX_BYTES, 'Output exceeds original tool bound')
    with path.open('xb') as handle:
        handle.write(raw)
    return raw


def read_bounded(path):
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'Input exceeds original tool bound')
    return raw


def canonical_abi_type(row):
    if row['type'].startswith('tuple'):
        return '(' + ','.join(canonical_abi_type(child) for child in row['components']) + ')' + row['type'][5:]
    return row['type']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-input', type=Path, help='Original retained current-source illustrative input; otherwise use its already-published exact archive member')
    parser.add_argument('--output-directory', type=Path, required=True, help='New exclusive directory; never an existing artifact or live configuration')
    args = parser.parse_args()
    module = ROOT / 'zzz_ops/opensea_drop.py'
    require(digest(read_bounded(module)) == MODULE_SHA256, 'Changed production reviewer requires a new source review')
    if args.source_input is not None:
        original = read_bounded(args.source_input)
        provenance = str(args.source_input)
    else:
        archive_raw = read_bounded(OLD_ARCHIVE)
        require(digest(archive_raw) == OLD_ARCHIVE_SHA256, 'Changed retained evidence archive')
        with zipfile.ZipFile(OLD_ARCHIVE) as archive:
            original = archive.read('current-source-cli/input.json')
        provenance = 'reports/readiness-advance-20261120/evidence.zip!current-source-cli/input.json'
    require(digest(original) == OLD_INPUT_SHA256, 'Changed retained illustrative example')
    base = json.loads(original)
    request = copy.deepcopy(base['manifest']['request'])
    require(request['mint_price_wei'] == '50000000000000000' and request['team_allocation'] == '20' and
        request['allowlist_allocation'] == '500' and request['release_unused_team_to_public'] is False,
        'Retained economic defaults differ')
    before = {name: digest(read_bounded(ROOT / name)) for name in request['source_sha256']}
    require(before == request['source_sha256'], 'Retained actual source graph no longer matches')
    sys.path.insert(0, str(ROOT))
    from zzz_ops.abi import keccak256
    from zzz_ops.opensea_drop import ALLOWLIST_MINT, PARAM_FIELDS
    upstream_abi_path = ROOT / 'reports/opensea-integration-20261109/official-seadrop/derived/abi.json'
    upstream_abi = read_bounded(upstream_abi_path)
    require(digest(upstream_abi) == ABI_SHA256, 'Changed retained upstream ABI')
    rows = [row for row in json.loads(upstream_abi) if row.get('type') == 'function' and row.get('name') == 'mintAllowList']
    require(len(rows) == 1, 'Ambiguous upstream mint ABI')
    upstream_signature = 'mintAllowList(' + ','.join(canonical_abi_type(row) for row in rows[0]['inputs']) + ')'
    require(upstream_signature == ALLOWLIST_MINT, 'Current reviewer selector differs from retained actual ABI')
    args.output_directory.mkdir(exist_ok=False)
    out = args.output_directory
    receipts = []
    env = {key: value for key, value in os.environ.items()
        if not any(secret in key.upper() for secret in ('PRIVATE_KEY', 'MNEMONIC', 'RPC_URL', 'API_KEY', 'PASSWORD', 'TOKEN'))}
    def invoke(command_name, input_path, output_path, label):
        command = [sys.executable, 'scripts/prepare-opensea-drop.py', command_name, str(input_path), '--output', str(output_path)]
        start = time.perf_counter()
        process = subprocess.run(command, cwd=ROOT, capture_output=True, env=env, timeout=60)
        (out / (label + '.stdout')).write_bytes(process.stdout)
        (out / (label + '.stderr')).write_bytes(process.stderr)
        receipt = dict(command=command, returncode=process.returncode, elapsed_seconds=time.perf_counter()-start,
            input_sha256=digest(read_bounded(input_path)), output_sha256=digest(read_bounded(output_path)) if output_path.exists() else None,
            stdout_sha256=digest(process.stdout), stderr_sha256=digest(process.stderr))
        receipts.append(receipt)
        if process.returncode:
            exclusive_json(out / 'FAILED_EXECUTION.json', dict(receipts=receipts, production_approved=False))
            raise ValueError('Offline CLI refused; original artifacts and failure evidence retained')
    started = datetime.now(timezone.utc).isoformat()
    exclusive_json(out / 'illustrative-phase-request.json', request)
    invoke('prepare', out / 'illustrative-phase-request.json', out / 'rebuilt-phase-manifest.json', 'prepare')
    rebuilt = json.loads(read_bounded(out / 'rebuilt-phase-manifest.json'))
    require(rebuilt == base['manifest'], 'Identical reviewed request did not reproduce its original exact manifest/proofs')
    facts = []
    for phase, quantity in [('team', 2), ('allowlist', 1)]:
        proof_record = next(row for row in rebuilt['proofs'] if row['phase'] == phase)
        params = proof_record['mint_params']
        minter = proof_record['minter']
        values = [int(request['nft_contract'],16), int(request['fee_recipient'],16), 0, quantity]
        values += [int(params[field]) for field in PARAM_FIELDS]
        values += [13 * 32, len(proof_record['proof'])]
        raw = keccak256(ALLOWLIST_MINT.encode())[:4] + b''.join(value.to_bytes(32,'big') for value in values)
        raw += b''.join(bytes.fromhex(sibling[2:]) for sibling in proof_record['proof'])
        window = request[phase + '_window']
        timestamp = (int(window['start']) + int(window['end'])) // 2
        value_wei = quantity * int(params['mintPrice'])
        review_request = dict(schema=1, manifest=rebuilt,
            intent=dict(caller=minter, minter=minter, phase=phase, quantity=str(quantity), review_timestamp=str(timestamp)),
            unsigned_transaction=dict(chain_id='4663', **{'from':minter, 'to':request['seadrop'], 'value':str(value_wei), 'data':'0x'+raw.hex()}))
        input_path, output_path = out / (phase + '-input.json'), out / (phase + '-review.json')
        exclusive_json(input_path, review_request)
        invoke('review-mint', input_path, output_path, phase)
        result = json.loads(read_bounded(output_path))
        require(result['unsigned_transaction'] == review_request['unsigned_transaction'] and not result['calldata_modified'], 'Reviewer changed the supplied exact transaction')
        require(result['recipient'] == minter and result['payer'] == minter and result['gross_native_value_wei'] == str(value_wei), 'Wrong phase recipient/payment')
        require(all(not value for key,value in result['boundaries'].items() if key != 'offline_only') and result['boundaries']['offline_only'] is True, 'A live readiness gate was incorrectly opened')
        facts.append(dict(phase=phase, quantity=quantity, gross_native_value_wei=str(value_wei), recipient=minter,
            calldata_bytes=len(raw), proof_siblings=len(proof_record['proof']), calldata_sha256=digest(raw),
            leaf=proof_record['leaf'], merkle_root=rebuilt['allowlist_root'], review_hash=result['review_hash'],
            input_sha256=digest(read_bounded(input_path)), output_sha256=digest(read_bounded(output_path)),
            transaction_preserved=True, live_readiness_flags_false=True))
    after = {name: digest(read_bounded(ROOT / name)) for name in request['source_sha256']}
    require(before == after, 'Source graph changed during offline example preparation')
    result = dict(schema=1, kind='new_actual_repository_source_phase_examples_with_illustrative_marketplace_inputs',
        started_utc=started, module_sha256=MODULE_SHA256, original_example_sha256=OLD_INPUT_SHA256,
        original_example_provenance=provenance, source_graph_count=len(before), source_sha256=before,
        source_inputs_unchanged=True, exact_rebuilt_manifest_matches_retained=True, examples=facts, cli_receipts=receipts,
        api_payload_received=False, actual_collection_deployed=False, actual_participants_or_sale_times=False,
        illustrative_fee_bps=request['fee_bps'], actual_opensea_fee_accepted=False,
        public_example_repeated=False, unchanged_unit_tests_rerun=0, network_calls=0,
        signing=False, transactions_submitted=0, opensea_primary_drop_accepted=False, production_approved=False)
    exclusive_json(out / 'EXECUTION.json', result)
    print(json.dumps({'new_phase_examples':len(facts),'new_cli_invocations':len(receipts),'actual_source_pins':len(before),
        'team_gross_wei':facts[0]['gross_native_value_wei'],'allowlist_gross_wei':facts[1]['gross_native_value_wei'],
        'unchanged_unit_tests_rerun':0,'network_calls':0,'production_approved':False}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError,OSError,KeyError,TypeError,subprocess.TimeoutExpired) as error:
        print('Phase example preparation refused: '+str(error), file=sys.stderr)
        raise SystemExit(2)
