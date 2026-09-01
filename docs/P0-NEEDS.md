# P0 setup — cần gì từ bạn?

**Mục tiêu:** ≥1 paying customer (crypto) + Telegram bot demo trên prod.

**Trạng thái VPS (2026-08-28):**

| Item | Prod hiện tại |
|------|----------------|
| `UAP_CRYPTO_MODE` | `live` |
| `UAP_CRYPTO_BOT_ENABLED` | `1` |
| RPC 5 chains | configured |
| `UAP_BILLING_MODE` | `mock` (đúng — plan flip qua on-chain, không card) |
| `UAP_TELEGRAM_BOT_TOKEN` | **trống** → gateway container **chưa chạy** |
| Receiver wallet | `0xa62297ec44dd59824f34132f9e8b3157b8b7f51a` (mặc định compose) |

---

## 1. Telegram demo (5 phút)

**Bạn cần gửi:**

| Secret | Lấy ở đâu |
|--------|-----------|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` → copy token dạng `123456:ABC…` |

**Tùy chọn:**

| Secret | Mục đích |
|--------|----------|
| `UAP_TELEGRAM_WEBHOOK_SECRET` | Nếu dùng webhook thay poll (gateway profile mặc định **poll**, không bắt buộc) |

**Sau khi có token — chạy (hoặc bảo agent chạy):**

```bash
TELEGRAM_BOT_TOKEN='123456:ABC…' ./scripts/vps_enable_telegram.sh
```

Hoặc GitHub Actions secret `TELEGRAM_BOT_TOKEN` + deploy workflow.

**Verify:** DM bot trên Telegram → NARNA trả lời + DQS. `GET /v1/agent/gateway/status` → `telegram.configured: true`, container `selfhost-gateway-1` running.

---

## 2. Crypto billing E2E — paying customer đầu tiên

**Infra đã sẵn.** Không cần code thêm — cần **một lần thanh toán thật** (hoặc bạn tự test).

**Bạn cần xác nhận:**

| Câu hỏi | Tại sao |
|---------|---------|
| Ví `0xa62297ec44dd59824f34132f9e8b3157b8b7f51a` là ví bạn kiểm soát? | Bot chỉ credit plan khi USDC/USDT vào đúng ví này |
| Muốn đổi ví? | Gửi địa chỉ EVM mới → patch `UAP_CRYPTO_RECEIVER_WALLET` trên VPS |

**Flow test (khuyến nghị Base — phí thấp):**

1. Vào https://narna.org/billing
2. Paste API key (`uap_live_…` từ Console/Settings)
3. Chọn **Cloud** · **Base** · **USDC** → Pay
4. Gửi **đúng số tiền** (vd `20.01`) tới wallet trên invoice
5. Đợi ~2–5 phút → Refresh → plan `cloud` + `planExpiresAt`

**Nếu muốn test không tốn tiền (dev only):** trên VPS tạm `UAP_ALLOW_MOCK_PLAN=1` — **không** dùng cho launch thật.

**RPC rate-limit:** nếu bot chậm, gửi Alchemy/Infura URLs:

```
UAP_BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
UAP_POLYGON_RPC_URL=…
```

---

## 3. Tùy chọn (không chặn P0)

| Item | Secret | Ghi chú |
|------|--------|---------|
| Live Ask trên server (không BYOK browser) | `OPENROUTER_API_KEY` | Hermes-default = user BYOK; server key chỉ cho demo ops |
| Discord / Slack gateway | `DISCORD_BOT_TOKEN`, `SLACK_BOT_TOKEN` | Sau Telegram |

---

## Checklist gửi agent

Copy-paste khi có:

```
TELEGRAM_BOT_TOKEN=…
# optional:
UAP_CRYPTO_RECEIVER_WALLET=0x…   # nếu đổi ví
UAP_BASE_RPC_URL=…               # nếu bot chậm
```

Agent sẽ: patch VPS `.env` → redeploy gateway → verify status.
