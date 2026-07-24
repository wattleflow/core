# Module name: core/creational.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

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
    would need an instance method instead; see ADR-004).

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


class IProduct(IWattleflow, ABC):
    """
    IProduct - Factory Method (product role) abstract interface.

    The object produced by an ICreator's factory_method.

    Interface:
        operation() -> Any
    """

    @abstractmethod
    def operation(self) -> Any: ...


# Prototype Interface
class IPrototype(IWattleflow, ABC):
    """
    IPrototype - Prototype abstract interface.

    Creates new objects by cloning an existing instance rather than
    constructing from scratch.

    Note:
        clone() is annotated "IPrototype" rather than typing.Self because the
        supported minimum is Python 3.10 (Self lands in 3.11). Reintroduce
        Self by ADR when the minimum rises — stronger subclass typing at
        zero runtime cost.

    Interface:
        clone() -> IPrototype
    """

    @abstractmethod
    def clone(self) -> "IPrototype": ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
