import asyncio
from typing import List
from aiogram import Bot, Dispatcher, types,Router,F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware


import app.database.models as md
import app.database.requests as rq
import app.keybord as kb
import app.root as rt

router_root = Router()



#для админа
class AddTaskStates(StatesGroup):
    waiting_for_task = State()
    waiting_for_task_category =State()
    waiting_for_task_points = State()

@router_root.message(F.text == 'Редактировать задание')
async def edit_task(message: types.Message, state: FSMContext):
    await message.answer('Выберите что будэ делать',reply_markup=kb.task_root)

@router_root.message(F.text == 'Добавить задание')
async def add_tasks(message: types.Message, state: FSMContext):
    await message.answer('Введите название задания')
    await state.set_state(AddTaskStates.waiting_for_task)

@router_root.message(AddTaskStates.waiting_for_task)
async def process_task_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите категорию задания:')
    await state.set_state(AddTaskStates.waiting_for_task_category)

@router_root.message(AddTaskStates.waiting_for_task_category)
async def process_task_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer('Введите количество очков за задание:')
    await state.set_state(AddTaskStates.waiting_for_task_points)

@router_root.message(AddTaskStates.waiting_for_task_points)
async def process_task_points(message: types.Message, state: FSMContext):
    try:
        points = int(message.text)
    except ValueError:
        await message.answer('Некорректное значение очков. Введите число.')
        return

    await state.update_data(points=points)
    data = await state.get_data()
    async with md.async_session() as session:
        new_task = md.Task(
            description=data['description'],
            category_id=data['category'],
            point=data['points']
        )
        session.add(new_task)
        await session.commit()

    await message.answer("Задача добавлена!")








