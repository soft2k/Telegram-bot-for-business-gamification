import asyncio
from aiogram import Bot, Dispatcher, types
import logging
from app.root import router_root
from app.handlers import router
from app.database.models import engine, Base

import app.database.requests as rq

API_TOKEN = ''
bot = Bot(token=API_TOKEN)



async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def on_startup(dp):
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Перезапустить бота"),
        
    ])

async def main():
    await async_main()
    
    dp = Dispatcher()  
    dp.include_router(router)
    dp.include_router(router_root)

    await on_startup(dp)
    await dp.start_polling(bot) 

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
