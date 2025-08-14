
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

# Получаем токен бота и ID администратора из переменных окружения
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # твой Telegram ID

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# FSM состояния
class ReportStates(StatesGroup):
    CHOOSE_CONTRACT = State()
    ENTER_ID = State()
    ENTER_QUANTITY = State()
    SEND_PHOTO = State()

# Контракты
contracts = [
    ("Ателье III - 1000", "1000"),
    ("Товар с корабля - 600", "600"),
    ("Апельсины - 24", "24"),
    ("Шампиньоны - 80", "80"),
    ("Сосна - 100", "100"),
    ("Пшеница - 250", "250"),
]

# Кнопка вернуться назад
back_button = KeyboardButton("🔙 Вернуться назад")

def contract_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for name, _ in contracts:
        kb.add(KeyboardButton(name))
    return kb

def back_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(back_button)
    return kb

# Старт
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋\nПожалуйста, выберите контракт для отчета ниже:",
        reply_markup=contract_keyboard()
    )
    await ReportStates.CHOOSE_CONTRACT.set()

# Выбор контракта
@dp.message_handler(state=ReportStates.CHOOSE_CONTRACT)
async def choose_contract(message: types.Message, state: FSMContext):
    if message.text == back_button.text:
        await message.answer("Вы уже на первом шаге.", reply_markup=contract_keyboard())
        return

    selected = next((name for name, _ in contracts if name == message.text), None)
    if selected:
        await state.update_data(contract=selected)
        await message.answer("Укажите ваш статический ID:", reply_markup=back_keyboard())
        await ReportStates.ENTER_ID.set()
    else:
        await message.answer("Пожалуйста, выберите контракт с кнопок ниже.", reply_markup=contract_keyboard())

# Ввод ID
@dp.message_handler(state=ReportStates.ENTER_ID)
async def enter_id(message: types.Message, state: FSMContext):
    if message.text == back_button.text:
        await message.answer("Вы вернулись к выбору контракта.", reply_markup=contract_keyboard())
        await ReportStates.CHOOSE_CONTRACT.set()
        return

    if not message.text.isdigit():
        await message.answer("Введите числовой ID!")
        return

    await state.update_data(user_id=message.text)
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_keyboard())
    await ReportStates.ENTER_QUANTITY.set()

# Ввод количества
@dp.message_handler(state=ReportStates.ENTER_QUANTITY)
async def enter_quantity(message: types.Message, state: FSMContext):
    if message.text == back_button.text:
        await message.answer("Вы вернулись к вводу статического ID:", reply_markup=back_keyboard())
        await ReportStates.ENTER_ID.set()
        return

    if not message.text.isdigit():
        await message.answer("Введите числовое значение!")
        return

    await state.update_data(quantity=message.text)
    await message.answer("Пришлите скриншот для отчёта:", reply_markup=back_keyboard())
    await ReportStates.SEND_PHOTO.set()

# Получение фото
@dp.message_handler(content_types=types.ContentType.PHOTO, state=ReportStates.SEND_PHOTO)
async def handle_photo(message: types.Message, state: FSMContext):
    if message.text == back_button.text:
        await message.answer("Вы вернулись к вводу количества:", reply_markup=back_keyboard())
        await ReportStates.ENTER_QUANTITY.set()
        return

    data = await state.get_data()
    contract = data.get("contract")
    user_id = data.get("user_id")
    quantity = data.get("quantity")

    # Отправка отчета админу
    photo_file = message.photo[-1].file_id
    await bot.send_message(
        ADMIN_ID,
        f"Новый отчет от пользователя:\n"
        f"Контракт: {contract}\n"
        f"Статический ID: {user_id}\n"
        f"Количество: {quantity}"
    )
    await bot.send_photo(ADMIN_ID, photo_file)

    await message.answer("Отчет принят 👌", reply_markup=contract_keyboard())
    await ReportStates.CHOOSE_CONTRACT.set()  # возвращаем пользователя к первому шагу

# Проверка текстового сообщения на этапе фото (чтобы не пропускать без фото)
@dp.message_handler(lambda message: True, state=ReportStates.SEND_PHOTO)
async def check_photo(message: types.Message):
    await message.answer("Пожалуйста, отправьте скриншот для отчета!")

# Ловушка на все этапы, где пользователь вводит некорректные данные
@dp.message_handler(state='*')
async def catch_all(message: types.Message):
    await message.answer("Пожалуйста, используйте кнопки или вводите данные в требуемом формате!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
