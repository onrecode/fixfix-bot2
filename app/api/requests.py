"""
API endpoints для работы с заявками
"""
from typing import List, Optional
import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
from app.database.models import RequestStatus, User, WorkFormat, PreferredTime
from app.config import settings
import httpx

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_data: RequestCreate,
    user_id: Optional[int] = Query(None, description="ID пользователя в БД (или telegram_id для обратной совместимости)"),
    telegram_id: Optional[int] = Query(None, description="Telegram ID пользователя"),
    db: AsyncSession = Depends(get_db)
):
    """Создание новой заявки.

    Логика разрешения пользователя:
    - Если передан telegram_id: находим/создаём пользователя по telegram_id
    - Иначе если передан user_id:
        - пытаемся найти пользователя по внутреннему user_id
        - если не найден, пробуем трактовать user_id как telegram_id (для обратной совместимости)
        - если не найден и это telegram_id: создаём пользователя
    """
    try:
        # Определяем/создаём пользователя
        resolved_user: Optional[User] = None

        if telegram_id is not None:
            result = await db.execute(select(User).where(User.telegram_id == telegram_id))
            resolved_user = result.scalar_one_or_none()
            if resolved_user is None:
                # Создаём минимального пользователя
                new_user = User(telegram_id=telegram_id)
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                resolved_user = new_user
        elif user_id is not None:
            # Сначала пробуем как внутренний ID
            result = await db.execute(select(User).where(User.id == user_id))
            resolved_user = result.scalar_one_or_none()
            if resolved_user is None:
                # Пробуем трактовать как telegram_id (обратная совместимость со старым ботом)
                result = await db.execute(select(User).where(User.telegram_id == user_id))
                resolved_user = result.scalar_one_or_none()
                if resolved_user is None:
                    # Создаём пользователя, считая, что нам передали telegram_id в user_id
                    new_user = User(telegram_id=user_id)
                    db.add(new_user)
                    await db.commit()
                    await db.refresh(new_user)
                    resolved_user = new_user

        if resolved_user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось определить пользователя")

        service = RequestService(db)
        request = await service.create_request(resolved_user.id, request_data)
        return request
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка создания заявки")


async def _send_service_log(text: str) -> None:
    """Отправка сообщения в сервисный чат (Telegram)."""
    try:
        token = settings.telegram.token if settings.telegram else None
        chat_id = settings.telegram.requests_group_id if settings.telegram else None
        if not token or not chat_id:
            return
        api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(api_url, json=payload)
    except Exception:
        # Без падения API
        pass


@router.post("/check")
async def check_flow(admin_id: int = Query(..., description="Telegram ID администратора"), db: AsyncSession = Depends(get_db)):
    """Сервисная проверка формирования заявки. Доступно только админам.

    Выбирает случайную категорию/услугу/формат/время, подставляет timestamp
    в описание и адрес (если требуется), создаёт заявку и помечает её завершённой.
    Отправляет лог в сервисный чат с деталями успеха/ошибки.
    """
    if not settings.telegram or admin_id not in (settings.telegram.admin_ids or []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    step = "start"
    try:
        # Каталог (синхронизирован с ботом)
        catalog = {
            "🔴 Компьютер глючит/не работает": [
                "💻 Тормозит/Не включается",
                "🔧 Выскакивают ошибки",
                "🦠 Вирусы и реклама",
                "✍️ Свой вариант",
            ],
            "⚙️ Установить/Настроить программу": [
                "📦 Установить программу",
                "🌐 Настроить интернет",
                "🖨️ Подключить устройства",
                "✍️ Свой вариант",
            ],
            "📷 Подключить/Настроить устройство": [
                "🖨️ Настроить принтер/сканер",
                "🎮 Настроить приставку",
                "🖱️ Настроить мышь/клавиатуру",
                "📱 Подключить телефон",
                "📺 Подключить телевизор",
                "✍️ Свой вариант",
            ],
            "🚀 Хочу апгрейд": [
                "💾 Увеличить оперативную память",
                "🔧 Заменить процессор",
                "💿 Установить SSD диск",
                "🎮 Установить видеокарту",
                "🖥️ Заменить блок питания",
                "❄️ Улучшить охлаждение",
                "🔧 Собрать ПК с нуля",
                "💻 Подбор комплектующих",
                "✍️ Свой вариант",
            ],
            "🌐 «Слабый Wi-Fi / новый роутер»": [
                "📶 Настроить Wi-Fi роутер",
                "🌐 Усилить сигнал",
                "🔐 Установить пароль",
                "📡 Новый роутер",
                "📱 Подключить устройства",
                "✍️ Свой вариант",
            ],
            "🔒 VPN и Защита данных": [
                "🔐 Настроить VPN",
                "🛡️ Проверка на вирусы",
                "💾 Восстановление данных",
                "🔒 Шифрование",
                "🔑 Парольная защита",
                "✍️ Свой вариант",
            ],
        }

        step = "randomize"
        timestamp = datetime.utcnow().isoformat()
        category = random.choice(list(catalog.keys()))
        service = random.choice(catalog[category])
        work_format = random.choice(list(WorkFormat))
        preferred_time = random.choice(list(PreferredTime))
        description = f"auto-check {timestamp}"
        address = f"auto-check address {timestamp}" if work_format in (WorkFormat.HOME_VISIT, WorkFormat.PICKUP) else None

        step = "ensure_user"
        result = await db.execute(select(User).where(User.telegram_id == admin_id))
        db_user = result.scalar_one_or_none()
        if db_user is None:
            db_user = User(telegram_id=admin_id)
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)

        step = "create_request"
        service_layer = RequestService(db)
        payload = {
            "category": category,
            "service": service,
            "description": description,
            "work_format": work_format,
            "address": address,
            "preferred_time": preferred_time,
        }
        request = await service_layer.create_request(db_user.id, RequestCreate(**payload))

        step = "complete_request"
        await service_layer.update_request_status(
            request.request_id,
            RequestStatusUpdate(status=RequestStatus.COMPLETED, comment="auto-check"),
            changed_by=db_user.id,
        )

        log_text = (
            "✅ CHECK OK\n"
            f"step: {step}\n"
            f"request_id: {request.request_id}\n"
            f"category: {category}\nservice: {service}\nformat: {work_format.value}\ntime: {preferred_time.value}"
        )
        await _send_service_log(log_text)
        return {"ok": True, "request_id": request.request_id, "category": category, "service": service}

    except Exception as e:
        err_text = (
            "❌ CHECK FAIL\n"
            f"step: {step}\n"
            f"error: {str(e)}"
        )
        await _send_service_log(err_text)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ошибка на шаге {step}: {e}")


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
