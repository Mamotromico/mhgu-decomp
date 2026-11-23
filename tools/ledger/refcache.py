"""Cached reference blocks for the byte gate — direct NSO extraction, no Ghidra.

The byte gate (``tools/ledger/bytegate.py``) compares a compiled function against the
original bytes of its memory block. Until now those bytes came from
``tools/ghidra/dump_blocks.sh`` — a full headless Ghidra import run *per gate check*.
``tools/ledger/revalidate.py`` already proved the cheaper path: the gate only ever
compares functions, and every function lives in ``.text``, so slicing the decompressed
``.text`` straight out of the NSO (pure-Python LZ4 via ``tools/nso/nso_extract.py``)
supplies every byte the gate needs.

This module turns that into a shared cache. ``.text`` is extracted once, written as
``.text_60000000.bin`` (the same ``<block>_<startHex>.bin`` naming the Ghidra dump
uses, so the gate's ``block_bin`` locates it), and served to every later gate run.

Scope — ``.text`` only, on purpose
-----------------------------------
Only ``.text`` is served from the cache. Two reasons:

* **Need.** The gate only compares ``kind=function`` bodies; all 42,333 of them are in
  ``.text``. No gate path reads another block.
* **Equivalence.** The raw NSO ``.text`` is *exactly* the loaded block's bytes (the
  image's relocations all land in ``.data``/``.got``; ``.text`` carries none) — a byte
  prefix of the Ghidra-derived block, which merely pads the block end. The other Ghidra
  blocks (``.rodata.1``, ``.data``…) are *loader segments* split differently from the
  NSO's three sections and rebased post-load, so direct extraction is not byte-equal
  there. Serving anything but ``.text`` would need its own proof.

``ref_bin_for_block`` therefore returns ``None`` for any other block and the caller
falls back to the Ghidra dump (``bytegate --ghidra-ref`` forces that path).

Cache key
---------
The block bytes are a pure function of the NSO file, so the key is the NSO identity
plus the extractor version — the same fingerprint convention ``gotmap`` uses:
``{path, size, mtime_ns}`` plus ``CACHE_VERSION`` (bump when the extraction logic or
block set changes). The inventory/ledger versions do not enter the key: they shape the
*extents* a caller asserts, never the reference bytes themselves. A sha256 of the block
is recorded in the sidecar and verified on every serve, so a corrupted or truncated
bin rebuilds instead of silently mis-gating; writes are atomic (temp file + rename),
so an interrupted run never leaves a half-written block behind.

Equivalence check
-----------------
``refcache --check`` regenerates the reference the slow way — a fresh
``dump_blocks.sh`` Ghidra import into a throwaway directory — and asserts the cached
``.text`` is byte-identical to it at every offset (prefix rule; the loader's trailing
pad byte is reported, not compared). Run it after any toolchain/image change that
could alter the loader's block construction.

Usage::

    python3 tools/ledger/refcache.py                 # ensure the cache, print its digest
    python3 tools/ledger/refcache.py --refresh       # drop and rebuild it from the NSO
    python3 tools/ledger/refcache.py --check         # byte-compare vs a fresh Ghidra dump
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "nso"))

import nso_extract  # noqa: E402

DEFAULT_NSO = REPO / "baserom" / "main.nso"
DEFAULT_CACHE_DIR = REPO / "baserom" / "work" / "bytegate" / "refcache"

# The image base / loaded start of .text (docs/architecture.md -> memory map). Kept in
# sync with complexity.BASE_ADDR; the NSO header's memory_offset for .text is 0.
TEXT_BLOCK = ".text"
TEXT_START = 0x60000000

BIN_NAME = f"{TEXT_BLOCK}_{TEXT_START:08x}.bin"
SIDECAR_NAME = "refcache.json"

# Bump when the extraction logic or block set changes (the extractor version half of
# the cache key; the other half is the NSO fingerprint).
CACHE_VERSION = 1


class RefError(Exception):
    """The reference cache cannot be built or served (missing/corrupt NSO)."""


def fingerprint(nso: Path) -> dict:
    """The NSO identity, in gotmap's convention: path, size, mtime."""
    try:
        stat = Path(nso).stat()
    except OSError as e:
        raise RefError(f"cannot stat NSO {nso}: {e}") from e
    return {"path": str(nso), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def extract_text(nso: Path) -> bytes:
    """The decompressed ``.text`` of ``nso`` — the same bytes revalidate gates against.

    Raises :class:`RefError` with an actionable cause when the image cannot be read;
    a truncated or non-NSO file is never served as a reference.
    """
    try:
        return nso_extract.extract(Path(nso))["data"]["text"]
    except (nso_extract.NsoError, OSError, KeyError) as e:
        raise RefError(f"cannot extract .text from {nso}: {e}") from e


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sidecar(cache_dir: Path) -> dict | None:
    """The parsed sidecar, or ``None`` when absent/corrupt (both mean "no cache")."""
    path = cache_dir / SIDECAR_NAME
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def _atomic_write(path: Path, data: bytes) -> None:
    """Write ``data`` to ``path`` via a temp file + rename (interrupt-safe)."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _write(cache_dir: Path, nso: Path, text: bytes) -> None:
    """(Re)build the bin and sidecar together so they can never disagree."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write(cache_dir / BIN_NAME, text)
    payload = {
        "version": CACHE_VERSION,
        "nso": fingerprint(nso),
        "block": TEXT_BLOCK,
        "start": f"{TEXT_START:08x}",
        "size": len(text),
        "sha256": _sha256(text),
    }
    _atomic_write(cache_dir / SIDECAR_NAME,
                  (json.dumps(payload, indent=1, sort_keys=True) + "\n").encode())


def _serves(payload: dict, nso: Path, bin_path: Path) -> bool:
    """Whether the cached bin is current, intact, and byte-identical to what was written.

    Fingerprint mismatch means a different/changed NSO; a digest mismatch means the bin
    was corrupted or truncated after writing (bit rot, a killed non-atomic writer). Both
    rebuild rather than mis-gate: the gate's authority is the original bytes, so the
    cache is only ever a faithful copy or absent.
    """
    if payload.get("version") != CACHE_VERSION:
        return False
    if payload.get("nso") != fingerprint(nso):
        return False
    try:
        blob = bin_path.read_bytes()
    except OSError:
        return False
    return len(blob) == payload.get("size") and _sha256(blob) == payload.get("sha256")


def load_or_build(nso: Path = DEFAULT_NSO, cache_dir: Path = DEFAULT_CACHE_DIR,
                  *, refresh: bool = False) -> Path:
    """The cached ``.text`` block .bin, extracting it from the NSO when absent or stale.

    ``refresh`` forces a rebuild even when the cache is current (the NSO may have been
    replaced with a same-size/same-mtime stand-in; the caller asking explicitly is the
    escape hatch).
    """
    nso, cache_dir = Path(nso), Path(cache_dir)
    bin_path = cache_dir / BIN_NAME
    if not refresh:
        payload = _sidecar(cache_dir)
        if payload is not None and _serves(payload, nso, bin_path):
            return bin_path
    text = extract_text(nso)
    _write(cache_dir, nso, text)
    return bin_path


def ref_bin_for_block(nso: Path, block: str, cache_dir: Path = DEFAULT_CACHE_DIR,
                      *, refresh: bool = False) -> Path | None:
    """The cached reference .bin for ``block``, or ``None`` to request the Ghidra path.

    Only ``.text`` is directly extractable in a byte-equivalent form (see the module
    docstring); any other block is the caller's cue to dump via Ghidra.
    """
    if block != TEXT_BLOCK:
        return None
    return load_or_build(nso, cache_dir, refresh=refresh)


def check_against_ghidra(nso: Path = DEFAULT_NSO,
                         cache_dir: Path = DEFAULT_CACHE_DIR) -> list[str]:
    """Byte-compare the cached ``.text`` against a fresh Ghidra dump.

    Runs ``tools/ghidra/dump_blocks.sh`` into a throwaway directory (the existing,
    Ghidra-derived path — a full headless import each time) and applies the
    equivalence rule:
    every cached byte must equal the Ghidra block at the same offset. The loader pads
    the block past the section end; padding is reported as information, not a failure.
    Returns a list of problems (empty means equivalent).
    """
    bin_path = load_or_build(nso, cache_dir)
    cached = bin_path.read_bytes()
    problems: list[str] = []
    with tempfile.TemporaryDirectory(dir=REPO / "baserom" / "work") as tmp:
        out = Path(tmp) / "dump"
        script = REPO / "tools" / "ghidra" / "dump_blocks.sh"
        proc = subprocess.run(["bash", str(script), str(nso), str(out)],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            tail = (proc.stdout + proc.stderr).strip().splitlines()[-10:]
            return [f"Ghidra dump failed (rc {proc.returncode}): "
                    + (tail[-1] if tail else "no output")]
        ghidra_bin = out / BIN_NAME
        if not ghidra_bin.exists():
            return [f"fresh dump has no {BIN_NAME}: {sorted(p.name for p in out.iterdir())}"]
        ghidra = ghidra_bin.read_bytes()
    if len(ghidra) < len(cached):
        problems.append(f"Ghidra block is shorter than the cached extraction "
                        f"({len(ghidra)} < {len(cached)})")
    prefix = ghidra[:len(cached)]
    if prefix != cached:
        first = next((i for i, (a, b) in enumerate(zip(cached, prefix)) if a != b), None)
        problems.append(
            f"byte divergence at offset {first} of {len(cached)} "
            f"(cached {cached[first]:#04x} != ghidra {prefix[first]:#04x})"
            if first is not None else
            f"byte divergence inside the {len(cached)}-byte cached span")
    return problems


def _fmt_size(n: int) -> str:
    return f"{n} B ({n / 1024 / 1024:.1f} MiB)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nso", type=Path, default=DEFAULT_NSO)
    ap.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR,
                    help="where the cached block lives (default under baserom/work)")
    ap.add_argument("--refresh", action="store_true",
                    help="drop and rebuild the cache from the NSO, even when current")
    ap.add_argument("--check", action="store_true",
                    help="byte-compare the cache against a fresh Ghidra dump")
    args = ap.parse_args(argv)

    try:
        path = load_or_build(args.nso, args.cache_dir, refresh=args.refresh)
    except RefError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    blob = path.read_bytes()
    print(f"cache:  {path}")
    print(f"  nso:  {args.nso}  ({fingerprint(args.nso)['size']} B, "
          f"mtime_ns={fingerprint(args.nso)['mtime_ns']})")
    print(f"  block {TEXT_BLOCK} @{TEXT_START:#010x}  {_fmt_size(len(blob))}  "
          f"sha256={_sha256(blob)}")

    if not args.check:
        return 0
    print("check:  dumping blocks via Ghidra (this takes a while) …")
    if not shutil.which("bash"):
        print("error: bash not found", file=sys.stderr)
        return 2
    problems = check_against_ghidra(args.nso, args.cache_dir)
    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("OK: cached .text is byte-identical to the Ghidra-derived block")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
