#

import asyncio
import random
from typing import List
from aiogram import Bot, Dispatcher, types,Router,F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
from functools import wraps
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from sqlalchemy import select,desc,delete,update

from app.database.models import User,Task,Shop,Confirm,Achievement
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
    waiting_for_shop_description = State()

class DeleteShop(StatesGroup):
    waiting_number_delete = State()

class ConfrimOne(StatesGroup):
    waiting_number_confrim = State()

class ConfrimDeleteOne(StatesGroup):
     waiting_number_confrim_delete = State()

class BroadcastStates(StatesGroup):
    WAITING_FOR_CONTENT = State()
    CONFIRM_BROADCAST = State()




def is_admin():
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs):
            async with async_session() as session:
                # Проверяем права администратора
                result = await session.execute(
                    select(User).where(User.tg_id == message.from_user.id)
                )
                user = result.scalar_one_or_none()
                
                if not user or user.root != 1:
                    await message.answer("⚠️ У вас нет прав администратора!")
                    return
                return await func(message, *args, **kwargs)
        return wrapper
    return decorator

def is_admin_plus():
    def decorator(func):
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs):
            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.tg_id == message.from_user.id)
                )
                user = result.scalar_one_or_none()
                
                # Проверяем, есть ли пользователь и соответствует ли он требованиям
                if user is None or (user.tg_id != 195170570 and user.tg_id != 1249342160):
                    await message.answer("⚠️ У вас нет доступа!", reply_markup=kb.root)
                    return
                
                return await func(message, *args, **kwargs)

        return wrapper  # Возвращаем wrapper
    return decorator


@router_root.message(Command("root"))
@is_admin()
async def check_root(message: types.Message):
    await message.answer("Вы администратор!",reply_markup=kb.root)

@router_root.message(F.text == 'Назад')
@is_admin()
async def back_root(message: types.Message,state: FSMContext):
    await message.answer("Главное меню", reply_markup=kb.root)
    await state.clear()


@router_root.message(F.text == 'Редактировать задание')
@is_admin()
async def edit_task(message: types.Message, state: FSMContext):
    await message.answer('Выберите что будэ делать',reply_markup=kb.task_root)
    async with async_session() as session:
        result = await session.execute(select(Task))
        tasks = result.scalars().all()

        if tasks:
            task_list = 'Список заданий\n\n'
            for task in tasks:
                task_list += f"{task.id}. | {task.description} | Категория {task.category_id}\n"
        else:
            task_list = 'Список заданий пуст'
        await message.reply(task_list)

@router_root.message(F.text == 'Удалить все задание')
@is_admin()
async def delete_all_task(message: types.Message, state : FSMContext):
    async with async_session() as session:
        task = await session.execute(delete(Task))
        await session.commit()
    await message.answer('Все задание удалены',reply_markup=kb.root)
    await state.clear()

@router_root.message(F.text == 'Удалить задание')
@is_admin()
async def deleat_task(message: types.Message, state : FSMContext):
    await message.answer('Введите номер задание, которого хотите удалить')
    await state.set_state(DeleatTask.waiting_number_deleat)

@router_root.message(DeleatTask.waiting_number_deleat)
@is_admin()
async def processing_deleat_task(message: types.Message,state: FSMContext):
    try:
        task_id = int(message.text)
        async with async_session() as session:
            task = await session.get(Task, task_id)
            if task:
                await session.delete(task)
                await session.commit()
                await message.reply(f"Задание с {task_id} успешно удалён")
                await state.clear()
            else:
                await message.reply(f'Задание с таким ID: {task_id} не найден')
                await state.clear()
    except ValueError:
        await message.reply('Введите коректный ID')

    
@router_root.message(F.text == 'Добавить задание')
@is_admin()
async def add_tasks(message: types.Message, state: FSMContext):
    await message.answer('Введите название задания')
    await state.set_state(AddTaskStates.waiting_for_task)


@router_root.message(AddTaskStates.waiting_for_task)
@is_admin()
async def process_task_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите категорию задания:', reply_markup=kb.task_category)
    await state.set_state(AddTaskStates.waiting_for_task_category)


@router_root.message(AddTaskStates.waiting_for_task_category)
@is_admin()
async def process_task_category(message: types.Message, state: FSMContext):
    category_mapping = {
        "Ежедневное задание": 1,
        "Еженедельное задание": 7,
        "Ежемесячное задание": 30,
    }
    
    selected_category = message.text
    
    if selected_category in category_mapping:
        category_value = category_mapping[selected_category]
        await state.update_data(category=category_value)
        await message.answer('Введите количество очков за задание:')
        await state.set_state(AddTaskStates.waiting_for_task_points)
    else:
        await message.answer('Пожалуйста, выберите корректную категорию из предложенных.')


@router_root.message(AddTaskStates.waiting_for_task_points)
@is_admin()
async def process_task_points(message: types.Message, state: FSMContext):
    try:
        points = int(message.text)
    except ValueError:
        await message.answer('Некорректное значение очков. Введите число.')
        await state.clear()
        return

    await state.update_data(points=points)
    data = await state.get_data()
    async with md.async_session() as session:
        new_task = md.Task(
            description=data['description'],
            category_id=data['category'],
            point=data['points'],
            number=random.randint(0,99999)

        )
        session.add(new_task)
        await session.commit()

    await message.answer("Задача добавлена!")




#Магазин 

@router_root.message(F.text == 'Редактировать магазин')
@is_admin()
async def edit_shop(message: types.Message, state: FSMContext):
    await message.answer('Выберите что будэ делать',reply_markup=kb.shop_root)
    async with async_session() as session:
        result = await session.execute(select(Shop))
        tasks = result.scalars().all()

        if tasks:
            task_list = 'Список предметов\n\n'
            for task in tasks:
                task_list += f"{task.id}. | {task.description}\n"
        else:
            task_list = 'Список предметов пуст'
        await message.reply(task_list)

@router_root.message(F.text == 'Удалить все предметы')
@is_admin()
async def delete_all_shop(message: types.Message, state : FSMContext):
    async with async_session() as session:
        shop = await session.execute(delete(Shop))
        await session.commit()
    await message.answer('Все предметы удалены',reply_markup=kb.root)
    await state.clear()

@router_root.message(F.text == 'Удалить предмет')
@is_admin()
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
@is_admin()
async def processing_deleat_shop(message: types.Message,state: FSMContext):
    try:
        shop_id = int(message.text)
        async with async_session() as session:
            shop = await session.get(Shop, shop_id)
            if shop:
                await session.delete(shop)
                await session.commit()
                await message.reply(f"Предмет с {shop_id} успешно удалён")
                await state.clear()
            else:
                await message.reply(f'Предмет с таким ID: {shop_id} не найден')
    except ValueError:
        await message.reply('Введите коректный ID')
        await state.clear()
    
@router_root.message(F.text == 'Добавить предмет')
@is_admin()
async def add_shop(message: types.Message, state: FSMContext):
    await message.answer('Введите название предмета')
    await state.set_state(AddShopStates.waiting_for_shop_description)



@router_root.message(AddShopStates.waiting_for_shop_description)
@is_admin()
async def process_shop_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите сколько стоит предмет: ')
    await state.set_state(AddShopStates.waiting_for_shop_points)

@router_root.message(AddShopStates.waiting_for_shop_points)
@is_admin()
async def process_shop_pints(message: types.Message, state: FSMContext):
    try:
        points = int(message.text)
    except ValueError:
        await message.answer('Некорректное значение очков. Введите число.')
        await state.clear()
        return

    await state.update_data(points=points)
    data = await state.get_data()
    async with md.async_session() as session:
        new_shop = md.Shop(
            description=data['description'],  
            points=data['points']
        )
        session.add(new_shop)
        await session.commit()

    await message.answer("Предмет добавлен!")



@router_root.message(F.text == 'Подтвердить задание')
@is_admin()
async def confirm_task(message: types.Message, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Confirm))
        confrims = result.scalars().all()
        if confrims:
            confrim_list = 'Список потверждений\n\n'
            for confrim in confrims:
                confrim_list += f"{confrim.id} | {confrim.name}  | {confrim.category} | {confrim.description} | {confrim.points}\n"
        else:
            confrim_list = 'Список потверждений пуст'
        await  message.answer(confrim_list,reply_markup=kb.confirm_root)

@router_root.message(F.text == 'Подтвердить все')
@is_admin()
async def confrim_task(message: types.Message, state: FSMContext):
    await rq.confirm_all(message, state)
    await message.reply('Все задачи подтверждены')

@router_root.message(F.text == 'Удалить все')
@is_admin()
async def delete_all(message: types.Message, state: FSMContext):
    await rq.deleat_all_confrim()
    await message.reply('Все задачи удалены') 
    await state.clear()  

@router_root.message(F.text == 'Потвердить одно')
@is_admin()
async def confrim_task(message: types.Message, state: FSMContext):
    await message.answer('Введите номер потверждения, которого хотите потвердить')
    await state.set_state(ConfrimOne.waiting_number_confrim)


@router_root.message(ConfrimOne.waiting_number_confrim)
@is_admin()
async def processing_delete_confirm(message: types.Message, state: FSMContext):
        await rq.confrim_one(message, state)



@router_root.message(F.text == 'Удалить одно')
@is_admin()
async def confrim_task(message: types.Message, state: FSMContext):
    await message.answer('Введите номер потверждения, которого хотите удалить')
    await state.set_state(ConfrimDeleteOne.waiting_number_confrim_delete)

@router_root.message(ConfrimDeleteOne.waiting_number_confrim_delete)
@is_admin()
async def processing_delete_confirm(message: types.Message, state: FSMContext):
        await rq.confrim_delete_one(message, state)
        await state.clear()

@router_root.message(F.text == 'Отправить рассылку')
@is_admin()
async def start_broadcast(message: types.Message, state: FSMContext):
    await message.answer("Отправьте текст и/или фото для рассылки. Когда закончите, нажмите /done", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(BroadcastStates.WAITING_FOR_CONTENT)
    await state.update_data(content=[])

@router_root.message(BroadcastStates.WAITING_FOR_CONTENT)
@is_admin()
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
@is_admin()
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

class AchievementForm(StatesGroup):
    category = State()
    name = State()
    description = State()
    points = State()
    photo = State()

@router_root.message(F.text == 'Редактировать ачивки')
@is_admin()
async def edit_shop(message: types.Message, state: FSMContext):
    await message.answer('Выберите что будэ делать',reply_markup=kb.ach_root)
    async with async_session() as session:
        result = await session.execute(select(Achievement))
        tasks = result.scalars().all()

        if tasks:
            task_list = 'Список ачивок\n\n'
            for task in tasks:
                task_list += f"{task.id}. | {task.category_id} | {task.description} \n"
        else:
            task_list = 'Список ачивок пуст'
        await message.reply(task_list)
 
class DeleatAch(StatesGroup):
    waiting_number_deleat = State()

@router_root.message(F.text == 'Удалить ачивку')
@is_admin()
async def deleat_task(message: types.Message, state : FSMContext):
    await rq.delete_one_ach(message,state)
    await message.answer('Введите номер ачивки, которого хотите удалить')
    await state.set_state(DeleatAch.waiting_number_deleat)

@router_root.message(DeleatAch.waiting_number_deleat)
@is_admin()
async def processing_deleat_task(message: types.Message,state: FSMContext):
    try:
        ach_id = int(message.text)
        async with async_session() as session:
            ach = await session.get(Achievement, ach_id)
            if ach:
                await session.delete(ach)
                await session.commit()
                await message.reply(f"Ачивка с {ach_id} успешно удалён")
                await state.clear()
            else:
                await message.reply(f'Ачивка с таким ID: {ach_id} не найден')
    except ValueError:
        await message.reply('Введите коректный ID')
        await state.clear()

@router_root.message(F.text == 'Удалить все ачивки')
@is_admin()
async def deleat_all(message: types.Message, state: FSMContext):
    await rq.deleat_all_confrim_ach()
    await message.answer('Вы удалили все ачивки!')
    await state.clear()



@router_root.message(F.text == 'Добавить ачивку')
async def cmd_add_achievement(message: types.Message, state: FSMContext):

    await message.reply("Давайте добавим новую ачивку. Введите категорию:")
    await state.set_state(AchievementForm.category)

@router_root.message(AchievementForm.category)
async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.reply("Теперь введите название ачивки:")
    await state.set_state(AchievementForm.name)

@router_root.message(AchievementForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Введите описание ачивки:")
    await state.set_state(AchievementForm.description)

@router_root.message(AchievementForm.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.reply("Введите количество поинтов за эту ачивку:")
    await state.set_state(AchievementForm.points)

@router_root.message(AchievementForm.points)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(points=message.text)
    await message.reply("Теперь скиньте фото:")
    await state.set_state(AchievementForm.photo)

# Остальной код остается без изменений
@router_root.message(AchievementForm.photo)
async def process_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.reply("Пожалуйста, отправьте фото.")
        return
    
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(photo=file_id)

    data = await state.get_data()
    
    async with async_session() as session: 
        async with session.begin():  
            new_achievement = Achievement(
                category_id=data['category'],
                name=data['name'],
                description=data['description'],
                points=data['points'],
                photo=data['photo']
            )
            session.add(new_achievement)
            await session.commit()

    await message.reply("Ачивка успешно добавлена!")
    await state.clear()

class ConfirmVisitStates(StatesGroup):
    waiting_for_ids = State()
    waiting_for_stop_check_ids = State()
    waiting_for_hourly_rate_ids = State()

@router_root.message(F.text == 'Подтвердить посещение')
@is_admin()
async def cmd_confirm_visit(message: types.Message, state: FSMContext):
    await message.answer("Выберите категорию:",reply_markup=kb.visit_categories)


@router_root.message(F.text == 'Стоп-чек')
@is_admin()
async def cmd_stop_check(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователей через запятую для начисления посещений и поинтов:")
    await state.set_state(ConfirmVisitStates.waiting_for_stop_check_ids)

@router_root.message(ConfirmVisitStates.waiting_for_stop_check_ids)
@is_admin()
async def process_stop_check_ids(message: types.Message, state: FSMContext, bot: Bot):
    user_ids = message.text.split(',')
    user_ids = [user_id.strip() for user_id in user_ids]  # Удаление пробелов

    async with async_session() as session:  # Переместили async with сюда
        for user_id in user_ids:
            try:
                user_id_int = int(user_id)  # Преобразуем ID в число
                # Получаем пользователя из БД
                stmt = select(User).where(User.id == user_id_int)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    # Обновляем значения
                    user.visit += 1
                    points_awarded = 100  # Сохраняем количество начисленных поинтов
                    user.point += points_awarded
                    user.all_point += points_awarded

                    # Проверяем статус для кешбека
                    if user.status in ['Уважаемый', 'Адепт', 'Амбассадор']:
                        cashback = 0.2 * points_awarded  # 20% от начисленных поинтов
                        user.point += cashback
                        user.all_point += cashback
                        points_awarded+= cashback

                    if user.referral == 1:
                        referral_stmt = select(User).where(User.phone == user.phoneReferral)
                        referral_result = await session.execute(referral_stmt)
                        referral_user = referral_result.scalar_one_or_none()
                        if referral_user:  # Проверяем, существует ли реферальный пользователь
                            referral_user.point += 200
                            referral_user.all_point += 200
                            user.point += 200
                            user.all_point += 200
                            user.referral -= 1
                            user.phoneReferral = '0'  # Исправлено на присваивание
                    await bot.send_message(
                        chat_id=user.tg_id,  # Предполагается, что у пользователя есть tg_id
                        text=f"Поздравляем! Вам начислено {points_awarded} поинтов за стоп-чек! 🏆\n\n"
                             f"💎 Общее количество поинтов: {user.all_point}."
                    )
                    # Сохраняем изменения
                    await session.commit()

                else:
                    await message.answer(f"Пользователь с ID {user_id} не найден.")
            except ValueError:
                await message.answer(f"ID {user_id} некорректен. Убедитесь, что это число.")
            except Exception as e:
                await message.answer(f"Ошибка при обновлении пользователя с ID {user_id}: {str(e)}")

    await message.answer("Посещения и поинты успешно обновлены.")
    await state.clear()


@router_root.message(F.text == 'Почасовка')
@is_admin()
async def cmd_hourly_rate(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователей и количество часов через запятую в формате: ID1, часы1; ID2, часы2;\nНапример: 10,2;15,3 ")
    await state.set_state(ConfirmVisitStates.waiting_for_hourly_rate_ids)

@router_root.message(ConfirmVisitStates.waiting_for_hourly_rate_ids)
@is_admin()
async def process_hourly_rate_ids(message: types.Message, state: FSMContext, bot: Bot):
    entries = message.text.split(';')  
    for entry in entries:
        try:
            user_id, hours_str = entry.split(',')
            user_id = int(user_id.strip())
            hours = int(hours_str.strip())
            points_awarded = hours * 25
            if hours < 0:
                await message.answer(f"Количество часов не может быть отрицательным для пользователя с ID {user_id}.")
                continue
            
            async with async_session() as session:
                stmt = select(User).where(User.id == user_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                

                if user:
                    user.visit += 1
                    user.point += hours * 25
                    user.all_point += hours * 25

                    # Проверяем статус для кешбека
                    if user.status in ['Уважаемый', 'Адепт', 'Амбассадор']:
                        cashback = 0.2 * (hours * 25)  # 20% от начисленных поинтов
                        user.point += cashback
                        user.all_point += cashback
                        points_awarded += cashback

                    if user.referral == 1:
                        referral_stmt = select(User).where(User.phone == user.phoneReferral)
                        referral_result = await session.execute(referral_stmt)
                        referral_user = referral_result.scalar_one_or_none()
                        
                        if referral_user:  # Проверяем, существует ли реферальный пользователь
                            referral_user.point += 200
                            referral_user.all_point += 200
                            user.point += 200
                            user.all_point += 200
                            user.referral -= 1
                            user.phoneReferral = '0'  # Исправлено на присваивание
                    await bot.send_message(
                        chat_id=user.tg_id,  # Предполагается, что у пользователя есть tg_id
                        text=f"🎉 Поздравляем! 🌟\n" \
                             f"Вам начислено {points_awarded} поинтов за посещение! 🏆\n\n" \
                             f"💎 Общее количество поинтов: {user.all_point}"
                    )
                    await session.commit()  # Здесь мы коммитим изменения
                    await message.answer(f"Пользователь с ID {user_id} получил {points_awarded} поинтов.")
                else:
                    await message.answer(f"Пользователь с ID {user_id} не найден.")
        except ValueError:
            await message.answer(f"Ошибка в формате ввода для записи '{entry}'. Убедитесь, что это число.")
        except Exception as e:
            await message.answer(f"Ошибка при обновлении пользователя с ID {user_id}: {str(e)}")

    await message.answer("Поинты успешно обновлены.")
    await state.clear()





# @router_root.message(ConfirmVisitStates.waiting_for_ids)
# @is_admin()
# async def process_visit_confirmation(message: types.Message, state: FSMContext):
#     user_ids = [id.strip() for id in message.text.split(',')]
    
#     async with async_session() as session:
#         confirmed_users = []
#         not_found_users = []
        
#         for user_id in user_ids:
#             try:
#                 user_id = int(user_id)
#                 result = await session.execute(select(User).where(User.id == user_id))  
#                 user = result.scalar_one_or_none()
                
#                 if user:
#                     await session.execute(
#                         update(User).
#                         where(User.id == user_id).  
#                         values(visit=User.visit + 1,
#                                point=User.point + 10,
#                                all_point=User.all_point + 10)
#                     )
#                     confirmed_users.append(user_id)
#                 else:
#                     not_found_users.append(user_id)
#             except ValueError:
#                 not_found_users.append(user_id)
        
#         await session.commit()
    
#     response = "Посещение подтверждено для пользователей: " + ", ".join(map(str, confirmed_users)) if confirmed_users else "Ни одного пользователя не подтверждено."
#     if not_found_users:
#         response += f"\nНе найдены пользователи с ID: {', '.join(map(str, not_found_users))}"
    
#     await message.answer(response)
#     await state.clear()


class AdminPlus(StatesGroup):
    waiting_add_admin = State()
    waiting_cancel_admin = State()


@router_root.message(F.text == 'Редактировать админов')
@is_admin_plus()
async def edit_admins(message: types.Message, state: FSMContext):
    await message.answer('Выберите действие', reply_markup=kb.root_menu)
    
    async with async_session() as session:
        try:
            result = await session.execute(select(User).where(User.root == 1))
            admins = result.scalars().all()

            if admins:
                # Используем list comprehension для создания списка
                admins_list = "Список админов:\n\n" + "\n".join(
                    f"{admin.id}. | {admin.name}" for admin in admins
                )
            else:
                admins_list = 'Список админов пуст'
            
            await message.reply(admins_list)
        
        except Exception as e:
            # Обработка возможных исключений
            await message.reply(f"Ошибка при получении списка администраторов: {str(e)}")
        finally:
            # Закрываем сессию 
            await session.close()
        


@router_root.message(F.text == 'Дать админку')
@is_admin_plus()
async def edit_admins_add(message: types.Message, state: FSMContext):
    await state.set_state(AdminPlus.waiting_add_admin)
    await message.answer('Введите ID пользователя, которому хотите дать админку:')

@router_root.message(AdminPlus.waiting_add_admin)
@is_admin_plus()
async def process_add_admin(message: types.Message, state: FSMContext):
    user_id = message.text.strip()  # Изменяем название переменной на user_id
    async with async_session() as session:
        # Проверяем, существует ли пользователь с таким id
        result = await session.execute(select(User).where(User.id == user_id))  # Изменяем tg_id на id
        user = result.scalar_one_or_none()

        if user:
            # Обновляем поле root для данного пользователя
            await session.execute(update(User).where(User.id == user_id).values(root=True))  # Изменяем tg_id на id
            await session.commit()
            await message.answer(f'Пользователь с ID {user_id} теперь администратор.')
        else:
            await message.answer(f'Пользователь с ID {user_id} не найден.')

        await state.clear()

@router_root.message(F.text == 'Снять админку')
@is_admin_plus()
async def edit_admins_cancel(message: types.Message, state: FSMContext):
    await state.set_state(AdminPlus.waiting_cancel_admin)
    await message.answer('Введите ID пользователя, у которого хотите снять админку:')  # Изменяем текст запроса

@router_root.message(AdminPlus.waiting_cancel_admin)
@is_admin_plus()
async def process_cancel_admin(message: types.Message, state: FSMContext):
    user_id = message.text.strip()  # Изменяем название переменной на user_id
    async with async_session() as session:
        # Проверяем, существует ли пользователь с таким id
        result = await session.execute(select(User).where(User.id == user_id))  # Изменяем tg_id на id
        user = result.scalar_one_or_none()

        if user:
            # Обновляем поле root для данного пользователя
            await session.execute(update(User).where(User.id == user_id).values(root=False))  # Изменяем tg_id на id
            await session.commit()
            await message.answer(f'Админка у пользователя с ID {user_id} снята.')
        else:
            await message.answer(f'Пользователь с ID {user_id} не найден.')

        await state.clear()

@router_root.message(F.text == 'Редактировать пользователей')
@is_admin()
async def edit_users(message: types.Message, state: FSMContext):
    await message.answer('Выберите действие', reply_markup=kb.edit_users)
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        if users:
            user_list = 'Список пользователей\n\n'
            for user in users:
                user_list += f"{user.id}. | {user.name}\n"
        else:
            user_list = 'Список пользователей пуст'
        await message.reply(user_list)


class UserStatusEdit(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_new_status = State()

@router_root.message(F.text == 'Редактировать статус')
@is_admin()
async def edit_user_status(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователя:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(UserStatusEdit.waiting_for_user_id)

@router_root.message(UserStatusEdit.waiting_for_user_id)
@is_admin()
async def process_user_id(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    
    async with async_session() as session:
        # Проверяем, существует ли пользователь с таким ID
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if user:
            await state.update_data(user_id=user.id)  # Сохраняем ID пользователя в состоянии
            await message.answer("Выберите новый статус:", reply_markup=kb.status)
            await state.set_state(UserStatusEdit.waiting_for_new_status)
        else:
            await message.answer("Пользователь с таким ID не найден. Попробуйте снова.")
            await state.clear()

@router_root.message(UserStatusEdit.waiting_for_new_status)
@is_admin()
async def process_new_status(message: types.Message, state: FSMContext):
    new_status = message.text.strip()

    # Проверяем, является ли статус допустимым
    valid_statuses = ['Базовичок', 'Уважаемый', 'Адепт', 'Амбассадор']
    if new_status not in valid_statuses:
        await message.answer("Недопустимый статус. Пожалуйста, выберите один из предложенных статусов.")
        return

    user_data = await state.get_data()
    user_id = user_data.get('user_id')

    async with async_session() as session:
        # Обновляем статус пользователя в базе данных
        await session.execute(
            update(User).where(User.id == user_id).values(status=new_status)
        )
        await session.commit()

    await message.answer(f"Статус пользователя с ID {user_id} успешно обновлен на '{new_status}'.",reply_markup=kb.root)
    await state.clear()

class UserPointEdit(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_edit_points = State()

@router_root.message(F.text == 'Редактировать поинты')
@is_admin()
async def edit_points(message: types.Message, state: FSMContext):
    await message.answer("Введите ID пользователя и количество поинтов (например: 123 +50 или 123 -100):")
    await state.set_state(UserPointEdit.waiting_for_user_id)


@router_root.message(UserPointEdit.waiting_for_user_id)
async def process_user_id(message: types.Message, state: FSMContext):

            user_id, points_change = message.text.split()
            user_id = int(user_id)
            points_change = int(points_change)

            # Используем async_session для создания сессии
            async with async_session() as session:        
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalars().first()

                if user is None:
                    await message.answer("Пользователь не найден.")
                    await state.clear()
                    return

                # Обновляем количество поинтов
                user.point += points_change

                # Сохраняем изменения в базе данных
                await session.commit()

                await message.answer(f"Поинты пользователя {user.name} обновлены на {points_change}. Текущие поинты: {user.point}.")
                await state.clear()

