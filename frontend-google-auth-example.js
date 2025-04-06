// Google Authentication for frontend (React example)
// Install required packages:
// npm install @react-oauth/google jwt-decode axios

import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import axios from 'axios';

// Google OAuth client setup
// In your main app component or index.js:
// import { GoogleOAuthProvider } from '@react-oauth/google';
// <GoogleOAuthProvider clientId="YOUR_GOOGLE_CLIENT_ID">
//   <App />
// </GoogleOAuthProvider>

const GoogleAuthButton = () => {
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      // Send the ID token to your backend
      const response = await axios.post('http://localhost:8082/api/v1/auth/google-login', {
        id_token: credentialResponse.credential
      });
      
      // Extract tokens from the response
      const { access_token, refresh_token } = response.data;
      
      // Store tokens in localStorage or secure storage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Redirect or update UI
      console.log('Successfully logged in with Google');
      // window.location.href = '/dashboard';
    } catch (error) {
      console.error('Google login error:', error);
    }
  };

  const handleGoogleError = () => {
    console.error('Google login failed');
  };

  return (
    <div className="google-login-container">
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={handleGoogleError}
        useOneTap
        text="signin_with"
        shape="rectangular"
        theme="filled_blue"
      />
    </div>
  );
};

export default GoogleAuthButton;

// USAGE INSTRUCTIONS:
// 1. Set up a Google Cloud Platform project
// 2. Enable the Google OAuth API
// 3. Configure the OAuth consent screen
// 4. Create OAuth 2.0 credentials (web application)
// 5. Add your application's domain to the authorized JavaScript origins
// 6. Add your API endpoint URL to the authorized redirect URIs if needed
// 7. Copy the client ID to your environment variables
//    - For the backend: GOOGLE_CLIENT_ID
//    - For the frontend: Use it in the GoogleOAuthProvider