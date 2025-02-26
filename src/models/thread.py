from sqlalchemy import Column, Integer, String, ForeignKey
from src.db import Base


class UserThread(Base):
    __tablename__ = "user_threads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_name = Column(String)  # например, 'solve_task', 'write_text' и т.д.
    thread_id = Column(String)     # хранит ID треда, созданного ассистентом

    # Если хотите, можно добавить relationship к User:
    # user = relationship("User", backref="threads")
