'use client';
import { useRouter } from 'next/navigation';
import { createContext, useContext, useEffect, useState } from 'react';
import Cookies from 'js-cookie';

interface AuthContextType {
  token: string | null;
  accountId: string | null;
  setAuth: (token: string | null, accountId: string | null) => void;
  signOut: () => void;
  isAuthInitialized: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [isAuthInitialized, setIsAuthInitialized] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [accountId, setAccountId] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Check for token in cookie on mount
    const storedToken = Cookies.get('auth_token');
    const storedAccountId = Cookies.get('account_id');
    if (storedToken && storedAccountId) {
      setToken(storedToken);
      setAccountId(storedAccountId);
    }
    setIsAuthInitialized(true); // Mark auth as initialized
  }, []);

  const setAuth = (newToken: string | null, newAccountId: string | null) => {
    if (newToken && newAccountId) {
      // Store in cookies
      Cookies.set('auth_token', newToken, {
        expires: 7,
        sameSite: 'lax',
        path: '/'
      });
      Cookies.set('account_id', newAccountId, {
        expires: 7,
        sameSite: 'lax',
        path: '/'
      });
      setToken(newToken);
      setAccountId(newAccountId);
    } else {
      Cookies.remove('auth_token');
      Cookies.remove('account_id');
      setToken(null);
      setAccountId(null);
    }
  };

  const signOut = () => {
    // Clear cookies
    Cookies.remove('auth_token');
    Cookies.remove('account_id');

    // Clear state
    setToken(null);
    setAccountId(null);

    router.push('/');
  };

  return (
    <AuthContext.Provider
      value={{ token, accountId, setAuth, signOut, isAuthInitialized }}
    >
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export { useAuth, AuthProvider };
