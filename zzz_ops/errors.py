"""Sanitized errors shared by read-only transports and request limits."""


class RpcError(RuntimeError):
    pass


class WorkLimit(RpcError):
    """Terminal request failure, never an upstream failover/retry signal."""

    def __init__(self, reason):
        if reason not in ('deadline', 'rpc_budget', 'snapshot_expired'):
            raise ValueError('Unknown work-limit reason')
        self.reason = reason
        super().__init__('Request work limit: ' + reason)
