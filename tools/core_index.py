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
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Constants                                                            #
# --------------------------------------------------------------------------- #

VERSION = "1.1.0"

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
    # `signature` reads as Python; UML wants the same facts taken apart, and
    # the binding (property / static / class) that Python spells as a decorator.
    args: str = ""
    returns: str = ""
    binding: str = "instance"

    # Decorator -> UML binding: Python spells as a decorator what UML spells
    # as a stereotype or a modifier.
    BINDINGS: ClassVar[dict[str, str]] = {
        "property": "property",
        "staticmethod": "static",
        "classmethod": "class",
    }


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
    """Reads interfaces out of the core package by AST, never by import."""

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
            returns = ast.unparse(child.returns) if child.returns else ""
            arrow = f" -> {returns}" if returns else ""
            methods.append(
                Method(
                    name=child.name,
                    signature=f"{child.name}({args}){arrow}",
                    is_async=isinstance(child, ast.AsyncFunctionDef),
                    args=args,
                    returns=returns,
                    binding=Method.BINDINGS.get(
                        next((d for d in Method.BINDINGS if d in decorators), ""),
                        "instance",
                    ),
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


class DiagramCatalogue:
    """Renders one PlantUML class diagram per interface.

    A diagram is a view with a declared viewpoint, never a source of truth
    (D-13, ISO/IEC/IEEE 42010). The viewpoint here is deliberately narrow: one
    interface as subject, the inheritance path that reaches it, and the core
    interfaces that derive from it directly. A whole-package diagram would be
    86 boxes and would say nothing an index does not already say.

    Type parameters are read where they are declared: a core interface shows
    the parameters of its own `Generic[...]` base inside the box, while a
    subscripted base (`IComponent[Element]`) puts the binding on the edge. An
    external base has no declaration to read here, so its subscript stays in
    the box.
    """

    SUFFIX = ".puml"
    SUBJECT_FILL = "#FFF3C4"
    # Above this many direct descendants the fan stops being a diagram and
    # becomes a list drawn badly: the root has 79. Past the cap the count is
    # stated instead of drawn — an omission declared, not hidden (D-11).
    MAX_CHILDREN = 10

    @classmethod
    def render(cls, item: Interface, index: dict[str, Interface], version: str) -> str:
        ancestors = cls._ancestors(item, index)
        family = [*reversed(ancestors), item]
        out: list[str] = [
            "@startuml",
            f"' Generated by tools/core_index.py {version} — do not edit; regenerate.",
            "' Source of truth is the source of wattleflow.core, not this file (D-13).",
            "' Viewpoint: one interface, its inheritance path and its direct core",
            "' descendants. Audience: architect, implementer.",
            "",
            "skinparam backgroundColor #FFFFFF",
            "skinparam shadowing false",
            "skinparam classAttributeIconSize 0",
            "hide empty members",
            "",
            cls._title(item),
            "",
        ]

        for name in cls._externals(family, index):
            out.append(cls._external_box(name))
        if len(out) and out[-1].startswith(("abstract class", "class")):
            out.append("")

        for member in family:
            out.extend(cls._box(member, subject=member is item))
            out.append("")

        children = cls._children(item, index)
        drawn = children if len(children) <= cls.MAX_CHILDREN else []
        for child in drawn:
            out.append(f"interface {cls._alias(child.name)} <<{child.module}>>")
        if drawn:
            out.append("")

        out.extend(cls._edges(item, family, drawn, index))
        out.append("")
        out.extend(cls._notes(item))
        if len(children) > cls.MAX_CHILDREN:
            out.extend(cls._descendant_note(item, children))
        out.append(cls._legend(children, drawn))
        out.append("@enduml")
        return "\n".join(line for line in out if line is not None).rstrip() + "\n"

    # -- structure ---------------------------------------------------------- #

    @classmethod
    def _ancestors(
        cls, item: Interface, index: dict[str, Interface]
    ) -> list[Interface]:
        """Core interfaces reached by following bases upwards, nearest first."""
        seen: list[Interface] = []
        queue = [b for b in cls._core_bases(item, index)]
        while queue:
            name = queue.pop(0)
            parent = index[name]
            if parent in seen:
                continue
            seen.append(parent)
            queue.extend(cls._core_bases(parent, index))
        return seen

    @classmethod
    def _children(cls, item: Interface, index: dict[str, Interface]) -> list[Interface]:
        """Direct core descendants only — the transitive set is the index's job."""
        return sorted(
            (i for i in index.values() if item.name in cls._core_bases(i, index)),
            key=lambda i: i.name,
        )

    @staticmethod
    def _core_bases(item: Interface, index: dict[str, Interface]) -> list[str]:
        heads = [b.split("[", 1)[0].strip() for b in item.bases]
        return [h for h in heads if h in index]

    @classmethod
    def _externals(
        cls, family: list[Interface], index: dict[str, Interface]
    ) -> list[str]:
        """Bases that are not core interfaces (ABC, typing generics), deduplicated."""
        found: list[str] = []
        for member in family:
            for base in member.bases:
                if base.split("[", 1)[0].strip() in index:
                    continue
                if base not in found:
                    found.append(base)
        return found

    # -- boxes -------------------------------------------------------------- #

    @classmethod
    def _box(cls, item: Interface, subject: bool) -> list[str]:
        head = f"interface {cls._declaration(item)} <<{item.module}>>"
        if subject:
            head += f" {cls.SUBJECT_FILL}"
        if not item.methods:
            return [head]
        return [head + " {", *[f"  {cls._member(m)}" for m in item.methods], "}"]

    @classmethod
    def _external_box(cls, base: str) -> str:
        alias = cls._alias(base)
        keyword = "abstract class" if base == "ABC" else "class"
        display = cls._display(base)
        if display == alias:
            return f"{keyword} {alias} <<external>>"
        return f'{keyword} "{display}" as {alias} <<external>>'

    @classmethod
    def _declaration(cls, item: Interface) -> str:
        params = cls._parameters(item)
        if not params:
            return item.name
        return f'"{item.name}<{params}>" as {item.name}'

    @staticmethod
    def _parameters(item: Interface) -> str:
        """The type parameters an interface declares, verbatim from `Generic[...]`."""
        for base in item.bases:
            if base.split("[", 1)[0].strip() == "Generic":
                return base[base.index("[") + 1 : -1]
        return ""

    @classmethod
    def _member(cls, method: Method) -> str:
        args = cls._arguments(method)
        returns = f" : {method.returns}" if method.returns else ""
        modifier = "{static} " if method.binding in ("static", "class") else ""
        stereotype = " <<property>>" if method.binding == "property" else ""
        if method.is_async:
            stereotype += " <<async>>"
        return f"+{modifier}{method.name}({args}){returns}{stereotype}"

    @staticmethod
    def _arguments(method: Method) -> str:
        """Drop the receiver: UML shows parameters, not the binding mechanism.

        Splitting on the first comma is enough — a receiver is a bare name, so
        it can never be the argument that carries a bracketed comma.
        """
        head, _, tail = method.args.partition(",")
        if head.split(":", 1)[0].strip() in ("self", "cls"):
            return tail.strip()
        return method.args

    # -- edges and prose ---------------------------------------------------- #

    @classmethod
    def _edges(
        cls,
        item: Interface,
        family: list[Interface],
        children: list[Interface],
        index: dict[str, Interface],
    ) -> list[str]:
        out: list[str] = []
        # Every interface re-declares `ABC` even though it already inherits it.
        # Inheritance is transitive, so the edge is drawn where it first enters
        # the family and suppressed below: repeating it is a fact about the
        # source, not about the architecture this view takes as its subject.
        seen_external: set[str] = set()
        for member in family:
            for base in member.bases:
                external = base.split("[", 1)[0].strip() not in index
                if external and base in seen_external:
                    continue
                if external:
                    seen_external.add(base)
                out.append(
                    f"{cls._ref(base, index)} <|-- {cls._alias(member.name)}{cls._binding_label(base, index)}"
                )
        for child in children:
            base = next(
                b for b in child.bases if b.split("[", 1)[0].strip() == item.name
            )
            out.append(
                f"{cls._alias(item.name)} <|-- {cls._alias(child.name)}{cls._binding_label(base, index)}"
            )
        return out

    @classmethod
    def _ref(cls, base: str, index: dict[str, Interface]) -> str:
        """The box a base points at: a core interface owns one box, subscript or not."""
        head = base.split("[", 1)[0].strip()
        return head if head in index else cls._alias(base)

    @staticmethod
    def _binding_label(base: str, index: dict[str, Interface]) -> str:
        head = base.split("[", 1)[0].strip()
        if head not in index or "[" not in base:
            return ""
        return f" : <{base[base.index('[') + 1 : -1]}>"

    @classmethod
    def _notes(cls, item: Interface) -> list[str]:
        out: list[str] = []
        if not item.methods and item.declared:
            # No abstract method of its own: the docstring block is the only
            # statement of the contract, so the box would otherwise be empty.
            out.append(f"note bottom of {cls._alias(item.name)}")
            out.append("  Contract (inherited, per docstring):")
            out.extend(f"  {line}" for line in item.declared)
            out.append("end note")
            out.append("")
        if item.findings:
            out.append(f"note right of {cls._alias(item.name)}")
            out.append(f"  Finding: {'; '.join(item.findings)}.")
            out.append("end note")
            out.append("")
        return out

    @classmethod
    def _descendant_note(cls, item: Interface, children: list[Interface]) -> list[str]:
        """State a fan too wide to draw, per family, rather than drawing it."""
        counts: dict[str, int] = {}
        for child in children:
            counts[child.module] = counts.get(child.module, 0) + 1
        out = [f"note bottom of {cls._alias(item.name)}"]
        out.append(f"  {len(children)} direct core descendants, not drawn:")
        for module in sorted(counts):
            out.append(f"  {counts[module]} in {module}")
        out.append("  See the index for the names.")
        out.append("end note")
        out.append("")
        return out

    @staticmethod
    def _legend(children: list[Interface], drawn: list[Interface]) -> str:
        if not children:
            tail = "no core interface derives from this one."
        elif drawn:
            tail = "descendants are names only — each has its own diagram."
        else:
            tail = "the descendant fan is counted in the note, not drawn."
        return (
            "legend right\n"
            "  Subject is highlighted. Ancestors carry their own abstract members,\n"
            f"  so the box stack is the whole contract; {tail}\n"
            "endlegend"
        )

    @staticmethod
    def _title(item: Interface) -> str:
        role = item.role or "(role not declared)"
        return f"title {item.name} — {role}"

    @staticmethod
    def _alias(name: str) -> str:
        """A PlantUML identifier: brackets and dots are not allowed in one."""
        head = name.split("[", 1)[0].strip()
        return (
            "".join(c if c.isalnum() or c == "_" else "_" for c in name)
            if head != name
            else name
        )

    @staticmethod
    def _display(base: str) -> str:
        return base.replace("[", "<").replace("]", ">")


class MarkdownOverview:
    """Renders the reading view: what exists, grouped by family."""

    # PlantUML writes PNG; the raster carried beside the docs is JPEG, produced
    # by the render step documented in tools/README. The tool names the file it
    # expects, it does not rasterise (core tools stay stdlib-only).
    IMAGE_SUFFIX = ".jpg"

    @classmethod
    def render(
        cls,
        interfaces: list[Interface],
        version: str,
        package: Path,
        diagrams: str | None = None,
    ) -> str:
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
                out.append(
                    f"| [`{item.name}`](#{item.name.lower()}) | {role} | `{item.inherits}` |"
                )
            out.append("")

        out.append("---")
        out.append("")

        for module in cls._ordered(by_module):
            out.append(f"## {MODULE_TITLES.get(module, module)}")
            out.append("")
            for item in sorted(by_module[module], key=lambda i: i.name):
                out.extend(cls._entry(item, package, diagrams))
        return "\n".join(out).rstrip() + "\n"

    @staticmethod
    def _ordered(by_module: dict[str, list[Interface]]) -> list[str]:
        known = [m for m in MODULE_ORDER if m in by_module]
        return known + sorted(set(by_module) - set(known))

    @staticmethod
    def _entry(
        item: Interface, package: Path, diagrams: str | None = None
    ) -> list[str]:
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
        if diagrams:
            stem = f"{diagrams}/{item.name}"
            out.append(
                f"![{item.name} class diagram]({stem}{MarkdownOverview.IMAGE_SUFFIX})"
            )
            out.append("")
            out.append(
                f"<sub>Class diagram — [source]({stem}{DiagramCatalogue.SUFFIX}). "
                "A view, not a source of truth (D-13).</sub>"
            )
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
            target.write_text(
                SnippetCatalogue.render(interfaces, VERSION), encoding="utf-8"
            )
            print(f"snippets  {len(interfaces)} interfaces -> {target}")
            wrote = True

        if args.uml:
            written, stale = cls._diagrams(interfaces, args.uml)
            print(f"uml       {written} diagrams -> {args.uml}")
            for name in stale:
                print(f"uml       removed stale {name}")
            wrote = True

        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(
                MarkdownOverview.render(interfaces, VERSION, package, cls._href(args)),
                encoding="utf-8",
            )
            print(f"markdown  {len(interfaces)} interfaces -> {args.markdown}")
            wrote = True

        failed = cls._report(interfaces) if args.check else 0
        if not wrote and not args.check:
            cls._summary(interfaces)
        return 1 if failed else 0

    @staticmethod
    def _diagrams(
        interfaces: list[Interface], directory: Path
    ) -> tuple[int, list[str]]:
        """Write one .puml per interface and drop the ones no interface claims.

        The tool owns `*.puml` in this directory: a diagram left behind by a
        removed interface would read as a current view of something that no
        longer exists. Rasters are not touched — the tool does not make them.
        """
        directory.mkdir(parents=True, exist_ok=True)
        index = {i.name: i for i in interfaces}
        for item in interfaces:
            target = directory / f"{item.name}{DiagramCatalogue.SUFFIX}"
            target.write_text(
                DiagramCatalogue.render(item, index, VERSION), encoding="utf-8"
            )

        stale = []
        for path in sorted(directory.glob(f"*{DiagramCatalogue.SUFFIX}")):
            if path.stem not in index:
                path.unlink()
                stale.append(path.name)
        return len(interfaces), stale

    @staticmethod
    def _href(args: argparse.Namespace) -> str | None:
        """Where the Markdown reaches the diagrams from, relative to itself."""
        if not (args.uml and args.markdown):
            return None
        return os.path.relpath(
            args.uml.resolve(), args.markdown.resolve().parent
        ).replace(os.sep, "/")

    @staticmethod
    def _parse(argv: list[str] | None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            prog="core_index",
            description="Generate a browsable index of the wattleflow.core interfaces.",
        )
        parser.add_argument(
            "--version", action="version", version=f"core_index {VERSION}"
        )
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
            "--uml",
            type=Path,
            help="write one PlantUML class diagram per interface into this "
            "directory; with --markdown the overview links the rendered image",
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
        print(
            f"\nconvention: {len(interfaces) - len(offenders)}/{len(interfaces)} conform, {len(offenders)} depart"
        )
        return len(offenders)


# --------------------------------------------------------------------------- #
# endregion Application                                                       #
# --------------------------------------------------------------------------- #


if __name__ == "__main__":
    raise SystemExit(Application.run())
