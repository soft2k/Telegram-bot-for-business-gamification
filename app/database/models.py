from sqlalchemy import BigInteger,LargeBinary,JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3',echo=True)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Session = sessionmaker(bind=engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(default='Unknown')
    phone: Mapped[str] = mapped_column(default='Unknown')
    point: Mapped[int] = mapped_column(default=0)
    all_point: Mapped[int] = mapped_column(default=0)
    all_task: Mapped[int] = mapped_column(default=0)
    completed_tasks: Mapped[list] = mapped_column(JSON, default=lambda: [])
    level: Mapped[int] = mapped_column(default=1)
    visit: Mapped[int] = mapped_column(default=0)
    root: Mapped[bool] = mapped_column(default=False)
    referral: Mapped[int] = mapped_column(default=0)
    phoneReferral: Mapped[str] = mapped_column(default='0')
    status: Mapped[str] = mapped_column(default='Базовичок')
    

class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True)   
    description: Mapped[str] = mapped_column(default='Unknown')
    category_id: Mapped[int] = mapped_column(default=0)
    point: Mapped[int] = mapped_column(default=0)
    number: Mapped[str] = mapped_column(default='Unknown')

class Achievement(Base):
    __tablename__ = 'achievements'
    id: Mapped[int] = mapped_column(primary_key=True) 
    name: Mapped[str] = mapped_column(default='Unknown')
    description: Mapped[str] = mapped_column(default='Unknown')
    category_id: Mapped[str] = mapped_column(default='Unknown')
    points : Mapped[int] = mapped_column(default=0)
    photo: Mapped[str] = mapped_column(default='Unknown')

class Shop(Base):
    __tablename__ = 'shop'
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(default='Unknown')
    category_id: Mapped[int] = mapped_column(default=0)
    points : Mapped[int] = mapped_column(default=0)

class Confirm(Base):
    __tablename__ = 'confrim'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    task_id: Mapped[int] = mapped_column(default=0)
    name: Mapped[str] = mapped_column(default='Unknown')
    category: Mapped[str] = mapped_column(default='Unknown')
    description: Mapped[str] = mapped_column(default='Unknown')
    points : Mapped[int] = mapped_column(default=0)
    number : Mapped[int] = mapped_column(default=0)
    







