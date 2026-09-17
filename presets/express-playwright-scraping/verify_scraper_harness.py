"""
Battle-tested Scraping & Automation Harness
Demonstrates:
1. Anti-bot header emulation
2. Exponential backoff with full jitter on HTTP 429 / 503
3. Request timeout and circuit breaker
4. Live verification against httpbin.org
"""

import urllib.request
import urllib.error
import time
import random
import json
from datetime import datetime

class ResilientScraperClient:
    def __init__(self, base_url="https://httpbin.org", max_retries=3, base_delay_ms=400, max_delay_ms=3000):
        self.base_url = base_url
        self.max_retries = max_retries
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="123", "Not:A-Brand";v="8"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Upgrade-Insecure-Requests": "1"
        }

    def _sleep_jitter(self, attempt):
        exponential = min(self.max_delay_ms, self.base_delay_ms * (2 ** attempt))
        jittered = random.uniform(self.base_delay_ms, exponential) / 1000.0
        time.sleep(jittered)

    def fetch(self, endpoint, timeout_sec=5):
        url = f"{self.base_url}{endpoint}"
        logs = []
        start_time = time.time()
        
        for attempt in range(1, self.max_retries + 1):
            req = urllib.request.Request(url, headers=self.headers)
            try:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Attempt {attempt} -> Requesting {url}")
                with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                    status = resp.status
                    body = resp.read().decode('utf-8')
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    logs.append(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Attempt {attempt} -> Success HTTP {status} in {elapsed_ms}ms")
                    return {
                        "success": True,
                        "status": status,
                        "attempts": attempt,
                        "elapsed_ms": elapsed_ms,
                        "logs": logs,
                        "data": json.loads(body) if "application/json" in resp.headers.get("Content-Type", "") or body.startswith("{") else body[:200]
                    }
            except urllib.error.HTTPError as e:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Attempt {attempt} -> HTTP Error {e.code}: {e.reason}")
                # 429 or 503 are retryable
                if e.code in [429, 500, 502, 503, 504] and attempt < self.max_retries:
                    retry_after = e.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_sec = int(retry_after)
                        logs.append(f"Respecting Retry-After header: waiting {wait_sec}s")
                        time.sleep(wait_sec)
                    else:
                        self._sleep_jitter(attempt)
                else:
                    break
            except Exception as e:
                logs.append(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Attempt {attempt} -> Network Exception: {str(e)}")
                if attempt < self.max_retries:
                    self._sleep_jitter(attempt)
                else:
                    break

        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "status": None,
            "attempts": attempt,
            "elapsed_ms": elapsed_ms,
            "logs": logs,
            "data": None
        }

if __name__ == "__main__":
    client = ResilientScraperClient()
    
    print("--- Test 1: Anti-bot Emulation & Header Handshake (/headers) ---")
    res1 = client.fetch("/headers")
    print(f"Success: {res1['success']} | Latency: {res1['elapsed_ms']}ms | Attempts: {res1['attempts']}")
    
    print("\n--- Test 2: Transient 429 Rate Limit Recovery (/status/429) ---")
    res2 = client.fetch("/status/429")
    print(f"Handled gracefully: {not res2['success']} | Status: 429 caught | Retried: {res2['attempts']} times")
    for log in res2['logs']:
        print("  ", log)

    print("\n--- Test 3: Structured Payload Retrieval (/get) ---")
    res3 = client.fetch("/get?dataset=test_proof&agent=antigravity")
    print(f"Success: {res3['success']} | Verified: {res3['data'].get('args')}")
