# Usage Guide

## Basic Usage

### Connecting to an IMAP Server

```python
import asyncio
from mailstream import MailStreamClient, Config

config = Config(
    host="imap.example.com",  # Replace with your IMAP server hostname
    port=993,                 # Default IMAP SSL port
    email="your_email@example.com",
    password="your_password"
)

client = MailStreamClient(config)

async def main():
    await client.connect()

    listener = client.subscribe()  # Subscribe to new email notifications
    print("Listening for new emails...")

asyncio.run(main())
```

## Listening for Emails

### Simple Listener

```python
import asyncio

async def on_new_email(mail):
    print(f"New email from: {mail.from_address[0]}")
    print(f"Subject: {mail.subject}")

async def listen_for_emails(client):
    listener = client.subscribe()
    while True:
        mail = await listener.get()
        await on_new_email(mail)

async def main():
    await client.connect()
    asyncio.create_task(listen_for_emails(client))

    # Keep the script running
    await asyncio.Event().wait()

asyncio.run(main())
```

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
await client.wait_for_updates(poll_interval=10.0)
```

## Error Handling

```python
from mailstream import ConnectionError, AuthenticationError

try:
    client = MailStreamClient(
        host='imap.example.com',
        email='your_email@example.com',
        password='your_password'
    )
    await client.connect()
except (ConnectionError, AuthenticationError) as e:
    print(f"Connection failed: {e}")
```

## Best Practices

- Always use a try-except block when connecting
- Close the client when done
- Be mindful of memory usage with long-running listeners