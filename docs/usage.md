# Usage Guide

## Basic Usage

### Connecting to an IMAP Server

```python
import asyncio
from mailstream import MailStreamClient, Config

async def main():
    config = Config(
        host="imap.example.com",
        port=993,
        email="your_email@example.com",
        password="your_password",
        mailbox="INBOX",  # Optional, defaults to "INBOX"
        debug=True       # Optional, enables detailed logging
    )

    client = MailStreamClient(config)
    await client.connect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Listening for Emails

### Simple Listener Implementation

```python
import asyncio
from mailstream import MailStreamClient, Config

async def main():
    config = Config(
        host="imap.example.com",
        port=993,
        email="your_email@example.com",
        password="your_password"
    )

    client = MailStreamClient(config)
    await client.connect()

    # Start the IDLE monitoring in the background
    background_task = asyncio.create_task(client.wait_for_updates())

    # Subscribe to email updates
    listener = client.subscribe()
    
    try:
        while True:
            # Process new emails as they arrive
            mail = await listener.get()
            print(f"New email from: {mail.from_address[0]}")
            print(f"Subject: {mail.subject}")
            print(f"Content: {mail.plain_text}")
            
    except KeyboardInterrupt:
        print("Stopping mail client")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up resources
        background_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await background_task
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Usage

### Working with Multiple Listeners

```python
async def main():
    client = MailStreamClient(config)
    await client.connect()

    # Start background monitoring
    background_task = asyncio.create_task(client.wait_for_updates())

    # Create multiple listeners
    listener1 = client.subscribe()
    listener2 = client.subscribe()

    async def handle_listener1():
        while True:
            mail = await listener1.get()
            print("Listener 1:", mail.subject)

    async def handle_listener2():
        while True:
            mail = await listener2.get()
            print("Listener 2:", mail.subject)

    # Create tasks for both listeners
    listener1_task = asyncio.create_task(handle_listener1())
    listener2_task = asyncio.create_task(handle_listener2())

    try:
        # Wait forever or until interrupted
        await asyncio.Event().wait()
    finally:
        # Clean up
        background_task.cancel()
        listener1_task.cancel()
        listener2_task.cancel()
        await client.close()
```

### Fetching Unseen Emails

```python
async def main():
    client = MailStreamClient(config)
    await client.connect()

    # Fetch unseen emails
    async for mail in client.get_unseen_mails():
        print(f"Unseen email: {mail.subject}")
```

## Error Handling

```python
from mailstream import ConnectionError, FetchError

async def main():
    try:
        client = MailStreamClient(config)
        await client.connect()
    except ConnectionError as e:
        print(f"Failed to connect: {e}")
        return

    try:
        async for mail in client.get_unseen_mails():
            try:
                print(f"Processing mail: {mail.subject}")
            except Exception as e:
                print(f"Error processing mail: {e}")
    except FetchError as e:
        print(f"Error fetching mails: {e}")
```

## Best Practices

- Always use a try-except block when connecting
- Close the client when done
- Be mindful of memory usage with long-running listeners