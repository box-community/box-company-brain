from box_sdk_gen import (
    AiItemBase,
    CreateAiExtractStructuredFields,
    CreateAiExtractStructuredFieldsOptionsField,
)

from box_client import get_box_client

REVIEW_FIELDS = [
    CreateAiExtractStructuredFields(
        key="summary",
        display_name="Summary",
        type="string",
        prompt="A two to three sentence summary of what this document contains.",
    ),
    CreateAiExtractStructuredFields(
        key="suggested_domain",
        display_name="Suggested domain",
        type="enum",
        prompt="The single domain this content best belongs to.",
        options=[
            CreateAiExtractStructuredFieldsOptionsField(key="security"),
            CreateAiExtractStructuredFieldsOptionsField(key="legal"),
            CreateAiExtractStructuredFieldsOptionsField(key="product"),
            CreateAiExtractStructuredFieldsOptionsField(key="other"),
        ],
    ),
    CreateAiExtractStructuredFields(
        key="suggested_tags",
        display_name="Suggested tags",
        type="string",
        prompt="Three to six comma-separated topic tags for retrieval.",
    ),
    CreateAiExtractStructuredFields(
        key="content_health_score",
        display_name="Content health score",
        type="float",
        prompt=(
            "A score from 0 to 100 for how usable this is as trusted knowledge. "
            "Lower the score for stale dates, missing ownership, unclear status, "
            "or content that reads like an unreviewed draft."
        ),
    ),
    CreateAiExtractStructuredFields(
        key="review_notes",
        display_name="Review notes",
        type="string",
        prompt=(
            "Concise notes on any issues an owner should resolve before approval, "
            "such as missing owner, stale dates, duplicate guidance, or draft assumptions."
        ),
    ),
]


def review_file(file_id: str) -> dict:
    """Run Box AI structured extract against a fixed review schema."""
    client = get_box_client()

    response = client.ai.create_ai_extract_structured(
        items=[AiItemBase(id=file_id)],
        fields=REVIEW_FIELDS,
    )

    return response.to_dict()["answer"]
