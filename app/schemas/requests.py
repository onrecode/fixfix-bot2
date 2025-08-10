"""
Схемы для заявок
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.database.models import RequestStatus, WorkFormat, PreferredTime


class RequestBase(BaseModel):
    """Базовая схема заявки"""
    category: str = Field(..., min_length=1, max_length=200, description="Категория услуги")
    service: Optional[str] = Field(None, max_length=200, description="Конкретная услуга")
    description: Optional[str] = Field(None, max_length=1000, description="Описание проблемы")
    work_format: WorkFormat = Field(..., description="Формат работы")
    address: Optional[str] = Field(None, max_length=500, description="Адрес для выезда")
    preferred_time: PreferredTime = Field(..., description="Предпочтительное время")
    
    @validator('description')
    def validate_description(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('Описание должно содержать минимум 10 символов')
        return v
    
    @validator('address')
    def validate_address(cls, v):
        if v and len(v.strip()) < 5:
            raise ValueError('Адрес должен содержать минимум 5 символов')
        return v


class RequestCreate(RequestBase):
    """Схема для создания заявки"""
    pass


class RequestUpdate(BaseModel):
    """Схема для обновления заявки"""
    category: Optional[str] = Field(None, min_length=1, max_length=200)
    service: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    work_format: Optional[WorkFormat] = None
    address: Optional[str] = Field(None, max_length=500)
    preferred_time: Optional[PreferredTime] = None
    status: Optional[RequestStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class RequestResponse(RequestBase):
    """Схема для ответа с заявкой"""
    id: int
    request_id: str
    user_id: int
    status: RequestStatus
    priority: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RequestListResponse(BaseModel):
    """Схема для списка заявок"""
    requests: list[RequestResponse]
    total: int
    page: int
    per_page: int


class RequestStatusUpdate(BaseModel):
    """Схема для обновления статуса заявки"""
    status: RequestStatus
    comment: Optional[str] = Field(None, max_length=500)
    priority: Optional[int] = Field(None, ge=1, le=5)


class RequestCommentCreate(BaseModel):
    """Схема для создания комментария"""
    comment: str = Field(..., min_length=1, max_length=500)
    is_internal: bool = Field(default=False, description="Внутренний комментарий")


class RequestCommentResponse(BaseModel):
    """Схема для ответа с комментарием"""
    id: int
    request_id: int
    user_id: int
    comment: str
    is_internal: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
