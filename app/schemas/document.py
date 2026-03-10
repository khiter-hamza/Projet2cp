import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.enums import Documents_type


class DocumentResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    document_type: Documents_type
    file_name: str
    file_size: int
    mime_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}
