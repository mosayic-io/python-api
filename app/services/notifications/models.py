from pydantic import BaseModel


class UserNotificationsRequest(BaseModel):
    recipient_ids: list[str]
    title: str = "You have a new notification"
    body: str = ""
    deep_link_url: str | None = None


class Notification(BaseModel):
    title: str
    body: str
    image_url: str | None = None
    deep_link_url: str | None = None


class UserNotificationCreate(BaseModel):
    user_id: str
    notification: Notification
    is_read: bool = False
