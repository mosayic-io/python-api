from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.auth import validate_api_key, get_current_user
from app.services.notifications.notification_service import send_notification_to_users, handle_deeplink
from app.services.notifications.models import UserNotificationsRequest

router = APIRouter()


@router.post("/send-push-notification", dependencies=[Depends(validate_api_key)])
async def send_push_notification(
    request: UserNotificationsRequest,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Send push notification to users."""
    return await send_notification_to_users(request, background_tasks)


@router.post("/deeplinks", dependencies=[Depends(get_current_user)])
async def deeplink_shortener(shortened_deeplink: str = Depends(handle_deeplink)) -> JSONResponse:
    """Generate a deep link URL."""
    return JSONResponse(status_code=200, content={"deeplink_url": shortened_deeplink})
