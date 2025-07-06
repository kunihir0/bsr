import logging
import toml
from typing import List, Optional
from pathlib import Path

from qdrant_client import QdrantClient, models

logger = logging.getLogger(__name__)

class HiveMind:
    """
    Manages the scraping queue and user data using a Qdrant database.
    """

    COLLECTION_NAME = "bluesky_users"

    def __init__(self, config_path: Path = Path("config.toml")):
        config = toml.load(config_path)
        qdrant_config = config.get("qdrant", {})
        host = qdrant_config.get("host", "localhost")
        port = qdrant_config.get("port", 6333)

        self.client = QdrantClient(host=host, port=port)
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensures the Qdrant collection for users exists."""
        try:
            self.client.get_collection(collection_name=self.COLLECTION_NAME)
            logger.info(f"Collection '{self.COLLECTION_NAME}' already exists.")
        except Exception:
            logger.info(f"Collection '{self.COLLECTION_NAME}' not found. Creating it...")
            self.client.recreate_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=models.VectorParams(size=1, distance=models.Distance.DOT),
            )

    def add_user(self, user_did: str, status: str = "queued"):
        """
        Adds a new user to the Hive Mind.

        Args:
            user_did: The decentralized identifier (DID) of the user.
            status: The initial status of the user (e.g., 'queued').
        """
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                models.PointStruct(
                    id=user_did,
                    vector=[0.0], # Dummy vector
                    payload={"did": user_did, "status": status},
                )
            ],
            wait=True,
        )
        logger.info(f"Added user '{user_did}' to the Hive Mind with status '{status}'.")

    def get_user_status(self, user_did: str) -> Optional[str]:
        """
        Retrieves the status of a specific user.

        Args:
            user_did: The DID of the user.

        Returns:
            The status of the user, or None if not found.
        """
        points = self.client.retrieve(
            collection_name=self.COLLECTION_NAME,
            ids=[user_did],
        )
        if points:
            return points[0].payload.get("status")
        return None

    def update_user_status(self, user_did: str, new_status: str):
        """
        Updates the status of a user.

        Args:
            user_did: The DID of the user to update.
            new_status: The new status to set.
        """
        self.client.set_payload(
            collection_name=self.COLLECTION_NAME,
            payload={"status": new_status},
            points=[user_did],
            wait=True,
        )
        logger.info(f"Updated user '{user_did}' to status '{new_status}'.")

    def get_users_by_status(self, status: str, limit: int = 10) -> List[str]:
        """
        Fetches a list of users with a specific status.

        Args:
            status: The status to filter by.
            limit: The maximum number of users to return.

        Returns:
            A list of user DIDs.
        """
        response = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="status",
                        match=models.MatchValue(value=status),
                    )
                ]
            ),
            limit=limit,
        )
        return [point.payload["did"] for point in response[0]]