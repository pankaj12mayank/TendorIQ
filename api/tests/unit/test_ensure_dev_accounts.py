"""ensure_dev_accounts creates missing system owner when demo already exists."""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.local_user_auth import _password_hash, ensure_dev_accounts
from src.core.models import Base, User, generate_uuid
from src.core.passwords import hash_password, verify_password


def test_creates_owner_when_only_demo_has_password():
    async def _run() -> None:
        engine = create_async_engine('sqlite+aiosqlite:///:memory:')
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            demo = User(
                id=generate_uuid(),
                email='demo@tendoriq.com',
                name='Demo',
                preferences={'password_hash': hash_password('old-demo-pass')},
            )
            session.add(demo)
            await session.commit()

            changed = await ensure_dev_accounts(session)
            assert changed is True

            owner = (
                await session.execute(select(User).where(User.email == 'admin@tendoriq.com'))
            ).scalar_one_or_none()
            assert owner is not None
            assert verify_password('Owner@ChangeMe123', _password_hash(owner))
        await engine.dispose()

    asyncio.run(_run())
