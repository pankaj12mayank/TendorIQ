"""Dependency injection container."""

from collections.abc import AsyncGenerator
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from .database import async_session_maker

T = TypeVar('T')


class Container:
    _instances: dict[type, Any] = {}
    _factories: dict[type, callable] = {}

    @classmethod
    def register(cls, interface: type[T], factory: callable[[], T]) -> None:
        cls._factories[interface] = factory

    @classmethod
    def register_singleton(cls, interface: type[T], instance: T) -> None:
        cls._instances[interface] = instance

    @classmethod
    def resolve(cls, interface: type[T]) -> T:
        if interface in cls._instances:
            return cls._instances[interface]
        if interface not in cls._factories:
            raise KeyError(f'No factory registered for {interface}')
        instance = cls._factories[interface]()
        cls._instances[interface] = instance
        return instance

    @classmethod
    def clear(cls) -> None:
        cls._instances.clear()


container = Container()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
