from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, SecretStr


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password1: SecretStr
    password2: SecretStr

    class Config:
        from_attributes = True

