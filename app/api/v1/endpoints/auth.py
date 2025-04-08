from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.models.schemas.user import UserCreate, Token
from app.services.user_services import UserService
from app.core.security import create_access_token, create_refresh_token
from app.api.dependencies import get_user_service
from app.core.config import get_settings
import httpx
import logging
import os
import traceback  # ✅ Missing import added
from datetime import timedelta

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("AUTH_GOOGLE_ID")
GOOGLE_CLIENT_SECRET = os.getenv("AUTH_GOOGLE_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://playstudy.ai/api/v1/auth/google/callback")


@router.get("/google/callback", response_model=Token)
async def google_callback(
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """Handle Google OAuth callback"""
    try:
        # Extract authorization code from request
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")

        # Exchange authorization code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if token_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to exchange code")

            token_data = token_response.json()
            id_token = token_data.get("id_token")

            # Verify the ID token
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests

            try:
                id_info = google_id_token.verify_oauth2_token(
                    id_token, requests.Request(), GOOGLE_CLIENT_ID
                )
            except Exception as e:
                raise HTTPException(status_code=401, detail=f"Invalid ID token: {str(e)}")

            # Get user info from the ID token
            user_data = UserCreate(
                email=id_info.get("email"),
                name=id_info.get("name"),
                image=id_info.get("picture", None),
            )

            # Create or update user in the database
            user = await user_service.create_or_update_user(user_data)

            # Generate JWT tokens
            access_token = create_access_token(
                subject=user.id,
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            )
            refresh_token = create_refresh_token(subject=user.id)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

    except Exception as e:  # ✅ Fixed indentation
        error_message = "A server-side error occurred during the Google OAuth callback process. This may be due to invalid tokens, misconfiguration, or issues with external services."
        detailed_traceback = traceback.format_exc()

        logger.error(
            f"{error_message}\n"
            f"Exception Type: {type(e).__name__}\n"
            f"Exception Message: {str(e)}\n"
            f"Traceback:\n{detailed_traceback}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Google OAuth callback failed",
                "description": "There was an internal server error while trying to authenticate the user via Google OAuth.",
                "hint": "Ensure that the Google OAuth credentials are correctly configured and that the callback URL is properly registered in the Google Cloud Console.",
                "exception_type": type(e).__name__,
            }
        )
