"""Test rejection of well-known seed/dev keys in production mode."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "web" / "backend"))


class WellKnownDevKeyTest(unittest.TestCase):
    def test_well_known_dev_key_hash(self) -> None:
        from app.auth import WELL_KNOWN_SEED_HASHES, hash_key

        seed_key = "uap_live_dev_local_key_change_in_prod"
        expected_hash = "5790c9c9a6eef649172e2867d5311512586536eb220df83943ac42e5f53c033f"
        self.assertEqual(hash_key(seed_key), expected_hash)
        self.assertIn(expected_hash, WELL_KNOWN_SEED_HASHES)

    def test_production_mode_detection(self) -> None:
        from app.auth import is_production_mode

        with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": ""}):
            self.assertTrue(is_production_mode())

        with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "mock", "SENTRY_ENVIRONMENT": "production"}):
            self.assertTrue(is_production_mode())

        with patch.dict(
            os.environ,
            {"UAP_CRYPTO_MODE": "mock", "SENTRY_ENVIRONMENT": "development"},
            clear=True,
        ):
            self.assertFalse(is_production_mode())

    def test_well_known_key_denied_in_production(self) -> None:
        from app.auth import is_key_denied

        seed_key = "uap_live_dev_local_key_change_in_prod"
        with patch.dict(
            os.environ,
            {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": "", "UAP_KEY_DENYLIST": ""},
        ):
            self.assertTrue(is_key_denied(seed_key))

    def test_well_known_key_allowed_in_dev(self) -> None:
        from app.auth import is_key_denied

        seed_key = "uap_live_dev_local_key_change_in_prod"
        with patch.dict(
            os.environ,
            {
                "UAP_CRYPTO_MODE": "mock",
                "SENTRY_ENVIRONMENT": "development",
                "UAP_KEY_DENYLIST": "",
            },
        ):
            self.assertFalse(is_key_denied(seed_key))


if __name__ == "__main__":
    unittest.main()
