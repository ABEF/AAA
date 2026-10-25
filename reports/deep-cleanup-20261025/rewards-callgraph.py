"""Read-only compiler-AST triage; not a compiler proof or a replacement for upstream review."""
from pathlib import Path
import argparse, hashlib, json


def walk(n):
    if isinstance(n, dict):
        yield n
        for value in n.values():
            yield from walk(value)
    elif isinstance(n, list):
        for value in n:
            yield from walk(value)


def cycles(graph):
    index = {}; low = {}; stack = []; active = set(); result = []
    def visit(v):
        index[v] = low[v] = len(index); stack.append(v); active.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                visit(w); low[v] = min(low[v], low[w])
            elif w in active:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            component = []
            while True:
                w = stack.pop(); active.remove(w); component.append(w)
                if w == v: break
            if len(component) > 1 or v in graph.get(v, ()):
                result.append(sorted(component))
    for v in graph:
        if v not in index: visit(v)
    return result


def main():
    p = argparse.ArgumentParser(); p.add_argument('--input', type=Path, required=True)
    p.add_argument('--ast', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); inputs = json.loads(args.input.read_text(encoding='utf-8'))
    output = json.loads(args.ast.read_text(encoding='utf-8'))
    errors = [x for x in output.get('errors',[]) if x.get('severity') == 'error']
    if errors:
        raise SystemExit(f"Refusing incomplete compiler output: {len(errors)} compiler error(s)")
    if not output.get('sources') or any('ast' not in s for s in output['sources'].values()):
        raise SystemExit('Refusing absent or incomplete compiler AST inventory')
    nodes = {}; files = {}; containers = {}; contracts = {}
    for path, source in output['sources'].items():
        for n in walk(source['ast']):
            if 'id' in n: nodes[n['id']] = n; files[n['id']] = path
            if n.get('nodeType') == 'ContractDefinition':
                contracts[n['id']] = n
                for item in n.get('nodes', []):
                    if item.get('nodeType') in ('FunctionDefinition', 'ModifierDefinition'):
                        containers[item['id']] = n['id']
    definitions = {k: n for k,n in nodes.items() if n.get('nodeType') in ('FunctionDefinition','ModifierDefinition')}
    def label(k):
        n = nodes[k]; contract = contracts.get(containers.get(k), {})
        return f"{files[k]}:{contract.get('name','')}:{n.get('name') or n.get('kind')}#{k}"
    def bases(k):
        result = set(nodes[k].get('baseFunctions', []))
        for base in list(result): result |= bases(base)
        return result
    roots = [k for k,n in contracts.items() if files[k].startswith('src/') and not n.get('abstract')
             and n.get('contractKind') == 'contract']
    if not {'ZZZNFT','ZZZRoyaltyRewards'} <= {contracts[k]['name'] for k in roots}:
        raise SystemExit('Refusing absent required production contract roots')
    root_results = []; all_unknown = {}; all_named_require = []; all_yul = []
    for root in roots:
        hierarchy = contracts[root]['linearizedBaseContracts']; override = {}
        for contract in reversed(hierarchy):
            for item in contracts[contract].get('nodes', []):
                if item.get('nodeType') == 'FunctionDefinition' and item.get('body'):
                    for base in bases(item['id']): override[base] = item['id']
        queue = [k for k in definitions if containers.get(k) in hierarchy and definitions[k].get('body')]
        graph = {}; unresolved = []; seen_asm = set()
        while queue:
            k = queue.pop()
            if k in graph: continue
            graph[k] = set()
            # Include modifier invocations and modifier arguments attached outside the body.
            for n in walk(definitions[k]):
                if n.get('nodeType') == 'FunctionCall':
                    expression = n.get('expression', {}); tid = expression.get('typeDescriptions',{}).get('typeIdentifier','')
                    if expression.get('name') == 'require' and len(n.get('arguments',[])) >= 2:
                        error = n['arguments'][1]
                        if error.get('nodeType') == 'FunctionCall' and error.get('names'):
                            all_named_require.append({'function':label(k),'src':n['src'],'names':error['names']})
                    if tid.startswith('t_function_internal'):
                        target = expression.get('referencedDeclaration')
                        if target in definitions:
                            # Calls through super or an explicit base type retain that statically selected body.
                            # Unqualified virtual calls dispatch against this concrete root's linearized overrides.
                            if expression.get('nodeType') == 'Identifier': target = override.get(target,target)
                            if definitions[target].get('body'):
                                graph[k].add(target); queue.append(target)
                        elif target is None or target >= 0:
                            unresolved.append({'function':label(k),'src':n['src'],'expression':expression})
                elif n.get('nodeType') == 'ModifierInvocation':
                    target = n.get('modifierName',{}).get('referencedDeclaration')
                    if target in definitions:
                        graph[k].add(target); queue.append(target)
                elif n.get('nodeType') == 'InlineAssembly' and n['id'] not in seen_asm:
                    seen_asm.add(n['id']); assembly = n.get('AST',{})
                    functions = {x['name']:x for x in walk(assembly) if x.get('nodeType') == 'YulFunctionDefinition'}
                    yg = {name:{x.get('functionName',{}).get('name') for x in walk(fn['body'])
                                if x.get('nodeType') == 'YulFunctionCall'} & functions.keys()
                          for name,fn in functions.items()}
                    all_yul.append({'root':contracts[root]['name'],'function':label(k),'src':n['src'],
                                    'functions':sorted(functions),'recursive_components':cycles(yg)})
        for item in unresolved: all_unknown[(item['function'],item['src'])] = item
        root_results.append({'contract':contracts[root]['name'],'source':files[root],
                             'node_count':len(graph),'edge_count':sum(map(len,graph.values())),
                             'recursive_components':[[label(x) for x in group] for group in cycles(graph)],
                             'unresolved_internal_calls':len(unresolved),
                             'internal_edges':{label(k):sorted(label(x) for x in v) for k,v in graph.items()}})
    hashes = {path:hashlib.sha256(v['content'].encode()).hexdigest() for path,v in inputs['sources'].items()}
    result = {'scope':'All concrete production src contracts plus reached installed dependency/library internal bodies',
              'compiler_input_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),
              'compiler_output_sha256':hashlib.sha256(args.ast.read_bytes()).hexdigest(),
              'closed_input_inventory':set(inputs['sources']) == set(output['sources']),
              'input_sources':hashes,'roots':root_results,
              'unresolved_internal_calls':list(all_unknown.values()),
              'named_error_require_calls':list({json.dumps(x,sort_keys=True):x for x in all_named_require}.values()),
              'assembly_function_scopes':all_yul,
              'distinct_inline_assembly_scopes':len({(x['function'],x['src']) for x in all_yul}),
              'limits':['External calls/reentrant callbacks are separate EVM call frames and are not internal recursion.',
                        'Ordinary lexical function calls and modifier invocations are included. Abstract unimplemented bodies are excluded.',
                        'Unqualified virtual dispatch follows compiler baseFunctions and each concrete root linearization; explicit base/super/library calls retain resolved target.',
                        'Manual review must resolve function pointers, unusual AST expressions, assembly scoping and compiler-generated code; this is applicability triage, not proof of compiler correctness.']}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'roots':len(root_results),'recursive_components':sum(len(x['recursive_components']) for x in root_results),
                      'unresolved_internal_calls':len(all_unknown),'named_error_require_calls':len(result['named_error_require_calls']),
                      'assembly_root_contexts':len(all_yul),'distinct_inline_assembly_scopes':result['distinct_inline_assembly_scopes'],
                      'output':str(args.output)},indent=2))


if __name__ == '__main__': main()
