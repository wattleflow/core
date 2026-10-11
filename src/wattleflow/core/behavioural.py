# Module name: core/behavioural.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any, Generic, TypeVar, final

from .framework import IWattleflow

# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

__all__ = [
    "IHandler",
    "ICommand",
    "IInvoker",
    "IExpression",
    "IIterator",
    "ISyncAggregate",
    "IAsyncIterator",
    "IAsyncAggregate",
    "IMediator",
    "IColleague",
    "IMemento",
    "IOriginator",
    "IObserver",
    "IObservable",
    "IStateMachine",
    "IState",
    "IStateContext",
    "IStrategy",
    "IStrategyContext",
    "ITemplate",
    "IVisitor",
    "IElement",
    "ILogger",
]

# --------------------------------------------------------------------------- #
# region Types                                                                #
# --------------------------------------------------------------------------- #
Action = TypeVar("Action")  # action type
Context = TypeVar("Context")  # context type
Result = TypeVar("Result")  # result type
State = TypeVar("State")  # state type
Element = TypeVar("Element")  # traversed element type  [NFRQ-ORG-03]
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

    handle() returns the result of processing, or None when no handler in the
    chain accepted the request. This lets the sender detect an unhandled
    request and route it to a fallback (e.g. a dead letter channel).

    Interface:
        set_next(handler: IHandler) -> None
        handle(request: Any) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def set_next(self, handler: IHandler) -> None: ...

    @abstractmethod
    def handle(self, request: Any) -> Any: ...


# ICommand (ICommand, IInvoker) - Command interfaces
class ICommand(IWattleflow, ABC):
    """
    ICommand - Command abstract interface.

    Encapsulates a request as an object, decoupling the sender from the
    receiver. The caller invokes execute() without knowing what work it performs.

    Interface:
        execute(**kwargs: Any) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any: ...


class IInvoker(IWattleflow, ABC):
    """
    IInvoker - Command (invoker role) abstract interface.

    Holds a command and triggers it. Sits between the client and the command,
    allowing cross-cutting concerns such as logging or queuing.
    invoke() forwards its keyword arguments to the command's execute().

    Interface:
        set_command(command: ICommand) -> None
        invoke(**kwargs: Any) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def set_command(self, command: ICommand) -> None: ...

    @abstractmethod
    def invoke(self, **kwargs: Any) -> Any: ...


class IExpression(IWattleflow, Generic[Context, Result], ABC):
    """
    IExpression - Interpreter abstract interface.

    Evaluates an expression against a context. Composite expressions are built
    from simpler ones, each implementing interpret(). Parameterised over Context
    and Result for input/output type safety.

    Interface:
        interpret(context: Context) -> Result
    """

    __slots__ = ()

    @abstractmethod
    def interpret(self, context: Context) -> Result: ...


# Iterator (IIterator, ISyncAggregate)
class IIterator(IWattleflow, Iterator[Element], ABC):
    """
    IIterator - Iterator abstract interface.

    An iterator that knows how to build its underlying traversal via
    create_iterator(). The contract fixes no construction policy: laziness
    and caching are implementation decisions (see
    wattleflow.concrete.iterator.LazyIterator for the canonical policy).

    Interface:
        create_iterator() -> Iterator[Element]
        __next__() -> Element   (inherited abstract, from Iterator)
    """

    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> Iterator[Element]: ...


class ISyncAggregate(IWattleflow, Generic[Element], ABC):
    """
    ISyncAggregate - Iterator (aggregate role) abstract interface.

    Interface:
        create_iterator() -> IIterator[Element]
    """

    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> IIterator[Element]: ...


class IAsyncIterator(IWattleflow, AsyncIterator[Element], ABC):
    """
    IAsyncIterator - Asynchronous Iterator abstract interface.

    Asynchronous counterpart of IIterator; same contract shape, awaited
    traversal via __anext__ (inherited abstract, from AsyncIterator).
    Canonical lazy policy: wattleflow.concrete.iterator.LazyAsyncIterator.

    Interface:
        create_iterator() -> AsyncIterator[Element]
    """

    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> AsyncIterator[Element]: ...


class IAsyncAggregate(IWattleflow, Generic[Element], ABC):
    """
    IAsyncAggregate - Asynchronous Iterator (aggregate role) abstract interface.

    Interface:
        create_iterator() -> IAsyncIterator[Element]
    """

    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> IAsyncIterator[Element]: ...


# Mediator interfaces
class IMediator(IWattleflow, ABC):
    """
    IMediator - Mediator abstract interface.

    Receives events from colleagues and dispatches them to other colleagues
    via IColleague.on_event(). An implementation must not dispatch an event
    back to its sender, to prevent recursive notification loops.

    Interface:
        notify(sender: IColleague, event: Any, **kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def notify(self, sender: IColleague, event: Any, **kwargs: Any) -> None: ...


class IColleague(IWattleflow, ABC):
    """
    IColleague - Mediator (colleague role) abstract interface.

    Sends events through IMediator.notify() and receives them through
    on_event(). An implementation must not synchronously re-emit the received
    event from within on_event().

    Interface:
        set_mediator(mediator: IMediator) -> None
        on_event(event: Any, **kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def set_mediator(self, mediator: IMediator) -> None: ...

    @abstractmethod
    def on_event(self, event: Any, **kwargs: Any) -> None: ...


# IMemento - Memento Interfaces (IMemento, IOriginator)
class IMemento(IWattleflow, Generic[State], ABC):
    """
    IMemento - Memento abstract interface.

    Carries a captured snapshot of an originator's internal state.

    Interface:
        get_state() -> State
    """

    __slots__ = ()

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

    __slots__ = ()

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
        update(event: Any, **kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def update(self, event: Any, **kwargs: Any) -> None: ...


class IObservable(IWattleflow, ABC):
    """
    IObservable - Observer / Reactive Programming abstract interface.

    Interface:
        subscribe(observer: IObserver) -> None
        unsubscribe(observer: IObserver) -> None
    """

    __slots__ = ()

    @abstractmethod
    def subscribe(self, observer: IObserver) -> None: ...

    @abstractmethod
    def unsubscribe(self, observer: IObserver) -> None: ...


# IStateMachine - State Machine interface
class IStateMachine(IWattleflow, Generic[Action], ABC):
    """
    IStateMachine - State Machine abstract interface.

    Guards and applies transitions: can() tests whether an action is admissible
    in the current state, apply() performs it. Parameterised over Action.

    Interface:
        can(action: Action) -> bool
        apply(action: Action) -> None
    """

    __slots__ = ()

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

    __slots__ = ()

    @abstractmethod
    def handle(self, context: IStateContext, **kwargs: Any) -> None: ...


class IStateContext(IWattleflow, ABC):
    """
    IStateContext - State (context role) abstract interface.

    Interface:
        set_state(state: IState) -> None
        request(**kwargs: Any) -> None
    """

    __slots__ = ()

    @abstractmethod
    def set_state(self, state: IState) -> None: ...

    @abstractmethod
    def request(self, **kwargs: Any) -> None: ...


# IStrategy - (IStrategy, IStrategyContext) - Strategy interfaces
class IStrategy(IWattleflow, ABC):
    """
    IStrategy - Strategy abstract interface.

    Interface:
        execute(caller: IWattleflow, **kwargs: Any) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def execute(self, caller: IWattleflow, **kwargs: Any) -> Any: ...


class IStrategyContext(IWattleflow, ABC):
    """
    IStrategyContext - Strategy (context role) abstract interface.

    Interface:
        set_strategy(strategy: IStrategy) -> None
        execute_strategy(caller: IWattleflow, **kwargs: Any) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def set_strategy(self, strategy: IStrategy) -> None: ...

    @abstractmethod
    def execute_strategy(self, caller: IWattleflow, **kwargs: Any) -> Any: ...


# Template method (ITemplate)
class ITemplate(IWattleflow, ABC):
    """
    ITemplate - The template method defining the steps of the process.

    process() is the fixed algorithm and must not be overridden. initialise()
    runs first; if it raises, finalise() is not called. Once initialise()
    succeeds, finalise() always runs. after_task() is skipped when
    perform_task() raises.

    Interface:
        process() -> None   (template method, final)

        # Abstract
        initialise() -> None
        perform_task() -> None
        finalise() -> None

        # Hooks (optional, no-op by default)
        before_task() -> None
        after_task() -> None
    """

    __slots__ = ()

    @final
    def process(self) -> None:
        self.initialise()
        try:
            self.before_task()
            self.perform_task()
            self.after_task()
        finally:
            self.finalise()

    def before_task(self) -> None:  # noqa: B027 - optional hook
        """Optional hook called before perform_task(). No-op by default."""

    def after_task(self) -> None:  # noqa: B027 - optional hook
        """Optional hook called after perform_task(). No-op by default."""

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

    __slots__ = ()

    @abstractmethod
    def visit(self, element: IElement) -> Any: ...


class IElement(IWattleflow, ABC):
    """
    IElement - Abstract interface for elements that accept visitors.

    accept() returns the visitor's result, typically visitor.visit(self).

    Interface:
        accept(visitor: IVisitor) -> Any
    """

    __slots__ = ()

    @abstractmethod
    def accept(self, visitor: IVisitor) -> Any: ...


# ILogger interface
class ILogger(IObservable, ABC):
    """
    ILogger - Logger abstract interface.

    Standard severity-level logging API. Extends IObservable, so a logger may
    also publish events to subscribed observers.

    Interface:
        subscribe(observer: IObserver) -> None     (inherited)
        unsubscribe(observer: IObserver) -> None   (inherited)
        debug(msg: str, **kwargs: Any) -> None
        info(msg: str, **kwargs: Any) -> None
        warning(msg: str, **kwargs: Any) -> None
        error(msg: str, **kwargs: Any) -> None
        critical(msg: str, **kwargs: Any) -> None
        exception(msg: str, **kwargs: Any) -> None
    """

    __slots__ = ()

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


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
