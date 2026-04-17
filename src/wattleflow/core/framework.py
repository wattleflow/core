# Module name: core/framework.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence


from __future__ import annotations
from abc import ABC
from typing import TypeVar


__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"


class IWattleflow(ABC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = self.__class__.__name__

    def __repr__(self) -> str:
        return self.name


T = TypeVar("T")
W = TypeVar("W", bound=IWattleflow)
