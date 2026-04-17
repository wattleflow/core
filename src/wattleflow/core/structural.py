# Module name: core/structural.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence


from __future__ import annotations
from abc import abstractmethod, ABC
from typing import Any, Generic
from .framework import IWattleflow, T


__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"


# IAdaptee (IAdaptee, IAdapter, ITarget) - Adapter interfaces
class IAdaptee(IWattleflow, ABC):
    def specific_request(self) -> "IAdaptee":
        return self


class ITarget(IWattleflow, ABC):
    @abstractmethod
    def request(self) -> IAdaptee: ...


class IAdapter(IWattleflow, ABC):
    def __init__(self, adaptee: IAdaptee):
        super().__init__()
        self._adaptee = adaptee


# IImplementor (IImplementor, IAbstraction) - Bridge interfaces
class IImplementor(IWattleflow, ABC):
    @abstractmethod
    def operation_impl(self) -> None: ...


class IAbstraction(IWattleflow, ABC):
    @abstractmethod
    def operation(self) -> None: ...


# ICompoenent (IComponent, IComposite) - Composite interface
class IComponent(IWattleflow, Generic[T], ABC):
    @abstractmethod
    def process(self, data: T) -> None: ...


class IComposite(IComponent[T], Generic[T], ABC):
    @abstractmethod
    def add(self, component: IComponent[T]) -> None: ...

    @abstractmethod
    def remove(self, component: IComponent[T]) -> None: ...

    @abstractmethod
    def get_child(self, index: int) -> IComponent[T]: ...


# IDecorator
class IDecorator(IComponent[T], Generic[T], ABC):
    @abstractmethod
    def set_component(self, component: IComponent[T]) -> None: ...


# IFacade
class IFacade(IWattleflow, ABC):
    @abstractmethod
    def operation(self, action: Any) -> Any:
        pass


# IFlyweight (IFlyweight, IFlyweightFactory)
class IFlyweight(IWattleflow, Generic[T], ABC):
    @abstractmethod
    def operation(self, extrinsic_state: T) -> None: ...


class IFlyweightFactory(IWattleflow, ABC):
    @abstractmethod
    def get_flyweight(self, key: str) -> Any: ...


# Proxy interface
class IProxy(IWattleflow, ABC):
    @abstractmethod
    def request(self) -> Any: ...
