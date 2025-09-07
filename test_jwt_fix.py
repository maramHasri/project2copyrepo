#!/usr/bin/env python3
"""
Test script to verify JWT token expiration fix
"""

from security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from jwt_debug_tool import decode_and_analyze_jwt, print_analysis

def test_jwt_expiration():
    """Test that JWT tokens now have the correct expiration time."""
    
    print("🧪 Testing JWT Token Expiration Fix")
    print("=" * 50)
    
    # Test 1: Create token with explicit expires_delta
    print("\n1️⃣ Testing with explicit expires_delta:")
    token1 = create_access_token(
        data={"sub": "test@example.com", "role": "reader"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    analysis1 = decode_and_analyze_jwt(token1)
    if analysis1.get('success'):
        expected_hours = ACCESS_TOKEN_EXPIRE_MINUTES / 60
        actual_hours = analysis1['time_remaining_hours']
        print(f"   Expected: {expected_hours:.1f} hours")
        print(f"   Actual: {actual_hours:.1f} hours")
        
        if abs(actual_hours - expected_hours) < 0.1:  # Within 6 minutes
            print("   ✅ PASS: Token expiration matches expected time")
        else:
            print("   ❌ FAIL: Token expiration doesn't match expected time")
    
    # Test 2: Create token without expires_delta (should use fallback)
    print("\n2️⃣ Testing without expires_delta (fallback):")
    token2 = create_access_token(
        data={"sub": "test@example.com", "role": "reader"}
    )
    
    analysis2 = decode_and_analyze_jwt(token2)
    if analysis2.get('success'):
        expected_hours = ACCESS_TOKEN_EXPIRE_MINUTES / 60
        actual_hours = analysis2['time_remaining_hours']
        print(f"   Expected: {expected_hours:.1f} hours")
        print(f"   Actual: {actual_hours:.1f} hours")
        
        if abs(actual_hours - expected_hours) < 0.1:  # Within 6 minutes
            print("   ✅ PASS: Fallback expiration matches expected time")
        else:
            print("   ❌ FAIL: Fallback expiration doesn't match expected time")
    
    # Test 3: Verify both tokens are different (not cached)
    print("\n3️⃣ Testing token uniqueness:")
    if token1 != token2:
        print("   ✅ PASS: Tokens are unique (no caching issue)")
    else:
        print("   ❌ FAIL: Tokens are identical (possible caching issue)")
    
    # Test 4: Show detailed analysis of first token
    print("\n4️⃣ Detailed analysis of first token:")
    print_analysis(analysis1)
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    print(f"   ACCESS_TOKEN_EXPIRE_MINUTES = {ACCESS_TOKEN_EXPIRE_MINUTES}")
    print(f"   That's {ACCESS_TOKEN_EXPIRE_MINUTES / 60:.1f} hours")
    print(f"   That's {ACCESS_TOKEN_EXPIRE_MINUTES / 60 / 24:.1f} days")
    print("=" * 50)

if __name__ == "__main__":
    test_jwt_expiration()
