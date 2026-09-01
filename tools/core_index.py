#!/usr/bin/env python3
# Module name: tools/core_index.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

"""Generate a browsable index of the `wattleflow.core` interfaces.

The interfaces already carry a machine-readable docstring convention, so this
tool reads them rather than a hand-kept list: presentation is generated from
the source, never maintained beside it (D-13).

Outputs a VS Code snippet catalogue (in-editor recall) and a Markdown overview
(reading). `--check` reports where the source departs from the convention.
"""

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Constants                                                            #
# --------------------------------------------------------------------------- #

VERSION = "1.0.0"

# The convention every interface docstring follows:
#     IName - <role> abstract interface.
#     <prose>
#     Interface:
#         <signature>
SUMMARY_RE = re.compile(r"^\s*(?P<name>\w+)\s*[-–]\s*(?P<role>.+?)\s*$")
INTERFACE_RE = re.compile(r"^\s*Interface:\s*$")

# Reading order: the pattern families, then the framework root. `__init__` only
# re-exports, so it carries no class of its own.
MODULE_ORDER = (
    "framework",
    "creational",
    "structural",
    "behavioural",
    "transactional",
    "concurrent",
)

MODULE_TITLES = {
    "framework": "Framework root",
    "creational": "Creational patterns",
    "structural": "Structural patterns",
    "behavioural": "Behavioural patterns",
    "transactional": "Transactional and data patterns",
    "concurrent": "Concurrent and reactive patterns",
}

SNIPPET_SCOPE = "python"

# --------------------------------------------------------------------------- #
# endregion Constants                                                         #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Model                                                                #
# --------------------------------------------------------------------------- #


@dataclass
class Method:
    """One abstract method, taken from the AST rather than from the prose."""

    name: str
    signature: str
    is_async: bool = False


@dataclass
class Interface:
    """One interface, as read from the source."""

    name: str
    module: str
    lineno: int
    bases: list[str] = field(default_factory=list)
    role: str = ""
    prose: str = ""
    declared: list[str] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def qualified(self) -> str:
        return f"wattleflow.core.{self.module}.{self.name}"

    @property
    def inherits(self) -> str:
        return ", ".join(self.bases) if self.bases else "—"


# --------------------------------------------------------------------------- #
# endregion Model                                                             #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Reader                                                               #
# --------------------------------------------------------------------------- #


class SourceReader:
    """Reads interfaces out of the core package by AST, never by import.

    Importing would execute the package and pull its runtime; the tool must run
    against a checkout that is not installed.
    """

    @classmethod
    def read(cls, package: Path) -> list[Interface]:
        found: list[Interface] = []
        for path in sorted(package.glob("*.py")):
            if path.stem.startswith("__"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    found.append(cls._interface(node, path.stem))
        return found

    @classmethod
    def _interface(cls, node: ast.ClassDef, module: str) -> Interface:
        item = Interface(
            name=node.name,
            module=module,
            lineno=node.lineno,
            bases=[ast.unparse(b) for b in node.bases],
            methods=cls._methods(node),
        )
        cls._apply_docstring(item, ast.get_docstring(node))
        return item

    @staticmethod
    def _methods(node: ast.ClassDef) -> list[Method]:
        methods: list[Method] = []
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = {ast.unparse(d) for d in child.decorator_list}
            if "abstractmethod" not in decorators:
                continue
            args = ast.unparse(
                ast.arguments(
                    posonlyargs=child.args.posonlyargs,
                    args=child.args.args,
                    vararg=child.args.vararg,
                    kwonlyargs=child.args.kwonlyargs,
                    kw_defaults=child.args.kw_defaults,
                    kwarg=child.args.kwarg,
                    defaults=child.args.defaults,
                )
            )
            returns = f" -> {ast.unparse(child.returns)}" if child.returns else ""
            methods.append(
                Method(
                    name=child.name,
                    signature=f"{child.name}({args}){returns}",
                    is_async=isinstance(child, ast.AsyncFunctionDef),
                )
            )
        return methods

    @staticmethod
    def _apply_docstring(item: Interface, doc: str | None) -> None:
        if not doc:
            item.findings.append("no docstring")
            return

        lines = doc.strip("\n").splitlines()
        body: list[str] = []
        seen_interface = False

        for index, line in enumerate(lines):
            if INTERFACE_RE.match(line):
                seen_interface = True
                continue
            if seen_interface:
                if line.strip():
                    item.declared.append(line.strip())
                continue
            if index == 0:
                match = SUMMARY_RE.match(line)
                if match and match.group("name") == item.name:
                    item.role = match.group("role").rstrip(".")
                    continue
                item.findings.append("summary line is not `Name - role`")
            body.append(line)

        item.prose = "\n".join(body).strip()
        if not seen_interface:
            item.findings.append("no `Interface:` block")


# --------------------------------------------------------------------------- #
# endregion Reader                                                            #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Renderers                                                            #
# --------------------------------------------------------------------------- #


class SnippetCatalogue:
    """Turns the interfaces into a VS Code snippet file.

    The completion list is the browser: the prefix carries the name, the
    description carries the role, so a half-remembered name is enough.
    """

    PREFIX = "wf"

    @classmethod
    def render(cls, interfaces: list[Interface], version: str) -> str:
        entries: dict[str, dict] = {
            "wattleflow.core import": {
                "scope": SNIPPET_SCOPE,
                "prefix": f"{cls.PREFIX}import",
                "body": ["from wattleflow.core import ${1:IWattleflow}"],
                "description": "Import a core interface (explicit submodule import "
                "across distributions — CLAUDE.md §2.7 t.4).",
            }
        }

        for item in sorted(interfaces, key=lambda i: i.name):
            entries[f"wattleflow.core: {item.name}"] = {
                "scope": SNIPPET_SCOPE,
                "prefix": f"{cls.PREFIX}{item.name}",
                "body": cls._body(item),
                "description": cls._description(item),
            }

        header = (
            f"// Generated by tools/core_index.py {version} — do not edit.\n"
            f"// Source of truth is the docstring in wattleflow.core (D-13).\n"
            f"// Regenerate: python tools/core_index.py --snippets <path>\n"
        )
        return header + json.dumps(entries, indent=2, ensure_ascii=False) + "\n"

    @staticmethod
    def _description(item: Interface) -> str:
        role = item.role or "(role not declared)"
        return f"{item.module} · {role} · inherits {item.inherits}"

    @classmethod
    def _body(cls, item: Interface) -> list[str]:
        # `removeprefix`, not `lstrip`: lstrip takes a character SET, so
        # `IIterator` would come back as `terator`.
        stem = item.name.removeprefix("I") or item.name
        body = [f"class ${{1:My{stem}}}({item.name}):"]
        if not item.methods:
            body.append("    ${0:pass}")
            return body

        for index, method in enumerate(item.methods, start=2):
            keyword = "async def" if method.is_async else "def"
            body.append(f"    {keyword} {method.signature}:")
            body.append(f"        ${{{index}:...}}")
        body.append("        $0")
        return body


class MarkdownOverview:
    """Renders the reading view: what exists, grouped by family."""

    @classmethod
    def render(cls, interfaces: list[Interface], version: str, package: Path) -> str:
        by_module: dict[str, list[Interface]] = {}
        for item in interfaces:
            by_module.setdefault(item.module, []).append(item)

        out: list[str] = [
            "# wattleflow.core — interface index",
            "",
            "> **Generated view, not a source of truth (D-13).** Produced by "
            f"`tools/core_index.py {version}` from the docstrings in "
            "`src/wattleflow/core/`. Do not edit by hand; regenerate.",
            "",
            f"Interfaces: {len(interfaces)}. Every name below is exported from `wattleflow.core`.",
            "",
            "## Contents",
            "",
        ]

        for module in cls._ordered(by_module):
            title = MODULE_TITLES.get(module, module)
            out.append(f"### {title} (`{module}`)")
            out.append("")
            out.append("| interface | role | inherits |")
            out.append("|---|---|---|")
            for item in sorted(by_module[module], key=lambda i: i.name):
                role = item.role or "**(role not declared)**"
                out.append(f"| [`{item.name}`](#{item.name.lower()}) | {role} | `{item.inherits}` |")
            out.append("")

        out.append("---")
        out.append("")

        for module in cls._ordered(by_module):
            out.append(f"## {MODULE_TITLES.get(module, module)}")
            out.append("")
            for item in sorted(by_module[module], key=lambda i: i.name):
                out.extend(cls._entry(item, package))
        return "\n".join(out).rstrip() + "\n"

    @staticmethod
    def _ordered(by_module: dict[str, list[Interface]]) -> list[str]:
        known = [m for m in MODULE_ORDER if m in by_module]
        return known + sorted(set(by_module) - set(known))

    @staticmethod
    def _entry(item: Interface, package: Path) -> list[str]:
        out = [f"### {item.name}", ""]
        out.append(f"`{item.qualified}` · `{item.module}.py:{item.lineno}`")
        out.append("")
        if item.role:
            out.append(f"**{item.role}.**")
            out.append("")
        if item.prose:
            out.append(item.prose)
            out.append("")
        if item.bases:
            out.append(f"Inherits: `{item.inherits}`")
            out.append("")
        if item.methods:
            out.append("```python")
            for method in item.methods:
                keyword = "async def" if method.is_async else "def"
                out.append(f"{keyword} {method.signature}: ...")
            out.append("```")
            out.append("")
        elif item.declared:
            # No abstract method of its own: the contract is inherited, and the
            # docstring block is the only statement of it.
            out.append("Contract (inherited, per docstring):")
            out.append("")
            out.append("```")
            out.extend(item.declared)
            out.append("```")
            out.append("")
        if item.findings:
            out.append(f"> **Finding:** {'; '.join(item.findings)}.")
            out.append("")
        return out


# --------------------------------------------------------------------------- #
# endregion Renderers                                                         #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Application                                                          #
# --------------------------------------------------------------------------- #


class Application:
    """Command line entry point."""

    DEFAULT_PACKAGE = Path("src/wattleflow/core")

    @classmethod
    def run(cls, argv: list[str] | None = None) -> int:
        args = cls._parse(argv)
        package = args.package.resolve()
        if not package.is_dir():
            print(f"core_index: no such package directory: {package}", file=sys.stderr)
            return 2

        interfaces = SourceReader.read(package)
        if not interfaces:
            print(f"core_index: no interfaces found in {package}", file=sys.stderr)
            return 2

        wrote = False
        for target in args.snippets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(SnippetCatalogue.render(interfaces, VERSION), encoding="utf-8")
            print(f"snippets  {len(interfaces)} interfaces -> {target}")
            wrote = True

        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(MarkdownOverview.render(interfaces, VERSION, package), encoding="utf-8")
            print(f"markdown  {len(interfaces)} interfaces -> {args.markdown}")
            wrote = True

        failed = cls._report(interfaces) if args.check else 0
        if not wrote and not args.check:
            cls._summary(interfaces)
        return 1 if failed else 0

    @staticmethod
    def _parse(argv: list[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog="core_index",
            description="Generate a browsable index of the wattleflow.core interfaces.",
        )
        parser.add_argument("--version", action="version", version=f"core_index {VERSION}")
        parser.add_argument(
            "--package",
            type=Path,
            default=Application.DEFAULT_PACKAGE,
            help="core package directory (default: %(default)s)",
        )
        parser.add_argument(
            "--snippets",
            type=Path,
            action="append",
            default=[],
            help="write a VS Code snippet catalogue here; repeatable, one per "
            "workspace folder (.vscode is gitignored, so this is a build output)",
        )
        parser.add_argument(
            "--markdown",
            type=Path,
            help="write the Markdown overview here",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="report interfaces that depart from the docstring convention; exit 1 if any do",
        )
        return parser.parse_args(argv)

    @staticmethod
    def _summary(interfaces: list[Interface]) -> None:
        by_module: dict[str, int] = {}
        for item in interfaces:
            by_module[item.module] = by_module.get(item.module, 0) + 1
        print(f"core_index {VERSION}: {len(interfaces)} interfaces")
        for module in sorted(by_module):
            print(f"  {module:<16} {by_module[module]}")
        print("nothing written — pass --snippets and/or --markdown")

    @staticmethod
    def _report(interfaces: list[Interface]) -> int:
        offenders = [i for i in interfaces if i.findings]
        for item in sorted(offenders, key=lambda i: (i.module, i.name)):
            location = f"{item.module}.py:{item.lineno}"
            print(f"{location:<24} {item.name:<24} {'; '.join(item.findings)}")
        print(f"\nconvention: {len(interfaces) - len(offenders)}/{len(interfaces)} conform, {len(offenders)} depart")
        return len(offenders)


# --------------------------------------------------------------------------- #
# endregion Application                                                       #
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    raise SystemExit(Application.run())
