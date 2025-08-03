from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class HouseRuleBase(BaseModel):
    property_id: int
    rule_text: str = Field(..., min_length=1, max_length=2000)  # Adjust max_length as needed

class HouseRuleCreate(HouseRuleBase):
    pass

class HouseRuleUpdate(BaseModel):
    rule_text: Optional[str] = Field(None, min_length=1, max_length=2000)

class HouseRuleInDB(HouseRuleBase):
    rule_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Orm_mode in older Pydantic versions
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HouseRuleResponse(HouseRuleInDB):
    pass