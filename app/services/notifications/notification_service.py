from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from app.services.notifications.models import UserNotificationsRequest, Notification
from app.services.notifications.fcm import PushNotificationService
from app.services.logger import get_logger

logger = get_logger(__name__)


async def send_notification_to_users(unr: UserNotificationsRequest, background_tasks: BackgroundTasks) -> JSONResponse:
    pns = PushNotificationService()

    if unr.recipient_ids == ['all']:
        unr.recipient_ids = pns.get_all_users()

    if not unr.recipient_ids:
        logger.warning("No recipient IDs provided for notification")
        raise HTTPException(status_code=400, detail="No recipient IDs provided for notification")

    logger.debug("Sending notification to users. Deep link: %s", str(unr.deep_link_url))
    notification = Notification(title=unr.title, body=unr.body, deep_link_url=unr.deep_link_url)
    background_tasks.add_task(pns.send_notification_to_users, unr.recipient_ids, notification)
    return JSONResponse(
        status_code=200,
        content={"message": "Notification sent successfully"}
    )
