import asyncio
from typing import List
from aiogram import Bot, Dispatcher, types,Router,F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
 
from sqlalchemy import select,desc
from app.database.models import async_session
from app.database.models import User,Task
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.orm import sessionmaker, declarative_base
import app.database.models as md
import app.database.requests as rq
import app.keybord as kb
import app.root as rt

router = Router()



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
async def show_tasks_day(message: types.Message):
    category_id = 1  
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.category_id == category_id))
        tasks = result.scalars().all()
        if tasks:
            response = ''
            for task in tasks:
                response += f" {task.description} | Очки: {task.point}\n\n"
            await message.answer(response)
        else:
            await message.answer("Задачь пока нет.Приходи позже")


@router.message(F.text == 'Еженедельные задание')
async def show_tasks_week(message: types.Message):
    category_id = 7  
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.category_id == category_id))
        tasks = result.scalars().all()
        if tasks:
            response = ''
            for task in tasks:
                response += f" {task.description} | Очки: {task.point}\n\n"
            await message.answer(response)
        else:
            await message.answer("Задачь пока нет.Приходи позже")


@router.message(F.text == 'Ежемесечные задание')
async def show_tasks_month(message: types.Message):
    category_id = 30  
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.category_id == category_id))
        tasks = result.scalars().all()
        if tasks:
            response = ''
            for task in tasks:
                response += f" {task.description} | Очки: {task.point}\n\n"
            await message.answer(response)
        else:
            await message.answer("Задачь пока нет.Приходи позже")

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