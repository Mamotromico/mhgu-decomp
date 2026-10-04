"""Shared ledger schema, reader, and the one canonical "matched" predicate.

Every tool that reads the committed ledger — the gate, the validator, the progress
reporter, CI — imports its schema and predicate from *here*, so the definitions cannot
drift (see ``docs/architecture.md`` → *Status layer & the shared "matched" predicate*).

The ledger is a line-oriented TSV with a mandatory header (``docs/architecture.md`` →
*Ledger & export format*). ``read_entries`` returns one dict per record, keyed by the
header; ``set_field`` edits a single record's field in place, line-surgically, so a status
write never reformats the rest of the file.

The predicate is expressed once::

    include(e)    := e.kind != external                 # externals leave the denominator
    counted(e)    := include(e) and not is_alias(e)     # honesty guard
    decompiled(e) := counted(e) and e.verify == match
    behaviour(e)  := counted(e) and e.verify == behaviour

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
    "kind",       # function | data | external
    "name",       # ledger identity: func_/D_/discovered, never the Ghidra raw name
    "block",      # memory block (.text/.rodata/.data/.bss); "" for externals
    "group",      # translation-unit membership; one-function-per-file default = name
    "size",       # bytes; "" for externals
    "name_class", # discovered | generated
    "bind",       # ELF binding, externals only (LOCAL|GLOBAL|WEAK)
    "guess",      # 0/1 — a *guessed* real name (never a placeholder)
    "verify",     # none | behaviour | match
    "review",     # generated | reviewed
    "enroll",     # rombytes | complete ("" for externals)
]

KINDS = ("function", "data", "external")
VERIFY_VALUES = ("none", "behaviour", "match")
REVIEW_VALUES = ("generated", "reviewed")
ENROLL_VALUES = ("rombytes", "complete")
NAMING_CLASSES = ("discovered", "generated")

STATUS_DEFAULTS = {"verify": "none", "review": "generated", "enroll": "rombytes"}


def read_entries(path: Path) -> list[dict]:
    """Read the ledger into one dict per record (header-keyed)."""
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def entry_key(entry: dict) -> tuple[str, str]:
    """The ledger key: ``(module, addr)`` (addr empty for externals)."""
    return entry["module"], entry["addr"]


# --- the shared predicate -------------------------------------------------------------

def included(e: dict) -> bool:
    """A non-external entry counts toward the denominator."""
    return e["kind"] != "external"


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


def matched_counts(entries: list[dict]) -> dict:
    """The published buckets, all derived from the one predicate."""
    n_counted = n_decompiled = n_behaviour = 0
    for e in entries:
        if counted(e):
            n_counted += 1
            if e["verify"] == "match":
                n_decompiled += 1
            elif e["verify"] == "behaviour":
                n_behaviour += 1
    return {
        "counted": n_counted,
        "decompiled": n_decompiled,
        "behaviour": n_behaviour,
    }


# --- surgical write -------------------------------------------------------------------

def set_field(path: Path, key: tuple[str, str], column: str, value: str) -> bool:
    """Set one record's ``column`` to ``value`` in place; return whether a row changed.

    Line-surgical: only the matching line is rewritten (split/join on tabs), so the rest
    of the file is byte-preserved. ``key`` is ``(module, addr)``.
    """
    path = Path(path)
    lines = path.read_text().splitlines(keepends=True)
    if not lines:
        raise ValueError(f"{path}: empty ledger")
    header = lines[0].rstrip("\n").split("\t")
    try:
        col = header.index(column)
    except ValueError:
        raise ValueError(f"{path}: no such column {column!r}")
    module, addr = key
    for i, line in enumerate(lines[1:], start=1):
        fields = line.rstrip("\n").split("\t")
        if len(fields) > col and fields[0] == module and fields[1] == addr:
            if fields[col] == value:
                return False
            fields[col] = value
            lines[i] = "\t".join(fields) + "\n"
            path.write_text("".join(lines))
            return True
    raise KeyError(f"{path}: no entry for {key}")
