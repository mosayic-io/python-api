from pydantic import BaseModel


class UserNotificationsRequest(BaseModel):
    recipient_ids: list[str]
    title: str = "A Pound of Cure"
    body: str = "You have a new notification"
    deep_link_url: str | None = None


class Notification(BaseModel):
    title: str
    body: str
    image_url: str | None = None
    deep_link_url: str | None = "https://pound-of-cure-llc.web.app"


class UserNotificationCreate(BaseModel):
    user_id: str
    notification: Notification
    is_read: bool = False
