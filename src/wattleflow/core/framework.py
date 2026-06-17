# Module name: core/framework.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations
from typing import TypeVar
# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"


# --------------------------------------------------------------------------- #
# region Interface                                                            #
# --------------------------------------------------------------------------- #
# Concrete framework root (identity), not an interface: provides shared name /
# repr to every framework object. Contract enforcement lives in the design-pattern
# interfaces, which mix in abc.ABC explicitly alongside this base.
class IWattleflow:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = self.__class__.__name__

    def __str__(self) -> str:
        # Human-readable: just the object's name.
        return self.name

    def __repr__(self) -> str:
        # Unambiguous: include the concrete type for logging / debugging.
        return f"{type(self).__name__}(name={self.name!r})"


T = TypeVar("T")
W = TypeVar("W", bound=IWattleflow)
# --------------------------------------------------------------------------- #
# endregion Interface                                                         #
# --------------------------------------------------------------------------- #
