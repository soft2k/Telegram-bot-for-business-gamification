import asyncio
from typing import List
from aiogram import Bot, Dispatcher, types,Router,F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
 
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy import select,desc
from app.database.models import async_session
from app.database.models import User,Task,Shop,Confirm
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.orm import sessionmaker, declarative_base
import app.database.models as md
import app.database.requests as rq
import app.keybord as kb
import app.root as rt

router = Router()


class ConfrimDay(StatesGroup):
    waiting_for_confrim = State


@router.message(Command("start"))
async def send_welcome(message: types.Message):
    await rq.set_user(message.from_user.id, message.from_user.full_name)
    await message.answer("Добро пожаловать в СходкаБот!",reply_markup=kb.main)


@router.message(Command("root"))
async def check_root(message: types.Message):
    user = rq.set_user(message.from_user.id, message.from_user.full_name)
    has_access = await rq.check_root_id(message.from_user.id)
    if has_access:
        await message.answer("Вы администратор!",reply_markup=kb.root)
    else:
        await message.answer("У вас нет доступа!",reply_markup=kb.main)

@router.message(F.text == 'Назад')
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать в СходкаБот!",reply_markup=kb.main)


    
#Хендлерс для пользователя

@router.message(F.text == 'Мой профиль')
async def my_profile(message: types.Message):
    user_info = await rq.profile(message.from_user.id)

    await message.answer(
        f"👤 Профиль пользователя:\n"
            f"Имя: {user_info['name']}\n"
            f"Баланс: {user_info['points']}\n"
            f"Всего очков: {user_info['all_point']}\n"
            f"Выполненные задания: {user_info['tasks']}\n"
            f"Твой уровень: {user_info['level']}\n"
           
             
              ,reply_markup=kb.main)


@router.message(F.text == 'Задание')
async def my_profile(message: types.Message):
    await message.answer('Выберите категорию заданий',reply_markup=kb.task)

async def get_tasks():
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == 1))
        tasks = result.scalars().all()
        return tasks





@router.message(F.text == 'Ежедневные задание')
async def show_tasks(message: types.Message):
    async with async_session() as session:
        
        # Изменяем запрос, чтобы выбирать только задания с category_id = 1
        result = await session.execute(select(Task).where(Task.category_id == 1))
        tasks = result.scalars().all()

    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(text=f"{task.description} | {task.point}", callback_data=f"task_{task.id}")
    
    builder.adjust(1)  # Устанавливаем по одной кнопке в ряд

    await message.answer("Выберите задание:", reply_markup=builder.as_markup())

    if not task:
        await message.answer('На данный момент заданий нет')
        return

@router.message(F.text == 'Еженедельные задание')
async def show_tasks(message: types.Message):
    async with async_session() as session:
        
        result = await session.execute(select(Task).where(Task.category_id == 7))
        tasks = result.scalars().all()


    if not tasks:
        await message.answer("На данный момент нет доступных заданий.")
        return

    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(text=f"{task.description} | {task.point}", callback_data=f"task_{task.id}")
    
    builder.adjust(1)  

    await message.answer("Выберите задание:", reply_markup=builder.as_markup())


@router.message(F.text == 'Ежемесечные задание')
async def show_tasks(message: types.Message):
    async with async_session() as session:
        
        result = await session.execute(select(Task).where(Task.category_id == 30))
        tasks = result.scalars().all()


    if not tasks:
        await message.answer("На данный момент нет доступных заданий.")
        return

    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(text=f"{task.description} | {task.point}", callback_data=f"task_{task.id}")
    
    builder.adjust(1)  

    await message.answer("Выберите задание:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("task_"))
async def process_task_selection(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split("_")[1])
    
    async with async_session() as session:
        result = await session.execute(select(Task).filter(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        if task:
            # Сохраняем нужные данные из task
            task_description = task.description
            task_point = task.point

            new_confirm = Confirm(
                tg_id=callback_query.from_user.id,
                name=callback_query.from_user.username,
                description=task_description,
                points=task_point
            )
            session.add(new_confirm)
            await session.commit()

    if task:
        await callback_query.answer(f"Вы выбрали задание: {task_description}")
        await callback_query.message.answer(f"Задание '{task_description}' ({task_point} points) добавлено в базу подтверждений.Ожидайте подтверждения администратором.")

    else:
        await callback_query.answer("Задание не найдено.")



@router.message(F.text == 'Лидерборд')
async def show_top_users(message: types.Message):
    async with async_session() as session:
        result = await session.execute(select(User).order_by(desc(User.all_point)).limit(10))
        users = result.scalars().all()
        if users:
            response = 'Топ 10 пользователей по очкам:\n\n'
            for i, user in enumerate(users, start=1):
                response += f"{i} | {user.name} | {user.all_point} очков\n"
            await message.answer(response)
        else:
            await message.answer("Пользователи не найдены")

#Магазин


@router.message(F.text == 'Магазин')
async def show_shop(message: types.Message):
    async with async_session() as session:
        
        result = await session.execute(select(Shop))
        shops = result.scalars().all()


    if not shops:
        await message.answer("На данный момент нельзя ничего купить.")
        return

    builder = InlineKeyboardBuilder()
    for shop in shops:
        builder.button(text=f"{shop.description} | {shop.points}", callback_data=f"shop_{shop.id}")
    
    builder.adjust(1)  

    await message.answer("Выберите задание:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("shop_"))
async def process_shop_purchase(callback: types.CallbackQuery):
    shop_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        async with session.begin():
            # Получаем информацию о товаре
            shop_item = await session.execute(select(Shop).where(Shop.id == shop_id))
            shop_item = shop_item.scalar_one_or_none()

            if not shop_item:
                await callback.answer("Товар не найден.")
                return

            # Получаем информацию о пользователе
            user = await session.execute(select(User).where(User.tg_id == user_id))
            user = user.scalar_one_or_none()

            if not user:
                await callback.answer("Пользователь не найден.")
                return

            # Проверяем, достаточно ли у пользователя очков
            if user.point >= shop_item.points:
                # Вычитаем очки у пользователя
                user.point -= shop_item.points
                
                # Используем callback.message вместо отдельного аргумента message
                await callback.message.answer(f"Вы успешно приобрели {shop_item.description}! Покажите это сообщение Админу, чтобы получить подарок!")
                
                # Отвечаем на callback, чтобы убрать "часики" на кнопке
                await callback.answer()
            else:
                await callback.answer("У вас недостаточно очков для покупки этого товара.")

        
