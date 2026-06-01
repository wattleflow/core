# Module Name: core/concurrent.py
# Author: (IWattleflow@outlook.com)
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
__license__ = "Apache 2 Licence"

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
# basic type variables for concurrent interfaces
Key = TypeVar("Key")
Value = TypeVar("Value")
Message = TypeVar("Message")
Destination = TypeVar("Destination")
Graph = TypeVar("Graph")
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #


logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #
# IActor (IActor, ISystem) - Actor-System
class IActor(IWattleflow, Generic[Message], ABC):
    @abstractmethod
    def receive(self, message: Message) -> None: ...


class ISystem(IWattleflow, ABC):
    @abstractmethod
    def create_actor(self, actor_class: type[IActor[Message]], *args, **kwargs) -> IActor[Message]: ...

    @abstractmethod
    def send_message(self, actor: IActor[Message], message: Message, *args, **kwargs) -> None: ...


# IFuture -(IFuture, IPromise) - Future/Promise interfaces
class IFuture(IWattleflow, Generic[T], ABC):
    """Future interface: blocking retrieval of a result (with optional timeout)."""

    @abstractmethod
    def result(self, timeout: Optional[float] = None) -> T: ...


class IPromise(IWattleflow, Generic[T], ABC):
    """Promise interface: provide a result to a corresponding future."""

    @abstractmethod
    def set_result(self, result: T) -> None: ...


# Callback Interface
class ICallback(IWattleflow, Generic[T], ABC):
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
class IPublisher(IWattleflow, ABC, Generic[Message]):
    """Publisher interface for publish-subscribe pattern."""

    @abstractmethod
    def subscribe(self, subscriber: "ISubscriber[Message]") -> None: ...

    @abstractmethod
    def unsubscribe(self, subscriber: "ISubscriber[Message]") -> None: ...

    @abstractmethod
    def notify(self, message: Message) -> None: ...


class ISubscriber(IWattleflow, ABC, Generic[Message]):
    """Subscriber interface receiving published messages."""

    @abstractmethod
    def update(self, message: Message) -> None: ...


# Message-Queue Interface
class IMessageQueue(IWattleflow, ABC, Generic[Message, Destination]):
    """
    Generic bidirectional message transport interface.

    Type parameters
    ---------------
    Msg  — payload type (bytes, dict, str, custom object, ...)
    Dest — destination/source routing type (str topic, URL, queue name,
           typed address object, ...)

    Examples
    --------
    IMessageQueue[bytes, str]          → Kafka  (bytes poruke, str topic)
    IMessageQueue[dict,  str]          → JSON queue (dict, str queue name)
    IMessageQueue[bytes, str]          → HTTP   (bytes body, str URL)
    IMessageQueue[bytes, QueueAddress] → AMQP s typed adresom

    Notes
    -----
    acknowledge() has a concrete no-op default — override only in systems
    that require explicit commit/ack (e.g. Kafka, AMQP manual-ack mode).
    """

    @abstractmethod
    def send(self, message: Message, destination: Destination) -> None: ...

    @abstractmethod
    def receive(self, source: Destination, timeout: Optional[float] = None) -> Optional[Message]: ...

    def acknowledge(self) -> None:
        """Commit/ack the last received message. No-op for systems without explicit ack."""


# ThreadPool-Pool Interface
class IThreadPool(IWattleflow, ABC):
    """Thread pool interface returning futures for submitted tasks."""

    @abstractmethod
    def submit(self, task: Callable[..., T], *args, **kwargs) -> IFuture[T]: ...

    @abstractmethod
    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None: ...


# Coroutine Interface
class ICoroutine(IWattleflow, Generic[T], ABC):
    """Coroutine interface (generator-like)."""

    @abstractmethod
    def send(self, value: T) -> T: ...

    @abstractmethod
    def throw(self, typ: type[BaseException], val: BaseException | None = None, tb=None) -> T: ...

    @abstractmethod
    def close(self) -> None: ...


# MapReduce Interface (IMapper, IReducer)
class IMapper(IWattleflow, ABC, Generic[Key, Value]):
    """Mapper: transforms input data into (key, value) pairs."""

    @abstractmethod
    def map(self, data: Iterable[Value]) -> Iterable[Tuple[Key, Value]]: ...


class IReducer(IWattleflow, ABC, Generic[Key, Value]):
    """Reducer: reduces values for a key into a single (key, value) result."""

    @abstractmethod
    def reduce(self, key: Key, values: Iterable[Value]) -> Tuple[Key, Value]: ...


# ISuperstep - (ISuperstep, IBSPSystem) - Bulk Synchronous Parallel interfaces
class ISuperstep(IWattleflow, ABC):
    @abstractmethod
    def execute(self, data: Any) -> Any: ...


class IBSPSystem(IWattleflow, ABC):
    @abstractmethod
    def run_supersteps(self, supersteps: Iterable[ISuperstep], data: Any) -> None: ...  # BUG-08: supersteps was untyped


# IForkJoinTask (IForkJoinTask, IForkJoinPool) - Fork/Join interfaces
class IForkJoinTask(IWattleflow, ABC):
    @abstractmethod
    def fork(self) -> None: ...

    @abstractmethod
    def join(self) -> Any: ...  # BUG-05: join must return the task result


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
    def divide(self, problem: Any) -> Iterable[Any]: ...  # BUG-04: must return sub-problems for combine()

    @abstractmethod
    def solve_subproblem(self, subproblem: Any) -> Any: ...  # BUG-04: must return solution for combine()

    @abstractmethod
    def combine(self, solutions: Any) -> Any: ...


# IDataParallelTask
class IDataParallelTask(IWattleflow, ABC):
    @abstractmethod
    def execute(self, data_chunk: Any) -> None: ...


# IWorkStealingScheduler -(IWorkStealingScheduler, IWorker) - Work-Stealing interface
class IWorkStealingScheduler(IWattleflow, ABC):
    @abstractmethod
    def steal(
        self,
    ) -> Optional[Callable[..., Any]]: ...  # BUG-06: steal must return the stolen task


class IWorker(IWattleflow, ABC):
    @abstractmethod
    def do_work(self) -> None: ...


# IStencil
class IStencil(IWattleflow, ABC):
    @abstractmethod
    def apply(self, grid: Any, point: Any) -> Any: ...  # BUG-07: must return computed stencil value


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


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
