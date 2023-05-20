from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import Text

from config import TOKEN_API
from sqlite import db_start, create_car, edit_profile, create_profile


async def on_startup(_):
    await db_start()  # подключение к БД, если существует, иначе создание и подключение


storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot,
                storage=storage)


class CarStatesGroup(StatesGroup):

    brand = State()
    year = State()
    name = State()
    phone = State()


def get_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/start'))

    return kb


def get_ikb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text='🚗', callback_data='car_start')
    kb.add(button)
    return kb


def get_phone_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(
        'Отправить мой сотовый телефон боту ☎️', request_contact=True))

    return kb


def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/cancel'))

    return kb


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.reply('Вы прервали создание заявки!',
                        reply_markup=get_kb())


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message) -> None:
    await create_profile(user_id=message.from_user.id)
    await message.answer('Добро пожаловать! Для того, чтобы  подать заявку на машину - нажмите на 🚗',
                         reply_markup=get_ikb())


@dp.message_handler(commands=['userid'])
async def cmd_userid(message: types.Message) -> None:
    await message.answer(f'{message.from_user.id}',
                         reply_markup=get_kb())


@dp.callback_query_handler()
async def vote_callback(callback: types.CallbackQuery):
    if callback.data == 'car_start':
        await bot.send_message(callback.from_user.id, "Давайте начнём создавать вашу заявку на машину! Для начала, отправьте мне марку машины",
                               reply_markup=get_cancel_kb())
        await CarStatesGroup.brand.set()  # установили состояние марки


@dp.message_handler(lambda message: message.text.isdigit(), state=CarStatesGroup.brand)
async def check_brand(message: types.Message):
    await message.reply('Это не марка машины!')


@dp.message_handler(content_types=['text'], state=CarStatesGroup.brand)
async def load_brand(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['brand'] = message.text

    await message.reply('Теперь напишите, какого года машину вы планируете рассмотреть')
    await CarStatesGroup.next()


@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) < 1950, state=CarStatesGroup.year)
async def check_year(message: types.Message):
    await message.reply('Введите реальный год!')


@dp.message_handler(state=CarStatesGroup.year)
async def load_year(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['year'] = message.text

    await message.reply('Отправьте своё имя')
    await CarStatesGroup.next()


@dp.message_handler(state=CarStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text

    # keyboard = types.ReplyKeyboardMarkup(
    #     resize_keyboard=True, one_time_keyboard=True)
    # keyboard.add(types.KeyboardButton(
    #     text="Send my number to bot ☎️", request_contact=True))
    await message.reply('Теперь поделитесь своим телефоном', reply_markup=get_phone_kb())
    await CarStatesGroup.next()


@ dp.message_handler(state=CarStatesGroup.phone, content_types=types.ContentTypes.CONTACT)
async def load_phone(message: types.Message, state: FSMContext):
    user_telephone_num = message.contact.phone_number
    async with state.proxy() as data:
        data['phone'] = user_telephone_num
        # отправляем созданную заявку указанному телеграм-юзеру
        await bot.send_message(chat_id=679553167, text=f"{data['brand']}, {data['year']}\n{data['name']}, {data['phone']}")

    # сохраняем заявку со всеми данными.
    await create_car(user_id=message.from_user.id, state=state)
    await message.answer('Заявка принята в работу. Скоро с вами свяжутся!', reply_markup=get_kb())
    # сохраняем пользователя со всеми данными.
    await edit_profile(state, user_id=message.from_user.id)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp,
                           skip_updates=True,
                           on_startup=on_startup)
