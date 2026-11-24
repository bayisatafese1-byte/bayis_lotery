from pydantic import BaseModel, Field
from typing import Optional

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=9, max_length=20)
    password: str = Field(..., min_length=4, max_length=50)

class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=9, max_length=20)
    password: str = Field(..., min_length=4, max_length=50)

class SettingsUpdateRequest(BaseModel):
    deadline: Optional[str] = None
    cbe_account: Optional[str] = None
    telebirr_phone: Optional[str] = None
    cash_contact_name: Optional[str] = None
    cash_contact_phone: Optional[str] = None
    price_amount: Optional[str] = None
    prize_1st: Optional[str] = None
    prize_2nd: Optional[str] = None
    prize_3rd: Optional[str] = None
