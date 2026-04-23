# Import all models here so SQLAlchemy can resolve relationships
from app.models.user import User
from app.models.laboratory import Laboratory
from app.models.notification import Notification
from app.models.application import Application
from app.models.document import Document
from app.models.session import Session
from app.models.password_reset_token import PasswordResetToken
from app.models.indemnity_calculation import Idemnity
from app.models.zone import Zone
