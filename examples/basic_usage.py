import asyncio
from mailstream import MailStreamClient, Config

async def main():
    # Basic configuration
    config = Config(
        host="imap.example.com",
        port=993,
        email="your_email@example.com",
        password="your_password",
        debug=False,  # Set to True to enable debug logs
    )

    # Initialize MailStreamClient
    client = MailStreamClient(config)

    try:
        # Connect to the IMAP server
        await client.connect()
        print("Connected to the IMAP server successfully.")

        # Fetch unseen emails
        print("Fetching unseen emails...")
        async for mail in client.get_unseen_mails():
            print(f"New email from: {mail.from_email}")
            print(f"Subject: {mail.subject}")
            print(f"Date: {mail.date}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        await client.close()
        print("Disconnected from the IMAP server.")


if __name__ == "__main__":
    asyncio.run(main())
