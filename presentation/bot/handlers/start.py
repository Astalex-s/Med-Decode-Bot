from aiogram import Router, html
from aiogram.types import Message
from aiogram.filters import CommandStart
# Импортируем функцию создания главной клавиатуры
from presentation.bot.keyboards.main_kb import main_keyboard

# Роутер для обработчиков команды /start
my_router = Router(name=__name__)


# Обработчик команды /start — срабатывает когда пользователь отправляет /start
@my_router.message(CommandStart())
async def message_handler(message: Message) -> None:
    # Отправляем приветствие с именем пользователя и главным меню с кнопками
    await message.answer(
        f'{html.bold(message.from_user.full_name)}, Приветствую тебя в боте для анализа медицинских '
        'изображений! Я помогу тебе загрузить анализ и узнать о твоей подписке. '
        'Пожалуйста, выбери действие из меню ниже.',
        reply_markup=main_keyboard()
    )
    


