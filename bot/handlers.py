import os
from dotenv import load_dotenv
from datetime import datetime
import uuid
import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram import ReplyKeyboardMarkup
from .keyboards import *

# Загружаем переменные окружения
load_dotenv()

# Получаем переменные из .env
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
REQUESTS_GROUP_ID = int(os.getenv("REQUESTS_GROUP_ID", "-1004796553922"))
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "123456789").split(",")]

# Временное хранилище заявок
user_requests = {}
request_counter = 1

# Добавляем импорт для работы с API
import httpx
import json

# URL API (должен быть настроен в .env)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================
async def safe_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode=None, reply_markup=None):
    """Безопасная отправка сообщения с автоматической обработкой ошибок Markdown"""
    try:
        await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        if "Can't parse entities" in str(e) or "parse entities" in str(e):
            await update.message.reply_text(text, reply_markup=reply_markup)
            print(f"Предупреждение: Ошибка Markdown в сообщении: {e}")
        else:
            print(f"Ошибка отправки сообщения: {e}")
            raise e

def escape_markdown(text):
    """Экранирует специальные символы Markdown"""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))

def get_safe_value(value, default="Не указано"):
    """Безопасно получает значение, заменяя пустые значения на default"""
    if value is None or str(value).strip() == "":
        return default
    return value

async def create_request_via_api(request_data: dict, user_id: int) -> dict:
    """Создание заявки через API"""
    try:
        # Преобразуем данные в формат API
        api_request = {
            "category": request_data["category"],
            "service": request_data.get("service", "Не указано"),
            "description": request_data.get("description", "Описание не предоставлено"),
            "work_format": map_work_format_to_enum(request_data.get("work_format", "💻 Удаленная помощь")),
            "address": request_data.get("address"),
            "preferred_time": map_time_to_enum(request_data.get("preferred_time", "⏰ Любое время"))
        }
        
        # Убираем None значения
        api_request = {k: v for k, v in api_request.items() if v is not None}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/requests/",
                params={"user_id": user_id},
                json=api_request,
                timeout=30.0
            )
            
            if response.status_code == 201:
                return response.json()
            else:
                error_detail = response.json().get("detail", "Неизвестная ошибка")
                raise ValueError(f"Ошибка API: {error_detail}")
                
    except Exception as e:
        print(f"Ошибка создания заявки через API: {e}")
        raise e

def map_work_format_to_enum(work_format: str) -> str:
    """Преобразование формата работы в enum для API"""
    mapping = {
        "🏠 Выезд на дом": "home_visit",
        "💻 Удаленная помощь": "remote", 
        "🚚 Забрать технику": "pickup",
        "🏢 В офис": "office"
    }
    return mapping.get(work_format, "remote")

def map_time_to_enum(time_pref: str) -> str:
    """Преобразование времени в enum для API"""
    mapping = {
        "🌅 Утро (9:00-12:00)": "morning",
        "☀️ День (12:00-18:00)": "day",
        "🌆 Вечер (18:00-22:00)": "evening",
        "⏰ Любое время": "any"
    }
    return mapping.get(time_pref, "any")

async def send_request_to_channel(request: dict, context: ContextTypes.DEFAULT_TYPE):
    """Отправка заявки в группу fixfix"""
    try:
        # Экранируем все поля, которые могут содержать специальные символы
        request_id = escape_markdown(get_safe_value(request['request_id']))
        username = escape_markdown(get_safe_value(request['username'], "Без имени"))
        category = escape_markdown(get_safe_value(request['category']))
        service = escape_markdown(get_safe_value(request.get('service')))
        description = escape_markdown(get_safe_value(request.get('description')))
        work_format = escape_markdown(get_safe_value(request.get('work_format')))
        address = escape_markdown(get_safe_value(request.get('address'), "Не требуется"))
        preferred_time = escape_markdown(get_safe_value(request.get('preferred_time'), "Любое"))
        phone = escape_markdown(get_safe_value(request.get('phone')))
        created_at = escape_markdown(get_safe_value(request['created_at'])[:16])
        status = escape_markdown(get_safe_value(request['status']))
        
        channel_text = (
            f"🆕 *Новая заявка #{request_id}*\n\n"
            f"👤 *Клиент:* @{username}\n"
            f"📝 *Категория:* {category}\n"
            f"🔧 *Услуга:* {service}\n"
            f"📄 *Описание:* {description}\n\n"
            f"📍 *Детали заказа:*\n"
            f"• Формат работы: {work_format}\n"
            f"• Адрес: {address}\n"
            f"• Удобное время: {preferred_time}\n"
            f"• Телефон: {phone}\n\n"
            f"📅 *Создана:* {created_at}\n"
            f"📊 *Статус:* {status}"
        )
        
        # Создаем клавиатуру для менеджеров
        keyboard = [
            ["✅ Принять в работу", "❌ Отклонить"],
            ["📞 Позвонить клиенту", "💬 Написать клиенту"],
            ["📝 Добавить комментарий"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Проверяем ID группы
        if REQUESTS_GROUP_ID == 0 or REQUESTS_GROUP_ID is None:
            raise ValueError("ID группы не указан в переменной окружения REQUESTS_GROUP_ID")
        
        print(f"Попытка отправить заявку в группу с ID: {REQUESTS_GROUP_ID}")
        
        # Отправляем сообщение в группу
        await context.bot.send_message(
            chat_id=REQUESTS_GROUP_ID,
            text=channel_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        print(f"✅ Заявка #{request['request_id']} успешно отправлена в группу {REQUESTS_GROUP_ID}")
        
    except Exception as e:
        error_message = f"❌ Ошибка отправки заявки #{request['request_id']}: {str(e)}"
        print(error_message)
        
        # Дополнительная информация для отладки
        if "Chat not found" in str(e):
            error_message += f"\n\n🔍 *Возможные причины:*\n"
            error_message += f"1. Неправильный ID группы: `{REQUESTS_GROUP_ID}`\n"
            error_message += f"2. Бот не добавлен в группу\n"
            error_message += f"3. Группа приватная и бот не имеет доступа\n"
            error_message += f"4. Группа была удалена или заблокирована\n\n"
            error_message += f"💡 *Решение:*\n"
            error_message += f"1. Проверьте ID группы командой /chatid в нужной группе\n"
            error_message += f"2. Убедитесь, что бот добавлен в группу\n"
            error_message += f"3. Если группа приватная, сделайте ее публичной или добавьте бота как администратора"
        
        # Отправляем уведомление администраторам
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=error_message,
                    parse_mode="Markdown"
                )
            except Exception as admin_error:
                print(f"Не удалось отправить уведомление админу {admin_id}: {admin_error}")
# Обработчик для получения chat_id
async def get_chat_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить ID текущего чата"""
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Личный чат"
    await safe_send_message(update, context, 
        f"📋 *Информация о чате:*\n\n"
        f"🆔 *ID:* `{chat_id}`\n"
        f"📝 *Название:* {chat_title}\n"
        f"👤 *Тип:* {update.effective_chat.type}",
        parse_mode="Markdown"
    )

# ==============================================================================
# СЕРВИСНЫЕ КОМАНДЫ АДМИНА
# ==============================================================================
async def check_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сервисная проверка /check: доступна только администраторам.
    Вызывает API endpoint /requests/check, который создаёт тестовую заявку.
    """
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await safe_send_message(update, context, "❌ У вас нет прав для этой команды.")
        return

    try:
        # Ожидаем, что API_BASE_URL указывает на корень API (в проде: http://app:8000/api/v1)
        url = f"{API_BASE_URL}/requests/check"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, params={"admin_id": user_id})
            if resp.status_code == 200:
                data = resp.json()
                await safe_send_message(
                    update,
                    context,
                    (
                        "✅ Проверка выполнена успешно\n"
                        f"ID: {data.get('request_id')}\n"
                        f"Категория: {data.get('category')}\n"
                        f"Услуга: {data.get('service')}"
                    )
                )
            else:
                try:
                    detail = resp.json().get("detail")
                except Exception:
                    detail = resp.text
                await safe_send_message(
                    update,
                    context,
                    f"❌ Ошибка проверки: {detail} (HTTP {resp.status_code})"
                )
    except Exception as e:
        await safe_send_message(update, context, f"❌ Ошибка запроса: {e}")

# ==============================================================================
# ОСНОВНЫЕ ОБРАБОТЧИКИ
# ==============================================================================
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Старт бота"""
    text = (
        "🔧 *fixfix* — быстрый ремонт ПК!\n\n"
        "Выберите нужную услугу:"
    )
    await safe_send_message(update, context, text, parse_mode="Markdown", reply_markup=main_menu())

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора категории"""
    category = update.message.text
    user_id = update.effective_user.id
    
    # Инициализируем заявку только для категорий, требующих создания заявки
    if category in ["🔴 Компьютер глючит/не работает", "⚙️ Установить/Настроить программу", 
                   "📷 Подключить/Настроить устройство", "🚀 Хочу апгрейд", 
                   "🌐 «Слабый Wi-Fi / новый роутер»", "🔒 VPN и Защита данных", 
                   "✍️ Описать запрос своими словами"]:
        
        global request_counter
        user_requests[user_id] = {
            "request_id": f"FX-{datetime.now().strftime('%Y%m%d')}-{request_counter:03d}",
            "user_id": user_id,
            "username": update.effective_user.username or update.effective_user.first_name,
            "category": category,
            "status": "новая",
            "created_at": datetime.now().isoformat()
        }
        request_counter += 1
    
    # Показываем соответствующее меню
    if "🔴 Компьютер глючит" in category:
        await safe_send_message(update, context, "🔍 Что именно происходит?", reply_markup=problems_menu())
    elif "⚙️ Установить" in category:
        await safe_send_message(update, context, "⚙️ Какую программу нужно установить?", reply_markup=setup_menu())
    elif "📷 Подключить" in category:
        await safe_send_message(update, context, "📷 Какое устройство нужно настроить?", reply_markup=device_setup_menu())
    elif "🚀 Хочу апгрейд" in category:
        await safe_send_message(update, context, "🚀 Что хотите улучшить?", reply_markup=upgrade_menu())
    elif "🌐 Wi-Fi" in category:
        await safe_send_message(update, context, "🌐 Какая помощь с Wi-Fi?", reply_markup=wifi_menu())
    elif "🔒 VPN" in category:
        await safe_send_message(update, context, "🔒 Какую услугу безопасности?", reply_markup=security_menu())
    elif "✍️ Описать запрос" in category:
        await safe_send_message(update, context, "✍️ Опишите вашу проблему:", reply_markup=custom_request_menu())
    # Кнопка "📋 Мои заявки" теперь обрабатывается отдельно в main.py

async def service_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора услуги"""
    service = update.message.text
    user_id = update.effective_user.id
    
    print(f"DEBUG: service_handler вызван для пользователя {user_id} с услугой: {service}")
    
    if user_id in user_requests:
        user_requests[user_id]["service"] = service
        
        # Специальные случаи
        if "🔧 Собрать ПК с нуля" in service:
            await safe_send_message(update, context, "🔧 Для каких целей собираем ПК?", reply_markup=pc_build_menu())
        elif "💻 Подбор комплектующих" in service:
            await safe_send_message(update, context, "💻 Какие компоненты подобрать?", reply_markup=pc_build_menu())
        elif "✍️ Свой вариант" in service:
            # Для "Свой вариант" сразу запрашиваем описание
            await safe_send_message(update, context, "✍️ Опишите проблему подробнее:", reply_markup=back_menu())
        else:
            await safe_send_message(update, context, "✍️ Опишите проблему подробнее:", reply_markup=back_menu())

async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик описания проблемы"""
    description = update.message.text
    user_id = update.effective_user.id
    
    print(f"DEBUG: description_handler вызван для пользователя {user_id} с описанием: {description}")
    
    if user_id in user_requests:
        # Ранняя валидация длины описания
        if len(description.strip()) < 10:
            await safe_send_message(
                update,
                context,
                "❌ Описание должно содержать минимум 10 символов.\n"
                "Пожалуйста, введите более подробное описание проблемы:",
                reply_markup=back_menu()
            )
            return
        user_requests[user_id]["description"] = description
        await safe_send_message(update, context, "📍 Как вам удобнее получить помощь?", reply_markup=work_format_menu())

async def work_format_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик формата работы"""
    work_format = update.message.text
    user_id = update.effective_user.id
    
    print(f"DEBUG: work_format_handler вызван для пользователя {user_id} с форматом: {work_format}")
    
    if user_id in user_requests:
        user_requests[user_id]["work_format"] = work_format
        
        # Если нужен адрес
        if "🏠 Выезд на дом" in work_format or "🚚 Забрать технику" in work_format:
            await safe_send_message(update, context, 
                "🏠 Укажите ваш адрес и удобное время:\n"
                "Пример: Проспект мира 188б корп2, кв 5, после 18:00",
                reply_markup=back_menu()
            )
        else:
            # Для форматов без выезда автоматически устанавливаем "Любое время"
            user_requests[user_id]["preferred_time"] = "⏰ Любое время"
            await safe_send_message(update, context, "📞 Оставьте номер для связи:", reply_markup=contact_menu())

async def time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора времени"""
    time_preference = update.message.text
    user_id = update.effective_user.id
    
    print(f"DEBUG: time_handler вызван для пользователя {user_id} с временем: {time_preference}")
    
    if user_id in user_requests:
        user_requests[user_id]["preferred_time"] = time_preference
        await safe_send_message(update, context, "📞 Оставьте номер для связи:", reply_markup=contact_menu())

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик контактов"""
    user_id = update.effective_user.id
    
    print(f"DEBUG: contact_handler вызван для пользователя {user_id}")
    print(f"DEBUG: Тип сообщения: {'контакт' if update.message.contact else 'текст'}")
    
    if update.message.contact:
        phone = update.message.contact.phone_number
        print(f"DEBUG: Получен контакт: {phone}")
    else:
        phone = update.message.text
        print(f"DEBUG: Получен текст: {phone}")
    
    if user_id in user_requests:
        user_requests[user_id]["phone"] = phone
        
        # Показываем подтверждение
        request = user_requests[user_id]
        confirm_text = (
            f"📋 *Подтвердите заявку:*\n\n"
            f"🆔 *Номер:* {request['request_id']}\n"
            f"📝 *Услуга:* {request['category']} → {request.get('service', '')}\n"
            f"📄 *Описание:* {request.get('description', '')}\n"
            f"📍 *Формат:* {request.get('work_format', '')}\n"
            f"🏠 *Адрес:* {request.get('address', 'Не требуется')}\n"
            f"⏰ *Время:* {request.get('preferred_time', 'Любое')}\n"
            f"📞 *Телефон:* {phone}"
        )
        
        await safe_send_message(update, context, confirm_text, parse_mode="Markdown", reply_markup=confirm_menu())

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения заявки"""
    user_id = update.effective_user.id
    action = update.message.text
    
    print(f"DEBUG: confirm_handler вызван для пользователя {user_id} с действием: {action}")
    
    if user_id not in user_requests:
        await safe_send_message(update, context, "❌ Ошибка: нет активной заявки", reply_markup=main_menu())
        return
    
    if action == "✅ Подтвердить заявку":
        request = user_requests[user_id]
        
        # Валидация обязательных полей
        required_fields = ['category', 'work_format', 'preferred_time', 'phone']
        missing_fields = []
        
        for field in required_fields:
            if field not in request or not request[field]:
                missing_fields.append(field)
        
        if missing_fields:
            await safe_send_message(update, context,
                f"❌ Не заполнены обязательные поля: {', '.join(missing_fields)}\n"
                "Пожалуйста, заполните все поля и попробуйте снова.",
                reply_markup=back_menu()
            )
            return
        
        # Проверяем минимальную длину описания
        if 'description' not in request or len(request.get('description', '').strip()) < 10:
            # Очистим некорректное описание, чтобы следующий ввод текста попал в обработчик описания
            if 'description' in request:
                del request['description']
            await safe_send_message(update, context,
                "❌ Описание должно содержать минимум 10 символов.\n"
                "Пожалуйста, введите более подробное описание проблемы:",
                reply_markup=back_menu()
            )
            return
        
        try:
            # Создаем заявку через API
            api_response = await create_request_via_api(request, user_id)
            
            # Обновляем локальные данные
            request.update(api_response)
            request["status"] = "подтверждена"
            request["updated_at"] = datetime.now().isoformat()
            
            # Отправляем в группу
            await send_request_to_channel(request, context)
            
            # Подтверждаем пользователю
            await safe_send_message(update, context,
                f"✅ Заявка #{request['request_id']} принята!\n\n"
                "Менеджер свяжется с вами в ближайшее время.\n"
                f"📞 Ваш телефон: {request.get('phone', 'Не указан')}",
                reply_markup=main_menu()
            )
            
            # Очищаем временные данные
            del user_requests[user_id]
            
        except ValueError as e:
            # Ошибка валидации API
            await safe_send_message(update, context,
                f"❌ Ошибка валидации данных: {str(e)}\n"
                "Пожалуйста, исправьте данные и попробуйте снова.",
                reply_markup=back_menu()
            )
            print(f"Ошибка валидации API: {e}")
            
        except Exception as e:
            # Общая ошибка
            await safe_send_message(update, context,
                "⚠️ Произошла ошибка при создании заявки.\n"
                "Пожалуйста, попробуйте позже или свяжитесь с поддержкой.",
                reply_markup=main_menu()
            )
            print(f"Ошибка при создании заявки: {e}")
    
    elif action == "🔄 Изменить данные":
        # Возвращаемся в главное меню для изменения данных
        await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())
    
    elif action == "❌ Отменить":
        # Удаляем заявку и возвращаемся в главное меню
        del user_requests[user_id]
        await safe_send_message(update, context, "❌ Заявка отменена", reply_markup=main_menu())

async def back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик 'Назад'"""
    user_id = update.effective_user.id
    
    print(f"DEBUG: back_handler вызван для пользователя {user_id}")
    
    if user_id not in user_requests:
        await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())
        return
    
    request = user_requests[user_id]
    
    # Этап 6: Введен номер -> возвращаемся к вводу номера
    if 'phone' in request:
        del request['phone']
        # Если был выбран формат работы с выездом/забором
        if 'preferred_time' in request:
            await safe_send_message(update, context, 
                "⏰ Теперь выберите удобное время:",
                reply_markup=time_menu()
            )
        elif 'address' in request:
            await safe_send_message(update, context, 
                "⏰ Теперь выберите удобное время:",
                reply_markup=time_menu()
            )
        else:
            await safe_send_message(update, context, 
                "📍 Как вам удобнее получить помощь?",
                reply_markup=work_format_menu()
            )
        return
    
    # Этап 5: Выбрано время -> возвращаемся к выбору времени
    if 'preferred_time' in request:
        del request['preferred_time']
        # Если был введен адрес
        if 'address' in request:
            await safe_send_message(update, context, 
                "🏠 Укажите адрес и удобное время:\n"
                "Пример: ул. Ленина 15, кв 5, после 18:00",
                reply_markup=back_menu()
            )
        else:
            await safe_send_message(update, context, 
                "📍 Как вам удобнее получить помощь?",
                reply_markup=work_format_menu()
            )
        return
    
    # Этап 4: Введен адрес -> возвращаемся к выбору формата работы
    if 'address' in request:
        del request['address']
        await safe_send_message(update, context, 
            "📍 Как вам удобнее получить помощь?",
            reply_markup=work_format_menu()
        )
        return
    
    # Этап 3: Выбран формат работы -> возвращаемся к вводу описания
    if 'work_format' in request:
        del request['work_format']
        await safe_send_message(update, context, 
            "✍️ Опишите проблему подробнее:",
            reply_markup=back_menu()
        )
        return
    
    # Этап 2: Введено описание -> возвращаемся к выбору услуги
    if 'description' in request:
        del request['description']
        category = request['category']
        if "🔴 Компьютер глючит" in category:
            await safe_send_message(update, context, "🔍 Что именно происходит?", reply_markup=problems_menu())
        elif "⚙️ Установить" in category:
            await safe_send_message(update, context, "⚙️ Какую программу нужно установить?", reply_markup=setup_menu())
        elif "📷 Подключить" in category:
            await safe_send_message(update, context, "📷 Какое устройство нужно настроить?", reply_markup=device_setup_menu())
        elif "🚀 Хочу апгрейд" in category:
            await safe_send_message(update, context, "🚀 Что хотите улучшить?", reply_markup=upgrade_menu())
        elif "🌐 Wi-Fi" in category:
            await safe_send_message(update, context, "🌐 Какая помощь с Wi-Fi?", reply_markup=wifi_menu())
        elif "🔒 VPN" in category:
            await safe_send_message(update, context, "🔒 Какую услугу безопасности?", reply_markup=security_menu())
        elif "✍️ Описать запрос" in category:
            await safe_send_message(update, context, "✍️ Опишите вашу проблему:", reply_markup=custom_request_menu())
        return
    
    # Этап 1: Выбрана услуга -> возвращаемся к выбору услуги в категории
    if 'service' in request:
        del request['service']
        category = request['category']
        if "🔴 Компьютер глючит" in category:
            await safe_send_message(update, context, "🔍 Что именно происходит?", reply_markup=problems_menu())
        elif "⚙️ Установить" in category:
            await safe_send_message(update, context, "⚙️ Какую программу нужно установить?", reply_markup=setup_menu())
        elif "📷 Подключить" in category:
            await safe_send_message(update, context, "📷 Какое устройство нужно настроить?", reply_markup=device_setup_menu())
        elif "🚀 Хочу апгрейд" in category:
            await safe_send_message(update, context, "🚀 Что хотите улучшить?", reply_markup=upgrade_menu())
        elif "🌐 Wi-Fi" in category:
            await safe_send_message(update, context, "🌐 Какая помощь с Wi-Fi?", reply_markup=wifi_menu())
        elif "🔒 VPN" in category:
            await safe_send_message(update, context, "🔒 Какую услугу безопасности?", reply_markup=security_menu())
        elif "✍️ Описать запрос" in category:
            await safe_send_message(update, context, "✍️ Опишите вашу проблему:", reply_markup=custom_request_menu())
        return
    
    # Этап 0: Только категория -> возвращаемся в главное меню
    if 'category' in request:
        del user_requests[user_id]
        await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())
        return
    
    # Если ничего нет - в главное меню
    await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())

# ==============================================================================
# ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ (ИСПРАВЛЕННЫЙ)
# ==============================================================================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    print(f"DEBUG: text_handler вызван для пользователя {user_id} с текстом: {text}")
    
    # Если нет активной заявки
    if user_id not in user_requests:
        await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())
        return
    
    request = user_requests[user_id]
    
    # Этап 1: Ввод описания услуги (после выбора услуги)
    if ('service' in request and 
        'description' not in request and
        '✍️ Свой вариант' not in request.get('service', '')):
        await description_handler(update, context)
        return
    
    # Этап 1.5: Обработка "Свой вариант" - сразу вводим описание
    if ('service' in request and 
        '✍️ Свой вариант' in request['service'] and
        'description' not in request):
        request['description'] = text
        await safe_send_message(update, context, 
            "📍 Как вам удобнее получить помощь?",
            reply_markup=work_format_menu()
        )
        return
    
    # Этап 2: Ввод адреса (для выезда/забора)
    if ('work_format' in request and 
        'address' not in request and
        ('🏠 Выезд на дом' in request['work_format'] or 
         '🚚 Забрать технику' in request['work_format'])):
        
        request['address'] = text
        await safe_send_message(update, context, 
            "⏰ Теперь выберите удобное время:",
            reply_markup=time_menu()
        )
        return
    
    # Этап 3: Ввод времени (после адреса)
    if ('address' in request and 
        'preferred_time' not in request and
        ('🏠 Выезд на дом' in request['work_format'] or 
         '🚚 Забрать технику' in request['work_format'])):
        
        request['preferred_time'] = text
        await safe_send_message(update, context, 
            "📞 Оставьте номер для связи:",
            reply_markup=contact_menu()
        )
        return
    
    # Этап 4: Ввод номера вручную
    if ('preferred_time' in request and 'phone' not in request) or \
       ('work_format' in request and 'phone' not in request and 
        '🏠 Выезд на дом' not in request['work_format'] and 
        '🚚 Забрать технику' not in request['work_format']):
        await contact_handler(update, context)
        return
    
    # Этап 3.5: Обработка "Мои требования" в меню сборки ПК
    if ('service' in request and 
        'description' not in request and
        ('🔧 Собрать ПК с нуля' in request['service'] or 
         '💻 Подбор комплектующих' in request['service']) and
        text == "📋 Мои требования"):
        
        await safe_send_message(update, context, 
            "✍️ Опишите ваши требования к ПК:",
            reply_markup=back_menu()
        )
        return
    
    # Этап 5: Свой вариант (для категории "Описать запрос своими словами")
    if ('category' in request and 
        '✍️ Описать запрос своими словами' in request['category'] and
        'service' not in request):
        request['service'] = "✍️ Свой вариант"
        request['description'] = text
        await safe_send_message(update, context, 
            "📍 Как вам удобнее получить помощь?",
            reply_markup=work_format_menu()
        )
        return
    
    # Если не распознано
    await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())

# ==============================================================================
# ТЕСТОВЫЕ И ВСПОМОГАТЕЛЬНЫЕ ОБРАБОТЧИКИ
# ==============================================================================
async def my_requests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для 'Мои заявки'"""
    user_id = update.effective_user.id
    text = update.message.text
    
    print(f"DEBUG: my_requests_handler вызван для пользователя {user_id} с текстом: {text}")
    
    # Обработка кнопок в меню "Мои заявки"
    if text == "📋 Активные заявки":
        # Логика показа активных заявок
        await safe_send_message(update, context, "Функция в разработке...", reply_markup=my_requests_menu())
        return
    elif text == "✅ Выполненные":
        # Логика показа выполненных заявок
        await safe_send_message(update, context, "Функция в разработке...", reply_markup=my_requests_menu())
        return
    elif text == "🔄 Создать новую заявку":
        await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())
        return
    elif text == "ℹ️ Помощь":
        await safe_send_message(update, context, "ℹ️ Справочная информация...", reply_markup=my_requests_menu())
        return
    elif text == "⬅️ Назад":
        await safe_send_message(update, context, "🔧 Главное меню:", reply_markup=main_menu())
        return
    
    # Здесь должна быть логика получения заявок пользователя из БД
    # Для примера используем временные данные
    user_requests_list = [req for req in user_requests.values() if req['user_id'] == user_id]
    
    if not user_requests_list:
        await safe_send_message(update, context, "У вас нет активных заявок", reply_markup=main_menu())
        return
    
    response = "📋 *Ваши заявки:*\n\n"
    for req in user_requests_list:
        response += (
            f"🆔 *Заявка #{req['request_id']}*\n"
            f"📝 {req['category']} → {req.get('service', '')}\n"
            f"📊 Статус: {req['status']}\n"
            f"📅 {req['created_at'][:10]}\n\n"
        )
    
    await safe_send_message(update, context, response, parse_mode="Markdown", reply_markup=my_requests_menu())

async def test_keyboards_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тест всех клавиатур"""
    keyboards_to_test = [
        ("Главное меню", main_menu()),
        ("Проблемы", problems_menu()),
        ("Настройки", setup_menu()),
        ("Устройства", device_setup_menu()),
        ("Апгрейд", upgrade_menu()),
        ("Сборка ПК", pc_build_menu()),
        ("Wi-Fi", wifi_menu()),
        ("Безопасность", security_menu()),
        ("Время", time_menu()),
        ("Контакты", contact_menu()),
        ("Подтверждение", confirm_menu()),
        ("Назад", back_menu())
    ]
    
    await safe_send_message(update, context, "🧪 Начинаю тестирование всех клавиатур...")
    
    for name, keyboard in keyboards_to_test:
        await safe_send_message(update, context, f"📋 {name}:", reply_markup=keyboard)
        await asyncio.sleep(2)
    
    await safe_send_message(update, context, "✅ Тестирование завершено!", reply_markup=remove_keyboard())

async def test_specific_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тест конкретной клавиатуры"""
    keyboard_name = context.args[0] if context.args else "main_menu"
    
    keyboards_dict = {
        "main": main_menu(),
        "problems": problems_menu(),
        "time": time_menu(),
        "contact": contact_menu(),
        "confirm": confirm_menu()
    }
    
    if keyboard_name in keyboards_dict:
        await safe_send_message(update, context,
            f"📋 Тест клавиатуры: {keyboard_name}",
            reply_markup=keyboards_dict[keyboard_name]
        )
    else:
        await safe_send_message(update, context,
            f"❌ Клавиатура '{keyboard_name}' не найдена\n"
            f"Доступные: {', '.join(keyboards_dict.keys())}"
        )

async def debug_state_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отладка текущего состояния пользователя"""
    user_id = update.effective_user.id
    
    if user_id in user_requests:
        state = user_requests[user_id]
        debug_text = (
            f"🔍 *Текущее состояние:*\n\n"
            f"🆔 ID: {state.get('request_id', 'Нет')}\n"
            f"📝 Категория: {state.get('category', 'Нет')}\n"
            f"🔧 Услуга: {state.get('service', 'Нет')}\n"
            f"📄 Описание: {state.get('description', 'Нет')}\n"
            f"📍 Формат: {state.get('work_format', 'Нет')}\n"
            f"🏠 Адрес: {state.get('address', 'Нет')}\n"
            f"⏰ Время: {state.get('preferred_time', 'Нет')}\n"
            f"📞 Телефон: {state.get('phone', 'Нет')}"
        )
        await safe_send_message(update, context, debug_text, parse_mode="Markdown")
    else:
        await safe_send_message(update, context, "❌ Нет активной заявки")

async def check_config_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка конфигурации бота"""
    config_info = (
        f"🔧 *Конфигурация бота:*\n\n"
        f"🤖 *Токен:* {'✅ Загружен' if TELEGRAM_TOKEN else '❌ Не загружен'}\n"
        f"👥 *ID группы:* `{REQUESTS_GROUP_ID}`\n"
        f"👨‍💼 *Админы:* {len(ADMIN_IDS)} шт.\n"
        f"📝 *Имя бота:* {os.getenv('BOT_NAME', 'fixfix_bot')}\n\n"
        f"🌐 *API URL:* {os.getenv('TELEGRAM_API_URL', 'https://api.telegram.org')}\n\n"
        f"💡 *Чтобы получить ID группы:*\n"
        f"1. Добавьте бота в нужную группу\n"
        f"2. Отправьте команду /chatid в этой группе"
    )
    
    await safe_send_message(update, context, config_info, parse_mode="Markdown")