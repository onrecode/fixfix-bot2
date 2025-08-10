"""
Модели базы данных для FixFix Bot
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

Base = declarative_base()


class RequestStatus(str, enum.Enum):
    """Статусы заявок"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class WorkFormat(str, enum.Enum):
    """Форматы работы"""
    HOME_VISIT = "home_visit"
    REMOTE = "remote"
    PICKUP = "pickup"
    OFFICE = "office"


class PreferredTime(str, enum.Enum):
    """Предпочтительное время"""
    MORNING = "morning"
    DAY = "day"
    EVENING = "evening"
    ANY = "any"


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    requests = relationship("Request", back_populates="user")


class Request(Base):
    """Модель заявки"""
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(20), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(200), nullable=False)
    service = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    work_format = Column(Enum(WorkFormat), nullable=False)
    address = Column(Text, nullable=True)
    preferred_time = Column(Enum(PreferredTime), nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.NEW)
    priority = Column(Integer, default=1)  # 1-5, где 5 - высший приоритет
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="requests")
    status_history = relationship("RequestStatusHistory", back_populates="request")
    comments = relationship("RequestComment", back_populates="request")


class RequestStatusHistory(Base):
    """История изменения статусов заявок"""
    __tablename__ = "request_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    old_status = Column(Enum(RequestStatus), nullable=True)
    new_status = Column(Enum(RequestStatus), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    request = relationship("Request", back_populates="status_history")
    user = relationship("User")


class RequestComment(Base):
    """Комментарии к заявкам"""
    __tablename__ = "request_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Внутренний комментарий для менеджеров
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    request = relationship("Request", back_populates="comments")
    user = relationship("User")


class Executor(Base):
    """Модель исполнителя"""
    __tablename__ = "executors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    specialization = Column(String(200), nullable=True)
    rating = Column(Integer, default=0)  # 0-5
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User")


class RequestExecutor(Base):
    """Связь заявок с исполнителями"""
    __tablename__ = "request_executors"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    executor_id = Column(Integer, ForeignKey("executors.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_primary = Column(Boolean, default=False)  # Основной исполнитель
    
    # Связи
    request = relationship("Request")
    executor = relationship("Executor")
