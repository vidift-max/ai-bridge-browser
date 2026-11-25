"""Periodic renewal for a durable provider request lease."""
import math
import threading


class ProviderRequestLeaseKeeper:
    """Keep a PROCESSING claim alive and report whether shutdown was clean."""

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
        self._thread = None
        self._started = False
        self.lost = False
        self.stopped = False

    def _run(self):
        while not self._stop.wait(self._interval):
            try:
                if not self._renew():
                    self.lost = True
                    self._stop.set()
                    return
            except Exception:
                self.lost = True
                self._stop.set()
                return

    def __enter__(self):
        if self._started:
            raise RuntimeError("provider_lease_keeper_already_started")
        self._started = True
        self._thread = threading.Thread(
            target=self._run, name="provider-request-lease", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self._shutdown_timeout)
            self.stopped = not self._thread.is_alive()
            if not self.stopped:
                # The renewal callback is still in flight. The caller must not
                # persist a provider response while lease ownership is uncertain.
                self.lost = True
        else:
            self.stopped = True
        return False
