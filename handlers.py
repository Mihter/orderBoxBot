from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, message_id, CallbackQuery, InlineKeyboardButton, \
    InputFile, FSInputFile, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

#from database.db import DataBase

import html
import logging


#db = DataBase()
router = Router()


#class Form(StatesGroup):
#    institution = State()


print("v1.0")
@router.message(Command("start"))
async def start_handler(message: Message):
    print("Start command received")
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Привет",
        callback_data=f"privet"))
    await message.answer(
        text='Привет',
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'privet')
async def student_handler(call: CallbackQuery):
    tg_id = call.from_user.id
    first_name = call.from_user.first_name
    last_name = call.from_user.last_name
    fullname = first_name + (f" {last_name}" if last_name else "")  # Объединяем имя и фамилию
    contact = '@' + call.from_user.username

    await call.message.answer(
        text='Привет '+fullname
    )
    await call.answer()