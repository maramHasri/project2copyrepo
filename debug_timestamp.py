#!/usr/bin/env python3
"""
Debug timestamp issues
"""

from datetime import datetime, timedelta
import time
from security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from jose import jwt

def debug_timestamps():
    print("🕐 TIMESTAMP DEBUG")
    print("=" * 40)
    
    # Current time methods
    now_utc = datetime.utcnow()
    now_timestamp = time.time()
    now_datetime_timestamp = now_utc.timestamp()
    
    print(f"datetime.utcnow(): {now_utc}")
    print(f"time.time(): {now_timestamp}")
    print(f"datetime.utcnow().timestamp(): {now_datetime_timestamp}")
    print(f"Current year: {now_utc.year}")
    print()
    
    # Test token creation
    print("🔑 TOKEN CREATION DEBUG")
    print("=" * 40)
    
    # Create token with explicit expiration
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_time = now_utc + expires_delta
    
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
    print(f"Expires delta: {expires_delta}")
    print(f"Expire time: {expire_time}")
    print(f"Expire timestamp: {expire_time.timestamp()}")
    print()
    
    # Create token
    token = create_access_token(
        data={"sub": "test@example.com"},
        expires_delta=expires_delta
    )
    
    # Decode token
    payload = jwt.get_unverified_claims(token)
    exp_timestamp = payload.get('exp')
    iat_timestamp = payload.get('iat')
    
    print("📄 TOKEN PAYLOAD:")
    print(f"exp (expiration): {exp_timestamp}")
    print(f"iat (issued at): {iat_timestamp}")
    print()
    
    # Convert back to datetime
    if exp_timestamp:
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        print(f"Expiration datetime: {exp_datetime}")
        print(f"Expiration year: {exp_datetime.year}")
    
    if iat_timestamp:
        iat_datetime = datetime.fromtimestamp(iat_timestamp)
        print(f"Issued at datetime: {iat_datetime}")
        print(f"Issued at year: {iat_datetime.year}")
    
    print()
    
    # Calculate difference
    if exp_timestamp and iat_timestamp:
        diff_seconds = exp_timestamp - iat_timestamp
        diff_minutes = diff_seconds / 60
        diff_hours = diff_minutes / 60
        
        print("⏱️ TIME DIFFERENCE:")
        print(f"Difference in seconds: {diff_seconds}")
        print(f"Difference in minutes: {diff_minutes}")
        print(f"Difference in hours: {diff_hours}")
        print(f"Expected minutes: {ACCESS_TOKEN_EXPIRE_MINUTES}")
        print(f"Expected hours: {ACCESS_TOKEN_EXPIRE_MINUTES / 60}")
        
        if abs(diff_minutes - ACCESS_TOKEN_EXPIRE_MINUTES) < 1:
            print("✅ PASS: Token expiration matches expected time")
        else:
            print("❌ FAIL: Token expiration doesn't match expected time")
            print(f"Difference: {abs(diff_minutes - ACCESS_TOKEN_EXPIRE_MINUTES)} minutes")

if __name__ == "__main__":
    debug_timestamps()
