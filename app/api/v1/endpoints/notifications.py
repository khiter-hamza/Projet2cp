from sqlalchemy import select
import uuid
from fastapi import APIRouter , Depends , HTTPException
from app.core.database import AsyncSessionLocal
from app.core.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.user import UserResponse
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.core.dependencies import get_current_user

router = APIRouter() 
@router.get("/", response_model=list[NotificationResponse])
async def get_Notification(user:UserResponse=Depends(get_current_user),db:AsyncSessionLocal=Depends(get_db),limit:int=10,offset:int=0):
      result = await db.execute(select(Notification).where(Notification.user_id==user.id).order_by(Notification.created_at.desc()).limit(limit).offset(offset))
      return result.scalars().all()


@router.delete("/{notification_id}")
async def delete_Notification(notification_id:uuid.UUID,user:UserResponse=Depends(get_current_user),db:AsyncSessionLocal=Depends(get_db)):
      result = await db.execute(select(Notification).where(Notification.id==notification_id))
      notification = result.scalar_one_or_none()
      if not notification:
            raise HTTPException(status_code=404,detail="Notification not found")
      if notification.user_id != user.id:
            raise HTTPException(status_code=403,detail="Not authorized to delete this notification")
      await db.delete(notification)
      await db.commit()
      return {"detail":"Notification deleted successfully"}



@router.get("/count-unread", response_model=UnreadCountResponse)
async def count_unread_notifications(user:UserResponse=Depends(get_current_user),db:AsyncSessionLocal=Depends(get_db)):
      result= await db.execute(select(Notification).where(Notification.user_id==user.id,Notification.is_read==False))
      unread_count=result.scalars().count()
      return UnreadCountResponse(unread_count=unread_count)

      
@router.patch("/{notification_id}/mark-as-read")
async def mark_notification_as_read(notification_id:uuid.UUID,user:UserResponse=Depends(get_current_user),db:AsyncSessionLocal=Depends(get_db)):
      result = await db.execute(select(Notification).where(Notification.id==notification_id))
      notification = result.scalar_one_or_none()
      if not notification:
            raise HTTPException(status_code=404,detail="Notification not found")
      if notification.user_id != user.id:
            raise HTTPException(status_code=403,detail="Not authorized to mark this notification as read")
      notification.mark_as_read()
      await db.commit()
      return {"detail":"Notification marked as read successfully"}
@router.patch("/mark-all-as-read")


async def mark_all_notifications_as_read(user:UserResponse=Depends(get_current_user),db:AsyncSessionLocal=Depends(get_db)):
      result = await db.execute(select(Notification).where(Notification.user_id==user.id,Notification.is_read==False))
      notifications = result.scalars().all()
      for notification in notifications:
            notification.mark_as_read()
      await db.commit()
      return {"detail":"All notifications marked as read successfully"}



