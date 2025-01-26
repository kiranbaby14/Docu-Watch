import React, { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { DocumentDownload } from './DocumentDownload';
import { useRouter } from 'next/navigation';

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

const ContractsList = () => {
  const router = useRouter();
  const { token, signOut } = useAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedContract, setExpandedContract] = useState<string | null>(null);

  const handleSessionExpired = async () => {
    await signOut();
  };

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        // Create URLSearchParams to handle query parameters
        const params = new URLSearchParams({
          webhook_url: `${window.location.origin}/api/webhook` // You'll need to create this API route
        });

        // Add any custom headers your webhook might need
        const webhookHeaders = {
          'x-custom-source': 'frontend',
          'x-client-id': 'your-client-id' // Add any necessary headers
        };

        // Encode headers as a JSON string in the query params
        params.append('webhook_headers', JSON.stringify(webhookHeaders));

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
            await handleSessionExpired();
          }
          throw new Error('Failed to fetch contracts');
        }

        const data = await response.json();
        setContracts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchContracts();
    }
  }, [token]);

  // Rest of the component remains the same
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

  if (loading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <LoadingSpinner size="lg" className="text-blue-500" />
      </div>
    );
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <div className="grid gap-4">
      {contracts.map((contract) => (
        <div
          key={contract.envelope_id}
          className="rounded-lg border p-4 shadow transition-shadow hover:shadow-md"
        >
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">{contract.subject}</h3>
            <button
              onClick={() => handleExpand(contract.envelope_id)}
              className="rounded-full p-2 hover:bg-gray-100"
            >
              {expandedContract === contract.envelope_id ? (
                <ChevronUp className="h-5 w-5" />
              ) : (
                <ChevronDown className="h-5 w-5" />
              )}
            </button>
          </div>

          <div className="mt-2 text-sm text-gray-600">
            <p>Status: {contract.status}</p>
            <p>Sent: {new Date(contract.sent_date).toLocaleDateString()}</p>
            <p>
              Last Modified:{' '}
              {new Date(contract.last_modified).toLocaleDateString()}
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
                      className="flex items-center justify-between"
                    >
                      <span>{doc.name}</span>
                      <DocumentDownload
                        envelopeId={contract.envelope_id}
                        documentId={doc.document_id}
                        fileName={doc.name}
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex justify-center">
                  <LoadingSpinner size="sm" className="text-blue-500" />
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export { ContractsList };
