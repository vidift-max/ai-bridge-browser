"""Periodic renewal for a durable provider request lease."""
import math
import threading
import time


class ProviderRequestLeaseKeeper:
    """Keep a PROCESSING claim alive and expose a thread-safe health snapshot."""

    def __init__(self, renew, *, interval_seconds=60.0, shutdown_timeout_seconds=5.0):
        if not callable(renew):
            raise ValueError("lease_renewal_callback_required")
        for name, value in (("interval", interval_seconds),
                            ("shutdown_timeout", shutdown_timeout_seconds)):
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or value <= 0):
                raise ValueError("invalid_lease_" + name)
        self._renew = renew
        self._interval = float(interval_seconds)
        self._shutdown_timeout = float(shutdown_timeout_seconds)
        self._stop = threading.Event()
        self._state_lock = threading.Lock()
        self._thread = None
        self._started = False
        self._lost = False
        self._stopped = False
        self._failure_reason = None
        self._renewal_count = 0
        self._last_successful_renewal_monotonic = None

    @property
    def lost(self):
        with self._state_lock:
            return self._lost

    @property
    def stopped(self):
        with self._state_lock:
            return self._stopped

    def snapshot(self):
        """Return a consistent, non-sensitive view of lease keeper health."""
        with self._state_lock:
            return {
                "started": self._started,
                "lost": self._lost,
                "stopped": self._stopped,
                "failureReason": self._failure_reason,
                "renewalCount": self._renewal_count,
                "lastSuccessfulRenewalMonotonic": self._last_successful_renewal_monotonic,
            }

    def _mark_lost(self, reason):
        with self._state_lock:
            self._lost = True
            if self._failure_reason is None:
                self._failure_reason = reason

    def _run(self):
        while not self._stop.wait(self._interval):
            try:
                renewed = self._renew()
            except Exception:
                self._mark_lost("renewal_exception")
                self._stop.set()
                return
            if renewed is not True:
                self._mark_lost(
                    "renewal_rejected" if renewed is False else "invalid_renewal_result")
                self._stop.set()
                return
            with self._state_lock:
                self._renewal_count += 1
                self._last_successful_renewal_monotonic = time.monotonic()

    def __enter__(self):
        with self._state_lock:
            if self._started:
                raise RuntimeError("provider_lease_keeper_already_started")
            self._started = True
        self._thread = threading.Thread(
            target=self._run, name="provider-request-lease", daemon=True)
        try:
            self._thread.start()
        except Exception:
            self._mark_lost("thread_start_failed")
            with self._state_lock:
                self._stopped = True
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self._shutdown_timeout)
            clean_stop = not self._thread.is_alive()
        else:
            clean_stop = True
        with self._state_lock:
            self._stopped = clean_stop
            if not clean_stop:
                self._lost = True
                if self._failure_reason is None:
                    self._failure_reason = "shutdown_timeout"
        return False
