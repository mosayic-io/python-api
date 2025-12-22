from supabase_auth.types import UserResponse
from supabase._async.client import AsyncClient, create_client
from app.core.logger import get_logger
from app.core.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class SupabaseClient:
    """
    Singleton class to manage a single instance of the Supabase Client.

    This class ensures that only one instance of the Supabase client exists throughout
    the application's lifecycle. It provides methods to initialize, retrieve, and close
    the Supabase client, facilitating centralized management of Supabase interactions.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize environment settings and placeholders for Supabase client."""
        if not hasattr(self, '_initialized'):  # Prevent reinitialization on multiple calls
            self.supabase_url = settings.supabase_url
            self.supabase_secret_key = settings.supabase_secret_key
            self._client: AsyncClient | None = None
            self._initialized = True  # Flag to indicate instance has been initialized

    async def initialize_client(self) -> None:
        """
        Initializes the Supabase Client instance asynchronously.
        """
        if self._client is None:
            self._client = await create_client(self.supabase_url, self.supabase_secret_key)
            logger.info("Supabase Client initialized.")

    async def get_client(self) -> AsyncClient:
        """
        Retrieves the Supabase Client instance.

        Returns:
            AsyncClient: The initialized Supabase Client instance.

        Raises:
            ValueError: If the Supabase client has not been initialized.
        """
        if self._client is None:
            await self.initialize_client()
        assert self._client is not None
        return self._client

    async def close_client(self) -> None:
        """
        Closes the Supabase Client instance.

        This method gracefully resets the Supabase client, allowing for re-initialization if necessary.
        """
        if self._client is None:
            raise ValueError("Supabase client has not been initialized.")
        self._client = None
        logger.info("Supabase Client closed.")

    async def verify_token(self, token: str) -> UserResponse:
        """
        Verifies a Supabase JWT token using the Supabase Auth API.

        Args:
            token: The JWT token to verify.

        Returns:
            The UserResponse containing user data.

        Raises:
            ValueError: If the token is invalid or user not found.
        """
        client = await self.get_client()
        user_response = await client.auth.get_user(jwt=token)
        if user_response is None or user_response.user is None:
            raise ValueError("Invalid authentication token")
        return user_response


async def get_supabase_client() -> AsyncClient:
    """
    Retrieves the singleton Supabase Client instance.

    Returns:
        AsyncClient: The initialized Supabase Client instance.
    """
    supabase_client_instance = SupabaseClient()
    return await supabase_client_instance.get_client()
