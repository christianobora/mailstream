import asyncio
import logging
from dataclasses import dataclass
from typing import List, AsyncGenerator

import aioimaplib
from email import message_from_bytes
import email.utils
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.message import Message

from .mail import Mail
from .exceptions import ConnectionError, FetchError


@dataclass
class Config:
    """IMAP Client Configuration"""

    host: str
    email: str
    password: str
    port: int = 993
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

        self._logger.debug("MailStreamClient initialized.")
        self._logger.info("MailStreamClient initialized.")

    def _parse_address(self, address: str) -> str:
        """Parse and clean email address"""
        name, addr = email.utils.parseaddr(address)
        return addr

    def _decode_header(self, header: str) -> str:
        """Decode email header, handling encoded words (like =?UTF-8?B?...?=)"""
        decoded_header = decode_header(header)
        return "".join(
            [
                (
                    str(text, encoding if encoding else "utf-8")
                    if isinstance(text, bytes)
                    else text
                )
                for text, encoding in decoded_header
            ]
        )

    def _parse_date(self, date_str: str) -> str:
        """Parse email date into a readable format"""
        date = parsedate_to_datetime(date_str)
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def _get_email_body(self, message: Message, content_type: str) -> str:
        """Extract the body of the email based on content type"""
        for part in message.walk():
            if part.get_content_type() == f"text/{content_type}":
                return part.get_payload(decode=True).decode(
                    part.get_content_charset(), errors="ignore"
                )
        return ""

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
            print(msg_nums)
            if len(msg_nums) == 1:
                self._logger.info("No unseen messages found.")
                return
            print(msg_nums)
            self._logger.debug(f"Unseen messages found: {msg_nums}")
            for num in msg_nums[0].split():
                async for mail in self._fetch_mail(num):
                    yield mail
        except Exception as e:
            self._logger.error(f"Error fetching unseen mails: {e}")
            raise FetchError(f"Error fetching unseen mails: {e}")

    # async def _fetch_mail(self, msg_num) -> AsyncGenerator[Mail, None]:
    #     """Fetch a specific email by message number"""
    #     self._logger.debug(f"Fetching mail with message number: {msg_num}")
    #     try:
    #         msg_num = msg_num.decode() if isinstance(msg_num, bytes) else msg_num
    #         print(f"Fetching mail with message number: {msg_num}")
    #         print(await self._client.fetch(str(msg_num), "(BODY[])"))
    #         _, msg_data = await self._client.fetch(str(msg_num), "(BODY[])")
    #         print(f"Fetching mail with message number: {msg_data}")
    #         raw_email = msg_data[1]

    #         self._logger.debug("Parsing email message...")
    #         email_message = message_from_bytes(raw_email)

    #         mail = Mail(
    #             uid=int(msg_num),
    #             from_address=[
    #                 self._parse_address(addr)
    #                 for addr in email_message.get("From", "").split(",")
    #             ],
    #             to_address=[
    #                 self._parse_address(addr)
    #                 for addr in email_message.get("To", "").split(",")
    #             ],
    #             subject=self._decode_header(email_message.get("Subject", "")),
    #             date=self._parse_date(email_message.get("Date", "")),
    #             plain_text=self._get_email_body(email_message, "plain"),
    #             html_text=self._get_email_body(email_message, "html"),
    #         )

    #         self._logger.info(f"Mail fetched: {mail.subject}")
    #         for listener in self._listeners:
    #             self._logger.debug("Broadcasting mail to listener.")
    #             await listener.put(mail)

    #         yield mail
    #     except Exception as e:
    #         self._logger.error(f"Error fetching mail: {e}")
    #         print(e)
    #         raise FetchError(f"Error parsing email: {e}")

    async def close(self):
        """Close the IMAP connection and clean up resources."""
        self._logger.info("Closing IMAP connection and cleaning up resources...")
        try:
            if self._client:
                self._logger.debug("Logging out from IMAP server...")
                await self._client.logout()
                self._logger.info("Logged out successfully.")
        except Exception as e:
            self._logger.error(f"Error during logout: {e}")
        finally:
            self._client = None
            self._listeners.clear()
            self._logger.info("All resources cleaned up.")

    async def wait_for_updates(self) -> None:
        """
        Wait for new emails using IMAP IDLE.
        Similar to Golang's WaitForUpdates, this method uses IDLE to efficiently
        wait for new messages and fetches them when they arrive.
        """
        self._logger.info("Starting to wait for updates...")

        if self._is_waiting:
            self._logger.error("Already waiting for updates")
            raise RuntimeError("Already waiting for updates")

        self._is_waiting = True
        try:
            while True:
                self._logger.debug("Starting IDLE command...")
                await self._client.idle_start()

                try:
                    self._logger.debug("Waiting for new messages...")
                    responses = await self._client.wait_server_push()

                    for response_line in responses:
                        if response_line.endswith(b" EXISTS"):
                            try:
                                new_msg_count = int(response_line.split()[0])
                                self._logger.debug(
                                    f"New message count: {new_msg_count}"
                                )

                                if new_msg_count > self._num_messages:
                                    self._client.idle_done()

                                    self._logger.info(
                                        f"Fetching {new_msg_count - self._num_messages} new messages"
                                    )
                                    for msg_num in range(
                                        self._num_messages + 1, new_msg_count + 1
                                    ):
                                        search_cmd = (
                                            f"SEARCH (UNDELETED) {msg_num}:{msg_num}"
                                        )
                                        _, search_data = await self._client.search(
                                            search_cmd
                                        )

                                        if search_data[0]:
                                            try:
                                                _, fetch_data = (
                                                    await self._client.fetch(
                                                        str(msg_num), "(RFC822)"
                                                    )
                                                )
                                                if fetch_data and len(fetch_data) > 1:
                                                    raw_email = fetch_data[1]
                                                    async for mail in self._fetch_mail(
                                                        msg_num, raw_email
                                                    ):
                                                        self._logger.debug(
                                                            f"Broadcasting new mail: {mail.subject}"
                                                        )
                                                        for listener in self._listeners:
                                                            await listener.put(mail)
                                            except Exception as e:
                                                self._logger.error(
                                                    f"Error fetching message {msg_num}: {e}"
                                                )

                                    self._num_messages = new_msg_count
                                    await self._client.idle_start()
                            except ValueError as e:
                                self._logger.error(f"Error parsing message count: {e}")
                                continue

                finally:
                    self._logger.debug("Stopping IDLE command...")
                    self._client.idle_done()

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            self._logger.info("Update waiting cancelled")
            raise
        except Exception as e:
            self._logger.error(f"Error in wait_for_updates: {e}")
            raise
        finally:
            self._is_waiting = False
            self._logger.info("Stopped waiting for updates")

    async def _fetch_mail(self, msg_num, raw_email=None) -> AsyncGenerator[Mail, None]:
        """Fetch a specific email by message number"""
        self._logger.debug(f"Fetching mail with message number: {msg_num}")
        try:
            if raw_email is None:
                _, msg_data = await self._client.fetch(str(msg_num), "(RFC822)")
                raw_email = msg_data[1]

            if raw_email:
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
                yield mail
            else:
                self._logger.error("No raw email data received")
        except Exception as e:
            self._logger.error(f"Error fetching mail: {e}")
            raise FetchError(f"Error parsing email: {e}")
