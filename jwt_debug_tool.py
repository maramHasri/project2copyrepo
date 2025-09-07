#!/usr/bin/env python3
"""
JWT Token Debugging Tool
========================

This script helps debug JWT token expiration issues by:
1. Decoding any JWT token
2. Showing expiration time in human-readable format
3. Comparing with current UTC time
4. Identifying potential issues

Usage:
    python jwt_debug_tool.py <your_jwt_token>
    
Or import and use the functions in your code.
"""

import sys
from datetime import datetime, timedelta
from jose import JWTError, jwt
import json

# Your security configuration (copy from security.py)
SECRET_KEY = "N93qNdu1uEX7oKM3ZQnHdV02TIuRt4umLG07eV4JhzI"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 7200  # This should be 7200 minutes (5 days)

def decode_and_analyze_jwt(token: str) -> dict:
    """
    Decode JWT token and analyze its expiration.
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Analysis results
    """
    try:
        # Decode without verification first to see the payload
        unverified_payload = jwt.get_unverified_claims(token)
        
        # Now decode with verification
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Get expiration time
        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return {
                'error': 'No expiration time found in token',
                'payload': payload
            }
        
        # Convert to datetime
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        current_utc = datetime.utcnow()
        
        # Calculate time remaining
        time_remaining = exp_datetime - current_utc
        is_expired = current_utc >= exp_datetime
        
        # Calculate when token was issued (if iat exists)
        iat_timestamp = payload.get('iat')
        issued_at = None
        if iat_timestamp:
            issued_at = datetime.fromtimestamp(iat_timestamp)
        
        return {
            'success': True,
            'payload': payload,
            'exp_timestamp': exp_timestamp,
            'exp_datetime': exp_datetime,
            'exp_datetime_readable': exp_datetime.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'current_utc': current_utc,
            'current_utc_readable': current_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'time_remaining': time_remaining,
            'time_remaining_hours': time_remaining.total_seconds() / 3600,
            'is_expired': is_expired,
            'issued_at': issued_at,
            'issued_at_readable': issued_at.strftime('%Y-%m-%d %H:%M:%S UTC') if issued_at else None,
            'token_age': (current_utc - issued_at) if issued_at else None,
            'token_age_hours': ((current_utc - issued_at).total_seconds() / 3600) if issued_at else None
        }
        
    except JWTError as e:
        return {
            'error': f'JWT decode error: {str(e)}',
            'token_preview': token[:50] + '...' if len(token) > 50 else token
        }
    except Exception as e:
        return {
            'error': f'Unexpected error: {str(e)}',
            'token_preview': token[:50] + '...' if len(token) > 50 else token
        }

def print_analysis(analysis: dict):
    """Print the analysis results in a readable format."""
    print("=" * 60)
    print("JWT TOKEN ANALYSIS")
    print("=" * 60)
    
    if 'error' in analysis:
        print(f"❌ ERROR: {analysis['error']}")
        if 'token_preview' in analysis:
            print(f"Token preview: {analysis['token_preview']}")
        return
    
    if not analysis.get('success'):
        print("❌ Analysis failed")
        return
    
    print("✅ Token decoded successfully!")
    print()
    
    # Basic info
    print("📋 TOKEN INFORMATION:")
    print(f"   Subject (sub): {analysis['payload'].get('sub', 'N/A')}")
    print(f"   Entity Type: {analysis['payload'].get('entity_type', 'N/A')}")
    print(f"   Role: {analysis['payload'].get('role', 'N/A')}")
    print()
    
    # Time information
    print("⏰ TIME INFORMATION:")
    print(f"   Current UTC Time: {analysis['current_utc_readable']}")
    print(f"   Token Expires At: {analysis['exp_datetime_readable']}")
    
    if analysis['issued_at_readable']:
        print(f"   Token Issued At: {analysis['issued_at_readable']}")
        print(f"   Token Age: {analysis['token_age_hours']:.2f} hours")
    
    print()
    
    # Expiration analysis
    print("⏳ EXPIRATION ANALYSIS:")
    if analysis['is_expired']:
        print("   ❌ TOKEN IS EXPIRED!")
        print(f"   Expired {abs(analysis['time_remaining_hours']):.2f} hours ago")
    else:
        print("   ✅ Token is still valid")
        print(f"   Time remaining: {analysis['time_remaining_hours']:.2f} hours")
        print(f"   Time remaining: {analysis['time_remaining']}")
    
    print()
    
    # Expected vs actual analysis
    print("🔍 EXPECTED vs ACTUAL ANALYSIS:")
    expected_hours = ACCESS_TOKEN_EXPIRE_MINUTES / 60
    print(f"   Expected expiration: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes ({expected_hours:.1f} hours)")
    
    if analysis['issued_at']:
        actual_hours = analysis['token_age_hours']
        print(f"   Actual token age: {actual_hours:.2f} hours")
        
        if abs(actual_hours - expected_hours) > 1:  # More than 1 hour difference
            print("   ⚠️  WARNING: Token age doesn't match expected expiration time!")
            print(f"   Difference: {abs(actual_hours - expected_hours):.2f} hours")
        else:
            print("   ✅ Token age matches expected expiration time")
    
    print()
    
    # Full payload (for debugging)
    print("📄 FULL TOKEN PAYLOAD:")
    print(json.dumps(analysis['payload'], indent=2, default=str))

def create_test_token(expires_minutes: int = None) -> str:
    """
    Create a test token for debugging purposes.
    
    Args:
        expires_minutes: Override expiration time in minutes
        
    Returns:
        str: JWT token
    """
    from datetime import datetime, timedelta
    
    data = {
        "sub": "test@example.com",
        "entity_type": "user",
        "role": "reader",
        "iat": datetime.utcnow()
    }
    
    if expires_minutes:
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def main():
    """Main function for command-line usage."""
    if len(sys.argv) != 2:
        print("Usage: python jwt_debug_tool.py <jwt_token>")
        print("\nExample:")
        print("python jwt_debug_tool.py eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...")
        print("\nOr create a test token:")
        test_token = create_test_token()
        print(f"Test token: {test_token}")
        print("\nAnalyzing test token:")
        analysis = decode_and_analyze_jwt(test_token)
        print_analysis(analysis)
        return
    
    token = sys.argv[1]
    analysis = decode_and_analyze_jwt(token)
    print_analysis(analysis)

if __name__ == "__main__":
    main()
