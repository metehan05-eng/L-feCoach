#!/usr/bin/env python3
"""
Simple automated register+chat test for local backend.
Run this while the FastAPI server is running (http://127.0.0.1:8001 by default).
"""
import time
import os
import sys

import httpx

BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8001')


def register(email, password):
    try:
        r = httpx.post(f"{BACKEND_URL}/auth/register", json={"email": email, "password": password}, timeout=15.0)
        print('REGISTER', r.status_code)
        print(r.text)
        return r
    except Exception as e:
        print('REGISTER error:', e)
        raise


def chat(token, message):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = httpx.post(f"{BACKEND_URL}/chat", json={"message": message, "feature": "chat"}, headers=headers, timeout=20.0)
        print('CHAT', r.status_code)
        print(r.text)
        return r
    except Exception as e:
        print('CHAT error:', e)
        raise


def main():
    timestamp = int(time.time())
    email = f"test+{timestamp}@example.com"
    password = "TestPass123!"
    print('Using backend:', BACKEND_URL)

    r = register(email, password)
    if r.status_code != 200:
        print('Register failed; exiting.')
        sys.exit(1)
    data = r.json()
    token = data.get('access_token')
    if not token:
        print('No token returned; exiting.')
        sys.exit(1)

    # Try chat
    r2 = chat(token, 'Merhaba, otomatik test mesajı.')
    if r2.status_code != 200:
        print('Chat failed; exiting.')
        sys.exit(1)

    resp = r2.json()
    print('Chat response:', resp)
    print('Test succeeded.')
    sys.exit(0)


if __name__ == '__main__':
    main()
