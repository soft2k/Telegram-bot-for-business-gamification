from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder,ReplyKeyboardBuilder

from app.database.models import Task



main = [
    [
        InlineKeyboardButton(text="Мой профиль", callback_data="my_profile"),
        InlineKeyboardButton(text="Задание", callback_data="task_")
    ],
    [
        InlineKeyboardButton(text="Ачивки", callback_data="ach_"),
        InlineKeyboardButton(text="Лидерборд", callback_data="liderboard_")
    ],
    [
        InlineKeyboardButton(text="Магазин", callback_data="sale_"),
        InlineKeyboardButton(text="Оставить отзыв", callback_data='review')
    ],
    [
        InlineKeyboardButton(text="Программа лояльности", callback_data="loyalty_")
    ],
    [
        InlineKeyboardButton(text="Запись на мероприятия", callback_data="event_",url='https://n1111820.yclients.com/')
    ]
]
keybord_main = InlineKeyboardMarkup(inline_keyboard=main)     





task = [
    [InlineKeyboardButton(
        text="Ежедневные задания",
        callback_data="task_1")],
    [InlineKeyboardButton(
        text="Еженедельные задания",
        callback_data="task_7")],
    [InlineKeyboardButton(
        text="Ежемесячные задания",
        callback_data="task_30")],
    [InlineKeyboardButton(
        text="◀️ Назад в главное меню",
        callback_data="back_to_main")]        
]
    

back_to_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="back_to_main")]
])


root = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Подтвердить задание")],
    [KeyboardButton(text="Подтвердить посещение")],
    [KeyboardButton(text="Редактировать задание")],
    [KeyboardButton(text="Редактировать ачивки")],
    [KeyboardButton(text="Редактировать магазин")],
    [KeyboardButton(text="Отправить рассылку")],
    [KeyboardButton(text="Редактировать админов")],
    [KeyboardButton(text='Редактировать пользователей')]
],resize_keyboard=True,)



task_root = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Добавить задание")],
    [KeyboardButton(text="Удалить задание")],
    [KeyboardButton(text="Удалить все задание")],
    [KeyboardButton(text='Назад')]
],resize_keyboard=True,)

task_category = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Ежедневное задание")],
    [KeyboardButton(text='Еженедельное задание')],
    [KeyboardButton(text='Ежемесячное задание')],
    [KeyboardButton(text='Назад')]
],resize_keyboard=True,)

shop_root = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Добавить предмет')],
    [KeyboardButton(text='Удалить предмет')],
    [KeyboardButton(text='Удалить все предметы')],
    [KeyboardButton(text='Назад')]
],resize_keyboard=True)

ach_root = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Добавить ачивку')],
    [KeyboardButton(text='Удалить ачивку')],
    [KeyboardButton(text='Удалить все ачивки')],
    [KeyboardButton(text='Назад')]
],resize_keyboard=True)

confirm_root= ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Подтвердить все')],
    [KeyboardButton(text='Потвердить одно')],
    [KeyboardButton(text='Удалить одно')],
    [KeyboardButton(text='Удалить все')],
    [KeyboardButton(text='Назад')]
],resize_keyboard=True)

visit_categories = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Стоп-чек")],
        [KeyboardButton(text="Почасовка")],
        [KeyboardButton(text='Назад')]
    ],resize_keyboard=True
)

root_menu=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Дать админку')],
        [KeyboardButton(text='Снять админку')],
        [KeyboardButton(text='Назад')]
    ],resize_keyboard=True
)

referals = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Пропустить')]
],one_time_keyboard=True,resize_keyboard=True)

phone_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Поделиться контактом", request_contact=True)]],
    resize_keyboard=True
)


edit_users=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Узнать всю информацию о пользователе')],
        [KeyboardButton(text='Редактировать статус')],
        [KeyboardButton(text='Редактировать поинты')],
        [KeyboardButton(text='Назад')]
    ],resize_keyboard=True
)

status=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Базовичок')],
        [KeyboardButton(text='Уважаемый')],
        [KeyboardButton(text='Адепт')],
        [KeyboardButton(text='Амбассадор')],
        [KeyboardButton(text='Блат')],
        [KeyboardButton(text='Назад')]
    ],resize_keyboard=True
)

back=ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Назад')]
    ],resize_keyboard=True
)