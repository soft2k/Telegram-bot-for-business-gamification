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

from app.database.models import User,Task,Shop,Confirm
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

class DeleteShop(StatesGroup):
    waiting_number_delete = State()

class ConfrimOne(StatesGroup):
    waiting_number_confrim = State()

class ConfrimDeleteOne(StatesGroup):
     waiting_number_confrim_delete = State()

class BroadcastStates(StatesGroup):
    WAITING_FOR_CONTENT = State()
    CONFIRM_BROADCAST = State()





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
    await state.set_state(DeleteShop.waiting_number_delete)

@router_root.message(DeleteShop.waiting_number_delete)
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



@router_root.message(F.text == 'Подтвердить задание')
async def confirm_task(message: types.Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Confirm))
        confrims = result.scalars().all()
        if confrims:
            confrim_list = 'Список потверждений"\n\n'
            for confrim in confrims:
                confrim_list += f"{confrim.id} | {confrim.name} | {confrim.description} | {confrim.points}\n"
        else:
            confrim_list = 'Список заданий пуст'
        await  message.answer(confrim_list,reply_markup=kb.confirm_root)

@router_root.message(F.text == 'Подтвердить все')
async def confrim_task(message: types.Message, state: FSMContext):
    await rq.confirm_all()
    await message.reply('Все задачи потверждены')

@router_root.message(F.text == 'Удалить все')
async def delete_all(message: types.Message, state: FSMContext):
    await rq.deleat_all_confrim()
    await message.reply('Все задачи удалены')

@router_root.message(F.text == 'Потвердить одно')
async def confrim_task(message: types.Message, state: FSMContext):
    await message.answer('Введите номер потверждения, которого хотите удалить')
    await state.set_state(ConfrimOne.waiting_number_confrim)


@router_root.message(ConfrimOne.waiting_number_confrim)
async def processing_delete_confirm(message: types.Message, state: FSMContext):
        await rq.confrim_one(message, state)



@router_root.message(F.text == 'Удалить одно')
async def confrim_task(message: types.Message, state: FSMContext):
    await message.answer('Введите номер потверждения, которого хотите удалить')
    await state.set_state(ConfrimDeleteOne.waiting_number_confrim_delete)

@router_root.message(ConfrimDeleteOne.waiting_number_confrim_delete)
async def processing_delete_confirm(message: types.Message, state: FSMContext):
        await rq.confrim_delete_one(message, state)

@router_root.message(F.text == 'Отправить рассылку')
async def start_broadcast(message: types.Message, state: FSMContext):
    await message.answer("Отправьте текст и/или фото для рассылки. Когда закончите, нажмите /done", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(BroadcastStates.WAITING_FOR_CONTENT)
    await state.update_data(content=[])

@router_root.message(BroadcastStates.WAITING_FOR_CONTENT)
async def process_broadcast_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    content = data.get('content', [])
    
    if message.text == "/done":
        if not content:
            await message.answer("Вы не отправили никакого контента. Рассылка отменена.")
            await state.clear()
        else:
            await message.answer("Вот содержимое вашей рассылки. Отправить? (да/нет)")
            for item in content:
                if item['type'] == 'text':
                    await message.answer(item['content'])
                elif item['type'] == 'photo':
                    await message.reply_photo(item['content'])
            await state.set_state(BroadcastStates.CONFIRM_BROADCAST)
    else:
        if message.text:
            content.append({'type': 'text', 'content': message.text})
        elif message.photo:
            content.append({'type': 'photo', 'content': message.photo[-1].file_id})
        await state.update_data(content=content)
        await message.answer("Контент добавлен. Продолжайте отправку или нажмите /done когда закончите.")

@router_root.message(BroadcastStates.CONFIRM_BROADCAST)
async def confirm_broadcast(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        data = await state.get_data()
        content = data.get('content', [])
        
        async with async_session() as session:
            result = await session.execute(select(User.tg_id))
            user_ids = [row[0] for row in result]

        for user_id in user_ids:
            for item in content:
                if item['type'] == 'text':
                    await message.bot.send_message(user_id, item['content'])
                elif item['type'] == 'photo':
                    await message.bot.send_photo(user_id, item['content'])

        await message.answer("Рассылка отправлена всем пользователям!", reply_markup=kb.root)
    else:
        await message.answer("Рассылка отменена.", reply_markup=kb.root)
    await state.clear()





