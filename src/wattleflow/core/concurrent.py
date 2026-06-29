# Module Name: core/concurrent.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations
from abc import ABC, abstractmethod
from threading import RLock
import logging
from typing import Any, Callable, Iterable, List, Optional, Generic, TypeVar, Tuple
from .framework import IWattleflow, T

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
# basic type variables for concurrent interfaces
Key = TypeVar("Key")
Value = TypeVar("Value")
Message = TypeVar("Message")
Destination = TypeVar("Destination")
Vertex = TypeVar("Vertex")  # graph vertex type
Edge = TypeVar("Edge")  # graph edge type
Output = TypeVar("Output")  # coroutine yield (output) type  [NFR-ORG-03]
Input = TypeVar("Input")  # coroutine send (input) type    [NFR-ORG-03]
Result = TypeVar("Result")  # coroutine return (result) type [NFR-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #
# IActor (IActor, ISystem) - Actor-System
class IActor(IWattleflow, Generic[Message], ABC):
    """
    IActor - Actor Model abstract interface.

    An actor processes messages sequentially, one at a time, holding its own
    private state. Concurrency arises from many actors running independently.

    Interface:
        receive(message: Message) -> None
    """

    @abstractmethod
    def receive(self, message: Message) -> None: ...


class ISystem(IWattleflow, ABC):
    """
    ISystem - Actor Model (system role) abstract interface.

    Creates actors and routes messages to them. Owns the lifecycle and
    scheduling of the actors it spawns.

    Interface:
        create_actor(actor_class: type[IActor[Message]], *args, **kwargs) -> IActor[Message]
        send_message(actor: IActor[Message], message: Message, *args, **kwargs) -> None
    """

    @abstractmethod
    def create_actor(self, actor_class: type[IActor[Message]], *args, **kwargs) -> IActor[Message]: ...

    @abstractmethod
    def send_message(self, actor: IActor[Message], message: Message, *args, **kwargs) -> None: ...


# IFuture -(IFuture, IPromise) - Future/Promise interfaces
class IFuture(IWattleflow, Generic[T], ABC):
    """
    IFuture - Future abstract interface.

    Read side of an asynchronous result: blocking retrieval of a value that may
    not yet be available, with an optional timeout.

    Interface:
        result(timeout: Optional[float] = None) -> T
    """

    @abstractmethod
    def result(self, timeout: Optional[float] = None) -> T: ...


class IPromise(IWattleflow, Generic[T], ABC):
    """
    IPromise - Promise abstract interface.

    Write side of an asynchronous result: fulfils the value that a corresponding
    future will return.

    Interface:
        set_result(result: T) -> None
    """

    @abstractmethod
    def set_result(self, result: T) -> None: ...


# Callback Interface
class ICallback(IWattleflow, Generic[T], ABC):
    """
    ICallback - Callback abstract interface.

    A deferred unit of work invoked with arbitrary arguments, returning a value.

    Interface:
        call(*args, **kwargs) -> T
    """

    @abstractmethod
    def call(self, *args, **kwargs) -> T: ...


# IObserverReactive - (IObserverReactive, IObservableReactive) - Reactive Programming Interfaces
class IObserverReactive(IWattleflow, ABC):
    """
    IObserverReactive - Observer (reactive) abstract interface.

    Receives push notifications from an IObservableReactive, with a reference to
    the source observable.

    Interface:
        update(observable: IObservableReactive, *args, **kwargs) -> None
    """

    @abstractmethod
    def update(self, observable: "IObservableReactive", *args, **kwargs) -> None: ...


class IObservableReactive(IWattleflow, ABC):
    """
    IObservableReactive - Observable (reactive) base with thread-safe registration.

    Concrete base, not abstract: implementations call notify_observers(...) to
    inform observers of events. Notifications are delivered to a snapshot of
    registered observers in order of registration. If an observer raises, the
    exception is logged and notification proceeds for the remaining observers.

    Interface:
        add_observer(observer: IObserverReactive) -> None
        remove_observer(observer: IObserverReactive) -> None
        notify_observers(*args, **kwargs) -> None
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
    """
    IEventLoop - Event Loop abstract interface (synchronous).

    Drives a single-threaded loop that runs scheduled callbacks until stopped.

    Interface:
        run_forever() -> None
        stop() -> None
        call_soon(callback: Callable[..., None], *args) -> None
    """

    @abstractmethod
    def run_forever(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def call_soon(self, callback: Callable[..., None], *args) -> None: ...


# IPublisher - (IPublisher, ISubscriber) - Pub-Sub interface
class IPublisher(IWattleflow, Generic[Message], ABC):
    """
    IPublisher - Publish-Subscribe (publisher role) abstract interface.

    Maintains subscribers and broadcasts messages to them. Publisher and
    subscribers are decoupled: the publisher does not know who consumes.

    Interface:
        subscribe(subscriber: ISubscriber[Message]) -> None
        unsubscribe(subscriber: ISubscriber[Message]) -> None
        notify(message: Message) -> None
    """

    @abstractmethod
    def subscribe(self, subscriber: "ISubscriber[Message]") -> None: ...

    @abstractmethod
    def unsubscribe(self, subscriber: "ISubscriber[Message]") -> None: ...

    @abstractmethod
    def notify(self, message: Message) -> None: ...


class ISubscriber(IWattleflow, Generic[Message], ABC):
    """
    ISubscriber - Publish-Subscribe (subscriber role) abstract interface.

    Receives messages broadcast by an IPublisher.

    Interface:
        update(message: Message) -> None
    """

    @abstractmethod
    def update(self, message: Message) -> None: ...


# Message-Queue Interface
class IMessageQueue(IWattleflow, Generic[Message, Destination], ABC):
    """
    IMessageQueue - Message Queue abstract interface (generic bidirectional transport).

    Type parameters
    ---------------
    Message     — payload type (bytes, dict, str, custom object, ...)
    Destination — destination/source routing type (str topic, URL, queue name,
                  typed address object, ...)

    Examples
    --------
    IMessageQueue[bytes, str]          → Kafka  (bytes message, str topic)
    IMessageQueue[dict,  str]          → JSON queue (dict, str queue name)
    IMessageQueue[bytes, str]          → HTTP   (bytes body, str URL)
    IMessageQueue[bytes, QueueAddress] → AMQP with a typed address

    Notes
    -----
    acknowledge() has a concrete no-op default — override only in systems
    that require explicit commit/ack (e.g. Kafka, AMQP manual-ack mode).

    Interface:
        send(message: Message, destination: Destination) -> None
        receive(source: Destination, timeout: Optional[float] = None) -> Optional[Message]
        acknowledge() -> None  # concrete no-op default
    """

    @abstractmethod
    def send(self, message: Message, destination: Destination) -> None: ...

    @abstractmethod
    def receive(self, source: Destination, timeout: Optional[float] = None) -> Optional[Message]: ...

    def acknowledge(self) -> None:
        """Commit/ack the last received message. No-op for systems without explicit ack."""


# ThreadPool-Pool Interface
class IThreadPool(IWattleflow, ABC):
    """
    IThreadPool - Thread Pool abstract interface.

    Submits callables for execution on a pool of worker threads, returning a
    future for each task, and shuts the pool down on request.

    Interface:
        submit(task: Callable[..., T], *args, **kwargs) -> IFuture[T]
        shutdown(wait: bool = True, cancel_futures: bool = False) -> None
    """

    @abstractmethod
    def submit(self, task: Callable[..., T], *args, **kwargs) -> IFuture[T]: ...

    @abstractmethod
    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None: ...


# Coroutine Interface
class ICoroutine(IWattleflow, Generic[Output, Input, Result], ABC):
    """
    ICoroutine - Coroutine abstract interface (generator-like).

    Type parameters  [NFR-ORG-03]
    ---------------
    Output — type produced (yielded) by the coroutine on each step
    Input  — type accepted by send()
    Result — type returned on completion (carried by StopIteration)

    Interface:
        send(value: Input) -> Output
        throw(typ: type[BaseException], val: BaseException | None = None, tb: Any = None) -> Output
        close() -> None
    """

    @abstractmethod
    def send(self, value: Input) -> Output: ...

    @abstractmethod
    def throw(self, typ: type[BaseException], val: BaseException | None = None, tb: Any = None) -> Output: ...

    @abstractmethod
    def close(self) -> None: ...


# MapReduce Interface (IMapper, IReducer)
class IMapper(IWattleflow, Generic[Key, Value], ABC):
    """
    IMapper - MapReduce (mapper role) abstract interface.

    Transforms input data into intermediate (key, value) pairs for grouping.

    Interface:
        map(data: Iterable[Value]) -> Iterable[Tuple[Key, Value]]
    """

    @abstractmethod
    def map(self, data: Iterable[Value]) -> Iterable[Tuple[Key, Value]]: ...


class IReducer(IWattleflow, Generic[Key, Value], ABC):
    """
    IReducer - MapReduce (reducer role) abstract interface.

    Reduces all values grouped under a key into a single (key, value) result.

    Interface:
        reduce(key: Key, values: Iterable[Value]) -> Tuple[Key, Value]
    """

    @abstractmethod
    def reduce(self, key: Key, values: Iterable[Value]) -> Tuple[Key, Value]: ...


# ISuperstep - (ISuperstep, IBSPSystem) - Bulk Synchronous Parallel interfaces
class ISuperstep(IWattleflow, ABC):
    """
    ISuperstep - Bulk Synchronous Parallel (superstep) abstract interface.

    A single BSP step: local computation over the data before the next global
    synchronisation barrier.

    Interface:
        execute(data: Any) -> Any
    """

    @abstractmethod
    def execute(self, data: Any) -> Any: ...


class IBSPSystem(IWattleflow, ABC):
    """
    IBSPSystem - Bulk Synchronous Parallel (system role) abstract interface.

    Runs an ordered sequence of supersteps, synchronising between each.

    Interface:
        run_supersteps(supersteps: Iterable[ISuperstep], data: Any) -> None
    """

    @abstractmethod
    def run_supersteps(self, supersteps: Iterable[ISuperstep], data: Any) -> None: ...  # BUG-08: supersteps was untyped


# IForkJoinTask (IForkJoinTask, IForkJoinPool) - Fork/Join interfaces
class IForkJoinTask(IWattleflow, ABC):
    """
    IForkJoinTask - Fork/Join (task role) abstract interface.

    Splits itself into subtasks (fork) and waits for their completion, returning
    the combined result (join).

    Interface:
        fork() -> None
        join() -> Any
    """

    @abstractmethod
    def fork(self) -> None: ...

    @abstractmethod
    def join(self) -> Any: ...  # BUG-05: join must return the task result


class IForkJoinPool(IWattleflow, ABC):
    """
    IForkJoinPool - Fork/Join (pool role) abstract interface.

    Executes a fork/join task to completion and returns its result.

    Interface:
        invoke(task: Any) -> Any
    """

    @abstractmethod
    def invoke(self, task: Any) -> Any: ...  # BUG-05b: invoke must return the task result (mirror of join)


# IBarrier - Barrier Interface
class IBarrier(IWattleflow, ABC):
    """
    IBarrier - Barrier synchronisation abstract interface.

    Blocks each participating thread until all participants have reached the
    barrier, then releases them together.

    Interface:
        wait() -> None
    """

    @abstractmethod
    def wait(self) -> None: ...


# IDivideAndConquer
class IDivideAndConquer(IWattleflow, ABC):
    """
    IDivideAndConquer - Divide and Conquer abstract interface.

    Splits a problem into sub-problems, solves each, and combines the partial
    solutions into the final result.

    Interface:
        divide(problem: Any) -> Iterable[Any]
        solve_subproblem(subproblem: Any) -> Any
        combine(solutions: Any) -> Any
    """

    @abstractmethod
    def divide(self, problem: Any) -> Iterable[Any]: ...  # BUG-04: must return sub-problems for combine()

    @abstractmethod
    def solve_subproblem(self, subproblem: Any) -> Any: ...  # BUG-04: must return solution for combine()

    @abstractmethod
    def combine(self, solutions: Any) -> Any: ...


# IDataParallelTask
class IDataParallelTask(IWattleflow, ABC):
    """
    IDataParallelTask - Data Parallelism abstract interface.

    Applies the same operation to an independent chunk of data; many chunks run
    in parallel.

    Interface:
        execute(data_chunk: Any) -> None
    """

    @abstractmethod
    def execute(self, data_chunk: Any) -> None: ...


# IWorkStealingScheduler -(IWorkStealingScheduler, IWorker) - Work-Stealing interface
class IWorkStealingScheduler(IWattleflow, ABC):
    """
    IWorkStealingScheduler - Work-Stealing (scheduler role) abstract interface.

    Lets an idle worker steal a pending task from another worker's queue to keep
    load balanced.

    Interface:
        steal() -> Optional[Callable[..., Any]]
    """

    @abstractmethod
    def steal(
        self,
    ) -> Optional[Callable[..., Any]]: ...  # BUG-06: steal must return the stolen task


class IWorker(IWattleflow, ABC):
    """
    IWorker - Work-Stealing (worker role) abstract interface.

    Executes tasks from its own queue and, when idle, steals from others.

    Interface:
        do_work() -> None
    """

    @abstractmethod
    def do_work(self) -> None: ...


# IStencil
class IStencil(IWattleflow, ABC):
    """
    IStencil - Stencil computation abstract interface.

    Computes a new value at a grid point from the values of its neighbourhood.

    Interface:
        apply(grid: Any, point: Any) -> Any
    """

    @abstractmethod
    def apply(self, grid: Any, point: Any) -> Any: ...  # BUG-07: must return computed stencil value


# IGraphProcessing
class IGraphProcessing(IWattleflow, Generic[Vertex, Edge], ABC):
    """
    IGraphProcessing - Graph Processing (vertex-centric) abstract interface.

    Defines per-vertex and per-edge computation for parallel graph traversal.
    Parameterised separately over Vertex and Edge types.

    Interface:
        process_vertex(vertex: Vertex) -> None
        process_edge(edge: Edge) -> None
    """

    @abstractmethod
    def process_vertex(self, vertex: Vertex) -> None: ...

    @abstractmethod
    def process_edge(self, edge: Edge) -> None: ...


# ISPMDProgram - Single Program, Multiple Data
class ISPMDProgram(IWattleflow, ABC):
    """
    ISPMDProgram - SPMD (Single Program, Multiple Data) abstract interface.

    The same program runs on every process, each operating on its own data
    partition.

    Interface:
        execute(data_partition: Any) -> None
    """

    @abstractmethod
    def execute(self, data_partition: Any) -> None: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
