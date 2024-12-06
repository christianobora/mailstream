import asyncio
from mailstream import MailStreamClient, Config

async def listener1(mail):
    print("[Listener 1] Received email:")
    print(f"  From: {mail.from_email}")
    print(f"  Subject: {mail.subject}")

async def listener2(mail):
    print("[Listener 2] Processing email:")
    print(f"  To: {mail.to_email}")
    print(f"  Date: {mail.date}")

async def main():
    # Advanced configuration with debug mode enabled
    config = Config(
        host="imap.example.com",
        port=993,
        email="your_email@example.com",
        password="your_password",
        debug=True  # Enable debug logs for detailed output
    )

    # Initialize MailStreamClient
    client = MailStreamClient(config)

    try:
        # Connect to the IMAP server
        await client.connect()

        # Add listeners for real-time email processing
        listener1_queue = client.subscribe()
        listener2_queue = client.subscribe()
        print("Subscribed listeners for email updates.")

        # Start a background task to process emails for each listener
        async def process_queue(listener, queue):
            while True:
                mail = await queue.get()
                await listener(mail)

        # Start tasks for both listeners
        tasks = [
            asyncio.create_task(process_queue(listener1, listener1_queue)),
            asyncio.create_task(process_queue(listener2, listener2_queue))
        ]

        # Wait for new emails (polling interval = 5 seconds)
        await client.wait_for_updates(poll_interval=5.0)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection and cancel tasks
        for task in tasks:
            task.cancel()
        await client.close()
        print("Disconnected from the IMAP server.")

if __name__ == "__main__":
    asyncio.run(main())
