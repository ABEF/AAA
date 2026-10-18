"""Killable, serial, read-only API requests; configuration stays in memory."""
from __future__ import annotations

import json
import multiprocessing
from pathlib import Path
import tempfile
import threading
import time

from frontend_api.service import Projection, UnknownNFT
from zzz_ops.errors import RpcError, WorkLimit
from zzz_ops.work_budget import request_scope

MAX_RESULT = 1024 * 1024
HARD_SECONDS = 30


def _run(output, config, activation_config, action, payload):
    # Catch/sanitize failures inside the child: multiprocessing must never print
    # upstream exception strings or configured credentials in a traceback.
    try:
        from frontend_api.activation import ActivationTransactions, ActivationInputError
        p = Projection(config)
        with request_scope():
            if action == 'protocol':
                result = p.protocol()
            elif action == 'mint_readiness':
                result = p.mint_readiness()
            elif action == 'nft':
                result = p.nft(payload)
            elif action == 'wallet':
                result = p.wallet(payload)
            elif action == 'activation' and activation_config is not None:
                result = ActivationTransactions(p, activation_config).prepare(payload)
            elif action == 'transactions':
                # Optional local adapter; the published read server exposes no
                # mint/claim POST. No signer/broadcast capability exists here.
                from frontend_api.transactions import Transactions
                result = Transactions(p).prepare(payload)
            else:
                raise ValueError('Unsupported operation')
        envelope = {'ok': result}
    except WorkLimit as exc:
        envelope = {'error': exc.reason}
    except UnknownNFT:
        envelope = {'error': 'nft_not_minted'}
    except BaseException as exc:
        # Map only the exact known input exception; no names or messages leak.
        from frontend_api.activation import ActivationInputError
        envelope = {'error': 'invalid_activation' if isinstance(exc, ActivationInputError) else 'unavailable'}
    try:
        encoded = json.dumps(envelope, separators=(',', ':'), allow_nan=False).encode()
        if len(encoded) > MAX_RESULT:
            encoded = b'{"error":"result_limit"}'
        Path(output).write_bytes(encoded)
    except BaseException:
        # Parent rejects missing/partial/malformed output after the child exits.
        pass


class WorkerClient:
    """One child per operation, no orphan work after the response deadline.

    The supervisor uses spawn on every OS. A worker can read RPC/history but
    cannot sign or broadcast. The serial HTTP listener admits only one at a time.
    Reverse-proxy admission/rate limiting remains an operating requirement.
    """

    def __init__(self, config, activation_config=None):
        # Validate before accepting requests, without network calls.
        self.config = json.loads(json.dumps(config))
        self.activation_config = json.loads(json.dumps(activation_config))
        p = Projection(self.config)
        self.chain = p.chain
        if activation_config is not None:
            from frontend_api.activation import ActivationTransactions
            ActivationTransactions(p, self.activation_config)
        self._lock = threading.Lock()
        self._unreaped = None

    def _request(self, action, payload=None):
        from frontend_api.activation import ActivationInputError
        if self._unreaped is not None or not self._lock.acquire(blocking=False):
            raise RpcError('Request worker unavailable')
        started = time.monotonic()
        event = 'failed'
        process = None
        directory = None
        try:
            directory = tempfile.TemporaryDirectory(prefix='popl-read-')
            output = Path(directory.name) / 'result.json'
            process = multiprocessing.get_context('spawn').Process(
                target=_run, args=(str(output), self.config, self.activation_config, action, payload), daemon=True)
            process.start()
            process.join(max(0, HARD_SECONDS - (time.monotonic() - started)))
            if process.is_alive():
                event = 'deadline'
                raise WorkLimit('deadline')
            if time.monotonic() - started >= HARD_SECONDS:
                event = 'deadline'
                raise WorkLimit('deadline')
            if process.exitcode != 0 or not output.is_file() or output.stat().st_size > MAX_RESULT:
                raise RpcError('Request worker did not produce a bounded result')
            envelope = json.loads(output.read_bytes())
            if not isinstance(envelope, dict):
                raise RpcError('Invalid request result')
            if set(envelope) == {'error'}:
                code = envelope['error']
                if code in ('deadline', 'rpc_budget', 'snapshot_expired'):
                    event = code
                    raise WorkLimit(code)
                if code == 'nft_not_minted':
                    raise UnknownNFT('NFT not minted')
                if code == 'invalid_activation':
                    from frontend_api.activation import ActivationInputError
                    raise ActivationInputError('Invalid activation request')
                raise RpcError('Request worker unavailable')
            if set(envelope) != {'ok'} or not isinstance(envelope['ok'], dict):
                raise RpcError('Invalid request result')
            result = envelope['ok']
            if 'expires_at' in result and time.time() >= result['expires_at']:
                event = 'snapshot_expired'
                raise WorkLimit('snapshot_expired')
            provenance = result.get('provenance', {})
            if 'block_timestamp' in provenance:
                stamp = provenance['block_timestamp']
                if not time.time()-self.config['max_block_age_seconds'] < stamp <= time.time()+30:
                    event = 'snapshot_expired'
                    raise WorkLimit('snapshot_expired')
            event = 'ok'
            return result
        except (WorkLimit, UnknownNFT, ActivationInputError):
            raise
        except Exception:
            raise RpcError('Request worker unavailable') from None
        finally:
            # Terminate stuck DNS/read/SQLite calls, then reap. No thread-pool
            # timeout that silently leaves the upstream work running.
            alive = False
            cleanup_failed = False
            try:
                if process is not None and process.pid is not None:
                    for stop in (process.terminate, process.kill):
                        if process.is_alive():
                            try:
                                stop()
                                process.join(1)
                            except (OSError, ValueError):
                                pass
                    alive = process.is_alive()
                    if alive:
                        self._unreaped = process
                        event = 'worker_cleanup_failed'
                    else:
                        process.close()
            except Exception:
                # If cleanup cannot be established, refuse another worker.
                alive = True
                self._unreaped = process or True
                cleanup_failed = True
            try:
                if directory is not None and not alive:
                    directory.cleanup()
                elif directory is not None:
                    # Retain cleanup state rather than racing a still-live worker;
                    # this client refuses ALL subsequent work and needs supervision.
                    self._unreaped_directory = directory
            except Exception:
                cleanup_failed = True
            finally:
                self._lock.release()
            if cleanup_failed:
                event = 'worker_cleanup_failed'
            print(json.dumps({'event': 'api_request', 'outcome': event,
                              'elapsed_ms': int((time.monotonic()-started)*1000)}), flush=True)
            if cleanup_failed:
                raise RpcError('Request worker cleanup failed') from None

    def protocol(self):
        return self._request('protocol')

    def mint_readiness(self):
        return self._request('mint_readiness')

    def nft(self, identifier):
        return self._request('nft', identifier)

    def wallet(self, owner):
        return self._request('wallet', owner)

    def prepare(self, payload):
        return self._request('activation' if self.activation_config is not None else 'transactions', payload)
