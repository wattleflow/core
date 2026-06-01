# Module name: core/creational.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations
import inspect
import threading
from typing import Any
from abc import abstractmethod, ABC
from .framework import IWattleflow
# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"

# --------------------------------------------------------------------------- #
# region Interfaces                                                           #
# --------------------------------------------------------------------------- #


# Creational design patterns
# Abstract Factory Interface
class IFactory(IWattleflow, ABC):
    @staticmethod
    @abstractmethod
    def create(**kwargs) -> Any: ...


# Builder
class IBuilder(IWattleflow, ABC):
    """
    def make_part_a(self)
    def make_part_b(self)
    def build(self)
        a = self.make_part_a()
        b = self.make_part_b()
        return a + b
    """

    # @abstractmethod
    # def build_part(self):
    #     pass
    @abstractmethod
    def build(self):
        pass


# Factory Method Interface (ICreator, IProduct)
class IProduct(IWattleflow, ABC):
    @abstractmethod
    def operation(self):
        pass


class ICreator(IWattleflow, ABC):
    @abstractmethod
    def factory_method(self):
        pass


# Prototype Interface
class IPrototype(IWattleflow, ABC):
    @abstractmethod
    def clone(self):
        pass


# Singleton Interface
class ISingleton(IWattleflow, ABC):
    _lock = threading.Lock()
    _instances = {}

    @abstractmethod
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __new__(cls, *args, **kwargs):
        # if class is apstract, don't cache
        if inspect.isabstract(cls):
            return super().__new__(cls)

        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]


# --------------------------------------------------------------------------- #
# endregion Interfaces                                                        #
# --------------------------------------------------------------------------- #
