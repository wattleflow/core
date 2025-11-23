# Module Name: concurrent.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2025 WattleFlow. All rights reserved.
# License: Apache 2 Licence


"""
This module centralises abstract interfaces (ABCs) used across the project for
concurrent/parallel patterns (actors, futures, reactive, pub-sub, queues, thread
pools, coroutines, map-reduce, BSP, fork/join, barriers, divide-and-conquer,
work-stealing, stencil, graph-processing, SPMD, etc).

Notes:
- Interfaces are intentionally minimal; concrete implementations should document
  contract details (exceptions, thread-safety guarantees, return semantics).
- IObservableReactive provides a thread-safe observer registry and snapshot
  semantics for notifications. Notifications are protected against exceptions
  raised by individual observers: an exception in one observer will be logged
  and will not prevent delivering notifications to other observers.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from threading import RLock
import logging
from typing import Any, Callable, Iterable, List, Optional, Generic, TypeVar, Tuple
from .framework import IWattleflow, T

logger = logging.getLogger(__name__)

V = TypeVar("V")
Msg = TypeVar("Msg")
Graph = TypeVar("Graph")


# IActor (IActor, ISystem) - Actor-System
class IActor(IWattleflow, ABC, Generic[Msg]):
    """Actor interface: implement receive to handle messages."""

    @abstractmethod
    def receive(self, message: Msg) -> None: ...


class ISystem(IWattleflow, ABC, Generic[Msg]):
    """Actor system interface: create actors and send messages to them."""

    @abstractmethod
    def create_actor(self, actor_class: type[IActor[Msg]], *args, **kwargs) -> IActor[Msg]: ...

    @abstractmethod
    def send_message(self, actor: IActor[Msg], message: Msg, *args, **kwargs) -> None: ...


# IFuture -(IFuture, IPromise) - Future/Promise interfaces
class IFuture(IWattleflow, ABC, Generic[T]):
    """Future interface: blocking retrieval of a result (with optional timeout)."""

    @abstractmethod
    def result(self, timeout: Optional[float] = None) -> T: ...


class IPromise(IWattleflow, ABC, Generic[T]):
    """Promise interface: provide a result to a corresponding future."""

    @abstractmethod
    def set_result(self, result: T) -> None: ...


# Callback Interface
class ICallback(IWattleflow, ABC, Generic[T]):
    """Callback interface: call is invoked with args/kwargs and returns a value."""

    @abstractmethod
    def call(self, *args, **kwargs) -> T: ...


# IObserverReactive - (IObserverReactive, IObservableReactive) - Reactive Programming Interfaces
class IObserverReactive(IWattleflow, ABC):
    """Observer interface for reactive objects."""

    @abstractmethod
    def update(self, observable: "IObservableReactive", *args, **kwargs) -> None: ...


class IObservableReactive(IWattleflow, ABC):
    """
    Observable base with thread-safe observer registration.

    Implementations should call notify_observers(...) to inform observers of events.
    Notifications are delivered to a snapshot of registered observers in order of
    registration. If an observer raises an exception, the exception is logged and
    notification proceeds for remaining observers.
    """

    def __init__(self) -> None:
        super().__init__()
        self._observers: List[IObserverReactive] = []
        # Use RLock to allow re-entrant calls if observer callbacks interact
        # with the observable (safer for some patterns).
        self._lock = RLock()

    def add_observer(self, observer: IObserverReactive) -> None:
        """Register an observer if not already present (thread-safe)."""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)

    def remove_observer(self, observer: IObserverReactive) -> None:
        """Unregister an observer (thread-safe)."""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)

    def notify_observers(self, *args, **kwargs) -> None:
        """
        Notify all registered observers.

        Notifications are made on a snapshot to allow concurrent modifications of
        the observer list during notification. Exceptions from observers are
        caught and logged; they do not stop notifications for other observers.
        """
        with self._lock:
            observers_snapshot = list(self._observers)
        for observer in observers_snapshot:
            try:
                observer.update(self, *args, **kwargs)
            except Exception as exc:
                # Log exception and continue notifying others.
                logger.exception("Observer %r raised exception during update: %s", observer, exc)


# IEventLoop (IEventLoop) Event-Loop Interface
class IEventLoop(IWattleflow, ABC):
    """Event loop interface (synchronous)."""

    @abstractmethod
    def run_forever(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def call_soon(self, callback: Callable[..., None], *args) -> None: ...


# IPublisher - (IPublisher-ISubscriber) - Pub-Sub interface
class IPublisher(IWattleflow, ABC, Generic[Msg]):
    """Publisher interface for publish-subscribe pattern."""

    @abstractmethod
    def subscribe(self, subscriber: "ISubscriber[Msg]") -> None: ...

    @abstractmethod
    def unsubscribe(self, subscriber: "ISubscriber[Msg]") -> None: ...

    @abstractmethod
    def notify(self, message: Msg) -> None: ...


class ISubscriber(IWattleflow, ABC, Generic[Msg]):
    """Subscriber interface receiving published messages."""

    @abstractmethod
    def update(self, message: Msg) -> None: ...


# Message-Queue Interface
class IMessageQueue(IWattleflow, ABC, Generic[Msg]):
    """Simple message queue interface. Implementations should document return semantics."""

    @abstractmethod
    def send(self, message: Msg) -> None: ...

    @abstractmethod
    def receive(self, timeout: Optional[float] = None) -> Optional[Msg]: ...


# ThreadPool-Pool Interface
class IThreadPool(IWattleflow, ABC):
    """Thread pool interface returning futures for submitted tasks."""

    @abstractmethod
    def submit(self, task: Callable[..., T], *args, **kwargs) -> IFuture[T]: ...

    @abstractmethod
    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None: ...


# Coroutine Interface
class ICoroutine(IWattleflow, ABC, Generic[T]):
    """Coroutine interface (generator-like)."""

    @abstractmethod
    def send(self, value: T) -> T: ...

    @abstractmethod
    def throw(self, typ: type[BaseException], val: BaseException | None = None, tb=None) -> T: ...

    @abstractmethod
    def close(self) -> None: ...


# MapReduce Interface (IMapper, IReducer)
class IMapper(IWattleflow, ABC, Generic[T, V]):
    """Mapper: transforms input data into (key, value) pairs."""

    @abstractmethod
    def map(self, data: Iterable[V]) -> Iterable[Tuple[T, V]]: ...


class IReducer(IWattleflow, ABC, Generic[T, V]):
    """Reducer: reduces values for a key into a single (key, value) result."""

    @abstractmethod
    def reduce(self, key: T, values: Iterable[V]) -> Tuple[T, V]: ...


# ISuperstep - (ISuperstep, IBSPSystem) - Bulk Synchronous Parallel interfaces
class ISuperstep(IWattleflow, ABC):
    @abstractmethod
    def execute(self, data: Any) -> Any: ...


class IBSPSystem(IWattleflow, ABC):
    @abstractmethod
    def run_supersteps(self, supersteps, data) -> None: ...


# IForkJoinTask (IForkJoinTask, IForkJoinPool) - Fork/Join interfaces
class IForkJoinTask(IWattleflow, ABC):
    @abstractmethod
    def fork(self) -> None: ...

    @abstractmethod
    def join(self) -> None: ...


class IForkJoinPool(IWattleflow, ABC):
    @abstractmethod
    def invoke(self, task: Any) -> None: ...


# IBarrier - Barrier Interface
class IBarrier(IWattleflow, ABC):
    @abstractmethod
    def wait(self) -> None: ...


# IDivideAndConquer
class IDivideAndConquer(IWattleflow, ABC):
    @abstractmethod
    def divide(self, problem: Any) -> None: ...

    @abstractmethod
    def solve_subproblem(self, subproblem: Any) -> None: ...

    @abstractmethod
    def combine(self, solutions: Any) -> None: ...


# IDataParallelTask
class IDataParallelTask(IWattleflow, ABC):
    @abstractmethod
    def execute(self, data_chunk: Any) -> None: ...


# IWorkStealingScheduler -(IWorkStealingScheduler, IWorker) - Work-Stealing interface
class IWorkStealingScheduler(IWattleflow, ABC):
    @abstractmethod
    def steal(self) -> None: ...


class IWorker(IWattleflow, ABC):
    @abstractmethod
    def do_work(self) -> None: ...


# IStencil
class IStencil(IWattleflow, ABC):
    @abstractmethod
    def apply(self, grid, point) -> None: ...


# IGraphProcessing
class IGraphProcessing(IWattleflow, Generic[Graph], ABC):
    @abstractmethod
    def process_vertex(self, vertex: Graph) -> None: ...

    @abstractmethod
    def process_edge(self, edge: Graph) -> None: ...


# ISPMDProgram - Single Program, Multiple Data
class ISPMDProgram(IWattleflow, ABC):
    @abstractmethod
    def execute(self, data_partition: Any) -> None: ...
