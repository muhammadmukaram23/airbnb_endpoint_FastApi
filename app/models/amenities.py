from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class AmenityBase(BaseModel):
    amenity_name: str = Field(..., max_length=100)
    amenity_category: str = Field(..., max_length=50)
    icon_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    is_active: bool = True

class AmenityCreate(AmenityBase):
    pass

class AmenityUpdate(BaseModel):
    amenity_name: Optional[str] = Field(None, max_length=100)
    amenity_category: Optional[str] = Field(None, max_length=50)
    icon_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AmenityInDB(AmenityBase):
    amenity_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AmenityResponse(AmenityInDB):
    pass