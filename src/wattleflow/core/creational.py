# Module Name: core/abstract/behavioural.py
# Author: (wattleflow@outlook.com)
# Copyright: (c) 2024 WattleFlow
# License: Apache 3 License
# Description: This modul contains abstract behavioural design patterns.


from abc import abstractmethod, ABC
from .framework import IWattleflow

"""
Creational Interfaces
    Abstract Factory
        IFactory
    Builder
        IBuilder
    Factory Method
        ICreator
        IProduct
    Prototype
        IPrototype
    Singleton
        ISingleton
"""


# Creational design patterns
# Abstract Factory Interface
class IFactory(IWattleflow, ABC):
    @staticmethod
    def create(self):
        pass


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


# Singletone Interface
class ISingleton(IWattleflow, ABC):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
