from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from app.services.notifications.models import UserNotificationsRequest, Notification
from app.services.notifications.fcm import PushNotificationService
from app.services.logger import get_logger
from app.core.links import TinyURLService
from app.core.supabase import supabase
from app.schemas.links import DeepLinkRequest


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


async def handle_deeplink(body: DeepLinkRequest) -> str:
    """Generate a deep link URL."""
    response = supabase.table(body.table_name).select('*').eq('id', body.record_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Record not found")

    deeplink_url = response.data[0].get('deeplink_url')
    if not deeplink_url:
        deeplink_url = await TinyURLService().create_deeplink(body.original_deeplink)

    try:
        response = supabase.table(body.table_name).update({'deeplink_url': deeplink_url}).eq('id', body.record_id).execute()
    except Exception as e:
        logger.error("Error updating deeplink URL in database: %s", str(e))
        raise HTTPException(status_code=500, detail="Error updating deeplink URL in database: " + str(e))

    return deeplink_url
