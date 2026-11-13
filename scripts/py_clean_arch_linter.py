#!/usr/bin/env python3
"""
Architecture linter for revoockv Python Clean Architecture.

Parses .py files with `ast` (no third-party dependencies, no code is imported or executed)
and reports violations of the clean architecture rules. Complements ruff and mypy: those
check generic Python quality, this checks layering, naming and project conventions.

The linter follows the project's template (`.clean_arch.toml` next to `pyproject.toml`, else the
skill's default template; `--template REF` for one run): `[structure]` sets the folders,
`[lint] off` turns rules off, `[lint] warn` makes rules warnings that `--strict` does not fail on,
and `[lint.params]` sets `allowed_numbers`, `max_file_lines` and `constant_layers`.

Usage:
  python3 scripts/py_clean_arch_linter.py                          # whole project (src/<package>)
  python3 scripts/py_clean_arch_linter.py src/my_app/features/auth # one feature
  python3 scripts/py_clean_arch_linter.py --strict                 # exit 1 on violations
  python3 scripts/py_clean_arch_linter.py --rules import_violation,naming_file
  python3 scripts/py_clean_arch_linter.py --ignore magic_strings
  python3 scripts/py_clean_arch_linter.py --json
  python3 scripts/py_clean_arch_linter.py --list-rules
  python3 scripts/py_clean_arch_linter.py --template revoockv-original@1.0.0

Rules (all enabled by default):
  folder_structure    — feature/core folders must match data/domain/presentation layout
  naming_file         — snake_case files with layer suffixes (_use_case.py, _repository.py, _service.py, ...)
  naming_class        — class names must match their file (sign_in_use_case.py → SignInUseCase)
  use_case_shape      — one class per use case file, exposing only __call__
  use_case_no_try     — no try/except in use cases (repositories convert errors to Failure)
  import_violation    — layer dependency rules (domain pure, presentation → getters only, ...)
  relative_import     — absolute imports only
  domain_repository   — domain repositories are ABC/Protocol interfaces
  repository_impl     — *RepositoryImpl inherits a domain repository and receives `logger`
  repository_result   — repository methods return Result[...]
  repository_logging  — every public repository method logs through self._logger
  model_mapping       — *Model classes define to_entity() and from_entity() (classmethod)
  entity_frozen       — domain entity dataclasses are frozen=True
  logger_injection    — no logging.getLogger()/logging.info() outside core DI; inject the logger
  no_print            — no print(); use the injected logger or the adapter's output API
  container_access    — the DI container is imported only by presentation/di and root modules
  docstring_public    — public classes, functions, methods and __call__ have docstrings
  type_hints          — every parameter and return value is annotated
  magic_numbers       — numbers in domain/presentation code are class constants (except -1, 0, 1, 2)
  magic_strings       — strings in domain/presentation code are class constants
  module_constants    — constants live in the owning class, not at module level (domain/presentation)
  di_naming           — <feature>_di.py with register_<feature>(), <feature>_getters.py, wired in di.py
  file_size           — a file longer than max_file_lines does too much: split it into data sources,
                        services and models that the repository orchestrates
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

__version__ = "0.3.0"

RULES: dict[str, str] = {
    "folder_structure": "feature/core folders must match data/domain/presentation layout",
    "naming_file": "snake_case files with layer suffixes",
    "naming_class": "class names must match their file",
    "use_case_shape": "one class per use case file, exposing only __call__",
    "use_case_no_try": "no try/except in use cases",
    "import_violation": "layer dependency rules",
    "relative_import": "absolute imports only",
    "domain_repository": "domain repositories are ABC/Protocol interfaces",
    "repository_impl": "*RepositoryImpl inherits a domain repository and receives logger",
    "repository_result": "repository methods return Result[...]",
    "repository_logging": "every public repository method logs through self._logger",
    "model_mapping": "*Model classes define to_entity() and from_entity()",
    "entity_frozen": "domain entity dataclasses are frozen=True",
    "logger_injection": "no logging.getLogger()/logging.info() outside core DI",
    "no_print": "no print()",
    "container_access": "the DI container is imported only by presentation/di and root modules",
    "docstring_public": "public classes, functions, methods and __call__ have docstrings",
    "type_hints": "every parameter and return value is annotated",
    "magic_numbers": "numbers in domain/presentation code are class constants",
    "magic_strings": "strings in domain/presentation code are class constants",
    "module_constants": "constants live in the owning class, not at module level",
    "di_naming": "<feature>_di.py / register_<feature>() / <feature>_getters.py / wired in di.py",
    "file_size": "a file longer than max_file_lines must be split (data sources, services, models)",
}
ALL_RULES = set(RULES)

LAYERS = ("data", "domain", "presentation")
# The defaults below are replaced by the project's template in configure().
# Required folders of every feature and of core/: layer → subfolders (template [structure.required])
REQUIRED_SUBDIRS: dict[str, tuple[str, ...]] = {
    "data": ("data_sources", "models", "repositories"),
    "domain": ("entities", "repositories", "use_cases"),
    "presentation": ("di",),
}
# Allowed but not required (template [structure.optional])
OPTIONAL_SUBDIRS: dict[str, tuple[str, ...]] = {"data": ("services",)}
# Layers that accept no other subfolders (template [structure] strict_layers)
STRICT_SUBDIRS: tuple[str, ...] = ("data", "domain")
# Layers whose code is checked by magic_numbers, magic_strings, module_constants ([lint.params] constant_layers)
CONSTANT_LAYERS: tuple[str, ...] = ("domain", "presentation")
# Longest allowed file, in non-blank lines ([lint.params] max_file_lines)
MAX_FILE_LINES = 200
# Rules reported as warnings: shown, but `--strict` does not fail on them ([lint] warn)
WARN_RULES: set[str] = set()
FILE_SUFFIXES = {
    ("domain", "use_cases"): ("_use_case.py",),
    ("domain", "repositories"): ("_repository.py",),
    ("data", "repositories"): ("_repository_impl.py",),
    ("data", "models"): ("_model.py",),
    ("data", "data_sources"): ("_data_source.py",),
    ("data", "services"): ("_service.py",),
    ("presentation", "di"): ("_di.py", "_getters.py"),
}
CORE_DI_EXTRA_FILES = {"container.py"}
SNAKE_FILE = re.compile(r"^[a-z_][a-z0-9_]*\.py$")
CONSTANT_NAME = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
ALLOWED_NUMBERS = {-1, 0, 1, 2}
LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical", "log"}
LIFECYCLE_METHODS = {"init", "close", "dispose"}
SKIP_DIRS = {"__pycache__", ".venv", "venv", ".git", ".mypy_cache", ".ruff_cache", ".pytest_cache"}


@dataclass(frozen=True)
class Violation:
    rule: str
    file: str
    line: int
    message: str

    @property
    def is_warning(self) -> bool:
        return self.rule in WARN_RULES


@dataclass(frozen=True)
class FileInfo:
    path: Path
    package_root: Path
    package: str
    rel: tuple[str, ...]  # parts relative to the package root, file name included
    tree: ast.Module

    @property
    def scope(self) -> str:
        """'feature', 'core' or 'root' (di.py, main.py, other top-level modules)."""
        if self.rel[0] == "features" and len(self.rel) > 2:
            return "feature"
        if self.rel[0] == "core" and len(self.rel) > 1:
            return "core"
        return "root"

    @property
    def feature(self) -> str | None:
        return self.rel[1] if self.scope == "feature" else None

    def _unit_parts(self) -> tuple[str, ...]:
        """Parts below the feature/core folder: (layer, sublayer, ..., file)."""
        if self.scope == "feature":
            return self.rel[2:]
        if self.scope == "core":
            return self.rel[1:]
        return ()

    @property
    def layer(self) -> str | None:
        parts = self._unit_parts()
        return parts[0] if len(parts) > 1 and parts[0] in LAYERS else None

    @property
    def sublayer(self) -> str | None:
        parts = self._unit_parts()
        return parts[1] if self.layer and len(parts) > 2 else None

    @property
    def name(self) -> str:
        return self.rel[-1]

    @property
    def is_presentation_di(self) -> bool:
        return self.layer == "presentation" and self.sublayer == "di"


# ── Discovery ───────────────────────────────────────────────────────


def _find_package_root(path: Path) -> Path | None:
    """Nearest ancestor (or self) that looks like the app package: has features/ or core/ + di.py."""
    for candidate in [path, *path.parents]:
        if candidate.is_dir() and (candidate / "di.py").is_file() and (
            (candidate / "features").is_dir() or (candidate / "core").is_dir()
        ):
            return candidate
    for candidate in [path, *path.parents]:
        if candidate.name in ("features", "core"):
            return candidate.parent
    return None


def _resolve_targets(target: str | None) -> list[tuple[Path, Path]]:
    """Return (scan_path, package_root) pairs."""
    if target is None:
        cwd = Path.cwd()
        src = cwd / "src"
        roots = [p for p in sorted(src.glob("*")) if _find_package_root(p) == p] if src.is_dir() else []
        if not roots:
            root = _find_package_root(cwd)
            roots = [root] if root else []
        if not roots:
            raise SystemExit("Cannot find the app package (src/<package>/di.py). Pass a path.")
        return [(r, r) for r in roots]
    path = Path(target).resolve()
    if not path.exists():
        raise SystemExit(f"Path not found: {target}")
    if (path / "src").is_dir():
        return _resolve_targets_in(path / "src")
    root = _find_package_root(path if path.is_dir() else path.parent)
    if root is None:
        src_roots = _resolve_targets_in(path) if path.is_dir() else []
        if src_roots:
            return src_roots
        raise SystemExit(f"Cannot find the app package for {target}.")
    return [(path, root)]


def _resolve_targets_in(src: Path) -> list[tuple[Path, Path]]:
    roots = [p for p in sorted(src.glob("*")) if p.is_dir() and _find_package_root(p) == p]
    return [(r, r) for r in roots]


def _iter_py_files(path: Path) -> Iterator[Path]:
    if path.is_file():
        if path.suffix == ".py":
            yield path
        return
    for p in sorted(path.rglob("*.py")):
        if not any(part in SKIP_DIRS for part in p.parts):
            yield p


# ── Helpers ─────────────────────────────────────────────────────────


def _title(snake: str) -> str:
    return "".join(part[:1].upper() + part[1:] for part in snake.split("_"))


def _base_names(cls: ast.ClassDef) -> list[str]:
    names = []
    for base in cls.bases:
        node = base.value if isinstance(base, ast.Subscript) else base
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
    return names


def _decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
    names = []
    for dec in node.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Name):
            names.append(target.id)
        elif isinstance(target, ast.Attribute):
            names.append(target.attr)
    return names


def _methods(cls: ast.ClassDef) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _mentions_name(node: ast.AST | None, name: str) -> bool:
    if node is None:
        return False
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id == name:
            return True
        if isinstance(sub, ast.Attribute) and sub.attr == name:
            return True
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and name in sub.value:
            return True
    return False


def _imported_modules(tree: ast.Module) -> Iterator[tuple[int, str, int]]:
    """Yield (line, module path, relative level) for every import in the file."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name, 0
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            for alias in node.names:
                full = f"{base}.{alias.name}" if base and alias.name != "*" else base
                yield node.lineno, full, node.level


@dataclass(frozen=True)
class ModuleRef:
    kind: str  # 'stdlib' | 'third_party' | 'app'
    scope: str = ""  # 'feature' | 'core' | 'root'
    feature: str | None = None
    layer: str | None = None
    sublayer: str | None = None
    parts: tuple[str, ...] = ()


def _classify(module: str, package: str) -> ModuleRef:
    top = module.split(".")[0]
    if top != package:
        stdlib = top in sys.stdlib_module_names or top == "__future__"
        return ModuleRef(kind="stdlib" if stdlib else "third_party")
    parts = tuple(module.split(".")[1:])
    if not parts:
        return ModuleRef(kind="app", scope="root", parts=parts)
    if parts[0] == "features" and len(parts) > 1:
        rest = parts[2:]
        return ModuleRef(
            kind="app",
            scope="feature",
            feature=parts[1],
            layer=rest[0] if rest else None,
            sublayer=rest[1] if len(rest) > 1 else None,
            parts=parts,
        )
    if parts[0] == "core":
        rest = parts[1:]
        return ModuleRef(
            kind="app",
            scope="core",
            layer=rest[0] if rest else None,
            sublayer=rest[1] if len(rest) > 1 else None,
            parts=parts,
        )
    return ModuleRef(kind="app", scope="root", parts=parts)


def _is_container_module(ref: ModuleRef) -> bool:
    return ref.scope == "core" and ref.parts[:4] == ("core", "presentation", "di", "container")


# ── Linter ──────────────────────────────────────────────────────────


class Linter:
    def __init__(self, rules: set[str]) -> None:
        self.rules = rules
        self.violations: list[Violation] = []

    def report(self, rule: str, path: Path, line: int, message: str) -> None:
        if rule in self.rules:
            self.violations.append(Violation(rule, str(path), line, message))

    # ── Folder-level rules ──

    def check_unit_folders(self, unit: Path, kind: str) -> None:
        """Check one feature folder (or core/) for the required layout."""
        for layer in LAYERS:
            layer_dir = unit / layer
            if not layer_dir.is_dir():
                self.report("folder_structure", layer_dir, 1, f"missing {kind} layer folder '{layer}/'")
                continue
            for sub in REQUIRED_SUBDIRS[layer]:
                if not (layer_dir / sub).is_dir():
                    self.report("folder_structure", layer_dir / sub, 1, f"missing folder '{layer}/{sub}/'")
            if layer in STRICT_SUBDIRS:
                allowed = REQUIRED_SUBDIRS[layer] + OPTIONAL_SUBDIRS.get(layer, ())
                for child in sorted(layer_dir.iterdir()):
                    if child.is_dir() and child.name not in SKIP_DIRS and child.name not in allowed:
                        self.report(
                            "folder_structure",
                            child,
                            1,
                            f"unexpected folder '{layer}/{child.name}/' — allowed: " + ", ".join(allowed),
                        )
                    elif child.is_file() and child.suffix == ".py" and child.name != "__init__.py":
                        self.report(
                            "folder_structure",
                            child,
                            1,
                            f"file directly in '{layer}/' — move it into one of: "
                            + ", ".join(REQUIRED_SUBDIRS[layer] + OPTIONAL_SUBDIRS.get(layer, ())),
                        )
        for child in sorted(unit.iterdir()):
            if child.is_file() and child.suffix == ".py" and child.name != "__init__.py":
                self.report("folder_structure", child, 1, f"file directly in the {kind} folder — move it into a layer")
            elif child.is_dir() and child.name not in LAYERS and child.name not in SKIP_DIRS:
                self.report("folder_structure", child, 1, f"unexpected folder '{child.name}/' in the {kind} folder")

    def check_feature_di(self, package_root: Path, feature_dir: Path) -> None:
        feature = feature_dir.name
        di_dir = feature_dir / "presentation" / "di"
        di_file = di_dir / f"{feature}_di.py"
        getters_file = di_dir / f"{feature}_getters.py"
        main_di = package_root / "di.py"
        if main_di.is_file() and f"register_{feature}(" not in main_di.read_text(encoding="utf-8"):
            self.report("di_naming", main_di, 1, f"register_{feature}(container) is not called in di.py")
        if not di_dir.is_dir():
            return  # reported by folder_structure
        if not di_file.is_file():
            self.report("di_naming", di_file, 1, f"missing {feature}_di.py with register_{feature}()")
        else:
            tree = ast.parse(di_file.read_text(encoding="utf-8"))
            funcs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
            if f"register_{feature}" not in funcs:
                self.report("di_naming", di_file, 1, f"{feature}_di.py must define register_{feature}(container)")
            for name, node in funcs.items():
                if name.startswith("init_") and not name.startswith(f"init_{feature}"):
                    self.report("di_naming", di_file, node.lineno, f"initiation function must be init_{feature}()")
        if not getters_file.is_file():
            self.report("di_naming", getters_file, 1, f"missing {feature}_getters.py")

    # ── File-level rules ──

    def check_file(self, info: FileInfo) -> None:
        self.check_naming(info)
        self.check_imports(info)
        self.check_calls(info)
        self.check_definitions(info)
        if info.layer in CONSTANT_LAYERS:
            self.check_magic(info)
            self.check_module_constants(info)
        self.check_file_size(info)

    def check_file_size(self, info: FileInfo) -> None:
        source = info.path.read_text(encoding="utf-8")
        lines = sum(1 for line in source.splitlines() if line.strip())
        if lines > MAX_FILE_LINES:
            self.report(
                "file_size",
                info.path,
                1,
                f"{lines} non-blank lines (> {MAX_FILE_LINES}) — the file does too much: move I/O of each "
                "external system into its own data source, a library/tool into a service, parsing into the "
                "model, and let the repository orchestrate them",
            )

    def check_naming(self, info: FileInfo) -> None:
        name = info.name
        if not SNAKE_FILE.match(name):
            self.report("naming_file", info.path, 1, f"file name '{name}' must be snake_case")
        if name == "__init__.py" or info.layer is None or info.sublayer is None:
            return
        if len(info._unit_parts()) != 3:
            return  # nested deeper (e.g. presentation/api/schemas) — adapter folders are free-form
        suffixes = FILE_SUFFIXES.get((info.layer, info.sublayer))
        if suffixes is None:
            return
        if info.scope == "core" and info.is_presentation_di and name in CORE_DI_EXTRA_FILES:
            return
        if not name.endswith(suffixes):
            self.report(
                "naming_file",
                info.path,
                1,
                f"files in {info.layer}/{info.sublayer}/ must end with " + " or ".join(suffixes),
            )
            return

        classes = [n for n in info.tree.body if isinstance(n, ast.ClassDef)]
        class_names = {c.name for c in classes}
        stem = name[:-3]
        expected: str | None = None
        if (info.layer, info.sublayer) == ("domain", "use_cases"):
            expected = _title(stem)  # sign_in_use_case → SignInUseCase
        elif (info.layer, info.sublayer) == ("domain", "repositories"):
            expected = _title(stem)
        elif (info.layer, info.sublayer) == ("data", "repositories"):
            expected = _title(stem.removesuffix("_impl")) + "Impl"
        elif (info.layer, info.sublayer) == ("data", "models"):
            expected = _title(stem)
        if expected and expected not in class_names:
            self.report("naming_class", info.path, 1, f"expected class '{expected}' in {name}")
        if (info.layer, info.sublayer) == ("data", "data_sources") and not any(
            n.endswith("DataSource") for n in class_names
        ):
            self.report("naming_class", info.path, 1, f"{name} must define a class ending with 'DataSource'")
        if (info.layer, info.sublayer) == ("data", "services") and not any(n.endswith("Service") for n in class_names):
            self.report("naming_class", info.path, 1, f"{name} must define a class ending with 'Service'")

    def check_imports(self, info: FileInfo) -> None:
        for line, module, level in _imported_modules(info.tree):
            if level:
                self.report("relative_import", info.path, line, "use absolute imports (from <package>....)")
                continue
            ref = _classify(module, info.package)
            if ref.kind == "app" and _is_container_module(ref):
                if not (info.is_presentation_di or info.scope == "root"):
                    self.report(
                        "container_access",
                        info.path,
                        line,
                        "only presentation/di modules and di.py may import the container — use getters",
                    )
                continue
            reason = self._import_violation(info, ref)
            if reason:
                self.report("import_violation", info.path, line, f"{reason} ({module})")

    def _import_violation(self, info: FileInfo, ref: ModuleRef) -> str | None:
        if info.scope == "root" or ref.kind == "stdlib":
            return None
        if info.scope == "core" and ref.kind == "app" and ref.scope == "feature":
            return "core must not depend on features"
        if ref.kind == "app" and ref.scope == "root":
            return "only entry points may import root modules (di.py, main.py)"
        other_feature = ref.scope == "feature" and ref.feature != info.feature
        layer = info.layer

        if layer == "domain":
            if ref.kind == "third_party":
                return "domain must be framework-free (stdlib + domain modules only)"
            if ref.layer in ("data", "presentation"):
                return f"domain must not import the {ref.layer} layer"
            return None

        if other_feature and ref.layer in ("data", "presentation"):
            return f"features may only use another feature's domain, not its {ref.layer} layer"

        if layer == "data":
            if ref.layer == "presentation":
                return "data must not import the presentation layer"
            return None

        if layer == "presentation" and not info.is_presentation_di:
            if ref.layer == "data":
                return "presentation must not import the data layer"
            if ref.layer == "domain" and ref.sublayer in ("repositories", "use_cases"):
                return f"presentation must reach domain {ref.sublayer} through <feature>_getters.py"
        return None

    def check_calls(self, info: FileInfo) -> None:
        allow_logging_setup = info.scope == "core" and info.is_presentation_di
        for node in ast.walk(info.tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id == "print":
                self.report("no_print", info.path, node.lineno, "print() — use the injected logger or adapter output")
            if allow_logging_setup:
                continue
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "logging":
                if func.attr in ("getLogger", "basicConfig") or func.attr in LOG_METHODS:
                    self.report(
                        "logger_injection",
                        info.path,
                        node.lineno,
                        f"logging.{func.attr}() — inject logging.Logger via the constructor (registered in core DI)",
                    )
            elif isinstance(func, ast.Name) and func.id == "getLogger":
                self.report("logger_injection", info.path, node.lineno, "getLogger() — inject logging.Logger instead")

    def check_definitions(self, info: FileInfo) -> None:
        tree = info.tree
        self._check_functions(info, tree.body, in_class=False)
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        sub = (info.layer, info.sublayer)

        if sub == ("domain", "use_cases") and info.name != "__init__.py":
            if len(classes) != 1:
                self.report("use_case_shape", info.path, 1, f"a use case file must contain exactly one class (found {len(classes)})")
            for cls in classes:
                methods = {m.name for m in _methods(cls)}
                if "__call__" not in methods:
                    self.report("use_case_shape", info.path, cls.lineno, f"{cls.name} must implement __call__")
                for m in _methods(cls):
                    if _is_public(m.name):
                        self.report(
                            "use_case_shape", info.path, m.lineno, f"{cls.name}.{m.name}: use cases expose only __call__"
                        )
            for node in ast.walk(tree):
                if isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
                    self.report(
                        "use_case_no_try",
                        info.path,
                        node.lineno,
                        "no try/except in use cases — the repository returns Failure instead of raising",
                    )

        if sub == ("domain", "repositories"):
            for cls in classes:
                if not {"ABC", "Protocol"} & set(_base_names(cls)):
                    self.report("domain_repository", info.path, cls.lineno, f"{cls.name} must inherit ABC (or Protocol)")
                self._check_result_returns(info, cls)

        if sub == ("data", "repositories"):
            for cls in classes:
                if not cls.name.endswith("RepositoryImpl"):
                    continue
                if not any(b.endswith("Repository") for b in _base_names(cls)):
                    self.report("repository_impl", info.path, cls.lineno, f"{cls.name} must inherit its domain repository")
                init = next((m for m in _methods(cls) if m.name == "__init__"), None)
                params = {a.arg for a in (init.args.args + init.args.kwonlyargs)} if init else set()
                if "logger" not in params:
                    self.report("repository_impl", info.path, cls.lineno, f"{cls.name}.__init__ must receive `logger`")
                self._check_result_returns(info, cls)
                for m in _methods(cls):
                    if _is_public(m.name) and m.name not in LIFECYCLE_METHODS and not self._logs(m):
                        self.report(
                            "repository_logging",
                            info.path,
                            m.lineno,
                            f"{cls.name}.{m.name} must log success/failure via self._logger",
                        )

        if sub == ("data", "models"):
            for cls in classes:
                if not cls.name.endswith("Model"):
                    continue
                methods = {m.name: m for m in _methods(cls)}
                if "to_entity" not in methods:
                    self.report("model_mapping", info.path, cls.lineno, f"{cls.name} must define to_entity()")
                from_entity = methods.get("from_entity")
                if from_entity is None:
                    self.report("model_mapping", info.path, cls.lineno, f"{cls.name} must define from_entity()")
                elif not {"classmethod", "staticmethod"} & set(_decorator_names(from_entity)):
                    self.report("model_mapping", info.path, from_entity.lineno, f"{cls.name}.from_entity must be a classmethod")

        if sub == ("domain", "entities"):
            for cls in classes:
                for dec in cls.decorator_list:
                    is_call = isinstance(dec, ast.Call)
                    target = dec.func if isinstance(dec, ast.Call) else dec
                    name = target.id if isinstance(target, ast.Name) else getattr(target, "attr", "")
                    if name != "dataclass":
                        continue
                    frozen = is_call and any(
                        k.arg == "frozen" and isinstance(k.value, ast.Constant) and k.value.value is True
                        for k in dec.keywords  # type: ignore[union-attr]
                    )
                    if not frozen:
                        self.report("entity_frozen", info.path, cls.lineno, f"{cls.name}: use @dataclass(frozen=True, slots=True)")

        for cls in classes:
            self._check_class(info, cls)

    def _check_class(self, info: FileInfo, cls: ast.ClassDef) -> None:
        if _is_public(cls.name) and ast.get_docstring(cls) is None:
            self.report("docstring_public", info.path, cls.lineno, f"class {cls.name} needs a docstring")
        self._check_functions(info, cls.body, in_class=True, owner=cls.name)
        for node in cls.body:
            if isinstance(node, ast.ClassDef):
                self._check_class(info, node)

    def _check_functions(self, info: FileInfo, body: list[ast.stmt], *, in_class: bool, owner: str = "") -> None:
        for node in body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            label = f"{owner}.{node.name}" if owner else node.name
            needs_doc = _is_public(node.name) or node.name == "__call__"
            if "overload" in _decorator_names(node):
                needs_doc = False
            if needs_doc and ast.get_docstring(node) is None:
                self.report("docstring_public", info.path, node.lineno, f"{label} needs a docstring")
            if node.returns is None:
                self.report("type_hints", info.path, node.lineno, f"{label} needs a return annotation")
            args = node.args
            positional = args.posonlyargs + args.args
            if in_class and positional and "staticmethod" not in _decorator_names(node):
                positional = positional[1:]  # self / cls
            for arg in positional + args.kwonlyargs + [a for a in (args.vararg, args.kwarg) if a]:
                if arg.annotation is None:
                    self.report("type_hints", info.path, node.lineno, f"{label}: parameter '{arg.arg}' needs an annotation")

    def _check_result_returns(self, info: FileInfo, cls: ast.ClassDef) -> None:
        for m in _methods(cls):
            if not _is_public(m.name) or m.name in LIFECYCLE_METHODS or m.name.startswith("watch_"):
                continue
            if not _mentions_name(m.returns, "Result"):
                self.report("repository_result", info.path, m.lineno, f"{cls.name}.{m.name} must return Result[...]")

    @staticmethod
    def _logs(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for node in ast.walk(func):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = node.func.value
                if (
                    node.func.attr in LOG_METHODS
                    and isinstance(owner, ast.Attribute)
                    and owner.attr in ("_logger", "logger")
                ):
                    return True
        return False

    # ── Magic values ──

    def check_magic(self, info: FileInfo) -> None:
        for node in ast.walk(info.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for stmt in node.body:
                    self._scan_magic(info, stmt, is_first=stmt is node.body[0])

    def _scan_magic(self, info: FileInfo, stmt: ast.stmt, *, is_first: bool) -> None:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return  # nested definitions are visited by check_magic itself
        if is_first and isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            return  # docstring
        skip: set[int] = set()
        for node in ast.walk(stmt):
            if isinstance(node, ast.AnnAssign):
                skip.update(id(n) for n in ast.walk(node.annotation))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in LOG_METHODS:
                skip.update(id(n) for n in ast.walk(node))  # logger messages
            elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "Literal":
                skip.update(id(n) for n in ast.walk(node))
            elif isinstance(node, ast.JoinedStr):
                parts = [p for p in node.values if isinstance(p, ast.Constant)]
                skip.update(id(n) for n in ast.walk(node))
                if any(isinstance(p.value, str) and re.search(r"[A-Za-z]", p.value) for p in parts):
                    self.report("magic_strings", info.path, node.lineno, "f-string text — move the template into a class constant")
        for node in ast.walk(stmt):
            if id(node) in skip or not isinstance(node, ast.Constant):
                continue
            value = node.value
            if isinstance(value, bool) or value is None or value is Ellipsis:
                continue
            if isinstance(value, (int, float)) and value not in ALLOWED_NUMBERS:
                self.report("magic_numbers", info.path, node.lineno, f"magic number {value!r} — use a class constant")
            elif isinstance(value, str) and value:
                shown = value if len(value) <= 30 else value[:27] + "..."
                self.report("magic_strings", info.path, node.lineno, f"magic string {shown!r} — use a class constant")

    def check_module_constants(self, info: FileInfo) -> None:
        for node in info.tree.body:
            targets: list[ast.expr] = []
            value: ast.expr | None = None
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if not names or "__all__" in names or value is None:
                continue
            literal = all(
                isinstance(n, (ast.Constant, ast.Tuple, ast.List, ast.Set, ast.Dict, ast.expr_context))
                for n in ast.walk(value)
            )
            if literal and any(CONSTANT_NAME.match(n) for n in names):
                self.report(
                    "module_constants",
                    info.path,
                    node.lineno,
                    f"module-level constant {names[0]} — move it into the class that owns it",
                )


# ── Entry point ─────────────────────────────────────────────────────


def configure(template: object) -> None:
    """Take the folders, warnings and parameters of a template (scripts/templates.py Template).

    `[structure]` → REQUIRED_SUBDIRS / OPTIONAL_SUBDIRS / STRICT_SUBDIRS; `[lint] warn` → WARN_RULES;
    `[lint.params]`: `allowed_numbers`, `max_file_lines`, `constant_layers`.
    """
    global REQUIRED_SUBDIRS, OPTIONAL_SUBDIRS, STRICT_SUBDIRS, WARN_RULES, ALLOWED_NUMBERS
    global MAX_FILE_LINES, CONSTANT_LAYERS
    data = template.data  # type: ignore[attr-defined]
    structure = data.get("structure", {})
    lint = data.get("lint", {})
    params = lint.get("params", {})
    REQUIRED_SUBDIRS = {layer: tuple(subs) for layer, subs in structure.get("required", {}).items()}
    for layer in LAYERS:
        REQUIRED_SUBDIRS.setdefault(layer, ())
    OPTIONAL_SUBDIRS = {layer: tuple(subs) for layer, subs in structure.get("optional", {}).items()}
    STRICT_SUBDIRS = tuple(structure.get("strict_layers", ()))
    WARN_RULES = set(lint.get("warn", ()))
    ALLOWED_NUMBERS = set(params.get("allowed_numbers", ALLOWED_NUMBERS))
    MAX_FILE_LINES = int(params.get("max_file_lines", MAX_FILE_LINES))
    CONSTANT_LAYERS = tuple(params.get("constant_layers", CONSTANT_LAYERS))


def _parse_rules(raw: str | None) -> set[str]:
    if not raw:
        return set()
    names = {r.strip() for r in raw.split(",") if r.strip()}
    unknown = names - RULES.keys()
    if unknown:
        raise SystemExit(f"Unknown rule(s): {', '.join(sorted(unknown))}. Use --list-rules.")
    return names


def run(target: str | None, rules: set[str]) -> list[Violation]:
    linter = Linter(rules)
    for scan_path, package_root in _resolve_targets(target):
        package = package_root.name
        # Folder-level checks for every feature/core folder inside the scan path.
        units: list[tuple[Path, str]] = []
        features_dir = package_root / "features"
        if features_dir.is_dir():
            for feature_dir in sorted(p for p in features_dir.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
                if scan_path in (package_root, features_dir) or feature_dir in [scan_path, *scan_path.parents]:
                    units.append((feature_dir, "feature"))
        core_dir = package_root / "core"
        if core_dir.is_dir() and (scan_path == package_root or core_dir in [scan_path, *scan_path.parents]):
            units.append((core_dir, "core"))
        for unit, kind in units:
            linter.check_unit_folders(unit, kind)
            if kind == "feature":
                linter.check_feature_di(package_root, unit)

        for path in _iter_py_files(scan_path):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError as e:
                linter.violations.append(Violation("syntax", str(path), e.lineno or 1, str(e)))
                continue
            rel = path.relative_to(package_root).parts
            linter.check_file(FileInfo(path=path, package_root=package_root, package=package, rel=rel, tree=tree))
    return linter.violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=None, help="Project, src/<package> or feature path (default: auto).")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 when violations are found.")
    parser.add_argument("--rules", default=None, help="Comma-separated subset of rules to run.")
    parser.add_argument("--ignore", default=None, help="Comma-separated rules to skip.")
    parser.add_argument("--json", action="store_true", help="Print violations as JSON.")
    parser.add_argument("--list-rules", action="store_true", help="List rules and exit.")
    parser.add_argument(
        "--template",
        default=None,
        help="Template (name@version); default: the project's .clean_arch.toml, else the skill's default.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ns = parser.parse_args(argv)

    if ns.list_rules:
        for name, desc in RULES.items():
            print(f"{name:20} {desc}")
        return 0

    # The template: its folders, warnings and parameters; the rules it turns off (only when all rules run)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import templates  # noqa: PLC0415

    try:
        template = templates.resolve(ns.template, Path(ns.path) if ns.path else Path.cwd())
    except templates.TemplateError as e:
        raise SystemExit(str(e)) from e
    configure(template)
    rules = _parse_rules(ns.rules)
    if not rules:
        rules = set(RULES) - set(template.lint_off)
    rules -= _parse_rules(ns.ignore)
    violations = sorted(run(ns.path, rules), key=lambda v: (v.file, v.line, v.rule))

    cwd = Path.cwd()

    def shown(path: str) -> str:
        p = Path(path)
        return str(p.relative_to(cwd)) if p.is_relative_to(cwd) else path

    if ns.json:
        print(
            json.dumps(
                [
                    asdict(v) | {"file": shown(v.file), "severity": "warning" if v.is_warning else "error"}
                    for v in violations
                ],
                indent=2,
            )
        )
    else:
        print(f"Template {template.ref}")
        for v in violations:
            level = " (warning)" if v.is_warning else ""
            print(f"{shown(v.file)}:{v.line}: [{v.rule}]{level} {v.message}")
        if violations:
            counts = Counter(v.rule for v in violations)
            print(f"\n{len(violations)} violation(s): " + ", ".join(f"{r}={n}" for r, n in counts.most_common()))
        else:
            print("No clean architecture violations found.")
    errors = [v for v in violations if not v.is_warning]
    return 1 if ns.strict and errors else 0


if __name__ == "__main__":
    sys.exit(main())
