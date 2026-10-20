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


def transaction_chain_id(transaction):
    """Resolve optional legacy chainId using EIP-155 v, never typed parity."""
    kind = quantity(transaction.get('type', '0x0'))
    chain = quantity(transaction['chainId']) if transaction.get('chainId') is not None else None
    if kind == 0 and transaction.get('v') is not None:
        v = quantity(transaction['v'])
        if v < 35:
            raise ValueError('Legacy transaction has no chain replay protection')
        signed_chain = (v - 35) // 2
        if chain is not None and chain != signed_chain:
            raise ValueError('Transaction chain ID conflicts with its signature')
        chain = signed_chain
    if chain is None:
        raise ValueError('Transaction has no verifiable signed chain ID')
    return chain


def execution_price(transaction, canonical_block, receipt):
    cap = fee_cap(transaction)
    if quantity(transaction.get('type', '0x0')) == 2:
        base = quantity(canonical_block.get('baseFeePerGas'))
        if base > cap:
            raise ValueError('Canonical base fee exceeds signed maximum fee')
        return min(cap, base + quantity(transaction.get('maxPriorityFeePerGas')))
    return quantity(receipt.get('effectiveGasPrice'))
