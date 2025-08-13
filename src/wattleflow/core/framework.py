# Module Name: core/abstract/framework.py
# Author: (wattleflow@outlook.com)
# Copyright: (c) 2022-2025 WattleFlow
# License: Apache 2 Licence
# Description: This modul contains abstract interfaces.

from abc import ABC
from typing import Optional, TypeVar


class IWattleflow(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.name = self.__class__.__name__

    def __getattr__(self, name: str) -> Optional[object]:
        return self.__dict__.get(name, None)


T = TypeVar("T")
W = TypeVar("W", bound=IWattleflow)
