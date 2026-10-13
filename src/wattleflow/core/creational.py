# Module name: core/creational.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Self, TypeVar

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
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #
# Singleton and Abstract Factory are intentionally not expressed as interfaces.


# Simple (static) Factory
class IFactory(IWattleflow, ABC):
    __slots__ = ()

    @staticmethod
    @abstractmethod
    def create(**kwargs: Any) -> Any:
        # A static factory is never instantiated, so ABC cannot enforce the
        # override; fail loudly instead of returning None.
        raise NotImplementedError("IFactory.create must be overridden.")


# Builder
class IBuilder(IWattleflow, Generic[Product], ABC):
    __slots__ = ()

    @abstractmethod
    def build(self) -> Product: ...


# Factory Method
class ICreator(IWattleflow, Generic[Product], ABC):
    __slots__ = ()

    @abstractmethod
    def factory_method(self) -> Product: ...


class IProduct(IWattleflow, ABC):
    __slots__ = ()


# Prototype
class IPrototype(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def clone(self) -> Self: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
