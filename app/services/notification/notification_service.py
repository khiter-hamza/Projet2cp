

from sqlalchemy import select

from app.models.notification import Notification
from app.models.user import User


async def create_notification(db, user_id, title, message, notification_type, demande_id=None):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        demande_id=demande_id
    )
    db.add(notification)
    await db.commit()
  

async def notify_admins(db, title, message, notification_type, demande_id=None):
    admins = await db.execute(
        select(User).where(User.role.in_(['admin_dpgr', 'assistant_dpgr']), User.is_active == True)
    )
    for admin in admins.scalars().all():
        await create_notification(db, admin.id, title, message, notification_type, demande_id)