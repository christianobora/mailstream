from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Address:
    """Represents an email address"""

    mailbox: str
    host: str

    def __str__(self):
        return f"{self.mailbox}@{self.host}"


@dataclass
class Mail:
    """Represents an email message"""

    uid: int
    from_address: List[Address]
    to_address: List[Address]
    subject: str
    date: datetime
    plain_text: Optional[bytes] = None
    html_text: Optional[bytes] = None

    @property
    def from_email(self) -> str:
        """Get the primary sender's email"""
        return str(self.from_address[0]) if self.from_address else None

    @property
    def to_email(self) -> str:
        """Get the primary recipient's email"""
        return str(self.to_address[0]) if self.to_address else None
