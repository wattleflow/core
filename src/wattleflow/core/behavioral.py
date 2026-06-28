# Module name: core/behavioural.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Generic, Iterator, Optional, TypeVar
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
WattleType = TypeVar("WattleType")
Action = TypeVar("Action")  # action type
Context = TypeVar("Context")  # context type
Result = TypeVar("Result")  # result type
State = TypeVar("State")  # state type
# --------------------------------------------------------------------------- #
# endregion Types                                                             #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# IHandler (IHandler) - Chain of Responsibility interface
class IHandler(IWattleflow, ABC):
    """
    IHandler - Chain of Responsibility abstract interface.

    Each handler holds a reference to the next handler and decides whether to
    process the request or pass it along. The sender does not know which handler
    will ultimately handle the request.

    Interface:
        set_next(handler: IHandler) -> None
        handle(request: Any) -> None
    """

    @abstractmethod
    def set_next(self, handler: "IHandler") -> None: ...

    @abstractmethod
    def handle(self, request: Any) -> None: ...


# ICommand (ICommand, IInvoker) - Command interface
class ICommand(IWattleflow, ABC):
    """
    ICommand - Command abstract interface.

    Encapsulates a request as an object, decoupling the sender from the
    receiver. The caller invokes execute() without knowing what work it performs.

    Interface:
        execute(**kwargs) -> Any
    """

    @abstractmethod
    def execute(self, **kwargs) -> Any: ...


class IInvoker(IWattleflow, ABC):
    """
    IInvoker - Command (invoker role) abstract interface.

    Holds a command and triggers it. Sits between the client and the command,
    allowing cross-cutting concerns such as logging, queuing or undo.

    Interface:
        set_command(command: ICommand) -> None
        invoke() -> Any
    """

    @abstractmethod
    def set_command(self, command: ICommand) -> None: ...

    @abstractmethod
    def invoke(self) -> Any: ...


class IExpression(IWattleflow, Generic[Context, Result], ABC):
    """
    IExpression - Interpreter abstract interface.

    Evaluates an expression against a context. Composite expressions are built
    from simpler ones, each implementing interpret(). Parameterised over Context
    and Result for input/output type safety.

    Interface:
        interpret(context: Context) -> Result
    """

    @abstractmethod
    def interpret(self, context: Context) -> Result: ...


# Iterator (IIterator, ISyncAggregate)
class IIterator(IWattleflow, Iterator[WattleType], Generic[WattleType], ABC):
    """
    IIterator - Iterator abstract interface.

    Lazily builds its underlying iterator on first use via create_iterator()
    and delegates traversal to it.

    Interface:
        create_iterator() -> Iterator[WattleType]
    """

    def __init__(self) -> None:
        super().__init__()
        self._iterator: Optional[Iterator[WattleType]] = None

    def __iter__(self) -> Iterator[WattleType]:
        return self

    def __next__(self) -> WattleType:
        if self._iterator is None:
            self._iterator = self.create_iterator()
        return next(self._iterator)

    @abstractmethod
    def create_iterator(self) -> Iterator[WattleType]: ...


# ISyncAggregate
class ISyncAggregate(IWattleflow, Generic[WattleType], ABC):
    """
    ISyncAggregate - Iterator (aggregate role) abstract interface.

    A collection that knows how to produce a synchronous iterator over its
    elements.

    Interface:
        create_iterator() -> IIterator[WattleType]
    """

    @abstractmethod
    def create_iterator(self) -> IIterator[WattleType]: ...


# IAsyncIterator (IAsyncIterator, IAsyncAggregate)
class IAsyncIterator(IWattleflow, AsyncIterator[WattleType], Generic[WattleType], ABC):
    """
    IAsyncIterator - Asynchronous Iterator abstract interface.

    Asynchronous counterpart of IIterator. create_iterator() is synchronous and
    returns an AsyncIterator; traversal is awaited via __anext__().

    Interface:
        create_iterator() -> AsyncIterator[WattleType]
    """

    def __init__(self) -> None:
        super().__init__()
        self._iterator: Optional[AsyncIterator[WattleType]] = None

    def __aiter__(self) -> AsyncIterator[WattleType]:
        return self

    async def __anext__(self) -> WattleType:
        if self._iterator is None:
            # create_iterator is synchronous and returns an AsyncIterator
            self._iterator = self.create_iterator()
        return await self._iterator.__anext__()

    @abstractmethod
    def create_iterator(self) -> AsyncIterator[WattleType]: ...


class IAsyncAggregate(IWattleflow, Generic[WattleType], ABC):
    """
    IAsyncAggregate - Asynchronous Iterator (aggregate role) abstract interface.

    A collection that knows how to produce an asynchronous iterator over its
    elements.

    Interface:
        create_iterator() -> IAsyncIterator[WattleType]
    """

    @abstractmethod
    def create_iterator(self) -> IAsyncIterator[WattleType]: ...


# Mediator interfaces
class IMediator(IWattleflow, ABC):
    """
    IMediator - Mediator abstract interface.

    Interface:
        notify(sender: IColleague, event: Any, **data: Any) -> None
    """

    @abstractmethod
    def notify(self, sender: "IColleague", event: Any, **data: Any) -> None: ...


class IColleague(IWattleflow, ABC):
    """
    IColleague - Mediator (colleague role) abstract interface.

    Interface:
        set_mediator(mediator: IMediator) -> None
        event_occurred(event: Any, **data: Any) -> None
    """

    @abstractmethod
    def set_mediator(self, mediator: IMediator) -> None: ...

    @abstractmethod
    def event_occurred(self, event: Any, **data: Any) -> None: ...


# IMemento - Memento Interfaces (IMemento, IOriginator)
class IMemento(IWattleflow, Generic[State], ABC):
    """
    IMemento - Memento abstract interface.

    Carries a captured snapshot of an originator's internal state.

    Interface:
        get_state() -> State
    """

    @abstractmethod
    def get_state(self) -> State: ...


class IOriginator(IWattleflow, Generic[State], ABC):
    """
    IOriginator - Memento (originator role) abstract interface.

    Produces mementos capturing its state and restores itself from one.

    Interface:
        save_state() -> IMemento[State]
        restore_state(memento: IMemento[State]) -> None
    """

    @abstractmethod
    def save_state(self) -> IMemento[State]: ...

    @abstractmethod
    def restore_state(self, memento: IMemento[State]) -> None: ...


# Observer interfaces - Reactive Programming Interfaces
class IObserver(IWattleflow, ABC):
    """
    IObserver - Observer abstract interface.

    Receives notifications from an IObservable when an event occurs.

    Interface:
        update(event: Any, **kwargs) -> None
    """

    @abstractmethod
    def update(self, event: Any, **kwargs) -> None: ...


class IObservable(IWattleflow, ABC):
    """
    IObservable - Observer / Reactive Programming abstract interface.

    Interface:
        subscribe(observer: IObserver) -> None
    """

    @abstractmethod
    def subscribe(self, observer: IObserver) -> None: ...


# IStateMachine - State Machine interface
class IStateMachine(IWattleflow, ABC):
    """
    IStateMachine - State Machine abstract interface.

    Guards and applies transitions: can() tests whether an action is admissible
    in the current state, apply() performs it.

    Interface:
        can(action: Action) -> bool
        apply(action: Action) -> None
    """

    @abstractmethod
    def can(self, action: Action) -> bool: ...

    @abstractmethod
    def apply(self, action: Action) -> None: ...


# IState (IState, IStateContext) - State interfaces
class IState(IWattleflow, ABC):
    """
    IState - State abstract interface.

    Interface:
        handle(context: IStateContext, **kwargs: Any) -> None
    """

    @abstractmethod
    def handle(self, context: "IStateContext", **kwargs: Any) -> None: ...


class IStateContext(IWattleflow, ABC):
    """
    IStateContext - State (context role) abstract interface.

    Interface:
        set_state(state: IState) -> None
        request(**kwargs: Any) -> None
    """

    @abstractmethod
    def set_state(self, state: IState) -> None: ...

    @abstractmethod
    def request(self, **kwargs: Any) -> None: ...


# IStrategy - (IStrategy, IStrategyContext) - Strategy interfaces
class IStrategy(IWattleflow, ABC):
    """
    IStrategy - Strategy abstract interface.

    Interface:
        execute(caller: IWattleflow, **kwargs) -> Any
    """

    # region FIX
    # BUG #1: Added `caller: IWattleflow` to the interface signature to match the
    # concrete Strategy.execute() override. The missing parameter caused a Liskov
    # Substitution Principle violation: code typed against IStrategy would have no
    # knowledge that caller is required, leading to silent TypeError at runtime.
    # BUG #2: Propagated `caller` to IStrategyContext.execute_strategy below so the
    # context is able to forward the now-mandatory argument to the strategy.
    # endregion FIX
    @abstractmethod
    def execute(self, caller: IWattleflow, **kwargs) -> Any: ...


class IStrategyContext(IWattleflow, ABC):
    """
    IStrategyContext - Strategy (context role) abstract interface.

    Interface:
        set_strategy(strategy: IStrategy) -> None
        execute_strategy(caller: IWattleflow, **kwargs) -> Any
    """

    @abstractmethod
    def set_strategy(self, strategy: IStrategy) -> None: ...

    @abstractmethod
    def execute_strategy(self, caller: IWattleflow, **kwargs) -> Any: ...


# Template method (ITemplate)
class ITemplate(IWattleflow, ABC):
    """
    ITemplate - The template method defining the steps of the process.

    Interface:
        process() -> None

        # Abstract
        initialise(self) -> None
        perform_task(self) -> None
        finalise(self) -> None

        # Hooks
        before_task(self) -> None: ...  # hook (optional)
        after_task(self) -> None: ...   # hook (optional)

    """

    def process(self) -> None:
        self.initialise()
        try:
            # call optional hooks around the main work
            self.before_task()
            self.perform_task()
            self.after_task()
        finally:
            self.finalise()

    def before_task(self) -> None: ...  # hook (optional)
    def after_task(self) -> None: ...  # hook (optional)

    @abstractmethod
    def initialise(self) -> None: ...

    @abstractmethod
    def perform_task(self) -> None: ...

    @abstractmethod
    def finalise(self) -> None: ...


# IVisitor (IVisitor, IElement) - Visitor interfaces
class IVisitor(IWattleflow, ABC):
    """
    IVisitor - Abstract interface for Visitor pattern.

    Interface:
        visit(element: IElement) -> Any
    """

    @abstractmethod
    def visit(self, element: "IElement") -> Any: ...


class IElement(IWattleflow, ABC):
    """
    IElement - Abstract interface for elements that accept visitors.

    Interface:
        accept(visitor: IVisitor) -> None
    """

    @abstractmethod
    def accept(self, visitor: IVisitor) -> None: ...


# ILogger interface
class ILogger(IObservable, ABC):
    """
    ILogger - Logger abstract interface.

    Standard severity-level logging API. Extends IObservable, so a logger may
    also publish events to subscribed observers.

    Interface:
        debug(msg: str, **kwargs: Any) -> None
        info(msg: str, **kwargs: Any) -> None
        warning(msg: str, **kwargs: Any) -> None
        error(msg: str, **kwargs: Any) -> None
        critical(msg: str, **kwargs: Any) -> None
        exception(msg: str, **kwargs: Any) -> None
    """

    @abstractmethod
    def debug(self, msg: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, msg: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, msg: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, msg: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def critical(self, msg: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def exception(self, msg: str, **kwargs: Any) -> None: ...

    # @abstractmethod
    # def log(self, level: int, msg: str, **kwargs: Any) -> None: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
