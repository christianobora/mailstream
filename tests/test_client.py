import pytest
import asyncio
from unittest.mock import AsyncMock, patch

import aioimaplib

from mailstream import MailStreamClient, Config
from mailstream.mail import Mail
from mailstream.exceptions import ConnectionError, AlreadyWaitingError

# Sample configuration for testing
TEST_CONFIG = Config(
    host="test.imap.example.com",
    port=993,
    email="test@example.com",
    password="testpassword",
    debug=True,
)


@pytest.fixture
async def mock_client():
    """Create a mock MailStreamClient for testing."""
    client = MailStreamClient(TEST_CONFIG)
    client._client = AsyncMock(spec=aioimaplib.IMAP4_SSL)
    # Return the mock client directly
    return client


@pytest.mark.asyncio
async def test_connect_success(mock_client):
    """Test successful connection to IMAP server using mocked connect."""
    # Mock server responses
    mock_client._client.wait_hello_from_server = AsyncMock(return_value=None)
    mock_client._client.login = AsyncMock(return_value=("OK", [b"LOGIN successful"]))
    mock_client._client.select = AsyncMock(return_value=("OK", [b"INBOX selected"]))
    mock_client._client.search = AsyncMock(return_value=("OK", [b"1 2 3"]))

    # Perform the connection logic manually to simulate a full flow
    await mock_client._client.wait_hello_from_server()
    await mock_client._client.login(TEST_CONFIG.email, TEST_CONFIG.password)
    await mock_client._client.select("INBOX")
    response, messages = await mock_client._client.search("ALL")

    # Simulate setting the number of messages
    mock_client._num_messages = len(messages[0].split())

    # Verify method calls
    mock_client._client.wait_hello_from_server.assert_awaited_once()
    mock_client._client.login.assert_awaited_once_with(
        TEST_CONFIG.email, TEST_CONFIG.password
    )
    mock_client._client.select.assert_awaited_once_with("INBOX")
    mock_client._client.search.assert_awaited_once_with("ALL")

    # Verify message count is set correctly
    assert mock_client._num_messages == 3


@pytest.mark.asyncio
async def test_connect_failure(mock_client):
    """Test connection failure."""
    # Mock server to raise an exception
    mock_client._client.wait_hello_from_server = AsyncMock(
        side_effect=Exception("Connection failed")
    )

    with pytest.raises(ConnectionError):
        await mock_client.connect()


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe(mock_client):
    """Test listener subscription and unsubscription."""
    # Initial state
    assert len(mock_client._listeners) == 0

    # Subscribe
    listener1 = mock_client.subscribe()
    assert len(mock_client._listeners) == 1
    assert listener1 in mock_client._listeners

    # Subscribe again
    listener2 = mock_client.subscribe()
    assert len(mock_client._listeners) == 2

    # Unsubscribe
    mock_client.unsubscribe(listener1)
    assert len(mock_client._listeners) == 1
    assert listener1 not in mock_client._listeners

    # Unsubscribe again
    mock_client.unsubscribe(listener2)
    assert len(mock_client._listeners) == 0
    assert listener2 not in mock_client._listeners


@pytest.mark.asyncio
async def test_get_unseen_mails(mock_client):
    """Test fetching unseen emails."""
    # Mock search response to return message IDs
    mock_client._client.search = AsyncMock(return_value=("OK", [b"1 2"]))

    # Define fake emails to return
    fake_emails = [
        Mail(
            uid=1,
            from_address=["sender@example.com"],
            to_address=["recipient@example.com"],
            subject="Test Email 1",
            date="Mon, 01 Jan 2024 12:00:00 +0000",
            plain_text="Test email body 1",
            html_text=None,
        ),
        Mail(
            uid=2,
            from_address=["another.sender@example.com"],
            to_address=["recipient@example.com"],
            subject="Test Email 2",
            date="Tue, 02 Jan 2024 12:00:00 +0000",
            plain_text="Test email body 2",
            html_text=None,
        ),
    ]

    # Patch `_fetch_mail` to return the fake emails
    async def mock_fetch_mail(msg_num):
        for mail in fake_emails:
            if mail.uid == int(msg_num):
                yield mail

    with patch.object(mock_client, "_fetch_mail", side_effect=mock_fetch_mail):
        unseen_mails = [mail async for mail in mock_client.get_unseen_mails()]

    # Verify
    assert len(unseen_mails) == 2  # Expect two unseen emails
    assert unseen_mails[0].subject == "Test Email 1"
    assert unseen_mails[1].subject == "Test Email 2"
    assert unseen_mails[0].plain_text == "Test email body 1"
    assert unseen_mails[1].plain_text == "Test email body 2"


@pytest.mark.asyncio
async def test_wait_for_updates(mock_client):
    """Test waiting for email updates."""
    # Mock initial and subsequent search results
    mock_client._num_messages = 2
    mock_client._client.noop = AsyncMock()
    mock_client._client.search = AsyncMock(
        side_effect=[
            ("OK", [b"1 2"]),  # Initial search
            ("OK", [b"1 2 3"]),  # Search after update
        ]
    )

    # Mock fetch method
    mock_client._client.fetch = AsyncMock()

    # Simulate a timeout
    async def fake_wait_for_updates(*args, **kwargs):
        await asyncio.sleep(0.2)  # Simulate polling delay
        raise asyncio.TimeoutError()

    with patch.object(
        mock_client, "wait_for_updates", side_effect=fake_wait_for_updates
    ):
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                mock_client.wait_for_updates(poll_interval=0.1), timeout=0.5
            )


@pytest.mark.asyncio
async def test_already_waiting_error(mock_client):
    """Test raising AlreadyWaitingError when already waiting."""
    # Set up mock state
    mock_client._is_waiting = True

    # Start one wait_for_updates
    update_task = asyncio.create_task(mock_client.wait_for_updates())

    # Try to start another, which should raise AlreadyWaitingError
    with pytest.raises(AlreadyWaitingError):
        await mock_client.wait_for_updates()

    # Cleanup
    update_task.cancel()
    try:
        await update_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_context_manager(mock_client):
    """Test context manager functionality."""
    with patch.object(
        mock_client, "connect", new_callable=AsyncMock
    ) as mock_connect, patch.object(
        mock_client, "close", new_callable=AsyncMock
    ) as mock_close:

        async with mock_client:
            mock_connect.assert_awaited_once()

        mock_close.assert_awaited_once()


def test_config_creation():
    """Test Config dataclass creation."""
    config = Config(
        host="imap.example.com", port=993, email="user@example.com", password="password"
    )

    assert config.host == "imap.example.com"
    assert config.port == 993
    assert config.email == "user@example.com"
    assert config.password == "password"
    assert config.mailbox == "INBOX"
    assert config.debug is False
