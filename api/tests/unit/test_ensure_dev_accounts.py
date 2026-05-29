"""ensure_dev_accounts creates system owner on empty database."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.local_user_auth import _password_hash, ensure_dev_accounts
from src.core.models import Base, User, generate_uuid
from src.core.passwords import hash_password, verify_password


def test_ensure_dev_accounts_creates_owner():
    async def _run() -> None:
        engine = create_async_engine('sqlite+aiosqlite:///:memory:')
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            changed = await ensure_dev_accounts(session)
            assert changed is True

            owner = (
                await session.execute(select(User).where(User.email == 'admin@tendoriq.com'))
            ).scalar_one_or_none()
            assert owner is not None
            assert verify_password('Owner@ChangeMe123', _password_hash(owner))

            legacy_demo = (
                await session.execute(select(User).where(User.email == 'demo@tendoriq.com'))
            ).scalar_one_or_none()
            assert legacy_demo is None
        await engine.dispose()

    asyncio.run(_run())


def test_ensure_dev_accounts_removes_legacy_demo_user():
    async def _run() -> None:
        engine = create_async_engine('sqlite+aiosqlite:///:memory:')
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            session.add(
                User(
                    id=generate_uuid(),
                    email='demo@tendoriq.com',
                    name='Legacy Demo',
                    preferences={'password_hash': hash_password('old-demo-pass')},
                )
            )
            await session.commit()

            changed = await ensure_dev_accounts(session)
            assert changed is True

            legacy_demo = (
                await session.execute(select(User).where(User.email == 'demo@tendoriq.com'))
            ).scalar_one_or_none()
            assert legacy_demo is None
        await engine.dispose()

    asyncio.run(_run())
