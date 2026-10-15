"""Generate the indexer's flat event schemas, rejecting ambiguous topic layouts."""
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
    texts = [path.read_text(encoding='utf-8') for path in sorted((root / 'src').glob('*.sol'))]
    return build_schema(texts + list(ERC721_EVENTS))


def main():
    schema = source_schema()
    (ROOT / 'indexer/event_schema.json').write_text(
        json.dumps(schema, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(f'Generated {len(schema)} event schemas from current source')


if __name__ == '__main__':
    main()
