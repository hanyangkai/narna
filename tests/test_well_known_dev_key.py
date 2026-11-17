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

        with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": "production"}):
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

        with patch.dict(
            os.environ,
            {
                "UAP_CRYPTO_MODE": "mock",
                "SENTRY_ENVIRONMENT": "production",
                "UAP_KEY_DENYLIST": "",
            },
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

    def test_manual_denylist_overrides(self) -> None:
        from app import auth
        from app.auth import hash_key, is_key_denied, load_key_denylist

        test_key = "some_random_test_key"
        test_hash = hash_key(test_key)

        with patch.dict(
            os.environ,
            {
                "UAP_CRYPTO_MODE": "mock",
                "SENTRY_ENVIRONMENT": "",
                "UAP_KEY_DENYLIST": test_hash,
            },
        ):
            auth._KEY_DENYLIST = load_key_denylist()
            self.assertTrue(is_key_denied(test_key))

        with patch.dict(
            os.environ,
            {
                "UAP_CRYPTO_MODE": "live",
                "SENTRY_ENVIRONMENT": "",
                "UAP_KEY_DENYLIST": test_hash,
            },
        ):
            auth._KEY_DENYLIST = load_key_denylist()
            self.assertTrue(is_key_denied(test_key))

    def test_seed_dev_org_skipped_in_production(self) -> None:
        from app.main import _seed_dev_org

        with patch.dict(os.environ, {"UAP_CRYPTO_MODE": "live", "SENTRY_ENVIRONMENT": ""}):
            try:
                _seed_dev_org()
            except Exception as e:
                msg = str(e).lower()
                if "database" in msg or "session" in msg:
                    self.fail(
                        f"_seed_dev_org should return early in prod mode, but attempted DB access: {e}"
                    )


if __name__ == "__main__":
    unittest.main()
