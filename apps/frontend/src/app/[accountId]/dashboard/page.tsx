'use client';

import { useEffect, use, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ContractsAnalysis } from '@/components/ContractAnalysis';
import { ChatInterface } from '@/components/ChatInterface ';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LayoutDashboard, MessageSquare, FileText } from 'lucide-react';
import { ProcessingModal } from '@/components/ProcessingModal';
import type { StoredWebhookMessage, ProcessingState } from '@/types/webhook';
import type { Contract, Document } from '@/types/contracts'; // You'll need to move these types to a separate file
import { UserProfile } from '@/components/UserProfile ';

const Dashboard = ({ params }: { params: Promise<{ accountId: string }> }) => {
  const resolvedParams = use(params);
  const searchParams = useSearchParams();
  const { setAuth, token, accountId, isAuthInitialized, signOut } = useAuth();
  const router = useRouter();

  // Lifted state from ContractsAnalysis
  const [userData, setUserData] = useState<{
    email: string;
    name: string;
  } | null>(null);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documentsMap, setDocumentsMap] = useState<Record<string, Document[]>>(
    {}
  );
  const [loadingDocs, setLoadingDocs] = useState<Record<string, boolean>>({});
  const [processingState, setProcessingState] = useState<ProcessingState>({
    isComplete: false,
    progress: 0,
    messages: [],
    currentPhase: 'download'
  });

  const checkProcessingStatus = async () => {
    try {
      const response = await fetch(`/api/webhook/${accountId}`);
      const messages: StoredWebhookMessage[] = await response.json();

      const currentPhase = messages[messages.length - 1]?.phase || 'download';
      const isComplete = messages.some(
        (msg) => msg.type === 'terminate' && msg.terminate === true
      );

      const progress = (() => {
        const lastMessage = messages[messages.length - 1];
        if (!lastMessage) return 0;
        if (lastMessage.type === 'batch') {
          return lastMessage.overall_progress.percentage;
        } else if (lastMessage.status === 'in_progress') {
          return lastMessage.progress.percentage;
        }
        return isComplete ? 100 : 0;
      })();

      setProcessingState({
        messages,
        isComplete,
        progress,
        currentPhase
      });

      if (isComplete) {
        await fetch(`/api/webhook/${accountId}`, { method: 'DELETE' });

        const jsonResponse = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/envelopes/json_files`,
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        const data = await jsonResponse.json();
        setContracts(data);
      } else {
        setTimeout(checkProcessingStatus, 1000);
      }
    } catch (err) {
      console.error('Error checking status:', err);
    }
  };

  const fetchContracts = async () => {
    try {
      const params = new URLSearchParams({
        webhook_url: `${window.location.origin}/api/webhook/${accountId}`
      });

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/envelopes?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );
      const data = await response.json();

      setUserData({
        email: data.email,
        name: data.name
      });

      checkProcessingStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async (envelopeId: string) => {
    if (documentsMap[envelopeId]) return;

    setLoadingDocs((prev) => ({ ...prev, [envelopeId]: true }));
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/envelopes/${envelopeId}/documents`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch documents');
      }

      const data = await response.json();
      setDocumentsMap((prev) => ({
        ...prev,
        [envelopeId]: data.documents
      }));
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoadingDocs((prev) => ({ ...prev, [envelopeId]: false }));
    }
  };

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

  useEffect(() => {
    if (isAuthInitialized && token) {
      fetchContracts();
    }
  }, [isAuthInitialized, token]);

  if (!token || !accountId) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-50 p-2">
              <FileText className="h-6 w-6 text-blue-500" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Docu Watch</h1>
          </div>
          <p className="text-sm text-gray-500">
            Analyze, manage, and track your contracts with AI-powered insights
          </p>
        </div>
        {userData && (
          <UserProfile
            email={userData.email}
            name={userData.name}
            onLogout={signOut}
          />
        )}
      </div>

      <Tabs defaultValue="dashboard" className="space-y-6">
        {!processingState.isComplete && (
          <div className="relative z-50">
            <ProcessingModal
              messages={processingState.messages}
              isComplete={processingState.isComplete}
              currentPhase={processingState.currentPhase}
              progress={processingState.progress}
            />
          </div>
        )}

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
          <ContractsAnalysis
            loading={loading}
            error={error}
            contracts={contracts}
            documentsMap={documentsMap}
            loadingDocs={loadingDocs}
            processingState={processingState}
            onFetchDocuments={fetchDocuments}
          />
        </TabsContent>

        <TabsContent value="chat" className="mt-6">
          <ChatInterface />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;
