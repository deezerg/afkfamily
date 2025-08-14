
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)

# Вставь сюда токен твоего бота
API_TOKEN = os.getenv("BOT_TOKEN")
# Вставь сюда свой Telegram ID для получения отчетов
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для FSM
class Form(StatesGroup):
    contract = State()
    static_id = State()
    quantity = State()
    screenshot = State()

# Клавиатура с контрактами
def contract_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("Ателье III - 1000"),
        KeyboardButton("Товар с корабля - 600"),
    )
    kb.add(
        KeyboardButton("Апельсины - 24"),
        KeyboardButton("Шампиньоны - 80"),
    )
    kb.add(
        KeyboardButton("Сосна - 100"),
        KeyboardButton("Пшеница - 250"),
    )
    return kb

# Кнопка "Вернуться назад"
back_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Вернуться назад"))

# /start
@dp.message_handler(commands="start")
async def start(message: types.Message):
    await Form.contract.set()
    await message.answer("Выберите контракт:", reply_markup=contract_keyboard())

# Выбор контракта
@dp.message_handler(state=Form.contract)
async def process_contract(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await message.answer("Вы уже на первом шаге", reply_markup=contract_keyboard())
        return
    await state.update_data(contract=message.text)
    await Form.static_id.set()
    await message.answer("Укажите ваш статический ID:", reply_markup=back_kb)

# Ввод статического ID
@dp.message_handler(state=Form.static_id)
async def process_static_id(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await Form.contract.set()
        await message.answer("Выберите контракт:", reply_markup=contract_keyboard())
        return
    if not message.text.isdigit():
        await message.answer("Введите числовой ID!")
        return
    await state.update_data(static_id=int(message.text))
    await Form.quantity.set()
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_kb)

# Ввод количества
@dp.message_handler(state=Form.quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    if message.text == "Вернуться назад":
        await Form.static_id.set()
        await message.answer("Укажите ваш статический ID:", reply_markup=back_kb)
        return
    if not message.text.isdigit():
        await message.answer("Введите числовое значение!")
        return
    await state.update_data(quantity=int(message.text))
    await Form.screenshot.set()
    await message.answer("Пришлите скриншот для отчёта:", reply_markup=back_kb)

# Присылка скриншота
@dp.message_handler(content_types=types.ContentType.PHOTO, state=Form.screenshot)
async def process_screenshot(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # Отправка админу
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Новый отчет:\nКонтракт: {data['contract']}\nID: {data['static_id']}\nКоличество: {data['quantity']}"
    )
    await message.answer("Отчет принят👌")
    # Возврат к первому этапу
    await Form.contract.set()
    await message.answer("Выберите контракт:", reply_markup=contract_keyboard())

# Кнопка "Вернуться назад" при фото
@dp.message_handler(lambda message: message.text == "Вернуться назад", state=Form.screenshot)
async def back_from_screenshot(message: types.Message):
    await Form.quantity.set()
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
