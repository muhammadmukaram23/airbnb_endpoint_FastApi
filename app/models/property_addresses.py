from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal

class PropertyAddressBase(BaseModel):
    property_id: int
    street_address: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(..., max_length=100)
    latitude: Optional[Decimal] = Field(None, max_digits=10, decimal_places=8)
    longitude: Optional[Decimal] = Field(None, max_digits=11, decimal_places=8)
    neighborhood: Optional[str] = Field(None, max_length=100)

class PropertyAddressCreate(PropertyAddressBase):
    pass

class PropertyAddressUpdate(BaseModel):
    street_address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = Field(None, max_digits=10, decimal_places=8)
    longitude: Optional[Decimal] = Field(None, max_digits=11, decimal_places=8)
    neighborhood: Optional[str] = Field(None, max_length=100)

class PropertyAddressInDB(PropertyAddressBase):
    address_id: int
    created_at: Optional[datetime] = None  # Make this optional

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)
        }

class PropertyAddressResponse(PropertyAddressInDB):
    pass