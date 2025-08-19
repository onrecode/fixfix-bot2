import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.handlers import *
from bot.keyboards import *

# Загрузка переменных окружения
load_dotenv()

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    # Получаем токен
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("Токен не найден!")
        return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("test", test_specific_handler))
    application.add_handler(CommandHandler("testkeyboards", test_keyboards_handler))
    application.add_handler(CommandHandler("config", check_config_handler))
    application.add_handler(CommandHandler("debug", debug_state_handler))
    application.add_handler(CommandHandler("check", check_command_handler))
    
    # Обработчики главного меню
    application.add_handler(MessageHandler(filters.Regex(r'^🔴 Компьютер глючит/не работает$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^⚙️ Установить/Настроить программу$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^📷 Подключить/Настроить устройство$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^🚀 Хочу апгрейд$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^🌐 «Слабый Wi-Fi / новый роутер»$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^🔒 VPN и Защита данных$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^✍️ Описать запрос своими словами$'), category_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^📋 Мои заявки$'), my_requests_handler))  # Исправлено
    
    # Обработчики услуг
    application.add_handler(MessageHandler(filters.Regex(r'^(💻 Тормозит/Не включается|🔧 Выскакивают ошибки|🦠 Вирусы и реклама|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📦 Установить программу|🌐 Настроить интернет|🖨️ Подключить устройства|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(🖨️ Настроить принтер/сканер|🎮 Настроить приставку|🖱️ Настроить мышь/клавиатуру|📱 Подключить телефон|📺 Подключить телевизор|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(💾 Увеличить оперативную память|🔧 Заменить процессор|💿 Установить SSD диск|🎮 Установить видеокарту|🖥️ Заменить блок питания|❄️ Улучшить охлаждение|🔧 Собрать ПК с нуля|💻 Подбор комплектующих|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(📶 Настроить Wi-Fi роутер|🌐 Усилить сигнал|🔐 Установить пароль|📡 Новый роутер|📱 Подключить устройства|✍️ Свой вариант)$'), service_handler))
    application.add_handler(MessageHandler(filters.Regex(r'^(🔐 Настроить VPN|🛡️ Проверка на вирусы|💾 Восстановление данных|🔒 Шифрование|🔑 Парольная защита|✍️ Свой вариант)$'), service_handler))
    
    # Обработчики формата работы
    application.add_handler(MessageHandler(filters.Regex(r'^(🏠 Выезд на дом|💻 Удаленная помощь|🚚 Забрать технику|🏢 В офис)$'), work_format_handler))
    
    # Обработчики времени
    application.add_handler(MessageHandler(filters.Regex(r'^(🌅 Утро \(9:00-12:00\)|☀️ День \(12:00-18:00\)|🌆 Вечер \(18:00-22:00\)|⏰ Любое время)$'), time_handler))
    
    # Обработчики контактов (исправлено)
    application.add_handler(MessageHandler(filters.Regex(r'^📞 Отправить номер$'), contact_handler))
    
    # Обработчик подтверждения (должен идти перед общим текстовым обработчиком)
    application.add_handler(MessageHandler(filters.Regex(r'^(✅ Подтвердить заявку|🔄 Изменить данные|❌ Отменить)$'), confirm_handler))
    
    # Обработчик кнопки "Назад"
    application.add_handler(MessageHandler(filters.Regex(r'^⬅️ Назад$'), back_handler))
    
    # Обработчик текстовых сообщений (должен быть последним)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    # Обработчик для получения chat_id
    application.add_handler(CommandHandler("chatid", get_chat_id_handler))
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()