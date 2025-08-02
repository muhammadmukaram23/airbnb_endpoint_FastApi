from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel

class AddressType(str, Enum):
    home = "home"
    billing = "billing"
    other = "other"

class UserAddressBase(BaseModel):
    user_id: int
    address_type: AddressType = AddressType.home
    street_address: str
    city: str
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    is_primary: bool = False

class UserAddressCreate(UserAddressBase):
    pass

class UserAddressUpdate(BaseModel):
    address_type: Optional[AddressType] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_primary: Optional[bool] = None

class UserAddressInDB(UserAddressBase):
    address_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserAddressResponse(UserAddressInDB):
    pass