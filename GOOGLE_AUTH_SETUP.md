# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for the PlayStudy.AI application.

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID for future reference

## 2. Enable the Google OAuth API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google OAuth" and select "Google OAuth API"
3. Click "Enable"

## 3. Configure the OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select the appropriate user type (External or Internal)
3. Fill in the required information:
   - App name
   - User support email
   - Developer contact information
4. Add the necessary scopes (at minimum):
   - `email`
   - `profile`
5. Add your domains to the authorized domains list
6. Click "Save and Continue"

## 4. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Enter a name for your OAuth client
5. Add authorized JavaScript origins:
   - Development: `http://localhost:3000`
   - Production: `https://yourdomain.com`
6. Add authorized redirect URIs (if needed):
   - Development: `http://localhost:3000/auth/google/callback`
   - Production: `https://yourdomain.com/auth/google/callback`
7. Click "Create"
8. Copy your Client ID and Client Secret

## 5. Update Environment Variables

### Backend

Add these environment variables to your backend configuration:

```
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

For local development, update `run_local.py`:

```python
# Add your Google OAuth credentials here
os.environ["GOOGLE_CLIENT_ID"] = "YOUR_GOOGLE_CLIENT_ID_HERE"
os.environ["GOOGLE_CLIENT_SECRET"] = "YOUR_GOOGLE_CLIENT_SECRET_HERE"
```

### Frontend

In your React application, set up the Google OAuth provider with your client ID:

```jsx
import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  return (
    <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID_HERE">
      {/* Your app components */}
    </GoogleOAuthProvider>
  );
}
```

## 6. Test Your Integration

1. Start your backend server
2. Start your frontend application
3. Try logging in with Google
4. Check the browser console and server logs for any errors

## Additional Resources

- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [React OAuth Google Library](https://github.com/MomenSherif/react-oauth/google)
- [FastAPI OAuth Documentation](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)