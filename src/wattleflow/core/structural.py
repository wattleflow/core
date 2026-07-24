# Module name: core/structural.py
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

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
Element = TypeVar("Element")  # part-whole element type      [NFR-ORG-03]
Extrinsic = TypeVar("Extrinsic")  # flyweight extrinsic state    [NFR-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# IAdaptee (IAdaptee, ITarget, IAdapter) - Adapter interfaces
class IAdaptee(IWattleflow, ABC):
    """
    IAdaptee - Adapter (adaptee role) abstract interface.

    The object a client reaches through a wrapper. specific_request() yields
    what the adaptee offers to the wrapping side; the return type is Any at
    the contract level and subclasses narrow it covariantly (IDocument and
    ISignal narrow to their content type; an identity adaptee may narrow to
    its own type and return self). The former concrete identity default
    (`return self`) was an implementation policy and now lives with concrete
    identity adaptees (ADR-009).

    Interface:
        specific_request() -> Any
    """

    # Holds no instance state; empty slots keep slotted subclass chains
    # (ISignal → IAdaptee → IWattleflow) dict-free.
    __slots__ = ()

    @abstractmethod
    def specific_request(self) -> Any: ...


class ITarget(IWattleflow, ABC):
    """
    ITarget - Adapter (target role) abstract interface.

    The interface the client expects; an IAdapter implements it by delegating to
    an IAdaptee.

    Interface:
        request() -> IAdaptee
    """

    @abstractmethod
    def request(self) -> IAdaptee: ...


class IAdapter(IWattleflow, ABC):
    """
    IAdapter - Adapter (adapter role) abstract interface.

    Wraps an IAdaptee. Adapter and Target are deliberately separate: the
    ITarget (e.g. a Facade) is what clients call; an adapter's own contract
    is only that it exposes the adaptee it wraps. How the adaptee is stored
    (constructor injection, lazy resolution, ...) is an implementation
    decision.

    Currently a catalog interface with no implementations: the document
    layer delegates to the adaptee directly (see concrete/document.py).
    Implement it only to wrap a FOREIGN (non-IAdaptee) object, with real
    per-type translation.

    Interface:
        adaptee -> IAdaptee  (read-only property)
    """

    @property
    @abstractmethod
    def adaptee(self) -> IAdaptee: ...


# IImplementor (IImplementor, IAbstraction) - Bridge interfaces
class IImplementor(IWattleflow, ABC):
    """
    IImplementor - Bridge (implementor role) abstract interface.

    The implementation side of a Bridge; an IAbstraction delegates to it,
    letting abstraction and implementation vary independently.

    Interface:
        operation_impl() -> None
    """

    @abstractmethod
    def operation_impl(self) -> None: ...


class IAbstraction(IWattleflow, ABC):
    """
    IAbstraction - Bridge (abstraction role) abstract interface.

    The abstraction side of a Bridge; its operation is defined in terms of an
    IImplementor.

    Interface:
        operation() -> None
    """

    @abstractmethod
    def operation(self) -> None: ...


# IComponent (IComponent, IComposite) - Composite interface
class IComponent(IWattleflow, Generic[Element], ABC):
    ...

    @abstractmethod
    def process(self, data: Element) -> None: ...


class IComposite(IComponent[Element], ABC):
    ...

    @abstractmethod
    def add(self, component: IComponent[Element]) -> None: ...
    @abstractmethod
    def remove(self, component: IComponent[Element]) -> None: ...
    @abstractmethod
    def get_child(self, index: int) -> IComponent[Element]: ...


class IDecorator(IComponent[Element], ABC):
    ...

    @abstractmethod
    def set_component(self, component: IComponent[Element]) -> None: ...


# IFacade
class IFacade(IWattleflow, ABC):
    """
    IFacade - Facade abstract interface.

    A single simplified entry point over a more complex subsystem.

    Interface:
        operation(action: Any) -> Any
    """

    @abstractmethod
    def operation(self, action: Any) -> Any: ...


class IFlyweight(IWattleflow, Generic[Extrinsic], ABC):
    ...

    @abstractmethod
    def operation(self, extrinsic_state: Extrinsic) -> None: ...


class IFlyweightFactory(IWattleflow, ABC):
    """
    IFlyweightFactory - Flyweight (factory role) abstract interface.

    Returns a shared flyweight for a key, creating it once and reusing it
    thereafter. (Conventionally returns an IFlyweight; typed as Any here to
    avoid binding the factory to a single flyweight type.)

    Interface:
        get_flyweight(key: str) -> Any
    """

    @abstractmethod
    def get_flyweight(self, key: str) -> Any: ...


# Proxy interface
class IProxy(IWattleflow, ABC):
    """
    IProxy - Proxy abstract interface.

    Stands in for another object, controlling access to it (e.g. lazy loading,
    access control, remoting).

    Interface:
        request() -> Any
    """

    @abstractmethod
    def request(self) -> Any: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
