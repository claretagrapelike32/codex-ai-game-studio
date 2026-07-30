from __future__ import annotations

from pathlib import Path
import unittest

from tools.validate_repository import Validator


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_complete_repository_contract(self) -> None:
        problems = Validator(ROOT).run()
        self.assertEqual([], [problem.render() for problem in problems])


if __name__ == "__main__":
    unittest.main()
