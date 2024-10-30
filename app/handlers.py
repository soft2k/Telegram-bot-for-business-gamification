import asyncio
from typing import List
from aiogram import Bot, Dispatcher, types,Router,F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
 
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import re
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

class RegisterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_phone_referals = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    async with async_session() as session:
        # Проверяем, есть ли пользователь в БД
        result = await session.execute(
            select(User).where(User.tg_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            await message.answer(f"👋 Добро пожаловать, {user.name}!",reply_markup=kb.main)
        else:
            await message.answer("Добро пожаловать! Для регистрации введите ваше имя:")
            await state.set_state(RegisterStates.waiting_for_name)

@router.message(RegisterStates.waiting_for_name)
async def cmd_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        text='Теперь поделись своим номером',
        reply_markup=kb.phone_kb
    )
    await state.set_state(RegisterStates.waiting_for_phone)

@router.message(RegisterStates.waiting_for_phone)
async def cmd_phone(message: types.Message, state: FSMContext):
    # Определяем номер телефона
    if message.contact:  # Если пользователь поделился контактом через кнопку
        phone = message.contact.phone_number
    else:  # Если пользователь ввел номер вручную
        phone = message.text

    # Сохраняем телефон в состояние
    await state.update_data(phone=phone)

    try:
        await message.answer(
            text='Введи номер друга и ему придут бонусы)',
            reply_markup=kb.referals
        )
        await state.set_state(RegisterStates.waiting_for_phone_referals)
        
    except Exception as e:
        print(f"Ошибка при сохранении телефона: {e}")
        await message.answer("Произошла ошибка при сохранении номера. Попробуйте еще раз.")

@router.message(RegisterStates.waiting_for_phone_referals)
async def processing_registr(message: types.Message, state: FSMContext):
    referral_phone = message.text
    state_data = await state.get_data()
    name = state_data.get('name')
    phone = state_data.get('phone')  # Получаем сохраненный ранее телефон

    async with async_session() as session:
        try:
            # Сначала создаем нового пользователя
            new_user = User(
                tg_id=message.from_user.id,
                name=name,
                phone=phone  # Используем сохраненный телефон
            )
            session.add(new_user)
            
            # Проверяем существование реферала
            if referral_phone:
                referral = await session.scalar(
                    select(User).where(User.phone == referral_phone)
                )
                if referral:
                    # Начисляем бонусы рефералу
                    referral.point += 100
                    referral.all_point += 100

            await session.commit()
            
            await message.answer(
                "Регистрация успешно завершена! Добро пожаловать!",
                reply_markup=kb.main
            )

        except Exception as e:
            print(f"Ошибка при регистрации: {e}")  # Добавлен вывод ошибки для отладки
            await session.rollback()
            await message.answer(
                "Произошла ошибка при регистрации. Попробуйте еще раз."
            )
        
        finally:
            await state.clear()



@router.message(F.text == 'Назад')
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать в СходкаБот!",reply_markup=kb.main)


    
#Хендлерс для пользователя

@router.message(F.text == 'Мой профиль')
async def my_profile(message: types.Message):
    user_info = await rq.profile(message.from_user.id)

    await message.answer(
        f"👤 Профиль пользователя:\n"
            f"Твой ID: {user_info['id']}\n"
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
        
        result = await session.execute(select(Task).where(Task.category_id == 1))
        tasks = result.scalars().all()


    if not tasks:
        await message.answer("На данный момент нет доступных заданий.")
        return

    builder = InlineKeyboardBuilder()
    for task in tasks:
        builder.button(text=f"{task.description} | {task.point}", callback_data=f"task_{task.id}")
    
    builder.adjust(1)  

    await message.answer("Выберите задание:", reply_markup=builder.as_markup())

    



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
        # Получаем задание
        result = await session.execute(select(Task).filter(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        # Получаем пользователя из базы данных
        user_result = await session.execute(
            select(User).filter(User.tg_id == callback_query.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if task and user:
            # Сохраняем нужные данные из task
            task_description = task.description
            task_point = task.point

            new_confirm = Confirm(
                tg_id=callback_query.from_user.id,
                name=user.name,  # Используем имя из базы данных
                description=task_description,
                points=task_point
            )
            session.add(new_confirm)
            await session.commit()

            await callback_query.answer(f"Вы выбрали задание: {task_description}")
            await callback_query.message.answer(f"Задание '{task_description}' ({task_point} points) добавлено в базу подтверждений. Ожидайте подтверждения администратором.")
        else:
            await callback_query.answer("Задание или пользователь не найдены.")


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
            shop_item = await session.execute(select(Shop).where(Shop.id == shop_id))
            shop_item = shop_item.scalar_one_or_none()

            if not shop_item:
                await callback.answer("Товар не найден.")
                return

            user = await session.execute(select(User).where(User.tg_id == user_id))
            user = user.scalar_one_or_none()

            if not user:
                await callback.answer("Пользователь не найден.")
                return

            if user.point >= shop_item.points:
                user.point -= shop_item.points
            
                await callback.message.answer(f"Вы успешно приобрели {shop_item.description}! Покажите это сообщение Админу, чтобы получить подарок!")
                
                await callback.answer()
            else:
                await callback.answer("У вас недостаточно очков для покупки этого товара.")

        
