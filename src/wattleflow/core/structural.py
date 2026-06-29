# Module name: core/structural.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations
from abc import abstractmethod, ABC
from typing import Any, Generic
from .framework import IWattleflow, T
# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
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

    The object an ITarget client reaches through a wrapper. By design
    specific_request returns the adaptee itself (identity): a wrapper calls it to
    obtain the underlying object and then delegates to it. The concrete
    `return self` is intentional — its known subclasses (Document, Wattle) follow
    the same identity contract — not a placeholder.

    Interface:
        specific_request() -> IAdaptee   # concrete default; returns self (identity)
    """

    # Holds no instance state of its own; an empty slot tuple keeps the
    # ISignal → IAdaptee → IWattleflow chain dict-free (see ISignal.__slots__).
    __slots__ = ()

    def specific_request(self) -> "IAdaptee":
        return self


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
    IAdapter - Adapter (adapter role) base.

    Holds the wrapped IAdaptee. Adapter and Target are kept deliberately
    separate: the ITarget (e.g. a Facade) is what clients call, while an adapter
    only stores the adaptee — so this base does not inherit ITarget or declare
    request(). Concrete base, not abstract.

    Currently a catalog interface with no implementations: the document layer
    delegates to the adaptee directly (see concrete/document.py), so no adapter
    is needed while every adaptee already conforms to IAdaptee. Reintroduce a
    concrete adapter only to wrap a FOREIGN (non-IAdaptee) object, with real
    per-type translation in request().
    """

    def __init__(self, adaptee: IAdaptee) -> None:
        super().__init__()
        self._adaptee = adaptee


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
class IComponent(IWattleflow, Generic[T], ABC):
    """
    IComponent - Composite (component role) abstract interface.

    Common interface for both leaves and composites in a part-whole tree.

    Interface:
        process(data: T) -> None
    """

    @abstractmethod
    def process(self, data: T) -> None: ...


class IComposite(IComponent[T], Generic[T], ABC):
    """
    IComposite - Composite (composite role) abstract interface.

    A component that contains children and manages them uniformly with leaves.

    Interface:
        add(component: IComponent[T]) -> None
        remove(component: IComponent[T]) -> None
        get_child(index: int) -> IComponent[T]

    Note:
        `Generic[T]` is redundant here — IComponent[T] already parameterises the
        class over T — kept only for stylistic symmetry; harmless.
    """

    @abstractmethod
    def add(self, component: IComponent[T]) -> None: ...

    @abstractmethod
    def remove(self, component: IComponent[T]) -> None: ...

    @abstractmethod
    def get_child(self, index: int) -> IComponent[T]: ...


# IDecorator
class IDecorator(IComponent[T], Generic[T], ABC):
    """
    IDecorator - Decorator abstract interface.

    Wraps an IComponent to add behaviour while preserving its interface.

    Interface:
        set_component(component: IComponent[T]) -> None

    Note:
        `Generic[T]` is redundant alongside IComponent[T]; kept for symmetry.
    """

    @abstractmethod
    def set_component(self, component: IComponent[T]) -> None: ...


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


# IFlyweight (IFlyweight, IFlyweightFactory)
class IFlyweight(IWattleflow, Generic[T], ABC):
    """
    IFlyweight - Flyweight abstract interface.

    A shared object holding intrinsic state; extrinsic state is supplied per
    call so many contexts can share one instance.

    Interface:
        operation(extrinsic_state: T) -> None
    """

    @abstractmethod
    def operation(self, extrinsic_state: T) -> None: ...


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
