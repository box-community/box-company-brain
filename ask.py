import os
import sys

from dotenv import load_dotenv
from box_sdk_gen import BoxClient, CreateAiAskMode, AiItemAsk

from box_client import get_box_client

load_dotenv()


def ask_company_brain(client: BoxClient, hub_id: str, question: str):
    response = client.ai.create_ai_ask(
        mode=CreateAiAskMode.SINGLE_ITEM_QA,
        prompt=question,
        items=[AiItemAsk(type="hubs", id=hub_id)],
        include_citations=True,
    )
    return response


def main():
    client = get_box_client()

    hub_id = os.getenv("BOX_HUB_ID")
    if not hub_id:
        raise SystemExit(
            "BOX_HUB_ID is not set. Run python publish.py first, "
            "or add BOX_HUB_ID=<id> to .env."
        )

    if len(sys.argv) > 1:
        questions = [" ".join(sys.argv[1:])]
    else:
        questions = [
            "What is our approved policy for handling customer data at rest?",
            "Which security controls must a new integration pass before launch?",
        ]

    for question in questions:
        print(f"\nQ: {question}")
        response = ask_company_brain(client, hub_id, question)
        print(f"A: {response.answer}")

        if response.citations:
            print("Sources:")
            for citation in response.citations:
                print(f"  - {citation.name}")


if __name__ == "__main__":
    main()
