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
Element = TypeVar("Element")  # part-whole element type      [NFRQ-ORG-03]
Extrinsic = TypeVar("Extrinsic")  # flyweight extrinsic state    [NFRQ-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #

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
    its own type and return self).

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

    The interface the client expects (e.g. a Facade). ITarget and IAdapter are
    deliberately separate contracts: an implementation may satisfy ITarget by
    delegating to an IAdaptee, directly or through an IAdapter, without
    exposing the adaptee to the client.

    Interface:
        request() -> Any
    """

    __slots__ = ()

    @abstractmethod
    def request(self) -> Any: ...


class IAdapter(IWattleflow, ABC):
    """
    IAdapter - Adapter (adapter role) abstract interface.

    Wraps an IAdaptee. Adapter and Target are deliberately separate: the
    ITarget (e.g. a Facade) is what clients call; an adapter's own contract
    is only that it exposes the adaptee it wraps. How the adaptee is stored
    (constructor injection, lazy resolution, ...) is an implementation
    decision.

    Implement it only to wrap a FOREIGN (non-IAdaptee) object, with real
    per-type translation.

    Interface:
        adaptee -> IAdaptee  (read-only property)
    """

    __slots__ = ()

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

    __slots__ = ()

    @abstractmethod
    def operation_impl(self) -> None: ...


class IAbstraction(IWattleflow, ABC):
    """
    IAbstraction - Bridge (abstraction role) abstract interface.

    The abstraction side of a Bridge. The contract declares only operation();
    how an implementation holds and delegates to its IImplementor is left to
    the concrete class.

    Interface:
        operation() -> None
    """

    __slots__ = ()

    @abstractmethod
    def operation(self) -> None: ...


# IComponent (IComponent, IComposite) - Composite interfaces
class IComponent(IWattleflow, Generic[Element], ABC):
    """
    IComponent - Composite (component role) abstract interface.

    The common contract for leaves and composites, so clients can treat
    individual elements and part-whole hierarchies uniformly.

    Interface:
        process(data: Element) -> None
    """

    __slots__ = ()

    @abstractmethod
    def process(self, data: Element) -> None: ...


class IComposite(IComponent[Element], ABC):
    """
    IComposite - Composite (composite role) abstract interface.

    A component that holds child components and typically forwards process()
    to them.

    Interface:
        process(data: Element) -> None   (inherited)
        add(component: IComponent[Element]) -> None
        remove(component: IComponent[Element]) -> None
        get_child(index: int) -> IComponent[Element]
    """

    __slots__ = ()

    @abstractmethod
    def add(self, component: IComponent[Element]) -> None: ...

    @abstractmethod
    def remove(self, component: IComponent[Element]) -> None: ...

    @abstractmethod
    def get_child(self, index: int) -> IComponent[Element]: ...


# IDecorator - Decorator interface
class IDecorator(IComponent[Element], ABC):
    """
    IDecorator - Decorator abstract interface.

    A component that wraps another component and adds behaviour around its
    process() while keeping the same interface.

    Interface:
        process(data: Element) -> None   (inherited)
        set_component(component: IComponent[Element]) -> None
    """

    __slots__ = ()

    @abstractmethod
    def set_component(self, component: IComponent[Element]) -> None: ...


# IFacade - Facade interface
class IFacade(IWattleflow, ABC):
    """
    IFacade - Facade abstract interface.

    A single simplified entry point over a more complex subsystem.

    Interface:
        operation(action: Any) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def operation(self, action: Any) -> Any: ...


# IFlyweight (IFlyweight, IFlyweightFactory) - Flyweight interfaces
class IFlyweight(IWattleflow, Generic[Extrinsic], ABC):
    """
    IFlyweight - Flyweight abstract interface.

    A shared object holding intrinsic state only; context-dependent
    (extrinsic) state is passed in by the client on each call.

    Interface:
        operation(extrinsic_state: Extrinsic) -> None
    """

    __slots__ = ()

    @abstractmethod
    def operation(self, extrinsic_state: Extrinsic) -> None: ...


class IFlyweightFactory(IWattleflow, ABC):
    """
    IFlyweightFactory - Flyweight (factory role) abstract interface.

    Returns a shared flyweight for a key, creating it once and reusing it
    thereafter. The extrinsic state type is left open (IFlyweight[Any]) so the
    factory is not bound to a single flyweight type.

    Interface:
        get_flyweight(key: Hashable) -> IFlyweight[Any]
    """

    __slots__ = ()

    @abstractmethod
    def get_flyweight(self, key: Hashable) -> IFlyweight[Any]: ...


# ISubject (ISubject, IProxy) - Proxy interfaces
class ISubject(IWattleflow, ABC):
    """
    ISubject - Proxy (subject role) abstract interface.

    The common contract of the real subject and its proxy, so a proxy can be
    used wherever the real subject is expected.

    Interface:
        request() -> Any
    """

    __slots__ = ()

    @abstractmethod
    def request(self) -> Any: ...


class IProxy(ISubject, ABC):
    """
    IProxy - Proxy abstract interface.

    Stands in for a real ISubject, controlling access to it (e.g. lazy loading,
    access control, remoting). How the real subject is held or resolved is an
    implementation decision.

    Interface:
        request() -> Any   (inherited)
    """

    __slots__ = ()


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
