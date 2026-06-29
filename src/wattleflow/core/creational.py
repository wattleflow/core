# Module name: core/creational.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations
import functools
import inspect
import threading
from typing import Any
from abc import abstractmethod, ABC
from .framework import IWattleflow
# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# Creational design patterns
# Abstract Factory Interface
class IFactory(IWattleflow, ABC):
    """
    IFactory - Abstract Factory abstract interface.

    Creates objects without exposing their concrete classes. create() is a
    static factory: it receives all inputs as keyword arguments and holds no
    instance state (a deliberate constraint — a stateful/configurable factory
    would need an instance method instead).

    Interface:
        create(**kwargs) -> Any  (staticmethod)
    """

    @staticmethod
    @abstractmethod
    def create(**kwargs) -> Any: ...


# Builder
class IBuilder(IWattleflow, ABC):
    """
    IBuilder - Builder abstract interface.

    Assembles a complex object step by step; build() returns the finished
    product.

    Interface:
        build() -> Any

    Note:
        Only build() is part of this contract. Concrete builders typically add
        step methods (e.g. make_part_a / make_part_b) and combine them inside
        build(); promote those to abstract methods only if every builder must
        implement them.
    """

    @abstractmethod
    def build(self) -> Any: ...


# Factory Method Interface (ICreator, IProduct)
class IProduct(IWattleflow, ABC):
    """
    IProduct - Factory Method (product role) abstract interface.

    The object produced by an ICreator's factory_method.

    Interface:
        operation() -> Any
    """

    @abstractmethod
    def operation(self) -> Any: ...


class ICreator(IWattleflow, ABC):
    """
    ICreator - Factory Method (creator role) abstract interface.

    Declares factory_method, which returns a product; subclasses decide which
    concrete product to instantiate.

    Interface:
        factory_method() -> IProduct
    """

    @abstractmethod
    def factory_method(self) -> "IProduct": ...


# Prototype Interface
class IPrototype(IWattleflow, ABC):
    """
    IPrototype - Prototype abstract interface.

    Creates new objects by cloning an existing instance rather than
    constructing from scratch.

    Interface:
        clone() -> IPrototype
    """

    @abstractmethod
    def clone(self) -> "IPrototype": ...


# Singleton Interface
class ISingleton(IWattleflow, ABC):
    """
    ISingleton - Singleton base (concrete base, not a pure interface).

    Caches exactly one instance per concrete subclass; abstract subclasses are
    never cached (see the inspect.isabstract guard in __new__). Construction is
    thread-safe via a per-subclass lock, and each subclass's __init__ runs
    exactly once for its cached instance (init-once guard installed in
    __init_subclass__).

    Interface:
        __new__(cls, *args, **kwargs) -> cached instance per concrete subclass

    Design notes:
      * INIT-ONCE: Python calls __init__ after __new__ on every construction.
        The guard wraps each subclass __init__ so it runs only when the cached
        instance is first built; later constructions return the same instance
        without re-running __init__, so state is not clobbered. Validated in
        tools/singleton_audit.py selftest.
      * The guard is installed via __init_subclass__ (no metaclass surgery),
        preserving the ABCMeta metaclass inherited from ABC.
      * Each subclass receives its own _lock, so first construction of unrelated
        singletons does not serialise on one shared lock.
      * ISingleton itself is now instantiable (the previously abstract __init__
        was dropped); it is a base and not meant to be constructed directly, but
        doing so is harmless.
      * The init-once flag is stored as an instance attribute (_wf_initialized).
        A concrete singleton using __slots__ must include that slot, or omit
        __slots__, for the guard to work.
    """

    _instances: dict = {}
    _lock = threading.Lock()  # base lock; each subclass gets its own (see below)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Per-class lock removes contention between unrelated singletons.
        cls._lock = threading.Lock()
        # Install an init-once guard around the subclass's own __init__, if any.
        original = cls.__dict__.get("__init__")
        if original is None or getattr(original, "_wf_singleton_wrapped", False):
            return

        @functools.wraps(original)
        def guarded(self, *args, **kwargs):
            if getattr(self, "_wf_initialized", False):
                return
            original(self, *args, **kwargs)
            object.__setattr__(self, "_wf_initialized", True)

        guarded._wf_singleton_wrapped = True
        cls.__init__ = guarded

    def __new__(cls, *args, **kwargs):
        # Abstract classes are never cached (and cannot be instantiated anyway).
        if inspect.isabstract(cls):
            return super().__new__(cls)

        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
