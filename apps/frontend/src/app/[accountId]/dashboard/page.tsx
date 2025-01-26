'use client';

import { useEffect, use } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ContractsList } from '@/components/ContractsList';

export default function Dashboard({
  params
}: {
  params: Promise<{ accountId: string }>;
}) {
  const resolvedParams = use(params);
  const searchParams = useSearchParams();
  const { setAuth, token, accountId } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Get token and accountId from URL if present
    const accessToken = searchParams.get('access_token');
    const urlAccountId = searchParams.get('account_id');

    if (accessToken && urlAccountId) {
      setAuth(accessToken, urlAccountId);
      // Remove params from URL
      router.replace(`/${urlAccountId}/dashboard`);
    } else if (!token || !accountId) {
      // If no auth info in URL or stored, redirect to login
      router.replace('/');
    } else if (accountId !== resolvedParams.accountId) {
      // If URL accountId doesn't match stored accountId, redirect to correct URL
      router.replace(`/${accountId}/dashboard`);
    }
  }, [searchParams]);

  if (!token || !accountId) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold">Your Documents</h1>
      <ContractsList accountId={accountId} />
    </div>
  );
}
