# JWT Token Expiration Debugging Guide

## 🚨 CRITICAL BUGS FOUND AND FIXED

### 1. **FIXED**: Incorrect Comment in security.py
- **Before**: `ACCESS_TOKEN_EXPIRE_MINUTES = 7200  # 100 hours (1440 minutes)`
- **After**: `ACCESS_TOKEN_EXPIRE_MINUTES = 7200  # 7200 minutes = 120 hours = 5 days`
- **Issue**: Comment was misleading (1440 minutes = 24 hours, not 100 hours)

### 2. **FIXED**: Hardcoded Fallback in create_access_token()
- **Before**: `expire = datetime.utcnow() + timedelta(minutes=1440)  # 24 hours fallback`
- **After**: `expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)`
- **Issue**: When no expires_delta was provided, it used 24 hours instead of your configured 7200 minutes

## 🔍 Debugging Steps

### Step 1: Use the JWT Debug Tool

```bash
# Install required package if not already installed
pip install python-jose[cryptography]

# Run the debug tool with your token
python jwt_debug_tool.py "your_jwt_token_here"

# Or create a test token
python jwt_debug_tool.py
```

### Step 2: Check Your Token Creation

Verify that your login endpoints are using the correct expiration:

```python
# In routers/auth.py, routers/admin_auth.py, routers/publisher_auth.py
# This should now work correctly:
access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
access_token = create_access_token(
    data={"sub": user.email}, 
    expires_delta=access_token_expires
)
```

### Step 3: Frontend Debugging

Add this JavaScript code to your frontend to debug token expiration:

```javascript
function debugJWT(token) {
    try {
        // Decode JWT payload (without verification for debugging)
        const payload = JSON.parse(atob(token.split('.')[1]));
        
        const exp = payload.exp;
        const iat = payload.iat;
        const now = Math.floor(Date.now() / 1000);
        
        console.log('=== JWT DEBUG INFO ===');
        console.log('Token payload:', payload);
        console.log('Issued at (iat):', new Date(iat * 1000).toISOString());
        console.log('Expires at (exp):', new Date(exp * 1000).toISOString());
        console.log('Current time:', new Date(now * 1000).toISOString());
        console.log('Time remaining (seconds):', exp - now);
        console.log('Time remaining (hours):', (exp - now) / 3600);
        console.log('Is expired:', now >= exp);
        
        return {
            payload,
            expiresAt: new Date(exp * 1000),
            timeRemaining: exp - now,
            isExpired: now >= exp
        };
    } catch (error) {
        console.error('Error decoding JWT:', error);
        return null;
    }
}

// Usage:
// debugJWT('your_jwt_token_here');
```

## 🧪 Testing Your Fix

### Test 1: Create a New Token
```python
# Test in Python console
from security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

# Create a test token
token = create_access_token(
    data={"sub": "test@example.com"},
    expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
)

print(f"Token: {token}")
print(f"Expected expiration: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
```

### Test 2: Decode and Verify
```python
# Use the debug tool
from jwt_debug_tool import decode_and_analyze_jwt, print_analysis

analysis = decode_and_analyze_jwt(token)
print_analysis(analysis)
```

## 🔧 Additional Debugging

### Check if Frontend is Caching Old Tokens

1. **Clear browser storage**:
   ```javascript
   localStorage.clear();
   sessionStorage.clear();
   ```

2. **Check if frontend is reusing tokens**:
   ```javascript
   // Add this to your login response handler
   console.log('New token received:', response.data.access_token);
   console.log('Token length:', response.data.access_token.length);
   ```

### Check Server Time vs Client Time

```python
# Add this endpoint to your FastAPI app for debugging
@app.get("/debug/time")
async def debug_time():
    from datetime import datetime
    return {
        "server_utc": datetime.utcnow().isoformat(),
        "server_timestamp": datetime.utcnow().timestamp(),
        "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES
    }
```

### Verify Token Generation in Each Router

Check these files to ensure they're using the correct expiration:

1. **routers/auth.py** (line ~104-105)
2. **routers/admin_auth.py** (line ~124-125)  
3. **routers/publisher_auth.py** (line ~165-166)

All should look like:
```python
access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
access_token = create_access_token(
    data={"sub": user.email}, 
    expires_delta=access_token_expires
)
```

## 🚀 Quick Fix Summary

The main issues were:

1. ✅ **Fixed**: Hardcoded 24-hour fallback in `create_access_token()`
2. ✅ **Fixed**: Misleading comment about expiration time
3. ✅ **Verified**: Using `datetime.utcnow()` correctly
4. ✅ **Verified**: `ACCESS_TOKEN_EXPIRE_MINUTES` is being used in token creation

After these fixes, your tokens should now properly expire after 7200 minutes (5 days) instead of 24 hours.

## 🔄 Next Steps

1. **Restart your FastAPI server** to apply the security.py changes
2. **Test with a fresh login** to get a new token
3. **Use the debug tool** to verify the new token has the correct expiration
4. **Clear frontend storage** to ensure no old tokens are cached
5. **Test the frontend** to confirm the issue is resolved

If the issue persists after these fixes, the problem is likely in the frontend token handling or caching mechanism.
