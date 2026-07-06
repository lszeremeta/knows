"""Tests for the knows.diagnostics module (the --version report)."""

import json
from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, patch

import pytest

from knows import __version__, diagnostics


@pytest.fixture
def no_container(monkeypatch, tmp_path):
    """Make container detection negative regardless of the host."""
    monkeypatch.delenv("KNOWS_CONTAINER", raising=False)
    monkeypatch.delenv("container", raising=False)
    monkeypatch.setattr(diagnostics, "_DOCKERENV_PATH", tmp_path / "missing")


def _mock_distribution(direct_url=None, installer="pip"):
    """Build a distribution mock with optional PEP 610/376 metadata files."""
    files = {}
    if direct_url is not None:
        files["direct_url.json"] = json.dumps(direct_url)
    if installer is not None:
        files["INSTALLER"] = installer + "\n"
    dist = MagicMock()
    dist.read_text.side_effect = files.get
    return dist


def test_install_source_container_env(monkeypatch, no_container):
    """KNOWS_CONTAINER set by the official Docker image wins detection."""
    monkeypatch.setenv("KNOWS_CONTAINER", "1")
    assert diagnostics.detect_install_source() == "Docker/container"


def test_install_source_dockerenv_file(monkeypatch, no_container, tmp_path):
    """An existing /.dockerenv marker is detected as a container."""
    marker = tmp_path / ".dockerenv"
    marker.touch()
    monkeypatch.setattr(diagnostics, "_DOCKERENV_PATH", marker)
    assert diagnostics.detect_install_source() == "Docker/container"


def test_install_source_pypi(no_container):
    """No direct_url.json but an INSTALLER file means an index install."""
    with patch("knows.diagnostics.distribution", return_value=_mock_distribution()):
        assert diagnostics.detect_install_source() == "PyPI (pip)"


def test_install_source_source_tree(no_container):
    """Bare egg-info metadata (no INSTALLER) means a source tree."""
    dist = _mock_distribution(installer=None)
    with patch("knows.diagnostics.distribution", return_value=dist):
        assert diagnostics.detect_install_source() == "local (source tree)"


def test_install_source_editable(no_container):
    """PEP 610 editable installs are reported as local editable."""
    dist = _mock_distribution(
        {"url": "file:///home/user/knows", "dir_info": {"editable": True}}
    )
    with patch("knows.diagnostics.distribution", return_value=dist):
        assert diagnostics.detect_install_source() == "local (editable install)"


def test_install_source_local_dir(no_container):
    """A non-editable file:// install is reported as local source."""
    dist = _mock_distribution({"url": "file:///home/user/knows", "dir_info": {}})
    with patch("knows.diagnostics.distribution", return_value=dist):
        assert diagnostics.detect_install_source() == "local (from source)"


def test_install_source_vcs(no_container):
    """A VCS install (pip install git+...) is reported as VCS."""
    dist = _mock_distribution(
        {"url": "https://github.com/lszeremeta/knows", "vcs_info": {"vcs": "git"}}
    )
    with patch("knows.diagnostics.distribution", return_value=dist):
        assert diagnostics.detect_install_source() == "VCS (git)"


def test_install_source_vcs_with_commit(no_container):
    """A VCS install shows the pinned commit from PEP 610 metadata."""
    dist = _mock_distribution(
        {
            "url": "https://github.com/lszeremeta/knows",
            "vcs_info": {
                "vcs": "git",
                "commit_id": "ca12d09e8f6ba44653e49143512130351be49f00",
            },
        }
    )
    with patch("knows.diagnostics.distribution", return_value=dist):
        assert (
            diagnostics.detect_install_source() == "VCS (git, commit ca12d09e8f6b)"
        )


def test_install_source_not_installed(no_container):
    """Missing package metadata means running from a source tree."""
    with patch(
        "knows.diagnostics.distribution",
        side_effect=PackageNotFoundError("knows"),
    ):
        assert (
            diagnostics.detect_install_source()
            == "not installed (running from source tree)"
        )


def test_git_describe_success():
    """A successful git describe returns the stripped describe string."""
    proc = MagicMock(returncode=0, stdout="v3.0.0-28-gca12d09-dirty\n")
    with patch("knows.diagnostics.subprocess.run", return_value=proc):
        assert diagnostics._git_describe() == "v3.0.0-28-gca12d09-dirty"


def test_git_describe_not_a_repo():
    """A non-zero git exit code (no repo, no tags) yields None."""
    proc = MagicMock(returncode=128, stdout="")
    with patch("knows.diagnostics.subprocess.run", return_value=proc):
        assert diagnostics._git_describe() is None


def test_git_describe_git_missing():
    """A missing git binary yields None instead of raising."""
    with patch(
        "knows.diagnostics.subprocess.run",
        side_effect=FileNotFoundError("git"),
    ):
        assert diagnostics._git_describe() is None


def test_report_includes_git_line_when_available(monkeypatch, no_container):
    """The report shows the git state right after the install source."""
    monkeypatch.setattr(
        diagnostics, "_git_describe", lambda: "v3.0.0-28-gca12d09"
    )
    report = diagnostics.build_version_report()
    lines = report.splitlines()
    installed_index = next(
        i for i, line in enumerate(lines) if line.startswith("Installed from:")
    )
    assert lines[installed_index + 1] == "Git: v3.0.0-28-gca12d09"


def test_report_omits_git_line_when_unavailable(monkeypatch, no_container):
    """No git information means no Git line in the report."""
    monkeypatch.setattr(diagnostics, "_git_describe", lambda: None)
    report = diagnostics.build_version_report()
    assert "Git:" not in report


def test_dependency_constants_match_package_metadata():
    """REQUIRED_DEPENDENCIES and DRAW_DEPENDENCIES mirror pyproject.toml."""
    from importlib.metadata import requires

    from packaging.requirements import Requirement

    raw = requires("knows")
    assert raw, "knows package metadata not available"
    reqs = [Requirement(r) for r in raw]

    required = {r.name for r in reqs if r.marker is None}
    draw = {
        r.name
        for r in reqs
        if r.marker is not None and r.marker.evaluate({"extra": "draw"})
    }
    assert required == set(diagnostics.REQUIRED_DEPENDENCIES)
    assert draw == set(diagnostics.DRAW_DEPENDENCIES)


def test_dependency_lines_mark_missing_optional(monkeypatch):
    """Missing draw extras show up as optional, present deps as OK."""
    def fake_version(name):
        return None if name in diagnostics.DRAW_DEPENDENCIES else "1.2.3"

    monkeypatch.setattr(diagnostics, "_dependency_version", fake_version)
    lines = diagnostics._dependency_lines()

    networkx_line = next(line for line in lines if "networkx" in line)
    assert "1.2.3" in networkx_line and "OK" in networkx_line
    matplotlib_line = next(line for line in lines if "matplotlib" in line)
    assert "not installed (optional)" in matplotlib_line


def test_dependency_lines_mark_missing_required(monkeypatch):
    """A missing required dependency is clearly flagged."""
    def fake_version(name):
        return None if name == "networkx" else "1.2.3"

    monkeypatch.setattr(diagnostics, "_dependency_version", fake_version)
    lines = diagnostics._dependency_lines()

    networkx_line = next(line for line in lines if "networkx" in line)
    assert "MISSING (required)" in networkx_line


def test_visualization_unavailable_without_matplotlib(monkeypatch):
    """Missing matplotlib disables visualization and shows the install hint."""
    monkeypatch.setattr("knows.graph_drawer.MATPLOTLIB_AVAILABLE", False)
    lines = diagnostics._visualization_lines()
    assert lines == [
        f"Visualization: NOT available - install with: {diagnostics.DRAW_INSTALL_HINT}"
    ]


def test_visualization_unavailable_without_scipy(monkeypatch):
    """Missing scipy disables visualization even with matplotlib present."""
    monkeypatch.setattr("knows.graph_drawer.MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr(diagnostics, "_dependency_version", lambda name: None)
    lines = diagnostics._visualization_lines()
    assert "NOT available" in lines[0]


def test_visualization_available_notes_missing_tkinter(monkeypatch):
    """Available visualization warns when only Tkinter (for -d) is missing."""
    monkeypatch.setattr("knows.graph_drawer.MATPLOTLIB_AVAILABLE", True)
    monkeypatch.setattr("knows.graph_drawer.TKINTER_AVAILABLE", False)
    monkeypatch.setattr(diagnostics, "_dependency_version", lambda name: "1.0.0")
    lines = diagnostics._visualization_lines()
    assert lines[0] == "Visualization: available"
    assert "Tkinter" in lines[1] and "-d" in lines[1]


def test_plugin_lines_list_builtin_formats():
    """The builtin entry point is listed with its format names."""
    lines = diagnostics._plugin_lines()
    builtin_line = next(line for line in lines if line.startswith("  builtin "))
    assert "yarspg" in builtin_line
    assert "formats)" in builtin_line


def test_plugin_lines_report_broken_plugin():
    """A broken plugin is reported instead of crashing the report."""
    mock_ep = MagicMock()
    mock_ep.name = "broken"
    mock_ep.load.side_effect = ImportError("no such module")
    mock_ep.dist.name = "broken-dist"
    mock_ep.dist.version = "0.1"

    from importlib.metadata import entry_points as real_ep

    def patched_entry_points(group):
        return list(real_ep(group=group)) + [mock_ep]

    with patch("knows.diagnostics.entry_points", side_effect=patched_entry_points):
        lines = diagnostics._plugin_lines()

    assert "  broken (broken-dist 0.1): broken - no such module" in lines
    # Other plugins are still listed.
    assert any(line.startswith("  builtin ") for line in lines)


def test_plugin_lines_without_entry_points():
    """No entry points at all still produces a valid section."""
    with patch("knows.diagnostics.entry_points", return_value=[]):
        assert diagnostics._plugin_lines() == ["  (none found)"]


def test_report_structure(no_container):
    """The full report starts with the plain version line and has all sections."""
    report = diagnostics.build_version_report()
    lines = report.splitlines()

    assert lines[0] == f"knows {__version__}"
    assert "Python:" in report
    assert "Installed from:" in report
    assert "Dependencies:" in report
    assert "networkx" in report
    assert "Tkinter" in report
    assert "Visualization:" in report
    assert "Format plugins (knows.formats):" in report
    assert "yarspg" in report
