#!/usr/bin/env python3
"""
Простой тест для проверки работы GitHub Actions
"""

import sys
import platform
import datetime

def test_environment():
    """Тестирует окружение выполнения"""
    print("🧪 Тестирование окружения GitHub Actions")
    print("=" * 50)
    
    # Системная информация
    print(f"🐧 Операционная система: {platform.system()} {platform.release()}")
    print(f"🔧 Архитектура: {platform.machine()}")
    print(f"📦 Python версия: {platform.python_version()}")
    print(f"📁 Текущая директория: {platform.node()}")
    
    # Время
    now = datetime.datetime.now()
    print(f"📅 Дата и время: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверка модулей
    modules = ['fastapi', 'sqlalchemy', 'httpx', 'psycopg2']
    print("\n📚 Проверка зависимостей:")
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module} - доступен")
        except ImportError:
            print(f"  ❌ {module} - недоступен")
    
    print("\n✅ Все проверки пройдены успешно!")
    return True

if __name__ == "__main__":
    try:
        test_environment()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        sys.exit(1)
