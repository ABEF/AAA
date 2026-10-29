"""Transaction provenance in ordered, possibly filtered block logs.

Missing legacy transaction indices remain unknown. Numeric gaps are valid when
untracked transactions or emitters have no observed logs; contradictions are not.
This checks internal consistency, never RPC authenticity or log completeness.
"""


class OrderedTransactions:
    def __init__(self):
        self.block = None
        self.last_log = -1
        self.transaction = None
        self.seen = set()
        self.ordinal = -1
        self.transaction_index = None
        self.skipped = -1

    def add(self, block, log_index, transaction, transaction_index=None):
        if any(type(n) is not int or not 0 <= n < 2**63 for n in (block, log_index)):
            raise ValueError('Invalid ordered log identity')
        if transaction_index is not None and (type(transaction_index) is not int or
                                              not 0 <= transaction_index < 2**63):
            raise ValueError('Invalid transaction index')
        if self.block is None or block > self.block:
            self.block, self.last_log, self.transaction = block, -1, None
            self.seen, self.ordinal, self.transaction_index, self.skipped = set(), -1, None, -1
        if block != self.block or log_index <= self.last_log:
            raise ValueError('Logs are not in canonical block order')
        if transaction != self.transaction:
            if transaction in self.seen:
                raise ValueError('Transaction logs are interleaved')
            self.seen.add(transaction)
            self.transaction, self.transaction_index = transaction, None
            self.ordinal += 1
        if transaction_index is not None:
            if self.transaction_index is not None and transaction_index != self.transaction_index:
                raise ValueError('Transaction index changes within a transaction')
            # Actual transaction ordinal minus observed ordinal counts omitted
            # transactions. Filtering can increase that count, never reduce it.
            skipped = transaction_index - self.ordinal
            if skipped < 0 or skipped < self.skipped:
                raise ValueError('Transaction indices contradict observed log order')
            self.transaction_index, self.skipped = transaction_index, skipped
        self.last_log = log_index
