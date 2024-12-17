import asyncio
import random
import os
from aiogram.types import Message
from typing import List
from aiogram import Bot, Dispatcher, types,Router,F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
import aiogram 
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup,CallbackQuery,FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.future import select
from sqlalchemy import select,desc,and_
from app.database.models import async_session
from app.database.models import User,Task,Shop,Confirm,Achievement
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.orm import sessionmaker, declarative_base
import app.database.models as md
import app.database.requests as rq
import app.keybord as kb
import app.root as rt
from functools import wraps

router = Router()


def is_test():
    def decorator(func):
        @wraps(func)
        async def wrapper(callback: CallbackQuery, *args, **kwargs):
            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.tg_id == callback.from_user.id)
                )
                user = result.scalar_one_or_none()
                
                # Проверяем, есть ли пользователь и соответствует ли он требованиям
                if user is None or (user.tg_id != 195170570 and user.tg_id != 1249342160):
                    await callback.answer("⚠️Сейчас в разработке⚠️")
                    return
            return await func(callback, *args, **kwargs)
        return wrapper
    return decorator


main_text = (
    "Добро пожаловать в мир возможностей!\n\n"
    "Я ваш личный помощник, и здесь вы можете:\n\n"
    "👤 Мой профиль\n"
    "Посмотреть и обновить информацию о себе, узнать свои достижения и статистику!\n"
    "📝 Задание\n"
    "Получить новые задания и выполнить их, чтобы заработать поинты и награды!\n"
    "🏆 Ачивки\n"
    "Откройте для себя свои достижения и посмотрите, какие награды вы можете получить!\n"
    "📊 Лидерборд\n"
    "Сравните свои результаты с другими участниками и узнайте, кто на вершине!\n"
    "🛒 Магазин\n"
    "Загляните в магазин, чтобы потратить свои поинты на уникальные предметы и улучшения!\n\n"
    "Выберите опцию, нажав на соответствующую кнопку, и начните свое приключение!"
)

class ConfrimDay(StatesGroup):
    waiting_for_confrim = State

class RegisterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_phone_referals = State()
    waiting_for_channel_subscription = State()


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    async with async_session() as session:
       
        result = await session.execute(
            select(User).where(User.tg_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            await message.answer(main_text,reply_markup=kb.keybord_main)
        else:
            await message.answer(
    "Добро пожаловать! Для регистрации введите ваше имя и фамилию:\n"
    "Просим не вводить никнеймы, это важно для идентификации ачивок.\n"
    "В противном случае аккаунт будет аннулирован."
)
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
    if message.contact:  
        phone = message.contact.phone_number
    else: 
        phone = message.text


    def normalize_phone(phone):
        phone = re.sub(r'\D', '', phone)
      
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        
     
        if not phone.startswith('7'):
            phone = '7' + phone
        

        return '+' + phone


    normalized_phone = normalize_phone(phone)


    if len(normalized_phone) != 12:
        await message.answer("Пожалуйста, введите корректный номер телефона в формате +7XXXXXXXXXX.")
        return

    await state.update_data(phone=normalized_phone)

    try:
        await message.answer(
           text = (
    "✨ Введите номер друга, который пригласил вас к нам! ✨\n"
    "🎉 После вашего первого визита на Сходку мы начислим вам 200 бонусов! 🎉\n"
    "Введите номер в формате: +7XXXXXXXXXX"
),
            reply_markup=kb.referals
        )
        await state.set_state(RegisterStates.waiting_for_phone_referals)
        
    except Exception as e:
        print(f"Ошибка при сохранении телефона: {e}")
        await message.answer("Произошла ошибка при сохранении номера. Попробуйте еще раз.")

@router.message(RegisterStates.waiting_for_phone_referals)
async def processing_registr(message: types.Message, state: FSMContext, bot: Bot):
    referral_phone = message.text.strip()  # Удаляем лишние пробелы
    state_data = await state.get_data()
    name = state_data.get('name')
    phone = state_data.get('phone')  

    # Приведение номера телефона к формату +7
    if referral_phone.startswith('7'):
        referral_phone = '+7' + referral_phone[1:]  # Заменяем первую цифру 7 на +7
    elif referral_phone.startswith('8'):
        referral_phone = '+7' + referral_phone[1:]  # Заменяем первую цифру 8 на +7
    elif not referral_phone.startswith('+'):
        referral_phone = '+7' + referral_phone  # Если номер не начинается с +, добавляем +7

    async with async_session() as session:
        try:
            new_user = User(
                tg_id=message.from_user.id,
                name=name,
                phone=phone,
                phoneReferral=referral_phone  
            )
            session.add(new_user)
            
            if referral_phone:
                referral = await session.scalar(
                    select(User).where(User.phone == referral_phone)
                )
                user = await session.scalar(
                    select(User).where(User.tg_id == new_user.tg_id)
                )

                if referral:  # Проверяем, найден ли реферал
                    # Увеличиваем значение referral на 1
                    user.referral += 1
                    
                    # Уведомление рефералу
                    await bot.send_message(
                        chat_id=referral.tg_id,  # Предполагается, что у реферала есть tg_id
                        text=f"Поздравляем! По вашему номеру зарегистрировался новый пользователь.\nПри первом визите вашего друга вы получите 200 очков."
                    )
            
            await session.commit()  # Сохраняем изменения в БД
            
            # Предложение подписаться на канал
            await state.set_state(RegisterStates.waiting_for_channel_subscription)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")],
                [InlineKeyboardButton(text="Пропустить", callback_data="skip_subscription")]
            ])
            await message.answer(
                "Отлично! Теперь, пожалуйста, подпишитесь на наш Telegram канал @shodka_tmn и нажмите 'Проверить подписку'.",
                reply_markup=keyboard
            )

        except Exception as e:
            print(f"Ошибка при регистрации: {e}") 
            await session.rollback()
            await message.answer(
                "Произошла ошибка при регистрации. Попробуйте еще раз."
            )
            await state.clear()

@router.callback_query(lambda c: c.data in ["check_subscription", "skip_subscription"])
async def process_subscription(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback_query.data == "check_subscription":
        # Проверка подписки на канал
        chat_member = await bot.get_chat_member(chat_id='@shodka_tmn', user_id=callback_query.from_user.id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            async with async_session() as session:
                try:
                    user = await session.scalar(
                        select(User).where(User.tg_id == callback_query.from_user.id)
                    )
                    if user:
                        user.point += 10
                        user.all_point += 10
                        await session.commit()
                    
                    await callback_query.answer("Вы успешно подписались и получили 10 очков!")
                except Exception as e:
                    print(f"Ошибка при обновлении очков: {e}")
                    await session.rollback()
                    await callback_query.answer("Произошла ошибка. Попробуйте еще раз.")
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")],
                [InlineKeyboardButton(text="Пропустить", callback_data="skip_subscription")]
            ])
            await callback_query.message.edit_text(
                "Вы не подписались на канал. Пожалуйста, подпишитесь и нажмите 'Проверить подписку' снова. @shodka_tmn",
                reply_markup=keyboard
            )
            return

    else:
        await callback_query.answer("Вы пропустили подписку.")

    await state.clear()
    await callback_query.message.edit_text(
        main_text,
        reply_markup=kb.keybord_main
    )


@router.callback_query(F.data == 'back_to_main')
async def back_to_main_menu(callback: types.CallbackQuery):
    # Option 1: Delete the previous message if necessary
    await callback.message.delete()  # Delete the previous message

    # Send a new message with the main menu
    await callback.message.answer(main_text, reply_markup=kb.keybord_main)

    
#Хендлерс для пользователя

@router.callback_query(F.data == 'my_profile')
async def my_profile(callback: CallbackQuery):
    user_info = await rq.profile(callback.from_user.id)

    # Создаем новую клавиатуру
    keyboard = [
        [InlineKeyboardButton(text="Мои достижения", callback_data="my_achievements")],
        [kb.back_to_main.inline_keyboard[0][0]]  # Кнопка "Назад"
    ]

    # Удаляем предыдущее сообщение, если оно существует
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    # Объединяем текст сообщения в одну строку
    profile_text = (
        f"👤 Профиль пользователя:\n"
        f"Твой ID: {user_info['id']}\n"
        f"Имя: {user_info['name']}\n"
        f"Статус:{user_info['status']}\n"
        f"Баланс поинтов: {user_info['points']}\n"
        f"Всего поинтов заработано: {user_info['all_point']}\n"
        f"Выполненные задания: {user_info['tasks']}\n"
        f"Уровень: {user_info['level']}\n"
        f"Кол-во посещений: {user_info['visit']}\n"
    )

    await callback.message.answer(
        profile_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

class ReviewStates(StatesGroup):
    waiting_for_review = State()

#Отзыв



@router.callback_query(F.data == 'review')
async def process_review(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Мы хотим услышать вас!\n"
                                    "Оставьте отзыв о нашем сервисе и расскажите, что вам понравилось или что можно улучшить. Ваши мысли помогут нам стать лучше.\n"
                                    "✉️ Чтобы отправить отзыв, просто напишите сообщение в этот чат. Ваш отзыв будет отправлен прямо боссу, и мы обязательно его учтем!\n"
                                    "Спасибо за ваше время! 🙏",reply_markup=kb.back_to_main)
    await state.set_state(ReviewStates.waiting_for_review)    

@router.message(ReviewStates.waiting_for_review)
async def handle_review(message: Message, state: FSMContext):
    async with async_session() as session:
        try:
            result = await session.execute(
                select(User).where(User.tg_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()

            # Отправляем отзыв конкретному пользователю
            await message.bot.send_message(
                chat_id=1249342160, 
                text=f"🌟 Новый отзыв!\n\n"
                     f"От пользователя: {user.name}\n"
                     f"ID пользователя: {user.id}\n\n"
                     f"Текст отзыва:\n"
                     f"{message.text}"
            )
            await message.bot.send_message(
                chat_id=195170570, 
                text=f"🌟 Новый отзыв!\n\n"
                     f"От пользователя: {user.name}\n"
                     f"ID пользователя: {user.id}\n\n"
                     f"Текст отзыва:\n"
                     f"{message.text}"
            )
            
            # Подтверждаем получение отзыва
            await message.answer(
                "Спасибо за ваш отзыв! Мы внимательно его изучим.", 
                reply_markup=kb.back_to_main
            )
            
            # Сбрасываем состояние
            await state.clear()
        
        except Exception as e:
            # Обработка возможных ошибок
            await message.answer(
                "Извините, произошла ошибка при отправке отзыва. Попробуйте позже.", 
                reply_markup=kb.back_to_main
            )
            await state.clear()
            print(f"Ошибка при отправке отзыва: {e}")           




@router.callback_query(F.data == 'my_achievements')
async def my_achievements(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.tg_id == callback.from_user.id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            await callback.answer("Пользователь не найден.")
            return
        

       

      
        achievements = await session.execute(
            select(Achievement).where(Achievement.id.in_(user.completed_tasks))
        )
        achievements = achievements.scalars().all()
        
        keyboard = []  
        
        if not achievements:
            text = "У вас пока нет достижений."
        else:
            text = "🏆 Ваши достижения:\n\n"
            for achievement in achievements:
                text += f"{achievement.id} | {achievement.name}: {achievement.description}\n"
                text += f"Очки: {achievement.points}\n\n"
                keyboard.append([InlineKeyboardButton(text=f"{achievement.id}", callback_data=f"achievement_info_{achievement.id}")])
        
        keyboard.append([InlineKeyboardButton(text="Назад в профиль", callback_data="my_profile")])

        
        try:
            await callback.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")

        
        await callback.message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        

@router.callback_query(F.data.startswith('achievement_info_'))
async def show_achievement_details(callback: CallbackQuery):
    achievement_id = int(callback.data.split('_')[-1])
    async with async_session() as session:
        result = await session.execute(
            select(Achievement).where(Achievement.id == achievement_id)
        )
        achievement = result.scalar_one_or_none()
        
        if achievement:
            keyboard = [
                [
                    InlineKeyboardButton(
                        text="◀️ Назад в профиль",
                        callback_data="my_profile"
                    )
                ]
            ]
            
            text = f"🏆 Ачивка: {achievement.name}\n"
            text += f"📑 Категория: {achievement.category_id}\n"
            text += f"📝 Описание: {achievement.description}\n"
            text += f"💎 Поинты: {achievement.points}"
            
            if achievement.photo:
                # Удаляем предыдущее сообщение, если оно существует
                try:
                    await callback.message.delete()
                except Exception as e:
                    print(f"Ошибка при удалении сообщения: {e}")

                await callback.message.answer_photo(
                    photo=achievement.photo,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            else:
                # Удаляем предыдущее сообщение, если оно существует
                try:
                    await callback.message.delete()
                except Exception as e:
                    print(f"Ошибка при удалении сообщения: {e}")

                await callback.message.answer(
                    text=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )



@router.callback_query(F.data == 'task_')
async def my_profile(callback: CallbackQuery):
    keybord = InlineKeyboardMarkup(inline_keyboard=kb.task)
    await callback.message.edit_text("Меню заданий\n\n"
        "Добро пожаловать в раздел заданий! Здесь вы можете выбрать задания, которые помогут вам заработать поинты и достичь новых высот!\n\n"
        "📅 Ежедневные задания - Выполняйте простые задания каждый день, чтобы получать бонусы и не упустить возможность заработать дополнительные поинты!\n"
        "📆 Еженедельные задания - Более сложные задачи, которые нужно выполнить в течение недели. За успешное выполнение вы получите значительные награды!\n"
        "📅 Ежемесячные задания - Самые масштабные и интересные задания, которые открываются раз в месяц. Успейте выполнить их, чтобы получить эксклюзивные награды!\n\n"
        "✨ Выберите тип задания, нажав на соответствующую кнопку, и начните зарабатывать поинты уже сегодня!",reply_markup=keybord)




async def get_tasks():
    async with async_session() as session:
        result = await session.execute(select(Task).where(Task.id == 1))
        tasks = result.scalars().all()
        return tasks


@router.callback_query(F.data == "task_1")
async def show_tasks(callback: CallbackQuery):
    await display_tasks(callback, category_id=1)

@router.callback_query(F.data == "task_7")
async def show_tasks(callback: CallbackQuery):
    await display_tasks(callback, category_id=7)

@router.callback_query(F.data == "task_30")
async def show_tasks(callback: CallbackQuery):
    await display_tasks(callback, category_id=30)

async def display_tasks(callback: CallbackQuery, category_id: int):
    async with async_session() as session:
        query = select(Task).where(Task.category_id == category_id)
        result = await session.execute(query)
        tasks = result.scalars().all()

        if not tasks:
            await callback.answer("Нет доступных ежедневных заданий.", show_alert=True)
            return

        # Формируем текст с заданиями
        tasks_text = "\n".join(f"{task.id}. {task.description} ({task.point} баллов)" for task in tasks)

        task_buttons = []
        for task in tasks:
            button = InlineKeyboardButton(
                text=f"Задание {task.id}",
                callback_data=f"do_task_{task.id}"
            )
            task_buttons.append([button])

        back_button = InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu")
        task_buttons.append([back_button])

        keyboard = InlineKeyboardMarkup(inline_keyboard=task_buttons)

        await callback.message.edit_text(f"Выберите ежедневное задание:\n\n{tasks_text}", reply_markup=keyboard)

@router.callback_query(F.data.startswith("do_task_"))
async def process_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
     
    
    async with async_session() as session:
        
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalar_one_or_none()
        result2 = await session.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result2.scalar_one_or_none()
        if task:
            # Проверяем существующие подтверждения
            existing_confirm = await session.execute(
                select(Confirm).where(
                    and_(
                        Confirm.tg_id == user_id,
                        Confirm.description == task.description
                    )
                )
            )
            if existing_confirm.scalar_one_or_none():
                await callback.answer("Вы уже отправили заявку на подтверждение этого достижения!", show_alert=True)
                return
        new_confirm = Confirm(
            tg_id=user_id,
            name=user.name,
            description=task.description,
            points=task.point,
            category='Задание',          
        )
        session.add(new_confirm)
        await session.commit()
        

        await callback.answer("Ваша заявка на подтверждение отправлена!", show_alert=True)


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    keybord = InlineKeyboardMarkup(inline_keyboard=kb.task)
    await callback.message.edit_text("*Меню заданий*\n\n"
        "Добро пожаловать в раздел заданий! Здесь вы можете выбрать задания, которые помогут вам заработать поинты и достичь новых высот!\n\n"
        "📅 *Ежедневные задания* - Выполняйте простые задания каждый день, чтобы получать бонусы и не упустить возможность заработать дополнительные поинты!\n"
        "📆 *Еженедельные задания* - Более сложные задачи, которые нужно выполнить в течение недели. За успешное выполнение вы получите значительные награды!\n"
        "📅 *Ежемесячные задания* - Самые масштабные и интересные задания, которые открываются раз в месяц. Успейте выполнить их, чтобы получить эксклюзивные награды!\n\n"
        "✨ *Выберите тип задания, нажав на соответствующую кнопку, и начните зарабатывать поинты уже сегодня!*",reply_markup=keybord)



@router.callback_query(F.data.startswith("task_"))
async def process_task_selection(callback_query: types.CallbackQuery):
    task_id = int(callback_query.data.split("_")[1])
    
    async with async_session() as session:
       
        result = await session.execute(select(Task).filter(Task.id == task_id))
        task = result.scalar_one_or_none()
        
        user_result = await session.execute(
            select(User).filter(User.tg_id == callback_query.from_user.id)
        )
        user = user_result.scalar_one_or_none()
        
        if task and user:
            task_description = task.description
            task_point = task.point
            new_confirm = Confirm(
                tg_id=callback_query.from_user.id,
                name=user.name, 
                description=task_description,
                points=task_point
            )
            session.add(new_confirm)
            await session.commit()

            await callback_query.answer(f"Вы выбрали задание: {task_description}")
            await callback_query.message.answer(f"Задание '{task_description}' ({task_point} points) добавлено в базу подтверждений. Ожидайте подтверждения администратором.")
        else:
            await callback_query.answer("Задание или пользователь не найдены.")


@router.callback_query(F.data == 'liderboard_')
async def show_top_users(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).order_by(desc(User.all_point)).limit(10))
        users = result.scalars().all()
        if users:
            response = 'Топ 10 пользователей по очкам:\n\n'
            for i, user in enumerate(users, start=1):
                response += f"{i} | {user.name} | {user.all_point} очков\n"
            await callback.message.edit_text(response,reply_markup=kb.back_to_main)
        else:
            await callback.message.answer("Пользователи не найдены")



#Магазин
@router.callback_query(F.data == 'sale_')
async def show_shop(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(Shop))
        shops = result.scalars().all()

    if not shops:
        await callback.answer("На данный момент нельзя ничего купить.")
        return

    builder = InlineKeyboardBuilder()
    

    for shop in shops:
        builder.button(text=f"{shop.description} | {shop.points}", callback_data=f"shop_{shop.id}")


    builder.button(text="◀️ Назад в главное меню", callback_data="back_to_main")

    builder.adjust(1)  
    await callback.message.edit_text("Выберите предмет для покупки:", reply_markup=builder.as_markup())


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
            
                await callback.message.answer(f"Вы успешно приобрели {shop_item.description}!\n"
                                              "Покажите это сообщение Админу, чтобы получить подарок!")
                
                await callback.answer()
            else:
                await callback.answer("У вас недостаточно очков для покупки этого товара.")

   
        
#Ачивки

@router.callback_query(F.data == 'ach_')
async def show_tasks(callback: types.CallbackQuery):
    keybord = await rq.get_categories_keyboard()
    await callback.message.edit_text('Выберите категорию',reply_markup=keybord)

@router.callback_query(F.data.startswith("category_"))
async def show_achievements(callback: CallbackQuery):
    category_id = str(callback.data.split("_")[1])
    async with async_session() as session:
        result = await session.execute(
            select(Achievement).where(Achievement.category_id == category_id)
        )
        achievements = result.scalars().all()
        
        keyboard = []
        row = []
        for ach in achievements:
            row.append(InlineKeyboardButton(
                text=ach.name,
                callback_data=f"achievement_{ach.id}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
                
        if row: 
            keyboard.append(row)
            
        keyboard.append([
            InlineKeyboardButton(
                text="◀️ Назад к категориям",
                callback_data="back_to_categories"
            )
        ])
        
        text = f"Ачивки в категории {category_id}:"
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        # Удаляем старое сообщение
        await callback.message.delete()
        
        # Отправляем новое сообщение
        await callback.message.answer(text=text, reply_markup=markup)
        
        # Отвечаем на callback, чтобы убрать "часики" на кнопке
        await callback.answer()


@router.callback_query(F.data.startswith("achievement_"))
async def show_achievement_details(callback: CallbackQuery):
    achievement_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        result = await session.execute(
            select(Achievement).where(Achievement.id == achievement_id)
        )
        achievement = result.scalar_one_or_none()
        
        if achievement:
            keyboard = [[
                InlineKeyboardButton(
                    text="◀️ Назад к ачивкам",
                    callback_data=f"category_{achievement.category_id}"
                )
            ],[InlineKeyboardButton(
                text='Подтвердить задание!',
                callback_data = f"confirm_{achievement_id}"
            )]]
            
            text = f"🏆 Ачивка: {achievement.name}\n"
            text += f"📑 Категория: {achievement.category_id}\n"
            text += f"📝 Описание: {achievement.description}\n"
            text += f"💎 Поинты: {achievement.points}"
            
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            else:
                
                if achievement.photo:  
                    await callback.message.delete()
                    await callback.message.answer_photo(
                        photo=achievement.photo,
                        caption=text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                    )
                else:
                    
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                    )
            await callback.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )

# Обработчик кнопки "Назад к категориям"
@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    keyboard = await rq.get_categories_keyboard()
    text = "Выберите категорию:"
    await callback.message.delete()
    await callback.message.answer(text=text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_"))
async def confirm_achievement(callback: CallbackQuery):
    achievement_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
     
    
    async with async_session() as session:
        
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalar_one_or_none()
        result2 = await session.execute(
            select(Achievement).where(Achievement.id == achievement_id)
        )
        achievement = result2.scalar_one_or_none()
        if achievement:
            # Проверяем существующие подтверждения
            existing_confirm = await session.execute(
                select(Confirm).where(
                    and_(
                        Confirm.tg_id == user_id,
                        Confirm.description == achievement.description,
                    )
                )
            )
            if existing_confirm.scalar_one_or_none():
                await callback.answer("Вы уже отправили заявку на подтверждение этого достижения!", show_alert=True)
                return
        new_confirm = Confirm(
            tg_id=user_id,
            task_id=achievement.id,
            name=user.name,
            description=achievement.description,
            points=achievement.points,
            category='Ачивка',          
        )
        session.add(new_confirm)
        await session.commit()
        

        await callback.answer("Ваша заявка на подтверждение отправлена!", show_alert=True,)
          

@router.callback_query(F.data.startswith("loyalty_"))
@is_test()
async def loyalty(callback: types.CallbackQuery):
    # Удаляем текст сообщения
    await callback.message.delete()

    # Полный путь к файлу
    photo_path = r'photo\loyal.jpg'

    # Проверяем, существует ли файл
    if os.path.exists(photo_path):
        # Создаем объект FSInputFile из файла
        photo = FSInputFile(photo_path)  # Use FSInputFile for file path
        # Отправляем новое сообщение с фотографией
        await callback.message.answer_photo(photo=photo, reply_markup=kb.back_to_main)
    else:
        await callback.message.answer("Извините, фотография не найдена.")


