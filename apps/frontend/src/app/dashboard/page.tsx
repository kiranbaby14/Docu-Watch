'use client';

import { useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ContractsList } from '@/components/ContractsList';

export default function Dashboard() {
  const searchParams = useSearchParams();
  const { setToken, token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Get token from URL if present
    const accessToken = searchParams.get('access_token');
    if (accessToken) {
      setToken(accessToken);
      // Remove token from URL
      router.replace('/dashboard');
    } else if (!token) {
      // If no token in URL or stored, redirect to login
      router.replace('/');
    }
  }, [searchParams, setToken, router, token]);

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold">Your Documents</h1>
      <ContractsList />
    </div>
  );
}
