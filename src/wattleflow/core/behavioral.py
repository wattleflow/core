# Module name: behavioural.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2025 WattleFlow. All rights reserved.
# License: Apache 2 Licence


from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Generic, Iterator, Optional, TypeVar
from .framework import IWattleflow, T

C = TypeVar("C")  # context type
R = TypeVar("R")  # result type
S = TypeVar("S")  # state type


# IHandler - (IHandler) - Chain of responsiblity interfaces
class IHandler(IWattleflow, ABC):
    """
    IHandler

    Interface:
        set_next(handler: IHandler)
        handle(request: Any)
    """

    @abstractmethod
    def set_next(self, handler: "IHandler") -> None: ...

    @abstractmethod
    def handle(self, request: Any) -> None: ...


# ICommand (ICommand, IInvoker) - Command interface
class ICommand(IWattleflow, ABC):
    """
    ICommand - Chain of responsibilty abstract interface.

    Interface:
        execute(*args, **kwargs)
    """

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any: ...


class IInvoker(IWattleflow, ABC):
    """
    IInvoker - Chain of responsibilty abstract interface.

    Interface:
        set_command(command: ICommand) -> None
        invoke() -> Any
    """

    @abstractmethod
    def set_command(self, command: ICommand) -> None: ...

    @abstractmethod
    def invoke(self) -> Any: ...


class IExpression(IWattleflow, Generic[C, R], ABC):
    """
    IExpression - abstract interface.

    Interface:
        interpret(context: C) -> R
    """

    @abstractmethod
    def interpret(self, context: C) -> R: ...


# Iterator (IIterator, ISyncAggregate)
class IIterator(IWattleflow, Iterator[T], Generic[T], ABC):
    def __init__(self) -> None:
        super().__init__()
        self._iterator: Optional[Iterator[T]] = None

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        if self._iterator is None:
            self._iterator = self.create_iterator()
        return next(self._iterator)

    @abstractmethod
    def create_iterator(self) -> Iterator[T]: ...


# ISyncAggregate
class ISyncAggregate(IWattleflow, Generic[T], ABC):
    @abstractmethod
    def create_iterator(self) -> IIterator[T]: ...


# IAsyncIterator (IAsyncIterator, IAsyncAggregate)
class IAsyncIterator(IWattleflow, AsyncIterator[T], Generic[T], ABC):
    def __init__(self) -> None:
        super().__init__()
        self._iterator: Optional[AsyncIterator[T]] = None

    def __aiter__(self) -> AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        if self._iterator is None:
            # create_iterator is synchronous and returns an AsyncIterator
            self._iterator = self.create_iterator()
        return await self._iterator.__anext__()

    @abstractmethod
    def create_iterator(self) -> AsyncIterator[T]: ...


class IAsyncAggregate(IWattleflow, Generic[T], ABC):
    @abstractmethod
    def create_iterator(self) -> IAsyncIterator[T]: ...


# Mediator interfaces
class IMediator(IWattleflow, ABC):
    """
    IMediator - abstract interface.

    Interface:
        notify(sender: IColleague, event: Any, **data: Any) -> None
    """

    @abstractmethod
    def notify(self, sender: "IColleague", event: Any, **data: Any) -> None: ...


class IColleague(IWattleflow, ABC):
    """
    IColleage - abstract interface.

    Interface:
        set_mediator(mediator: IMediator) -> None
        event_occurred(event: Any, **data: Any) -> None
    """

    @abstractmethod
    def set_mediator(self, mediator: IMediator) -> None: ...

    @abstractmethod
    def event_occurred(self, event: Any, **data: Any) -> None: ...


# IMemento - Memento Interfaces (IMemento, IOriginator)
class IMemento(IWattleflow, Generic[S], ABC):
    """
    IMemento - abstract interface.

    Interface:
        get_state(self) -> Any
    """

    @abstractmethod
    def get_state(self) -> S: ...


class IOriginator(IWattleflow, Generic[S], ABC):
    """
    IOriginator - abstract interface.

    Interface:
        save_state() -> None
        restore_state(memento) -> None
    """

    @abstractmethod
    def save_state(self) -> IMemento[S]: ...

    @abstractmethod
    def restore_state(self, memento: IMemento[S]) -> None: ...


# Observer interfaces - Reactive Programming Interfaces
class IObserver(IWattleflow, ABC):
    """
    IObserver - Observer/Reactive Programming Interface

    Interface:
        update(event: Any, *args: Any, **kwargs: Any) -> None
    """

    @abstractmethod
    def update(self, event: Any, *args: Any, **kwargs: Any) -> None: ...


class IObservable(IWattleflow, ABC):
    """
    IObservable - Observer/Reactive Programming Interface desing pattern
                  abstract interface.

    Interface:
        subscribe(observer: IObserver) -> None
    """

    @abstractmethod
    def subscribe(self, observer: IObserver) -> None: ...


# IState (IState, IStateContext) - State interfaces
class IState(IWattleflow, ABC):
    """
    IState - State abstract interface.

    Interface:
        def handle(self, context: "IStateContext", *args: Any, **kwargs: Any)
    """

    @abstractmethod
    def handle(self, context: "IStateContext", *args: Any, **kwargs: Any) -> None: ...


class IStateContext(IWattleflow, ABC):
    """
    IStateContext - State abstract interface.

    Interface:
        set_state(state: IState) -> None: ...
        request(*args: Any, **kwargs: Any) -> None: ...
    """

    @abstractmethod
    def set_state(self, state: IState) -> None: ...

    @abstractmethod
    def request(self, *args: Any, **kwargs: Any) -> None: ...


# IStrategy - (IStrategy, IStrategyContext) - Strategy interfaces
class IStrategy(IWattleflow, ABC):
    """
    IStrategy - Strategy abstract interface.

    Interface:
        execute(*args, **kwargs) -> Any
    """

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any: ...


class IStrategyContext(IWattleflow, ABC):
    """
    IStrategyContext

    Interface:
        set_strategy(strategy: IStrategy) -> None
        execute_strategy(*args, **kwargs) -> Any
    """

    @abstractmethod
    def set_strategy(self, strategy: IStrategy) -> None: ...

    @abstractmethod
    def execute_strategy(self, *args, **kwargs) -> Any: ...


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


# IVisitor (IVisitor IElement) - Visitor interfaces
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

    @abstractmethod
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def subscribe(self, observer: IObserver) -> None: ...

    # @abstractmethod
    # def log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None: ...


# Mark IState.handle as @abstractmethod so implementers must implement handle.
# Call before_task and after_task hooks in ITemplate.process around perform_task.
# Standardize IAsyncIterator.create_iterator to be a synchronous method returning an AsyncIterator (remove awaiting create call).
