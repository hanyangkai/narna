#!/usr/bin/env python3
"""Test script for mobile API integration with NARNA agent runtime."""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from websockets import connect


BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key_here"  # Replace with actual API key


def test_pairing_flow():
    """Test mobile pairing flow."""
    print("=" * 60)
    print("TEST: Mobile Pairing Flow")
    print("=" * 60)
    
    # 1. Start pairing
    print("\n1. Starting pairing...")
    resp = requests.post(
        f"{BASE_URL}/v1/mobile/pairing/start",
        json={"device_name": "Test iPhone", "platform": "ios"},
        headers={"X-API-Key": API_KEY}
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code != 200:
        print("❌ Failed to start pairing")
        return None
    
    pairing_code = data["pairing_code"]
    print(f"✅ Pairing code: {pairing_code}")
    
    # 2. Verify pairing
    print(f"\n2. Verifying pairing with code {pairing_code}...")
    resp = requests.post(
        f"{BASE_URL}/v1/mobile/pairing/verify",
        json={"pairing_code": pairing_code}
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code != 200:
        print("❌ Failed to verify pairing")
        return None
    
    mobile_token = data["mobile_token"]
    print(f"✅ Mobile token: {mobile_token[:20]}...")
    
    return mobile_token


def test_bot_list(mobile_token: str):
    """Test listing bots."""
    print("\n" + "=" * 60)
    print("TEST: List Bots")
    print("=" * 60)
    
    resp = requests.get(
        f"{BASE_URL}/v1/mobile/bots",
        params={"mobile_token": mobile_token}
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code != 200:
        print("❌ Failed to list bots")
        return None
    
    print(f"✅ Found {len(data)} bot(s)")
    return data[0]["bot_id"] if data else "default"


def test_bot_thread(mobile_token: str, bot_id: str):
    """Test getting bot conversation thread."""
    print("\n" + "=" * 60)
    print("TEST: Get Bot Thread")
    print("=" * 60)
    
    resp = requests.get(
        f"{BASE_URL}/v1/mobile/bots/{bot_id}/thread",
        params={"mobile_token": mobile_token}
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code != 200:
        print("❌ Failed to get thread")
        return False
    
    print(f"✅ Got thread with {len(data['messages'])} message(s)")
    return True


def test_send_message(mobile_token: str, bot_id: str):
    """Test sending message to bot."""
    print("\n" + "=" * 60)
    print("TEST: Send Message to Bot")
    print("=" * 60)
    
    message = "Hello, NARNA! What's the weather like today?"
    print(f"Sending: {message}")
    
    resp = requests.post(
        f"{BASE_URL}/v1/mobile/bots/{bot_id}/message",
        json={"message": message},
        params={"mobile_token": mobile_token}
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code != 200:
        print("❌ Failed to send message")
        return False
    
    print("✅ Message sent successfully")
    return True


def test_approvals(mobile_token: str):
    """Test approval list."""
    print("\n" + "=" * 60)
    print("TEST: List Approvals")
    print("=" * 60)
    
    resp = requests.get(
        f"{BASE_URL}/v1/mobile/approvals",
        params={"mobile_token": mobile_token}
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code != 200:
        print("❌ Failed to list approvals")
        return False
    
    print(f"✅ Found {len(data)} pending approval(s)")
    return True


async def test_websocket(mobile_token: str, bot_id: str):
    """Test WebSocket connection."""
    print("\n" + "=" * 60)
    print("TEST: WebSocket Connection")
    print("=" * 60)
    
    ws_url = f"ws://localhost:8000/v1/mobile/bots/{bot_id}/stream?mobile_token={mobile_token}"
    
    try:
        async with connect(ws_url) as websocket:
            print("✅ WebSocket connected")
            
            # Wait for connection message
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            print(f"Received: {json.dumps(data, indent=2)}")
            
            # Send ping
            print("\nSending ping...")
            await websocket.send("ping")
            
            # Wait for pong
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)
            print(f"Received: {json.dumps(data, indent=2)}")
            
            if data.get("type") == "pong":
                print("✅ Ping/pong successful")
            
            print("\nListening for events (5 seconds)...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    print(f"Event: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("No more events received")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False
    
    return True


def test_revoke(mobile_token: str):
    """Test revoking mobile token."""
    print("\n" + "=" * 60)
    print("TEST: Revoke Mobile Token")
    print("=" * 60)
    
    resp = requests.delete(
        f"{BASE_URL}/v1/mobile/pairing/revoke",
        json={"mobile_token": mobile_token},
        headers={"X-API-Key": API_KEY}
    )
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if resp.status_code != 200:
        print("❌ Failed to revoke token")
        return False
    
    print("✅ Token revoked successfully")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NARNA Mobile API Integration Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    # Test pairing
    mobile_token = test_pairing_flow()
    if not mobile_token:
        print("\n❌ Pairing failed, cannot continue")
        sys.exit(1)
    
    # Test bot operations
    bot_id = test_bot_list(mobile_token)
    if not bot_id:
        print("\n❌ Bot list failed")
        sys.exit(1)
    
    test_bot_thread(mobile_token, bot_id)
    test_send_message(mobile_token, bot_id)
    test_approvals(mobile_token)
    
    # Test WebSocket
    asyncio.run(test_websocket(mobile_token, bot_id))
    
    # Test revoke
    test_revoke(mobile_token)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "your_api_key_here":
        API_KEY = sys.argv[1]
    
    if API_KEY == "your_api_key_here":
        print("Usage: python test_mobile_integration.py <api_key>")
        print("Or set API_KEY in the script")
        sys.exit(1)
    
    main()
