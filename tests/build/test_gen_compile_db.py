#!/usr/bin/env python3
"""Regression tests for the compile-database generator's pure helpers.

No clang, no ledger, no filesystem beyond a temp dir for the one existence check. Run with::

    python3 tests/build/test_gen_compile_db.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "build"))

from gen_compile_db import (
    ConfigError,
    build_db,
    compile_command,
    function_groups,
    load_build_config,
    load_json,
    render,
)


def entry(module: str, kind: str, group: str) -> dict:
    return {"module": module, "kind": kind, "group": group}


class LoadBuildConfigTests(unittest.TestCase):
    def test_defaults_fill_absent_keys(self):
        cfg = load_build_config({})
        self.assertEqual(cfg["source_root"], "src")
        self.assertEqual(cfg["include_dirs"], ["include"])

    def test_present_keys_win(self):
        cfg = load_build_config({"source_root": "code", "include_dirs": ["inc"]})
        self.assertEqual(cfg["source_root"], "code")
        self.assertEqual(cfg["include_dirs"], ["inc"])
        self.assertEqual(cfg["object_dir"], "build/obj")  # untouched default


class LoadJsonTests(unittest.TestCase):
    """A malformed config must surface as ConfigError, never a raw traceback."""

    def setUp(self):
        import tempfile
        self._dir = tempfile.TemporaryDirectory()
        self._tmp = Path(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_reads_object(self):
        p = self._tmp / "c.json"
        p.write_text('{"a": 1}')
        self.assertEqual(load_json(p, "thing"), {"a": 1})

    def test_bad_json_is_config_error(self):
        p = self._tmp / "c.json"
        p.write_text("{not json")
        with self.assertRaises(ConfigError):
            load_json(p, "thing")

    def test_non_object_is_config_error(self):
        p = self._tmp / "c.json"
        p.write_text("[1, 2]")
        with self.assertRaises(ConfigError):
            load_json(p, "thing")

    def test_missing_file_is_config_error(self):
        with self.assertRaises(ConfigError):
            load_json(self._tmp / "nope.json", "thing")


class FunctionGroupsTests(unittest.TestCase):
    def test_only_functions_and_nonempty_groups(self):
        entries = [entry("main", "function", "func_1"), entry("main", "data", "D_1"),
                   entry("main", "external", "")]
        self.assertEqual(function_groups(entries), [("main", "func_1")])

    def test_merged_tu_collapses_to_one(self):
        entries = [entry("main", "function", "grp"), entry("main", "function", "grp")]
        self.assertEqual(function_groups(entries), [("main", "grp")])

    def test_deterministic_order(self):
        entries = [entry("main", "function", "b"), entry("main", "function", "a"),
                   entry("other", "function", "a")]
        self.assertEqual(function_groups(entries), [("main", "a"), ("main", "b"),
                                                    ("other", "a")])


class CompileCommandTests(unittest.TestCase):
    def test_arguments_and_file(self):
        repo = Path("/r")
        cmd = compile_command(repo, "clang", ["-O2"], [Path("/r/include")],
                              Path("/r/src/main/x.cpp"), Path("/r/build/obj/main/x.o"))
        self.assertEqual(cmd["directory"], "/r")
        self.assertEqual(cmd["file"], "/r/src/main/x.cpp")
        self.assertEqual(cmd["arguments"][0], "clang")
        self.assertIn("-I/r/include", cmd["arguments"])
        self.assertEqual(cmd["arguments"][-4:],
                         ["-c", "/r/src/main/x.cpp", "-o", "/r/build/obj/main/x.o"])

    def test_source_and_output_present(self):
        cmd = compile_command(Path("/r"), "clang", [], [], Path("/r/a.cpp"), Path("/r/a.o"))
        self.assertEqual(cmd["arguments"][-4:], ["-c", "/r/a.cpp", "-o", "/r/a.o"])


class BuildDbTests(unittest.TestCase):
    """The generator only emits entries for groups whose source file exists."""

    def setUp(self):
        import tempfile
        self._dir = tempfile.TemporaryDirectory()
        self._tmp = Path(self._dir.name)
        (self._tmp / "src" / "main").mkdir(parents=True)

    def tearDown(self):
        self._dir.cleanup()

    def cfg(self) -> dict:
        return {"source_root": "src", "include_dirs": ["include"],
                "object_dir": "build/obj", "compile_db": "build/compile_commands.json"}

    def test_only_existing_sources_are_emitted(self):
        (self._tmp / "src" / "main" / "func_1.cpp").write_text("// x\n")
        entries = [entry("main", "function", "func_1"), entry("main", "function", "func_2")]
        db = build_db(self._tmp, entries, {"clang": "clang", "cflags": ["-O2"]}, self.cfg())
        self.assertEqual(len(db), 1)
        self.assertTrue(db[0]["file"].endswith("src/main/func_1.cpp"))
        self.assertTrue(db[0]["arguments"][-1].endswith("build/obj/main/func_1.o"))

    def test_render_is_deterministic(self):
        db = [compile_command(Path("/r"), "clang", [], [], Path("/r/a.cpp"), Path("/r/a.o"))]
        self.assertEqual(render(db), render(db))
        self.assertTrue(render(db).endswith("\n"))


if __name__ == "__main__":
    unittest.main()
