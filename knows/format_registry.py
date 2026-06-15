"""Singleton registry that discovers and caches format plugins.

Plugins are loaded lazily from the ``knows.formats``
:mod:`importlib.metadata` entry-point group the first time any public
method is called.  Each entry point must reference a callable (factory)
that returns either a single :class:`~knows.format_plugin.FormatPlugin`
or an iterable of them.

Broken or duplicate plugins emit :func:`warnings.warn` messages but
never crash the application.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from importlib.metadata import entry_points

from .format_plugin import FormatPlugin


class FormatRegistry:
    """Discover, cache and look up format plugins.

    This is a singleton -- every ``FormatRegistry()`` call returns the
    same instance.  Plugins are discovered on the first access and
    cached until :meth:`reset` is called.
    """

    _instance: FormatRegistry | None = None
    _plugins: dict[str, FormatPlugin] | None = None

    def __new__(cls) -> FormatRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # -- internal ------------------------------------------------------------

    def _discover(self) -> None:
        """Load all ``knows.formats`` entry points and populate the cache."""
        self._plugins = {}
        eps = entry_points(group="knows.formats")
        for ep in eps:
            try:
                factory = ep.load()
            except Exception as exc:
                warnings.warn(
                    f"Failed to load format plugin {ep.name!r}: {exc}",
                    stacklevel=2,
                )
                continue

            try:
                result = factory()

                # Prefer a single conforming plugin even if it is also iterable.
                if isinstance(result, FormatPlugin):
                    plugins: Iterable[object] = [result]
                elif isinstance(result, Iterable) and not isinstance(
                    result, (str, bytes)
                ):
                    plugins = list(result)
                else:
                    plugins = [result]
            except Exception as exc:
                warnings.warn(
                    f"Failed to initialize format plugin {ep.name!r}: {exc}",
                    stacklevel=2,
                )
                continue

            for candidate in plugins:
                try:
                    if not isinstance(candidate, FormatPlugin):
                        warnings.warn(
                            f"Plugin {ep.name!r} returned object that does not "
                            f"satisfy FormatPlugin protocol",
                            stacklevel=2,
                        )
                        continue
                except Exception as exc:
                    warnings.warn(
                        f"Failed to inspect format plugin {ep.name!r}: {exc}",
                        stacklevel=2,
                    )
                    continue

                plugin = candidate
                try:
                    name = plugin.name
                except Exception as exc:
                    warnings.warn(
                        f"Failed to inspect format plugin {ep.name!r}: {exc}",
                        stacklevel=2,
                    )
                    continue
                if not isinstance(name, str) or not name:
                    warnings.warn(
                        f"Plugin {ep.name!r} returned an invalid format name: {name!r}",
                        stacklevel=2,
                    )
                    continue
                if name in self._plugins:
                    warnings.warn(
                        f"Duplicate format name {name!r} from "
                        f"{ep.name!r}, skipping",
                        stacklevel=2,
                    )
                    continue
                self._plugins[name] = plugin

    def _ensure_discovered(self) -> None:
        """Trigger discovery if the cache is empty."""
        if self._plugins is None:
            self._discover()

    # -- public API ----------------------------------------------------------

    def get(self, name: str) -> FormatPlugin:
        """Return the plugin registered under *name*.

        Args:
            name: Format identifier (e.g. ``"graphml"``).

        Returns:
            The matching :class:`~knows.format_plugin.FormatPlugin`.

        Raises:
            KeyError: If *name* is not registered.
        """
        self._ensure_discovered()
        assert self._plugins is not None  # ensured by _ensure_discovered
        try:
            return self._plugins[name]
        except KeyError:
            available = ', '.join(sorted(self._plugins))
            raise KeyError(
                f"Unknown format: {name!r}. Available: {available}"
            ) from None

    def names(self) -> list[str]:
        """Return the names of all registered formats (insertion order).

        Returns:
            A new list so callers can mutate it freely.
        """
        self._ensure_discovered()
        assert self._plugins is not None
        return list(self._plugins)

    def reset(self) -> None:
        """Invalidate the cache so the next access re-discovers plugins.

        Mainly useful in tests.
        """
        self._plugins = None
