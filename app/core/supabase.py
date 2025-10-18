import warnings
from supabase import Client, create_client
from app.core.config import get_settings

# TODO: Claude screwed us over here, need to fix these deprecations rather than silence them.
warnings.filterwarnings(
    "ignore",
    message="The 'timeout' parameter is deprecated",
    category=DeprecationWarning
)
warnings.filterwarnings(
    "ignore",
    message="The 'verify' parameter is deprecated",
    category=DeprecationWarning
)

settings = get_settings()

# Initialize Supabase client lazily to avoid import-time secret fetching
# TODO get rid of this awful global variable antipattern
_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get the Supabase client, initializing it if needed."""
    global _supabase_client
    if _supabase_client is None:
        # Get Supabase URL and Key from the appropriate Secret Manager via our config
        url = settings.supabase_url
        key = settings.supabase_service_role_key

        if not url or not key:
            raise ValueError(
                "Supabase URL or Key not found. "
                "Ensure 'supabase-url' and 'supabase-service-role-key' secrets exist "
                "in the correct GCP Project's Secret Manager for the current ENVIRONMENT."
            )

        # Initialize the Supabase client
        _supabase_client = create_client(url, key)

    return _supabase_client

# For backward compatibility, expose the client as 'supabase'
# This will be initialized on first access
class SupabaseClientProxy:
    def __getattr__(self, name):
        return getattr(get_supabase_client(), name)

supabase = SupabaseClientProxy()
