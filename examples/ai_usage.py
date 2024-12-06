import asyncio
import os
import openai
from bs4 import BeautifulSoup
from mailstream import MailStreamClient, Config

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


# Function to strip HTML tags
def strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


# GPT email processing
async def process_email_with_gpt(email_subject: str, email_body: str) -> str:
    prompt = f"""
    You are a job applicant managing responses from various companies regarding your job applications. 
    A new email has been received with the following details:
    
    Subject: "{email_subject}"
    Body: {email_body}

    Based on the content of this email, decide the appropriate action. Choose one of the following:
    - Reject: If the email is a rejection notice.
    - Offer Acceptance: If the email contains a job offer and requires your acceptance.
    - Interview: If the email invites you for an interview or provides scheduling details.
    - Request Information: If the email asks you to provide additional details or documents.
    - Ignore: If the email is unrelated or does not require a response.

    Respond in the following format:
    ---
    Action: <Reject/Offer Acceptance/Interview/Request Information/Ignore>
    Reason: <Brief explanation of why this action was chosen>
    Next Steps: <Optional - Describe any actions you recommend the applicant take>
    ---
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for managing job applications."},
                {"role": "user", "content": prompt},
            ],
        )
        decision = response["choices"][0]["message"]["content"]
        return decision
    except Exception as e:
        return f"Error processing email: {e}"


# Handle GPT Decisions
async def handle_decision(decision: str, email_subject: str, email_body: str) -> None:
    print(f"Processing decision for email: {email_subject}")
    print(f"GPT Decision: {decision}")
    # Further processing based on the decision can be added here


async def main():
    # Basic configuration
    config = Config(
        host="imap.example.com",
        port=993,
        email="your_email@example.com",
        password="your_password",
        debug=False,  # Set to True to enable debug logs
    )

    # Create mail client
    async with MailStreamClient(config) as client:
        # Subscribe to get real-time updates
        listener = client.subscribe()

        # Wait for new emails
        try:

            async def handle_new_mail() -> None:
                """
                Handles new incoming emails by processing them through GPT.

                Returns:
                    None
                """
                while True:
                    mail = await listener.get()

                    # Extract plain text or HTML
                    email_body = mail.plain_text or strip_html(mail.html_text) or ""
                    print(f"New Mail: {mail.subject} from {mail.from_email}")

                    # Skip if no body content
                    if not email_body.strip():
                        print("Email body is empty. Skipping...")
                        continue

                    # Pass email to GPT for processing
                    decision = await process_email_with_gpt(mail.subject, email_body)

                    # Handle the decision
                    await handle_decision(decision, mail.subject, email_body)

            # Run mail handling concurrently with updates
            await asyncio.gather(client.wait_for_updates(), handle_new_mail())
        except KeyboardInterrupt:
            print("Stopping mail listener")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
