"""Tests for the reference-block cache (tools/ledger/refcache.py).

Hermetic — the NSO is a synthetic 3-section image, so no ROM, Ghidra, or network is
needed. Covers extraction, keying/staleness, integrity re-verification, refresh, and
the block-scope rule that only ``.text`` is served from the cache. Run with::

    python3 tests/ledger/test_refcache.py
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))
sys.path.insert(0, str(REPO / "tools" / "nso"))

import nso_extract  # noqa: E402
import refcache  # noqa: E402

TEXT = bytes((0x40 + i) & 0xFF for i in range(0x4000))          # deterministic .text
TEXT2 = bytes((0xC3 + i) & 0xFF for i in range(0x4000))         # a different image
COMPRESSED_SIZE_BASE = 0x60


def build_image(payloads: list[bytes]) -> bytes:
    """Assemble a synthetic uncompressed 3-section NSO0 (same idea as tests/nso)."""
    header = bytearray(0x100)
    header[0:4] = b"NSO0"
    struct.pack_into("<I", header, 0x0C, 0)               # flags: uncompressed
    offset = 0x100
    body = bytearray()
    for i, blob in enumerate(payloads):
        base = 0x10 + 0x10 * i
        struct.pack_into("<I", header, base + 0x0, offset)
        struct.pack_into("<I", header, base + 0x4, 0x60000000 + i * 0x1000)
        struct.pack_into("<I", header, base + 0x8, len(blob))
        struct.pack_into("<I", header, COMPRESSED_SIZE_BASE + 4 * i, len(blob))
        body += blob
        offset += len(blob)
    return bytes(header) + bytes(body)


class RefcacheTestCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._dir.name)
        self.cache = self.tmp / "cache"

    def tearDown(self):
        self._dir.cleanup()

    def make_nso(self, text: bytes = TEXT) -> Path:
        nso = self.tmp / "main.nso"
        nso.write_bytes(build_image([text, b"rodata-bytes", b"data-bytes"]))
        return nso

    def sidecar(self) -> dict:
        return json.loads((self.cache / refcache.SIDECAR_NAME).read_text())

    def bin_bytes(self) -> bytes:
        return (self.cache / refcache.BIN_NAME).read_bytes()


class ExtractionTests(RefcacheTestCase):
    def test_extracts_text_and_writes_bin_and_sidecar(self):
        nso = self.make_nso()
        path = refcache.load_or_build(nso, self.cache)
        self.assertEqual(path, self.cache / refcache.BIN_NAME)
        self.assertEqual(self.bin_bytes(), TEXT)
        payload = self.sidecar()
        self.assertEqual(payload["version"], refcache.CACHE_VERSION)
        self.assertEqual(payload["block"], ".text")
        self.assertEqual(payload["start"], "60000000")
        self.assertEqual(payload["size"], len(TEXT))
        self.assertEqual(payload["sha256"], hashlib.sha256(TEXT).hexdigest())
        self.assertEqual(payload["nso"]["size"], nso.stat().st_size)
        self.assertEqual(payload["nso"]["mtime_ns"], nso.stat().st_mtime_ns)

    def test_a_second_call_serves_the_cache_without_reextracting(self):
        nso = self.make_nso()
        refcache.load_or_build(nso, self.cache)
        with mock.patch.object(refcache, "extract_text",
                               side_effect=AssertionError("must not re-extract")):
            path = refcache.load_or_build(nso, self.cache)
        self.assertEqual(path.read_bytes(), TEXT)

    def test_a_tampered_bin_rebuilds(self):
        nso = self.make_nso()
        refcache.load_or_build(nso, self.cache)
        blob = bytearray(self.bin_bytes())
        blob[0x100] ^= 0xFF
        (self.cache / refcache.BIN_NAME).write_bytes(bytes(blob))
        refcache.load_or_build(nso, self.cache)
        self.assertEqual(self.bin_bytes(), TEXT)

    def test_a_truncated_bin_rebuilds(self):
        nso = self.make_nso()
        refcache.load_or_build(nso, self.cache)
        (self.cache / refcache.BIN_NAME).write_bytes(self.bin_bytes()[:0x100])
        refcache.load_or_build(nso, self.cache)
        self.assertEqual(self.bin_bytes(), TEXT)

    def test_no_tmp_files_are_left_behind(self):
        refcache.load_or_build(self.make_nso(), self.cache)
        leftovers = [p.name for p in self.cache.iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(leftovers, [])


class StalenessTests(RefcacheTestCase):
    def rebuild_after(self, mutate):
        """Build once, apply ``mutate``, rebuild, and return the final bin bytes."""
        nso = self.make_nso()
        refcache.load_or_build(nso, self.cache)
        mutate()
        refcache.load_or_build(nso, self.cache)
        return self.bin_bytes()

    def test_an_mtime_change_rebuilds(self):
        nso = self.make_nso()

        def mutate():
            nso.write_bytes(build_image([TEXT2, b"rodata-bytes", b"data-bytes"]))
            os.utime(nso, ns=(nso.stat().st_atime_ns + 1_000_000,
                              nso.stat().st_mtime_ns + 1_000_000))

        self.assertEqual(self.rebuild_after(mutate), TEXT2)

    def test_a_size_change_rebuilds(self):
        nso = self.make_nso()

        def mutate():
            nso.write_bytes(build_image([TEXT2, b"r", b"d"]))   # smaller sections
            os.utime(nso, ns=(0, nso.stat().st_mtime_ns + 1_000_000))

        self.assertEqual(self.rebuild_after(mutate), TEXT2)

    def test_a_version_mismatch_rebuilds(self):
        nso = self.make_nso()
        refcache.load_or_build(nso, self.cache)
        payload = self.sidecar()
        payload["version"] = refcache.CACHE_VERSION + 1
        (self.cache / refcache.SIDECAR_NAME).write_text(json.dumps(payload))
        refcache.load_or_build(nso, self.cache)
        self.assertEqual(self.sidecar()["version"], refcache.CACHE_VERSION)

    def test_a_corrupt_sidecar_rebuilds(self):
        def mutate():
            (self.cache / refcache.SIDECAR_NAME).write_text("{ not json")

        self.assertEqual(self.rebuild_after(mutate), TEXT)

    def test_a_missing_sidecar_rebuilds_the_orphan_bin(self):
        def mutate():
            (self.cache / refcache.SIDECAR_NAME).unlink()

        self.assertEqual(self.rebuild_after(mutate), TEXT)


class FailureTests(RefcacheTestCase):
    def test_a_missing_nso_raises(self):
        with self.assertRaises(refcache.RefError):
            refcache.load_or_build(self.tmp / "nope.nso", self.cache)

    def test_a_non_nso_file_raises(self):
        bogus = self.tmp / "main.nso"
        bogus.write_bytes(b"MZ" + b"\x00" * 0x200)
        with self.assertRaises(refcache.RefError):
            refcache.load_or_build(bogus, self.cache)


class RefreshTests(RefcacheTestCase):
    def test_refresh_picks_up_new_bytes_without_an_mtime_change(self):
        nso = self.make_nso()
        refcache.load_or_build(nso, self.cache)
        # Same file, new content, mtime forced identical: only an explicit refresh
        # (or a fingerprint difference, tested above) may notice.
        nso.write_bytes(build_image([TEXT2, b"rodata-bytes", b"data-bytes"]))
        os.utime(nso, ns=(0, self.sidecar()["nso"]["mtime_ns"]))
        served = refcache.load_or_build(nso, self.cache)
        self.assertEqual(served.read_bytes(), TEXT)                # cache still current
        rebuilt = refcache.load_or_build(nso, self.cache, refresh=True)
        self.assertEqual(rebuilt.read_bytes(), TEXT2)


class BlockScopeTests(RefcacheTestCase):
    def test_text_is_served_from_the_cache(self):
        nso = self.make_nso()
        path = refcache.ref_bin_for_block(nso, ".text", self.cache)
        self.assertEqual(path, self.cache / refcache.BIN_NAME)
        self.assertEqual(path.read_bytes(), TEXT)

    def test_other_blocks_are_not_served(self):
        # The Ghidra blocks are loader segments, not byte-equal NSO slices — the
        # caller must take the dump path for them (bytegate's fallback).
        for block in (".data", ".rodata.1", ".got"):
            self.assertIsNone(
                refcache.ref_bin_for_block(self.make_nso(), block, self.cache))


if __name__ == "__main__":
    unittest.main(verbosity=2)
