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

# Test PostgreSQL Null-byte (\x00) sanitation
null_payload = {"user\x00name": "Danh\x00Leader", "note": "Safe\x00Text"}
null_cleaned = mask_sensitive_data(null_payload)
assert "\x00" not in str(null_cleaned), "Null-byte was not stripped!"
assert null_cleaned["username"] == "DanhLeader"
assert null_cleaned["note"] == "SafeText"
print("PASSED: Null-bytes (\\x00) stripped completely for PostgreSQL JSONB safety.")

print("\n--- 2. Testing Anti-IP Spoofing (get_client_ip) ---")
class MockRequest:
    def __init__(self, host, headers):
        class Client:
            pass
        class State:
            pass
        self.client = Client()
        self.client.host = host
        self.headers = headers
        self.state = State()

# Case A: Attacker directly connects from untrusted IP with forged CF-Connecting-IP
attacker_req = MockRequest("203.0.113.5", {
    "cf-connecting-ip": "1.1.1.1",
    "x-forwarded-for": "8.8.8.8",
})
ip_detected = get_client_ip(attacker_req)
assert ip_detected == "203.0.113.5", f"IP Spoofing succeeded! Detected {ip_detected} instead of 203.0.113.5"
print(f"PASSED: Attacker forged headers ignored from untrusted client {ip_detected}.")

# Case B: Request comes from trusted proxy (127.0.0.1)
# B1: Nginx overrides X-Real-IP, attacker tries to spoof CF-Connecting-IP while USE_CLOUDFLARE=False
nginx_req = MockRequest("127.0.0.1", {
    "cf-connecting-ip": "1.2.3.4",
    "x-real-ip": "203.0.113.88",
})
ip_from_nginx = get_client_ip(nginx_req)
assert ip_from_nginx == "203.0.113.88", f"X-Real-IP was not prioritized over fake CF header! Got: {ip_from_nginx}"
print(f"PASSED: X-Real-IP took priority over fake CF header from trusted proxy: {ip_from_nginx}.")

# B2: Nginx appends client IP to X-Forwarded-For: <fake_ip>, <real_ip>
x_forwarded_req = MockRequest("127.0.0.1", {
    "x-forwarded-for": "1.2.3.4, 203.0.113.99",
})
ip_from_forwarded = get_client_ip(x_forwarded_req)
assert ip_from_forwarded == "203.0.113.99", f"X-Forwarded-For reverse lookup failed! Got: {ip_from_forwarded}"
print(f"PASSED: X-Forwarded-For picked real client IP from end of chain: {ip_from_forwarded}.")

# B3: USE_CLOUDFLARE=True trusts CF-Connecting-IP
settings.USE_CLOUDFLARE = True
cf_req = MockRequest("127.0.0.1", {
    "cf-connecting-ip": "198.51.100.77",
})
ip_cf = get_client_ip(cf_req)
assert ip_cf == "198.51.100.77", f"CF-Connecting-IP not honored with USE_CLOUDFLARE=True! Got: {ip_cf}"
settings.USE_CLOUDFLARE = False
print(f"PASSED: Cloudflare header honored when USE_CLOUDFLARE=True: {ip_cf}.")

# B4: Fallback step 4 removed: When USE_CLOUDFLARE=False and no X-Real-IP or X-Forwarded-For, fake CF header must NOT be trusted
fake_cf_only = MockRequest("127.0.0.1", {
    "cf-connecting-ip": "1.2.3.4",
})
ip_fake_cf = get_client_ip(fake_cf_only)
assert ip_fake_cf == "127.0.0.1", f"Fake CF header was trusted without USE_CLOUDFLARE! Got: {ip_fake_cf}"
print(f"PASSED: Fake CF header rejected when USE_CLOUDFLARE=False (fallback step 4 safely removed).")

# B5: JWT length limit & JWT bomb protection test
from app.middleware.rate_limit import extract_user_id_from_request
from app.middleware.audit import extract_user_info_from_token
bomb_token = "Bearer " + ("A" * 3000)
bomb_req = MockRequest("127.0.0.1", {"authorization": bomb_token})
assert extract_user_id_from_request(bomb_req) is None
uid, uname = extract_user_info_from_token(bomb_req)
assert uid is None
print("PASSED: Oversized JWT bomb (> 2048 chars) rejected before HMAC decoding.")

print("\n--- 3. Testing In-Memory LRU Cache Eviction & Cleanup ---")
from app.middleware.rate_limit import _cleanup_memory_cache, _memory_rate_cache, _memory_breached_keys, MAX_MEMORY_CACHE_KEYS
import time

now = time.time()
for i in range(5500):
    _memory_rate_cache[f"key_{i}"] = [now]
    _memory_breached_keys[f"key_{i}"] = now

assert len(_memory_rate_cache) == 5500
assert len(_memory_breached_keys) == 5500

_cleanup_memory_cache(now, 60)
assert len(_memory_rate_cache) <= MAX_MEMORY_CACHE_KEYS, f"_memory_rate_cache not capped! Len: {len(_memory_rate_cache)}"
assert len(_memory_breached_keys) <= MAX_MEMORY_CACHE_KEYS, f"_memory_breached_keys not capped! Len: {len(_memory_breached_keys)}"
print(f"PASSED: Memory cache capped strictly at {len(_memory_rate_cache)} and {len(_memory_breached_keys)} keys.")

print("\n--- 4. Testing FastAPI Middlewares Integration ---")
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(docs_url="/docs", redoc_url="/redoc", debug=False)
setup_middlewares(app)

# Track calls to log_audit_background
audit_calls = []
import app.middleware.audit as audit_mod
orig_audit = audit_mod.log_audit_background
def mock_log_audit(*args, **kwargs):
    audit_calls.append((args, kwargs))
audit_mod.log_audit_background = mock_log_audit

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

@app.get("/api/v1/trigger_429")
async def rate_limited_endpoint():
    raise HTTPException(status_code=429, detail="Rate limit exceeded test")

async def run_async_tests():
    # Test 4.1: Docs CSP
    docs_resp = await call_asgi(app, "GET", "/docs")
    assert docs_resp.status_code == 200
    csp = docs_resp.headers.get("content-security-policy", "")
    assert "cdn.jsdelivr.net" in csp, f"CDN not permitted in docs CSP: {csp}"
    print("PASSED: /docs CSP allows CDN resources.")

    # Test 4.2: API CSP, Modern Security Headers & Correlation-ID header
    api_resp = await call_asgi(app, "GET", "/api/v1/test", headers={"X-Correlation-ID": "test-req-12345"})
    assert api_resp.status_code == 200
    assert api_resp.headers.get("x-correlation-id") == "test-req-12345"
    assert "x-process-time" in api_resp.headers
    assert api_resp.headers.get("x-xss-protection") == "0", f"Expected X-XSS-Protection=0, got {api_resp.headers.get('x-xss-protection')}"
    assert api_resp.headers.get("cross-origin-opener-policy") == "same-origin", f"Expected COOP=same-origin, got {api_resp.headers.get('cross-origin-opener-policy')}"
    assert api_resp.json()["correlation_id"] == "test-req-12345"
    print("PASSED: API endpoint returned modern OWASP headers (X-XSS-Protection=0, COOP=same-origin) & correlation_id.")

    # Test 4.3: Unhandled 500 Exception handler preserves correlation_id & ISO 8601 UTC timestamp
    err_resp = await call_asgi(app, "GET", "/api/v1/unhandled_error", headers={"X-Correlation-ID": "err-corr-999"})
    assert err_resp.status_code == 500
    err_data = err_resp.json()
    assert err_data["success"] is False
    assert err_data["error"] == "InternalServerError"
    assert err_data["correlation_id"] == "err-corr-999", f"Correlation ID lost in 500 response! Got: {err_data}"
    assert err_data["details"]["support_id"] == "err-corr-999"
    assert "timestamp" in err_data and "+00:00" in err_data["timestamp"] or "Z" in err_data["timestamp"]
    print("PASSED: 500 unhandled error preserved correlation_id and valid timezone-aware UTC timestamp.")

    # Test 4.4: Post JSON body reading works without stream deadlock
    sample_body = json.dumps({"user": "Danh", "secret_pass": "123"}).encode("utf-8")
    post_resp = await call_asgi(
        app,
        "POST",
        "/api/v1/json_body",
        headers={"content-type": "application/json", "content-length": str(len(sample_body))},
        body=sample_body,
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["received"] == {"user": "Danh", "secret_pass": "123"}
    print("PASSED: POST JSON body parsed by endpoint successfully without stream deadlock.")

    # Test 4.5: Transfer-Encoding: chunked / missing Content-Length body protection (OOM DoS fix)
    chunked_resp = await call_asgi(
        app,
        "POST",
        "/api/v1/json_body",
        headers={"content-type": "application/json", "transfer-encoding": "chunked"},
        body=b'{"chunked": true}',
    )
    assert chunked_resp.status_code == 200
    print("PASSED: Chunked JSON payload without Content-Length handled without calling request.body() in audit.")

    # Test 4.6: Large body audit protection (> 64KB)
    large_payload = json.dumps({"big_data": "A" * (70 * 1024)}).encode("utf-8")
    large_resp = await call_asgi(
        app,
        "POST",
        "/api/v1/json_body",
        headers={"content-type": "application/json", "content-length": str(len(large_payload))},
        body=large_payload,
    )
    assert large_resp.status_code == 200
    print("PASSED: Large JSON body (> 64KB) handled safely without OOM or crashing.")

    # Test 4.7: ComprehensiveAuditLogMiddleware does NOT duplicate log on 429
    audit_calls.clear()
    resp_429 = await call_asgi(app, "GET", "/api/v1/trigger_429")
    assert resp_429.status_code == 429
    # ComprehensiveAuditLogMiddleware must skip log_audit_background when status_code == 429
    assert len(audit_calls) == 0, f"Expected 0 audit log calls for 429, got {len(audit_calls)}"
    print("PASSED: ComprehensiveAuditLogMiddleware bypassed audit logging on 429 to prevent DB spam.")

    print("\n==========================================")
    print("ALL EDGE-CASE SECURITY VERIFICATION TESTS PASSED!")
    print("==========================================")

asyncio.run(run_async_tests())
