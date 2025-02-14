from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from src.db import Base


class Pricing(Base):
    __tablename__ = "pricing"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    task_limit = Column(Integer, nullable=True)   # для пакета
    duration_days = Column(Integer, nullable=True)  # для безлимита

    # Связь с транзакциями
    transactions = relationship("Transaction", back_populates="pricing")
