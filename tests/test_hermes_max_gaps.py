"""WhatsApp Cloud + remote shell singularity stubs."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest import mock

from uap.shell_remote import exec_singularity, exec_vercel
from uap.whatsapp_gateway import (
    extract_whatsapp_cloud,
    whatsapp_backend,
    whatsapp_cloud_enabled,
)


class WhatsAppCloudTests(unittest.TestCase):
    def test_extract_cloud_payload(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "84901234567",
                                        "type": "text",
                                        "text": {"body": "Hello NARNA"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        frm, text = extract_whatsapp_cloud(payload)
        self.assertEqual(frm, "84901234567")
        self.assertEqual(text, "Hello NARNA")

    def test_cloud_enabled_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(whatsapp_cloud_enabled())
            self.assertEqual(whatsapp_backend(), "off")
        with mock.patch.dict(
            os.environ,
            {
                "UAP_WHATSAPP_TOKEN": "tok",
                "UAP_WHATSAPP_PHONE_NUMBER_ID": "123",
            },
            clear=False,
        ):
            self.assertTrue(whatsapp_cloud_enabled())
            self.assertEqual(whatsapp_backend(), "cloud")


class ShellRemoteStubTests(unittest.TestCase):
    def test_singularity_missing_url(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            out = exec_singularity(command="echo hi")
            self.assertFalse(out.get("ok"))
            self.assertEqual(out.get("backend"), "singularity")
            self.assertIn("UAP_SINGULARITY_EXEC_URL", str(out.get("error")))

    def test_vercel_missing_url(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            out = exec_vercel(command="echo hi")
            self.assertFalse(out.get("ok"))
            self.assertEqual(out.get("backend"), "vercel")

    def test_singularity_mocked_http(self):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"stdout": "ok\n", "exitCode": 0}).encode()

        with mock.patch.dict(
            os.environ,
            {"UAP_SINGULARITY_EXEC_URL": "https://example.test/exec"},
            clear=False,
        ):
            with mock.patch("urllib.request.urlopen", return_value=Resp()):
                out = exec_singularity(command="echo hi")
        self.assertTrue(out.get("ok"))
        self.assertEqual(out.get("stdout"), "ok\n")


if __name__ == "__main__":
    unittest.main()
