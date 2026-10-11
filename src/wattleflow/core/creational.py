# Module name: core/creational.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from .framework import IWattleflow

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

__all__ = [
    "IFactory",
    "IBuilder",
    "ICreator",
    "IProduct",
    "IPrototype",
]

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
Product = TypeVar("Product")  # built product type
Prototype = TypeVar("Prototype", bound="IPrototype")  # clone self-type
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #
# Singleton is intentionally not expressed as an interface: it is a
# construction policy (module-level instance, metaclass or __new__), not a
# behavioural contract. Abstract Factory is likewise not a single interface:
# a concrete family factory exposes one creation method per product type,
# which a generic contract cannot name in advance.


# IFactory (IFactory) - Simple (static) Factory interface
class IFactory(IWattleflow, ABC):
    """
    IFactory - Simple (static) Factory abstract interface.

    Creates objects without exposing their concrete classes. create() is a
    static factory: it receives all inputs as keyword arguments and holds no
    instance state (a deliberate constraint — a stateful/configurable factory
    would need an instance method instead). The return type stays Any because
    a static method cannot bind a class-level type parameter.

    Interface:
        create(**kwargs: Any) -> Any  (staticmethod)
    """

    __slots__ = ()

    @staticmethod
    @abstractmethod
    def create(**kwargs: Any) -> Any: ...


# IBuilder (IBuilder) - Builder interface
class IBuilder(IWattleflow, Generic[Product], ABC):
    """
    IBuilder - Builder abstract interface.

    Assembles a complex object step by step; build() returns the finished
    product. Parameterised over Product for output type safety.

    Interface:
        build() -> Product

    Note:
        Only build() is part of this contract. Concrete builders typically add
        step methods (e.g. make_part_a / make_part_b) and combine them inside
        build(); promote those to abstract methods only if every builder must
        implement them. No Director role is defined: build() owns the order
        of steps.
    """

    __slots__ = ()

    @abstractmethod
    def build(self) -> Product: ...


# ICreator (ICreator, IProduct) - Factory Method interfaces
class ICreator(IWattleflow, ABC):
    """
    ICreator - Factory Method (creator role) abstract interface.

    Declares factory_method, which returns a product; subclasses decide which
    concrete product to instantiate.

    Interface:
        factory_method() -> IProduct
    """

    __slots__ = ()

    @abstractmethod
    def factory_method(self) -> IProduct: ...


class IProduct(IWattleflow, ABC):
    """
    IProduct - Factory Method (product role) abstract interface.

    The object produced by an ICreator's factory_method.

    Interface:
        operation() -> Any
    """

    __slots__ = ()

    @abstractmethod
    def operation(self) -> Any: ...


# IPrototype (IPrototype) - Prototype interface
class IPrototype(IWattleflow, ABC):
    """
    IPrototype - Prototype abstract interface.

    Creates new objects by cloning an existing instance rather than
    constructing from scratch. clone() returns the same type as the instance
    it is called on (bound self-type), so subclasses need not re-annotate it.

    Interface:
        clone() -> Self
    """

    __slots__ = ()

    @abstractmethod
    def clone(self: Prototype) -> Prototype: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
