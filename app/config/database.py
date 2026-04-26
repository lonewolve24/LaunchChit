from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool


def make_engine(database_url: str):
    kwargs = {}
    if database_url.startswith("sqlite"):
        kwargs = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    return create_async_engine(database_url, **kwargs)


def make_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
