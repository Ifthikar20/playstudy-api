from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import get_settings
import logging
from typing import Dict, Any, Optional
from app.core.exceptions import AuthenticationException

settings = get_settings()
logger = logging.getLogger(__name__)

def verify_google_token(token: str) -> Dict[str, Any]:
    """
    Verify the Google ID token and return user information
    
    Args:
        token: The Google ID token to verify
        
    Returns:
        Dict containing the user information from the verified token
        
    Raises:
        AuthenticationException: If token verification fails
    """
    try:
        # Specify the CLIENT_ID of the app that accesses the backend
        # Using any value for request here because we're only validating the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
        
        # Or, if multiple clients access the backend server:
        # idinfo = id_token.verify_oauth2_token(token, requests.Request())
        # if idinfo['aud'] not in [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3]:
        #     raise ValueError('Could not verify audience.')
        
        # If auth request is from a domain with multiple origins:
        # if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        #     raise ValueError('Wrong issuer.')
        
        # Get the user data
        google_user = {
            "id": idinfo["sub"],
            "email": idinfo["email"],
            "name": idinfo.get("name"),
            "image": idinfo.get("picture")
        }
        
        return google_user
        
    except Exception as e:
        logger.error(f"Google token verification failed: {str(e)}")
        raise AuthenticationException("Invalid Google token")