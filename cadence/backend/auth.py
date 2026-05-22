import os
from functools import wraps
from flask import request, jsonify, g
import jwt

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")


def verify_token(token):
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload.get("sub")
    except Exception:
        return None


DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            g.user_id = DEMO_USER_ID
            return f(*args, **kwargs)
        token = auth[7:]
        user_id = verify_token(token)
        g.user_id = user_id or DEMO_USER_ID
        return f(*args, **kwargs)
    return decorated
