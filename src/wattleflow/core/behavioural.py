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


# Chain of Responsibility
class IHandler(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def set_next(self, handler: IHandler) -> None: ...

    @abstractmethod
    def handle_request(self, request: Any) -> Any: ...


# Command
class ICommand(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any: ...


class IInvoker(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def set_command(self, command: ICommand) -> None: ...

    @abstractmethod
    def invoke(self, **kwargs: Any) -> Any: ...


# Interpreter
class IExpression(IWattleflow, Generic[Context, Result], ABC):
    __slots__ = ()

    @abstractmethod
    def interpret(self, context: Context) -> Result: ...


# Iterator
class IIterator(IWattleflow, Iterator[Element], ABC):
    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> Iterator[Element]: ...


class ISyncAggregate(IWattleflow, Generic[Element], ABC):
    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> IIterator[Element]: ...


class IAsyncIterator(IWattleflow, AsyncIterator[Element], ABC):
    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> AsyncIterator[Element]: ...


class IAsyncAggregate(IWattleflow, Generic[Element], ABC):
    __slots__ = ()

    @abstractmethod
    def create_iterator(self) -> IAsyncIterator[Element]: ...


# Mediator
class IMediator(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def colleague_changed(self, sender: IColleague, event: Any, **kwargs: Any) -> None: ...


class IColleague(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def set_mediator(self, mediator: IMediator) -> None: ...

    @abstractmethod
    def on_event(self, event: Any, **kwargs: Any) -> None: ...


# Memento
class IMemento(IWattleflow, Generic[State], ABC):
    __slots__ = ()

    @abstractmethod
    def get_state(self) -> State: ...


class IOriginator(IWattleflow, Generic[State], ABC):
    __slots__ = ()

    @abstractmethod
    def save_state(self) -> IMemento[State]: ...

    @abstractmethod
    def restore_state(self, memento: IMemento[State]) -> None: ...


# Observer
class IObserver(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def update(self, event: Any, **kwargs: Any) -> None: ...


class IObservable(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def attach(self, observer: IObserver) -> None: ...

    @abstractmethod
    def detach(self, observer: IObserver) -> None: ...

    @abstractmethod
    def notify(self, event: Any, **kwargs: Any) -> None: ...


# State Machine
class IStateMachine(IWattleflow, Generic[Action], ABC):
    __slots__ = ()

    @abstractmethod
    def can(self, action: Action) -> bool: ...

    @abstractmethod
    def apply(self, action: Action) -> None: ...


# State
class IState(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def handle(self, context: IStateContext, **kwargs: Any) -> None: ...


class IStateContext(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def set_state(self, state: IState) -> None: ...

    @abstractmethod
    def request(self, **kwargs: Any) -> None: ...


# Strategy
class IStrategy(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def algorithm(self, caller: IWattleflow, **kwargs: Any) -> Any: ...


class IStrategyContext(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def set_strategy(self, strategy: IStrategy) -> None: ...

    @abstractmethod
    def execute_strategy(self, caller: IWattleflow, **kwargs: Any) -> Any: ...


# Template Method
class ITemplate(IWattleflow, ABC):
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "process" in vars(cls):
            raise TypeError(f"{cls.__name__} must not override ITemplate.process().")

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
        return None

    def after_task(self) -> None:  # noqa: B027 - optional hook
        return None

    @abstractmethod
    def initialise(self) -> None: ...

    @abstractmethod
    def perform_task(self) -> None: ...

    @abstractmethod
    def finalise(self) -> None: ...


# Visitor
class IVisitor(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def visit(self, element: IElement) -> Any: ...


class IElement(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def accept(self, visitor: IVisitor) -> Any: ...


# Logger
class ILogger(IWattleflow, ABC):
    __slots__ = ()

    @abstractmethod
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def fatal(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
