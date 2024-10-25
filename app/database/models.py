from sqlalchemy import BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base


engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')
async_session = async_sessionmaker(engine)

Session = sessionmaker(bind=engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(default='Unknown')
    point: Mapped[int] = mapped_column(default=0)
    all_point: Mapped[int] = mapped_column(default=0)
    all_task: Mapped[int] = mapped_column(default=0)
    root: Mapped[bool] = mapped_column(default=False)
    level: Mapped[int] = mapped_column(default=1)

class Task(Base):
    __tablename__ = 'tasks'
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(default='Unknown')
    category_id: Mapped[int] = mapped_column(default=0)
    point: Mapped[int] = mapped_column(default=0)

class Achievement(Base):
    __tablename__ = 'achievements'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(default='Unknown')
    description: Mapped[str] = mapped_column(default='Unknown')
    category_id: Mapped[int] = mapped_column(default=0)
    points : Mapped[str] = mapped_column(default=0)

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
    name: Mapped[str] = mapped_column(default='Unknown')
    description: Mapped[str] = mapped_column(default='Unknown')
    points : Mapped[int] = mapped_column(default=0)
    







