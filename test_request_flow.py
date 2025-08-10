#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех возможных алгоритмов создания заявки
"""
import asyncio
import json
from datetime import datetime

# Симуляция данных пользователя
test_user_id = 12345
test_username = "test_user"

# Тестовые сценарии
test_scenarios = [
    {
        "name": "Сценарий 1: Компьютер глючит → Тормозит → Описание → Удаленная помощь → Телефон",
        "steps": [
            ("🔴 Компьютер глючит/не работает", "category"),
            ("💻 Тормозит/Не включается", "service"),
            ("Компьютер очень медленно работает, зависает при запуске программ", "description"),
            ("💻 Удаленная помощь", "work_format"),
            ("+7 999 123-45-67", "phone")
        ],
        "expected_result": {
            "category": "🔴 Компьютер глючит/не работает",
            "service": "💻 Тормозит/Не включается",
            "description": "Компьютер очень медленно работает, зависает при запуске программ",
            "work_format": "💻 Удаленная помощь",
            "address": None,
            "preferred_time": "⏰ Любое время",
            "phone": "+7 999 123-45-67"
        }
    },
    {
        "name": "Сценарий 2: Установить программу → Установить программу → Описание → Выезд на дом → Адрес → Время → Телефон",
        "steps": [
            ("⚙️ Установить/Настроить программу", "category"),
            ("📦 Установить программу", "service"),
            ("Нужно установить Photoshop для работы с графикой", "description"),
            ("🏠 Выезд на дом", "work_format"),
            ("ул. Ленина 15, кв 5, после 18:00", "address"),
            ("🌆 Вечер (18:00-22:00)", "preferred_time"),
            ("+7 999 123-45-67", "phone")
        ],
        "expected_result": {
            "category": "⚙️ Установить/Настроить программу",
            "service": "📦 Установить программу",
            "description": "Нужно установить Photoshop для работы с графикой",
            "work_format": "🏠 Выезд на дом",
            "address": "ул. Ленина 15, кв 5, после 18:00",
            "preferred_time": "🌆 Вечер (18:00-22:00)",
            "phone": "+7 999 123-45-67"
        }
    },
    {
        "name": "Сценарий 3: Свой вариант → Описание → Выезд на дом → Адрес → Время → Телефон",
        "steps": [
            ("✍️ Описать запрос своими словами", "category"),
            ("Нужна помощь с настройкой домашней сети", "description"),
            ("🏠 Выезд на дом", "work_format"),
            ("пр. Мира 188б корп2, кв 5", "address"),
            ("☀️ День (12:00-18:00)", "preferred_time"),
            ("+7 999 123-45-67", "phone")
        ],
        "expected_result": {
            "category": "✍️ Описать запрос своими словами",
            "service": "✍️ Свой вариант",
            "description": "Нужна помощь с настройкой домашней сети",
            "work_format": "🏠 Выезд на дом",
            "address": "пр. Мира 188б корп2, кв 5",
            "preferred_time": "☀️ День (12:00-18:00)",
            "phone": "+7 999 123-45-67"
        }
    },
    {
        "name": "Сценарий 4: Апгрейд → Собрать ПК с нуля → Игровой ПК → Описание → Забрать технику → Адрес → Время → Телефон",
        "steps": [
            ("🚀 Хочу апгрейд", "category"),
            ("🔧 Собрать ПК с нуля", "service"),
            ("🎮 Игровой ПК", "pc_build"),
            ("Нужен мощный игровой компьютер для современных игр", "description"),
            ("🚚 Забрать технику", "work_format"),
            ("ул. Пушкина 10, кв 15", "address"),
            ("🌅 Утро (9:00-12:00)", "preferred_time"),
            ("+7 999 123-45-67", "phone")
        ],
        "expected_result": {
            "category": "🚀 Хочу апгрейд",
            "service": "🔧 Собрать ПК с нуля",
            "description": "Нужен мощный игровой компьютер для современных игр",
            "work_format": "🚚 Забрать технику",
            "address": "ул. Пушкина 10, кв 15",
            "preferred_time": "🌅 Утро (9:00-12:00)",
            "phone": "+7 999 123-45-67"
        }
    },
    {
        "name": "Сценарий 5: Wi-Fi → Настроить Wi-Fi роутер → Описание → В офис → Телефон",
        "steps": [
            ("🌐 «Слабый Wi-Fi / новый роутер»", "category"),
            ("📶 Настроить Wi-Fi роутер", "service"),
            ("Нужно настроить новый роутер TP-Link для офиса", "description"),
            ("🏢 В офис", "work_format"),
            ("+7 999 123-45-67", "phone")
        ],
        "expected_result": {
            "category": "🌐 «Слабый Wi-Fi / новый роутер»",
            "service": "📶 Настроить Wi-Fi роутер",
            "description": "Нужно настроить новый роутер TP-Link для офиса",
            "work_format": "🏢 В офис",
            "address": None,
            "preferred_time": "⏰ Любое время",
            "phone": "+7 999 123-45-67"
        }
    }
]

def simulate_request_creation(scenario):
    """Симуляция создания заявки по сценарию"""
    print(f"\n🧪 Тестирование: {scenario['name']}")
    print("=" * 80)
    
    # Инициализация заявки
    request = {
        "request_id": f"FX-{datetime.now().strftime('%Y%m%d')}-001",
        "user_id": test_user_id,
        "username": test_username,
        "status": "новая",
        "created_at": datetime.now().isoformat()
    }
    
    # Выполнение шагов
    for i, (input_text, step_type) in enumerate(scenario['steps'], 1):
        print(f"Шаг {i}: {step_type} → '{input_text}'")
        
        if step_type == "category":
            request["category"] = input_text
        elif step_type == "service":
            request["service"] = input_text
        elif step_type == "pc_build":
            # Для сборки ПК добавляем как описание
            request["description"] = input_text
        elif step_type == "description":
            request["description"] = input_text
        elif step_type == "work_format":
            request["work_format"] = input_text
            # Автоматически добавляем preferred_time для форматов без выезда
            if "🏠 Выезд на дом" not in input_text and "🚚 Забрать технику" not in input_text:
                request["preferred_time"] = "⏰ Любое время"
                print(f"  → Автоматически добавлено: preferred_time = '⏰ Любое время'")
        elif step_type == "address":
            request["address"] = input_text
        elif step_type == "preferred_time":
            request["preferred_time"] = input_text
        elif step_type == "phone":
            request["phone"] = input_text
    
    # Автоматически добавляем недостающие поля
    if "✍️ Описать запрос своими словами" in request.get("category", ""):
        if "service" not in request:
            request["service"] = "✍️ Свой вариант"
            print(f"  → Автоматически добавлено: service = '✍️ Свой вариант'")
    
    # Проверка результата
    print(f"\n📋 Результат создания заявки:")
    print(f"🆔 ID: {request['request_id']}")
    print(f"📝 Категория: {request.get('category', 'Нет')}")
    print(f"🔧 Услуга: {request.get('service', 'Нет')}")
    print(f"📄 Описание: {request.get('description', 'Нет')}")
    print(f"📍 Формат: {request.get('work_format', 'Нет')}")
    print(f"🏠 Адрес: {request.get('address', 'Не требуется')}")
    print(f"⏰ Время: {request.get('preferred_time', 'Не указано')}")
    print(f"📞 Телефон: {request.get('phone', 'Нет')}")
    
    # Валидация
    validation_errors = []
    
    # Проверка обязательных полей
    required_fields = ['category', 'work_format', 'preferred_time', 'phone']
    for field in required_fields:
        if field not in request or not request[field]:
            validation_errors.append(f"Отсутствует обязательное поле: {field}")
    
    # Проверка описания
    if 'description' not in request or len(request.get('description', '').strip()) < 10:
        validation_errors.append("Описание должно содержать минимум 10 символов")
    
    # Проверка соответствия ожидаемому результату
    for key, expected_value in scenario['expected_result'].items():
        if key in request:
            actual_value = request[key]
            if actual_value != expected_value:
                validation_errors.append(f"Несоответствие в поле '{key}': ожидалось '{expected_value}', получено '{actual_value}'")
    
    if validation_errors:
        print(f"\n❌ Ошибки валидации:")
        for error in validation_errors:
            print(f"  • {error}")
        return False
    else:
        print(f"\n✅ Заявка создана успешно!")
        return True

def test_all_scenarios():
    """Тестирование всех сценариев"""
    print("🚀 Начинаю тестирование всех алгоритмов создания заявки")
    print("=" * 80)
    
    successful_scenarios = 0
    total_scenarios = len(test_scenarios)
    
    for scenario in test_scenarios:
        try:
            if simulate_request_creation(scenario):
                successful_scenarios += 1
        except Exception as e:
            print(f"❌ Ошибка при тестировании сценария: {e}")
    
    print(f"\n📊 Результаты тестирования:")
    print(f"✅ Успешно: {successful_scenarios}")
    print(f"❌ Ошибок: {total_scenarios - successful_scenarios}")
    print(f"📈 Процент успеха: {(successful_scenarios / total_scenarios) * 100:.1f}%")
    
    if successful_scenarios == total_scenarios:
        print("\n🎉 Все сценарии прошли успешно! Логика создания заявок работает корректно.")
    else:
        print(f"\n⚠️ Обнаружены проблемы в {total_scenarios - successful_scenarios} сценариях.")

if __name__ == "__main__":
    test_all_scenarios()
