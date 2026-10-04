#!/usr/bin/env python3
"""Regression tests for the externals-seed demangled-signature parser.

Pure-function tests — no demangler subprocess, no ledger, no binary. Run with::

    python3 tests/build/test_seed_externals.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "build"))

from seed_externals import (
    classify_kind,
    find_params_start,
    is_builtin_param,
    matching_paren,
    no_signature_kind,
    param_kind,
    parse,
    split_qualified,
    split_top,
    summarize_params,
)


class SplitQualifiedTests(unittest.TestCase):
    def test_namespaced(self):
        self.assertEqual(split_qualified("nn::fs::GetFileSize"), ("nn::fs", "GetFileSize"))

    def test_unqualified(self):
        self.assertEqual(split_qualified("CreateFile"), ("", "CreateFile"))

    def test_template_scope_is_not_split_inside_angles(self):
        self.assertEqual(split_qualified("nn::Foo<Bar::Baz>::f"), ("nn::Foo<Bar::Baz>", "f"))


class SplitTopTests(unittest.TestCase):
    def test_commas_inside_template_args_are_not_separators(self):
        self.assertEqual(split_top("int, nn::A<B, C>, char"), ["int", "nn::A<B, C>", "char"])

    def test_empty(self):
        self.assertEqual(split_top(""), [])


class ParamTests(unittest.TestCase):
    def test_param_kinds(self):
        self.assertEqual(param_kind("unsigned int"), "scalar")
        self.assertEqual(param_kind("char const*"), "ptr")
        self.assertEqual(param_kind("nn::fs::FileHandle"), "class-value")
        self.assertEqual(param_kind("void"), "void")
        self.assertEqual(param_kind("..."), "variadic")
        self.assertEqual(param_kind("void (*)(void*)"), "fnptr")

    def test_builtin_params(self):
        for good in ("void", "...", "int", "unsigned long long", "char const*",
                     "void*", "bool", "double&"):
            self.assertTrue(is_builtin_param(good), good)
        for bad in ("nn::fs::FileHandle", "nn::fs::FileHandle*", "in_addr*",
                    "addrinfo const*", "void (*)(int)"):
            self.assertFalse(is_builtin_param(bad), bad)

    def test_summarize_flags_byvalue_class(self):
        self.assertEqual(summarize_params("long long*, nn::fs::FileHandle")[1],
                         "has-byvalue-class")
        self.assertEqual(summarize_params("int, char const*")[1], "scalars")
        self.assertEqual(summarize_params("")[1], "void")


class ClassifyKindTests(unittest.TestCase):
    def test_ctor_and_dtor(self):
        self.assertEqual(classify_kind("nn::fs::FileHandle::FileHandle", "")[0], "ctor")
        self.assertEqual(classify_kind("nn::fs::FileHandle::~FileHandle", "")[0], "dtor")

    def test_const_member(self):
        self.assertEqual(classify_kind("nn::util::Font::GetFontData", " const")[0],
                         "member-const")

    def test_free_vs_qualified_ambiguity(self):
        self.assertEqual(classify_kind("nn::fs::CreateFile", "")[0], "qualified")
        self.assertEqual(classify_kind("CreateFile", "")[0], "free-global")


class ParseTests(unittest.TestCase):
    def test_free_scalar_is_a_candidate(self):
        r = parse("_ZN2nn2fs10CreateFileEPKcx", "nn::fs::CreateFile(char const*, long long)")
        self.assertEqual(r["kind"], "qualified")
        self.assertEqual(r["ns"], "nn::fs")
        self.assertEqual(r["name"], "CreateFile")
        self.assertIn('asm("_ZN2nn2fs10CreateFileEPKcx")', r["decl_hint"])

    def test_byvalue_class_is_not_a_candidate(self):
        r = parse("_ZN2nn2fs11GetFileSizeEPxNS0_10FileHandleE",
                  "nn::fs::GetFileSize(long long*, nn::fs::FileHandle)")
        self.assertEqual(r["param_kind"], "has-byvalue-class")
        self.assertEqual(r["decl_hint"], "")

    def test_pointer_to_class_is_not_a_candidate(self):
        r = parse("_ZN2nn2fs8OpenFileEPNS0_10FileHandleEPKci",
                  "nn::fs::OpenFile(nn::fs::FileHandle*, char const*, int)")
        self.assertEqual(r["decl_hint"], "")

    def test_template_scope_is_not_a_candidate(self):
        r = parse("_ZN2nn6crypto6detail7AesImplILj16EE10InitializeEPKvjb",
                  "nn::crypto::detail::AesImpl<16u>::Initialize(void const*, unsigned int, "
                  "bool)")
        self.assertEqual(r["decl_hint"], "")

    def test_no_signature_kinds(self):
        self.assertEqual(no_signature_kind("_ZTVN10__cxxabiv117__class_type_infoE",
                                           "vtable for __cxxabiv1::__class_type_info"),
                         "vtable")
        self.assertEqual(no_signature_kind("_ZN2nn3hid6NpadId8HandheldE",
                                           "nn::hid::NpadId::Handheld"), "data")
        self.assertEqual(no_signature_kind("__aeabi_memcpy", "__aeabi_memcpy"), "c-symbol")


class PositionTests(unittest.TestCase):
    def test_find_params_start_skips_template_angles(self):
        s = "nn::A<B>::f(int)"
        self.assertEqual(s[find_params_start(s)], "(")

    def test_matching_paren_handles_nesting(self):
        s = "f(void (*)(int))"
        end = matching_paren(s, find_params_start(s))
        self.assertEqual(s[end], ")")


if __name__ == "__main__":
    unittest.main()
