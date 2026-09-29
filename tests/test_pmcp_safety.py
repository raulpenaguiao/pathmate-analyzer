"""The clean reference coaching must never pass the write guard (Raul,
2026-09-29, agents/RULES.md "PMCP coachings")."""
import asyncio
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "coaching-bundle-export"))
import _pmcp_safety as S  # noqa: E402


class FakePage:
    def __init__(self, title):
        self.title = title

    async def evaluate(self, _js, *args):
        return self.title


def guard(title, expected=None):
    return asyncio.run(S.assert_expected_coaching(FakePage(title), expected))


class ProtectedCoachingTest(unittest.TestCase):
    def test_exact_names(self):
        self.assertTrue(S.is_protected("ALEX v01 zum Ausprobieren 2"))
        self.assertFalse(S.is_protected("ALEX v01 zum Ausprobieren"))
        self.assertFalse(S.is_protected(None))

    def test_sandbox_passes(self):
        self.assertEqual(guard('Coaching "ALEX v01 zum Ausprobieren"'),
                         "ALEX v01 zum Ausprobieren")

    def test_clean_copy_refused_even_if_expected(self):
        with self.assertRaises(S.WrongCoachingError):
            guard('Coaching "ALEX v01 zum Ausprobieren 2"')
        with self.assertRaises(S.WrongCoachingError):
            guard('Coaching "ALEX v01 zum Ausprobieren 2"', expected="ALEX v01 zum Ausprobieren 2")

    def test_env_override_cannot_unprotect(self):
        os.environ[S.ENV_VAR] = "ALEX v01 zum Ausprobieren 2"
        try:
            with self.assertRaises(S.WrongCoachingError):
                guard('Coaching "ALEX v01 zum Ausprobieren 2"')
        finally:
            del os.environ[S.ENV_VAR]


if __name__ == "__main__":
    unittest.main()
