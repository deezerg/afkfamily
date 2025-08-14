
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Ваш Telegram ID для получения отчетов

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# FSM состояния
class ReportStates(StatesGroup):
    CHOOSING_CONTRACT = State()
    ENTER_ID = State()
    ENTER_QUANTITY = State()
    SEND_PHOTO = State()

# Контракты
contracts = [
    ("Ателье III - 1000", "contract_1"),
    ("Товар с корабля - 600", "contract_2"),
    ("Апельсины - 24", "contract_3"),
    ("Шампиньоны - 80", "contract_4"),
    ("Сосна - 100", "contract_5"),
    ("Пшеница - 250", "contract_6")
]

# Кнопка вернуться назад
back_button = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Вернуться назад", callback_data="back"))

# /start команда
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for name, callback in contracts:
        keyboard.add(InlineKeyboardButton(text=name, callback_data=callback))
    await message.answer("Пожалуйста, выберите контракт:", reply_markup=keyboard)
    await ReportStates.CHOOSING_CONTRACT.set()

# Выбор контракта
@dp.callback_query_handler(lambda c: c.data.startswith("contract_"), state=ReportStates.CHOOSING_CONTRACT)
async def choose_contract(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(contract=call.data)
    await call.message.edit_reply_markup(reply_markup=None)  # убираем кнопки
    await call.message.answer("Укажите ваш статический ID:", reply_markup=back_button)
    await ReportStates.ENTER_ID.set()

# Кнопка вернуться назад
@dp.callback_query_handler(lambda c: c.data == "back", state="*")
async def go_back(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == ReportStates.ENTER_ID.state or current_state == ReportStates.ENTER_QUANTITY.state or current_state == ReportStates.SEND_PHOTO.state:
        keyboard = InlineKeyboardMarkup(row_width=2)
        for name, callback in contracts:
            keyboard.add(InlineKeyboardButton(text=name, callback_data=callback))
        await call.message.answer("Выберите контракт заново:", reply_markup=keyboard)
        await ReportStates.CHOOSING_CONTRACT.set()
        await state.update_data(contract=None, user_id=None, quantity=None, photo=None)
    await call.answer()

# Ввод статического ID
@dp.message_handler(lambda message: not message.text.isdigit(), state=ReportStates.ENTER_ID)
async def invalid_id(message: types.Message):
    await message.reply("Пожалуйста, введите числовое значение для статического ID!")

@dp.message_handler(lambda message: message.text.isdigit(), state=ReportStates.ENTER_ID)
async def enter_id(message: types.Message, state: FSMContext):
    await state.update_data(user_id=int(message.text))
    await message.answer("Введите количество позиций к отгрузке:", reply_markup=back_button)
    await ReportStates.ENTER_QUANTITY.set()

# Ввод количества
@dp.message_handler(lambda message: not message.text.isdigit(), state=ReportStates.ENTER_QUANTITY)
async def invalid_quantity(message: types.Message):
    await message.reply("Пожалуйста, введите числовое значение для количества позиций!")

@dp.message_handler(lambda message: message.text.isdigit(), state=ReportStates.ENTER_QUANTITY)
async def enter_quantity(message: types.Message, state: FSMContext):
    await state.update_data(quantity=int(message.text))
    await message.answer("Пришлите скриншот для отчёта:", reply_markup=back_button)
    await ReportStates.SEND_PHOTO.set()

# Получение фото
@dp.message_handler(content_types=['photo'], state=ReportStates.SEND_PHOTO)

async def receive_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(photo=message.photo[-1].file_id)

    # Отправка отчета админу
    report_text = (
        f"Новый отчет!\n"
        f"Контракт: {data.get('contract')}\n"
        f"Статический ID: {data.get('user_id')}\n"
        f"Количество: {data.get('quantity')}"
    )
    await bot.send_message(ADMIN_ID, report_text)
    await bot.send_photo(ADMIN_ID, data.get("photo"))

    await message.answer("Отчет принят👌")
    # Возврат к первому этапу
    keyboard = InlineKeyboardMarkup(row_width=2)
    for name, callback in contracts:
        keyboard.add(InlineKeyboardButton(text=name, callback_data=callback))
    await message.answer("Пожалуйста, выберите контракт:", reply_markup=keyboard)
    await ReportStates.CHOOSING_CONTRACT.set()
    await state.update_data(contract=None, user_id=None, quantity=None, photo=None)

# Проверка на не фото
@dp.message_handler(lambda message: message.content_type != 'photo', state=ReportStates.SEND_PHOTO)
async def invalid_photo(message: types.Message):
    await message.reply("Пожалуйста, пришлите именно фото!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
