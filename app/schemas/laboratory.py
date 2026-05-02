from pydantic import BaseModel, ConfigDict
from uuid import UUID

class LaboratoryBase(BaseModel):
    name: str

class CreateLaboratory(LaboratoryBase):
    pass

class UpdateLaboratory(LaboratoryBase):
    pass

class LaboratoryResponse(LaboratoryBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
