'use client';

import { useState } from 'react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const LoginButton = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = () => {
    setIsLoading(true);
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/login`;
  };

  return (
    <button
      onClick={handleLogin}
      disabled={isLoading}
      className={`rounded-lg px-6 py-3 text-white ${
        isLoading
          ? 'cursor-not-allowed bg-blue-300'
          : 'bg-blue-500 hover:bg-blue-600'
      } flex min-w-[150px] items-center justify-center transition-colors duration-200`}
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <LoadingSpinner size="md" />
          Connecting...
        </span>
      ) : (
        'Sign in with DocuSign'
      )}
    </button>
  );
};

export { LoginButton };
