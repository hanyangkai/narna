"""Gateway config + desktop runtime tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.gateway_config import (
    apply_gateway_to_env,
    load_gateway_config,
    save_gateway_config,
)


class GatewayConfigTests(unittest.TestCase):
    def test_save_and_apply(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            save_gateway_config(
                {"telegramBotToken": "123:ABC", "gatewayEnabled": True},
                td,
            )
            cfg = load_gateway_config(td)
            self.assertTrue(cfg.get("gatewayEnabled"))
            apply_gateway_to_env(td)
            import os

            self.assertEqual(os.environ.get("UAP_TELEGRAM_BOT_TOKEN"), "123:ABC")


if __name__ == "__main__":
    unittest.main()
