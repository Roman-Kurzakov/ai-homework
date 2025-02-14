from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship

from src.db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, index=True)
    class_level = Column(String, nullable=True)  # класс или уровень образования
    remaining_tasks = Column(Integer, default=3)
    subscription_type = Column(String, nullable=False, default='free')
    solved_tasks_count = Column(Integer, nullable=False, default=0)
    referred_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)  # Ссылка на пригласившего пользователя
    referral_bonus_claimed = Column(Boolean, default=False)

    feedbacks = relationship("Feedback", back_populates="user")
