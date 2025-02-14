from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.db import Base


class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    feedback_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now())

    user = relationship("User", back_populates="feedbacks")
