"""
Quick smoke test for QwenClient → Ollama /api/chat connection.
No MCP, no Django — just a raw chat completion call.
"""

import sys
import os
import json
import time

# Ensure ai-agent dir is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qwen_client import QwenClient


def main():
    print("=" * 55)
    print("  QwenClient → Ollama Smoke Test")
    print("=" * 55)

    # ── 1. Initialize client ─────────────────────────────
    try:
        client = QwenClient()
        print(f"\n✅ Client initialized")
        print(f"   Endpoint : {client.chat_url}")
        print(f"   Model    : {client.model}")
        print(f"   Temp     : {client.temperature}")
        print(f"   num_ctx  : {client.num_ctx}")
        print(f"   num_pred : {client.num_predict}")
    except Exception as e:
        print(f"\n❌ Client init failed: {e}")
        sys.exit(1)

    # ── 2. Send test message ─────────────────────────────
    messages = [
        {"role": "system", "content": "You are FinPay AI, a helpful financial assistant."},
        {"role": "user", "content": "Hello, introduce yourself as the FinPay AI assistant."},
    ]

    print(f"\n📤 Sending test message to Ollama...")
    start = time.time()

    try:
        response = client.chat_completion(messages=messages)
        elapsed = time.time() - start
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n❌ Connection failed after {elapsed:.1f}s: {e}")
        sys.exit(1)

    # ── 3. Validate response format ──────────────────────
    print(f"\n⏱️  Response received in {elapsed:.1f}s")

    # Check top-level keys
    expected_keys = {"model", "message", "done"}
    actual_keys = set(response.keys())
    missing = expected_keys - actual_keys
    if missing:
        print(f"\n⚠️  Missing expected keys: {missing}")
        print(f"   Actual keys: {list(response.keys())}")
    else:
        print(f"✅ Response has expected keys: model, message, done")

    # Check message structure
    msg = response.get("message", {})
    role = msg.get("role", "")
    content = msg.get("content", "")

    print(f"✅ message.role    = '{role}'")
    print(f"✅ message.content = {len(content)} chars")
    print(f"✅ done            = {response.get('done')}")

    if response.get("total_duration"):
        duration_ms = response["total_duration"] / 1_000_000
        print(f"✅ total_duration  = {duration_ms:.0f}ms")

    # ── 4. Print the actual response ─────────────────────
    print(f"\n{'─' * 55}")
    print(f"💬 Qwen Response:\n")
    print(content.strip() if content else "(empty response)")
    print(f"\n{'─' * 55}")

    # ── 5. Summary ───────────────────────────────────────
    if content.strip():
        print(f"\n✅ TEST PASSED — Ollama Qwen integration is working.")
    else:
        print(f"\n⚠️  TEST WARNING — Response was empty.")


if __name__ == "__main__":
    main()
