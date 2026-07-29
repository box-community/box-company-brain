import os

from dotenv import load_dotenv
from box_sdk_gen import BoxClient, BoxCCGAuth, CCGConfig

load_dotenv()


def get_box_client() -> BoxClient:
    """Authenticate as the application's Service Account using CCG.

    Share the top-level Company Brain folder with this service account
    as Editor so the app can write metadata and move approved files.
    """
    config = CCGConfig(
        client_id=os.getenv("BOX_CLIENT_ID"),
        client_secret=os.getenv("BOX_CLIENT_SECRET"),
        enterprise_id=os.getenv("BOX_ENTERPRISE_ID"),
    )
    auth = BoxCCGAuth(config=config)
    return BoxClient(auth=auth)
