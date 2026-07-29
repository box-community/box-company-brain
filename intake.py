import os

from dotenv import load_dotenv
from box_sdk_gen import BoxClient, CreateFileMetadataByIdScope

from box_client import get_box_client
from review import review_file

load_dotenv()


def build_governance(review: dict) -> dict:
    """Map AI review fields to Knowledge Governance metadata keys."""
    return {
        "domain": review.get("suggested_domain", "other"),
        "owner": "unassigned",
        "status": "staged",
        "contentHealthScore": review.get("content_health_score", 0),
        "summary": review.get("summary", ""),
        "tags": review.get("suggested_tags", ""),
        "reviewNotes": review.get("review_notes", ""),
    }


def apply_governance(client: BoxClient, file_id: str, governance: dict):
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")
    client.file_metadata.create_file_metadata_by_id(
        file_id=file_id,
        scope=CreateFileMetadataByIdScope.ENTERPRISE,
        template_key=template_key,
        request_body=governance,
    )


def process_staging_folder(client: BoxClient, folder_id: str):
    items = client.folders.get_folder_items(folder_id).entries

    for item in items:
        if item.type != "file":
            continue

        print(f"\nReviewing: {item.name} ({item.id})")
        review = review_file(item.id)
        governance = build_governance(review)

        print(f"  Domain:  {governance['domain']}")
        print(f"  Health:  {governance['contentHealthScore']}")
        print(f"  Summary: {governance['summary']}")
        if governance["reviewNotes"]:
            print(f"  Notes:   {governance['reviewNotes']}")

        apply_governance(client, item.id, governance)
        print("  Governance metadata applied.")


def main():
    client = get_box_client()
    staging_folder_id = os.getenv("STAGING_FOLDER_ID")
    if not staging_folder_id:
        raise SystemExit(
            "STAGING_FOLDER_ID is not set in .env. "
            "Upload sample_content into a domain _staging folder and set its ID."
        )
    process_staging_folder(client, staging_folder_id)


if __name__ == "__main__":
    main()
