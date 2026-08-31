"""Social channel registry and gateway tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from uap.channels.registry import CHANNELS, channel_by_id, channels_status, list_configured_channel_ids
from uap.facebook_gateway import extract_facebook_message, verify_webhook
from uap.gateway_runner import UnifiedGateway
from uap.instagram_gateway import extract_instagram_message
from uap.x_gateway import extract_x_event, verify_crc
from uap.youtube_gateway import extract_youtube_webhook, poll_channel_ids


class ChannelRegistryTests(unittest.TestCase):
    def test_registry_has_core_socials(self):
        ids = {c.id for c in CHANNELS}
        for expected in (
            "telegram",
            "whatsapp",
            "discord",
            "slack",
            "x",
            "facebook",
            "youtube",
            "instagram",
        ):
            self.assertIn(expected, ids)

    def test_channels_status_shape(self):
        st = channels_status()
        self.assertIn("channels", st)
        self.assertIn("configuredCount", st)
        self.assertEqual(st["totalCount"], len(CHANNELS))
        self.assertIn("telegram", st["channels"])

    def test_channel_by_id(self):
        self.assertEqual(channel_by_id("x").name, "X (Twitter)")
        self.assertIsNone(channel_by_id("unknown"))


class ExtractorTests(unittest.TestCase):
    def test_x_dm_extract(self):
        payload = {
            "direct_message_events": [
                {
                    "sender_id": "42",
                    "message_create": {
                        "message_data": {"text": "hello from X"},
                    },
                }
            ]
        }
        uid, text, tid = extract_x_event(payload)
        self.assertEqual(uid, "42")
        self.assertEqual(text, "hello from X")
        self.assertIsNone(tid)

    def test_facebook_extract(self):
        psid, text = extract_facebook_message(
            {
                "entry": [
                    {
                        "messaging": [
                            {
                                "sender": {"id": "psid1"},
                                "message": {"text": "hi fb"},
                            }
                        ]
                    }
                ]
            }
        )
        self.assertEqual(psid, "psid1")
        self.assertEqual(text, "hi fb")

    def test_instagram_extract(self):
        igid, text = extract_instagram_message(
            {"igid": "ig99", "text": "story reply"}
        )
        self.assertEqual(igid, "ig99")

    def test_youtube_webhook_extract(self):
        author, text, tid = extract_youtube_webhook(
            {"authorChannelId": "UC123", "text": "great video", "commentThreadId": "t1"}
        )
        self.assertEqual(author, "UC123")
        self.assertEqual(tid, "t1")

    def test_x_crc(self):
        with mock.patch.dict(os.environ, {"UAP_X_API_SECRET": "secret"}):
            token = verify_crc("challenge-token")
            self.assertTrue(token.startswith("sha256="))

    def test_fb_verify(self):
        with mock.patch.dict(os.environ, {"UAP_FB_VERIFY_TOKEN": "narna-verify"}):
            self.assertEqual(verify_webhook("subscribe", "narna-verify", "12345"), "12345")
            self.assertIsNone(verify_webhook("subscribe", "wrong", "12345"))


class GatewayStatusTests(unittest.TestCase):
    def test_status_includes_registry(self):
        gw = UnifiedGateway(ask_fn=lambda *_: {}, workspace=tempfile.mkdtemp())
        st = gw.status()
        self.assertIn("channels", st)
        self.assertIn("configuredCount", st)

    def test_youtube_poll_channels_env(self):
        with mock.patch.dict(
            os.environ,
            {"UAP_YOUTUBE_POLL_CHANNELS": "UCa,UCb"},
            clear=False,
        ):
            self.assertEqual(poll_channel_ids(), ["UCa", "UCb"])


class JobDeliveryChannelTests(unittest.TestCase):
    def test_list_configured_empty_by_default(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("UAP_")}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(list_configured_channel_ids(), [])


if __name__ == "__main__":
    unittest.main()
