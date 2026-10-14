"""Small static-ABI codec. Never used for signing or wallet key handling."""
from __future__ import annotations
import re

_MASK = (1 << 64) - 1
_ROT = ((0,36,3,41,18),(1,44,10,45,2),(62,6,43,15,61),(28,55,25,21,56),(27,20,39,8,14))
_RC = (0x0000000000000001,0x0000000000008082,0x800000000000808A,0x8000000080008000,
       0x000000000000808B,0x0000000080000001,0x8000000080008081,0x8000000000008009,
       0x000000000000008A,0x0000000000000088,0x0000000080008009,0x000000008000000A,
       0x000000008000808B,0x800000000000008B,0x8000000000008089,0x8000000000008003,
       0x8000000000008002,0x8000000000000080,0x000000000000800A,0x800000008000000A,
       0x8000000080008081,0x8000000000008080,0x0000000080000001,0x8000000080008008)

def keccak256(data: bytes) -> bytes:
    """Ethereum Keccak-256 (not NIST SHA3-256); public-data utility only."""
    def rol(x: int, n: int) -> int:
        return ((x << n) | (x >> ((64-n) % 64))) & _MASK
    a = [0] * 25
    padding = 136 - len(data) % 136
    data += b'\x81' if padding == 1 else b'\x01' + b'\0' * (padding-2) + b'\x80'
    for offset in range(0, len(data), 136):
        block = data[offset:offset+136]
        for i in range(17): a[i] ^= int.from_bytes(block[8*i:8*i+8], 'little')
        for rc in _RC:
            c = [a[x] ^ a[x+5] ^ a[x+10] ^ a[x+15] ^ a[x+20] for x in range(5)]
            d = [c[(x-1)%5] ^ rol(c[(x+1)%5], 1) for x in range(5)]
            b = [0] * 25
            for x in range(5):
                for y in range(5):
                    b[y + 5*((2*x+3*y)%5)] = rol(a[x+5*y] ^ d[x], _ROT[x][y])
            for x in range(5):
                for y in range(5):
                    a[x+5*y] = b[x+5*y] ^ ((~b[(x+1)%5+5*y]) & b[(x+2)%5+5*y])
            a[0] ^= rc
    return b''.join(v.to_bytes(8, 'little') for v in a)[:32]

def address(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{40}', value):
        raise ValueError('Expected an Ethereum address')
    if int(value,16) == 0: raise ValueError('Zero address is not permitted')
    return value.lower()

def word(value: int | str, typ: str) -> str:
    if typ == 'address': return address(str(value))[2:].rjust(64,'0')
    if typ == 'bytes32':
        if not isinstance(value,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}',value):
            raise ValueError('Expected bytes32')
        return value[2:].lower()
    if typ == 'bool':
        if value not in (False,True,0,1): raise ValueError('Invalid boolean')
        return f'{int(value):064x}'
    m = re.fullmatch(r'uint(\d*)',typ)
    if not m: raise ValueError(f'Unsupported static ABI type: {typ}')
    bits = int(m[1] or 256)
    if bits < 8 or bits > 256 or bits % 8: raise ValueError('Invalid integer width')
    n = int(value)
    if n < 0 or n >= 1 << bits: raise ValueError(f'Value exceeds {typ}')
    return f'{n:064x}'

def calldata(signature: str, *args: int | str) -> str:
    match = re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\(([^()]*)\)',signature)
    if not match: raise ValueError('Only flat static ABI signatures are supported')
    types = match[1].split(',') if match[1] else []
    if len(types) != len(args): raise ValueError('Argument count mismatch')
    return '0x' + keccak256(signature.encode()).hex()[:8] + ''.join(word(a,t) for a,t in zip(args,types))

def uint_result(result: str) -> int:
    if not isinstance(result,str) or not re.fullmatch(r'0x[0-9a-fA-F]{64}', result):
        raise ValueError('Expected one ABI word')
    return int(result,16)

def decode_words(data: str) -> list[str]:
    if not isinstance(data,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{64})*',data):
        raise ValueError('Malformed ABI event data')
    return [data[i:i+64] for i in range(2,len(data),64)]
