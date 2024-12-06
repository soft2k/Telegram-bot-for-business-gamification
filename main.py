import asyncio
from aiogram import Bot, Dispatcher,F
import logging
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from app.root import router_root
from app.handlers import router
from app.database.models import engine, Base



import app.database.requests as rq

bot = Bot(token='7302355885:AAGog8u9zfK7k0yR4v7MXcihRGijB7lLFY8')
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    await async_main()
    bot = Bot(token='7302355885:AAGog8u9zfK7k0yR4v7MXcihRGijB7lLFY8')
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(router_root)


    await dp.start_polling(bot)
    


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')