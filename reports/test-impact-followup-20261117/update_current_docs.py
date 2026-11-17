"""Reconcile current guidance without rewriting historical reports or task status."""
from difflib import SequenceMatcher
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def write(path,text):
    path=ROOT/path;before=path.read_bytes();after=text.encode('utf-8')
    old=before.splitlines(keepends=True);new=after.splitlines(keepends=True)
    clean=lambda rows:[row.rstrip(b'\r\n') for row in rows]
    result=[]
    for kind,a,b,c,d in SequenceMatcher(a=clean(old),b=clean(new),autojunk=True).get_opcodes():
        result.extend(old[a:b] if kind=='equal' else new[c:d])
    assert clean(result)==clean(new)
    path.write_bytes(b''.join(result))


def main():
    for name in ('README.md','AGENTS.md','PROJECT_CONTEXT.md','docs/WORK_HANDOFF.md','docs/IMPLEMENTATION_STATUS.md'):
        path=ROOT/name;text=path.read_text(encoding='utf-8')
        intro=text.split('\n\n',2)[1]
        assert 'test-seal-deep-review-20261117' in intro or 'test-impact-followup-20261117' in intro,name
        prefix='../' if name.startswith('docs/') else ''
        paragraph=(f'The [repaired-test impact follow-up]({prefix}reports/test-impact-followup-20261117/REVIEW.md) '
            'traces affected fixtures into LP maintenance, rewards, recovery, keeper submission and manual preparation. '
            'It fixes a late manual-review reorg race and stale test expectations, with source-scoped behavioral checks rather than a claimed full-suite pass. '
            'All61 Solidity sources, financial rights/defaults and live environments remain unchanged. '
            'The trusted build remains seal-boundaries-20261117; actual dependencies, operating qualification and independent approval remain open.')
        write(name,text.replace(intro,paragraph,1))
    path='docs/MANUAL_LP_PREPARATION.md';text=(ROOT/path).read_text(encoding='utf-8')
    old=('6. Revalidate through the actual operator wallet immediately before any separate\n'
         '   signing decision. The last head/deadline check follows slow RPC work, but later\n')
    new=('6. Revalidate through the actual operator wallet immediately before any separate\n'
         '   signing decision. After the last head read, the tool re-reads the exact final\n'
         '   simulation height, even when the head advanced. An orphaned simulation anchor\n'
         '   refuses the review with `final_anchor_changed`; a healthy new head does not\n'
         '   by itself invalidate the review. The last checks follow slow RPC work, but later\n')
    assert old in text or new in text;write(path,text.replace(old,new,1))
    path='docs/OPERATOR_MANUAL.md';text=(ROOT/path).read_text(encoding='utf-8')
    marker='No key, nonce, signer or pending journal is accessed. Output is a review candidate,'
    addition=('The preparer rechecks the exact simulated block after its last head read,\n'
              'including when a newer head appears. `final_anchor_changed` means discard\n'
              'that candidate and prepare again from current canonical state; do not extend\n'
              'its expiry or edit the saved artifact. Healthy head advancement can pass.\n'
              'These separate reads are not an atomic guarantee against later reorgs or\n'
              'market changes; repeat exact validation through the authorized wallet.\n\n')
    assert marker in text
    if addition not in text:write(path,text.replace(marker,addition+marker,1))
    path='docs/DEVELOPMENT.md';text=(ROOT/path).read_text(encoding='utf-8')
    marker='For current native financial fixtures, keep their execution interfaces current'
    addition=('After repairing a shared fixture, trace import/inheritance consumers and\n'
              'the intended production branches before carrying any old evidence forward.\n'
              'Check current percentage/unit expectations and callback timing; a generic\n'
              'revert or a passing setup does not establish the advertised failure. Use\n'
              'focused cross-action/physical checks for genuinely affected paths and keep\n'
              'inventory, source review and execution distinct. See the\n'
              '[impact follow-up](../reports/test-impact-followup-20261117/REVIEW.md).\n\n')
    assert marker in text
    if addition not in text:write(path,text.replace(marker,addition+marker,1))
    path='docs/project-todo.json';obj=json.loads((ROOT/path).read_text(encoding='utf-8'))
    tasks={row['id']:row for area in obj['areas'] for row in area['tasks']}
    updates={
        'local-verification':'Trace repaired test fixtures into their intended production behavior and dependent methods; distinguish declaration exposure, source review, finite cross-action/physical execution and unqualified workloads. Current percentage/native-backing expectations and exact failure-stage proofs are corrected. [Impact follow-up](reports/test-impact-followup-20261117/REVIEW.md) preserves earlier records and actual failures; no full-suite or market approval is implied.',
        'security-integration':'Manual B/C/D and Parked D preparation rechecks the exact simulated height after reading the last head, including head advancement; a late orphaned anchor refuses review. Healthy advancement and existing fee/calldata/expiry/authority limits remain. These separate RPC reads are not an atomic future-chain guarantee; actual wallet/provider acceptance remains open. [Source-scoped follow-up](reports/test-impact-followup-20261117/TOOLS_REVIEW.md).',
        'keeper-guardrails':'Verify the actual cycle-to-submit dry-run path after the hourly harvest clock crosses during another maintenance failure: complete void simulation is required, malformed output must stop before estimation, and no simulated submission may advance pending/spend/harvest-success state. New injected-RPC checks cover this without changing keeper software or operating configuration. [Impact follow-up](reports/test-impact-followup-20261117/TOOLS_REVIEW.md).',
    }
    for key,value in updates.items():
        if value not in tasks[key]['acceptance']:tasks[key]['acceptance'].append(value)
    write(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    path='reports/README.md';text=(ROOT/path).read_text(encoding='utf-8');head,tail=text.split('\n',1)
    addition=('\n[Repaired-test impact follow-up](test-impact-followup-20261117/REVIEW.md) '
              'checks intended dependent behavior and fixes a late manual-review reorg race; '
              'source review, finite execution and remaining workload limits stay separate.\n')
    if addition not in text:write(path,head+'\n'+addition+tail)
    path='.gitattributes';text=(ROOT/path).read_text(encoding='utf-8')
    if 'reports/test-impact-followup-20261117/**' not in text:
        write(path,text+'\n# Preserve exact repaired-test impact observations and original failures.\n'
                   'reports/test-impact-followup-20261117/** -text whitespace=cr-at-eol,-blank-at-eol,-blank-at-eof\n')
    print('Current docs and acceptance criteria updated; all task statuses retained.')


if __name__=='__main__':main()
