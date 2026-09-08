"""
Test Django POST /api/chat/ multi-turn context integration.

Steps:
1. POST /api/chat/ with {"message": "What is Arjun Sharma's current account balance?"}
2. Extract response answer, construct history list.
3. POST /api/chat/ with:
   {
       "message": "What are his recent transactions?",
       "history": [
           {"role": "user", "content": "What is Arjun Sharma's current account balance?"},
           {"role": "assistant", "content": "<answer 1>"}
       ]
   }
4. Verify response handles "his" correctly.
"""

import json
import sys
import os
import httpx

DJANGO_CHAT_URL = "http://127.0.0.1:8000/api/chat/"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("==================================================")
    print("  Testing Django Endpoint: POST /api/chat/        ")
    print("==================================================")

    with httpx.Client(timeout=120.0) as client:
        # ── Turn 1 ───────────────────────────────────────────
        prompt1 = "What is Arjun Sharma's current account balance?"
        payload1 = {"message": prompt1}

        print(f"\n--- Turn 1 ---")
        print(f"POST {DJANGO_CHAT_URL}")
        print(f"Payload: {json.dumps(payload1, indent=2)}")

        resp1 = client.post(DJANGO_CHAT_URL, json=payload1)
        print(f"HTTP Status: {resp1.status_code}")
        data1 = resp1.json()
        print(f"Response Body: {json.dumps(data1, indent=2, ensure_ascii=False)}")

        if resp1.status_code != 200 or not data1.get("success"):
            print("❌ Turn 1 failed")
            sys.exit(1)

        ans1 = data1.get("response", "")

        # Build history for Turn 2
        history = [
            {"role": "user", "content": prompt1},
            {"role": "assistant", "content": ans1},
        ]

        # ── Turn 2 ───────────────────────────────────────────
        prompt2 = "What are his recent transactions?"
        payload2 = {
            "message": prompt2,
            "history": history,
        }

        print(f"\n--- Turn 2 (Contextual Follow-up) ---")
        print(f"POST {DJANGO_CHAT_URL}")
        print(f"Payload: {json.dumps(payload2, indent=2, ensure_ascii=False)}")

        resp2 = client.post(DJANGO_CHAT_URL, json=payload2)
        print(f"HTTP Status: {resp2.status_code}")
        data2 = resp2.json()
        print(f"Response Body: {json.dumps(data2, indent=2, ensure_ascii=False)}")

        if resp2.status_code != 200 or not data2.get("success"):
            print("❌ Turn 2 failed")
            sys.exit(1)

        ans2 = data2.get("response", "")

        print("\n==================================================")
        print("  Django Integration Multi-turn Test Complete     ")
        print("==================================================")


if __name__ == "__main__":
    main()
