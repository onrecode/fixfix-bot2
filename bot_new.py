"""
Обновленный Telegram бот для FixFix с интеграцией базы данных
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Импорты из нашего приложения
from app.config import settings
from app.database.connection import init_db, close_db, get_db
from app.services.request_service import RequestService
from app.database.models import User, Request, RequestStatus, WorkFormat, PreferredTime
from app.schemas.requests import RequestCreate

# Импорты существующих модулей
from bot.handlers import *
from bot.keyboards import *

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальное хранилище состояний пользователей
user_states = {}
user_requests = {}


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем или получаем пользователя в БД
    async for db in get_db():
        # Проверяем, существует ли пользователь
        result = await db.execute(
            select(User).where(User.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            # Создаем нового пользователя
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            logger.info(f"Создан новый пользователь: {user.id}")
        
        # Сбрасываем состояние пользователя
        user_states[user.id] = "main_menu"
        user_requests[user.id] = {}
        
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            "🔧 Добро пожаловать в сервис по ремонту ПК!\n\n"
            "Выберите нужную вам услугу:"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=main_menu()
        )


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора категории"""
    user_id = update.effective_user.id
    category = update.message.text
    
    # Сохраняем категорию
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['category'] = category
    user_states[user_id] = "service_selection"
    
    # Определяем соответствующее меню услуг
    if "глючит" in category.lower():
        await update.message.reply_text(
            "Выберите конкретную проблему:",
            reply_markup=problems_menu()
        )
    elif "установить" in category.lower() or "настроить программу" in category.lower():
        await update.message.reply_text(
            "Выберите услугу:",
            reply_markup=setup_menu()
        )
    elif "устройство" in category.lower():
        await update.message.reply_text(
            "Выберите устройство для настройки:",
            reply_markup=device_setup_menu()
        )
    elif "апгрейд" in category.lower():
        await update.message.reply_text(
            "Выберите тип апгрейда:",
            reply_markup=upgrade_menu()
        )
    elif "wi-fi" in category.lower() or "роутер" in category.lower():
        await update.message.reply_text(
            "Выберите услугу по Wi-Fi:",
            reply_markup=wifi_menu()
        )
    elif "vpn" in category.lower() or "защита" in category.lower():
        await update.message.reply_text(
            "Выберите услугу по безопасности:",
            reply_markup=security_menu()
        )
    else:
        # Для "своими словами"
        user_states[user_id] = "description_input"
        await update.message.reply_text(
            "Опишите вашу проблему своими словами (минимум 10 символов):",
            reply_markup=custom_request_menu()
        )


async def service_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора услуги"""
    user_id = update.effective_user.id
    service = update.message.text
    
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['service'] = service
    
    # Если выбрана услуга, переходим к описанию
    if service != "✍️ Свой вариант":
        user_states[user_id] = "description_input"
        await update.message.reply_text(
            "Опишите вашу проблему подробнее (минимум 10 символов):",
            reply_markup=custom_request_menu()
        )
    else:
        user_states[user_id] = "description_input"
        await update.message.reply_text(
            "Опишите вашу проблему своими словами (минимум 10 символов):",
            reply_markup=custom_request_menu()
        )


async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода описания"""
    user_id = update.effective_user.id
    description = update.message.text
    
    # Валидация описания
    if len(description.strip()) < 10:
        await update.message.reply_text(
            "❌ Описание должно содержать минимум 10 символов. Попробуйте еще раз:",
            reply_markup=custom_request_menu()
        )
        return
    
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['description'] = description
    user_states[user_id] = "work_format_selection"
    
    await update.message.reply_text(
        "Выберите формат работы:",
        reply_markup=work_format_menu()
    )


async def work_format_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора формата работы"""
    user_id = update.effective_user.id
    work_format_text = update.message.text
    
    # Маппинг текста на enum
    work_format_mapping = {
        "🏠 Выезд на дом": WorkFormat.HOME_VISIT,
        "💻 Удаленная помощь": WorkFormat.REMOTE,
        "🚚 Забрать технику": WorkFormat.PICKUP,
        "🏢 В офис": WorkFormat.OFFICE
    }
    
    work_format = work_format_mapping.get(work_format_text)
    if not work_format:
        await update.message.reply_text(
            "❌ Неверный формат работы. Выберите из списка:",
            reply_markup=work_format_menu()
        )
        return
    
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['work_format'] = work_format
    user_states[user_id] = "time_selection"
    
    await update.message.reply_text(
        "Выберите удобное время:",
        reply_markup=time_menu()
    )


async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора времени"""
    user_id = update.effective_user.id
    time_text = update.message.text
    
    # Маппинг текста на enum
    time_mapping = {
        "🌅 Утро (9:00-12:00)": PreferredTime.MORNING,
        "☀️ День (12:00-18:00)": PreferredTime.DAY,
        "🌆 Вечер (18:00-21:00)": PreferredTime.EVENING,
        "⏰ Любое время": PreferredTime.ANY
    }
    
    preferred_time = time_mapping.get(time_text)
    if not preferred_time:
        await update.message.reply_text(
            "❌ Неверное время. Выберите из списка:",
            reply_markup=time_menu()
        )
        return
    
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['preferred_time'] = preferred_time
    user_states[user_id] = "contact_selection"
    
    await update.message.reply_text(
        "Для связи нам нужен ваш номер телефона:",
        reply_markup=contact_menu()
    )


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения контакта"""
    user_id = update.effective_user.id
    
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        # Если пользователь не поделился контактом, просим ввести вручную
        user_states[user_id] = "phone_input"
        await update.message.reply_text(
            "Пожалуйста, введите ваш номер телефона в формате +7XXXXXXXXXX:",
            reply_markup=back_menu()
        )
        return
    
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['phone'] = phone
    user_states[user_id] = "address_input"
    
    # Проверяем, нужен ли адрес
    work_format = user_requests[user_id].get('work_format')
    if work_format in [WorkFormat.HOME_VISIT, WorkFormat.PICKUP]:
        await update.message.reply_text(
            "Введите адрес для выезда:",
            reply_markup=back_menu()
        )
    else:
        # Адрес не нужен, переходим к подтверждению
        await show_confirmation(update, context)


async def phone_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ручного ввода телефона"""
    user_id = update.effective_user.id
    phone = update.message.text
    
    # Простая валидация телефона
    if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
        await update.message.reply_text(
            "❌ Неверный формат номера. Введите номер в формате +7XXXXXXXXXX:",
            reply_markup=back_menu()
        )
        return
    
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['phone'] = phone
    user_states[user_id] = "address_input"
    
    # Проверяем, нужен ли адрес
    work_format = user_requests[user_id].get('work_format')
    if work_format in [WorkFormat.HOME_VISIT, WorkFormat.PICKUP]:
        await update.message.reply_text(
            "Введите адрес для выезда:",
            reply_markup=back_menu()
        )
    else:
        # Адрес не нужен, переходим к подтверждению
        await show_confirmation(update, context)


async def address_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода адреса"""
    user_id = update.effective_user.id
    address = update.message.text
    
    # Валидация адреса
    if len(address.strip()) < 5:
        await update.message.reply_text(
            "❌ Адрес должен содержать минимум 5 символов. Попробуйте еще раз:",
            reply_markup=back_menu()
        )
        return
    
    if user_id not in user_requests:
        user_requests[user_id] = {}
    
    user_requests[user_id]['address'] = address
    
    # Переходим к подтверждению
    await show_confirmation(update, context)


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать подтверждение заявки"""
    user_id = update.effective_user.id
    
    if user_id not in user_requests:
        await update.message.reply_text(
            "❌ Ошибка: данные заявки не найдены. Начните заново.",
            reply_markup=main_menu()
        )
        return
    
    request_data = user_requests[user_id]
    
    # Формируем текст подтверждения
    confirmation_text = (
        "📋 *Подтвердите данные заявки:*\n\n"
        f"🔧 *Категория:* {request_data.get('category', 'Не указано')}\n"
        f"⚙️ *Услуга:* {request_data.get('service', 'Не указано')}\n"
        f"📝 *Описание:* {request_data.get('description', 'Не указано')}\n"
        f"📍 *Формат работы:* {request_data.get('work_format', 'Не указано')}\n"
        f"🏠 *Адрес:* {request_data.get('address', 'Не требуется')}\n"
        f"⏰ *Время:* {request_data.get('preferred_time', 'Не указано')}\n"
        f"📞 *Телефон:* {request_data.get('phone', 'Не указано')}\n\n"
        "Все верно?"
    )
    
    user_states[user_id] = "confirmation"
    
    await update.message.reply_text(
        confirmation_text,
        parse_mode="Markdown",
        reply_markup=confirm_menu()
    )


async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения заявки"""
    user_id = update.effective_user.id
    action = update.message.text
    
    if action == "✅ Подтвердить заявку":
        # Создаем заявку в БД
        try:
            async for db in get_db():
                # Получаем пользователя
                result = await db.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                db_user = result.scalar_one_or_none()
                
                if not db_user:
                    await update.message.reply_text(
                        "❌ Ошибка: пользователь не найден. Начните заново.",
                        reply_markup=main_menu()
                    )
                    return
                
                # Создаем заявку
                request_service = RequestService(db)
                request_create = RequestCreate(
                    category=user_requests[user_id]['category'],
                    service=user_requests[user_id].get('service'),
                    description=user_requests[user_id].get('description'),
                    work_format=user_requests[user_id]['work_format'],
                    address=user_requests[user_id].get('address'),
                    preferred_time=user_requests[user_id]['preferred_time']
                )
                
                db_request = await request_service.create_request(db_user.id, request_create)
                
                # Отправляем в группу
                await send_request_to_channel(db_request, context)
                
                # Очищаем состояние пользователя
                user_states[user_id] = "main_menu"
                user_requests[user_id] = {}
                
                await update.message.reply_text(
                    f"✅ Заявка #{db_request.request_id} успешно создана!\n\n"
                    "Наш менеджер свяжется с вами в ближайшее время.",
                    reply_markup=main_menu()
                )
                
        except Exception as e:
            logger.error(f"Ошибка создания заявки: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при создании заявки. Попробуйте позже.",
                reply_markup=main_menu()
            )
    
    elif action == "🔄 Изменить данные":
        # Возвращаемся к выбору категории
        user_states[user_id] = "main_menu"
        user_requests[user_id] = {}
        await update.message.reply_text(
            "Выберите категорию услуги:",
            reply_markup=main_menu()
        )
    
    elif action == "❌ Отменить":
        # Отменяем заявку
        user_states[user_id] = "main_menu"
        user_requests[user_id] = {}
        await update.message.reply_text(
            "Заявка отменена. Выберите категорию услуги:",
            reply_markup=main_menu()
        )


async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки 'Назад'"""
    user_id = update.effective_user.id
    
    if user_id not in user_states:
        user_states[user_id] = "main_menu"
    
    current_state = user_states[user_id]
    
    # Логика возврата по состояниям
    if current_state == "service_selection":
        user_states[user_id] = "main_menu"
        await update.message.reply_text(
            "Выберите категорию услуги:",
            reply_markup=main_menu()
        )
    elif current_state == "description_input":
        user_states[user_id] = "service_selection"
        # Возвращаемся к выбору услуги
        category = user_requests.get(user_id, {}).get('category', '')
        if "глючит" in category.lower():
            await update.message.reply_text(
                "Выберите конкретную проблему:",
                reply_markup=problems_menu()
            )
        elif "установить" in category.lower():
            await update.message.reply_text(
                "Выберите услугу:",
                reply_markup=setup_menu()
            )
        # ... и так далее для других категорий
    elif current_state == "work_format_selection":
        user_states[user_id] = "description_input"
        await update.message.reply_text(
            "Опишите вашу проблему подробнее:",
            reply_markup=custom_request_menu()
        )
    elif current_state == "time_selection":
        user_states[user_id] = "work_format_selection"
        await update.message.reply_text(
            "Выберите формат работы:",
            reply_markup=work_format_menu()
        )
    elif current_state == "contact_selection":
        user_states[user_id] = "time_selection"
        await update.message.reply_text(
            "Выберите удобное время:",
            reply_markup=time_menu()
        )
    elif current_state == "address_input":
        user_states[user_id] = "contact_selection"
        await update.message.reply_text(
            "Для связи нам нужен ваш номер телефона:",
            reply_markup=contact_menu()
        )
    else:
        # По умолчанию возвращаемся в главное меню
        user_states[user_id] = "main_menu"
        await update.message.reply_text(
            "Выберите категорию услуги:",
            reply_markup=main_menu()
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    
    if user_id not in user_states:
        user_states[user_id] = "main_menu"
        await update.message.reply_text(
            "Выберите категорию услуги:",
            reply_markup=main_menu()
        )
        return
    
    current_state = user_states[user_id]
    
    # Обработка в зависимости от состояния
    if current_state == "description_input":
        await description_handler(update, context)
    elif current_state == "phone_input":
        await phone_input_handler(update, context)
    elif current_state == "address_input":
        await address_input_handler(update, context)
    else:
        # Неизвестное состояние
        await update.message.reply_text(
            "Выберите действие из меню:",
            reply_markup=main_menu()
        )


async def my_requests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик просмотра заявок пользователя"""
    user_id = update.effective_user.id
    
    try:
        async for db in get_db():
            # Получаем пользователя
            result = await db.execute(
                select(User).where(User.telegram_id == user_id)
            )
            db_user = result.scalar_one_or_none()
            
            if not db_user:
                await update.message.reply_text(
                    "❌ Пользователь не найден.",
                    reply_markup=main_menu()
                )
                return
            
            # Получаем заявки пользователя
            request_service = RequestService(db)
            requests, total = await request_service.get_user_requests(db_user.id)
            
            if not requests:
                await update.message.reply_text(
                    "📋 У вас пока нет заявок.\n\n"
                    "Создайте первую заявку, выбрав услугу из главного меню!",
                    reply_markup=my_requests_menu()
                )
                return
            
            # Показываем заявки
            response_text = f"📋 Ваши заявки (всего: {total}):\n\n"
            
            for req in requests[:5]:  # Показываем первые 5
                status_emoji = {
                    RequestStatus.NEW: "🆕",
                    RequestStatus.IN_PROGRESS: "🔄",
                    RequestStatus.COMPLETED: "✅",
                    RequestStatus.CANCELLED: "❌",
                    RequestStatus.REJECTED: "🚫"
                }
                
                response_text += (
                    f"{status_emoji.get(req.status, '📋')} "
                    f"*Заявка #{req.request_id}*\n"
                    f"📝 {req.category}\n"
                    f"📊 Статус: {req.status.value}\n"
                    f"📅 Создана: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                )
            
            if total > 5:
                response_text += f"... и еще {total - 5} заявок"
            
            await update.message.reply_text(
                response_text,
                parse_mode="Markdown",
                reply_markup=my_requests_menu()
            )
            
    except Exception as e:
        logger.error(f"Ошибка получения заявок: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при получении заявок. Попробуйте позже.",
            reply_markup=main_menu()
        )


async def send_request_to_channel(request: Request, context: ContextTypes.DEFAULT_TYPE):
    """Отправка заявки в группу"""
    try:
        # Формируем текст для группы
        channel_text = (
            f"🆕 *Новая заявка #{request.request_id}*\n\n"
            f"👤 *Клиент:* ID {request.user_id}\n"
            f"📝 *Категория:* {request.category}\n"
            f"🔧 *Услуга:* {request.service or 'Не указано'}\n"
            f"📄 *Описание:* {request.description or 'Не указано'}\n\n"
            f"📍 *Детали заказа:*\n"
            f"• Формат работы: {request.work_format.value}\n"
            f"• Адрес: {request.address or 'Не требуется'}\n"
            f"• Удобное время: {request.preferred_time.value}\n\n"
            f"📅 *Создана:* {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📊 *Статус:* {request.status.value}"
        )
        
        # Создаем клавиатуру для менеджеров
        keyboard = [
            ["✅ Принять в работу", "❌ Отклонить"],
            ["📞 Позвонить клиенту", "💬 Написать клиенту"],
            ["📝 Добавить комментарий"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Отправляем в группу
        await context.bot.send_message(
            chat_id=settings.telegram.requests_group_id,
            text=channel_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        logger.info(f"Заявка {request.request_id} отправлена в группу")
        
    except Exception as e:
        logger.error(f"Ошибка отправки заявки в группу: {e}")


async def main():
    """Основная функция запуска бота"""
    # Инициализация базы данных
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return
    
    # Получаем токен
    token = settings.telegram.token
    if not token:
        logger.error("Токен не найден!")
        return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("myrequests", my_requests_handler))
    
    # Обработчики главного меню
    application.add_handler(MessageHandler(filters.Regex(r'^🔴 Компьютер глючит/не работает$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^⚙️ Установить/Настроить программу$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^📷 Подключить/Настроить устройство$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^🚀 Хочу апгрейд$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^🌐 «Слабый Wi-Fi / новый роутер»$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^🔒 VPN и Защита данных$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^✍️ Описать запрос своими словами$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^📋 Мои заявки$'), my_requests_handler))
    
    # Обработчики услуг
    application.add_handler(MessageHandler(filters.Regex(r'^(💻 Тормозит/Не включается|🔧 Выскакивают ошибки|🦠 Вирусы и реклама|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📦 Установить программу|🌐 Настроить интернет|🖨️ Подключить устройства|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(🖨️ Настроить принтер/сканер|🎮 Настроить приставку|🖱️ Настроить мышь/клавиатуру|📱 Подключить телефон|📺 Подключить телевизор|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(💾 Увеличить оперативную память|🔧 Заменить процессор|💿 Установить SSD диск|🎮 Установить видеокарту|🖥️ Заменить блок питания|❄️ Улучшить охлаждение|🔧 Собрать ПК с нуля|💻 Подбор комплектующих|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📶 Настроить Wi-Fi роутер|🌐 Усилить сигнал|🔐 Установить пароль|📡 Новый роутер|📱 Подключить устройства|✍️ Свой вариант)$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(🔐 Настроить VPN|🛡️ Проверка на вирусы|💾 Восстановление данных|🔒 Шифрование|🔑 Парольная защита|✍️ Свой вариант)$'), category_handler))
    
    # Обработчики формата работы
    application.add_handler(MessageHandler(filters.Regex(r'^(🏠 Выезд на дом|💻 Удаленная помощь|🚚 Забрать технику|🏢 В офис)$'), work_format_handler))
    
    # Обработчики времени
    application.add_handler(MessageHandler(filters.Regex(r'^(🌅 Утро \(9:00-12:00\)|☀️ День \(12:00-18:00\)|🌆 Вечер \(18:00-21:00\)|⏰ Любое время)$'), time_handler))
    
    # Обработчики контактов
    application.add_handler(MessageHandler(filters.Regex(r'^📞 Отправить номер$'), contact_handler))
    
    # Обработчик подтверждения
    application.add_handler(MessageHandler(filters.Regex(r'^(✅ Подтвердить заявку|🔄 Изменить данные|❌ Отменить)$'), confirm_handler))
    
    # Обработчик кнопки "Назад"
    application.add_handler(MessageHandler(filters.Regex(r'^⬅️ Назад$'), back_handler))
    
    # Обработчик текстовых сообщений (должен быть последним)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Запускаем бота
    logger.info("Бот запущен")
    await application.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        # Закрываем соединения с БД
        asyncio.run(close_db())
