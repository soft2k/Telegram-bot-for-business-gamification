from aiogram import types,Bot
from aiogram.fsm.context import FSMContext
from app.database.models import async_session
from app.database.models import User,Task,Confirm,Achievement
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select,text
import app.database.models as md
import json


async def check_user(tg_id):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        return user is not None
    
async def set_user(tg_id,name):
    async with async_session() as session:
        user_id = await session.scalar(select(User).where(User.tg_id == tg_id))
       
        
       
        
        if not user_id:
            session.add(User(tg_id=tg_id,name=name))
            await session.commit()
        return user_id

 

async def check_root_id(tg_id):
    async with async_session() as session:
        user_id = await session.scalar(select(User).where(User.tg_id == tg_id))
         
        if user_id is not None:
            if user_id.root:
                return True
            else:
                return False
        else:
            return False

def calculate_level(points):
    levels = {
        0: 1,
        600: 2,
        1800: 3,
        3000: 4,
        5000: 5,
    }
    level = 1
    for p, lvl in levels.items():
        if points >= p:
            level = lvl
    return level

async def profile(tg_id: int):
    async with async_session() as session:
        query = select(User).where(User.tg_id == tg_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user:
            # Обработка completed_tasks
            completed_tasks = user.completed_tasks if isinstance(user.completed_tasks, list) else []
            
            # Получение названий выполненных задач (ачивок)
            completed_task_names = []
            if completed_tasks:
                task_query = select(Achievement).where(Achievement.id.in_(completed_tasks))
                tasks = (await session.execute(task_query)).scalars().all()
                completed_task_names = [task.name for task in tasks]

            # Рассчитываем уровень на основе текущих поинтов
            user_level = calculate_level(user.all_point)

            # Обновляем уровень пользователя в базе данных, если он изменился
            if user.level != user_level:
                user.level = user_level
                session.add(user)  # Добавляем пользователя в сессию для обновления
                await session.commit()  # Сохраняем изменения в базе данных

            return {
                "id": user.id,
                "name": user.name,
                "tg_id": user.tg_id,
                "points": user.point,
                "all_point": user.all_point,
                "tasks": user.all_task,
                "completed_tasks": completed_task_names,
                "level": user.level,
                "visit": user.visit
            }
        return None
        

async def add_achievement(user_id: int, achievement_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            achievements = json.loads(user.completed_tasks) if user.completed_tasks else []
            if achievement_id not in achievements:
                achievements.append(achievement_id)
                user.completed_tasks = json.dumps(achievements)
                await session.commit()

from sqlalchemy import select, update,delete
import json

async def confirm_all(message: types.Message, state: FSMContext):
    bot: Bot = message.bot
    async with async_session() as session:
        result = await session.execute(select(Confirm))
        confirm_records = result.scalars().all()

        for confirm in confirm_records:
            user_query = select(User).where(User.tg_id == confirm.tg_id)
            user = (await session.execute(user_query)).scalar_one_or_none()
            
            if user:
                # Обновляем очки и задания
                await session.execute(
                    update(User).
                    where(User.id == user.id).
                    values(
                        all_point=User.all_point + confirm.points,
                        point=User.point + confirm.points,
                        all_task=User.all_task + 1
                    )
                )
                
                notification_text = f"Ваше задание было подтверждено! Вы получили {confirm.points} очков."

                # Если это ачивка
                if confirm.category == "Ачивка":
                    # Обновляем список выполненных задач
                    new_completed_tasks = user.completed_tasks + [confirm.task_id]
                    await session.execute(
                        update(User).
                        where(User.id == user.id).
                        values(completed_tasks=new_completed_tasks)
                    )
                    
                    notification_text += f"\nПоздравляем! Вы получили ачивку '{confirm.description}'!"

                # Отправка уведомления пользователю
                try:
                    await bot.send_message(
                        chat_id=user.tg_id,
                        text=notification_text
                    )
                except Exception as e:
                    await message.reply(f"Подтверждение обработано, но возникла ошибка при отправке уведомления пользователю: {e}")

        # Удаляем обработанные подтверждения
        await session.execute(delete(Confirm))
        await session.commit()
    
    await message.answer("Все подтверждения обработаны и уведомления отправлены.")

async def deleat_all_confrim():
    async with async_session() as session:
        await session.execute(text("DELETE FROM confrim"))
        await session.commit()

async def confrim_one(message: types.Message, state: FSMContext):
    bot: Bot = message.bot
    try:
        confirm_id = int(message.text)
        
        async with async_session() as session:
            async with session.begin():
                confirm_query = await session.execute(select(Confirm).where(Confirm.id == confirm_id))
                confirm = confirm_query.scalar_one_or_none()
                
                if confirm:
                    user_query = await session.execute(select(User).where(User.tg_id == confirm.tg_id))
                    user = user_query.scalar_one_or_none()
                    
                    if user:
                        # Обновляем очки и задания
                        await session.execute(
                            update(User).
                            where(User.id == user.id).
                            values(
                                all_point=User.all_point + confirm.points,
                                point=User.point + confirm.points,
                                all_task=User.all_task + 1
                            )
                        )
                        
                        notification_text = f"Ваше задание было подтверждено! Вы получили {confirm.points} очков."

                        # Если это ачивка
                        if confirm.category == "Ачивка":
                            # Обновляем список выполненных задач
                            new_completed_tasks = user.completed_tasks + [confirm.task_id]
                            await session.execute(
                                update(User).
                                where(User.id == user.id).
                                values(completed_tasks=new_completed_tasks)
                            )
                            
                            notification_text += f"\nПоздравляем! Вы получили ачивку '{confirm.description}'!"

                        await session.delete(confirm)
                        
                        try:
                            await bot.send_message(
                                chat_id=user.tg_id,
                                text=notification_text
                            )
                            await message.reply(f"Подтверждение с ID {confirm_id} обработано. Пользователю начислено {confirm.points} очков и отправлено уведомление.")
                        except Exception as e:
                            await message.reply(f"Подтверждение обработано, но возникла ошибка при отправке уведомления пользователю: {e}")
                    else:
                        await message.reply(f"Пользователь для подтверждения с ID {confirm_id} не найден.")
                else:
                    await message.reply(f"Подтверждение с ID {confirm_id} не найдено.")

    except ValueError:
        await message.reply("Пожалуйста, введите корректный ID подтверждения (целое число).")
    finally:
        await state.clear()

async def confrim_delete_one(message:  types.Message, state: FSMContext):
    try:
        confirm_query = int(message.text)
        async with async_session() as session:
            shop = await session.get(Confirm, confirm_query)
            if shop:
                await session.delete(shop)
                await session.commit()
                await message.reply(f"Потверждение  {confirm_query} успешно удалён")
            else:
                await message.reply(f'Потверждение с таким ID: {confirm_query} не найден')
    except ValueError:
        await message.reply('Введите коректный ID')


async def delete_one_ach(message: types.Message,state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Achievement))
        achs = result.scalars().all()

        if achs:
            ach_list = 'Список ачивок"\n\n'
            for ach in achs:
                ach_list += f"{ach.id}. | {ach.category_id} | {ach.name} | {ach.description} | {ach.points}\n"
        else:
            ach_list = 'Список ачивок пуст'
        await message.reply(ach_list)

async def deleat_all_confrim_ach():
    async with async_session() as session:
        await session.execute(text("DELETE FROM achievements"))
        await session.commit()


async def get_categories_keyboard():
    async with async_session() as session:
        result = await session.execute(select(Achievement.category_id).distinct())
        categories = result.scalars().all()
        
        keyboard = []
        row = []
        for category in categories:
            row.append(InlineKeyboardButton(
                text=f"{category}",
                callback_data=f"category_{category}"
            ))
            if len(row) == 2:  
                keyboard.append(row)
                row = []
        if row:  
            keyboard.append(row)
        
        keyboard.append([
            InlineKeyboardButton(
                text="◀️ Назад в меню",
                callback_data="back_to_main"
            )
        ])
            
    return InlineKeyboardMarkup(inline_keyboard=keyboard)




 

        
