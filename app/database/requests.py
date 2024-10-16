from app.database.models import async_session
from app.database.models import User,Task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import select
import app.database.models as md


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

async def profile(tg_id):
    async with async_session() as session:
        user_id = await session.scalar(select(User).where(User.tg_id == tg_id))

        if user_id:
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
        


