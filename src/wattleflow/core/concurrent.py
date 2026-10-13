# Module name: core/concurrent.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar

from .framework import IWattleflow

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
Key = TypeVar("Key")
Value = TypeVar("Value")
Message = TypeVar("Message")
Destination = TypeVar("Destination")
Vertex = TypeVar("Vertex")  # graph vertex type
Edge = TypeVar("Edge")  # graph edge type
Output = TypeVar("Output")  # coroutine yield (output) type  [NFRQ-ORG-03]
Input = TypeVar("Input")  # coroutine send (input) type     [NFRQ-ORG-03]
Result = TypeVar("Result")  # deferred/computed value type   [NFRQ-ORG-03]
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #
# Actor Model
class IActor(IWattleflow, Generic[Message], ABC):
    __slots__ = ()

    @abstractmethod
    def receive(self, message: Message) -> None: ...


class ISystem(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def create_actor(self, actor_class: type[IActor[Message]], *args, **kwargs) -> IActor[Message]: ...

    @abstractmethod
    def send_message(self, actor: IActor[Message], message: Message, *args, **kwargs) -> None: ...


# Future / Promise
class IFuture(IWattleflow, Generic[Result], ABC):
    __slots__ = ()

    @abstractmethod
    def result(self, timeout: float | None = None) -> Result: ...

    @abstractmethod
    def done(self) -> bool: ...

    @abstractmethod
    def cancel(self) -> bool: ...


class IPromise(IWattleflow, Generic[Result], ABC):
    __slots__ = ()

    @abstractmethod
    def set_result(self, result: Result) -> None: ...

    @abstractmethod
    def set_exception(self, exception: BaseException) -> None: ...


# Callback
class ICallback(IWattleflow, Generic[Result], ABC):
    __slots__ = ()

    @abstractmethod
    def call(self, *args, **kwargs) -> Result: ...


# Reactive Programming
class IObserverReactive(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def update(self, observable: IObservableReactive, *args, **kwargs) -> None: ...


class IObservableReactive(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def add_observer(self, observer: IObserverReactive) -> None: ...

    @abstractmethod
    def remove_observer(self, observer: IObserverReactive) -> None: ...

    @abstractmethod
    def notify_observers(self, *args, **kwargs) -> None: ...


# Event Loop
class IEventLoop(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def run_forever(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def call_soon(self, callback: Callable[..., None], *args) -> None: ...


# Publish-Subscribe
class IPublisher(IWattleflow, Generic[Message], ABC):
    __slots__ = ()

    @abstractmethod
    def subscribe(self, subscriber: ISubscriber[Message]) -> None: ...

    @abstractmethod
    def unsubscribe(self, subscriber: ISubscriber[Message]) -> None: ...

    @abstractmethod
    def publish(self, message: Message) -> None: ...


class ISubscriber(IWattleflow, Generic[Message], ABC):
    __slots__ = ()

    @abstractmethod
    def on_message(self, message: Message) -> None: ...


# Message Queue
class IMessageQueue(IWattleflow, Generic[Message, Destination], ABC):
    __slots__ = ()

    @abstractmethod
    def send(self, message: Message, destination: Destination) -> None: ...

    @abstractmethod
    def receive(self, source: Destination, timeout: float | None = None) -> Message | None: ...

    def acknowledge(self) -> None:  # noqa: B027 - contract default (Null-ack)
        return None


# Thread Pool
class IThreadPool(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def submit(self, task: Callable[..., Result], *args, **kwargs) -> IFuture[Result]: ...

    @abstractmethod
    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None: ...


# Coroutine
class ICoroutine(IWattleflow, Generic[Output, Input], ABC):
    __slots__ = ()

    @abstractmethod
    def send(self, value: Input) -> Output: ...

    @abstractmethod
    def throw(self, exc: BaseException) -> Output: ...

    @abstractmethod
    def close(self) -> None: ...


# MapReduce
class IMapper(IWattleflow, Generic[Key, Value], ABC):
    __slots__ = ()

    @abstractmethod
    def map(self, data: Iterable[Value]) -> Iterable[tuple[Key, Value]]: ...


class IReducer(IWattleflow, Generic[Key, Value], ABC):
    __slots__ = ()

    @abstractmethod
    def reduce(self, key: Key, values: Iterable[Value]) -> tuple[Key, Value]: ...


# Bulk Synchronous Parallel
class ISuperstep(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def compute(self, data: Any) -> Any: ...


class IBSPSystem(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def run_supersteps(self, supersteps: Iterable[ISuperstep], data: Any) -> Any: ...


# Fork/Join
class IForkJoinTask(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def fork(self) -> None: ...

    @abstractmethod
    def join(self) -> Any: ...


class IForkJoinPool(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def invoke(self, task: IForkJoinTask) -> Any: ...


# Barrier
class IBarrier(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def wait(self) -> None: ...


# Divide and Conquer
class IDivideAndConquer(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def divide(self, problem: Any) -> Iterable[Any]: ...

    @abstractmethod
    def solve_subproblem(self, subproblem: Any) -> Any: ...

    @abstractmethod
    def combine(self, solutions: Any) -> Any: ...


# Data Parallelism
class IDataParallelTask(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def compute(self, data_chunk: Any) -> None: ...


# Work Stealing
class IWorkStealingScheduler(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def steal(self, thief: IWorker) -> Callable[..., Any] | None: ...


class IWorker(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def do_work(self) -> None: ...


# Stencil
class IStencil(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def apply(self, grid: Any, point: Any) -> Any: ...


# Graph Processing
class IGraphProcessing(IWattleflow, Generic[Vertex, Edge], ABC):
    __slots__ = ()

    @abstractmethod
    def process_vertex(self, vertex: Vertex) -> None: ...

    @abstractmethod
    def process_edge(self, edge: Edge) -> None: ...


# Single Program, Multiple Data
class ISPMDProgram(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def run(self, data_partition: Any) -> None: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
