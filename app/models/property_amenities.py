from pydantic import BaseModel
from typing import Optional

class PropertyAmenityBase(BaseModel):
    property_id: int
    amenity_id: int

class PropertyAmenityCreate(PropertyAmenityBase):
    pass

class PropertyAmenityUpdate(BaseModel):
    old_amenity_id: int
    new_amenity_id: int

class PropertyAmenityResponse(PropertyAmenityBase):
    amenity_name: Optional[str] = None
    amenity_category: Optional[str] = None
    icon_url: Optional[str] = None
    
    class Config:
        from_attributes = True