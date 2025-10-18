import requests
import validators
from fastapi import HTTPException
from app.core.config import get_settings
from app.services.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TinyURLService:
    """Service to create and manage TinyURLs."""

    def __init__(self):
        self.base_url = "https://api.tinyurl.com"
        self.api_key = settings.tinyurl_api_key

    async def _validate_url(self, url: str) -> bool:
        """Validate the given URL."""
        if not validators.url(url):
            logger.error("Invalid URL provided: %s", url)
            raise HTTPException(status_code=400, detail="Invalid URL provided")
        return True

    async def create_deeplink(self, original_deeplink: str) -> str:
        """Create a TinyURL for the given original URL."""
        await self._validate_url(original_deeplink)
        payload = {
            "url": original_deeplink,
            "domain": "tinyurl.com" # change this to pount of cure domain when available
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.post(f"{self.base_url}/create", json=payload, headers=headers)
        except Exception as e:
            logger.error("Error while creating TinyURL: %s", str(e))
            raise HTTPException(status_code=500, detail="Error while creating TinyURL: " + str(e))

        errors = response.json().get("errors")
        if errors:
            logger.error("Failed to create TinyURL: %s", response.text)
            raise HTTPException(status_code=500, detail="Failed to create TinyURL: " + str(errors))

        return response.json().get("data", {}).get("tiny_url")
