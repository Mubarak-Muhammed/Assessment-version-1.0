"""Firebase Admin SDK singleton initialiser.

Usage:
    from app.core.firebase_client import get_firestore
    db = get_firestore()
    db.collection("interactions").document(doc_id).set(data)
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_firestore_client = None
_initialized = False


def _initialize_firebase():
    """Initialize Firebase Admin SDK exactly once."""
    global _firestore_client, _initialized
    if _initialized:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        from app.core.config import settings

        # Determine service-account path:
        # 1. From settings (env var FIREBASE_SERVICE_ACCOUNT_PATH)
        # 2. Auto-detect common filename in backend folder
        sa_path: Optional[str] = settings.FIREBASE_SERVICE_ACCOUNT_PATH

        if not sa_path:
            # Try to find the JSON in the backend directory automatically
            backend_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            candidates = [
                "serviceAccountKey.json.json",
                "serviceAccountKey.json",
                "firebase-service-account.json",
            ]
            for candidate in candidates:
                full_path = os.path.join(backend_dir, candidate)
                if os.path.exists(full_path):
                    sa_path = full_path
                    logger.info("Auto-detected service account at: %s", full_path)
                    break

        if not firebase_admin._apps:
            if sa_path and os.path.exists(sa_path):
                cred = credentials.Certificate(sa_path)
                firebase_admin.initialize_app(
                    cred,
                    {"projectId": settings.FIREBASE_PROJECT_ID},
                )
                logger.info(
                    "Firebase Admin initialised with service account for project '%s'",
                    settings.FIREBASE_PROJECT_ID,
                )
            else:
                # Fall back to Application Default Credentials (ADC)
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(
                    cred,
                    {"projectId": settings.FIREBASE_PROJECT_ID},
                )
                logger.info(
                    "Firebase Admin initialised with ADC for project '%s'",
                    settings.FIREBASE_PROJECT_ID,
                )

        _firestore_client = firestore.client()
        _initialized = True

    except Exception as exc:
        logger.warning(
            "Firebase Admin SDK could not be initialised — Firestore writes will be skipped. "
            "Error: %s",
            exc,
        )
        _initialized = True  # Mark as attempted so we don't retry on every request


def get_firestore():
    """Return the Firestore client, or None if Firebase is unavailable."""
    if not _initialized:
        _initialize_firebase()
    return _firestore_client
