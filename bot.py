import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# Включите логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
BOT_TOKEN = '8974328120:AAGj5zUqnlrgQktPlUCjLxoQvF1JV7JSEGs'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Определяем состояния (шаги) диалога
class HookGenerator(StatesGroup):
    waiting_for_lib = State()   # Ожидание выбора библиотеки
    waiting_for_subs = State()  # Ожидание списка функций

# Обычная клавиатура для главного меню
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 Патчи")]
        ],
        resize_keyboard=True
    )

# Команда /start
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()  # Сбрасываем старые состояния
    await message.answer("Че надо?", reply_markup=get_main_keyboard())

# Кнопка "Патчи" запускает процесс генерации
@dp.message(F.text == "🔧 Патчи")
async def start_patches(message: Message, state: FSMContext):
    await message.answer("Выбери библиотеку (или введи её имя вручную):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(HookGenerator.waiting_for_lib)

# Шаг 1: Получаем имя библиотеки
@dp.message(HookGenerator.waiting_for_lib)
async def process_lib_name(message: Message, state: FSMContext):
    lib_name = message.text.strip()
    await state.update_data(chosen_lib=lib_name) # Сохраняем имя библиотеки
    
    await message.answer("Кидай список sub_xxxxx (каждая функция с новой строки):")
    await state.set_state(HookGenerator.waiting_for_subs)

# Шаг 2: Получаем функции и генерируем C++ код
@dp.message(HookGenerator.waiting_for_subs)
async def process_subs(message: Message, state: FSMContext):
    user_data = await state.get_data()
    lib_name = user_data['chosen_lib']
    
    # Разбиваем текст пользователя по строкам и убираем лишние пробелы
    lines = message.text.strip().split('\n')
    
    generated_code = f"// Hooks for {lib_name}\n\n"
    
    for line in lines:
        sub_name = line.strip()
        if not sub_name:
            continue
            
        # Пытаемся вытащить адрес из названия (например, из sub_1D081C получаем 0x1D081C)
        # Если формат другой, можно просто подставлять имя
        address = sub_name.replace("sub_", "0x")
        if not address.startswith("0x"):
            address = f"// [Неверный формат адреса для {sub_name}]"

        # Формируем шаблон C++ кода (как на скриншоте)
        generated_code += (
            f"// {sub_name} at {address}\n"
            f"int64 (*osub_{sub_name[4:]})(int64 a1, int64 a2, int64 a3, __int64 a4) = 0;\n\n"
            f"int64 fastcall hsub_{sub_name[4:]}(int64 a1, int64 a2, int64 a3, int64 a4)\n"
            f"{{\n"
            f"    return 0;\n"
            f"}}\n\n"
            f'HOOK_LIB("{lib_name}", "{address}", hsub_{sub_name[4:]}, osub_{sub_name[4:]});\n\n'
        )

    # Оборачиваем код в Markdown-блок, чтобы в Telegram появилась кнопка "Копировать код"
    final_message = f"`C++\n{generated_code.strip()}\n```"
    
    await message.answer(final_message, parse_mode="MarkdownV2")
    await message.answer("✅ Готово! /start для нового", reply_markup=get_main_keyboard())
    
    # Завершаем работу машины состояний
    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if name == 'main':
    asyncio.run(main())