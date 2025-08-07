import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setTokens } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const error = searchParams.get('error');

      if (error) {
        console.error('OAuth error:', error);
        navigate('/login?error=oauth_failed');
        return;
      }

      if (code) {
        try {
          // Exchange code for tokens
          const response = await fetch(`http://localhost:8000/api/auth/google/callback?code=${code}`);
          
          if (response.ok) {
            const tokens = await response.json();
            setTokens(tokens);
            navigate('/');
          } else {
            throw new Error('Failed to authenticate');
          }
        } catch (error) {
          console.error('Authentication error:', error);
          navigate('/login?error=auth_failed');
        }
      } else {
        navigate('/login?error=no_code');
      }
    };

    handleCallback();
  }, [searchParams, navigate, setTokens]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Completing sign in...</p>
      </div>
    </div>
  );
}