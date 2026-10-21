"""Live end-to-end test against a real Box enterprise.

Runs the tutorial flow with the repo's own functions:

1. intake.py: upload a sample policy to a temporary staging folder, run the
   Box AI review, and check the Knowledge Governance metadata.
2. publish.py: approve the file and move it to a temporary approved folder,
   then create a hub and add that folder to it.
3. ask.py: ask the permanent, already-indexed hub in BOX_HUB_ID a question and
   check the answer cites sources.
4. health.py: run the low-health metadata query.

Temporary folders sit under STAGING_FOLDER_ID, so CI files never land in the
approved folder the permanent hub indexes. The temporary folders and hub are
deleted at the end. Reads the same variables as .env.example, plus BOX_HUB_ID,
from the environment or a local .env.
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from box_sdk_gen import (  # noqa: E402
    CreateFolderParent,
    GetFileMetadataByIdScope,
    UploadFileAttributes,
    UploadFileAttributesParentField,
)

from ask import ask_company_brain  # noqa: E402
from box_client import get_box_client  # noqa: E402
from health import find_low_health_content  # noqa: E402
from intake import process_staging_folder  # noqa: E402
from publish import (  # noqa: E402
    add_folder_to_hub,
    approve_file,
    create_domain_hub,
    move_to_approved,
)

REQUIRED_ENV = [
    "BOX_CLIENT_ID",
    "BOX_CLIENT_SECRET",
    "BOX_ENTERPRISE_ID",
    "BOX_METADATA_TEMPLATE_KEY",
    "STAGING_FOLDER_ID",
    "APPROVED_FOLDER_ID",
    "DOMAIN",
    "CONTENT_OWNER",
    "BOX_HUB_ID",
]
SAMPLE = "sample_content/security/customer-data-at-rest-policy.pdf"
DOMAINS = {"security", "legal", "product", "other"}


def read_governance(client, file_id: str) -> dict:
    metadata = client.file_metadata.get_file_metadata_by_id(
        file_id,
        GetFileMetadataByIdScope.ENTERPRISE,
        os.getenv("BOX_METADATA_TEMPLATE_KEY"),
    )
    return metadata.extra_data or {}


def check_intake(client, staging_id: str, file_name: str) -> str:
    with open(SAMPLE, "rb") as sample:
        uploaded = client.uploads.upload_file(
            UploadFileAttributes(
                name=file_name, parent=UploadFileAttributesParentField(id=staging_id)
            ),
            sample,
        )
    file_id = uploaded.entries[0].id
    print(f"Uploaded {file_name} as file {file_id}")

    process_staging_folder(client, staging_id)

    governance = read_governance(client, file_id)
    assert governance.get("status") == "staged", governance
    assert governance.get("owner") == "unassigned", governance
    assert governance.get("domain") in DOMAINS, f"Unexpected domain {governance.get('domain')}"
    assert 0 <= float(governance.get("contentHealthScore", -1)) <= 100, governance
    assert governance.get("summary"), "AI review returned no summary"
    return file_id


def check_publish(client, file_id: str, approved_id: str) -> None:
    owner = os.getenv("CONTENT_OWNER")
    approve_file(client, file_id, owner)
    move_to_approved(client, file_id, approved_id)

    governance = read_governance(client, file_id)
    assert governance.get("status") == "approved", governance
    assert governance.get("owner") == owner, governance
    assert client.files.get_file_by_id(file_id).parent.id == approved_id, "File was not moved"


def check_hub(client, hub_id: str, approved_id: str) -> None:
    add_folder_to_hub(client, hub_id, approved_id)
    items = client.hub_items.get_hub_items_v2025_r0(hub_id).entries
    assert approved_id in [item.id for item in items], "Folder was not added to the hub"


def check_ask(client) -> None:
    question = "What is our approved policy for handling customer data at rest?"
    response = ask_company_brain(client, os.getenv("BOX_HUB_ID"), question)
    print(f"Q: {question}\nA: {response.answer}")
    sources = [citation.name for citation in response.citations or []]
    print(f"Sources: {sources}")
    assert response.answer, "Box AI returned no answer"
    assert any("at-rest" in name for name in sources), (
        "Answer does not cite a data-at-rest document; check the hub is indexed"
    )


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    client = get_box_client()
    run_id = os.getenv("GITHUB_RUN_ID") or f"local-{int(time.time())}"
    run_folder = client.folders.create_folder(
        f"ci-run-{run_id}", CreateFolderParent(id=os.getenv("STAGING_FOLDER_ID"))
    )
    hub_id = None

    try:
        staging = client.folders.create_folder("staging", CreateFolderParent(id=run_folder.id))
        approved = client.folders.create_folder("approved", CreateFolderParent(id=run_folder.id))

        file_id = check_intake(client, staging.id, f"ci-run-{run_id}-policy.pdf")
        check_publish(client, file_id, approved.id)

        hub_id = create_domain_hub(client, os.getenv("DOMAIN"))
        check_hub(client, hub_id, approved.id)

        check_ask(client)
        find_low_health_content(client, os.getenv("BOX_METADATA_TEMPLATE_KEY"))
        print("Live test passed")
    finally:
        if hub_id:
            client.hubs.delete_hub_by_id_v2025_r0(hub_id)
            print(f"Deleted hub {hub_id}")
        client.folders.delete_folder_by_id(run_folder.id, recursive=True)
        print(f"Deleted folder {run_folder.id}")


if __name__ == "__main__":
    main()
