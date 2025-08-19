#!/usr/bin/env python3
"""
Автотест/скрипт для массового формирования всех возможных заявок через слой сервисов.

Как запускать (в контейнере):
  docker-compose exec app python scripts/generate_all_requests.py

Скрипт:
  - создаёт (или находит) тестового пользователя в БД
  - перебирает ВСЕ комбинации: категории × услуги × форматы × предпочтительное время
  - для форматов, которые требуют адрес (home_visit, pickup) — добавляет адрес
  - создаёт заявки через RequestService
  - печатает итоги
"""

import asyncio
from typing import Dict, List, Tuple

from sqlalchemy import select

from app.database.connection import get_db, init_db
from app.database.models import (
    User,
    Request,
    WorkFormat,
    PreferredTime,
    RequestStatus,
)
from app.services.request_service import RequestService
from app.schemas.requests import RequestCreate, RequestStatusUpdate


TEST_TELEGRAM_ID = 999_000_001
TEST_USERNAME = "autotest_user"
TEST_FIRST_NAME = "Auto"
TEST_LAST_NAME = "Tester"


def build_catalog() -> Dict[str, List[str]]:
    """Возвращает словарь: категория -> список услуг.

    Категории и услуги синхронизированы с `bot/keyboards.py` и `bot/handlers.py`.
    Отдельно обрабатывается категория "✍️ Описать запрос своими словами" (без выбора услуги).
    """
    return {
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


def build_formats() -> List[WorkFormat]:
    return [
        WorkFormat.HOME_VISIT,
        WorkFormat.REMOTE,
        WorkFormat.PICKUP,
        WorkFormat.OFFICE,
    ]


def build_times() -> List[PreferredTime]:
    return [
        PreferredTime.MORNING,
        PreferredTime.DAY,
        PreferredTime.EVENING,
        PreferredTime.ANY,
    ]


def make_description(category: str, service: str | None) -> str:
    base = "Автотест: заявка по категории"
    service_part = f", услуга: {service}" if service else ""
    # Гарантируем >= 10 символов
    return f"{base} {category}{service_part}. Подробности: минимально валидное описание."


def make_address() -> str:
    return "г. Москва, ул. Тестовая, д. 1, кв. 1"


async def ensure_test_user() -> Tuple[int, User]:
    """Создаёт или возвращает тестового пользователя. Возвращает (db_user_id, User)."""
    async for db in get_db():
        result = await db.execute(select(User).where(User.telegram_id == TEST_TELEGRAM_ID))
        user: User | None = result.scalar_one_or_none()
        if user is None:
            user = User(
                telegram_id=TEST_TELEGRAM_ID,
                username=TEST_USERNAME,
                first_name=TEST_FIRST_NAME,
                last_name=TEST_LAST_NAME,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user.id, user


async def create_all_requests() -> None:
    # Инициализация БД (на случай, если таблицы ещё не созданы)
    await init_db()

    user_id, user = await ensure_test_user()

    catalog = build_catalog()
    formats = build_formats()
    times = build_times()

    total = 0
    succeeded = 0
    failed = 0

    # Отдельная категория: "своими словами"
    free_text_category = "✍️ Описать запрос своими словами"

    async for db in get_db():
        service_layer = RequestService(db)

        # 1) Все стандартные категории с услугами
        for category, services in catalog.items():
            for service in services:
                for fmt in formats:
                    for t in times:
                        total += 1
                        try:
                            payload = RequestCreate(
                                category=category,
                                service=service,
                                description=make_description(category, service),
                                work_format=fmt,
                                address=make_address()
                                if fmt in (WorkFormat.HOME_VISIT, WorkFormat.PICKUP)
                                else None,
                                preferred_time=t,
                            )
                            created: Request = await service_layer.create_request(user_id, payload)
                            # Сразу помечаем выполненной, чтобы не упереться в лимит активных заявок
                            await service_layer.update_request_status(
                                created.request_id,
                                RequestStatusUpdate(status=RequestStatus.COMPLETED),
                                changed_by=user_id,
                            )
                            print(
                                f"[OK] {created.request_id} | {category} | {service} | {fmt.value} | {t.value}"
                            )
                            succeeded += 1
                        except Exception as e:
                            print(
                                f"[FAIL] {category} | {service} | {fmt.value} | {t.value} -> {e}"
                            )
                            failed += 1

        # 2) Категория без выбора услуги (свободный текст)
        for fmt in formats:
            for t in times:
                total += 1
                try:
                    payload = RequestCreate(
                        category=free_text_category,
                        service="✍️ Свой вариант",
                        description=make_description(free_text_category, "✍️ Свой вариант"),
                        work_format=fmt,
                        address=make_address()
                        if fmt in (WorkFormat.HOME_VISIT, WorkFormat.PICKUP)
                        else None,
                        preferred_time=t,
                    )
                    created = await service_layer.create_request(user_id, payload)
                    await service_layer.update_request_status(
                        created.request_id,
                        RequestStatusUpdate(status=RequestStatus.COMPLETED),
                        changed_by=user_id,
                    )
                    print(
                        f"[OK] {created.request_id} | {free_text_category} | ✍️ Свой вариант | {fmt.value} | {t.value}"
                    )
                    succeeded += 1
                except Exception as e:
                    print(
                        f"[FAIL] {free_text_category} | ✍️ Свой вариант | {fmt.value} | {t.value} -> {e}"
                    )
                    failed += 1

    print("\n================ SUMMARY ================")
    print(f"Total:     {total}")
    print(f"Succeeded: {succeeded}")
    print(f"Failed:    {failed}")
    print("========================================\n")


if __name__ == "__main__":
    asyncio.run(create_all_requests())


