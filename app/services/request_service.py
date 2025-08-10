"""
Сервис для работы с заявками
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.database.models import Request, User, RequestStatus, RequestStatusHistory, RequestComment
from app.schemas.requests import RequestCreate, RequestUpdate, RequestStatusUpdate
from app.config import settings


class RequestService:
    """Сервис для работы с заявками"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_request(self, user_id: int, request_data: RequestCreate) -> Request:
        """Создание новой заявки"""
        # Проверяем лимит заявок пользователя
        active_requests = await self.get_user_active_requests_count(user_id)
        if active_requests >= settings.max_requests_per_user:
            raise ValueError(f"Превышен лимит активных заявок ({settings.max_requests_per_user})")
        
        # Генерируем уникальный ID заявки
        request_id = await self._generate_request_id()
        
        # Создаем заявку
        db_request = Request(
            request_id=request_id,
            user_id=user_id,
            **request_data.dict()
        )
        
        self.db.add(db_request)
        await self.db.commit()
        await self.db.refresh(db_request)
        
        # Создаем запись в истории статусов
        status_history = RequestStatusHistory(
            request_id=db_request.id,
            new_status=RequestStatus.NEW,
            changed_by=user_id,
            comment="Заявка создана"
        )
        self.db.add(status_history)
        await self.db.commit()
        
        return db_request
    
    async def get_request(self, request_id: str) -> Optional[Request]:
        """Получение заявки по ID"""
        result = await self.db.execute(
            select(Request)
            .options(selectinload(Request.user))
            .options(selectinload(Request.status_history))
            .options(selectinload(Request.comments))
            .where(Request.request_id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_requests(
        self, 
        user_id: int, 
        status: Optional[RequestStatus] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Request], int]:
        """Получение заявок пользователя с пагинацией"""
        # Базовый запрос
        query = select(Request).where(Request.user_id == user_id)
        
        # Фильтр по статусу
        if status:
            query = query.where(Request.status == status)
        
        # Общее количество
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Пагинация
        query = query.offset((page - 1) * per_page).limit(per_page)
        query = query.order_by(Request.created_at.desc())
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        return list(requests), total
    
    async def update_request_status(
        self, 
        request_id: str, 
        new_status: RequestStatusUpdate,
        changed_by: int
    ) -> Request:
        """Обновление статуса заявки"""
        request = await self.get_request(request_id)
        if not request:
            raise ValueError("Заявка не найдена")
        
        old_status = request.status
        request.status = new_status.status
        
        if new_status.priority:
            request.priority = new_status.priority
        
        if new_status.status == RequestStatus.COMPLETED:
            request.completed_at = datetime.utcnow()
        
        request.updated_at = datetime.utcnow()
        
        # Создаем запись в истории
        status_history = RequestStatusHistory(
            request_id=request.id,
            old_status=old_status,
            new_status=new_status.status,
            changed_by=changed_by,
            comment=new_status.comment
        )
        
        self.db.add(status_history)
        await self.db.commit()
        await self.db.refresh(request)
        
        return request
    
    async def add_comment(
        self, 
        request_id: str, 
        user_id: int, 
        comment: str,
        is_internal: bool = False
    ) -> RequestComment:
        """Добавление комментария к заявке"""
        request = await self.get_request(request_id)
        if not request:
            raise ValueError("Заявка не найдена")
        
        db_comment = RequestComment(
            request_id=request.id,
            user_id=user_id,
            comment=comment,
            is_internal=is_internal
        )
        
        self.db.add(db_comment)
        await self.db.commit()
        await self.db.refresh(db_comment)
        
        return db_comment
    
    async def get_user_active_requests_count(self, user_id: int) -> int:
        """Получение количества активных заявок пользователя"""
        result = await self.db.execute(
            select(func.count())
            .select_from(Request)
            .where(
                and_(
                    Request.user_id == user_id,
                    or_(
                        Request.status == RequestStatus.NEW,
                        Request.status == RequestStatus.IN_PROGRESS
                    )
                )
            )
        )
        return result.scalar() or 0
    
    async def _generate_request_id(self) -> str:
        """Генерация уникального ID заявки"""
        import random
        import string
        
        while True:
            # Формат: FF-YYYYMMDD-XXXX
            date_part = datetime.now().strftime("%Y%m%d")
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            request_id = f"FF-{date_part}-{random_part}"
            
            # Проверяем уникальность
            existing = await self.db.execute(
                select(Request).where(Request.request_id == request_id)
            )
            if not existing.scalar_one_or_none():
                return request_id
    
    async def get_requests_for_executor(
        self,
        executor_id: int,
        status: Optional[RequestStatus] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Request], int]:
        """Получение заявок для исполнителя"""
        # TODO: Реализовать логику получения заявок для исполнителя
        # Пока возвращаем пустой список
        return [], 0
    
    async def assign_executor(
        self, 
        request_id: str, 
        executor_id: int,
        assigned_by: int
    ) -> bool:
        """Назначение исполнителя на заявку"""
        # TODO: Реализовать назначение исполнителя
        return True
