import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Lightweight ASGI test runner without httpx dependency
import json

async def call_asgi(app, method: str, path: str, headers: dict = None, body: bytes = b""):
    headers = headers or {}
    raw_headers = [
        (k.lower().encode("latin1"), v.encode("latin1")) for k, v in headers.items()
    ]
    if body and "content-length" not in [k.lower() for k in headers]:
        raw_headers.append((b"content-length", str(len(body)).encode("latin1")))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("latin1"),
        "query_string": b"" if "?" not in path else path.split("?")[1].encode("latin1"),
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    if "?" in path:
        scope["path"] = path.split("?")[0]
        scope["raw_path"] = scope["path"].encode("latin1")

    sent_events = []
    response_body = []
    status_code = [None]
    response_headers = [{}]

    body_chunks = [body] if body else []
    
    async def receive():
        if body_chunks:
            return {"type": "http.request", "body": body_chunks.pop(0), "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(event):
        sent_events.append(event)
        if event["type"] == "http.response.start":
            status_code[0] = event["status"]
            response_headers[0] = {
                k.decode("latin1").lower(): v.decode("latin1")
                for k, v in event.get("headers", [])
            }
        elif event["type"] == "http.response.body":
            response_body.append(event.get("body", b""))

    try:
        await app(scope, receive, send)
    except Exception:
        pass

    class SimpleResponse:
        def __init__(self, status, headers, body_bytes):
            self.status_code = status
            self.headers = headers
            self.body = body_bytes
            self.text = body_bytes.decode("utf-8", errors="replace")

        def json(self):
            return json.loads(self.text)

    return SimpleResponse(status_code[0], response_headers[0], b"".join(response_body))

from app.core.config import settings
from app.middleware import setup_middlewares, get_correlation_id
from app.middleware.audit import mask_sensitive_data, is_sensitive_key
from app.middleware.rate_limit import get_client_ip, is_trusted_proxy

print("--- 1. Testing mask_sensitive_data & is_sensitive_key ---")
test_payload = {
    "username": "danh_leader",
    "password": "SuperSecretPassword123!",
    "new_password": "NewSecretPassword456!",
    "nested": {
        "auth_token": "jwt_secret_token_abc",
        "pin_code": "1234",
        "credit_cvv": "999",
        "general_text": "safe_value",
        "keyboard": "mechanical",  # should NOT be masked
        "monkey": "banana",        # should NOT be masked
    },
    "items": [
        {"sms_otp": "654321"},
        {"note": "Regular text"}
    ]
}

masked = mask_sensitive_data(test_payload)
assert masked["password"] == "***REDACTED***", "Password not masked!"
assert masked["new_password"] == "***REDACTED***", "New password not masked!"
assert masked["nested"]["auth_token"] == "***REDACTED***", "Auth token not masked!"
assert masked["nested"]["pin_code"] == "***REDACTED***", "Pin code not masked!"
assert masked["nested"]["credit_cvv"] == "***REDACTED***", "CVV not masked!"
assert masked["nested"]["general_text"] == "safe_value", "general_text wrongly masked!"
assert masked["nested"]["keyboard"] == "mechanical", "keyboard wrongly masked!"
assert masked["nested"]["monkey"] == "banana", "monkey wrongly masked!"
assert masked["items"][0]["sms_otp"] == "***REDACTED***", "OTP in list not masked!"
assert masked["items"][1]["note"] == "Regular text", "Regular note wrongly masked!"
print("PASSED: mask_sensitive_data properly masked sensitive fields and avoided false positives.")

# Test recursion depth limit
deep_dict = {}
cur = deep_dict
for i in range(15):
    cur["next"] = {}
    cur = cur["next"]
deep_masked = mask_sensitive_data(deep_dict, max_depth=5)
# Check that max depth exceeded was hit
found_exceeded = False
cur = deep_masked
while isinstance(cur, dict) and "next" in cur:
    if cur["next"] == "***MAX_DEPTH_EXCEEDED***":
        found_exceeded = True
        break
    cur = cur["next"]
assert found_exceeded, "Deep recursion limit failed!"
print("PASSED: mask_sensitive_data max recursion depth limit protected against Stack Overflow DoS.")

print("\n--- 2. Testing Anti-IP Spoofing (get_client_ip) ---")
class MockRequest:
    def __init__(self, host, headers):
        class Client:
            pass
        self.client = Client()
        self.client.host = host
        self.headers = headers

# Case A: Attacker directly connects from untrusted IP with forged CF-Connecting-IP
attacker_req = MockRequest("203.0.113.5", {
    "cf-connecting-ip": "1.1.1.1",
    "x-forwarded-for": "8.8.8.8",
})
ip_detected = get_client_ip(attacker_req)
assert ip_detected == "203.0.113.5", f"IP Spoofing succeeded! Detected {ip_detected} instead of 203.0.113.5"
print(f"PASSED: Attacker forged headers ignored from untrusted client {ip_detected}.")

# Case B: Request comes from trusted proxy (127.0.0.1)
proxy_req = MockRequest("127.0.0.1", {
    "cf-connecting-ip": "203.0.113.99",
})
ip_from_proxy = get_client_ip(proxy_req)
assert ip_from_proxy == "203.0.113.99", f"Proxy IP extraction failed! Detected {ip_from_proxy}"
print(f"PASSED: Trusted proxy client IP properly extracted: {ip_from_proxy}.")

print("\n--- 3. Testing FastAPI Middlewares Integration ---")
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(docs_url="/docs", redoc_url="/redoc", debug=False)
setup_middlewares(app)

@app.get("/api/v1/test")
async def test_endpoint(request: Request):
    return {"message": "success", "correlation_id": get_correlation_id(request)}

@app.get("/api/v1/unhandled_error")
async def error_endpoint(request: Request):
    raise RuntimeError("Simulated internal database crash!")

@app.post("/api/v1/json_body")
async def body_endpoint(request: Request):
    body = await request.json()
    return {"received": body}

async def run_async_tests():
    # Test 3.1: Docs CSP
    docs_resp = await call_asgi(app, "GET", "/docs")
    assert docs_resp.status_code == 200
    csp = docs_resp.headers.get("content-security-policy", "")
    assert "cdn.jsdelivr.net" in csp, f"CDN not permitted in docs CSP: {csp}"
    print("PASSED: /docs CSP allows CDN resources.")

    # Test 3.2: API CSP & Correlation-ID header
    api_resp = await call_asgi(app, "GET", "/api/v1/test", headers={"X-Correlation-ID": "test-req-12345"})
    assert api_resp.status_code == 200
    assert api_resp.headers.get("x-correlation-id") == "test-req-12345"
    assert "x-process-time" in api_resp.headers
    assert api_resp.json()["correlation_id"] == "test-req-12345"
    print("PASSED: API endpoint returned correlation_id and process time.")

    # Test 3.3: Unhandled 500 Exception handler preserves correlation_id
    err_resp = await call_asgi(app, "GET", "/api/v1/unhandled_error", headers={"X-Correlation-ID": "err-corr-999"})
    assert err_resp.status_code == 500
    err_data = err_resp.json()
    assert err_data["success"] is False
    assert err_data["error"] == "InternalServerError"
    assert err_data["correlation_id"] == "err-corr-999", f"Correlation ID lost in 500 response! Got: {err_data}"
    assert err_data["details"]["support_id"] == "err-corr-999"
    print("PASSED: 500 unhandled error preserved correlation_id in response without leaking stack trace.")

    # Test 3.4: Post JSON body reading works without stream deadlock
    sample_body = json.dumps({"user": "Danh", "secret_pass": "123"}).encode("utf-8")
    post_resp = await call_asgi(
        app,
        "POST",
        "/api/v1/json_body",
        headers={"content-type": "application/json"},
        body=sample_body,
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["received"] == {"user": "Danh", "secret_pass": "123"}
    print("PASSED: POST JSON body parsed by endpoint successfully without stream deadlock.")

    # Test 3.5: Large body audit protection (> 64KB)
    large_payload = json.dumps({"big_data": "A" * (70 * 1024)}).encode("utf-8")
    large_resp = await call_asgi(
        app,
        "POST",
        "/api/v1/json_body",
        headers={"content-type": "application/json"},
        body=large_payload,
    )
    assert large_resp.status_code == 200
    print("PASSED: Large JSON body (> 64KB) handled safely without OOM or crashing.")

    print("\n==========================================")
    print("ALL SECURITY & PENTEST VERIFICATION TESTS PASSED!")
    print("==========================================")

asyncio.run(run_async_tests())
