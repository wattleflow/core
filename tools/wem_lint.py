#!/usr/bin/env python3
# Module name: tools/wem_lint.py  (wattleflow-core edition)
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence
# Version: 0.5.1
"""
wem_lint — conformance lint for the wattleflow-core interface layer,
built WITH the framework it checks (self-reference, NFR analysis task 9).

Changelog
---------
0.5.1 (2026-07-29)
    No rule semantics: wattleflow-core carries configuration in JSON only,
    so the retired tools/dictionary.yaml symlink is gone from the
    distribution and the dictionary default moved to tools/dictionary.json
    — anchored to the tool's own directory, so the criterion travels with
    the tool that reads it and is the copy git actually tracks
    (documentation/ is ignored in this repository).
0.5.0 (2026-07-28)
    The criterion moved out of the tool and into the repository:
    documentation/dictionary.json, converted from the NFR-ORG-03 block of
    the retired tools/naming_registry.yaml. JSON, not YAML — the tool is
    stdlib-only and json is the only structured format the standard
    library parses; the .yaml path the option carried was never readable.
    The default is anchored to the repo root, not the cwd, so the same
    criterion applies wherever the lint is invoked from, and
    underscore-prefixed keys carry the prose JSON cannot.
    New rule R-CORE-CFG-01 (WARNING): a dictionary key no rule consumes is
    a criterion stated but not measured, and is reported — it currently
    fires for typevar_synonyms and typevar_tolerated, both carried
    over from the YAML and both awaiting a TypeVarRule that reads them.
    Rule set changed => minor version per the criterion-versioning
    convention.
0.4.2 (2026-07-28)
    Reporting change only, no rule semantics: a clean run was reported by
    the absence of findings alone ('(no findings)' inside the vector),
    which is indistinguishable from a run that never executed. The report
    now closes with a RESULT verdict — OK / FAIL, per-severity counts and
    the scope actually checked (module count, dictionary version) — so a
    passing run says so explicitly. New --quiet/-q suppresses the report
    on an error-free run for CI use; errors are printed regardless, so
    silence can never hide a violation.
0.4.1 (2026-07-24)
    Criterion content change, no rule-semantics change: python_reference
    pinned 3.12 -> 3.10 (dictionary_version 0.1.0 -> 0.2.0). Decision: the
    core targets the lowest interpreter providing sys.stdlib_module_names
    (exact IMP classification); typing.Self was dropped from creational
    (clone() -> "IPrototype") so no typing_extensions runtime dependency
    and no conditional-import guard is needed — the planned SFX-01
    compat-guard exception is therefore withdrawn before release.
0.4.0 (2026-07-24)
    Instrument-validity fix, found because ABS stayed silent on a run that
    should have flagged ISingleton: once the root IWattleflow gained an
    abstract name property (DR-COR-001), every subclass not implementing it
    became nominally abstract, so inspect.isabstract lost discriminative
    power for ORG-02d — the proxy diverged from the construct, with no
    change to the tool. New rule R-CORE-ABS-03: an I-prefixed class whose
    only abstract members are inherited from the root, and which defines
    concrete machinery of its own, is concrete in spirit (ERROR). Rule
    semantics changed => minor version per the criterion-versioning
    convention.
0.3.0 (2026-07-24)
    First field run (Python 3.9 environment, mid-transition core) exposed
    two tool defects and one gap; all three fixed:
    * IMP: vendored _STDLIB_FALLBACK for interpreters < 3.10, where
      sys.stdlib_module_names does not exist — without it every stdlib
      import was misclassified as IMP-02 "outside stdlib"; an environment
      WARNING declares the fallback classification as approximate.
    * HDR: header detection is case-insensitive with precise messages —
      '# Module Name:' now reports "nonstandard header casing" instead of
      the misleading "missing".
    * EXC: new exclude_modules dictionary key (default: _version.py) for
      infrastructure files inside the package; every exclusion is emitted
      as R-CORE-EXC-01 INFO so blind spots are declared, never silent.
0.2.0 (2026-07-24)
    Rewritten to consume the framework it checks (dogfooding): the run is
    an ITemplate, each rule an IStrategy, the report an IBuilder, identity
    via a local IWattleflow implementation (the canonical one lives in the
    workflow distribution, which core tools must not import). The tool is
    thereby consumer #2 of the core catalogue.
0.1.0 (2026-07-24)
    Initial procedural version: rules R-CORE-IMP/SFX/ABS/STA/TYP/FAC/HDR
    derived from the DR series; stdlib-only, single file, JSON dictionary
    override, vector output with no aggregate score.

Pattern mapping (dogfooding):
    lint run          -> ITemplate   (initialise / perform_task / finalise;
                                      finalise always renders the report)
    each rule         -> IStrategy   (execute(caller, **kwargs); rules are
                                      interchangeable and dictionary-driven)
    report rendering  -> IBuilder    (build() -> str, vector output)
    identity          -> IWattleflow (name property implemented locally —
                                      the canonical implementation lives in
                                      wattleflow.concrete.wattleflow, which
                                      this tool must NOT import: core tools
                                      never depend on the workflow
                                      distribution)

The tool is therefore consumer #2 of the core catalogue (after the
workflow distribution): it consumes framework, behavioural and creational
contracts. This changes the offered/consumed measurement and is
deliberate.

Rules (mapped to the DR series):
  R-CORE-IMP-01  interface modules import only the allowlist:
                 __future__, abc, typing, typing_extensions, datetime,
                 collections.abc + package-relative.          [DR-COR-003/005]
  R-CORE-IMP-02  absolute imports resolve within pinned stdlib or the
                 allowed third-party set.                     [DR-ORG-01]
  R-CORE-SFX-01  no module-level side effects.                [DR-COR-005]
  R-CORE-ABS-01  I<Upper>-named class must be abstract.       [DR-ORG-02d]
  R-CORE-ABS-02  abstract class should carry the I prefix (warning).
  R-CORE-STA-01  no __init__ in interface classes.            [DR-COR-001]
  R-CORE-STA-02  __slots__, if declared, is empty.            [DR-COR-002]
  R-CORE-STA-03  concrete methods in I-classes reported as INFO — the
                 defining-algorithm exception is not machine-decidable.
  R-CORE-TYP-01  no mechanism TypeVar names (T, W, WattleType, 1–2 chars).
  R-CORE-TYP-02  TypeVar names should be in the role vocabulary (warning).
  R-CORE-TYP-03  TypeVar("X") string equals the bound name.
  R-CORE-FAC-01  __init__.py: __all__ equals the imported-name set.
  R-CORE-FAC-02  __init__.py re-exports no TypeVars (roles are
                 module-scoped).
  R-CORE-HDR-01  "# Module name:" header matches the file name.
  R-CORE-CFG-01  dictionary key declared but read by no rule (warning).
  R-CORE-EXC-01  module excluded by the dictionary (info, declared blind
                 spot).

Output is a VECTOR grouped per dimension with per-rule counts and
deliberately no aggregate score (NFR §3.4: nominal-scale conformance
results admit counting, not weighted sums), closed by a RESULT verdict
line stating the outcome in words (OK / FAIL) and the scope checked.
--quiet suppresses that output on an error-free run. Exit: 0 clean,
1 errors, 2 usage/environment failure.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# --------------------------------------------------------------------------- #
# region Bootstrap                                                            #
# --------------------------------------------------------------------------- #
# The tool lives in <repo>/tools/ and consumes <repo>/src/wattleflow/core.
# Make the src layout importable before the framework imports below. This is
# a module-level side effect — legal here: tools are a consumer layer, not
# the interface layer; the R-CORE-SFX-01 discipline binds core/, not tools/.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPO_SRC = _REPO_ROOT / "src"
if _REPO_SRC.is_dir() and str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))

# The criterion dictionary ships next to the tool that reads it, and is
# anchored to that location rather than the cwd: the lint must measure against
# the same criterion wherever it is invoked from. JSON, not YAML —
# wattleflow-core carries configuration in JSON only, the tools being
# stdlib-only and json the sole structured format the standard library parses.
_DEFAULT_DICTIONARY = Path(__file__).resolve().parent / "dictionary.json"

from wattleflow.core.behavioural import IStrategy, ITemplate  # noqa: E402
from wattleflow.core.creational import IBuilder  # noqa: E402
from wattleflow.core.framework import IWattleflow  # noqa: E402

# --------------------------------------------------------------------------- #
# endregion Bootstrap                                                         #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"
__version__ = "0.5.1"

# --------------------------------------------------------------------------- #
# region Identity                                                             #
# --------------------------------------------------------------------------- #


class WemComponent(IWattleflow):
    """
    Local identity implementation of the IWattleflow contract.

    Mirrors the canonical wattleflow.concrete.wattleflow.Wattleflow (name
    derived from the concrete type, immutable) without importing it: the
    core repository's tools must not depend on the workflow distribution —
    the dependency direction core <- workflow is inviolable, including for
    tooling convenience.
    """

    __slots__ = ()

    @property
    def name(self) -> str:
        return type(self).__name__

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


# --------------------------------------------------------------------------- #
# endregion Identity                                                          #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Configuration                                                        #
# --------------------------------------------------------------------------- #

DEFAULT_CONFIG: Dict[str, Any] = {
    "dictionary_version": "0.2.0",
    "python_reference": "3.10",
    "allowed_imports": [
        "__future__",
        "abc",
        "typing",
        "typing_extensions",
        "datetime",
        "collections.abc",
    ],
    "allowed_third_party": ["typing_extensions"],
    "typevar_roles": [
        "Action",
        "Adaptee",
        "Connection",
        "Content",
        "Context",
        "Destination",
        "Edge",
        "Element",
        "Entity",
        "Event",
        "Extrinsic",
        "Input",
        "Item",
        "Key",
        "Message",
        "Output",
        "Result",
        "State",
        "Value",
        "Vertex",
    ],
    "typevar_forbidden": ["T", "W", "WattleType"],
    "allowed_dunders": [
        "__author__",
        "__copyright__",
        "__license__",
        "__version__",
        "__all__",
    ],
    # Modules in the package directory that are infrastructure, not
    # interface modules (e.g. a setuptools-scm _version.py). Every entry is
    # a DECLARED blind spot: the tool reports the exclusion as INFO so the
    # vector never hides silently.
    "exclude_modules": ["_version.py"],
}

SEVERITIES = ("ERROR", "WARNING", "INFO")

# Vendored fallback for interpreters older than 3.10, where
# sys.stdlib_module_names does not exist. Without it every stdlib import
# would be misclassified as IMP-02 "outside stdlib" (observed on 3.9).
# Deliberately conservative: the mechanism modules the rules care about
# plus common stdlib names; an unknown-but-stdlib name degrades to IMP-02,
# which the accompanying environment WARNING declares as approximate.
_STDLIB_FALLBACK = frozenset(
    {
        "abc",
        "argparse",
        "array",
        "ast",
        "asyncio",
        "atexit",
        "base64",
        "bisect",
        "builtins",
        "collections",
        "concurrent",
        "contextlib",
        "contextvars",
        "copy",
        "csv",
        "ctypes",
        "dataclasses",
        "datetime",
        "decimal",
        "difflib",
        "dis",
        "enum",
        "errno",
        "fnmatch",
        "functools",
        "gc",
        "getpass",
        "glob",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "importlib",
        "inspect",
        "io",
        "itertools",
        "json",
        "logging",
        "math",
        "multiprocessing",
        "operator",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "queue",
        "random",
        "re",
        "secrets",
        "select",
        "shutil",
        "signal",
        "socket",
        "sqlite3",
        "ssl",
        "stat",
        "string",
        "struct",
        "subprocess",
        "sys",
        "sysconfig",
        "tempfile",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tokenize",
        "traceback",
        "types",
        "typing",
        "unittest",
        "urllib",
        "uuid",
        "warnings",
        "weakref",
        "xml",
        "zipfile",
        "zlib",
    }
)

# --------------------------------------------------------------------------- #
# endregion Configuration                                                     #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Findings and report builder                                          #
# --------------------------------------------------------------------------- #

Finding = Tuple[str, str, str, int, str]  # rule, severity, module, line, msg


class FindingLog(WemComponent):
    """Accumulates findings; consumed by ReportBuilder."""

    def __init__(self) -> None:
        self.findings: List[Finding] = []

    def add(self, rule: str, severity: str, module: str, line: int, message: str) -> None:
        self.findings.append((rule, severity, module, line, message))

    @property
    def has_errors(self) -> bool:
        return any(sev == "ERROR" for _, sev, _, _, _ in self.findings)


class ReportBuilder(WemComponent, IBuilder):
    """
    IBuilder producing the vector report.

    build() renders findings grouped per dimension plus a per-(rule,
    severity) count vector. No aggregate score is built — deliberately.
    """

    def __init__(self, log: FindingLog, modules: int = 0, dictionary_version: str = "?") -> None:
        self._log = log
        self._modules = modules
        self._dictionary_version = dictionary_version

    @staticmethod
    def _dimension(rule: str) -> str:
        parts = rule.split("-")
        return parts[2] if len(parts) >= 3 else rule

    def build(self) -> str:
        out: List[str] = []
        by_dim: Dict[str, List[Finding]] = {}
        for f in self._log.findings:
            by_dim.setdefault(self._dimension(f[0]), []).append(f)

        for dim in sorted(by_dim):
            out.append(f"\n== {dim} " + "=" * (74 - len(dim)))
            for rule, sev, module, line, msg in sorted(by_dim[dim], key=lambda x: (x[2], x[3], x[0])):
                loc = f"{module}:{line}" if line else module
                out.append(f"  [{sev:<7}] {rule:<14} {loc}: {msg}")

        out.append("\n== VECTOR " + "=" * 68)
        counts: Dict[Tuple[str, str], int] = {}
        for rule, sev, _, _, _ in self._log.findings:
            counts[(rule, sev)] = counts.get((rule, sev), 0) + 1
        if not counts:
            out.append("  (no findings)")
        for rule, sev in sorted(counts):
            out.append(f"  {rule:<14} {sev:<7} {counts[(rule, sev)]}")
        out.append("  note: conformance vector — no aggregate score is defined for these checks (NFR §3.4).")

        # A silent clean run is indistinguishable from a run that never
        # executed; the verdict line states the outcome explicitly. It is a
        # statement about the vector, not a score derived from it.
        by_sev: Dict[str, int] = {sev: 0 for sev in SEVERITIES}
        for _, sev, _, _, _ in self._log.findings:
            by_sev[sev] = by_sev.get(sev, 0) + 1
        errors, warnings, infos = by_sev["ERROR"], by_sev["WARNING"], by_sev["INFO"]
        scope = f"{self._modules} module(s) checked, dictionary {self._dictionary_version}"
        if errors:
            verdict = f"FAIL — {errors} error(s), {warnings} warning(s), {infos} info ({scope})"
        elif warnings or infos:
            verdict = f"OK — no errors; {warnings} warning(s), {infos} info to review ({scope})"
        else:
            verdict = f"OK — every rule held, no findings ({scope})"
        out.append("\n== RESULT " + "=" * 68)
        out.append(f"  {verdict}")
        return "\n".join(out)


# --------------------------------------------------------------------------- #
# endregion Findings and report builder                                       #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region AST helpers and module scan                                          #
# --------------------------------------------------------------------------- #


def _is_typevar_assign(node: ast.stmt) -> Optional[Tuple[str, Optional[str], int]]:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return None
    target = node.targets[0]
    if not isinstance(target, ast.Name):
        return None
    value = node.value
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    fname = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else None)
    if fname != "TypeVar":
        return None
    first: Optional[str] = None
    if value.args and isinstance(value.args[0], ast.Constant) and isinstance(value.args[0].value, str):
        first = value.args[0].value
    return (target.id, first, node.lineno)


def _decorator_names(fn) -> Set[str]:
    names: Set[str] = set()
    for dec in fn.decorator_list:
        if isinstance(dec, ast.Name):
            names.add(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.add(dec.attr)
    return names


def _is_interface_name(name: str) -> bool:
    return len(name) >= 2 and name[0] == "I" and name[1].isupper()


class ModuleScan(WemComponent):
    """Parsed view of one core module (AST + collected facts)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.relname = path.name
        self.typevars: Dict[str, int] = {}
        self.imported_names: Dict[str, int] = {}
        self.tree: Optional[ast.Module] = None
        self.source: str = ""
        self.parse_error: Optional[str] = None

    @property
    def modname(self) -> str:
        return self.path.stem

    def parse(self) -> None:
        try:
            self.source = self.path.read_text(encoding="utf-8")
            self.tree = ast.parse(self.source, filename=str(self.path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            self.parse_error = str(exc)


# --------------------------------------------------------------------------- #
# endregion AST helpers and module scan                                       #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Rules (IStrategy implementations)                                    #
# --------------------------------------------------------------------------- #


class LintRule(WemComponent, IStrategy):
    """
    Base lint rule. Concrete rules implement execute(caller, **kwargs);
    caller is the CoreLintRun template, kwargs carry the shared context
    (scans, cfg, log, stdlib_names, pkg_dir).
    """


class HeaderRule(LintRule):
    def execute(self, caller: IWattleflow, **kwargs) -> Any:
        log: FindingLog = kwargs["log"]
        for scan in kwargs["scans"]:
            if scan.parse_error:
                continue
            first = scan.source.splitlines()[0] if scan.source else ""
            lowered = first.lower()
            if lowered.startswith("# module name:"):
                declared = first.split(":", 1)[1].strip()
                if not declared.endswith(scan.relname):
                    log.add(
                        "R-CORE-HDR-01",
                        "WARNING",
                        scan.relname,
                        1,
                        f"header declares {declared!r}, file is {scan.relname!r}",
                    )
                if not first.startswith("# Module name:"):
                    log.add(
                        "R-CORE-HDR-01",
                        "WARNING",
                        scan.relname,
                        1,
                        f"nonstandard header casing {first!r} — canonical form is '# Module name:'",
                    )
            else:
                log.add("R-CORE-HDR-01", "WARNING", scan.relname, 1, "missing '# Module name:' header")


class SideEffectRule(LintRule):
    def execute(self, caller: IWattleflow, **kwargs) -> Any:
        log: FindingLog = kwargs["log"]
        allowed_dunders = set(kwargs["cfg"]["allowed_dunders"])
        for scan in kwargs["scans"]:
            if scan.parse_error:
                log.add("R-CORE-SFX-01", "ERROR", scan.relname, 0, f"module does not parse: {scan.parse_error}")
                continue
            body = list(scan.tree.body)
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body = body[1:]
            for node in body:
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef)):
                    continue
                tv = _is_typevar_assign(node)
                if tv is not None:
                    scan.typevars[tv[0]] = tv[2]
                    continue
                if (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in allowed_dunders
                ):
                    continue
                if (
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and node.target.id in allowed_dunders
                ):
                    continue
                log.add(
                    "R-CORE-SFX-01",
                    "ERROR",
                    scan.relname,
                    node.lineno,
                    f"module-level {type(node).__name__} is a side "
                    f"effect in the interface layer (allowed: "
                    f"docstring, imports, dunders, TypeVar "
                    f"declarations, classes)",
                )


class ImportRule(LintRule):
    def execute(self, caller: IWattleflow, **kwargs) -> Any:
        log: FindingLog = kwargs["log"]
        cfg = kwargs["cfg"]
        stdlib_names: Set[str] = kwargs["stdlib_names"]
        allowed = set(cfg["allowed_imports"])
        third_party = set(cfg["allowed_third_party"])

        for scan in kwargs["scans"]:
            if scan.parse_error:
                continue
            for node in ast.walk(scan.tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level and node.level > 0:
                        for alias in node.names:
                            scan.imported_names[alias.asname or alias.name] = node.lineno
                        continue
                    self._classify(node.module or "", node.lineno, scan, allowed, third_party, stdlib_names, log)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self._classify(alias.name, node.lineno, scan, allowed, third_party, stdlib_names, log)

    @staticmethod
    def _classify(
        mod: str,
        line: int,
        scan: ModuleScan,
        allowed: Set[str],
        third_party: Set[str],
        stdlib_names: Set[str],
        log: FindingLog,
    ) -> None:
        if not mod:
            return
        top = mod.split(".")[0]
        if mod in allowed or top in allowed:
            return
        if top in third_party:
            log.add(
                "R-CORE-IMP-01",
                "ERROR",
                scan.relname,
                line,
                f"import {mod!r}: third-party allowed by ORG-01 but not in the interface-layer allowlist",
            )
        elif top in stdlib_names:
            log.add(
                "R-CORE-IMP-01",
                "ERROR",
                scan.relname,
                line,
                f"import {mod!r}: stdlib runtime mechanism — the interface layer declares contracts only",
            )
        else:
            log.add(
                "R-CORE-IMP-02",
                "ERROR",
                scan.relname,
                line,
                f"import {mod!r}: outside stdlib ∪ allowed third-party (clean-core violation)",
            )


class TypeVarRule(LintRule):
    def execute(self, caller: IWattleflow, **kwargs) -> Any:
        log: FindingLog = kwargs["log"]
        cfg = kwargs["cfg"]
        roles = set(cfg["typevar_roles"])
        forbidden = set(cfg["typevar_forbidden"])
        for scan in kwargs["scans"]:
            if scan.parse_error:
                continue
            for name, line in scan.typevars.items():
                if name in forbidden or len(name) <= 2:
                    log.add(
                        "R-CORE-TYP-01",
                        "ERROR",
                        scan.relname,
                        line,
                        f"TypeVar {name!r} names a mechanism, not a role (ORG-03)",
                    )
                elif name not in roles:
                    log.add(
                        "R-CORE-TYP-02",
                        "WARNING",
                        scan.relname,
                        line,
                        f"TypeVar {name!r} not in the role vocabulary — extend the dictionary via DR or rename",
                    )
            for node in scan.tree.body:
                tv = _is_typevar_assign(node)
                if tv and tv[1] is not None and tv[1] != tv[0]:
                    log.add(
                        "R-CORE-TYP-03",
                        "ERROR",
                        scan.relname,
                        tv[2],
                        f"declared as {tv[0]} = TypeVar({tv[1]!r}) — names must match",
                    )


class ClassStateRule(LintRule):
    def execute(self, caller: IWattleflow, **kwargs) -> Any:
        log: FindingLog = kwargs["log"]
        for scan in kwargs["scans"]:
            if scan.parse_error:
                continue
            for node in scan.tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                concrete: List[str] = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        decs = _decorator_names(item)
                        if item.name == "__init__":
                            log.add(
                                "R-CORE-STA-01",
                                "ERROR",
                                scan.relname,
                                item.lineno,
                                f"{node.name}.__init__: interface "
                                f"classes hold no state and impose no "
                                f"constructor discipline (DR-COR-001)",
                            )
                        elif "abstractmethod" not in decs:
                            concrete.append(item.name)
                    elif isinstance(item, ast.Assign):
                        for tgt in item.targets:
                            if isinstance(tgt, ast.Name) and tgt.id == "__slots__":
                                val = item.value
                                empty = isinstance(val, ast.Tuple) and not val.elts
                                if not empty:
                                    log.add(
                                        "R-CORE-STA-02",
                                        "ERROR",
                                        scan.relname,
                                        item.lineno,
                                        f"{node.name}.__slots__ non-empty: interfaces contribute no storage (DR-COR-002)",
                                    )
                if concrete and _is_interface_name(node.name):
                    log.add(
                        "R-CORE-STA-03",
                        "INFO",
                        scan.relname,
                        node.lineno,
                        f"{node.name} has concrete method(s) "
                        f"{', '.join(sorted(concrete))} — verify the "
                        f"defining-algorithm exception (DR-COR-001); not "
                        f"machine-decidable",
                    )


class FacadeRule(LintRule):
    def execute(self, caller: IWattleflow, **kwargs) -> Any:
        log: FindingLog = kwargs["log"]
        scans: List[ModuleScan] = kwargs["scans"]
        init_scan = next((s for s in scans if s.modname == "__init__"), None)
        if init_scan is None or init_scan.parse_error:
            return
        all_typevars: Dict[str, str] = {}
        for scan in scans:
            for tv in scan.typevars:
                all_typevars.setdefault(tv, scan.relname)

        declared_all: Set[str] = set()
        all_line = 0
        for node in init_scan.tree.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "__all__"
                and isinstance(node.value, (ast.List, ast.Tuple))
            ):
                all_line = node.lineno
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        declared_all.add(elt.value)

        imported = set(init_scan.imported_names)
        for name in sorted(imported - declared_all):
            log.add(
                "R-CORE-FAC-01",
                "ERROR",
                init_scan.relname,
                init_scan.imported_names[name],
                f"{name!r} imported but missing from __all__",
            )
        for name in sorted(declared_all - imported):
            log.add("R-CORE-FAC-01", "ERROR", init_scan.relname, all_line, f"{name!r} in __all__ but not imported")
        for name in sorted(imported):
            if name in all_typevars:
                log.add(
                    "R-CORE-FAC-02",
                    "ERROR",
                    init_scan.relname,
                    init_scan.imported_names[name],
                    f"{name!r} is a TypeVar (declared in "
                    f"{all_typevars[name]}) — roles are module-scoped "
                    f"and must not be re-exported by the facade",
                )


class AbstractnessRule(LintRule):
    """
    Runtime ORG-02d check; skipped when the run is static-only.

    Validity note (0.4.0): once the root IWattleflow became abstract (its
    name property), EVERY subclass that does not implement name is
    nominally abstract, so inspect.isabstract alone lost discriminative
    power for "is this a contract" — the proxy diverged from the
    construct.
    """

    def execute(self, caller: IWattleflow, **kwargs) -> Any:
        if kwargs.get("static_only"):
            return
        log: FindingLog = kwargs["log"]
        pkg_dir: Path = kwargs["pkg_dir"]
        parts = pkg_dir.resolve().parts
        try:
            idx = len(parts) - 1 - parts[::-1].index("wattleflow")
        except ValueError:
            log.add(
                "R-CORE-ABS-01",
                "WARNING",
                str(pkg_dir),
                0,
                "cannot locate 'wattleflow' in path; abstractness check skipped",
            )
            return
        root = str(Path(*parts[:idx]))
        if root not in sys.path:
            sys.path.insert(0, root)
        pkg_name = ".".join(parts[idx:])

        # Root contract members: abstract names every descendant inherits.
        root_abstracts: frozenset = frozenset()
        try:
            fw = importlib.import_module(f"{pkg_name}.framework")
            root_cls = getattr(fw, "IWattleflow", None)
            if root_cls is not None:
                root_abstracts = frozenset(getattr(root_cls, "__abstractmethods__", ()))
        except Exception:
            pass  # pre-refactor root or missing module;

        for scan in kwargs["scans"]:
            if scan.parse_error or scan.modname == "__init__":
                continue
            qualified = f"{pkg_name}.{scan.modname}"
            try:
                mod = importlib.import_module(qualified)
            except Exception as exc:
                log.add(
                    "R-CORE-ABS-01",
                    "ERROR",
                    scan.relname,
                    0,
                    f"module failed to import ({type(exc).__name__}: {exc}) — abstractness not verifiable",
                )
                continue
            for name, obj in vars(mod).items():
                if not inspect.isclass(obj) or obj.__module__ != qualified:
                    continue
                if _is_interface_name(name) and not inspect.isabstract(obj):
                    log.add(
                        "R-CORE-ABS-01",
                        "ERROR",
                        scan.relname,
                        0,
                        f"{name}: I-prefixed but concrete (inspect.isabstract is False) — ORG-02d",
                    )
                elif not _is_interface_name(name) and inspect.isabstract(obj):
                    log.add("R-CORE-ABS-02", "WARNING", scan.relname, 0, f"{name}: abstract but not I-prefixed")
                elif _is_interface_name(name):
                    own = frozenset(getattr(obj, "__abstractmethods__", ())) - root_abstracts
                    machinery = self._own_machinery(obj)
                    if not own and machinery:
                        log.add(
                            "R-CORE-ABS-03",
                            "ERROR",
                            scan.relname,
                            0,
                            f"{name}: abstract only via the inherited "
                            f"root contract (no abstract members of "
                            f"its own) yet defines concrete machinery "
                            f"({', '.join(sorted(machinery))}) — "
                            f"concrete in spirit, ORG-02d",
                        )

    @staticmethod
    def _own_machinery(cls: type) -> List[str]:
        """Concrete callables/properties defined in the class itself."""
        found: List[str] = []
        for attr, member in vars(cls).items():
            if attr in (
                "__module__",
                "__qualname__",
                "__doc__",
                "__slots__",
                "__abstractmethods__",
                "__dict__",
                "__weakref__",
                "__parameters__",
                "__orig_bases__",
                "_abc_impl",
            ):
                continue
            target = member.fget if isinstance(member, property) else member
            if callable(target) or isinstance(member, (staticmethod, classmethod)):
                if isinstance(member, (staticmethod, classmethod)):
                    target = member.__func__
                if not getattr(target, "__isabstractmethod__", False) and not getattr(
                    member, "__isabstractmethod__", False
                ):
                    found.append(attr)
        return found


# --------------------------------------------------------------------------- #
# endregion Rules                                                             #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Lint run (ITemplate)                                                 #
# --------------------------------------------------------------------------- #


class CoreLintRun(WemComponent, ITemplate):
    """
    ITemplate driving the lint: initialise() loads config and parses
    modules, perform_task() executes every rule strategy, finalise()
    renders the report via ReportBuilder — including when a rule raises,
    courtesy of the try/finally in process().

    process() is implemented here, not inherited: ITemplate declares the
    step ordering without a body (the core interface layer holds contracts
    only), so the consumer supplies the algorithm.
    """

    #: Rule order is deliberate: SideEffectRule must run before
    #: TypeVarRule/FacadeRule because it collects TypeVar declarations,
    #: and ImportRule before FacadeRule because it collects facade imports.
    RULES = (HeaderRule, SideEffectRule, ImportRule, TypeVarRule, ClassStateRule, FacadeRule, AbstractnessRule)

    def __init__(self, pkg_dir: Path, dictionary: Optional[Path], static_only: bool, quiet: bool = False) -> None:
        self._pkg_dir = pkg_dir
        self._dictionary = dictionary
        self._static_only = static_only
        self._quiet = quiet
        self._log = FindingLog()
        self._cfg: Dict[str, Any] = {}
        self._scans: List[ModuleScan] = []
        self.exit_code = 0

    # -- ITemplate steps --------------------------------------------------- #
    def process(self) -> None:
        self.initialise()
        try:
            # call optional hooks around the main work
            self.before_task()
            self.perform_task()
            self.after_task()
        finally:
            self.finalise()

    def initialise(self) -> None:
        self._cfg = dict(DEFAULT_CONFIG)
        if self._dictionary is not None:
            try:
                override = json.loads(self._dictionary.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                print(f"error: cannot read dictionary {self._dictionary}: {e}", file=sys.stderr)
                self.exit_code = 2
                raise SystemExit(2) from e
            # JSON carries no comments: underscore-prefixed keys are the
            # dictionary's prose and are dropped before the merge.
            override = {k: v for k, v in override.items() if not k.startswith("_")}
            self._cfg.update(override)
            # A key the dictionary declares but no rule reads is a criterion
            # stated and not measured — the same silent gap the vector exists
            # to prevent, so it is reported rather than ignored.
            for key in sorted(set(override) - set(DEFAULT_CONFIG)):
                self._log.add(
                    "R-CORE-CFG-01",
                    "WARNING",
                    self._dictionary.name,
                    0,
                    f"dictionary key {key!r} is declared but consumed by no rule in wem_lint "
                    f"{__version__} — criterion stated, not measured",
                )
        running = f"{sys.version_info.major}.{sys.version_info.minor}"
        if running != self._cfg["python_reference"]:
            self._log.add(
                "R-CORE-IMP-02",
                "WARNING",
                "(environment)",
                0,
                f"running Python {running}, dictionary pins "
                f"{self._cfg['python_reference']} — the stdlib "
                f"set tested is the interpreter's; results may "
                f"not be reproducible against the pin",
            )
        excluded = set(self._cfg.get("exclude_modules", ()))
        for path in sorted(self._pkg_dir.glob("*.py")):
            if path.name in excluded:
                self._log.add(
                    "R-CORE-EXC-01",
                    "INFO",
                    path.name,
                    0,
                    "excluded by dictionary (declared blind spot: infrastructure module, not an interface module)",
                )
                continue
            scan = ModuleScan(path)
            scan.parse()
            self._scans.append(scan)

    def perform_task(self) -> None:
        stdlib_names = set(getattr(sys, "stdlib_module_names", ()))
        if not stdlib_names:
            stdlib_names = set(_STDLIB_FALLBACK)
            self._log.add(
                "R-CORE-IMP-02",
                "WARNING",
                "(environment)",
                0,
                "sys.stdlib_module_names unavailable (Python < "
                "3.10); using a vendored fallback list — "
                "IMP-01/IMP-02 classification is approximate on "
                "this interpreter",
            )
        context = {
            "scans": self._scans,
            "cfg": self._cfg,
            "log": self._log,
            "stdlib_names": stdlib_names,
            "pkg_dir": self._pkg_dir,
            "static_only": self._static_only,
        }
        for rule_cls in self.RULES:
            rule_cls().execute(self, **context)

    def finalise(self) -> None:
        # --quiet suppresses the report on a run without errors; errors are
        # always reported, so silence never hides a violation.
        if not (self._quiet and not self._log.has_errors):
            print(ReportBuilder(self._log, len(self._scans), str(self._cfg.get("dictionary_version", "?"))).build())
        if self._log.has_errors:
            self.exit_code = 1


# --------------------------------------------------------------------------- #
# endregion Lint run                                                          #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Main                                                                 #
# --------------------------------------------------------------------------- #


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Conformance lint for the wattleflow-core interface layer (vector output, no aggregate score)."
    )
    parser.add_argument(
        "package", nargs="?", default=f"{_REPO_ROOT}/src/wattleflow/core", help="path to the core package directory"
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=_DEFAULT_DICTIONARY,
        help=f"JSON criterion dictionary overriding the embedded defaults (default: {_DEFAULT_DICTIONARY})",
    )
    parser.add_argument("--no-import", action="store_true", help="skip the runtime abstractness check (R-CORE-ABS-*)")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="print nothing when the run has no errors (the report is still printed when errors exist)",
    )
    args = parser.parse_args(argv)

    pkg_dir = Path(args.package)
    if not pkg_dir.is_dir():
        print(f"error: {pkg_dir} is not a directory", file=sys.stderr)
        return 2

    run = CoreLintRun(pkg_dir, args.dictionary, args.no_import, args.quiet)
    run.process()
    return run.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
# --------------------------------------------------------------------------- #
# endregion Main                                                              #
# --------------------------------------------------------------------------- #
