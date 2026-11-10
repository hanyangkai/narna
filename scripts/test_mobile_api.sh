#!/bin/bash
# Test NARNA Mobile API endpoints

set -e

BASE_URL="${BASE_URL:-http://localhost:8765}"
API_KEY="${API_KEY:-uap_live_dev_local_key_change_in_prod}"

echo "🧪 Testing NARNA Mobile API"
echo "Base URL: $BASE_URL"
echo ""

# Health check
echo "1️⃣  Testing health endpoint..."
curl -s "$BASE_URL/v1/mobile/health" | python3 -m json.tool
echo ""

# Start pairing
echo "2️⃣  Testing pairing start (desktop)..."
PAIRING_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/mobile/pairing/start" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"device_name":"Test iPhone","platform":"ios"}')

echo "$PAIRING_RESPONSE" | python3 -m json.tool
PAIRING_CODE=$(echo "$PAIRING_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['pairing_code'])")
echo ""
echo "✅ Pairing code: $PAIRING_CODE"
echo ""

# Verify pairing
echo "3️⃣  Testing pairing verify (mobile)..."
VERIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/v1/mobile/pairing/verify" \
  -H "Content-Type: application/json" \
  -d "{\"pairing_code\":\"$PAIRING_CODE\"}")

echo "$VERIFY_RESPONSE" | python3 -m json.tool
MOBILE_TOKEN=$(echo "$VERIFY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['mobile_token'])")
echo ""
echo "✅ Mobile token: ${MOBILE_TOKEN:0:30}..."
echo ""

# List bots
echo "4️⃣  Testing list bots..."
curl -s "$BASE_URL/v1/mobile/bots?mobile_token=$MOBILE_TOKEN" | python3 -m json.tool
echo ""

# Get bot thread
echo "5️⃣  Testing get bot thread..."
curl -s "$BASE_URL/v1/mobile/bots/bot_1/thread?mobile_token=$MOBILE_TOKEN" | python3 -m json.tool
echo ""

# Send message
echo "6️⃣  Testing send message..."
curl -s -X POST "$BASE_URL/v1/mobile/bots/bot_1/message?mobile_token=$MOBILE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello from mobile test!"}' | python3 -m json.tool
echo ""

# List approvals
echo "7️⃣  Testing list approvals..."
curl -s "$BASE_URL/v1/mobile/approvals?mobile_token=$MOBILE_TOKEN" | python3 -m json.tool
echo ""

# Revoke pairing
echo "8️⃣  Testing revoke pairing..."
curl -s -X DELETE "$BASE_URL/v1/mobile/pairing/revoke" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"mobile_token\":\"$MOBILE_TOKEN\"}" | python3 -m json.tool
echo ""

echo "✅ All tests passed!"
echo ""
echo "Next steps:"
echo "- Test WebSocket: wscat -c \"ws://localhost:8765/v1/mobile/bots/bot_1/stream?mobile_token=...\""
echo "- Build iOS app: see apps/mobile-ios/"
echo "- Build Android app: see apps/mobile-android/"
