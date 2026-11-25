"""Periodic renewal for a durable provider request lease."""
import threading


class ProviderRequestLeaseKeeper:
    """Keep a PROCESSING claim alive while a synchronous provider call runs."""

    def __init__(self, renew, *, interval_seconds=60.0):
        if not callable(renew):
            raise ValueError("lease_renewal_callback_required")
        if not isinstance(interval_seconds, (int, float)) or interval_seconds <= 0:
            raise ValueError("invalid_lease_renewal_interval")
        self._renew = renew
        self._interval = float(interval_seconds)
        self._stop = threading.Event()
        self._thread = None
        self.lost = False

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
        self._thread = threading.Thread(
            target=self._run, name="provider-request-lease", daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self._interval))
        return False
