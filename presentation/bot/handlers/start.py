from aiogram import Router, html
from aiogram.types import Message
from aiogram.filters import CommandStart    
from presentation.bot.keyboards.main_kb import main_keyboard


my_router = Router(name=__name__)

    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
@my_router.message(CommandStart())
async def message_handler(message: Message) -> None:
    await message.answer(f'{html.bold(message.from_user.full_name)}, Приветствую тебя в боте для анализа медицинских'
                          'изображений! Я помогу тебе загрузить анализ и узнать о твоей подписке.'
                          'Пожалуйста, выбери действие из меню ниже.', reply_markup=main_keyboard())
    


