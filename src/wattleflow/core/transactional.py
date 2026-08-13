# Module name: core/transactional.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from .framework import IWattleflow
from .structural import IAdaptee, ITarget

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"


# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
Content = TypeVar("Content")  # document/signal payload type      [NFR-ORG-03]
Entity = TypeVar("Entity")  # unit-of-work tracked entity type  [NFR-ORG-03]
Event = TypeVar("Event")  # emitted/handled event type        [NFR-ORG-03]
Item = TypeVar("Item")  # processor work item type          [NFR-ORG-03]
Result = TypeVar("Result")  # query result type                 [NFR-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# Document
class IDocument(IAdaptee, Generic[Content], ABC):
    ...

    @abstractmethod
    def update_content(self, content: Content) -> None: ...
    @abstractmethod
    def specific_request(self) -> Content: ...


# IDriver
class IDriver(IWattleflow, ABC):
    """
    IDriver - Resource driver abstract interface.

    Manages the lifecycle of an external resource (open/close) and reads from or
    writes to it by URI. metadata() describes the driver at the class level.

    Interface:
        load() -> None
        close() -> None
        read(uri: str, **kwargs) -> Any
        write(uri: str, **kwargs) -> Any
        metadata() -> Any  (classmethod)
    """

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def read(self, uri: str, **kwargs) -> Any: ...

    @abstractmethod
    def write(self, uri: str, **kwargs) -> Any: ...

    @classmethod
    @abstractmethod
    def metadata(cls) -> Any: ...


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
        parse(**kwargs) -> Content
    """

    @abstractmethod
    def parse(self, **kwargs) -> Content: ...


class IFormatter(IWattleflow, Generic[Content], ABC):
    """
    IFormatter - Serialisation abstract interface.

    The write-side mirror of IParser: renders a domain object into a payload.
    The caller owns the sink, so render() returns the payload and writes
    nothing. As with IParser, the contract fixes no transport.

    Interface:
        render(**kwargs) -> bytes | str
    """

    @abstractmethod
    def render(self, **kwargs) -> bytes | str: ...


# Signal
class ISignal(IAdaptee, Generic[Content], ABC):
    ...

    @abstractmethod
    def specific_request(self) -> Content: ...


# IEvent - (IEvent, IEventListener, IEventSource) - Event-Driven
class IEvent(IWattleflow, ABC):
    """
    IEvent - Event-Driven (event) abstract interface.

    An immutable description of something that happened: identity, optional
    correlation/source, timestamp, type and payload.

    Interface:
        correlation_id -> Optional[str]  (property)
        id -> str                        (property)
        source -> Optional[str]          (property)
        timestamp -> datetime            (property)
        type -> str                      (property)
        payload -> Dict[str, Any]        (property)
    """

    @property
    @abstractmethod
    def correlation_id(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def source(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def timestamp(self) -> datetime: ...

    @property
    @abstractmethod
    def type(self) -> str: ...

    @property
    @abstractmethod
    def payload(self) -> Dict[str, Any]: ...


class IEventListener(IWattleflow, ABC):
    """
    IEventListener - Event-Driven (listener role) abstract interface.

    Reacts to events delivered by an IEventSource.

    Interface:
        on_event(event: IEvent) -> None
    """

    @abstractmethod
    def on_event(self, event: IEvent) -> None: ...


class IEventSource(IWattleflow, Generic[Event], ABC):
    """
    IEventSource - Event-Driven (source role) abstract interface.

    Registers listeners and emits events to them. Generic over the emitted
    Event type; **kwargs carries emission metadata (DR-COR-010) so subclasses
    need no widening override.

    Interface:
        register_listener(listener: IEventListener) -> None
        emit_event(event: Event, **kwargs) -> None
    """

    @abstractmethod
    def register_listener(self, listener: IEventListener) -> None: ...

    @abstractmethod
    def emit_event(self, event: Event, **kwargs) -> None: ...


# IRepository
class IRepository(IWattleflow, ABC):
    """
    IRepository - Repository abstract interface.

    Collection-like persistence boundary: counts, clears, reads by identifier
    and writes target facades.

    Interface:
        count -> int  (property)
        clear() -> None
        read(identifier: str, *args, **kwargs) -> ITarget
        write(facade: ITarget, *args, **kwargs) -> bool
    """

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def read(self, identifier: str, *args, **kwargs) -> ITarget: ...

    @abstractmethod
    def write(self, facade: ITarget, *args, **kwargs) -> bool: ...


# IBlackboard - (IBlackboard, IModule)
class IBlackboard(IWattleflow, ABC):
    """
    IBlackboard - Blackboard (blackboard role) abstract interface.

    Shared workspace that modules read from and write to. Holds a canvas,
    registers repositories and mediates creation/lookup of target facades.

    Interface:
        canvas -> Dict[str, Any]  (property)
        count -> int              (property)
        clean() -> None
        create(caller: IWattleflow, *args, **kwargs) -> ITarget
        read(identifier: str) -> ITarget
        register(repository: IRepository) -> None
        write(caller: IWattleflow, facade: ITarget, *args, **kwargs) -> str
    """

    @property
    @abstractmethod
    def canvas(self) -> Dict[str, Any]: ...

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clean(self) -> None: ...

    @abstractmethod
    def create(self, caller: IWattleflow, *args, **kwargs) -> ITarget: ...

    @abstractmethod
    def read(self, identifier: str) -> ITarget: ...

    @abstractmethod
    def register(self, repository: IRepository) -> None: ...

    @abstractmethod
    def write(
        self,
        caller: IWattleflow,
        facade: ITarget,
        *args,
        **kwargs,
    ) -> str: ...


class IModule(IWattleflow, ABC):
    """
    IModule - Blackboard (knowledge-source role) abstract interface.

    A knowledge source that inspects and updates the blackboard.

    Interface:
        update(blackboard: IBlackboard, *args, **kwargs) -> None
    """

    @abstractmethod
    def update(self, blackboard: IBlackboard, *args, **kwargs) -> None: ...


# IPipeline
class IPipeline(IWattleflow, ABC):
    """
    IPipeline - Pipeline abstract interface.

    Drives a target facade through a processor as one stage of processing.

    Interface:
        process(processor: IProcessor, facade: ITarget, *args, **kwargs) -> None
    """

    @abstractmethod
    def process(
        self,
        processor: "IProcessor",
        facade: ITarget,
        *args,
        **kwargs,
    ) -> None: ...


# IProcessor
class IProcessor(IWattleflow, Generic[Item], ABC):
    """
    IProcessor - Processor abstract interface.

    Produces a generator of work items and starts processing them.

    Interface:
        create_generator() -> Item
        start() -> None

    Note (DR-COR-011, open): the parameter denotes the produced value; the
    return type of create_generator() is likely Iterator[Item] rather than
    Item. Decision deferred until GenericProcessor (workflow) is reviewed —
    the contract shape is preserved unchanged here.
    """

    @abstractmethod
    def create_generator(self) -> Item: ...

    @abstractmethod
    def start(self) -> None: ...


# IQuery
class IQuery(IWattleflow, Generic[Result], ABC):
    """
    IQuery - Query Object abstract interface.

    Encapsulates a query that yields a typed result when executed.

    Interface:
        execute() -> Result
    """

    @abstractmethod
    def execute(self) -> Result: ...


# Saga pattern
class ISaga(IWattleflow, Generic[Event], ABC):
    """
    ISaga - Saga abstract interface.

    Coordinates a long-running transaction as a sequence of steps, compensating
    completed steps if a later one fails.

    Interface:
        start(initial_state, *args, **kwargs) -> None
        handle_event(event: Event, *args, **kwargs) -> None
        compensate() -> None
    """

    @abstractmethod
    def start(self, initial_state, *args, **kwargs) -> None: ...

    @abstractmethod
    def handle_event(self, event: Event, *args, **kwargs) -> None: ...

    @abstractmethod
    def compensate(self) -> None: ...


# IUnitOfWork
class IUnitOfWork(IWattleflow, Generic[Entity], ABC):
    """
    IUnitOfWork - Unit of Work abstract interface.

    Tracks new/dirty/deleted entities within a business transaction and applies
    them atomically on commit (or discards them on rollback).

    Interface:
        commit() -> None
        rollback() -> None
        register_new(entity: Entity, *args, **kwargs) -> None
        register_dirty(entity: Entity, *args, **kwargs) -> None
        register_deleted(entity: Entity, *args, **kwargs) -> None
    """

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def register_new(self, entity: Entity, *args, **kwargs) -> None: ...

    @abstractmethod
    def register_dirty(self, entity: Entity, *args, **kwargs) -> None: ...

    @abstractmethod
    def register_deleted(self, entity: Entity, *args, **kwargs) -> None: ...


# IScheduler
# IEventSource already derives from IWattleflow; IScheduler stays an
# IWattleflow through IEventSource (C3/MRO note unchanged).
class IScheduler(IEventSource[Event], ABC):
    """
    IScheduler - Scheduler / Orchestrator abstract interface (Event-Driven source).

    Orchestrates execution of work and emits lifecycle events. A pure
    contract: the single-instance policy, if required, belongs on the
    concrete implementation (e.g. `class Scheduler(Wattleflow, IScheduler[Event],
    Singleton)`), not here.

    Interface:
        setup_orchestrator(*args, **kwargs) -> None
        start_orchestration(parallel: bool) -> None
        stop_orchestration() -> None
        (register_listener, emit_event inherited from IEventSource[Event])
    """

    @abstractmethod
    def setup_orchestrator(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def start_orchestration(self, parallel: bool) -> None: ...

    @abstractmethod
    def stop_orchestration(self) -> None: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
