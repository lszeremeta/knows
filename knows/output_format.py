"""High-level facade that converts a :class:`~knows.graph.Graph` to any
registered output format via the plugin registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .format_plugin import ConvertContext, FormatResult
from .format_registry import FormatRegistry
from .graph_drawer import DEFAULT_VIZ_LIMIT

if TYPE_CHECKING:
    from .graph import Graph


class OutputFormat:
    """Thin wrapper that delegates format conversion to the plugin registry.

    Attributes:
        graph: An instance of the Graph class.
        viz_limit: Maximum nodes to display in visual outputs.
        show_info: Whether to show node count info on visualizations.
    """

    def __init__(self, graph: Graph, viz_limit: int = DEFAULT_VIZ_LIMIT, show_info: bool = True) -> None:
        """Inits OutputFormat with a graph.

        Args:
            graph: An instance of the Graph class.
            viz_limit: Maximum nodes for visual formats. Set to 0 to disable.
            show_info: Whether to show node count info on visualizations.
        """
        self.graph = graph
        self.viz_limit = viz_limit
        self.show_info = show_info

    def to_format(self, format_type: str) -> FormatResult:
        """Convert the graph to *format_type*.

        Args:
            format_type: Format identifier (e.g. ``"graphml"``).

        Returns:
            The conversion result containing data, kind, and default extension.

        Raises:
            KeyError: If *format_type* is not registered.
        """
        plugin = FormatRegistry().get(format_type)
        ctx = ConvertContext(viz_limit=self.viz_limit, show_info=self.show_info)
        return plugin.convert(self.graph.graph, ctx)
