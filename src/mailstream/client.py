import asyncio
import logging
from dataclasses import dataclass
from typing import List, AsyncGenerator

import aioimaplib
from email import message_from_bytes

from .mail import Mail
from .exceptions import ConnectionError, FetchError


@dataclass
class Config:
    """IMAP Client Configuration"""

    host: str
    port: int
    email: str
    password: str
    mailbox: str = "INBOX"
    debug: bool = False


class MailStreamClient:
    def __init__(self, config: Config):
        self._config = config
        self._client = None
        self._listeners: List[asyncio.Queue[Mail]] = []
        self._num_messages = 0
        self._is_waiting = False

        # Configure logging
        self._logger = logging.getLogger(__name__)
        if self._config.debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - %(levelname)s - %(message)s",
            )
            self._logger.debug("Debug mode enabled.")
        else:
            logging.basicConfig(level=logging.CRITICAL)

        self._logger.info("MailStreamClient initialized.")

    async def connect(self):
        """Establish IMAP connection"""
        self._logger.info("Connecting to IMAP server...")
        try:
            self._client = aioimaplib.IMAP4_SSL(
                host=self._config.host,
                port=self._config.port,
            )
            self._logger.debug("Waiting for server hello...")
            await self._client.wait_hello_from_server()

            self._logger.debug("Logging in with provided credentials...")
            await self._client.login(self._config.email, self._config.password)

            self._logger.debug(f"Selecting mailbox: {self._config.mailbox}")
            await self._client.select(self._config.mailbox)

            # Get initial message count
            self._logger.debug("Fetching initial message count...")
            _, msg_count = await self._client.search("ALL")
            self._num_messages = len(msg_count[0].split())
            self._logger.info(
                f"Connected successfully with {self._num_messages} "
                "existing messages."
            )
        except Exception as e:
            self._logger.error(f"Failed to connect: {e}")
            raise ConnectionError(f"Failed to connect: {e}")

    def subscribe(self) -> asyncio.Queue[Mail]:
        """Create a new listener queue"""
        self._logger.info("Creating a new listener...")
        listener = asyncio.Queue()
        self._listeners.append(listener)
        self._logger.debug(f"Listener added. Total listeners: {len(self._listeners)}")
        return listener

    def unsubscribe(self, listener: asyncio.Queue):
        """Remove a listener queue"""
        if listener in self._listeners:
            self._listeners.remove(listener)
            self._logger.info(
                "Listener removed. Remaining listeners: " f"{len(self._listeners)}"
            )

    async def get_unseen_mails(self) -> AsyncGenerator[Mail, None]:
        """Fetch all unseen emails"""
        self._logger.info("Fetching unseen emails...")
        try:
            _, msg_nums = await self._client.search("UNSEEN")
            self._logger.debug(f"Unseen messages found: {msg_nums}")
            for num in msg_nums[0].split():
                async for mail in self._fetch_mail(num):
                    yield mail
        except Exception as e:
            self._logger.error(f"Error fetching unseen mails: {e}")
            raise FetchError(f"Error fetching unseen mails: {e}")

    async def _fetch_mail(self, msg_num) -> AsyncGenerator[Mail, None]:
        """Fetch a specific email by message number"""
        self._logger.debug(f"Fetching mail with message number: {msg_num}")
        try:
            msg_num = msg_num.decode() if isinstance(msg_num, bytes) else msg_num
            _, msg_data = await self._client.fetch(str(msg_num), "(BODY[])")
            raw_email = msg_data[1]

            self._logger.debug("Parsing email message...")
            email_message = message_from_bytes(raw_email)

            mail = Mail(
                uid=int(msg_num),
                from_address=[
                    self._parse_address(addr)
                    for addr in email_message.get("From", "").split(",")
                ],
                to_address=[
                    self._parse_address(addr)
                    for addr in email_message.get("To", "").split(",")
                ],
                subject=self._decode_header(email_message.get("Subject", "")),
                date=self._parse_date(email_message.get("Date", "")),
                plain_text=self._get_email_body(email_message, "plain"),
                html_text=self._get_email_body(email_message, "html"),
            )

            self._logger.info(f"Mail fetched: {mail.subject}")
            for listener in self._listeners:
                self._logger.debug("Broadcasting mail to listener.")
                await listener.put(mail)

            yield mail
        except Exception as e:
            self._logger.error(f"Error fetching mail: {e}")
            raise FetchError(f"Error parsing email: {e}")
