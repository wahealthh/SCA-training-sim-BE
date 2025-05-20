from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base_model import BaseModel, Base


class PeerComment(BaseModel, Base):
    """
    Comments from peers on shared consultations
    """
    __tablename__ = 'peer_comments'
    
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    comment = Column(Text, nullable=False)
    
    # Relationships
    consultation = relationship("Consultation", back_populates="peer_comments")
    user = relationship("User", back_populates="comments")
    
    def __repr__(self):
        return f"<PeerComment(id={self.id}, user_id={self.user_id})>" 