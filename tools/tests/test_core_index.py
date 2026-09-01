# Module name: tools/tests/test_core_index.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

"""Tests for tools/core_index.py — the core interface index generator.

Run: python -m unittest discover -s tools/tests -v

Every assertion here is a claim about the tool, so each carries a mutation that
must break it (DR-WFL-023). The fixture is written inline rather than read from
the real package: the tool's behaviour must be provable without the source it
normally reads.
"""

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core_index import (  # noqa: E402
    Application,
    MarkdownOverview,
    SnippetCatalogue,
    SourceReader,
)

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Fixture                                                              #
# --------------------------------------------------------------------------- #

# Four shapes in one module: the conforming case, the double-I name that broke
# the stem, a class with no abstract method of its own, and the two ways a
# docstring departs from the convention.
FIXTURE = '''
from abc import ABC, abstractmethod


class IIterator(IWattleflow, ABC):
    """
    IIterator - Iterator abstract interface.

    Prose that explains why.

    Interface:
        create_iterator() -> Iterator[Element]
    """

    @abstractmethod
    def create_iterator(self) -> Iterator[Element]: ...


class IAsyncThing(IWattleflow, ABC):
    """
    IAsyncThing - Async abstract interface.

    Interface:
        run() -> None
    """

    @abstractmethod
    async def run(self, timeout: float = 1.0) -> None: ...

    def helper(self) -> None:
        """Not abstract, so not part of the contract."""


class INoDocstring(IWattleflow, ABC):
    @abstractmethod
    def process(self, data: Element) -> None: ...


class IWrongSummary(IWattleflow, ABC):
    """
    Some other opening line entirely.

    Interface:
        act() -> None
    """

    @abstractmethod
    def act(self) -> None: ...


class INoInterfaceBlock(IWattleflow, ABC):
    """
    INoInterfaceBlock - Blockless abstract interface.

    Prose only.
    """
'''


class IndexHarness(unittest.TestCase):
    """Writes the fixture into a temporary package and reads it back."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.package = Path(self._tmp.name) / "core"
        self.package.mkdir()
        (self.package / "behavioural.py").write_text(FIXTURE, encoding="utf-8")
        # Only *.py that is not dunder should be read.
        (self.package / "__init__.py").write_text(
            'class INotRead(ABC):\n    """INotRead - re-export only."""\n',
            encoding="utf-8",
        )
        self.interfaces = SourceReader.read(self.package)
        self.by_name = {i.name: i for i in self.interfaces}
        self.addCleanup(self._tmp.cleanup)


# --------------------------------------------------------------------------- #
# endregion Fixture                                                           #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Tests                                                                #
# --------------------------------------------------------------------------- #


class TestReader(IndexHarness):
    def test_dunder_modules_are_skipped(self):
        # `__init__.py` re-exports; a class found there would be a duplicate.
        self.assertNotIn("INotRead", self.by_name)
        self.assertEqual(len(self.interfaces), 5)

    def test_role_is_taken_from_the_summary_line(self):
        self.assertEqual(self.by_name["IIterator"].role, "Iterator abstract interface")

    def test_prose_excludes_summary_and_interface_block(self):
        prose = self.by_name["IIterator"].prose
        self.assertEqual(prose, "Prose that explains why.")

    def test_declared_contract_is_captured(self):
        self.assertEqual(self.by_name["IIterator"].declared, ["create_iterator() -> Iterator[Element]"])

    def test_only_abstract_methods_enter_the_contract(self):
        names = [m.name for m in self.by_name["IAsyncThing"].methods]
        self.assertEqual(names, ["run"])

    def test_signature_keeps_defaults_and_return(self):
        method = self.by_name["IAsyncThing"].methods[0]
        self.assertEqual(method.signature, "run(self, timeout: float=1.0) -> None")
        self.assertTrue(method.is_async)

    def test_bases_are_recorded(self):
        self.assertEqual(self.by_name["IIterator"].bases, ["IWattleflow", "ABC"])


class TestFindings(IndexHarness):
    def test_missing_docstring_is_a_finding(self):
        self.assertEqual(self.by_name["INoDocstring"].findings, ["no docstring"])

    def test_wrong_summary_is_a_finding(self):
        findings = self.by_name["IWrongSummary"].findings
        self.assertIn("summary line is not `Name - role`", findings)

    def test_missing_interface_block_is_a_finding(self):
        self.assertIn("no `Interface:` block", self.by_name["INoInterfaceBlock"].findings)

    def test_conforming_interface_has_no_finding(self):
        self.assertEqual(self.by_name["IIterator"].findings, [])


class TestSnippets(IndexHarness):
    def _entries(self) -> dict:
        raw = SnippetCatalogue.render(self.interfaces, "test")
        stripped = "\n".join(line for line in raw.splitlines() if not line.strip().startswith("//"))
        return json.loads(stripped)

    def test_output_is_valid_json_once_comments_are_stripped(self):
        # VS Code accepts JSONC; the header must not be the only thing making it
        # parse, so the body alone has to be valid JSON.
        entries = self._entries()
        self.assertEqual(len(entries), len(self.interfaces) + 1)

    def test_prefix_carries_the_interface_name(self):
        entry = self._entries()["wattleflow.core: IIterator"]
        self.assertEqual(entry["prefix"], "wfIIterator")

    def test_stem_strips_one_leading_i_not_a_character_set(self):
        # `lstrip("I")` turned IIterator into `terator`; removeprefix must not.
        body = self._entries()["wattleflow.core: IIterator"]["body"][0]
        self.assertEqual(body, "class ${1:MyIterator}(IIterator):")

    def test_description_carries_module_and_role(self):
        entry = self._entries()["wattleflow.core: IIterator"]
        self.assertIn("behavioural", entry["description"])
        self.assertIn("Iterator abstract interface", entry["description"])

    def test_missing_role_is_visible_in_the_description(self):
        # A silent blank would read as "no role needed"; it must say so.
        entry = self._entries()["wattleflow.core: INoDocstring"]
        self.assertIn("(role not declared)", entry["description"])

    def test_async_method_keeps_its_keyword_in_the_stub(self):
        body = self._entries()["wattleflow.core: IAsyncThing"]["body"]
        self.assertIn("    async def run(self, timeout: float=1.0) -> None:", body)

    def test_tab_stops_are_unique_and_ordered(self):
        body = "\n".join(self._entries()["wattleflow.core: IAsyncThing"]["body"])
        self.assertIn("${1:MyAsyncThing}", body)
        self.assertIn("${2:...}", body)
        self.assertIn("$0", body)


class TestMarkdown(IndexHarness):
    def setUp(self) -> None:
        super().setUp()
        self.text = MarkdownOverview.render(self.interfaces, "test", self.package)

    def test_declares_itself_generated(self):
        self.assertIn("not a source of truth (D-13)", self.text)

    def test_contents_table_links_every_interface(self):
        for name in self.by_name:
            self.assertIn(f"[`{name}`](#{name.lower()})", self.text)

    def test_missing_role_is_flagged_in_the_table(self):
        self.assertIn("**(role not declared)**", self.text)

    def test_findings_are_rendered_not_swallowed(self):
        self.assertIn("> **Finding:** no docstring.", self.text)

    def test_inherited_contract_falls_back_to_the_docstring_block(self):
        # INoInterfaceBlock has neither; IIterator has an abstract method, so
        # the fallback must not fire for it.
        self.assertIn("def create_iterator(self) -> Iterator[Element]: ...", self.text)


class TestApplication(IndexHarness):
    def _run(self, *argv) -> tuple[int, str]:
        buffer = StringIO()
        with redirect_stdout(buffer):
            code = Application.run(["--package", str(self.package), *argv])
        return code, buffer.getvalue()

    def test_check_exits_nonzero_when_the_convention_is_broken(self):
        code, out = self._run("--check")
        self.assertEqual(code, 1)
        self.assertIn("2/5 conform, 3 depart", out)

    def test_missing_package_is_an_error_not_an_empty_index(self):
        code = Application.run(["--package", str(self.package / "nope")])
        self.assertEqual(code, 2)

    def test_writes_both_outputs_and_creates_parents(self):
        out_dir = Path(self._tmp.name) / "made" / "up"
        snippets = out_dir / "s.code-snippets"
        markdown = out_dir / "m.md"
        code, _ = self._run("--snippets", str(snippets), "--markdown", str(markdown))
        self.assertEqual(code, 0)
        self.assertTrue(snippets.is_file())
        self.assertTrue(markdown.is_file())

    def test_writing_and_checking_together_still_reports_the_failure(self):
        snippets = Path(self._tmp.name) / "s.code-snippets"
        code, _ = self._run("--snippets", str(snippets), "--check")
        self.assertEqual(code, 1)


# --------------------------------------------------------------------------- #
# endregion Tests                                                             #
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    unittest.main(verbosity=2)
