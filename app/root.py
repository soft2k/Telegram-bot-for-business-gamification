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
from sqlalchemy import select,desc,delete

from app.database.models import User,Task,Shop
from app.database.models import async_session
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

class DeleatTask(StatesGroup):
    waiting_number_deleat = State()

class AddShopStates(StatesGroup):
    waiting_for_shop = State()
    waiting_for_shop_category = State()
    waiting_for_shop_points = State()

class DeleatShop(StatesGroup):
    waiting_number_deleat = State()
    



@router_root.message(F.text == 'Редактировать задание')
async def edit_task(message: types.Message, state: FSMContext):
    await message.answer('Выберите что будэ делать',reply_markup=kb.task_root)

@router_root.message(F.text == 'Удалить все задание')
async def delete_all_task(message: types.Message, state : FSMContext):
    async with async_session() as session:
        task = await session.execute(delete(Task))
        await session.commit()
    await message.answer('Все задание удалены',reply_markup=kb.root)

@router_root.message(F.text == 'Удалить задание')
async def deleat_task(message: types.Message, state : FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()

        if tasks:
            task_list = 'Список заданий"\n\n'
            for task in tasks:
                task_list += f"{task.id}. | {task.description}\n"
        else:
            task_list = 'Список заданий пуст'
        await message.reply(task_list)
    await message.answer('Введите номер задание, которого хотите удалить')
    await state.set_state(DeleatTask.waiting_number_deleat)

@router_root.message(DeleatTask.waiting_number_deleat)
async def processing_deleat_task(message: types.Message,state: FSMContext):
    try:
        task_id = int(message.text)
        async with async_session() as session:
            task = await session.get(Task, task_id)
            if task:
                await session.delete(task)
                await session.commit()
                await message.reply(f"Задание с {task_id} успешно удалён")
            else:
                await message.reply(f'Задание с таким ID: {task_id} не найден')
    except ValueError:
        await message.reply('Введите коректный ID')
    
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




#Магазин 

@router_root.message(F.text == 'Редактировать магазин')
async def edit_shop(message: types.Message, state: FSMContext):
    await message.answer('Выберите что будэ делать',reply_markup=kb.shop_root)

@router_root.message(F.text == 'Удалить все предметы')
async def delete_all_shop(message: types.Message, state : FSMContext):
    async with async_session() as session:
        shop = await session.execute(delete(Shop))
        await session.commit()
    await message.answer('Все предметы удалены',reply_markup=kb.root)

@router_root.message(F.text == 'Удалить предмет')
async def deleat_shop(message: types.Message, state : FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Shop))
        shops = result.scalars().all()

        if shops:
            shop_list = 'Список предметов"\n\n'
            for shop in shops:
                shop_list += f"{shop.id}. | {shop.description} | {shop.points}\n"
        else:
            shop_list = 'Список предметов пуст'
        await message.reply(shop_list)
    await message.answer('Введите номер предмета, которого хотите удалить')
    await state.set_state(DeleatShop.waiting_number_deleat)

@router_root.message(DeleatShop.waiting_number_deleat)
async def processing_deleat_shop(message: types.Message,state: FSMContext):
    try:
        shop_id = int(message.text)
        async with async_session() as session:
            shop = await session.get(Shop, shop_id)
            if shop:
                await session.delete(shop)
                await session.commit()
                await message.reply(f"Предмет с {shop_id} успешно удалён")
            else:
                await message.reply(f'Предмет с таким ID: {shop_id} не найден')
    except ValueError:
        await message.reply('Введите коректный ID')
    
@router_root.message(F.text == 'Добавить предмет')
async def add_shop(message: types.Message, state: FSMContext):
    await message.answer('Введите название предмета')
    await state.set_state(AddShopStates.waiting_for_shop)

@router_root.message(AddShopStates.waiting_for_shop)
async def process_shop_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите категорию предмета:')
    await state.set_state(AddShopStates.waiting_for_shop_category)

@router_root.message(AddShopStates.waiting_for_shop_category)
async def process_shop_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer('Введите сколько стоит предмет: ')
    await state.set_state(AddShopStates.waiting_for_shop_points)


@router_root.message(AddShopStates.waiting_for_shop_points)
async def process_shop_pints(message: types.Message, state: FSMContext):
    try:
        points = int(message.text)
    except ValueError:
        await message.answer('Некорректное значение очков. Введите число.')
        return

    await state.update_data(points=points)
    data = await state.get_data()
    async with md.async_session() as session:
        new_shop = md.Shop(
            description=data['description'],
            category_id=data['category'],
            points=data['points']
        )
        session.add(new_shop)
        await session.commit()

    await message.answer("Предмет добавлен!")







