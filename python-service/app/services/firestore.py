import json
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore

from app.config import settings
from app.models import StartupProfile


@lru_cache
def get_firestore_client():
    """Initialise only when server-side Firestore access is requested."""
    if not settings.firebase_service_account_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON is not configured.")
    if not firebase_admin._apps:
        service_account = json.loads(settings.firebase_service_account_json)
        firebase_admin.initialize_app(credentials.Certificate(service_account))
    return firestore.client()


def load_profile(user_id: str) -> StartupProfile:
    snapshot = get_firestore_client().collection("users").document(user_id).get()
    if not snapshot.exists:
        raise LookupError("No Firestore profile exists for this user.")
    return StartupProfile.model_validate(snapshot.to_dict())
