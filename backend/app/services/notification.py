import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session as SqlSession

from app.models.notification import Notification
from app.services.audit_log import AuditLogService

# Provider Interfaces
class BaseEmailProvider(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        pass

class BaseSMSProvider(ABC):
    @abstractmethod
    def send_sms(self, phone: str, text: str) -> bool:
        pass

class BasePushProvider(ABC):
    @abstractmethod
    def send_push(self, user_id: int, title: str, body: str) -> bool:
        pass

# Mock Providers
class MockEmailProvider(BaseEmailProvider):
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        logging.info(f"[MockEmail] Sent to {to_email} | Subject: {subject}")
        return True

class MockSMSProvider(BaseSMSProvider):
    def send_sms(self, phone: str, text: str) -> bool:
        logging.info(f"[MockSMS] Sent to {phone} | Content: {text}")
        return True

class MockPushProvider(BasePushProvider):
    def send_push(self, user_id: int, title: str, body: str) -> bool:
        logging.info(f"[MockPush] Sent to User ID {user_id} | Title: {title}")
        return True


class NotificationService:
    def __init__(self, db: SqlSession):
        self.db = db
        # Instantiating concrete mock channels
        self.email_provider = MockEmailProvider()
        self.sms_provider = MockSMSProvider()
        self.push_provider = MockPushProvider()

    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notif_type: str = "System",
        email_recipient: Optional[str] = None,
        phone_recipient: Optional[str] = None
    ) -> Notification:
        """
        Deliver a multi-channel notification: In-App, Email, SMS, and Push alerts.
        """
        # 1. Store In-App Notification in DB
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            is_read=False
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)

        # 2. Trigger Email mock channel
        if email_recipient:
            self.email_provider.send_email(
                to_email=email_recipient,
                subject=title,
                body=message
            )

        # 3. Trigger SMS mock channel
        if phone_recipient:
            self.sms_provider.send_sms(
                phone=phone_recipient,
                text=message
            )

        # 4. Trigger Push mock channel
        self.push_provider.send_push(
            user_id=user_id,
            title=title,
            body=message
        )

        # 5. Log audit trail
        AuditLogService.log_event(
            db=self.db,
            actor_id=user_id,
            action="NotificationDelivery",
            module="Notification",
            new_value=f"In-app notification ID {notif.id} sent to User {user_id}. Type: {notif_type}"
        )

        return notif

    def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Notification]:
        return self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(limit).all()

    def mark_as_read(self, notif_id: int, user_id: int) -> Optional[Notification]:
        notif = self.db.query(Notification).filter(
            Notification.id == notif_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
            self.db.commit()
            self.db.refresh(notif)
        return notif

    def clear_all(self, user_id: int) -> None:
        self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).delete()
        self.db.commit()
