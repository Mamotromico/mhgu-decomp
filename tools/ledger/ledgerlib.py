"""Shared ledger schema, reader, and the one canonical "matched" predicate.

Every tool that reads the committed ledger — the gate, the validator, the progress
reporter, CI — imports its schema and predicate from *here*, so the definitions cannot
drift (see ``docs/architecture.md`` → *Status layer & the shared "matched" predicate*).

The ledger is a line-oriented TSV with a mandatory header (``docs/architecture.md`` →
*Ledger & export format*). ``read_entries`` returns one dict per record, keyed by the
header; ``set_field`` edits a single record's field in place, line-surgically, so a status
write never reformats the rest of the file, and ``set_fields`` does the same for a set of
columns that must land together.

The predicate is expressed once::

    include(e)    := e.kind not in (external, import-stub)   # leave the denominator
    counted(e)    := include(e) and not is_alias(e)          # honesty guard
    decompiled(e) := counted(e) and e.verify == match
    behaviour(e)  := counted(e) and e.verify == behaviour
    built_stub(e) := e.kind == import-stub and e.verify == match

``import-stub`` is a **linker-generated** GOT import stub (the 12-byte ``add/add/ldr pc``
thunks at the end of ``.text``), not compiled code — so it leaves the denominator like an
external, but it keeps its address/block/size because it *does* occupy ``.text`` and the
block partition must stay gapless. Its ``verify=match`` means "derived from the GOT map and
byte-identical to the reference" (see ``tools/ledger/importstub.py``), never "decompiled".

``is_alias`` is a placeholder returning false until alias detection is settled (an open
item in ``docs/architecture.md``); the zero-size guard is implemented, since it needs no
extra data.
"""

from __future__ import annotations

import csv
from pathlib import Path

# --- schema ---------------------------------------------------------------------------
# Identity columns first, then linker/identity attributes, then the four status axes.
# ``reloc`` is *derived* by the link build and deliberately NOT stored.
LEDGER_COLUMNS = [
    "module",
    "addr",
    "kind",       # function | data | import-stub | external
    "name",       # ledger identity: func_/D_/plt_/discovered, never the Ghidra raw name
    "block",      # memory block (.text/.rodata/.data/.bss); "" for externals
    "group",      # translation-unit membership; one-function-per-file default = name
    "size",       # bytes; "" for externals
    "name_class", # discovered | generated
    "bind",       # ELF binding, externals only (LOCAL|GLOBAL|WEAK)
    "guess",      # 0/1 — a *guessed* real name (never a placeholder)
    "verify",     # none | behaviour | match
    "gate",       # how verify was established: "" (no match) | raw | reloc
    "review",     # generated | reviewed
    "enroll",     # rombytes | complete ("" for externals and import-stubs)
]

KINDS = ("function", "data", "import-stub", "external")
# Kinds that are not reconstructed from source and therefore never in the denominator.
# ``external`` has no address at all; ``import-stub`` has one (it is real ``.text``).
UNCOUNTED_KINDS = ("external", "import-stub")
VERIFY_VALUES = ("none", "behaviour", "match")
# Provenance of a ``verify=match``. ``""`` is not evidence: it is the only value an entry
# without a match may carry. ``raw`` is the byte-identical compare; ``reloc`` means at least
# one address-dependent word was verified through its relocation rather than byte-for-byte
# (see ``docs/architecture.md`` -> *Gate provenance*); ``link`` is a linker-generated
# ``import-stub`` reproduced from the GOT map (never compiled), see ``importstub.py``.
GATE_VALUES = ("raw", "reloc", "link")
REVIEW_VALUES = ("generated", "reviewed")
ENROLL_VALUES = ("rombytes", "complete")
NAMING_CLASSES = ("discovered", "generated")

STATUS_DEFAULTS = {"verify": "none", "gate": "", "review": "generated",
                   "enroll": "rombytes"}


def read_entries(path: Path) -> list[dict]:
    """Read the ledger into one dict per record (header-keyed)."""
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def entry_key(entry: dict) -> tuple[str, str]:
    """The ledger key: ``(module, addr)`` (addr empty for externals)."""
    return entry["module"], entry["addr"]


# --- the shared predicate -------------------------------------------------------------

def included(e: dict) -> bool:
    """A source-reconstructed entry counts toward the denominator.

    Externals (no address, provided by the SDK) and ``import-stub`` entries (linker output,
    not compilable C — see ``AGENTS.md`` -> *Linker veneers are not functions*) are both
    excluded; a stub still occupies ``.text``, so it stays in the block partition.
    """
    return e["kind"] not in UNCOUNTED_KINDS


def is_zero_size(e: dict) -> bool:
    """A zero-size content entry counts in neither numerator nor denominator.

    Externals carry an empty ``size``; they are already excluded by ``included``.
    """
    return e["size"] in ("", None) or int(e["size"]) == 0


def is_alias(e: dict) -> bool:
    """Placeholder: alias detection is an open item; no entry is an alias yet."""
    return False


def counted(e: dict) -> bool:
    """In the progress denominator (honesty guards applied)."""
    return included(e) and not is_alias(e) and not is_zero_size(e)


def decompiled(e: dict) -> bool:
    return counted(e) and e["verify"] == "match"


def behaviour(e: dict) -> bool:
    return counted(e) and e["verify"] == "behaviour"


def is_import_stub(e: dict) -> bool:
    """A linker-generated GOT import stub (not compiled code, not in the denominator)."""
    return e["kind"] == "import-stub"


def built_stub(e: dict) -> bool:
    """An ``import-stub`` reproduced byte-identically from the GOT map.

    This is *not* a decompilation: the body is derived from ``(stub address, GOT slot)`` the
    same way the linker derived it, and checked against the reference bytes. It is reported
    separately from ``decompiled`` so the two can never be confused.
    """
    return is_import_stub(e) and e["verify"] == "match" and e["gate"] == "link"


def matched_counts(entries: list[dict]) -> dict:
    """The published buckets, all derived from the one predicate."""
    return {
        "counted": sum(1 for e in entries if counted(e)),
        "decompiled": sum(1 for e in entries if decompiled(e)),
        "behaviour": sum(1 for e in entries if behaviour(e)),
        "import_stubs": sum(1 for e in entries if is_import_stub(e)),
        "import_stubs_built": sum(1 for e in entries if built_stub(e)),
    }


# --- surgical write -------------------------------------------------------------------

def set_field(path: Path, key: tuple[str, str], column: str, value: str) -> bool:
    """Set one record's ``column`` to ``value`` in place; return whether a row changed.

    Line-surgical: only the matching line is rewritten (split/join on tabs), so the rest
    of the file is byte-preserved. ``key`` is ``(module, addr)``.
    """
    return bool(set_fields(path, key, {column: value}))


def set_fields(path: Path, key: tuple[str, str], updates: dict[str, str]) -> list[str]:
    """Set several columns of one record in a single rewrite; return the columns changed.

    The status write is a unit: ``verify`` and ``gate`` are written together, so no reader
    can observe a match whose provenance line has not landed yet. Like :func:`set_field`
    the edit is line-surgical — every other line stays byte-identical.
    """
    path = Path(path)
    if not updates:
        return []
    lines = path.read_text().splitlines(keepends=True)
    if not lines:
        raise ValueError(f"{path}: empty ledger")
    header = lines[0].rstrip("\n").split("\t")
    cols: dict[str, int] = {}
    for column in updates:
        try:
            cols[column] = header.index(column)
        except ValueError:
            raise ValueError(f"{path}: no such column {column!r}")
    module, addr = key
    for i, line in enumerate(lines[1:], start=1):
        fields = line.rstrip("\n").split("\t")
        if len(fields) > max(cols.values()) and fields[0] == module and fields[1] == addr:
            changed = [c for c in updates if fields[cols[c]] != updates[c]]
            if not changed:
                return []
            for c in changed:
                fields[cols[c]] = updates[c]
            lines[i] = "\t".join(fields) + "\n"
            path.write_text("".join(lines))
            return changed
    raise KeyError(f"{path}: no entry for {key}")
