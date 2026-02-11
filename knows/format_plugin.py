"""Public plugin interface for output formats.

Defines the protocol that every format plugin must satisfy, plus the
data types shared between plugins and the rest of the application:

* :class:`OutputKind` -- discriminator for text / binary / multi-file output.
* :class:`FormatResult` -- immutable container returned by every plugin.
* :class:`ConvertContext` -- conversion parameters passed to every plugin.
* :class:`FormatPlugin` -- structural (duck-typed) protocol checked at runtime.

External packages register plugins via the ``knows.formats`` entry-point
group.  Each entry point must be a callable that returns a single
:class:`FormatPlugin` instance or an iterable of them.
"""

import enum
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import networkx as nx


class OutputKind(enum.Enum):
    """Discriminator for the kind of data a format plugin produces.

    Attributes:
        TEXT: Single text output (``str``).
        BINARY: Single binary blob (``bytes``).
        MULTI_FILE: Multiple named files (``dict[str, str | bytes]``).
    """

    TEXT = "text"
    BINARY = "binary"
    MULTI_FILE = "multi_file"


@dataclass(frozen=True)
class ConvertContext:
    """Parameters passed to :meth:`FormatPlugin.convert`.

    Attributes:
        viz_limit: Maximum nodes for visual formats (0 = unlimited).
        show_info: Whether to show node-count info on visualizations.
    """

    viz_limit: int = 0
    show_info: bool = True


@dataclass(frozen=True)
class FormatResult:
    """Immutable result returned by :meth:`FormatPlugin.convert`.

    Attributes:
        data: The converted output whose concrete type depends on *kind*:
            ``str`` for TEXT, ``bytes`` for BINARY,
            ``dict[str, str | bytes]`` for MULTI_FILE (keys are filename
            suffixes, e.g. ``"_nodes.csv"``).
        kind: Discriminator that tells callers how to interpret *data*.
        default_extension: File extension including the leading dot
            (e.g. ``".graphml"``).
    """

    data: str | bytes | dict[str, str | bytes]
    kind: OutputKind
    default_extension: str


@runtime_checkable
class FormatPlugin(Protocol):
    """Structural protocol that every output-format plugin must satisfy.

    Implementations do **not** need to inherit from this class --
    any object with the right attributes and method signature will pass
    an ``isinstance`` check thanks to :func:`typing.runtime_checkable`.
    """

    @property
    def name(self) -> str:
        """Short, unique identifier used on the CLI (e.g. ``"graphml"``)."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description shown in help text."""
        ...

    @property
    def output_kind(self) -> OutputKind:
        """The kind of output this plugin produces."""
        ...

    @property
    def default_extension(self) -> str:
        """Default file extension including the leading dot."""
        ...

    def convert(self, graph: nx.DiGraph, ctx: ConvertContext) -> FormatResult:
        """Convert *graph* to this format.

        Args:
            graph: The NetworkX directed graph to convert.
            ctx: Conversion parameters (visual limits, info display, ...).

        Returns:
            A :class:`FormatResult` whose *kind* matches
            :attr:`output_kind`.
        """
        ...
