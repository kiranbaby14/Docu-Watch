'use client';
import { LoginButton } from '@/components/LoginButton';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { token, accountId, isAuthInitialized } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthInitialized && token) {
      router.replace(`${accountId}/dashboard`);
    }
  }, [isAuthInitialized]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="mb-8 text-4xl font-bold">Docu Watch</h1>
      <LoginButton />
    </main>
  );
}
