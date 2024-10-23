from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Task


main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Мой профиль")],
    [KeyboardButton(text="Задание")],
    [KeyboardButton(text="Ачивки")],
    [KeyboardButton(text="Лидерборд")],
    [KeyboardButton(text="Магазин")]
],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите пункт меню.')

task = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ежедневные задание")],
    [KeyboardButton(text="Еженедельные задание")],
    [KeyboardButton(text="Ежемесечные задание")],
    [KeyboardButton(text="Назад")]
], resize_keyboard=True)



root = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Подтвердить задание")],
    [KeyboardButton(text="Редактировать задание")],
    [KeyboardButton(text="Редактировать ачивки")],
    [KeyboardButton(text="Редактировать магазин")],
    [KeyboardButton(text="Отправить рассылку")]
],resize_keyboard=True,)



task_root = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Добавить задание")],
    [KeyboardButton(text="Удалить задание")],
    [KeyboardButton(text="Удалить все задание")]
],resize_keyboard=True,)

shop_root = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Добавить предмет')],
    [KeyboardButton(text='Удалить предмет')],
    [KeyboardButton(text='Удалить все предметы')]
],resize_keyboard=True)

confirm_root= ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Подтвердить все')],
    [KeyboardButton(text='Потвердить одно')],
    [KeyboardButton(text='Удалить одно')],
    [KeyboardButton(text='Удалить все')]
],resize_keyboard=True)

