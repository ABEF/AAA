"""Exact execution-fee derivation from Ethereum transaction and block fields.

RPC gasPrice/effectiveGasPrice are derived fields for type-2 transactions.
Use signed caps and the canonical inclusion block instead. This does not price
additional chain-specific data fees or authenticate the RPC's chain history.
"""
import re


def quantity(value):
    if not isinstance(value, str) or not re.fullmatch(r'0x[0-9a-fA-F]{1,64}', value):
        raise ValueError('Invalid exact fee quantity')
    return int(value, 16)


def fee_cap(transaction):
    kind = quantity(transaction.get('type', '0x0'))
    if kind == 2:
        cap = quantity(transaction.get('maxFeePerGas'))
        if quantity(transaction.get('maxPriorityFeePerGas')) > cap:
            raise ValueError('Priority fee exceeds signed maximum fee')
        return cap
    if kind not in (0, 1):
        raise ValueError('Unsupported transaction fee type')
    return quantity(transaction.get('gasPrice'))


def execution_price(transaction, canonical_block, receipt):
    cap = fee_cap(transaction)
    if quantity(transaction.get('type', '0x0')) == 2:
        base = quantity(canonical_block.get('baseFeePerGas'))
        if base > cap:
            raise ValueError('Canonical base fee exceeds signed maximum fee')
        return min(cap, base + quantity(transaction.get('maxPriorityFeePerGas')))
    return quantity(receipt.get('effectiveGasPrice'))
