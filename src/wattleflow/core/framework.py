# Module name: core/framework.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

# --------------------------------------------------------------------------- #
# region Imports                                                              #
# --------------------------------------------------------------------------- #
from __future__ import annotations
from abc import ABC, abstractmethod
# --------------------------------------------------------------------------- #
# endregion Imports                                                           #
# --------------------------------------------------------------------------- #

__author__ = "WattleFlow"
__copyright__ = "© 2022–2026 WattleFlow. All rights reserved"
__license__ = "Apache 2 Licence"


# --------------------------------------------------------------------------- #
# region Interface                                                            #
# --------------------------------------------------------------------------- #
class IWattleflow(ABC):
    """
    IWattleflow - root abstract interface of the framework.

    The single contract every framework object carries: a stable, readable
    identity. `name` MUST be stable for the lifetime of the object and SHOULD
    be derived from the concrete type rather than stored as mutable state
    (integrity: a forgeable name forges audit trails downstream).

    The core layer declares this contract only. The canonical implementation
    (name derived from type(self).__name__) lives with the consumer, e.g.
    wattleflow.concrete.wattleflow.Wattleflow.

    Interface:
        name -> str  (read-only property)
    """

    # The root contributes no storage, so any subclass that opts into
    # __slots__ can be truly dict-free.
    __slots__ = ()

    @property
    @abstractmethod
    def name(self) -> str: ...


# --------------------------------------------------------------------------- #
# endregion Interface                                                         #
# --------------------------------------------------------------------------- #
