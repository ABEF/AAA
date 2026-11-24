"""NEW read-only c7ff saved-vector review. Never imports/runs keeper or tests.

Required: original BEFORE_ON/AFTER_ON, BEFORE_OFF/AFTER_OFF and RESULT JSON.
Optional public report closure: --public-root, with its evidence manifest.
Writes nothing; emits a bounded verification JSON on stdout for caller capture.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, re, stat, sys

MAX_FILE = 16 * 1024 * 1024
MAX_PUBLIC_TOTAL = 64 * 1024 * 1024
MAX_MEMBERS = 512
BUCKET = 47181787163762592248710325652087236475813397965818762058663276509558631703230
ZERO = '0x' + '0' * 40
ZZZ = '0x7dbf38976f6d3b9c529e7d9484a71898b409ee6a'
FEES_COLLECTED = '0xa54e6c2fc0861aa9c991b26891d71059d517983b9e84b91020f42609c452eb9d'
POOL_REWARDS_CREDITED = '0xd2be5953426407e79d42608bb76bb75c5c665102042c6c4279d64a4e414b17aa'

class Refused(ValueError): pass

def need(ok, message):
    if not ok: raise Refused(message)

def uint(value, name):
    if type(value) is str:
        need(re.fullmatch(r'0|[1-9][0-9]{0,77}', value) is not None, name + ': invalid decimal')
        value = int(value)
    need(type(value) is int and 0 <= value < 1 << 256, name + ': invalid unsigned value')
    return value

def quantity(value, name):
    need(type(value) is str and re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]{0,63})', value) is not None,
         name + ': invalid hexadecimal quantity')
    return int(value, 16)

def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON member')
        result[key] = value
    return result

def read_json(path):
    path = Path(path)
    st = path.lstat()
    need(stat.S_ISREG(st.st_mode) and not path.is_symlink() and st.st_size <= MAX_FILE,
         'Input must be a bounded regular file')
    raw = path.read_bytes()
    need(len(raw) == st.st_size, 'Input changed while reading')
    def bad_constant(_): raise Refused('Non-finite JSON constant')
    value = json.loads(raw.decode('utf-8', 'strict'), object_pairs_hook=unique, parse_constant=bad_constant)
    return value, {'name': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def address(value):
    need(type(value) is str and re.fullmatch(r'0x[0-9a-fA-F]{40}', value) is not None,
         'Invalid address')
    return value.lower()

def words(raw, count):
    need(type(raw) is str and len(raw) == 2 + count * 64 and re.fullmatch(r'0x[0-9a-fA-F]*', raw) is not None,
         'Wrong exact event data shape')
    return [int(raw[i:i+64], 16) for i in range(2, len(raw), 64)]

def verify_stage(tag, before_doc, after_doc):
    before = before_doc['snapshot']; after = after_doc['snapshot']
    receipt = after_doc['receipt']; tx = after_doc['actual_transaction_without_signature']; header = after_doc['header']
    need(receipt['status'] == '0x1', tag + ': transaction did not succeed')
    need(tx['hash'] == receipt['transactionHash'] and tx['blockHash'] == receipt['blockHash'] == header['hash']
         and tx['blockNumber'] == receipt['blockNumber'] == header['number'], tag + ': inclusion mismatch')
    need(address(tx['to']) == '0x6e113da826ec57f968fff0f7cb7c0163b6b31db1', tag + ': not this frozen Vault')
    need(before['rights'] == after['rights'] and before['total_shares'] == after['total_shares'],
         tag + ': NFT rights/shares changed')
    need(before['group'][0] == after['group'][0] and before['group'][4] == after['group'][4],
         tag + ': pool/deposit bookkeeping changed')
    need(uint(after['group'][6], 'lastRebalance') == quantity(header['timestamp'], 'timestamp'),
         tag + ': rebalance clock does not match inclusion')
    need(after['policy']['pending'] == 0 and after['policy']['applied'] == after['policy']['geometry'],
         tag + ': desired geometry not physically committed')
    harvests = []; reward_events = {ZERO: [], ZZZ: []}
    for event in receipt['logs']:
        need(event['transactionHash'] == receipt['transactionHash'] and event['blockHash'] == header['hash']
             and event['blockNumber'] == header['number'] and event.get('removed') is False,
             tag + ': event inclusion mismatch')
        topics = event.get('topics', [])
        if address(event['address']) == address(tx['to']) and topics and topics[0].lower() == FEES_COLLECTED:
            need(len(topics) == 2 and int(topics[1], 16) == BUCKET, tag + ': wrong harvested bucket')
            harvests.append(words(event['data'], 2))
        if address(event['address']) == '0x05c2d0f16cc810acad17168446f52d60d4733062' and topics and topics[0].lower() == POOL_REWARDS_CREDITED:
            need(len(topics) == 3 and int(topics[1], 16) == BUCKET, tag + ': wrong credited bucket')
            token_value = int(topics[2], 16); need(0 <= token_value < 1 << 160, tag + ': oversized token topic')
            token = '0x' + token_value.to_bytes(20, 'big').hex()
            need(token in reward_events, tag + ': unsupported LP currency')
            reward_events[token].append(words(event['data'], 2))
    # In these ordinary whole replacements, one Vault event contains BOTH leg receipts.
    need(len(harvests) == 1, tag + ': expected one aggregate actual harvest, not double-counted legs')
    rows = {}
    for index, token in enumerate((ZERO, ZZZ)):
        old = before['funds'][token]; new = after['funds'][token]
        dust = uint(old['dust'], 'old dust'); units = 0
        for amounts in harvests:
            units_now, dust = divmod(dust + amounts[index], 20); units += units_now
        gross = sum(amounts[index] for amounts in harvests)
        expected_release = uint(old['compound'], 'old compound') + units
        # Stronger NEW check, absent from the original frozen worker assertions.
        need(uint(new['compound'], 'new compound') == 0, tag + ': compound reserve was not fully reinvested')
        inferred_release = uint(old['accounted'], 'old accounted') + gross - 18 * units - uint(new['accounted'], 'new accounted')
        need(inferred_release == expected_release, tag + ': released amount differs from all old/new designated compound')
        need(new['dust'] == dust and new['buyback'] == old['buyback'] + units,
             tag + ': dust or buyback split differs')
        need(new['fees_balance'] == old['fees_balance'] + gross - 18 * units - expected_release,
             tag + ': physical fee backing debit differs')
        need(new['accounted'] == old['accounted'] + gross - 18 * units - expected_release,
             tag + ': classified fee debit differs')
        need(new['liabilities'] == old['liabilities'] + 18 * units and new['rewards_balance'] == old['rewards_balance'] + 18 * units,
             tag + ': funded holder liability or backing differs')
        need(new['orphaned'] == old['orphaned'] and new['direct_liabilities'] == old['direct_liabilities'],
             tag + ': unrelated reward classifications changed')
        need(sum(sum(uint(v, 'new claim') for v in pair) for pair in new['claims']) == sum(sum(uint(v, 'old claim') for v in pair) for pair in old['claims']) + 18 * units,
             tag + ': complete two-NFT claim aggregate differs')
        need(sum(v[0] for v in reward_events[token]) == 16 * units and sum(v[1] for v in reward_events[token]) == 2 * units,
             tag + ': authenticated80/10 credit events differ')
        for snapshot, row in ((before, old), (after, new)):
            need(row['accounted'] == row['dust'] + row['compound'] + row['buyback']
                 and row['fees_balance'] >= row['accounted'] and row['rewards_balance'] >= row['liabilities'] + row['orphaned']
                 and row['vault_balance'] >= row['total_idle'] == snapshot['group'][2 + index],
                 tag + ': reserve/idle backing mismatch')
        rows[token] = {'actual_harvested': gross, 'units_of_twenty': units, 'post_compound': 0,
                       'released_all_old_and_new_compound': expected_release, 'holder_credit': 18 * units,
                       'individual_credit': 16 * units, 'collective_credit': 2 * units,
                       'buyback_credit': units, 'remaining_dust': dust}
    if tag == 'ON':
        need(len(before['legs']) == 1 and len(after['legs']) == 2, 'ON: physical one-to-two transition absent')
    else:
        need(len(before['legs']) == 2 and len(after['legs']) == 1 and after['active_secondary_count'] == 0,
             'OFF: physical two-to-one merge absent')
    # Use the pre-execution lower-price vector; never revalue away a loss after the swap.
    def value(amounts):
        return sum(uint(amounts[i], 'raw principal') * uint(before['prices'][token]['bounds'][0], 'price')
                   // uint(before['prices'][token]['scale'], 'scale') for i, token in enumerate((ZERO, ZZZ)))
    main = value(after['legs'][0]['amounts']); residual = value(after['legs'][1]['amounts']) if tag == 'ON' else 0
    idle = value(after['group'][2:4]); total = main + residual + idle; floor = uint(after['policy']['main_floor'], 'main floor')
    need(main > 0 and total > 0, tag + ': no live principal value')
    if tag == 'ON':
        need(main >= (total * floor + 9999) // 10000 and residual <= total * (10000-floor) // 10000,
             'ON: main/residual allocation bounds fail')
    return {'tag': tag, 'fees': rows, 'main_value': main, 'residual_value': residual,
            'attributed_idle_value': idle, 'total_postcost_value': total, 'main_floor_bps': floor,
            'per_NFT_phase_oracle_requalified': False,
            'captured_price_scope': 'saved stable controlled pre-execution lower marks; no live market-source qualification'}

def public_closure(root):
    root = Path(root).resolve(strict=True); manifest_path = root / 'verification/EVIDENCE_MANIFEST.json'
    manifest, identity = read_json(manifest_path)
    need(type(manifest) is dict and type(manifest.get('files')) is list and len(manifest['files']) <= MAX_MEMBERS,
         'Public manifest shape/member bound differs')
    pins = {}; total = 0
    for row in manifest['files']:
        name = row.get('path'); need(type(name) is str and chr(92) not in name, 'Non-canonical public member path')
        rel = PurePosixPath(name)
        need(not rel.is_absolute() and rel.parts and rel.as_posix() == name and all(p not in ('', '.', '..') for p in rel.parts), 'Unsafe or non-canonical public member path')
        need(type(row.get('sha256')) is str and re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is not None,
             'Malformed public SHA256 pin')
        size = uint(row.get('bytes'), 'manifest bytes'); need(size <= MAX_FILE, 'Public file exceeds bounded review size')
        if name in pins:
            need(pins[name] == (size, row['sha256']), 'Conflicting duplicate public pin'); continue
        path = root.joinpath(*rel.parts)
        need(path.resolve(strict=True).is_relative_to(root), 'Public member resolves outside report')
        need(all(not root.joinpath(*rel.parts[:i]).is_symlink() for i in range(1, len(rel.parts)+1)),
             'Symlink in public member path')
        st = path.lstat(); need(stat.S_ISREG(st.st_mode) and st.st_size == size, 'Public member size/type differs')
        total += size; need(total <= MAX_PUBLIC_TOTAL, 'Public evidence total exceeds64MiB review bound')
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(65536), b''): digest.update(chunk)
        need(digest.hexdigest() == row['sha256'], 'Public evidence hash differs: ' + name)
        pins[name] = (size, row['sha256'])
    checked_roots = ('evidence', 'verification'); extras = []
    for dirname in checked_roots:
        folder = root / dirname
        if not folder.exists(): continue
        for path in folder.rglob('*'):
            need(not path.is_symlink(), 'Symlink found in evidence closure')
            if path.is_file():
                name = path.relative_to(root).as_posix()
                if name != 'verification/EVIDENCE_MANIFEST.json' and name not in pins: extras.append(name)
    need(not extras, 'Unlisted evidence/tool members: ' + ','.join(extras[:8]))
    return {'status': 'passed', 'manifest': identity, 'unique_members': len(pins), 'total_reviewed_bytes': total,
            'closure_roots': list(checked_roots), 'self_manifest_excluded_to_avoid_recursion': True,
            'not_external_chain_authentication_or_release_approval': True}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before-on', 'after-on', 'before-off', 'after-off', 'result'): parser.add_argument('--'+name, required=True)
    parser.add_argument('--public-root', help='Optional report root; missing means public closure is NOT verified')
    args = parser.parse_args(); docs = {}; identities = {}
    for name in ('before_on', 'after_on', 'before_off', 'after_off', 'result'):
        docs[name], identities[name] = read_json(getattr(args, name))
    result = docs['result']; need(result.get('success') is True and result.get('source_inputs_preserved') is True,
                                'Source runtime result is not a complete successful preserved-input journey')
    need(result.get('public_transactions') == result.get('new_seals') == result.get('old_test_bodies_run') == 0,
         'Runtime preservation scope differs')
    need(result.get('raw_submission_attempts') == result.get('reviewed_raw_forward_attempts') == 2,
         'Unexpected raw submission count')
    reviews = [verify_stage('ON', docs['before_on'], docs['after_on']),
               verify_stage('OFF', docs['before_off'], docs['after_off'])]
    closure = public_closure(args.public_root) if args.public_root else {'status': 'not_requested_not_verified'}
    output = {'schema': 1, 'accounting_verification': 'passed', 'public_evidence_closure': closure,
              'stages': reviews, 'input_identities': identities, 'new_runtime_transactions': 0,
              'old_test_bodies_run': 0, 'production_source_changes': False, 'production_approved': False,
              'limitations': ['Only this finite two-NFT controlled logical-time journey is checked.',
                'Exact aggregate80/10/5/5 and full compound release are checked; per-NFT prior phase carry is not independently replayed.',
                'Snapshot physical-amount/fingerprint and clock-seam proofs retain the original runtime source scope.',
                'Hash/closure checks bind retained bytes, not honesty of RPC/providers or actual market-source independence.',
                'Unlisted top-level narrative docs are outside artifact closure; all listed manifest paths are still verified.']}
    print(json.dumps(output, sort_keys=True, indent=2, allow_nan=False)); return 0

if __name__ == '__main__':
    try: raise SystemExit(main())
    except (Refused, ValueError, KeyError, TypeError, OSError, ZeroDivisionError) as exc:
        print(json.dumps({'schema':1,'accounting_verification':'refused','error_type':type(exc).__name__,
                          'reason':str(exc)[:512],'new_runtime_transactions':0,'old_test_bodies_run':0,
                          'production_approved':False},sort_keys=True)); raise SystemExit(1)
