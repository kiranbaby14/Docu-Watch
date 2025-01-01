'use client';

import { useState } from 'react';

const LoginButton = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = () => {
    setIsLoading(true);
    // Set loading state before redirect
    console.log(process.env.NEXT_PUBLIC_API_URL);

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
          <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Connecting...
        </span>
      ) : (
        'Sign in with DocuSign'
      )}
    </button>
  );
};

export { LoginButton };
