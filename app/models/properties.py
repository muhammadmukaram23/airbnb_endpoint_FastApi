from datetime import time, datetime, timedelta
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator, field_validator
from decimal import Decimal

class PropertyType(str, Enum):
    entire_place = "entire_place"
    private_room = "private_room"
    shared_room = "shared_room"

class PropertyBase(BaseModel):
    host_id: int
    category_id: int
    title: str = Field(..., max_length=255)
    description: str
    property_type: PropertyType
    max_guests: int = Field(default=1, ge=1)
    bedrooms: int = Field(default=0, ge=0)
    beds: int = Field(default=1, ge=1)
    bathrooms: Decimal = Field(default=1.0, ge=0, max_digits=3, decimal_places=1)
    price_per_night: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    cleaning_fee: Decimal = Field(default=0.00, ge=0, max_digits=10, decimal_places=2)
    service_fee_percentage: Decimal = Field(default=3.00, ge=0, le=100, max_digits=5, decimal_places=2)
    minimum_nights: int = Field(default=1, ge=1)
    maximum_nights: int = Field(default=365, ge=1)
    check_in_time: time = Field(default=time(15, 0))
    check_out_time: time = Field(default=time(11, 0))
    instant_book: bool = False
    is_active: bool = True

    @validator('maximum_nights')
    def validate_max_nights(cls, v, values):
        if 'minimum_nights' in values and v < values['minimum_nights']:
            raise ValueError('Maximum nights cannot be less than minimum nights')
        return v

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    host_id: Optional[int] = None
    category_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    property_type: Optional[PropertyType] = None
    max_guests: Optional[int] = Field(None, ge=1)
    bedrooms: Optional[int] = Field(None, ge=0)
    beds: Optional[int] = Field(None, ge=1)
    bathrooms: Optional[Decimal] = Field(None, ge=0, max_digits=3, decimal_places=1)
    price_per_night: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    cleaning_fee: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    service_fee_percentage: Optional[Decimal] = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    minimum_nights: Optional[int] = Field(None, ge=1)
    maximum_nights: Optional[int] = Field(None, ge=1)
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    instant_book: Optional[bool] = None
    is_active: Optional[bool] = None

    @validator('maximum_nights')
    def validate_max_nights(cls, v, values):
        if v is not None and 'minimum_nights' in values and values['minimum_nights'] is not None and v < values['minimum_nights']:
            raise ValueError('Maximum nights cannot be less than minimum nights')
        return v

class PropertyInDB(PropertyBase):
    property_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v),
            time: lambda v: v.strftime('%H:%M:%S') if v else None
        }

class PropertyResponse(PropertyInDB):
    @field_validator('check_in_time', 'check_out_time', mode='before')
    def convert_times(cls, value):
        if value is None:
            return None
        if isinstance(value, timedelta):
            seconds = value.total_seconds()
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return time(hour=hours, minute=minutes)
        return value

    class Config:
        json_encoders = {
            time: lambda v: v.strftime('%H:%M') if v else None,
            Decimal: lambda v: str(v)
        }