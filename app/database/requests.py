from aiogram import types,Bot
from aiogram.fsm.context import FSMContext
from app.database.models import async_session
from app.database.models import User,Task,Confirm
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select,text
import app.database.models as md


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
        5: 2,
        15: 3,
        30: 4,
        50: 5,
        
    }
    level = 1
    for p, lvl in levels.items():
        if points >= p:
            level = lvl
    return level

async def profile(tg_id):
    async with async_session() as session:
        user_id = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user_id:
            user_id.level = calculate_level(user_id.point)
            return{
                'name': user_id.name,
                'tg_id': user_id.tg_id,
                'points': user_id.point,
                'all_point': user_id.all_point,
                'tasks': user_id.all_task,
                'level': user_id.level  
        }
        else:
            return None
        
async def confirm_all(message: types.Message, state: FSMContext):
    bot: Bot = message.bot
    async with async_session() as session:
        result = await session.execute(select(Confirm))
        confirm_records = result.scalars().all()
    
        for confirm in confirm_records:
            user = await session.execute(select(User).where(User.tg_id == confirm.tg_id))
            user = user.scalar_one_or_none()
            if user:
                user.all_point += confirm.points
                user.point += confirm.points
                user.all_task += 1
                
                # Отправка уведомления пользователю
                
                try:
                            await bot.send_message(
                                chat_id=user.tg_id,
                                text=f"Ваше задание было подтверждено! Вы получили {confirm.points} очков."
                            )
                except Exception as e:
                     await message.reply(f"Подтверждение обработано, но возникла ошибка при отправке уведомления пользователю: {e}")

        await session.execute(text("DELETE FROM confrim"))
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
                        user.point += confirm.points
                        user.all_task += 1 
                        
                        await session.delete(confirm)
                        
                        try:
                            await bot.send_message(
                                chat_id=user.tg_id,
                                text=f"Ваше задание было подтверждено! Вы получили {confirm.points} очков."
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



    



 

        
