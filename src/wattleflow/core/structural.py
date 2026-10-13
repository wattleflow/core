# Module name: core/structural.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Hashable
from typing import Any, Generic, TypeVar

from .framework import IWattleflow

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

__all__ = [
    "IAdaptee",
    "ITarget",
    "IAdapter",
    "IImplementor",
    "IAbstraction",
    "IComponent",
    "IComposite",
    "IDecorator",
    "IFacade",
    "IFlyweight",
    "IFlyweightFactory",
    "ISubject",
    "IProxy",
]

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
Adaptee = TypeVar("Adaptee")  # wrapped foreign object type   [NFRQ-ORG-03]
Element = TypeVar("Element")  # part-whole element type      [NFRQ-ORG-03]
Extrinsic = TypeVar("Extrinsic")  # flyweight extrinsic state    [NFRQ-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# Adapter
class IAdaptee(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def specific_request(self) -> Any: ...


class ITarget(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def request(self) -> Any: ...


class IAdapter(IWattleflow, Generic[Adaptee], ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def adaptee(self) -> Adaptee: ...


# Bridge
class IImplementor(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def operation_impl(self) -> Any: ...


class IAbstraction(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def operation(self) -> Any: ...


# Composite
class IComponent(IWattleflow, Generic[Element], ABC):
    __slots__ = ()

    @abstractmethod
    def operation(self, data: Element) -> None: ...


class IComposite(IComponent[Element], ABC):
    __slots__ = ()

    @abstractmethod
    def add(self, component: IComponent[Element]) -> None: ...

    @abstractmethod
    def remove(self, component: IComponent[Element]) -> None: ...

    @abstractmethod
    def get_child(self, index: int) -> IComponent[Element]: ...


# Decorator
class IDecorator(IComponent[Element], ABC):
    __slots__ = ()

    @abstractmethod
    def set_component(self, component: IComponent[Element]) -> None: ...


# Facade
class IFacade(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def dispatch(self, action: Any) -> Any: ...


# Flyweight
class IFlyweight(IWattleflow, Generic[Extrinsic], ABC):
    __slots__ = ()

    @abstractmethod
    def operation(self, extrinsic_state: Extrinsic) -> None: ...


class IFlyweightFactory(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def get_flyweight(self, key: Hashable) -> IFlyweight[Any]: ...


# Proxy
class ISubject(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def request(self) -> Any: ...


class IProxy(ISubject, ABC):
    __slots__ = ()


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
