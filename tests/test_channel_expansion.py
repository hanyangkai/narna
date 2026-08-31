"""Phase S channel stubs + X poll + jobs delete."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from uap.agent_jobs import AgentJobStore
from uap.channels.registry import channels_status
from uap.imessage_gateway import extract_imessage, imessage_enabled
from uap.line_gateway import extract_line_message, format_agent_reply as line_fmt
from uap.linkedin_gateway import format_agent_reply as li_fmt
from uap.tiktok_gateway import format_agent_reply as tt_fmt
from uap.wechat_gateway import extract_wechat_message
from uap.x_gateway import poll_mentions, x_poll_ready


class ChannelExpansionTests(unittest.TestCase):
    def test_registry_includes_apac_channels(self):
        st = channels_status()
        ids = set(st["channels"].keys())
        for cid in ("line", "wechat", "imessage", "tiktok", "linkedin", "x"):
            self.assertIn(cid, ids)
        self.assertGreaterEqual(st["totalCount"], 15)

    def test_adqa_badges_on_formatters(self):
        out = {"answer": "ok", "dqs": 88, "guardian": "approve"}
        self.assertIn("ADQA", tt_fmt(out))
        self.assertIn("ADQA", li_fmt(out))
        self.assertIn("ADQA", line_fmt(out))

    def test_line_extract(self):
        payload = {
            "events": [
                {
                    "type": "message",
                    "message": {"type": "text", "text": "hello"},
                    "source": {"userId": "U123"},
                }
            ]
        }
        uid, text = extract_line_message(payload)
        self.assertEqual(uid, "U123")
        self.assertEqual(text, "hello")

    def test_wechat_extract(self):
        frm, text = extract_wechat_message(
            {"FromUserName": "wx1", "MsgType": "text", "Content": "hi"}
        )
        self.assertEqual(frm, "wx1")
        self.assertEqual(text, "hi")

    def test_imessage_extract(self):
        frm, text = extract_imessage({"data": {"handle": "+15551212", "text": "yo"}})
        self.assertEqual(frm, "+15551212")
        self.assertEqual(text, "yo")
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(imessage_enabled())

    def test_x_poll_ready_off_by_default(self):
        with mock.patch.dict("os.environ", {"UAP_X_BEARER_TOKEN": "tok"}, clear=False):
            # poll requires UAP_X_POLL=1
            with mock.patch.dict("os.environ", {"UAP_X_POLL": ""}, clear=False):
                self.assertFalse(x_poll_ready())

    def test_x_poll_mentions_mocked(self):
        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return b'{"data":[{"id":"99","text":"@bot hi","author_id":"1"}]}'

        with mock.patch.dict(
            "os.environ",
            {"UAP_X_BEARER_TOKEN": "tok", "UAP_X_USER_ID": "me"},
            clear=False,
        ):
            with mock.patch("urllib.request.urlopen", return_value=Resp()):
                rows = poll_mentions()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "99")

    def test_job_delete(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
            store = AgentJobStore(td)
            job = store.create(prompt="test", every_minutes=60)
            self.assertTrue(store.delete(job["jobId"]))
            self.assertIsNone(store.get(job["jobId"]))


if __name__ == "__main__":
    unittest.main()
