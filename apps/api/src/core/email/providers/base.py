"""Email provider abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SendResult:
    success: bool
    message_id: Optional[str] = None
    provider: str = 'unknown'
    error: Optional[str] = None


@dataclass
class OutboundEmail:
    to: str | list[str]
    subject: str
    html: str
    text: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None


class EmailProvider(ABC):
    name: str = 'base'

    @abstractmethod
    async def send(self, email: OutboundEmail) -> SendResult:
        pass

    @abstractmethod
    async def test_connection(self) -> SendResult:
        pass
