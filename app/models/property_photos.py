from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PropertyPhotoBase(BaseModel):
    property_id: int
    photo_url: str = Field(..., max_length=500)
    caption: Optional[str] = Field(None, max_length=255)
    is_cover_photo: bool = False
    display_order: int = 0

class PropertyPhotoCreate(PropertyPhotoBase):
    pass

class PropertyPhotoUpdate(BaseModel):
    photo_url: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = Field(None, max_length=255)
    is_cover_photo: Optional[bool] = None
    display_order: Optional[int] = None

class PropertyPhotoInDB(PropertyPhotoBase):
    photo_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PropertyPhotoResponse(PropertyPhotoInDB):
    pass