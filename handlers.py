from aiogram import Router, F, Bot, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, message_id, CallbackQuery, InlineKeyboardButton, \
    InputFile, FSInputFile, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from decimal import Decimal

from database.db import DataBase

import html
import logging


db = DataBase()
router = Router()


# Определение состояний
class OrderStates(StatesGroup):
    choosing_box = State()
    adding_products = State()
    choosing_date = State()
    choosing_location = State()
    confirming_order = State()


print("v1.0")


@router.message(Command("start"))
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Предзаказ", callback_data="preorder"))
    await message.answer(text='Привет! Выберите действие:', reply_markup=builder.as_markup())


@router.callback_query(F.data == 'preorder')
async def preorder_handler(call: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Energy Box", callback_data="box_1"),
        InlineKeyboardButton(text="No Stress Box", callback_data="box_2"),
    ).row(
        InlineKeyboardButton(text="Обжора Box", callback_data="box_3"),
        InlineKeyboardButton(text="VIP Box", callback_data="box_4"),
    ).row(
        InlineKeyboardButton(text="Собрать самому", callback_data="custom_box"),
    )
    await call.message.answer(text='Выберите коробку или соберите свою: \n', reply_markup=builder.as_markup())
    await state.set_state(OrderStates.choosing_box)


@router.callback_query(F.data.in_(['box_1', 'box_2', 'box_3', 'box_4']))
async def box_selection_handler(call: CallbackQuery, state: FSMContext):
    box_id = call.data.split('_')[1]  # Получаем номер коробки
    await state.update_data(box_id=box_id)
    await call.message.answer(text=f"Вы выбрали коробку {box_id}. Хотите добавить что-то еще?")

    # Получаем список товаров из базы данных
    products = db.exec_query("SELECT name FROM products")
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(InlineKeyboardButton(text=product[0], callback_data=f"add_{product[0]}"))

    builder.row(InlineKeyboardButton(text="Завершить выбор", callback_data="finish_selection"))
    await call.message.answer(text='Выберите товары для добавления:', reply_markup=builder.as_markup())
    await state.set_state(OrderStates.adding_products)


@router.callback_query(F.data.startswith("add_"))
async def add_product_handler(call: CallbackQuery, state: FSMContext):
    product_name = call.data.split('_')[1]
    products_id = db.exec_query(f"SELECT id FROM products where name = '{product_name}'")

    # Добавляем товар в состояние
    current_data = await state.get_data()
    added_products_id = current_data.get("added_products", [])
    added_products_id.append(products_id[0][0])  # Добавляем ID продукта
    await state.update_data(added_products=added_products_id)

    added_products_name = current_data.get("added_products_name", [])
    added_products_name.append(product_name)  # Добавляем имя продукта
    await state.update_data(added_products_name=added_products_name)

    await call.answer(text=f"Товар {product_name} добавлен.")


@router.callback_query(F.data == "finish_selection")
async def finish_selection_handler(call: CallbackQuery, state: FSMContext):
    await call.message.answer(text="Введите дату, когда вам нужен заказ (например, 2023-10-01):")
    await state.set_state(OrderStates.choosing_date)


@router.message(OrderStates.choosing_date)
async def date_handler(message: Message, state: FSMContext):
    date = message.text
    await state.update_data(date=date)  # Сохраняем дату в состоянии
    await message.answer(text="Введите место получения заказа (например, общага, дом):")
    await state.set_state(OrderStates.choosing_location)


@router.message(OrderStates.choosing_location)
async def location_handler(message: Message, state: FSMContext):
    location = message.text
    await state.update_data(location=location)  # Сохраняем место в состоянии

    # Получаем данные о заказе
    data = await state.get_data()
    date = data.get("date")
    location = data.get("location")
    added_products = data.get("added_products", [])
    added_products_name = data.get("added_products_name", [])

    # Подсчёт стоимости заказа
    data = await state.get_data()
    box_id = data.get("box_id")
    base_price = db.exec_query(f"SELECT base_price FROM boxes WHERE id = {box_id}")
    total_price = Decimal(base_price[0][0]) if base_price else Decimal(0)  # Инициализируем total_price как Decimal
    for product_name in added_products:
        product = db.exec_query(f"SELECT price FROM products WHERE name = '{product_name}'")
        if product:
            total_price += product[0][0]  # Добавляем цену товара к общей стоимости

    # Сохраняем total_price в состоянии
    await state.update_data(total_price=total_price)

    # Запрос на подтверждение заказа
    confirm_keyboard = InlineKeyboardBuilder()
    confirm_keyboard.add(InlineKeyboardButton(text="Подтвердить", callback_data="confirm_order"))
    confirm_keyboard.add(InlineKeyboardButton(text="Отменить", callback_data="cancel_order"))

    await message.answer(
        text=f"Ваш предзаказ:\nДата: {date}\nМесто: {location}\nТовары: {', '.join(added_products_name)}\nСумма: {total_price} рублей.\n\nПодтвердите заказ?",
        reply_markup=confirm_keyboard.as_markup()
    )
    await state.set_state(OrderStates.confirming_order)

@router.callback_query(F.data == "confirm_order")
async def confirm_order_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    box_id = data.get("box_id")
    date = data.get("date")
    location = data.get("location")
    added_products = data.get("added_products", [])
    total_price = data.get("total_price")  # Получаем total_price из состояния

    # Здесь вы можете добавить логику для создания заказа в базе данных
    telegram_id = call.from_user.id  # Получаем ID пользователя
    box_id = box_id  # Если это кастомный заказ, box_id будет None
    custom_products = [product for product in added_products]  # Список кастомных товаров

    # Создание заказа в базе данных
    db.exec_update_query(f"""
            INSERT INTO orders (telegram_id, box_id, custom_products, scheduled_time, location, total_price)
            VALUES ({telegram_id}, {box_id}, ARRAY{custom_products}, '{date}', '{location}', {total_price});
        """)

    await call.message.answer("Ваш заказ успешно создан! Спасибо за покупку.")
    await state.clear()  # Сброс состояния

@router.callback_query(F.data == "cancel_order")
async def cancel_order_handler(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Ваш предзаказ отменён.")
    await state.clear()  # Сброс состояния