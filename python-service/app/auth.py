"""Firebase ID token authentication for every automation endpoint."""

import json

import firebase_admin
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials

from app.config import settings


_bearer = HTTPBearer(auto_error=False)


def get_admin_app():
    if not settings.firebase_service_account_json:
        raise HTTPException(503, "Firebase Admin is not configured.")
    try:
        return firebase_admin.get_app()
    except ValueError:
        try:
            service_account = json.loads(settings.firebase_service_account_json)
            return firebase_admin.initialize_app(credentials.Certificate(service_account))
        except (ValueError, KeyError, TypeError) as error:
            raise HTTPException(503, "Firebase Admin credentials are invalid.") from error


def _verify_token(
    bearer: HTTPAuthorizationCredentials | None,
    *,
    check_revoked: bool = False,
) -> str:
    if bearer is None or bearer.scheme.lower() != "bearer" or not bearer.credentials:
        raise HTTPException(401, "A Firebase ID token is required.", headers={"WWW-Authenticate": "Bearer"})

    app = get_admin_app()
    try:
        claims = auth.verify_id_token(bearer.credentials, app=app, check_revoked=check_revoked)
    except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, ValueError) as error:
        raise HTTPException(401, "Your session is invalid or expired. Please sign in again.", headers={"WWW-Authenticate": "Bearer"}) from error
    except Exception as error:
        raise HTTPException(503, "Authentication service is unavailable.") from error

    uid = claims.get("uid")
    if not isinstance(uid, str) or not uid:
        raise HTTPException(401, "Your session is invalid or expired. Please sign in again.")
    if claims.get("email_verified") is not True:
        raise HTTPException(403, "Verify your email address before using grant tools.")
    return uid


def authenticated_uid(bearer: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    return _verify_token(bearer)


def authenticated_uid_for_execution(bearer: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    return _verify_token(bearer, check_revoked=True)
