from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.db import Base


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pricing_id = Column(Integer, ForeignKey("pricing.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, default="success")  # success / error
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", backref="transactions")
    pricing = relationship("Pricing", back_populates="transactions")
