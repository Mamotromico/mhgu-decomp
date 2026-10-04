#!/usr/bin/env python3
"""Seed the ``include/`` declaration tree from the ledger's externals (Phase A).

The ledger reproduces the exact Itanium-**mangled** name of every external (``dynsym``), and
mangling *encodes the parameter types*, so a demangle pass recovers each signature almost for
free (``docs/llm-harness-design.md`` → *The declaration layer*). This tool performs that pass
and writes, under ``include/generated/``:

* ``externals.tsv`` — the review catalog: ``mangled`` / ``demangled`` / parsed ``kind`` /
  ``ns`` / ``name`` / ``params`` / ``param_kind`` / ``decl_hint`` for every external; and
* ``externals.hpp`` — compilable **Phase A candidates** (``asm("mangled")``-pinned) for the
  subset whose types are expressible today (scalar / pointer / reference parameters on a
  free function).

What this tool deliberately does **not** guess
----------------------------------------------
* **Return types.** Itanium mangling does not encode a non-template function's return type,
  so no return type is recoverable; the candidates declare ``void`` as a placeholder and the
  catalog leaves ``ret`` to review.
* **Member vs. free.** ``A::B::f`` is a free function in namespace ``A::B`` *or* a member of
  class ``B``; the mangled form does not distinguish the two (const members, ctors, dtors and
  operators do carry a marker and are classified). Such names are catalogued as ``qualified``
  and only emitted as candidates when a declaration compiles either way.
* **By-value class types.** A by-value aggregate parameter needs a *complete* type, so a name
  taking one is catalogued but not emitted until its type is reconstructed.

The output is a deterministic function of the committed ledger, and is committed so it is
reviewable in a diff; ``--check`` fails on drift.

Usage::

    python3 tools/build/seed_externals.py            # write include/generated/*
    python3 tools/build/seed_externals.py --check    # fail if out of date (CI)
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "ledger"))

from ledgerlib import read_entries

DEFAULT_LEDGER = REPO / "config" / "main" / "ledger.tsv"
DEFAULT_OUT_DIR = REPO / "include" / "generated"

CATALOG_COLUMNS = ["mangled", "demangled", "bind", "kind", "ns", "name", "params",
                   "param_kind", "decl_hint"]

_SCALARS = {
    "bool", "char", "signed char", "unsigned char", "short", "unsigned short",
    "int", "unsigned int", "long", "unsigned long", "long long", "unsigned long long",
    "float", "double", "long double", "wchar_t", "char8_t", "char16_t", "char32_t",
    "void", "__int128", "unsigned __int128",
}
_SCALAR_RE = re.compile(r"(unsigned |signed )?(char|short|int|long|long long)")


# --- demangling -----------------------------------------------------------------------

def demangler() -> list[str]:
    """Prefer the clang-matched ``llvm-cxxfilt``; fall back to binutils ``c++filt``."""
    for tool in ("llvm-cxxfilt", "c++filt"):
        if shutil.which(tool):
            return [tool]
    return []


def demangle_batch(names: list[str], tool: list[str]) -> list[str]:
    """Demangle ``names`` in one subprocess, preserving order (identity on failure)."""
    if not tool or not names:
        return list(names)
    proc = subprocess.run([*tool], input="\n".join(names), capture_output=True, text=True)
    out = proc.stdout.splitlines()
    return out if len(out) == len(names) else list(names)


# --- parsing the demangled form (pure; unit-tested) -----------------------------------

def find_params_start(s: str) -> int:
    """Index of the parameter list ``(`` at angle-depth 0, or -1."""
    depth = 0
    for i, ch in enumerate(s):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        elif ch == "(" and depth == 0:
            return i
    return -1


def matching_paren(s: str, start: int) -> int:
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def split_top(s: str) -> list[str]:
    """Split on top-level commas (respecting ``<>`` and ``()`` nesting)."""
    out: list[str] = []
    depth = last = 0
    for i, ch in enumerate(s):
        if ch in "<(":
            depth += 1
        elif ch in ">)":
            depth = max(0, depth - 1)
        elif ch == "," and depth == 0:
            out.append(s[last:i])
            last = i + 1
    tail = s[last:]
    if out or tail.strip():
        out.append(tail)
    return [p.strip() for p in out]


def split_qualified(head: str) -> tuple[str, str]:
    """Split a qualified name at its last top-level ``::`` → ``(scope, leaf)``."""
    depth = 0
    idx = -1
    for i, ch in enumerate(head):
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        elif ch == ":" and depth == 0 and i + 1 < len(head) and head[i + 1] == ":":
            idx = i
    if idx < 0:
        return "", head
    return head[:idx], head[idx + 2:]


def classify_kind(head: str, qualifiers: str) -> tuple[str, str, str]:
    """Return ``(kind, scope, leaf)`` for a demangled function head."""
    scope, leaf = split_qualified(head)
    cls = split_qualified(scope)[1].split("<")[0] if scope else ""
    leaf_base = leaf.split("<")[0]
    if qualifiers.strip().startswith("const"):
        return "member-const", scope, leaf
    if leaf_base.startswith("~"):
        return "dtor", scope, leaf
    if scope and leaf_base == cls:
        return "ctor", scope, leaf
    if leaf_base.startswith("operator"):
        return "operator", scope, leaf
    if "<" in leaf:
        return "template", scope, leaf
    if not scope:
        return "free-global", scope, leaf
    return "qualified", scope, leaf


def param_kind(param: str) -> str:
    p = param.strip()
    if p in ("", "void"):
        return "void"
    if p == "...":
        return "variadic"
    if p.endswith("*") or p.endswith("&"):
        return "ptr"
    if p.endswith("]"):  # array parameter (adjusts to a pointer)
        return "ptr"
    if p in _SCALARS or _SCALAR_RE.fullmatch(p):
        return "scalar"
    if "(" in p:
        return "fnptr"
    if "::" in p or "<" in p:
        return "class-value"
    return "other"


def is_builtin_param(param: str) -> bool:
    """Whether a parameter is expressible today: a builtin scalar, pointer/reference to one,
    ``void`` or ``...``. Function-pointer and named (class/C-struct) types are excluded."""
    p = param.strip()
    if p in ("...", "void"):
        return True
    if "(" in p or ")" in p:  # function pointer — needs a decomposed type
        return False
    core = p.replace("const", " ").replace("volatile", " ")
    core = core.replace("*", " ").replace("&", " ").replace("[]", " ")
    return " ".join(core.split()) in _SCALARS


def summarize_params(params: str) -> tuple[list[str], str]:
    parts = [] if params.strip() in ("", "void") else split_top(params)
    kinds = [param_kind(p) for p in parts]
    if not kinds or kinds == ["void"]:
        return parts, "void"
    if "class-value" in kinds:
        return parts, "has-byvalue-class"
    if all(k in ("scalar", "ptr", "fnptr", "variadic") for k in kinds):
        return parts, "scalars"
    return parts, "mixed"


def no_signature_kind(mangled: str, demangled: str) -> str:
    """Classify an external that demangles to no parameter list (data / runtime C)."""
    if mangled.startswith("_ZTV"):
        return "vtable"
    if mangled.startswith("_ZTI"):
        return "typeinfo"
    if mangled.startswith("_Z"):
        return "data" if "::" in demangled else "unknown"
    return "c-symbol"


def parse(mangled: str, demangled: str) -> dict:
    """Parse one demangled signature into catalog fields."""
    start = find_params_start(demangled) if demangled != mangled else -1
    if start < 0:
        return {"kind": no_signature_kind(mangled, demangled), "ns": "", "name": demangled,
                "params": "", "param_kind": "", "decl_hint": ""}
    end = matching_paren(demangled, start)
    head = demangled[:start]
    params = demangled[start + 1:end]
    qualifiers = demangled[end + 1:]
    kind, scope, leaf = classify_kind(head, qualifiers)
    parts, pk = summarize_params(params)

    # Emit a candidate only when it needs no other declaration: the scope is a plain
    # namespace (no template args), the name is not a template, and every parameter is a
    # builtin scalar / pointer / reference. Forward declarations are a later increment.
    hint = ""
    if (kind in ("free-global", "qualified") and "<" not in scope and "<" not in leaf
            and all(is_builtin_param(p) for p in parts)):
        arg = "" if params.strip() in ("", "void") else params
        decl = f"void {leaf}({arg})"
        if scope:
            hint = f"namespace {scope} {{ {decl} asm(\"{mangled}\"); }}"
        else:
            hint = f"{decl} asm(\"{mangled}\");"
    return {"kind": kind, "ns": scope, "name": leaf, "params": params,
            "param_kind": pk, "decl_hint": hint}


# --- rendering ------------------------------------------------------------------------

def render_catalog(rows: list[dict]) -> str:
    lines = ["\t".join(CATALOG_COLUMNS)]
    for r in rows:
        lines.append("\t".join(str(r.get(c, "")) for c in CATALOG_COLUMNS))
    return "\n".join(lines) + "\n"


def render_header(rows: list[dict]) -> str:
    hints = [r for r in rows if r["decl_hint"]]
    out = [
        "// GENERATED by tools/build/seed_externals.py — do not edit by hand.",
        "// Phase A candidates: the mangled symbol is pinned with asm(); the return type is a",
        "// 'void' PLACEHOLDER (mangling does not encode it) and a 'qualified' name may be a",
        "// free function or a member. Promote real declarations into include/<ns>/ as types",
        "// are reconstructed; see docs/llm-harness-design.md. Regenerate with --check in CI.",
        f"// {len(hints)} of {len(rows)} externals are expressible with today's type knowledge.",
        "",
        "#pragma once",
        "",
    ]
    for r in hints:
        out.append(f"// {r['demangled']}")
        out.append(r["decl_hint"])
    out.append("")
    return "\n".join(out)


# --- main -----------------------------------------------------------------------------

def build_rows(entries: list[dict], tool: list[str]) -> list[dict]:
    externals = [e for e in entries if e["kind"] == "external"]
    demangled = demangle_batch([e["name"] for e in externals], tool)
    rows = []
    for e, dem in zip(externals, demangled):
        row = {"mangled": e["name"], "demangled": dem, "bind": e["bind"]}
        row.update(parse(e["name"], dem))
        rows.append(row)
    return rows


def report(rows: list[dict], out_dir: Path) -> str:
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    hinted = sum(1 for r in rows if r["decl_hint"])
    lines = [f"externals seed: {out_dir}", f"  externals   {len(rows)}"]
    for k in sorted(kinds, key=lambda x: (-kinds[x], x)):
        lines.append(f"    {k:<12} {kinds[k]}")
    lines.append(f"  candidates  {hinted} declared in externals.hpp")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the seed is out of date")
    args = ap.parse_args(argv)

    if not args.ledger.exists():
        print(f"error: missing {args.ledger}", file=sys.stderr)
        return 2

    tool = demangler()
    if not tool:
        print("error: no demangler (llvm-cxxfilt / c++filt) on PATH", file=sys.stderr)
        return 2

    rows = build_rows(read_entries(args.ledger), tool)
    files = {
        "externals.tsv": render_catalog(rows),
        "externals.hpp": render_header(rows),
    }
    print(report(rows, args.out_dir))

    if args.check:
        stale = [n for n, t in files.items()
                 if not (args.out_dir / n).exists() or (args.out_dir / n).read_text() != t]
        if stale:
            print(f"error: out of date: {', '.join(stale)} — run "
                  "tools/build/seed_externals.py", file=sys.stderr)
            return 1
        print("  OK: up to date")
        return 0

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (args.out_dir / name).write_text(text)
        print(f"wrote {args.out_dir / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
