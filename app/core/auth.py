from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader, APIKeyQuery

from app.core.firebase import verify_firebase_token
from app.core.config import get_settings

security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)
ALLOWED_ROLES = ("authenticated", "staff", "admin", "moderator")


def _is_request_from_localhost(request: Request) -> bool:
    """Helper function to safely check if a request is from localhost."""
    if request.client:
        # Docker containers see requests from host as different IPs
        # Common Docker bridge network IPs
        local_ips = (
            "127.0.0.1",
            "::1",
            "localhost",
            "172.17.0.1",
            "172.18.0.1",
            "192.168.0.1",
        )
        return request.client.host in local_ips or request.client.host.startswith(
            "172."
        )
    return False


def _is_debug_mode() -> bool:
    """Check if debug mode is enabled via environment variable."""
    settings = get_settings()
    return settings.debug_mode


def get_privileged_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """
    Returns the current user based on Firebase token.
    In debug mode, can bypass auth or use provided token.
    Only allows users with elevated roles (staff, admin, moderator).
    """

    user = get_current_user(request, credentials)
    role = user.get("role")
    if role not in ("staff", "admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: insufficient privileges"
        )
    return user


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """
    Returns the current user based on Firebase token.
    In debug mode, can bypass auth or use provided token.
    """

    is_local = _is_request_from_localhost(request)
    is_debug = _is_debug_mode()

    print(
        f"[DEBUG] Auth check: is_debug={is_debug}, is_local={is_local}, "
        f"has_credentials={credentials is not None}"
    )

    # Debug mode: flexible authentication
    if is_debug:
        if credentials and credentials.credentials:
            # Token provided - try to validate it for testing
            try:
                print("[DEBUG] Attempting to validate provided token...")
                user = verify_firebase_token(credentials)
                user["is_local"] = is_local
                user["is_debug"] = True
                print(f"[DEBUG] Auth token validated: {user.get('uid')}")
                return user
            except Exception as e:  # Catch any exception, not just HTTPException
                print(f"[DEBUG] Token validation failed: {str(e)}")
                # In debug mode, fall through to dummy user instead of raising
                print("[DEBUG] Falling back to dummy user due to auth failure")
        else:
            print("[DEBUG] No credentials provided in debug mode")

        # No token provided or auth failed in debug mode - return dummy user
        print(f"[DEBUG] Using dummy user (is_local: {is_local})")
        return {
            "uid": "debug-uid",
            "role": "authenticated",
            "is_local": is_local,
            "is_debug": True,
        }

    # Production mode: strict authentication required
    if not credentials:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")

    user = verify_firebase_token(credentials)
    role = user.get("role")
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied: invalid user role"
        )

    user["is_local"] = is_local
    user["is_debug"] = is_debug
    return user


async def validate_api_key(
    api_key_from_header: str | None = Security(api_key_header),
    api_key_from_query: str | None = Security(api_key_query)
) -> str:
    """
    Validates the API key from either X-API-KEY header or api_key query parameter.
    Header takes precedence if both are provided.

    Raises HTTPException if the key is missing or invalid.
    Returns the validated API key.
    """
    settings = get_settings()
    expected_api_key = settings.api_key

    api_key = api_key_from_header or api_key_from_query

    if not api_key or api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key. Provide a valid X-API-KEY header or api_key query parameter."
        )

    return api_key
