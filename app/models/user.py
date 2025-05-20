from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from sqlalchemy.sql import func

from app.models.base_model import BaseModel, Base


class User(BaseModel, Base):
    __tablename__ = "users"
    
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=False)
    
    # Relationships
    consultations = relationship("Consultation", back_populates="user")

    def __repr__(self):
        return f"<User(first_name='{self.first_name}', last_name='{self.last_name}')>"
