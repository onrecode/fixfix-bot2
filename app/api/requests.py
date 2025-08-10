"""
API endpoints для работы с заявками
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.request_service import RequestService
from app.schemas.requests import (
    RequestCreate, 
    RequestResponse, 
    RequestUpdate, 
    RequestStatusUpdate,
    RequestListResponse,
    RequestCommentCreate,
    RequestCommentResponse
)
from app.database.models import RequestStatus

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_data: RequestCreate,
    user_id: int = Query(..., description="ID пользователя"),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой заявки"""
    try:
        service = RequestService(db)
        request = await service.create_request(user_id, request_data)
        return request
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка создания заявки")


@router.get("/{request_id}", response_model=RequestResponse)
async def get_request(
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получение заявки по ID"""
    service = RequestService(db)
    request = await service.get_request(request_id)
    
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    
    return request


@router.get("/user/{user_id}", response_model=RequestListResponse)
async def get_user_requests(
    user_id: int,
    status: Optional[RequestStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(10, ge=1, le=100, description="Количество на странице"),
    db: AsyncSession = Depends(get_db)
):
    """Получение заявок пользователя"""
    service = RequestService(db)
    requests, total = await service.get_user_requests(user_id, status, page, per_page)
    
    return RequestListResponse(
        requests=requests,
        total=total,
        page=page,
        per_page=per_page
    )


@router.put("/{request_id}/status", response_model=RequestResponse)
async def update_request_status(
    request_id: str,
    status_update: RequestStatusUpdate,
    changed_by: int = Query(..., description="ID пользователя, изменившего статус"),
    db: AsyncSession = Depends(get_db)
):
    """Обновление статуса заявки"""
    try:
        service = RequestService(db)
        request = await service.update_request_status(request_id, status_update, changed_by)
        return request
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка обновления статуса")


@router.post("/{request_id}/comments", response_model=RequestCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    request_id: str,
    comment_data: RequestCommentCreate,
    user_id: int = Query(..., description="ID пользователя"),
    db: AsyncSession = Depends(get_db)
):
    """Добавление комментария к заявке"""
    try:
        service = RequestService(db)
        comment = await service.add_comment(
            request_id, 
            user_id, 
            comment_data.comment,
            comment_data.is_internal
        )
        return comment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка добавления комментария")


@router.get("/", response_model=RequestListResponse)
async def get_all_requests(
    status: Optional[RequestStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(10, ge=1, le=100, description="Количество на странице"),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех заявок (для администраторов)"""
    # TODO: Добавить проверку прав администратора
    service = RequestService(db)
    # Пока возвращаем пустой список, нужно реализовать метод в сервисе
    return RequestListResponse(
        requests=[],
        total=0,
        page=page,
        per_page=per_page
    )
