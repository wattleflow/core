# Module name: core/transactional.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
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
EventType = TypeVar("EventType", bound="IEvent")  # emitted/handled event type  [NFRQ-ORG-03]
Item = TypeVar("Item")  # processor work item type                [NFRQ-ORG-03]
Result = TypeVar("Result")  # query result type                   [NFRQ-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# Document
class IDocument(IAdaptee, Generic[Content], ABC):
    __slots__ = ()

    @abstractmethod
    def update_content(self, content: Content) -> None: ...

    @abstractmethod
    def specific_request(self) -> Content: ...


# Resource driver
class IDriver(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def read(self, uri: str, **kwargs: Any) -> Any: ...

    @abstractmethod
    def write(self, uri: str, data: Any, **kwargs: Any) -> Any: ...

    @classmethod
    @abstractmethod
    def metadata(cls) -> Any: ...


# Configuration
class IConfig(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def find(self, *keys: str, default: Any = None) -> Any: ...


# Parser / Formatter
class IParser(IWattleflow, Generic[Content], ABC):
    __slots__ = ()

    @abstractmethod
    def parse(self, **kwargs: Any) -> Content: ...


class IFormatter(IWattleflow, Generic[Content], ABC):
    __slots__ = ()

    @abstractmethod
    def render(self, **kwargs: Any) -> bytes | str: ...


# Signal
class ISignal(IAdaptee, Generic[Content], ABC):
    __slots__ = ()

    @abstractmethod
    def specific_request(self) -> Content: ...


# Event-Driven
class IEvent(IWattleflow, ABC):
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
    def payload(self) -> Mapping[str, Any]: ...


class IEventListener(IWattleflow, Generic[EventType], ABC):
    __slots__ = ()

    @abstractmethod
    def on_event(self, event: EventType) -> None: ...


class IEventSource(IWattleflow, Generic[EventType], ABC):
    __slots__ = ()

    @abstractmethod
    def register_listener(self, listener: IEventListener[EventType]) -> None: ...

    @abstractmethod
    def unregister_listener(self, listener: IEventListener[EventType]) -> None: ...

    @abstractmethod
    def emit_event(self, event: EventType, **kwargs: Any) -> None: ...


# Repository
class IRepository(IWattleflow, ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def read(self, identifier: str, *args: Any, **kwargs: Any) -> ITarget: ...

    @abstractmethod
    def write(self, facade: ITarget, *args: Any, **kwargs: Any) -> Any: ...


# Blackboard
class IBlackboard(IWattleflow, ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def canvas(self) -> Mapping[str, Any]: ...

    @property
    @abstractmethod
    def count(self) -> int: ...

    @abstractmethod
    def clear(self) -> None: ...

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
    ) -> Any: ...


class IModule(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def exec_condition(self, blackboard: IBlackboard) -> bool: ...

    @abstractmethod
    def exec_action(self, blackboard: IBlackboard, *args: Any, **kwargs: Any) -> None: ...


# Pipeline
class IPipeline(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def run_stage(
        self,
        processor: IProcessor,
        facade: ITarget,
        *args: Any,
        **kwargs: Any,
    ) -> None: ...


# Processor
class IProcessor(IWattleflow, Generic[Item], ABC):
    __slots__ = ()

    @abstractmethod
    def create_generator(self) -> Iterator[Item]: ...

    @abstractmethod
    def start(self) -> None: ...


# Query Object
class IQuery(IWattleflow, Generic[Result], ABC):
    __slots__ = ()

    @abstractmethod
    def execute(self) -> Result: ...


# Saga
class ISaga(IWattleflow, Generic[EventType], ABC):
    __slots__ = ()

    @abstractmethod
    def start(self, initial_state: Any, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def handle_event(self, event: EventType, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def compensate(self) -> None: ...


# Unit of Work
class IUnitOfWork(IWattleflow, Generic[Entity], ABC):
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


# Scheduler / Orchestrator
class IScheduler(IEventSource[EventType], ABC):
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
