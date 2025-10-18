from firebase_admin import auth, initialize_app as init_firebase, get_app as get_firebase_app
from firebase_admin.auth import ExpiredIdTokenError
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.services.logger import get_logger

logger = get_logger(__name__)


def initialize_firebase():
    """
    Initialize the Firebase Admin SDK if it hasn't been initialized already.
    """
    try:
        get_firebase_app()
        logger.warning("Firebase Admin SDK already initialized, skipping..")
    except ValueError:
        init_firebase()

    if get_firebase_app().project_id:
        return

    raise RuntimeError("Firebase Admin SDK initialization failed: No project ID found. You must activate the firebase project in your environment. See README.md for details.")


def verify_firebase_token(credentials: HTTPAuthorizationCredentials):
    """Verify Firebase ID token and return user info."""
    try:
        decoded_token = auth.verify_id_token(credentials.credentials)
        return {
            "uid": decoded_token["uid"],
            "email": decoded_token.get("email"),
            "role": decoded_token.get("role", "authenticated"),
        }
    except ExpiredIdTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth token has expired")
    except Exception as e:
        logger.error("Error encountered during JWT token verification: %s", e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
