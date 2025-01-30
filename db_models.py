from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger, Boolean
from sqlalchemy.orm import relationship
from db import Base
from sqlalchemy.sql import func
from datetime import datetime, timezone

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


class Pricing(Base):
    __tablename__ = "pricing"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    task_limit = Column(Integer, nullable=True)   # для пакета
    duration_days = Column(Integer, nullable=True) # для безлимита

    # Связь с транзакциями
    transactions = relationship("Transaction", back_populates="pricing")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pricing_id = Column(Integer, ForeignKey("pricing.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, default="success") # success / error
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", backref="transactions")
    pricing = relationship("Pricing", back_populates="transactions")


class UserThread(Base):
    __tablename__ = "user_threads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_name = Column(String)  # например, 'solve_task', 'write_text' и т.д.
    thread_id = Column(String)     # хранит ID треда, созданного ассистентом

    # Если хотите, можно добавить relationship к User:
    # user = relationship("User", backref="threads")

class Feedback(Base):
    __tablename__ = 'feedback'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    feedback_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now())

    user = relationship("User", back_populates="feedbacks")