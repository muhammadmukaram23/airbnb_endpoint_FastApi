from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl

class PropertyCategoryBase(BaseModel):
    category_name: str
    description: Optional[str] = None
    icon_url: Optional[HttpUrl] = None  # Using HttpUrl for URL validation
    is_active: bool = True

class PropertyCategoryCreate(PropertyCategoryBase):
    pass

class PropertyCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None

class PropertyCategoryInDB(PropertyCategoryBase):
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # For ORM compatibility (formerly orm_mode)

class PropertyCategoryResponse(PropertyCategoryInDB):
    pass