"""Sanitized errors shared by read-only transports and request limits."""


class RpcError(RuntimeError):
    pass

class RemoteRPCError(RpcError):
    """Sanitized wire-error metadata; never retain provider text, data or URL."""
    def __init__(self, method, code, reason='unclassified'):
        if type(code) is not int:code=None
        if reason not in ('unavailable_block','invalid_params','rate_limited','unclassified'):
            raise ValueError('Unsupported sanitized RPC reason')
        self.method,self.code,self.reason=method,code,reason
        super().__init__(f'{method} returned JSON-RPC error {code} ({reason})')


class WorkLimit(RpcError):
    """Terminal request failure, never an upstream failover/retry signal."""

    def __init__(self, reason):
        if reason not in ('deadline', 'rpc_budget', 'snapshot_expired'):
            raise ValueError('Unknown work-limit reason')
        self.reason = reason
        super().__init__('Request work limit: ' + reason)
