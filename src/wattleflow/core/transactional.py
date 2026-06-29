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
from typing import Any, Dict, Generic, Optional
from .framework import IWattleflow, T
from .structural import IAdaptee, ITarget
# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# Document
class IDocument(IAdaptee, Generic[T], ABC):
    """
    IDocument - Adaptable document abstract interface.

    A content-bearing document exposed through the Adapter pattern (IAdaptee),
    identified by a stable identifier and able to update its payload.

    Interface:
        identifier -> str  (property)
        update_content(content: T) -> None
        specific_request() -> T
    """

    @property
    @abstractmethod
    def identifier(self) -> str: ...

    @abstractmethod
    def update_content(self, content: T) -> None: ...

    @abstractmethod
    def specific_request(self) -> T: ...


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


# Signal
class ISignal(IAdaptee, Generic[T], ABC):
    """
    ISignal - Adaptable signal abstract interface.

    A read-only timestamped signal exposed through the Adapter pattern
    (IAdaptee). Unlike IDocument it carries no mutation operation.

    Interface:
        identifier -> str  (property)
        specific_request() -> T

    Note:
        __slots__ declares storage for concrete subclasses. It only saves memory
        if every base in the MRO (IAdaptee, IWattleflow, ...) is also slotted;
        otherwise instances still receive a __dict__. Kept as a subclass contract
        — review against the actual bases before relying on the saving.
    """

    __slots__ = ("_identifier", "_signal", "_timestamp")

    @property
    @abstractmethod
    def identifier(self) -> str: ...

    @abstractmethod
    def specific_request(self) -> T: ...


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


class IEventSource(IWattleflow, ABC):
    """
    IEventSource - Event-Driven (source role) abstract interface.

    Registers listeners and emits events to them.

    Interface:
        register_listener(listener: IEventListener) -> None
        emit_event(event: Any) -> None
    """

    @abstractmethod
    def register_listener(self, listener: IEventListener) -> None: ...

    @abstractmethod
    def emit_event(self, event: Any) -> None: ...


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
class IProcessor(IWattleflow, Generic[T], ABC):
    """
    IProcessor - Processor abstract interface.

    Produces a generator of work items and starts processing them.

    Interface:
        create_generator() -> T
        start() -> None
    """

    @abstractmethod
    def create_generator(self) -> T: ...

    @abstractmethod
    def start(self) -> None: ...


# IQuery
class IQuery(IWattleflow, Generic[T], ABC):
    """
    IQuery - Query Object abstract interface.

    Encapsulates a query that yields a typed result when executed.

    Interface:
        execute() -> T
    """

    @abstractmethod
    def execute(self) -> T: ...


# Saga pattern
class ISaga(IWattleflow, Generic[T], ABC):
    """
    ISaga - Saga abstract interface.

    Coordinates a long-running transaction as a sequence of steps, compensating
    completed steps if a later one fails.

    Interface:
        start(initial_state, *args, **kwargs) -> None
        handle_event(event: T, *args, **kwargs) -> None
        compensate() -> None
    """

    @abstractmethod
    def start(self, initial_state, *args, **kwargs) -> None: ...

    @abstractmethod
    def handle_event(self, event: T, *args, **kwargs) -> None: ...

    @abstractmethod
    def compensate(self) -> None: ...


# IUnitOfWork
class IUnitOfWork(IWattleflow, Generic[T], ABC):
    """
    IUnitOfWork - Unit of Work abstract interface.

    Tracks new/dirty/deleted entities within a business transaction and applies
    them atomically on commit (or discards them on rollback).

    Interface:
        commit() -> None
        rollback() -> None
        register_new(entity: T, *args, **kwargs) -> None
        register_dirty(entity: T, *args, **kwargs) -> None
        register_deleted(entity: T, *args, **kwargs) -> None
    """

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def register_new(self, entity: T, *args, **kwargs) -> None: ...

    @abstractmethod
    def register_dirty(self, entity: T, *args, **kwargs) -> None: ...

    @abstractmethod
    def register_deleted(self, entity: T, *args, **kwargs) -> None: ...


# IScheduler
# IEventSource already derives from IWattleflow, so listing IWattleflow first
# would put a base ahead of its own subclass and break C3/MRO. IScheduler stays
# an IWattleflow through IEventSource.
class IScheduler(IEventSource, Generic[T], ABC):
    """
    IScheduler - Scheduler / Orchestrator abstract interface (Event-Driven source).

    Orchestrates execution of work and emits lifecycle events. A pure contract:
    the single-instance (singleton) policy, if required, belongs on the concrete
    implementation (e.g. `class Scheduler(IScheduler, ISingleton)`), not here.

    Interface:
        setup_orchestrator(*args, **kwargs) -> None
        start_orchestration(parallel: bool) -> None
        stop_orchestration() -> None
        emit_event(event: T, **kwargs) -> None   # generic-typed override of IEventSource
        (register_listener inherited from IEventSource)

    Note:
        emit_event overrides IEventSource.emit_event(event: Any), narrowing to
        event: T and widening with **kwargs (LSP-safe widening). Alternative:
        make IEventSource generic and drop this override entirely — open decision.
    """

    @abstractmethod
    def setup_orchestrator(self, *args, **kwargs) -> None: ...

    @abstractmethod
    def start_orchestration(self, parallel: bool) -> None: ...

    @abstractmethod
    def stop_orchestration(self) -> None: ...

    @abstractmethod
    def emit_event(self, event: T, **kwargs) -> None: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
