import os

from dotenv import load_dotenv
from box_sdk_gen import (
    BoxClient,
    UpdateFileMetadataByIdScope,
    UpdateFileMetadataByIdRequestBody,
    UpdateFileMetadataByIdRequestBodyOpField,
    UpdateFileByIdParent,
    FolderReferenceV2025R0,
    HubItemOperationV2025R0,
    HubItemOperationV2025R0ActionField,
)

from box_client import get_box_client

load_dotenv()


def approve_file(client: BoxClient, file_id: str, owner: str):
    template_key = os.getenv("BOX_METADATA_TEMPLATE_KEY")
    client.file_metadata.update_file_metadata_by_id(
        file_id=file_id,
        scope=UpdateFileMetadataByIdScope.ENTERPRISE,
        template_key=template_key,
        request_body=[
            UpdateFileMetadataByIdRequestBody(
                op=UpdateFileMetadataByIdRequestBodyOpField.REPLACE,
                path="/status",
                value="approved",
            ),
            UpdateFileMetadataByIdRequestBody(
                op=UpdateFileMetadataByIdRequestBodyOpField.REPLACE,
                path="/owner",
                value=owner,
            ),
        ],
    )
    print(f"Approved file {file_id}, owner set to {owner}")


def move_to_approved(client: BoxClient, file_id: str, approved_folder_id: str):
    client.files.update_file_by_id(
        file_id, parent=UpdateFileByIdParent(id=approved_folder_id)
    )
    print(f"Moved file {file_id} to approved folder {approved_folder_id}")


def create_domain_hub(client: BoxClient, domain: str) -> str:
    hub = client.hubs.create_hub_v2025_r0(
        f"{domain.title()} Knowledge Base",
        description=(
            f"Curated, approved {domain} knowledge for the company brain. "
            "Answers are grounded in reviewed, source-backed content."
        ),
    )
    print(f"Created hub: {hub.title} (ID: {hub.id})")
    return hub.id


def add_folder_to_hub(client: BoxClient, hub_id: str, folder_id: str):
    client.hub_items.manage_hub_items_v2025_r0(
        hub_id,
        operations=[
            HubItemOperationV2025R0(
                action=HubItemOperationV2025R0ActionField.ADD,
                item=FolderReferenceV2025R0(id=folder_id),
            )
        ],
    )
    print(f"Added approved folder {folder_id} to hub {hub_id}")


def _persist_env(key: str, value: str) -> None:
    """Write or update a key in .env so later scripts can reuse it."""
    env_path = ".env"
    line = f"{key}={value}\n"
    if not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(line)
        return

    with open(env_path, encoding="utf-8") as f:
        lines = f.readlines()

    updated = False
    for i, existing in enumerate(lines):
        if existing.startswith(f"{key}="):
            lines[i] = line
            updated = True
            break
    if not updated:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(line)

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    client = get_box_client()

    approved_folder_id = os.getenv("APPROVED_FOLDER_ID")
    file_id = os.getenv("FILE_ID")
    owner = os.getenv("CONTENT_OWNER", "security-team@example.com")
    domain = os.getenv("DOMAIN", "security")
    hub_id = os.getenv("BOX_HUB_ID")

    if not approved_folder_id:
        raise SystemExit("APPROVED_FOLDER_ID is not set in .env.")
    if not file_id:
        raise SystemExit(
            "FILE_ID is not set in .env. Set it to a file ID from staging "
            "(printed by intake.py)."
        )

    approve_file(client, file_id, owner)
    move_to_approved(client, file_id, approved_folder_id)

    if hub_id:
        print(f"Reusing existing hub {hub_id}")
        add_folder_to_hub(client, hub_id, approved_folder_id)
    else:
        hub_id = create_domain_hub(client, domain)
        add_folder_to_hub(client, hub_id, approved_folder_id)
        _persist_env("BOX_HUB_ID", hub_id)

    print(f"\n{domain.title()} knowledge base ready. Hub ID: {hub_id}")
    print("BOX_HUB_ID is in .env for ask.py. Wait a few minutes before querying.")


if __name__ == "__main__":
    main()
