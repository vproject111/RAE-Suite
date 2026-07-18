# scripts/trigger_sonar_webhook.py
import requests
import json
import hmac
import hashlib

url = "http://localhost:8010/v2/quality/webhook/sonarqube"
secret = "sonarqube_webhook_secret_key".encode()

payload = {
    "serverUrl": "http://localhost:9000",
    "taskId": "AZ8zWgSnGSzwUfIeWChJ",
    "status": "SUCCESS",
    "analysedAt": "2026-07-05T17:35:34+0200",
    "revision": "5ef600d8e796ceff16c77746e3836c3f82f4d3d5",
    "project": {
        "key": "dreamsoft_factory",
        "name": "Dreamsoft Factory",
        "url": "http://localhost:9000/dashboard?id=dreamsoft_factory"
    },
    "properties": {},
    "qualityGate": {
        "name": "Sonar way",
        "status": "OK",
        "conditions": []
    }
}

body = json.dumps(payload).encode()
signature = hmac.new(secret, body, hashlib.sha256).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Sonar-Webhook-HMAC-Signature": signature
}

print("Sending webhook payload to RAE-Quality...")
response = requests.post(url, data=body, headers=headers)
print(f"Response Code: {response.status_code}")
print(f"Response Body: {response.text}")
