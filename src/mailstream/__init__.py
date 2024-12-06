from .client import MailStreamClient, Config
from .mail import Mail
from .context import with_mailstream, from_mailstream
from .exceptions import (
    MailStreamError,
    ConnectionError,
    AuthenticationError,
    FetchError,
    AlreadyWaitingError,
)

__all__ = [
    "MailStreamClient",
    "Config",
    "Mail",
    "with_mailstream",
    "from_mailstream",
    "MailStreamError",
    "ConnectionError",
    "AuthenticationError",
    "FetchError",
    "AlreadyWaitingError",
]
