'use client';

import { useState } from 'react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { LogIn } from 'lucide-react';

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
      className={`group relative flex min-w-[200px] items-center justify-center gap-2 overflow-hidden rounded-xl px-6 py-3 shadow-lg transition-all duration-300 ${
        isLoading
          ? 'cursor-not-allowed bg-blue-300'
          : 'bg-blue-500 hover:bg-blue-600'
      }`}
    >
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-20 w-20 rotate-45 transform bg-white/10 transition-all duration-500 group-hover:scale-150"></div>
      </div>

      <div className="relative flex items-center gap-2 text-white">
        {isLoading ? (
          <>
            <LoadingSpinner size="sm" className="text-white" />
            <span>Connecting...</span>
          </>
        ) : (
          <>
            <LogIn className="h-5 w-5" />
            <span>Sign in with DocuSign</span>
          </>
        )}
      </div>
    </button>
  );
};

export { LoginButton };
