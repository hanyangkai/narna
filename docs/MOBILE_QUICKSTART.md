# NARNA Mobile API - Quick Start Guide

Get your mobile app connected to NARNA agents in 5 minutes.

## Prerequisites

- NARNA backend running (`uvicorn app.main:app`)
- Organization API key
- Redis (optional, auto-falls back to in-memory)

## Step 1: Run Database Migration

```bash
cd /workspace
python scripts/migrate_mobile_tables.py
```

**Output:**
```
✅ Database migration completed successfully!
  ✅ mobile_devices table exists
  ✅ approval_requests table exists
```

## Step 2: Start Backend Server

```bash
cd web/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 3: Test Pairing Flow

### Generate Pairing Code

```bash
curl -X POST http://localhost:8000/v1/mobile/pairing/start \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Test iPhone",
    "platform": "ios"
  }'
```

**Response:**
```json
{
  "pairing_code": "123456",
  "qr_data": "narna://pair?code=123456&org=dev",
  "expires_at": "2024-01-01T12:05:00Z"
}
```

### Verify Pairing

```bash
curl -X POST http://localhost:8000/v1/mobile/pairing/verify \
  -H "Content-Type: application/json" \
  -d '{
    "pairing_code": "123456"
  }'
```

**Response:**
```json
{
  "mobile_token": "narna_mobile_xxxxx",
  "agent_name": "dev",
  "org_id": 1
}
```

Save the `mobile_token` - you'll need it for all other requests!

## Step 4: Test Bot Operations

### List Bots

```bash
export TOKEN="narna_mobile_xxxxx"

curl "http://localhost:8000/v1/mobile/bots?mobile_token=$TOKEN"
```

### Send Message

```bash
curl -X POST "http://localhost:8000/v1/mobile/bots/default/message?mobile_token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, NARNA! What can you help me with?"
  }'
```

### Get Conversation Thread

```bash
curl "http://localhost:8000/v1/mobile/bots/default/thread?mobile_token=$TOKEN"
```

## Step 5: Test WebSocket Connection

Use `websocat` or your WebSocket client:

```bash
websocat "ws://localhost:8000/v1/mobile/bots/default/stream?mobile_token=$TOKEN"
```

**Send:**
```
ping
```

**Receive:**
```json
{"type": "connected", "bot_id": "default", "timestamp": "..."}
{"type": "pong", "timestamp": "..."}
```

## Step 6: Run Automated Tests

```bash
python scripts/test_mobile_integration.py your_api_key
```

**Expected output:**
```
✅ Pairing code: 123456
✅ Mobile token: narna_mobile_...
✅ Found 1 bot(s)
✅ Got thread with 0 message(s)
✅ Message sent successfully
✅ Found 0 pending approval(s)
✅ WebSocket connected
✅ Ping/pong successful
✅ Token revoked successfully
✅ All tests completed!
```

## Common Issues

### Issue: "Invalid or expired mobile token"
**Solution:** Token may have expired (30 days). Generate new pairing code.

### Issue: "Failed to list bots"
**Solution:** 
- Check UAP_HOME environment variable
- Ensure workspace directory exists
- Verify organization has proper configuration

### Issue: WebSocket connection refused
**Solution:**
- Check server is running on correct port
- Verify mobile_token is valid
- Ensure no firewall blocking WebSocket

### Issue: "Redis connection failed"
**Solution:** Redis is optional. System automatically falls back to in-memory storage.

## Mobile App Integration

### iOS Swift Example

```swift
import Foundation

class NARNAMobileClient {
    let baseURL = "http://localhost:8000"
    var mobileToken: String?
    
    func startPairing(apiKey: String, deviceName: String) async throws -> String {
        let url = URL(string: "\(baseURL)/v1/mobile/pairing/start")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["device_name": deviceName, "platform": "ios"]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(PairingStartResponse.self, from: data)
        return response.pairingCode
    }
    
    func verifyPairing(code: String) async throws {
        let url = URL(string: "\(baseURL)/v1/mobile/pairing/verify")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["pairing_code": code]
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(PairingVerifyResponse.self, from: data)
        self.mobileToken = response.mobileToken
    }
    
    func sendMessage(botId: String, message: String) async throws {
        guard let token = mobileToken else { throw NARNAError.notAuthenticated }
        
        let url = URL(string: "\(baseURL)/v1/mobile/bots/\(botId)/message?mobile_token=\(token)")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["message": message]
        request.httpBody = try JSONEncoder().encode(body)
        
        let _ = try await URLSession.shared.data(for: request)
    }
}
```

### Android Kotlin Example

```kotlin
import okhttp3.*
import kotlinx.coroutines.*

class NARNAMobileClient {
    private val client = OkHttpClient()
    private val baseUrl = "http://localhost:8000"
    private var mobileToken: String? = null
    
    suspend fun startPairing(apiKey: String, deviceName: String): String {
        val request = Request.Builder()
            .url("$baseUrl/v1/mobile/pairing/start")
            .header("X-API-Key", apiKey)
            .post("""{"device_name": "$deviceName", "platform": "android"}""".toRequestBody())
            .build()
        
        val response = client.newCall(request).execute()
        val json = JSONObject(response.body!!.string())
        return json.getString("pairing_code")
    }
    
    suspend fun verifyPairing(code: String) {
        val request = Request.Builder()
            .url("$baseUrl/v1/mobile/pairing/verify")
            .post("""{"pairing_code": "$code"}""".toRequestBody())
            .build()
        
        val response = client.newCall(request).execute()
        val json = JSONObject(response.body!!.string())
        mobileToken = json.getString("mobile_token")
    }
    
    suspend fun sendMessage(botId: String, message: String) {
        val request = Request.Builder()
            .url("$baseUrl/v1/mobile/bots/$botId/message?mobile_token=$mobileToken")
            .post("""{"message": "$message"}""".toRequestBody())
            .build()
        
        client.newCall(request).execute()
    }
}
```

## Next Steps

1. ✅ Set up mobile app pairing UI
2. ✅ Implement WebSocket reconnection logic
3. ✅ Add push notifications for approvals
4. ✅ Build conversation UI with message history
5. ✅ Test approval gates with real agent actions

## API Reference

See [MOBILE_INTEGRATION.md](./MOBILE_INTEGRATION.md) for complete API documentation.

## Support

- GitHub Issues: https://github.com/hanyangkai/narna/issues
- Documentation: https://narna.ai/docs/mobile
- Discord: https://discord.gg/narna
