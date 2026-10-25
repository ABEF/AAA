"""Generate current and reviewed historical event schemas; reject ambiguous layouts."""
from pathlib import Path
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from zzz_ops.abi import keccak256

ROOT = Path(__file__).resolve().parents[1]
ERC721_EVENTS = (
    'event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);',
    'event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);',
    'event ApprovalForAll(address indexed owner, address indexed operator, bool approved);',
)


def build_schema(texts):
    schema = {}
    for text in texts:
        for name, arguments in re.findall(r'event\s+(\w+)\s*\((.*?)\)\s*;', text, re.S):
            fields = []
            for argument in arguments.split(','):
                terms = argument.strip().split()
                if not terms:
                    continue
                fields.append({'type': terms[0], 'name': terms[-1], 'indexed': 'indexed' in terms})
            signature = f"{name}({','.join(field['type'] for field in fields)})"
            topic = '0x' + keccak256(signature.encode()).hex()
            entry = {'name': name, 'signature': signature, 'fields': fields}
            previous = schema.get(topic)
            if previous is not None:
                # Parameter names are not part of the ABI. Keep the first
                # declaration's canonical decoder names rather than silently
                # renaming existing fields when another module adds an alias.
                old_layout = [(field['type'], field['indexed']) for field in previous['fields']]
                new_layout = [(field['type'], field['indexed']) for field in fields]
                if previous['signature'] != signature or old_layout != new_layout:
                    raise ValueError(f'Conflicting event topic {topic}: '
                                     f"{previous['signature']} versus {signature}")
                continue
            schema[topic] = entry
    return schema


def source_schema(root=ROOT):
    # Shared/base implementations declare events inherited by concrete modules.
    # Keep the existing top-level declarations first so inherited aliases cannot
    # rename canonical decoder fields. Then visit nested files by depth/name,
    # using POSIX strings for the same ordering on Windows and Unix.
    source = root / 'src'
    paths = sorted(source.rglob('*.sol'),
                   key=lambda path: (len(path.relative_to(source).parts), path.relative_to(source).as_posix()))
    texts = [path.read_text(encoding='utf-8') for path in paths]
    schema = build_schema(texts + list(ERC721_EVENTS))
    historical = json.loads((root / 'indexer/historical_event_schema.json').read_text(encoding='utf-8'))
    return merge_historical(schema, historical)


def merge_historical(schema, historical):
    result = dict(schema)
    for topic, entry in historical.items():
        if set(entry) != {'name','signature','fields'} or any(
            set(field) != {'type','name','indexed'} or type(field['indexed']) is not bool
            for field in entry['fields']):
            raise ValueError('Invalid historical event descriptor')
        arguments = ','.join(field['type'] + (' indexed ' if field['indexed'] else ' ') + field['name']
                             for field in entry['fields'])
        rebuilt = build_schema([f"event {entry['name']}({arguments});"])
        if rebuilt.get(topic) != entry:
            raise ValueError('Historical event topic or signature does not match its layout')
        previous = result.get(topic)
        if previous is not None:
            layout = lambda fields: [(field['type'],field['indexed']) for field in fields]
            if previous['signature'] != entry['signature'] or layout(previous['fields']) != layout(entry['fields']):
                raise ValueError('Conflicting historical event topic layout')
        else:
            result[topic] = entry
    return result


def main():
    schema = source_schema()
    (ROOT / 'indexer/event_schema.json').write_text(
        json.dumps(schema, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(f'Generated {len(schema)} current/historical event schemas')


if __name__ == '__main__':
    main()
