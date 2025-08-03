from datetime import date, datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    in_progress = "in_progress"

class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    partially_paid = "partially_paid"
    refunded = "refunded"
    failed = "failed"

class BookingBase(BaseModel):
    property_id: int
    guest_id: int
    check_in_date: date
    check_out_date: date
    num_guests: int = Field(..., gt=0)
    total_nights: int = Field(..., gt=0)
    base_price: float = Field(..., gt=0)
    cleaning_fee: float = Field(0.00, ge=0)
    service_fee: float = Field(..., ge=0)
    taxes: float = Field(0.00, ge=0)
    total_amount: float = Field(..., gt=0)
    booking_status: BookingStatus = BookingStatus.pending
    payment_status: PaymentStatus = PaymentStatus.pending
    special_requests: Optional[str] = Field(None, max_length=1000)
    cancellation_reason: Optional[str] = Field(None, max_length=500)

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    num_guests: Optional[int] = Field(None, gt=0)
    total_nights: Optional[int] = Field(None, gt=0)
    base_price: Optional[float] = Field(None, gt=0)
    cleaning_fee: Optional[float] = Field(None, ge=0)
    service_fee: Optional[float] = Field(None, ge=0)
    taxes: Optional[float] = Field(None, ge=0)
    total_amount: Optional[float] = Field(None, gt=0)
    booking_status: Optional[BookingStatus] = None
    payment_status: Optional[PaymentStatus] = None
    special_requests: Optional[str] = Field(None, max_length=1000)
    cancellation_reason: Optional[str] = Field(None, max_length=500)

class BookingInDB(BookingBase):
    booking_id: int
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class BookingResponse(BookingInDB):
    pass