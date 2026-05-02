from pydantic import BaseModel
from typing import Optional

class JobCreate(BaseModel):
    customer_name: str
    customer_phone: str
    status: str = "scheduled"
    before_photo_url: Optional[str] = None
    after_photo_url: Optional[str] = None
    