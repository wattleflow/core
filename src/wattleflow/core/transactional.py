# Module name: core/transactional.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Generic, TypeVar

from .framework import IWattleflow
from .structural import IAdaptee, ITarget

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

__all__ = [
    "IDocument",
    "IDriver",
    "IConfig",
    "IParser",
    "IFormatter",
    "ISignal",
    "IEvent",
    "IEventListener",
    "IEventSource",
    "IRepository",
    "IBlackboard",
    "IModule",
    "IPipeline",
    "IProcessor",
    "IQuery",
    "ISaga",
    "IUnitOfWork",
    "IScheduler",
]

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
Content = TypeVar("Content")  # document/signal payload type      [NFRQ-ORG-03]
Entity = TypeVar("Entity")  # unit-of-work tracked entity type    [NFRQ-ORG-03]
Event = TypeVar("Event")  # emitted/handled event type            [NFRQ-ORG-03]
Item = TypeVar("Item")  # processor work item type                [NFRQ-ORG-03]
Result = TypeVar("Result")  # query result type                   [NFRQ-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# IDocument (IDocument) - Document interface
class IDocument(IAdaptee, Generic[Content], ABC):
    """
    IDocument - Document abstract interface.

    A mutable adaptee that carries a typed payload. specific_request() narrows
    the IAdaptee return type to Content; update_content() replaces it.

    Interface:
        specific_request() -> Content
        update_content(content: Content) -> None
    """

    __slots__ = ()

    @abstractmethod
    def update_content(self, content: Content) -> None: ...

    @abstractmethod
    def specific_request(self) -> Content: ...


# IDriver (IDriver) - Resource driver interface
class IDriver(IWattleflow, ABC):
    """
    IDriver - Resource driver abstract interface.

    Manages the lifecycle of an external resource (load() acquires it,
    close() releases it) and reads from or writes to it by URI. metadata()
    describes the driver at the class level.

    Interface:
        load() -> None
        close() -> None
        read(uri: str, **kwargs: Any) -> Any
        write(uri: str, **kwargs: Any) -> Any
        metadata() -> Any  (classmethod)
    """

    __slots__ = ()

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def read(self, uri: str, **kwargs: Any) -> Any: ...

    @abstractmethod
    def write(self, uri: str, **kwargs: Any) -> Any: ...

    @classmethod
    @abstractmethod
    def metadata(cls) -> Any: ...


# IConfig - declarative side of the same boundary: settings, not payload
class IConfig(IWattleflow, ABC):
    """
    IConfig - Read-only hierarchical configuration source.

    The contract every configuration carries: resolve a path of keys to a
    value, or yield the caller's default when the path is absent. It fixes no
    serialisation format, no file, and no resolution policy — a document on
    disk, an in-memory mapping and a secret-resolving adapter all satisfy it,
    which is what lets a consumer state its need without naming a format.

    Absence is answered with `default`, never by raising: configuration
    lookups sit on the construction path, where an exception per missing
    optional key would make every consumer defensive.

    Interface:
        find(*keys: str, default: Any = None) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def find(self, *keys: str, default: Any = None) -> Any: ...


# IParser / IFormatter - format side of the I/O boundary opened by IDriver
class IParser(IWattleflow, Generic[Content], ABC):
    """
    IParser - Deserialisation abstract interface.

    A Strategy specialisation at the I/O boundary: turns a serialised source
    into a domain object. The contract fixes no transport — what a source is
    (open stream, path, in-memory payload) and how it is obtained is the
    implementation's policy, not the interface's. Not an Interpreter: the
    catalogue excludes parsing from that pattern, and no grammar or composite
    expression tree is implied here.

    Interface:
        parse(**kwargs: Any) -> Content
    """

    __slots__ = ()

    @abstractmethod
    def parse(self, **kwargs: Any) -> Content: ...


class IFormatter(IWattleflow, Generic[Content], ABC):
    """
    IFormatter - Serialisation abstract interface.

    The write-side counterpart of IParser: produces a payload from the inputs
    passed as keyword arguments. The caller owns the sink, so render() returns
    the payload and writes nothing. As with IParser, the contract fixes no
    transport. The Content parameter pairs a formatter with an IParser of the
    same type; it does not appear in the render() signature.

    Interface:
        render(**kwargs: Any) -> bytes | str
    """

    __slots__ = ()

    @abstractmethod
    def render(self, **kwargs: Any) -> bytes | str: ...


# ISignal (ISignal) - Signal interface
class ISignal(IAdaptee, Generic[Content], ABC):
    """
    ISignal - Signal abstract interface.

    An immutable adaptee that carries a typed payload. specific_request()
    narrows the IAdaptee return type to Content.

    Interface:
        specific_request() -> Content
    """

    __slots__ = ()

    @abstractmethod
    def specific_request(self) -> Content: ...


# IEvent - (IEvent, IEventListener, IEventSource) - Event-Driven
class IEvent(IWattleflow, ABC):
    """
    IEvent - Event-Driven (event) abstract interface.

    An immutable description of something that happened: identity, optional
    correlation/source, timestamp, type and payload.

    Interface:
        correlation_id -> str | None   (property)
        id -> str                      (property)
        source -> str | None           (property)
        timestamp -> datetime          (property)
        type -> str                    (property)
        payload -> dict[str, Any]      (property)
    """

    __slots__ = ()

    @property
    @abstractmethod
    def correlation_id(self) -> str | None: ...

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def source(self) -> str | None: ...

    @property
    @abstractmethod
    def timestamp(self) -> datetime: ...

    @property
    @abstractmethod
    def type(self) -> str: ...

    @property
    @abstractmethod
    def payload(self) -> dict[str, Any]: ...


class IEventListener(IWattleflow, Generic[Event], ABC):
    """
    IEventListener - Event-Driven (listener role) abstract interface.

    Reacts to events delivered by an IEventSource. Generic over the same Event
    type as its source, so a source and its listeners agree on the event type.

    Interface:
        on_event(event: Event) -> None
    """

    __slots__ = ()

    @abstractmethod
    def on_event(self, event: Event) -> None: ...


class IEventSource(IWattleflow, Generic[Event], ABC):
    """
    IEventSource - Event-Driven (source role) abstract interface.

    Registers and unregisters listeners and emits events to them. Generic over
    the emitted Event type; **kwargs carries emission metadata so subclasses
    need no widening override.

    Interface:
        register_listener(listener: IEventListener[Event]) -> None
        unregister_listener(listener: IEventListener[Event]) -> None
        emit_event(event: Event, **kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def register_listener(self, listener: IEventListener[Event]) -> None: ...

    @abstractmethod
    def unregister_listener(self, listener: IEventListener[Event]) -> None: ...

    @abstractmethod
    def emit_event(self, event: Event, **kwargs: Any) -> None: ...


# IRepository (IRepository) - Repository interface
class IRepository(IWattleflow, ABC):
    """
    IRepository - Repository abstract interface.

    Collection-like persistence boundary: counts, clears, reads by identifier
    and writes target facades.

    Interface:
        count -> int  (property)
        clear() -> None
        read(identifier: str, *args: Any, **kwargs: Any) -> ITarget
        write(facade: ITarget, *args: Any, **kwargs: Any) -> bool
    """

    __slots__ = ()

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def read(self, identifier: str, *args: Any, **kwargs: Any) -> ITarget: ...

    @abstractmethod
    def write(self, facade: ITarget, *args: Any, **kwargs: Any) -> bool: ...


# IBlackboard - (IBlackboard, IModule) - Blackboard interfaces
class IBlackboard(IWattleflow, ABC):
    """
    IBlackboard - Blackboard (blackboard role) abstract interface.

    Shared workspace that modules read from and write to. Holds a canvas,
    registers repositories and mediates creation/lookup of target facades.
    The canvas is exposed read-only: modules change the blackboard only
    through create() and write().

    Interface:
        canvas -> Mapping[str, Any]  (property, read-only view)
        count -> int                 (property)
        clean() -> None
        create(caller: IWattleflow, *args: Any, **kwargs: Any) -> ITarget
        read(identifier: str) -> ITarget
        register(repository: IRepository) -> None
        write(caller: IWattleflow, facade: ITarget,
              *args: Any, **kwargs: Any) -> str
    """

    __slots__ = ()

    @property
    @abstractmethod
    def canvas(self) -> Mapping[str, Any]: ...

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clean(self) -> None: ...

    @abstractmethod
    def create(self, caller: IWattleflow, *args: Any, **kwargs: Any) -> ITarget: ...

    @abstractmethod
    def read(self, identifier: str) -> ITarget: ...

    @abstractmethod
    def register(self, repository: IRepository) -> None: ...

    @abstractmethod
    def write(
        self,
        caller: IWattleflow,
        facade: ITarget,
        *args: Any,
        **kwargs: Any,
    ) -> str: ...


class IModule(IWattleflow, ABC):
    """
    IModule - Blackboard (knowledge-source role) abstract interface.

    A knowledge source that inspects and updates the blackboard.

    Interface:
        update(blackboard: IBlackboard, *args: Any, **kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def update(self, blackboard: IBlackboard, *args: Any, **kwargs: Any) -> None: ...


# IPipeline (IPipeline) - Pipeline interface
class IPipeline(IWattleflow, ABC):
    """
    IPipeline - Pipeline abstract interface.

    Drives a target facade through a processor as one stage of processing.

    Interface:
        process(processor: IProcessor, facade: ITarget,
                *args: Any, **kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def process(
        self,
        processor: IProcessor,
        facade: ITarget,
        *args: Any,
        **kwargs: Any,
    ) -> None: ...


# IProcessor (IProcessor) - Processor interface
class IProcessor(IWattleflow, Generic[Item], ABC):
    """
    IProcessor - Processor abstract interface.

    Produces a generator of work items and starts processing them.

    Interface:
        create_generator() -> Item
        start() -> None

    Note (open): the parameter denotes the produced value; the
    return type of create_generator() is likely Iterator[Item] rather than
    Item. Decision deferred until GenericProcessor (workflow) is reviewed —
    the contract shape is preserved unchanged here.
    """

    __slots__ = ()

    @abstractmethod
    def create_generator(self) -> Item: ...

    @abstractmethod
    def start(self) -> None: ...


# IQuery (IQuery) - Query Object interface
class IQuery(IWattleflow, Generic[Result], ABC):
    """
    IQuery - Query Object abstract interface.

    Encapsulates a query that yields a typed result when executed.

    Interface:
        execute() -> Result
    """

    __slots__ = ()

    @abstractmethod
    def execute(self) -> Result: ...


# ISaga (ISaga) - Saga interface
class ISaga(IWattleflow, Generic[Event], ABC):
    """
    ISaga - Saga abstract interface.

    Coordinates a long-running transaction as a sequence of steps, compensating
    completed steps if a later one fails.

    Interface:
        start(initial_state: Any, *args: Any, **kwargs: Any) -> None
        handle_event(event: Event, *args: Any, **kwargs: Any) -> None
        compensate() -> None
    """

    __slots__ = ()

    @abstractmethod
    def start(self, initial_state: Any, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def handle_event(self, event: Event, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def compensate(self) -> None: ...


# IUnitOfWork (IUnitOfWork) - Unit of Work interface
class IUnitOfWork(IWattleflow, Generic[Entity], ABC):
    """
    IUnitOfWork - Unit of Work abstract interface.

    Tracks new/dirty/deleted entities within a business transaction and applies
    them atomically on commit (or discards them on rollback).

    Interface:
        commit() -> None
        rollback() -> None
        register_new(entity: Entity, *args: Any, **kwargs: Any) -> None
        register_dirty(entity: Entity, *args: Any, **kwargs: Any) -> None
        register_deleted(entity: Entity, *args: Any, **kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def register_new(self, entity: Entity, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def register_dirty(self, entity: Entity, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def register_deleted(self, entity: Entity, *args: Any, **kwargs: Any) -> None: ...


# IScheduler (IScheduler) - Scheduler / Orchestrator interface
# IScheduler is an IWattleflow through IEventSource; no direct base needed.
class IScheduler(IEventSource[Event], ABC):
    """
    IScheduler - Scheduler / Orchestrator abstract interface (Event-Driven source).

    Orchestrates execution of work and emits lifecycle events. A pure
    contract: the single-instance policy, if required, belongs on the
    concrete implementation (e.g. `class Scheduler(Wattleflow, IScheduler[Event],
    Singleton)`), not here.

    Interface:
        setup_orchestrator(*args: Any, **kwargs: Any) -> None
        start_orchestration(parallel: bool) -> None
        stop_orchestration() -> None
        (register_listener, unregister_listener, emit_event
         inherited from IEventSource[Event])
    """

    __slots__ = ()

    @abstractmethod
    def setup_orchestrator(self, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def start_orchestration(self, parallel: bool) -> None: ...

    @abstractmethod
    def stop_orchestration(self) -> None: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
