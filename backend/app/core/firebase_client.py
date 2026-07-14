"""Firebase REST API client for Firestore.

Uses standard HTTP requests instead of the heavy firebase-admin/grpcio SDK
to stay well under Vercel's 250MB Serverless Function size limit.
"""

import logging
import os
import json
from typing import Optional

logger = logging.getLogger(__name__)

_initialized = False
_project_id = None
_credentials = None


def _initialize_firebase():
    """Initialize Firebase credentials exactly once."""
    global _initialized, _project_id, _credentials
    if _initialized:
        return

    try:
        from google.oauth2 import service_account
        import google.auth
        from app.core.config import settings

        _project_id = settings.FIREBASE_PROJECT_ID

        # Determine service-account path
        sa_path: Optional[str] = settings.FIREBASE_SERVICE_ACCOUNT_PATH
        if not sa_path:
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

        if sa_path and os.path.exists(sa_path):
            _credentials = service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=["https://www.googleapis.com/auth/datastore"]
            )
            logger.info("Firebase REST initialized with service account.")
        else:
            # Fall back to ADC
            _credentials, project = google.auth.default(
                scopes=["https://www.googleapis.com/auth/datastore"]
            )
            if not _project_id:
                _project_id = project
            logger.info("Firebase REST initialized with ADC.")

        _initialized = True

    except Exception as exc:
        logger.warning(
            "Firebase REST SDK could not be initialised — Firestore writes will be skipped. "
            "Error: %s", exc
        )
        _initialized = True


class FirestoreRestClient:
    """A minimal mock of the Firestore client that uses REST."""
    def __init__(self, project_id, credentials):
        self.project_id = project_id
        self.credentials = credentials
        self._collection = None

    def collection(self, name: str):
        self._collection = name
        return self

    def document(self, doc_id: str):
        return FirestoreDocumentRef(self.project_id, self.credentials, self._collection, doc_id)


class FirestoreDocumentRef:
    def __init__(self, project_id, credentials, collection, doc_id):
        self.project_id = project_id
        self.credentials = credentials
        self.collection = collection
        self.doc_id = doc_id

    def set(self, data: dict, merge: bool = False):
        import requests
        import google.auth.transport.requests

        request = google.auth.transport.requests.Request()
        self.credentials.refresh(request)
        token = self.credentials.token

        # Convert simple dict to Firestore Document format
        # Note: This is a simplified converter covering string, int, bool, dict
        fields = {}
        for k, v in data.items():
            if isinstance(v, str):
                fields[k] = {"stringValue": v}
            elif isinstance(v, bool):
                fields[k] = {"booleanValue": v}
            elif isinstance(v, int):
                fields[k] = {"integerValue": str(v)}
            elif isinstance(v, float):
                fields[k] = {"doubleValue": v}
            elif isinstance(v, dict):
                # Only 1 level deep supported in this simple mock
                fields[k] = {"stringValue": json.dumps(v)}

        payload = {"fields": fields}
        url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents/{self.collection}/{self.doc_id}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        params = {}
        if merge:
            params["updateMask.fieldPaths"] = list(fields.keys())
            # For merge, we actually use PATCH
            res = requests.patch(url, headers=headers, params=params, json=payload, timeout=5)
        else:
            # If doc exists, this will fail unless we use PATCH without updateMask?
            # Actually, PATCH without updateMask replaces the document in REST.
            res = requests.patch(url, headers=headers, json=payload, timeout=5)

        if not res.ok:
            raise Exception(f"Firestore REST error: {res.text}")


def get_firestore():
    """Return the Firestore REST client mock, or None if Firebase is unavailable."""
    if not _initialized:
        _initialize_firebase()
    if _credentials and _project_id:
        return FirestoreRestClient(_project_id, _credentials)
    return None
