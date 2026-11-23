"""Typed dependency injection container (GetIt equivalent)."""

from collections.abc import Callable
from typing import cast

type _Key = tuple[type[object], str | None]


class Container:
    """Service locator keyed by interface type and optional instance name.

    Use ``register_*`` only from ``presentation/di`` modules and ``di.py``; everything else
    receives dependencies through constructors or reads them via ``<feature>_getters.py``.
    """

    _NOT_REGISTERED = "{key} is not registered"
    _ALREADY_REGISTERED = "{key} is already registered"
    _NAMED_KEY = "{interface} (name={name!r})"

    def __init__(self) -> None:
        self._singletons: dict[_Key, object] = {}
        self._lazy: dict[_Key, Callable[[], object]] = {}
        self._factories: dict[_Key, Callable[[], object]] = {}

    def register_singleton[T](
        self, interface: type[T], instance: T, *, name: str | None = None
    ) -> None:
        """Register an eagerly created instance shared by every ``get`` call."""
        key = self._new_key(interface, name)
        self._singletons[key] = instance

    def register_lazy_singleton[T](
        self, interface: type[T], factory: Callable[[], T], *, name: str | None = None
    ) -> None:
        """Register a factory that runs once, on the first ``get`` call."""
        key = self._new_key(interface, name)
        self._lazy[key] = factory

    def register_factory[T](
        self, interface: type[T], factory: Callable[[], T], *, name: str | None = None
    ) -> None:
        """Register a factory that creates a new instance on every ``get`` call."""
        key = self._new_key(interface, name)
        self._factories[key] = factory

    def get[T](self, interface: type[T], *, name: str | None = None) -> T:
        """Return the registered instance for ``interface`` (and ``name``).

        Raises:
            LookupError: If nothing is registered under that key.
        """
        key: _Key = (interface, name)
        if key in self._singletons:
            return cast(T, self._singletons[key])
        if key in self._lazy:
            instance = self._lazy.pop(key)()
            self._singletons[key] = instance
            return cast(T, instance)
        if key in self._factories:
            return cast(T, self._factories[key]())
        raise LookupError(self._NOT_REGISTERED.format(key=self._describe(key)))

    def is_registered(self, interface: type[object], *, name: str | None = None) -> bool:
        """Return True when ``interface`` (and ``name``) has a registration."""
        key: _Key = (interface, name)
        return key in self._singletons or key in self._lazy or key in self._factories

    def reset(self) -> None:
        """Drop every registration (used by ``register_and_init`` and tests)."""
        self._singletons.clear()
        self._lazy.clear()
        self._factories.clear()

    def _new_key(self, interface: type[object], name: str | None) -> _Key:
        if self.is_registered(interface, name=name):
            raise ValueError(self._ALREADY_REGISTERED.format(key=self._describe((interface, name))))
        return (interface, name)

    @classmethod
    def _describe(cls, key: _Key) -> str:
        interface, name = key
        if name is None:
            return interface.__qualname__
        return cls._NAMED_KEY.format(interface=interface.__qualname__, name=name)


container = Container()
"""The application container. Import it only in ``presentation/di`` modules and ``di.py``."""
