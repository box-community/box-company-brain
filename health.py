"""Find approved content below a health threshold (tutorial keep-healthy pattern).

Usage:

    python health.py
    python health.py 70
"""

import os
import sys

from dotenv import load_dotenv
from box_sdk_gen import BoxClient

from box_client import get_box_client

load_dotenv()


def find_low_health_content(
    client: BoxClient, template_key: str, threshold: int = 60
):
    enterprise_id = os.getenv("BOX_ENTERPRISE_ID")
    ancestor = os.getenv("COMPANY_BRAIN_FOLDER_ID", "0")
    results = client.search.search_by_metadata_query(
        from_=f"enterprise_{enterprise_id}.{template_key}",
        ancestor_folder_id=ancestor,
        query="status = :status AND contentHealthScore < :score",
        query_params={"status": "approved", "score": threshold},
    )
    for entry in results.entries:
        print(f"Needs review: {entry.name} ({entry.id})")


def main():
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")
    if not template_key:
        raise SystemExit("BOX_METADATA_TEMPLATE_KEY is not set in .env.")

    threshold = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    client = get_box_client()
    find_low_health_content(client, template_key, threshold)


if __name__ == "__main__":
    main()
