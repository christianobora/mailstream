# Mailstream

## Overview

MailStream is an asynchronous IMAP email client built with `aioimaplib`. It supports streaming emails, polling for updates, and broadcasting new emails to listeners.

## Features

- Asynchronous IMAP connection
- Fetch unseen emails
- Broadcast new emails to subscribers
- Easily integrate with context management

## Installation

```bash
pip install mailstream
```

## Quick Start

```python
import asyncio
from mailstream import MailStreamClient, Config

async def process_email(mail):
    print(f"New email from: {mail.from_email}")
    print(f"Subject: {mail.subject}")

config = Config(
    host="imap.example.com",
    port=993,
    email="your_email@example.com",
    password="your_password",
    debug=True
)

async def main():
    client = MailStreamClient(config)
    await client.connect()

    # Start wait_for_updates in the background
    asyncio.create_task(client.wait_for_updates())

    # Subscribe to new emails
    listener = client.subscribe()
    
    # Process emails from listener
    while True:
        mail = await listener.get()
        await process_email(mail)

    # Close connection
    await client.close()

asyncio.run(main())
```

## Configuration Options

- `host`: IMAP server hostname (required)
- `email`: Login email (required)
- `password`: Login password (required)
- `port`: IMAP server port (default: 993)
- `mailbox`: Target mailbox (default: 'INBOX')
- `debug`: Enable debug mode (default: False)

## Advanced Usage

### Fetching Unseen Mails

```python
# Retrieve all unseen emails
unseen_mails = client.get_unseen_mails()
for mail in unseen_mails:
    print(mail.subject)
```

### Multiple Listeners

```python
async def listener1(mail):
    print("Listener 1 received:", mail.subject)

async def listener2(mail):
    print("Listener 2 received:", mail.subject)

listener1_queue = client.subscribe()
listener2_queue = client.subscribe()
```

### Waiting for New Emails

```python
await client.wait_for_updates()
```

## Examples
For more examples, including advanced usage, please see the [examples](examples) directory.

## Error Handling

```python
from mailstream import ConnectionError, AuthenticationError

try:
    client = MailStreamClient(
        host='imap.example.com',
        port=993,
        email='your_email@example.com',
        password='your_password',
        debug=True
    )
    await client.connect()
except (ConnectionError, AuthenticationError) as e:
    print(f"Connection failed: {e}")
```

## Contributing

Contributions are welcome! Please see our [contributing guidelines](docs/development.md) for more details.

## License

[MIT](LICENSE)

## Support

For issues, please open a GitHub issue in the repository.