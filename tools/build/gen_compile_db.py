"""Generate the build's ``compile_commands.json`` from the committed ledger.

The build is a **function of the ledger** (``docs/architecture.md`` → *File layout &
generated build*): translation-unit membership is the ``group`` column, so the source list
is *derived*, never hand-maintained. For every ledger ``function`` entry whose source file
exists at ``src/<module>/<group>.cpp`` this tool emits one compile-database entry, using the
pinned toolchain (``config/toolchain.json``) and the shared include dirs
(``config/build.json``) — so clangd and the byte gate compile a candidate exactly the way
the build will.

It is the **sole writer** of the compile database and is deterministic and idempotent:
``--check`` regenerates in memory and fails on drift (the CI shape used by the ledger's own
tooling). The output (``build/compile_commands.json``) is a derived artifact under the
git-ignored ``build/`` tree, never committed.

Usage::

    python3 tools/build/gen_compile_db.py            # write build/compile_commands.json
    python3 tools/build/gen_compile_db.py --check    # fail if it is out of date (CI)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))

from ledgerlib import read_entries

DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_TOOLCHAIN = REPO / "config" / "toolchain.json"
DEFAULT_BUILD = REPO / "config" / "build.json"

CFG_DEFAULTS = {
    "source_root": "src",
    "include_dirs": ["include"],
    "object_dir": "build/obj",
    "compile_db": "build/compile_commands.json",
}


class ConfigError(Exception):
    """A config file is missing, unreadable, or not a JSON object."""


def load_json(path: Path, what: str) -> dict:
    """Read a JSON object from ``path``, or raise ``ConfigError`` with a clean message.

    These config files are hand-editable and documented as the source of truth, so a typo
    should read as ``error: toolchain config …: invalid JSON (line 4, column 3: …)`` rather
    than a Python traceback.
    """
    try:
        raw = json.loads(path.read_text())
    except OSError as e:
        raise ConfigError(f"cannot read {what} {path}: {e.strerror or e}")
    except json.JSONDecodeError as e:
        raise ConfigError(f"{what} {path}: invalid JSON "
                          f"(line {e.lineno}, column {e.colno}: {e.msg})")
    if not isinstance(raw, dict):
        raise ConfigError(f"{what} {path}: expected a JSON object")
    return raw


# --- pure helpers (unit-tested) -------------------------------------------------------

def load_build_config(raw: dict) -> dict:
    """Fill a build config with defaults for any absent key."""
    return {k: raw.get(k, v) for k, v in CFG_DEFAULTS.items()}


def function_groups(entries: list[dict]) -> list[tuple[str, str]]:
    """Distinct ``(module, group)`` translation units, in deterministic order.

    A ``group`` is a TU; a merged TU (several entries sharing a group) yields one unit.
    Entries without a group (externals) are skipped.
    """
    seen: set[tuple[str, str]] = set()
    for e in entries:
        if e["kind"] != "function":
            continue
        group = e["group"]
        if group:
            seen.add((e["module"], group))
    return sorted(seen)


def compile_command(repo: Path, clang: str, cflags: list[str],
                    include_dirs: list[Path], src: Path, obj: Path) -> dict:
    """One ``compile_commands.json`` record for a translation unit."""
    arguments = [clang, *cflags, *(f"-I{d}" for d in include_dirs), "-c", str(src),
                 "-o", str(obj)]
    return {"directory": str(repo), "arguments": arguments, "file": str(src)}


def build_db(repo: Path, entries: list[dict], toolchain: dict, cfg: dict) -> list[dict]:
    """The compile database: one entry per translation unit whose source exists."""
    clang = toolchain.get("clang", "clang")
    cflags = list(toolchain["cflags"]) + list(toolchain.get("section_flags", []))
    include_dirs = [(repo / d).resolve() for d in cfg["include_dirs"]]
    src_root = repo / cfg["source_root"]
    obj_root = repo / cfg["object_dir"]
    db: list[dict] = []
    for module, group in function_groups(entries):
        src = src_root / module / f"{group}.cpp"
        if not src.exists():
            continue
        obj = obj_root / module / f"{group}.o"
        db.append(compile_command(repo, clang, cflags, include_dirs, src.resolve(),
                                  obj.resolve()))
    return db


def render(db: list[dict]) -> str:
    """Deterministic JSON rendering (stable key order, trailing newline)."""
    return json.dumps(db, indent=2, ensure_ascii=False, sort_keys=False) + "\n"


# --- main -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER,
                    help="committed ledger (default config/main/ledger.tsv)")
    ap.add_argument("--toolchain", type=Path, default=DEFAULT_TOOLCHAIN,
                    help="pinned compiler flags (default config/toolchain.json)")
    ap.add_argument("--build-config", type=Path, default=DEFAULT_BUILD,
                    help="shared build layout constants (default config/build.json)")
    ap.add_argument("--repo", type=Path, default=REPO,
                    help="repo root that source paths are relative to")
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the compile database is out of date")
    args = ap.parse_args(argv)

    for path in (args.ledger, args.toolchain, args.build_config):
        if not path.exists():
            print(f"error: missing {path}", file=sys.stderr)
            return 2

    try:
        cfg = load_build_config(load_json(args.build_config, "build config"))
        toolchain = load_json(args.toolchain, "toolchain config")
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not toolchain.get("cflags"):
        print(f"error: toolchain config {args.toolchain} has no \"cflags\"",
              file=sys.stderr)
        return 2

    repo = args.repo.resolve()
    entries = read_entries(args.ledger)
    db = build_db(repo, entries, toolchain, cfg)
    text = render(db)

    out = repo / cfg["compile_db"]
    groups = len(function_groups(entries))
    print(f"compile db: {len(db)}/{groups} translation unit(s) have a source")

    if args.check:
        if not out.exists():
            print(f"error: {out} is missing — run tools/build/gen_compile_db.py",
                  file=sys.stderr)
            return 1
        if out.read_text() != text:
            print(f"error: {out} is out of date — run tools/build/gen_compile_db.py",
                  file=sys.stderr)
            return 1
        print("  OK: up to date")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
