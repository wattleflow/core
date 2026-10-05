# Module name: tools/tests/test_criterion.py
# Author: (wattleflow@outlook.com)
# Copyright: © 2022–2026 WattleFlow. All rights reserved.
# License: Apache 2 Licence

"""The criterion this distribution ships names the documentation version it is written against."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

CRITERION = Path(__file__).resolve().parents[1] / "dictionary.json"


class CriterionTest(unittest.TestCase):
    def test_documentation_version(self) -> None:
        doc = json.loads(CRITERION.read_text(encoding="utf-8"))
        self.assertEqual(doc.get("documentation_version"), "v0.0.5")


if __name__ == "__main__":
    unittest.main()
