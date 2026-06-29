# Module name: tests/unit/audit.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

"""audit — static + dynamic design audit for a source tree.

A thin CLI host that dispatches to one analysis class per subcommand. The
static modes import NOTHING from the target tree (pure AST) and are safe to run
on any source; the dynamic `bench` mode DOES import the classes it measures, so
run it only on code you trust. Behavioural unit tests (e.g. the ISingleton
selftest) live under tests/unit/<category>/, keeping this file extensible.

  scan      Static, import-graph based, for ANY interface name:
              a) every module that imports the interface
              b) every class that derives from it (direct + transitive)
              c) every instantiation call site of such a class
              d) the DANGEROUS pattern: a singleton re-instantiated with
                 DIFFERENT argument signatures (a re-init guard would break it)

  impls     Static, inheritance-graph based: lists every implementation of an
            interface GROUPED BY LIBRARY (path), with inheritance depth and
            leaf/internal status. Formats: text (default), dot, mermaid, csv.

  stats     Static, interface-agnostic design metrics: fan-out per base class,
            @abstractmethod count per interface (ISP), and Robert C. Martin's
            per-module coupling (Ce, Ca, instability I, abstractness A,
            distance-from-main-sequence D). Refactor radar.

  mem       Static, AST-only memory model: detects __slots__ leaks (a class
            declares __slots__ but an ancestor lacks them, so the __dict__
            survives) and estimates per-instance footprint, projected to N.

  bench     Dynamic A/B runtime+memory benchmark: imports two or more classes
            and times construction, an optional method call, and attribute
            access, plus per-instance memory, with stdev and a scale projection.

Usage
-----
    python tests/unit/audit.py scan  ISingleton --src src/wattleflow
    python tests/unit/audit.py impls IWattleflow --format dot | dot -Tsvg -o t.svg
    python tests/unit/audit.py stats --top 20
    python tests/unit/audit.py mem   --at 100000
    python tests/unit/audit.py bench --demo slots        # self-contained, no setup
    python tests/unit/audit.py bench --path src \
        --case existing=wattleflow.x:FacadeExisting \
        --case simplified=wattleflow.x:FacadeSimplified \
        --factory wattleflow.x:make_doc --attr identifier --call request

    # the behavioural singleton selftest now lives at:
    python tests/unit/creational/singleton.py --threads 100

LIMITS (be honest): static cross-module base/callee resolution is best-effort
and falls back to name matching. Dynamic dispatch and metaprogramming are not
seen — treat the static reports as a LOWER BOUND. `bench` numbers are machine-
and interpreter-specific; its projection is linear/first-order.
"""

from __future__ import annotations
import argparse
import ast
import gc
import importlib
import statistics as _stats
import sys
import timeit
import tracemalloc
from collections import defaultdict
from pathlib import Path


# --------------------------------------------------------------------------- #
# region Static model                                                         #
# --------------------------------------------------------------------------- #
class ModuleInfo:
    """Parsed view of one .py file: imports, class defs, instantiation calls."""

    __slots__ = ("path", "tree", "import_aliases", "module_aliases", "classes")

    def __init__(self, path: Path, tree: ast.AST):
        self.path = path
        self.tree = tree
        # local name -> interface name, for `from x import Iface as Y`
        self.import_aliases: dict[str, str] = {}
        # local name -> True, for `import a.b.creational as c` (module aliases)
        self.module_aliases: dict[str, bool] = {}
        # classname -> list of base expressions (ast nodes)
        self.classes: dict[str, list[ast.expr]] = {}


class Scanner:
    """Static import-graph audit of a source tree for a configurable interface.

    The interface name (e.g. "ISingleton") is required, so the same scanner can
    audit any singleton-style base class. Every step below is invoked exactly
    once by `run`, so each lives here as a private method.
    """

    def __init__(self, src: Path, interface: str):
        self.src = src
        self.interface = interface

    # --- public entry ----------------------------------------------------- #
    def run(self) -> int:
        src = self.src
        iface = self.interface
        if not src.exists():
            print(f"audit: source tree not found: {src}", file=sys.stderr)
            return 2

        modules, importers = self._load_modules()
        singletons, where = self._build_singleton_set(modules)
        sites = self._find_call_sites(modules, singletons)

        rel = self._rel

        print("=" * 70)
        print(f"a) Modules importing {iface}")
        print("=" * 70)
        if not importers:
            print(f"  (none found — {iface} not imported anywhere under src)")
        for p in importers:
            print(f"  {rel(p)}")

        print("\n" + "=" * 70)
        print(f"b) Classes deriving from {iface} (direct + transitive, by-name)")
        print("=" * 70)
        if not singletons:
            print("  (none found)")
        for cls in sorted(singletons):
            print(f"  {cls:<28} {rel(where[cls])}")

        print("\n" + "=" * 70)
        print("c) Instantiation call sites")
        print("=" * 70)
        if not sites:
            print("  (none detected — note: dynamic/factory construction is invisible)")
        for cls in sorted(sites):
            print(f"  {cls}")
            for p, line, sig in sorted(sites[cls], key=lambda t: (str(t[0]), t[1])):
                print(f"      {rel(p)}:{line}   ({sig})")

        print("\n" + "=" * 70)
        print("d) DANGEROUS pattern — re-instantiation with differing arguments")
        print(f"    (an init-once/caching guard on {iface} would SILENTLY IGNORE the later arguments)")
        print("=" * 70)
        danger = 0
        for cls in sorted(sites):
            records = sites[cls]
            sigs = {sig for _, _, sig in records}
            # risk if instantiated >1 time AND any call passes arguments AND
            # signatures differ (true reconfiguration) — or differ at all.
            passes_args = any(sig != "0pos" for _, _, sig in records)
            if len(records) >= 2 and passes_args and len(sigs) >= 2:
                danger += 1
                print(f"  [RISK] {cls} — {len(records)} call sites, {len(sigs)} distinct signatures:")
                for p, line, sig in sorted(records, key=lambda t: (str(t[0]), t[1])):
                    print(f"           {rel(p)}:{line}   ({sig})")
                print("         → guard breaks this: second+ construction reuses the FIRST")
                print("           instance and ignores these arguments. Resolve before guarding.")
        if danger == 0:
            print(f"  None found. An init-once guard is SAFE to apply: every {iface} subclass is")
            print("  either constructed once, or re-constructed only with identical arguments.")

        print("\n" + "-" * 70)
        print(
            f"summary: {len(importers)} importer(s), {len(singletons)} {iface} subclass(es), "
            f"{sum(len(v) for v in sites.values())} call site(s), {danger} risk(s)"
        )
        print("NOTE: call-site detection is a lower bound (AST name match only). Dynamic")
        print("construction and cross-module aliasing beyond simple cases are not resolved.")
        return 1 if danger else 0

    # --- shared loading / formatting (used by run + impls) ---------------- #
    def _load_modules(self) -> tuple[list[ModuleInfo], list[Path]]:
        """Parse every .py under src into ModuleInfo; also collect importers."""
        modules: list[ModuleInfo] = []
        importers: list[Path] = []
        for path in sorted(self.src.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            tree = self._parse_tree(path)
            if tree is None:
                print(f"  [skip] unparseable: {path}", file=sys.stderr)
                continue
            mi = self._collect_module(path, tree)
            modules.append(mi)
            if mi.import_aliases:
                importers.append(path)
        return modules, importers

    def _rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.src))
        except ValueError:
            return str(p)

    # --- private steps (each invoked once by run) ------------------------- #
    def _parse_tree(self, path: Path) -> ast.AST | None:
        try:
            return ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def _collect_module(self, path: Path, tree: ast.AST) -> ModuleInfo:
        mi = ModuleInfo(path, tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == self.interface:
                        mi.import_aliases[alias.asname or alias.name] = self.interface
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    # remember module aliases so we can resolve `c.Iface`
                    local = alias.asname or alias.name.split(".")[0]
                    mi.module_aliases[local] = True
            elif isinstance(node, ast.ClassDef):
                mi.classes[node.name] = list(node.bases)
        return mi

    def _base_refers_to_singleton(self, base: ast.expr, mi: ModuleInfo) -> bool:
        # `Iface` (possibly aliased), `something.Iface`, or generic `Iface[T]`
        if isinstance(base, ast.Subscript):
            base = base.value
        if isinstance(base, ast.Name):
            return mi.import_aliases.get(base.id) == self.interface or base.id == self.interface
        if isinstance(base, ast.Attribute):
            return base.attr == self.interface
        return False

    def _base_local_class(self, base: ast.expr) -> str | None:
        # unwrap generic parametrization, e.g. `IComponent[T]` -> IComponent
        if isinstance(base, ast.Subscript):
            base = base.value
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return None

    def _build_hierarchy(self, modules: list[ModuleInfo]) -> dict[str, dict]:
        """Return name -> {'path': Path, 'depth': int, 'parents': set[str]}.

        depth 1 = direct subclass of the interface; depth n = n inheritance
        hops from it. `parents` are the immediate bases that sit inside the
        interface subtree (the interface itself for direct subclasses). Cross-
        module resolution is by class name only (best-effort, see module LIMITS).
        """
        iface = self.interface
        info: dict[str, dict] = {}

        # seed: direct subclasses of the interface
        for mi in modules:
            for cls, bases in mi.classes.items():
                if cls == iface:
                    continue
                if any(self._base_refers_to_singleton(b, mi) for b in bases):
                    info[cls] = {"path": mi.path, "depth": 1, "parents": {iface}}

        # transitive closure: a class is in the subtree if a base already is.
        changed = True
        while changed:
            changed = False
            for mi in modules:
                for cls, bases in mi.classes.items():
                    if cls == iface:
                        continue
                    for b in bases:
                        parent = self._base_local_class(b)
                        if not parent or parent not in info:
                            continue
                        depth = info[parent]["depth"] + 1
                        cur = info.get(cls)
                        if cur is None:
                            info[cls] = {"path": mi.path, "depth": depth, "parents": {parent}}
                            changed = True
                        else:
                            if parent not in cur["parents"]:
                                cur["parents"].add(parent)
                            if depth < cur["depth"]:
                                cur["depth"] = depth
                                changed = True
        return info

    def _build_singleton_set(self, modules: list[ModuleInfo]) -> tuple[set[str], dict[str, Path]]:
        """Return (class names that derive from the interface, name -> defining path).

        Thin wrapper over `_build_hierarchy`, kept for the singleton-safety scan.
        """
        info = self._build_hierarchy(modules)
        singletons = set(info)
        where = {cls: d["path"] for cls, d in info.items()}
        return singletons, where

    def _call_signature(self, node: ast.Call) -> str:
        pos = len(node.args)
        star = any(isinstance(a, ast.Starred) for a in node.args)
        kw = sorted(k.arg for k in node.keywords if k.arg is not None)
        dstar = any(k.arg is None for k in node.keywords)
        parts = [f"{pos}pos"]
        if star:
            parts.append("*args")
        if kw:
            parts.append("kw=" + ",".join(kw))
        if dstar:
            parts.append("**kwargs")
        return " ".join(parts)

    def _find_call_sites(self, modules: list[ModuleInfo], singletons: set[str]):
        # class -> list of (path, lineno, signature)
        sites: dict[str, list[tuple[Path, int, str]]] = defaultdict(list)
        for mi in modules:
            for node in ast.walk(mi.tree):
                if not isinstance(node, ast.Call):
                    continue
                callee = None
                if isinstance(node.func, ast.Name):
                    callee = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee = node.func.attr
                if callee in singletons:
                    sites[callee].append((mi.path, node.lineno, self._call_signature(node)))
        return sites

    # --- implementations report (subcommand `impls`) ---------------------- #
    def report_implementations(self, fmt: str = "text") -> int:
        """List every implementation of the interface, grouped by library (path).

        fmt:
          text     human report grouped by file, with depth + statistics footer
          dot      Graphviz digraph (clusters = files, edges = inheritance)
          mermaid  Mermaid classDiagram (paste into Markdown under a fence)
          csv      class,library,depth,parents  (feed to pandas/sqlite/sheets)
        """
        if not self.src.exists():
            print(f"audit: source tree not found: {self.src}", file=sys.stderr)
            return 2

        modules, _ = self._load_modules()
        info = self._build_hierarchy(modules)

        if fmt == "dot":
            return self._emit_dot(info)
        if fmt == "mermaid":
            return self._emit_mermaid(info)
        if fmt == "csv":
            return self._emit_csv(info)
        return self._emit_text(info)

    def _emit_text(self, info: dict[str, dict]) -> int:
        iface = self.interface
        # which classes are themselves subclassed further (internal vs leaf)
        subclassed = {p for d in info.values() for p in d["parents"]}

        by_lib: dict[str, list[tuple[str, dict]]] = defaultdict(list)
        for cls, d in info.items():
            by_lib[self._rel(d["path"])].append((cls, d))

        print("=" * 70)
        print(f"Implementations of {iface}, grouped by library (path)")
        print("=" * 70)
        if not info:
            print(f"  (none found — no class derives from {iface} under {self.src})")
            return 0

        for lib in sorted(by_lib):
            entries = sorted(by_lib[lib], key=lambda t: (t[1]["depth"], t[0]))
            print(f"\n{lib}   ({len(entries)} impl)")
            for cls, d in entries:
                origin = "" if d["depth"] == 1 else "  ← " + ", ".join(sorted(d["parents"]))
                leaf = "" if cls in subclassed else "  ·leaf"
                print(f"    [d{d['depth']}] {cls:<26}{origin}{leaf}")

        # ---- statistics footer ------------------------------------------- #
        depths = defaultdict(int)
        for d in info.values():
            depths[d["depth"]] += 1
        leaves = sum(1 for c in info if c not in subclassed)
        max_depth = max(depths)

        print("\n" + "-" * 70)
        print(f"stats: {len(by_lib)} library(ies), {len(info)} implementation(s), max depth {max_depth}")
        print("   by library:  " + " | ".join(f"{lib.split('/')[-1]} {len(v)}" for lib, v in sorted(by_lib.items())))
        print("   by depth:    " + " | ".join(f"d{k} {depths[k]}" for k in sorted(depths)))
        print(f"   leaves: {leaves}   internal (extended further): {len(info) - leaves}")
        print("NOTE: inheritance is resolved by class name (cross-module best-effort).")
        return 0

    def _emit_dot(self, info: dict[str, dict]) -> int:
        libs: dict[str, list[str]] = defaultdict(list)
        for cls, d in info.items():
            libs[self._rel(d["path"])].append(cls)

        print(f"// Graphviz: dot -Tsvg this.dot -o {self.interface}.svg")
        print(f"digraph {self.interface}_impls {{")
        print("  rankdir=LR; node [shape=box, fontname=monospace, fontsize=10];")
        print(f'  "{self.interface}" [style=filled, fillcolor=lightyellow];')
        for i, lib in enumerate(sorted(libs)):
            print(f'  subgraph cluster_{i} {{ label="{lib}"; style=filled; color=gray95;')
            for cls in sorted(libs[lib]):
                print(f'    "{cls}";')
            print("  }")
        for cls, d in sorted(info.items()):
            for parent in sorted(d["parents"]):
                print(f'  "{parent}" -> "{cls}";')
        print("}")
        return 0

    def _emit_mermaid(self, info: dict[str, dict]) -> int:
        # namespace blocks group classes by library; edges are declared after.
        libs: dict[str, list[str]] = defaultdict(list)
        for cls, d in info.items():
            libs[self._rel(d["path"])].append(cls)

        print("%% paste under a ```mermaid fence in Markdown")
        print("classDiagram")
        print(f"    class {self.interface}")
        for lib in sorted(libs):
            ns = lib.replace("/", "_").replace(".", "_")
            print(f"    namespace {ns} {{")
            for cls in sorted(libs[lib]):
                print(f"        class {cls}")
            print("    }")
        for cls, d in sorted(info.items()):
            for parent in sorted(d["parents"]):
                print(f"    {parent} <|-- {cls}")
        return 0

    def _emit_csv(self, info: dict[str, dict]) -> int:
        print("class,library,depth,parents")
        for cls in sorted(info):
            d = info[cls]
            parents = "|".join(sorted(d["parents"]))
            print(f"{cls},{self._rel(d['path'])},{d['depth']},{parents}")
        return 0


# --------------------------------------------------------------------------- #
# endregion Static model                                                      #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Statistics (whole-tree design metrics)                               #
# --------------------------------------------------------------------------- #
class ModuleStats:
    """Per-file facts needed for the design metrics."""

    __slots__ = ("path", "key", "efferent", "classes")

    def __init__(self, path: Path, key: str):
        self.path = path
        self.key = key
        # internal module keys this file imports from
        self.efferent: set[str] = set()
        # list of {name, bases:list[str], abstract:bool, abstractmethods:int}
        self.classes: list[dict] = []


class Statistics:
    """Whole-tree, interface-agnostic design metrics to guide refactoring.

    Three reports, all from pure AST (no import of the target tree):

      fan-out      direct subclass count per base class. A very wide base is a
                   split candidate (Single Responsibility / Interface Segregation).
      richness     @abstractmethod count per interface. Fat interfaces that few
                   types fully implement signal an ISP violation; zero-method
                   ones are marker interfaces worth questioning.
      coupling     Robert C. Martin's per-module metrics:
                     Ce efferent, Ca afferent, I = Ce/(Ca+Ce) instability,
                     A = abstract/total abstractness, D = |A + I - 1| distance
                   from the main sequence. High D = "zone of pain" (stable+concrete)
                   or "zone of uselessness" (unstable+abstract) — refactor targets.

    `__init__.py` aggregators are excluded from the coupling graph (they re-export
    everything and would dwarf every real Ca/Ce). LIMIT: same name-based, best-
    effort resolution as the scanner — treat figures as directional, not exact.
    """

    def __init__(self, src: Path, top: int = 15):
        self.src = src
        self.top = top

    def run(self) -> int:
        if not self.src.exists():
            print(f"audit: source tree not found: {self.src}", file=sys.stderr)
            return 2
        mods = self._collect()
        self._report_fanout(mods)
        self._report_richness(mods)
        self._report_coupling(mods)
        return 0

    # --- collection ------------------------------------------------------- #
    @staticmethod
    def _base_name(b: ast.expr) -> str | None:
        if isinstance(b, ast.Subscript):
            b = b.value
        if isinstance(b, ast.Name):
            return b.id
        if isinstance(b, ast.Attribute):
            return b.attr
        return None

    @staticmethod
    def _dec_name(dec: ast.expr) -> str | None:
        if isinstance(dec, ast.Call):
            dec = dec.func
        if isinstance(dec, ast.Name):
            return dec.id
        if isinstance(dec, ast.Attribute):
            return dec.attr
        return None

    def _key(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.src))
        except ValueError:
            return str(path)

    def _resolve_import(self, importer: Path, node: ast.ImportFrom, known: set[Path]) -> str | None:
        """Map a `from ... import` to an internal module key, or None if external."""
        if node.level:  # relative: from .x import / from . import
            base = importer.parent
            for _ in range(node.level - 1):
                base = base.parent
            target = base
            if node.module:
                for part in node.module.split("."):
                    target = target / part
        else:  # absolute: only resolve inside our own top package
            if not node.module:
                return None
            parts = node.module.split(".")
            if parts[0] != self.src.name:
                return None
            target = self.src
            for part in parts[1:]:
                target = target / part
        for cand in (target.with_suffix(".py"), target / "__init__.py"):
            if cand in known:
                return self._key(cand)
        return None

    def _collect(self) -> list[ModuleStats]:
        paths = [p for p in sorted(self.src.rglob("*.py")) if "__pycache__" not in p.parts]
        known = set(paths)
        mods: list[ModuleStats] = []
        for path in paths:
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                print(f"  [skip] unparseable: {path}", file=sys.stderr)
                continue
            ms = ModuleStats(path, self._key(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    tgt = self._resolve_import(path, node, known)
                    if tgt and tgt != ms.key:
                        ms.efferent.add(tgt)
                elif isinstance(node, ast.ClassDef):
                    ms.classes.append(self._class_facts(node))
            mods.append(ms)
        return mods

    def _class_facts(self, node: ast.ClassDef) -> dict:
        bases = [n for n in (self._base_name(b) for b in node.bases) if n]
        abstractmethods = 0
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(self._dec_name(d) == "abstractmethod" for d in stmt.decorator_list):
                    abstractmethods += 1
        meta_abc = any(kw.arg == "metaclass" and self._base_name(kw.value) in ("ABCMeta",) for kw in node.keywords)
        abstract = "ABC" in bases or meta_abc or abstractmethods > 0
        return {
            "name": node.name,
            "bases": bases,
            "abstract": abstract,
            "abstractmethods": abstractmethods,
        }

    # --- reports ---------------------------------------------------------- #
    def _report_fanout(self, mods: list[ModuleStats]) -> None:
        fanout: dict[str, int] = defaultdict(int)
        for ms in mods:
            for c in ms.classes:
                for b in c["bases"]:
                    fanout[b] += 1
        ranked = sorted(fanout.items(), key=lambda kv: (-kv[1], kv[0]))
        print("=" * 70)
        print(f"fan-out — direct subclasses per base class (top {self.top})")
        print("=" * 70)
        print("  a very wide base is a split candidate (SRP / Interface Segregation)")
        for base, n in ranked[: self.top]:
            print(f"  {n:>4}  {base}")

    def _report_richness(self, mods: list[ModuleStats]) -> None:
        rows = [(c["name"], c["abstractmethods"]) for ms in mods for c in ms.classes if c["abstract"]]
        rows.sort(key=lambda r: (-r[1], r[0]))
        markers = [name for name, n in rows if n == 0]
        print("\n" + "=" * 70)
        print(f"interface richness — @abstractmethod count (top {self.top})")
        print("=" * 70)
        print("  fat interfaces (high count) strain implementers (ISP); 0 = marker")
        for name, n in rows[: self.top]:
            print(f"  {n:>4}  {name}")
        if markers:
            print(f"  marker interfaces (0 abstract methods): {', '.join(sorted(markers))}")

    def _report_coupling(self, mods: list[ModuleStats]) -> None:
        graph = [m for m in mods if m.path.name != "__init__.py" and m.classes]
        keys = {m.key for m in graph}
        afferent: dict[str, int] = defaultdict(int)
        for ms in graph:
            for tgt in ms.efferent:
                if tgt in keys:
                    afferent[tgt] += 1

        print("\n" + "=" * 70)
        print("module coupling — Martin metrics (sorted by distance D, worst first)")
        print("=" * 70)
        print("  Ce efferent · Ca afferent · I instability · A abstractness · D |A+I-1|")
        print(f"  {'module':<26}{'Ce':>4}{'Ca':>4}{'I':>7}{'A':>7}{'D':>7}")
        rows = []
        for ms in graph:
            ce = len({t for t in ms.efferent if t in keys})
            ca = afferent.get(ms.key, 0)
            inst = ce / (ca + ce) if (ca + ce) else 0.0
            total = len(ms.classes)
            abstr = sum(1 for c in ms.classes if c["abstract"]) / total if total else 0.0
            dist = abs(abstr + inst - 1)
            rows.append((ms.key, ce, ca, inst, abstr, dist))
        for key, ce, ca, inst, abstr, dist in sorted(rows, key=lambda r: -r[5]):
            print(f"  {key:<26}{ce:>4}{ca:>4}{inst:>7.2f}{abstr:>7.2f}{dist:>7.2f}")
        print("  (__init__.py excluded as a re-export aggregator)")


# --------------------------------------------------------------------------- #
# endregion Statistics                                                        #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Static memory model                                                  #
# --------------------------------------------------------------------------- #
class MemoryModel:
    """Static, AST-only estimate of per-instance memory cost + __slots__ leaks.

    Without importing anything it answers two refactoring questions across the
    whole tree:

      slots-leak   classes that declare __slots__ yet STILL receive a __dict__
                   because some in-tree ancestor does NOT declare __slots__ — so
                   the slots save nothing. (The classic mistake: __slots__ on a
                   leaf whose base interface forgot them.)
      footprint    a coarse per-instance byte estimate (object header + slot
                   pointers + a __dict__ when present) and how many bytes a slots
                   fix would recover, projected to N instances via --at.

    Byte constants below are a rough CPython-64-bit model — figures are
    DIRECTIONAL, not exact; for measured numbers use `bench`. External bases not
    found in the tree (object, ABC, Generic, typing aliases) are assumed slotted.
    """

    # rough CPython 3.x / 64-bit model — directional only
    HEADER = 16   # PyObject_HEAD (refcount + type pointer)
    GC = 16       # GC header carried by objects that hold references
    SLOT = 8      # one pointer per __slots__ entry
    DICT = 112    # a small instance __dict__ once materialised

    def __init__(self, src: Path, at: int = 100_000, top: int = 20):
        self.src = src
        self.at = at
        self.top = top

    def run(self) -> int:
        if not self.src.exists():
            print(f"audit: source tree not found: {self.src}", file=sys.stderr)
            return 2
        classes = self._collect()
        if not classes:
            print("  (no classes found)")
            return 0
        leaks = self._report_leaks(classes)
        self._report_footprint(classes)
        return 1 if leaks else 0

    # --- collection ------------------------------------------------------- #
    def _rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.src))
        except ValueError:
            return str(p)

    @staticmethod
    def _base_name(b: ast.expr) -> str | None:
        if isinstance(b, ast.Subscript):
            b = b.value
        if isinstance(b, ast.Name):
            return b.id
        if isinstance(b, ast.Attribute):
            return b.attr
        return None

    @staticmethod
    def _slots_count(node: ast.ClassDef) -> tuple[bool, int | None]:
        """(declares __slots__, count or None if not a literal sequence)."""
        for stmt in node.body:
            targets = stmt.targets if isinstance(stmt, ast.Assign) else (
                [stmt.target] if isinstance(stmt, ast.AnnAssign) else []
            )
            if not any(isinstance(t, ast.Name) and t.id == "__slots__" for t in targets):
                continue
            value = stmt.value
            if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
                return True, len(value.elts)
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return True, 1
            return True, None  # declared but count not statically known
        return False, 0

    def _collect(self) -> dict[str, dict]:
        classes: dict[str, dict] = {}
        for path in sorted(self.src.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                print(f"  [skip] unparseable: {path}", file=sys.stderr)
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                declares, count = self._slots_count(node)
                bases = [n for n in (self._base_name(b) for b in node.bases) if n]
                classes[node.name] = {
                    "path": path,
                    "bases": bases,
                    "declares_slots": declares,
                    "slot_count": count,
                }
        return classes

    # --- slots resolution ------------------------------------------------- #
    def _dict_free(self, name: str, classes: dict, memo: dict) -> bool:
        """True if instances have NO __dict__ (slots effective all the way up)."""
        if name in memo:
            return memo[name]
        info = classes.get(name)
        if info is None:
            return True  # external base (object/ABC/Generic/…) assumed slotted
        memo[name] = True  # optimistic, guards inheritance cycles
        if not info["declares_slots"]:
            res = False
        else:
            res = all(self._dict_free(b, classes, memo) for b in info["bases"])
        memo[name] = res
        return res

    def _dictless_ancestors(self, name: str, classes: dict) -> list[str]:
        """In-tree ancestors that lack __slots__ (the reason a leak has a dict)."""
        out, stack, seen = [], list(classes[name]["bases"]), set()
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            info = classes.get(n)
            if info is None:
                continue
            if not info["declares_slots"]:
                out.append(n)
            stack.extend(info["bases"])
        return out

    # --- reports ---------------------------------------------------------- #
    def _report_leaks(self, classes: dict) -> int:
        memo: dict = {}
        leaks = []
        for name, info in classes.items():
            if info["declares_slots"] and not self._dict_free(name, classes, memo):
                leaks.append((name, info))

        print("=" * 70)
        print("__slots__ leaks — declares __slots__ but instances keep a __dict__")
        print("=" * 70)
        if not leaks:
            print("  (none — every class that declares __slots__ has slotted ancestors)")
        for name, info in sorted(leaks):
            culprits = self._dictless_ancestors(name, classes)
            why = ", ".join(culprits) if culprits else "a base outside the tree"
            print(f"  [LEAK] {name:<22} {self._rel(info['path'])}")
            print(f"           slots wasted; __dict__ forced by: {why}")
            print(f"           fix: add `__slots__ = ()` to {why if culprits else 'the offending base(s)'}")
        if leaks:
            recover = self.DICT * self.at
            print(f"\n  recoverable ≈ {self.DICT} B/instance per leaking class "
                  f"→ {recover/1024/1024:.2f} MB at {self.at:,} instances")
        return len(leaks)

    def _report_footprint(self, classes: dict) -> None:
        memo: dict = {}
        rows = []
        declared = dict_free_n = dict_bearing = 0
        for name, info in classes.items():
            if info["declares_slots"]:
                declared += 1
            free = self._dict_free(name, classes, memo)
            dict_free_n += free
            dict_bearing += not free
            size = self.HEADER + self.GC
            if info["slot_count"]:
                size += self.SLOT * info["slot_count"]
            if not free:
                size += self.DICT
            rows.append((name, size, free, info))

        print("\n" + "=" * 70)
        print(f"per-instance footprint estimate (coarse) — top {self.top} by size")
        print("=" * 70)
        print(f"  {'class':<24}{'~bytes':>8}  dict?  slots")
        for name, size, free, info in sorted(rows, key=lambda r: -r[1])[: self.top]:
            sc = info["slot_count"]
            slots = "—" if not info["declares_slots"] else (str(sc) if sc is not None else "?")
            print(f"  {name:<24}{size:>8}  {'no' if free else 'YES':<5}  {slots}")

        print("\n" + "-" * 70)
        print(f"summary: {len(classes)} class(es), {declared} declare __slots__, "
              f"{dict_free_n} dict-free, {dict_bearing} carry a __dict__")
        print(f"  every dict-bearing instance costs ~{self.DICT} B of __dict__; at "
              f"{self.at:,} that is {self.DICT*self.at/1024/1024:.1f} MB per class.")
        print("  NOTE: byte model is directional (CPython-64-bit constants); use `bench` to measure.")


# --------------------------------------------------------------------------- #
# endregion Static memory model                                               #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Dynamic benchmark                                                    #
# --------------------------------------------------------------------------- #
class Benchmark:
    """Dynamic A/B/N runtime cost comparison of construction, an optional method
    call, optional attribute access, and per-instance memory — with stdev and a
    linear projection at scale.

    Unlike the static tools this DOES import and instantiate the given classes,
    so it only runs on code you trust (opt-in, like a unit test). It generalises
    the facade_bench experiment: pass two or more cases and it measures each on
    the same axes, then (for exactly two cases) projects the A−B delta to N.

    Parameters
    ----------
    cases : list[(label, build)]
        `build()` takes no args and returns a fresh instance.
    attr : str | None
        Attribute name to time the access hot path (e.g. a __getattr__ delegate).
    call : str | None
        Method name to time a representative call (invoked with no args).
    n_time, n_mem, repeat : int
        Operations per timing run, instances held for the memory delta, and
        timeit repeat count (best-of and stdev are taken across repeats).
    """

    def __init__(self, cases, *, attr=None, call=None,
                 n_time=1_000_000, n_mem=100_000, repeat=5):
        self.cases = cases
        self.attr = attr
        self.call = call
        self.n_time = n_time
        self.n_mem = n_mem
        self.repeat = repeat

    def run(self) -> int:
        if len(self.cases) < 2:
            print("bench: need at least two --case specs to compare", file=sys.stderr)
            return 2
        print("Python:", sys.version.split()[0])
        print("=" * 70)

        results = {}
        for label, build in self.cases:
            results[label] = self._measure(label, build)

        self._report(results)
        if len(self.cases) == 2:
            self._project(results)
        return 0

    # --- measurement ------------------------------------------------------ #
    def _time(self, op) -> tuple[float, float]:
        """Return (best seconds/op, stdev seconds/op) over `repeat` runs."""
        gc.disable()
        try:
            totals = timeit.Timer(stmt=op).repeat(repeat=self.repeat, number=self.n_time)
        finally:
            gc.enable()
        per = [t / self.n_time for t in totals]
        stdev = _stats.pstdev(per) if len(per) > 1 else 0.0
        return min(per), stdev

    def _measure(self, label, build) -> dict:
        r = {"construct": self._time(build)}

        inst = build()
        if self.call is not None:
            method = getattr(inst, self.call)
            r["call"] = self._time(method)
        if self.attr is not None:
            attr = self.attr
            r["attr"] = self._time(lambda: getattr(inst, attr))

        # memory: structural (getsizeof of one) + traced delta for n_mem
        r["sizeof"] = sys.getsizeof(inst)
        r["has_dict"] = hasattr(inst, "__dict__")
        gc.collect()
        gc.disable()
        tracemalloc.start()
        base, _ = tracemalloc.get_traced_memory()
        keep = [build() for _ in range(self.n_mem)]
        cur, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        gc.enable()
        r["traced_per"] = (cur - base) / len(keep)
        del keep
        return r

    # --- reporting -------------------------------------------------------- #
    @staticmethod
    def _ns(t):
        return f"{t * 1e9:8.1f} ns"

    def _report(self, results: dict) -> None:
        axes = [("construct", "construction / wrapper")]
        if self.call is not None:
            axes.append(("call", f"{self.call}() / call"))
        if self.attr is not None:
            axes.append(("attr", f".{self.attr} access"))

        print("Per-operation timing (best-of, ±stdev over repeats):")
        for key, title in axes:
            print(f"  {title}")
            for label, r in results.items():
                best, sd = r[key]
                print(f"      {label:<22} {self._ns(best)}  ± {self._ns(sd).strip()}")

        print("\nMemory per instance:")
        for label, r in results.items():
            note = "has __dict__" if r["has_dict"] else "slotted"
            print(f"  {label:<22} traced={r['traced_per']:7.1f} B   "
                  f"getsizeof={r['sizeof']:>4} B ({note})")
        print("  (traced > getsizeof ⇒ a hidden __dict__ or sub-objects — see `mem`)")

    def _project(self, results: dict) -> None:
        (la, ra), (lb, rb) = list(results.items())
        print("\n" + "=" * 70)
        print(f"Projection at scale ({la} − {lb}, linear/first-order):")
        d_con = (ra["construct"][0] - rb["construct"][0])
        d_mem = (ra["traced_per"] - rb["traced_per"])
        d_acc = None
        if "attr" in ra:
            d_acc = ra["attr"][0] - rb["attr"][0]
        for n_obj, n_acc in [(10_000, 100_000), (100_000, 5_000_000)]:
            line = f"  {n_obj:,} objs: {d_con*n_obj*1e3:+7.1f} ms build, {d_mem/1024/1024*n_obj:+6.2f} MB"
            if d_acc is not None:
                line += f", {d_acc*n_acc*1e3:+7.1f} ms over {n_acc:,} reads"
            print(line)
        print("  NOTE: linear extrapolation ignores cache/GC effects at scale.")

    # --- built-in demos (self-contained, no target import needed) --------- #
    @staticmethod
    def demo_slots():
        """Cases that quantify the __slots__ leak `mem` reports and the fix just
        applied to IWattleflow/IAdaptee: the SAME three-attribute subclass keeps
        a __dict__ when its base forgot __slots__ (leak), but is dict-free when
        the base is slotted. Run via `bench --demo slots`."""

        class _DictBase:  # forgot __slots__ → a __dict__ leaks into every subclass
            pass

        class Leaky(_DictBase):
            __slots__ = ("a", "b", "c")  # declared, but defeated by _DictBase
            def __init__(self):
                self.a = self.b = self.c = 1

        class _SlotBase:
            __slots__ = ()

        class Slotted(_SlotBase):
            __slots__ = ("a", "b", "c")
            def __init__(self):
                self.a = self.b = self.c = 1

        return [("leaky (base lacks __slots__)", Leaky), ("slotted (base has __slots__)", Slotted)]


# --------------------------------------------------------------------------- #
# endregion Dynamic benchmark                                                 #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Audit (CLI front-end)                                                #
# --------------------------------------------------------------------------- #
class Audit:
    """CLI front-end: builds the parser and dispatches to one analysis class.

    `run` is the single entry point. Each subcommand maps to its own analysis
    class (Scanner / Statistics / MemoryModel / Benchmark) so audit.py stays a
    thin, extensible host — new static or dynamic checks are added as a class
    plus one `_handler`, without touching the others. Behavioural unit tests
    (e.g. the ISingleton selftest) live under tests/unit/<category>/, not here.
    """

    def __init__(self, argv: list[str] | None = None):
        self.argv = argv

    def run(self) -> int:
        parser = self._build_parser()
        args = parser.parse_args(self.argv)
        return args.func(args)

    def _build_parser(self) -> argparse.ArgumentParser:
        ap = argparse.ArgumentParser(description="static + dynamic design audit for a source tree")
        sub = ap.add_subparsers(dest="cmd", required=True)

        s = sub.add_parser("scan", help="static import-graph audit of a source tree")
        s.add_argument("interface", help="interface/base class name to audit (e.g. ISingleton)")
        s.add_argument("--src", type=Path, default=Path("src/wattleflow"))
        s.set_defaults(func=self._scan)

        i = sub.add_parser("impls", help="list implementations of an interface, grouped by library")
        i.add_argument("interface", help="interface/base class name to list (e.g. IWattleflow)")
        i.add_argument("--src", type=Path, default=Path("src/wattleflow"))
        i.add_argument(
            "--format",
            choices=("text", "dot", "mermaid", "csv"),
            default="text",
            help="text report (default), Graphviz dot, Mermaid classDiagram, or csv",
        )
        i.set_defaults(func=self._impls)

        st = sub.add_parser("stats", help="whole-tree design metrics (fan-out, ISP, Martin I/A/D)")
        st.add_argument("--src", type=Path, default=Path("src/wattleflow"))
        st.add_argument("--top", type=int, default=15, help="rows per ranked table (default: 15)")
        st.set_defaults(func=self._stats)

        m = sub.add_parser("mem", help="static per-instance memory model + __slots__ leak detector")
        m.add_argument("--src", type=Path, default=Path("src/wattleflow"))
        m.add_argument("--at", type=int, default=100_000, help="instance count for projection (default: 100000)")
        m.add_argument("--top", type=int, default=20, help="rows in the footprint table (default: 20)")
        m.set_defaults(func=self._mem)

        b = sub.add_parser("bench", help="dynamic A/B runtime+memory benchmark (imports the classes)")
        b.add_argument(
            "--demo",
            choices=("slots",),
            help="run a self-contained demo instead of --case (slots: dict-leak vs slotted)",
        )
        b.add_argument(
            "--case",
            action="append",
            metavar="LABEL=module:Class",
            help="a class to benchmark; repeat for ≥2 cases (omit when --demo is used)",
        )
        b.add_argument(
            "--factory",
            metavar="module:callable",
            help="no-arg callable returning the constructor argument(s); default: build with no args",
        )
        b.add_argument("--attr", help="attribute name to time (the access hot path)")
        b.add_argument("--call", help="method name to time (invoked with no args)")
        b.add_argument("--path", type=Path, default=Path("src"), help="dir prepended to sys.path for imports (default: src)")
        b.add_argument("--n-time", type=int, default=1_000_000, dest="n_time", help="ops per timing run (default: 1e6)")
        b.add_argument("--n-mem", type=int, default=100_000, dest="n_mem", help="instances for the memory delta (default: 1e5)")
        b.add_argument("--repeat", type=int, default=5, help="timeit repeat count (default: 5)")
        b.set_defaults(func=self._bench)
        return ap

    # --- handlers --------------------------------------------------------- #
    def _scan(self, args) -> int:
        return Scanner(args.src, args.interface).run()

    def _impls(self, args) -> int:
        return Scanner(args.src, args.interface).report_implementations(args.format)

    def _stats(self, args) -> int:
        return Statistics(args.src, top=args.top).run()

    def _mem(self, args) -> int:
        return MemoryModel(args.src, at=args.at, top=args.top).run()

    def _bench(self, args) -> int:
        if args.demo:
            cases = getattr(Benchmark, f"demo_{args.demo}")()
            return Benchmark(
                cases, attr=args.attr or "a",
                n_time=args.n_time, n_mem=args.n_mem, repeat=args.repeat,
            ).run()

        if not args.case:
            print("bench: provide two or more --case specs, or use --demo", file=sys.stderr)
            return 2
        if str(args.path) not in sys.path:
            sys.path.insert(0, str(args.path))
        factory = self._load(args.factory) if args.factory else None

        def make_build(cls):
            if factory is None:
                return cls
            return lambda: cls(*self._as_args(factory()))

        cases = []
        for spec in args.case:
            label, _, target = spec.partition("=")
            if not target:
                label, target = target, label  # allow bare module:Class with no label
            cls = self._load(target)
            cases.append((label or cls.__name__, make_build(cls)))

        return Benchmark(
            cases, attr=args.attr, call=args.call,
            n_time=args.n_time, n_mem=args.n_mem, repeat=args.repeat,
        ).run()

    @staticmethod
    def _as_args(value) -> tuple:
        return value if isinstance(value, tuple) else (value,)

    @staticmethod
    def _load(spec: str):
        """Resolve a `module:qualname` string to the object it names."""
        mod_name, _, qual = spec.partition(":")
        obj = importlib.import_module(mod_name)
        for part in filter(None, qual.split(".")):
            obj = getattr(obj, part)
        return obj


if __name__ == "__main__":
    raise SystemExit(Audit().run())
# --------------------------------------------------------------------------- #
# endregion Audit (CLI front-end)                                             #
# --------------------------------------------------------------------------- #
