'use client';

import { useEffect, use } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import ContractsAnalysis from '@/components/ContractAnalysis';
import ChatInterface from '@/components/ChatInterface ';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LayoutDashboard, MessageSquare } from 'lucide-react';

export default function Dashboard({
  params
}: {
  params: Promise<{ accountId: string }>;
}) {
  const resolvedParams = use(params);
  const searchParams = useSearchParams();
  const { setAuth, token, accountId, isAuthInitialized } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthInitialized) {
      const accessToken = searchParams.get('access_token');
      const urlAccountId = searchParams.get('account_id');

      if (accessToken && urlAccountId) {
        setAuth(accessToken, urlAccountId);
        router.replace(`/${urlAccountId}/dashboard`);
      } else if (!token || !accountId) {
        router.replace('/');
      } else if (accountId !== resolvedParams.accountId) {
        router.replace(`/${accountId}/dashboard`);
      }
    }
  }, [searchParams, isAuthInitialized]);

  if (!token || !accountId) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-bold">Contract Management</h1>

      <Tabs defaultValue="dashboard" className="space-y-6">
        <TabsList>
          <TabsTrigger value="dashboard" className="space-x-2">
            <LayoutDashboard className="h-4 w-4" />
            <span>Dashboard</span>
          </TabsTrigger>
          <TabsTrigger value="chat" className="space-x-2">
            <MessageSquare className="h-4 w-4" />
            <span>Chat</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="mt-6">
          <ContractsAnalysis accountId={accountId} />
        </TabsContent>

        <TabsContent value="chat" className="mt-6">
          <ChatInterface />
        </TabsContent>
      </Tabs>
    </div>
  );
}
