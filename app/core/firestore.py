from firebase_admin import firestore, get_app as get_firebase_app
from app.services.logger import get_logger

logger = get_logger(__name__)

# Initialize Firestore client lazily to avoid import-time initialization
_firestore_client = None

def get_firestore_client():
    """Get the Firestore client, initializing it if needed."""
    global _firestore_client
    if _firestore_client is None:
        # Ensure Firebase app is initialized
        try:
            app = get_firebase_app()
            if not app.project_id:
                raise ValueError(
                    "Firebase app found but no project ID configured. "
                    "Ensure Firebase is properly initialized with credentials."
                )
        except ValueError as e:
            raise ValueError(
                "Firebase app not initialized. "
                "Call initialize_firebase() from app.core.firebase first."
            ) from e

        # Initialize the Firestore client
        _firestore_client = firestore.client()
        logger.info("Firestore client initialized successfully")

    return _firestore_client
