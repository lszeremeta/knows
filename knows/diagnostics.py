"""Environment diagnostics shown by ``knows --version``.

Builds a curl-style multi-line report: knows version, Python and
platform info, dependency versions, visualization availability,
install source (PyPI, Docker, local) and installed ``knows.formats``
plugins.  The first report line is always ``knows <version>`` so
scripts that parse the version keep working.

This module is imported lazily by the CLI, so a normal run never pays
for probing optional dependencies.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from collections.abc import Iterable
from importlib.metadata import EntryPoint, PackageNotFoundError, distribution, entry_points
from importlib.metadata import version as installed_version
from pathlib import Path

from . import __version__
from .format_plugin import FormatPlugin

#: Required runtime dependencies (mirrors ``[project.dependencies]``).
REQUIRED_DEPENDENCIES = ("networkx", "Faker", "jsonschema")

#: Optional dependencies from the ``draw`` extra.
DRAW_DEPENDENCIES = ("matplotlib", "scipy")

DRAW_INSTALL_HINT = "pip install knows[draw]"

_DOCKERENV_PATH = Path("/.dockerenv")


def build_version_report() -> str:
    """Builds the multi-line ``--version`` report.

    Returns:
        str: The report; the first line is exactly ``knows <version>``.
    """
    lines = [
        f"knows {__version__}",
        "",
        f"Python: {platform.python_version()} ({platform.python_implementation()}), "
        f"{platform.system()} {platform.machine()}",
        f"Installed from: {detect_install_source()}",
    ]
    git_state = _git_describe()
    if git_state:
        lines.append(f"Git: {git_state}")
    lines += [
        "",
        "Dependencies:",
        *_dependency_lines(),
        "",
        *_visualization_lines(),
        "",
        "Format plugins (knows.formats):",
        *_plugin_lines(),
    ]
    return "\n".join(lines)


def detect_install_source() -> str:
    """Guesses where this knows installation comes from.

    Detection order: container markers (``KNOWS_CONTAINER`` set by the
    official Docker image, ``/.dockerenv``, the ``container`` variable
    set e.g. by podman), then PEP 610 ``direct_url.json`` metadata,
    which distinguishes PyPI, local and VCS installs.

    Returns:
        str: A short human-readable description of the install source.
    """
    if (
        os.environ.get("KNOWS_CONTAINER")
        or os.environ.get("container")
        or _DOCKERENV_PATH.exists()
    ):
        return "Docker/container"

    try:
        dist = distribution("knows")
    except PackageNotFoundError:
        return "not installed (running from source tree)"

    raw_direct_url = dist.read_text("direct_url.json")
    if raw_direct_url is None:
        # PEP 376: installers (pip, uv, conda) record themselves in
        # INSTALLER; a bare egg-info in a source tree has no such file.
        installer = (dist.read_text("INSTALLER") or "").strip()
        if installer:
            return f"PyPI ({installer})"
        return "local (source tree)"
    try:
        direct_url = json.loads(raw_direct_url)
    except ValueError:
        return "unknown"

    if (direct_url.get("dir_info") or {}).get("editable"):
        return "local (editable install)"
    if "vcs_info" in direct_url:
        vcs_info = direct_url.get("vcs_info") or {}
        vcs = vcs_info.get("vcs", "unknown")
        commit = (vcs_info.get("commit_id") or "")[:12]
        if commit:
            return f"VCS ({vcs}, commit {commit})"
        return f"VCS ({vcs})"
    if direct_url.get("url", "").startswith("file://"):
        return "local (from source)"
    return "unknown"


def _git_describe() -> str | None:
    """Describes the git state of the running package, if it is a checkout.

    Returns e.g. ``v3.0.0-28-gca12d09-dirty`` (28 commits after the
    ``v3.0.0`` release tag, uncommitted changes present) or None when
    the package does not live in a git repository, git is missing or
    no release tag is reachable.  Only ``v<number>`` tags are matched,
    so floating tags like ``latest`` are ignored.
    """
    package_root = Path(__file__).resolve().parent.parent
    try:
        proc = subprocess.run(
            [
                "git", "-C", str(package_root),
                "describe", "--tags", "--match", "v[0-9]*", "--dirty",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _dependency_version(name: str) -> str | None:
    """Returns the installed version of *name* or None when missing."""
    try:
        return installed_version(name)
    except PackageNotFoundError:
        return None


def _dependency_lines() -> list[str]:
    """Builds aligned table lines for required and optional dependencies."""
    from . import graph_drawer

    rows = []
    for name in REQUIRED_DEPENDENCIES:
        found = _dependency_version(name)
        rows.append((name, found or "-", "OK" if found else "MISSING (required)"))
    for name in DRAW_DEPENDENCIES:
        found = _dependency_version(name)
        rows.append((name, found or "-", "OK" if found else "not installed (optional)"))
    rows.append((
        "Tkinter",
        "-",
        "OK" if graph_drawer.TKINTER_AVAILABLE else "not available (optional)",
    ))

    name_width = max(len(name) for name, _, _ in rows)
    version_width = max(len(version) for _, version, _ in rows)
    return [
        f"  {name.ljust(name_width)}  {version.ljust(version_width)}  {status}"
        for name, version, status in rows
    ]


def _visualization_lines() -> list[str]:
    """Summarizes whether graph visualization can work and why not."""
    from . import graph_drawer

    if graph_drawer.MATPLOTLIB_AVAILABLE and _dependency_version("scipy") is not None:
        lines = ["Visualization: available"]
        if not graph_drawer.TKINTER_AVAILABLE:
            lines.append(
                "  Note: Tkinter is not available - the interactive window (-d) "
                "will not work; file formats (svg, png, jpg, pdf) still work."
            )
        return lines
    return [f"Visualization: NOT available - install with: {DRAW_INSTALL_HINT}"]


def _plugin_lines() -> list[str]:
    """Lists ``knows.formats`` entry points with their distributions.

    Unlike :class:`~knows.format_registry.FormatRegistry`, this keeps
    the provenance of each plugin (the providing distribution) and
    reports broken plugins instead of skipping them silently.
    """
    lines = []
    for ep in entry_points(group="knows.formats"):
        provider = _entry_point_provider(ep)
        try:
            names = _load_format_names(ep)
        except Exception as exc:
            lines.append(f"  {ep.name} ({provider}): broken - {exc}")
            continue
        if names:
            suffix = f" ({len(names)} formats)" if len(names) > 1 else ""
            lines.append(f"  {ep.name} ({provider}): {', '.join(names)}{suffix}")
        else:
            lines.append(f"  {ep.name} ({provider}): no formats")
    return lines or ["  (none found)"]


def _entry_point_provider(ep: EntryPoint) -> str:
    """Returns ``<distribution> <version>`` for the entry point, if known."""
    dist = getattr(ep, "dist", None)
    if dist is None:
        return "unknown distribution"
    try:
        return f"{dist.name} {dist.version}"
    except Exception:
        return "unknown distribution"


def _load_format_names(ep: EntryPoint) -> list[str]:
    """Instantiates the plugins behind *ep* and returns their format names.

    Mirrors the normalization rules of
    :meth:`~knows.format_registry.FormatRegistry._discover` (a factory
    may return a single plugin or an iterable of them), but propagates
    exceptions so the caller can report the plugin as broken.
    """
    result = ep.load()()
    if isinstance(result, FormatPlugin):
        plugins: Iterable[object] = [result]
    elif isinstance(result, Iterable) and not isinstance(result, (str, bytes)):
        plugins = list(result)
    else:
        plugins = [result]
    return [plugin.name for plugin in plugins if isinstance(plugin, FormatPlugin)]
