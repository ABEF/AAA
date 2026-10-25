#!/usr/bin/env python3
"""Generate/check the source-bound callable contract reference without compilation."""
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from zzz_ops.function_reference import ReferenceError, generate, import_compiler, merge_notes, write_atomic


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--compiler-input',type=Path)
    parser.add_argument('--compiler-output',type=Path)
    parser.add_argument('--size-report',type=Path)
    parser.add_argument('--notes',type=Path,action='append')
    parser.add_argument('--output-json',type=Path)
    parser.add_argument('--output-md',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args(argv)
    root=args.root.resolve()
    notes=root/'docs/function-reference-notes.json'
    out_json=args.output_json or root/'docs/function-reference.json'
    out_md=args.output_md or root/'docs/CONTRACT_FUNCTIONS.md'
    try:
        supplied=[args.compiler_input,args.compiler_output,args.size_report]
        if any(supplied) and not all(supplied):
            raise ReferenceError('Provide compiler input, output and size report together')
        base=import_compiler(root,*supplied) if all(supplied) else None
        if args.notes:
            merged=merge_notes(args.notes)
            if args.check:
                raise ReferenceError('--check uses committed explanation inputs; it never rewrites notes')
            # The data is validated against the exact ABI before note publication.
            if base is None:
                from zzz_ops.function_reference import load_json
                base=load_json(out_json)
            from zzz_ops.function_reference import build_reference
            build_reference(root,base,merged)
            write_atomic(notes,json.dumps(merged,ensure_ascii=False,indent=2)+'\n')
        counts=generate(root,notes,out_json,out_md,base=base,check=args.check)
    except (ReferenceError,OSError,ValueError,KeyError,TypeError) as exc:
        print('Function reference check failed: '+str(exc),file=sys.stderr)
        return 1
    print(json.dumps({'checked':args.check,**counts}))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
