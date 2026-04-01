import sys
import os

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from app.main import app
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    from slowapi.middleware import SlowAPIMiddleware
    from app.api.auth import router as auth_router
    
    https = [m for m in app.user_middleware if m.cls == HTTPSRedirectMiddleware]
    slow = [m for m in app.user_middleware if m.cls == SlowAPIMiddleware]
    reg = next((r for r in auth_router.routes if r.path == "/register"), None)
    
    print(f"HTTPS Middleware: {'✅' if https else '❌'}")
    print(f"SlowAPI Middleware: {'✅' if slow else '❌'}")
    
    if reg:
        # Check for limiter attributes
        if hasattr(reg.endpoint, "_rate_limit_checker"):
             print("Register Rate Limit: ✅")
        else:
             print("Register Rate Limit: ⚠️ (Could not verify decorator via attribute, but route exists)")
    else:
        print("Register Route: ❌")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
