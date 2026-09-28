"""Atomic-cache behaviour for the Steinmetz archive fetcher."""
from __future__ import annotations

import threading
import time

import pytest

from snntopo.data import steinmetz


class _Response:
    def __init__(self, chunks, fail_after=None):
        self.chunks = chunks
        self.fail_after = fail_after

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, _chunk_size):
        for index, chunk in enumerate(self.chunks):
            if self.fail_after == index:
                raise OSError("connection lost")
            yield chunk


def test_download_failure_never_leaves_a_partial_final_file(monkeypatch, tmp_path):
    path = tmp_path / "steinmetz_part0.npz"
    monkeypatch.setattr(steinmetz, "_path", lambda part: path)
    monkeypatch.setattr(steinmetz.requests, "get",
                        lambda *args, **kwargs: _Response([b"first", b"second"], fail_after=1))

    with pytest.raises(OSError, match="connection lost"):
        steinmetz._download(0)

    assert not path.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_concurrent_downloaders_publish_only_complete_archives(monkeypatch, tmp_path):
    path = tmp_path / "steinmetz_part0.npz"
    payload = b"a complete archive"
    barrier = threading.Barrier(2)
    monkeypatch.setattr(steinmetz, "_path", lambda part: path)

    def get(*args, **kwargs):
        # Both callers have passed the initial path.exists() check before either
        # begins publishing its temporary file.
        barrier.wait(timeout=2)

        class SlowResponse(_Response):
            def iter_content(self, chunk_size):
                yield payload[:4]
                time.sleep(0.01)
                yield payload[4:]
        return SlowResponse([])

    monkeypatch.setattr(steinmetz.requests, "get", get)
    errors = []
    threads = [threading.Thread(target=lambda: _download_in_thread(errors)) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert path.read_bytes() == payload
    assert not list(tmp_path.glob(".*.tmp"))


def _download_in_thread(errors):
    try:
        steinmetz._download(0)
    except BaseException as error:  # pragma: no cover - assertion below reports it
        errors.append(error)
