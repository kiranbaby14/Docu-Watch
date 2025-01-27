// ContractsList.tsx
import React, { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { DocumentDownload } from './DocumentDownload';
import { ProcessingModal } from './ProcessingModal';
import type {
  StoredWebhookMessage,
  ProcessingState,
  ProcessingPhase
} from '@/types/webhook';

interface ContractsListProps {
  accountId: string;
}

interface Document {
  document_id: string;
  name: string;
  type: string;
  uri: string;
}

interface Contract {
  envelope_id: string;
  status: string;
  subject: string;
  sent_date: string;
  last_modified: string;
  documents?: Document[];
}

const ContractsList = ({ accountId }: ContractsListProps) => {
  const { token, signOut } = useAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedContract, setExpandedContract] = useState<string | null>(null);
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

      // Get the current phase from the latest message
      const currentPhase = messages[messages.length - 1]?.phase || 'download';

      // Check if ALL processing is complete (graph phase is completed)
      const isComplete = messages.some(
        (msg) =>
          (msg.type === 'batch' &&
            msg.status === 'batch_completed' &&
            msg.phase === 'json_to_graph') ||
          // Check for terminate message
          (msg.type === 'terminate' && msg.terminate === true)
      );

      // Calculate progress based on latest message for current phase
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

      // If processing is complete, clear the messages for the account_id
      if (isComplete) {
        await fetch(`/api/webhook/${accountId}`, {
          method: 'DELETE'
        });
      } else {
        // If not complete, check again in 2 seconds
        setTimeout(checkProcessingStatus, 2000);
      }
    } catch (err) {
      console.error('Error checking status:', err);
    }
  };

  const fetchDocuments = async (envelopeId: string) => {
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
      setContracts(
        contracts.map((contract) =>
          contract.envelope_id === envelopeId
            ? { ...contract, documents: data.documents }
            : contract
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleExpand = async (envelopeId: string) => {
    if (expandedContract === envelopeId) {
      setExpandedContract(null);
    } else {
      setExpandedContract(envelopeId);
      const contract = contracts.find((c) => c.envelope_id === envelopeId);
      if (!contract?.documents) {
        await fetchDocuments(envelopeId);
      }
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

      if (!response.ok) {
        if (response.status === 401) {
          await signOut();
        }
        throw new Error('Failed to fetch contracts');
      }

      const data = await response.json();
      setContracts(data);
      // Start checking processing status
      checkProcessingStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchContracts();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <LoadingSpinner size="lg" className="text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
        Error: {error}
      </div>
    );
  }

  return (
    <>
      {!processingState.isComplete && (
        <ProcessingModal
          messages={processingState.messages}
          isComplete={processingState.isComplete}
          currentPhase={processingState.currentPhase}
          progress={processingState.progress}
        />
      )}

      {processingState.isComplete ? (
        <div className="grid gap-4">
          {contracts.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
              <p className="text-gray-600">No documents found</p>
            </div>
          ) : (
            contracts.map((contract) => (
              <div
                key={contract.envelope_id}
                className="rounded-lg border bg-white p-4 shadow transition-shadow hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{contract.subject}</h3>
                  <button
                    onClick={() => handleExpand(contract.envelope_id)}
                    className="rounded-full p-2 hover:bg-gray-100"
                    aria-label={
                      expandedContract === contract.envelope_id
                        ? 'Collapse'
                        : 'Expand'
                    }
                  >
                    {expandedContract === contract.envelope_id ? (
                      <ChevronUp className="h-5 w-5" />
                    ) : (
                      <ChevronDown className="h-5 w-5" />
                    )}
                  </button>
                </div>

                <div className="mt-2 text-sm text-gray-600">
                  <p>
                    Status:{' '}
                    <span className="font-medium">{contract.status}</span>
                  </p>
                  <p>
                    Sent:{' '}
                    <span className="font-medium">
                      {new Date(contract.sent_date).toLocaleDateString()}
                    </span>
                  </p>
                  <p>
                    Last Modified:{' '}
                    <span className="font-medium">
                      {new Date(contract.last_modified).toLocaleDateString()}
                    </span>
                  </p>
                </div>

                {expandedContract === contract.envelope_id && (
                  <div className="mt-4 border-t pt-4">
                    <h4 className="mb-2 font-medium">Documents</h4>
                    {contract.documents ? (
                      <div className="space-y-2">
                        {contract.documents.map((doc) => (
                          <div
                            key={doc.document_id}
                            className="flex items-center justify-between rounded-md bg-gray-50 p-2"
                          >
                            <span className="text-sm">{doc.name}</span>
                            <DocumentDownload
                              envelopeId={contract.envelope_id}
                              documentId={doc.document_id}
                              fileName={doc.name}
                            />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex justify-center py-4">
                        <LoadingSpinner size="sm" className="text-blue-500" />
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="flex min-h-[200px] items-center justify-center">
          <p className="text-gray-600">Initializing document processing...</p>
        </div>
      )}
    </>
  );
};

export { ContractsList };
