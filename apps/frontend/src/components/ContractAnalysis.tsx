import React, { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ProcessingModal } from './ProcessingModal';
import {
  Download,
  AlertTriangle,
  Calendar,
  Users,
  Scale,
  FileText,
  ChevronDown
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '@/components/ui/accordion';
import type {
  StoredWebhookMessage,
  ProcessingState,
  ProcessingPhase
} from '@/types/webhook';
import { DocumentDownload } from './DocumentDownload';
import UserProfile from './UserProfile ';

interface ContractsAnalysisProps {
  accountId: string;
}

interface Party {
  role: string;
  name: string;
  incorporation_country: string;
  incorporation_state: string;
}

interface Risk {
  risk_type: string;
  description: string;
  level: string;
  impact: string;
  related_clause?: string;
}

interface Obligation {
  description: string;
  due_date: string;
  recurring: boolean;
  recurrence_pattern: string;
  status: string;
  reminder_days: number;
}

interface Document {
  document_id: string;
  name: string;
  type: string;
  uri: string;
}

interface Contract {
  agreement: {
    agreement_name: string;
    agreement_type: string;
    effective_date: string;
    expiration_date: string;
    renewal_term: string;
    Notice_period_to_Terminate_Renewal: string;
    parties: Party[];
    governing_law: {
      country: string;
      state: string;
      most_favored_country: string;
    };
    risks: Risk[];
    obligations: Obligation[];
    industry_patterns: {
      industry: string;
      unusual_clauses: string[];
      common_patterns: string[];
    };
    email_subject: string;
    envelope_id: string;
    documents?: Document[];
  };
}

const ContractsAnalysis = ({ accountId }: ContractsAnalysisProps) => {
  const { token, signOut, isAuthInitialized } = useAuth();
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

  const getRiskBadgeColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'HIGH':
        return 'bg-red-100 text-red-800';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800';
      case 'LOW':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return 'bg-blue-100 text-blue-800';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'OVERDUE':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

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
      const data = await response.json(); // USER and EMAIL data

      // Set user data from the response
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
    if (documentsMap[envelopeId]) return; // Don't fetch if we already have the documents

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
    if (isAuthInitialized && token) {
      fetchContracts();
    }
  }, [isAuthInitialized]);

  const ContractContent = ({ contract }: { contract: Contract }) => (
    <div className="space-y-6 px-2 pt-4">
      {/* Key Details Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Dates Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Key Dates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Effective Date</dt>
                <dd className="font-medium">
                  {new Date(
                    contract.agreement.effective_date
                  ).toLocaleDateString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Expiration Date</dt>
                <dd className="font-medium">
                  {new Date(
                    contract.agreement.expiration_date
                  ).toLocaleDateString()}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Renewal Term</dt>
                <dd className="font-medium">
                  {contract.agreement.renewal_term}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Notice Period</dt>
                <dd className="font-medium">
                  {contract.agreement.Notice_period_to_Terminate_Renewal}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        {/* Parties Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Parties Involved
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {contract.agreement.parties.map((party, index) => (
                <div key={index} className="space-y-1">
                  <div className="font-medium">{party.role}</div>
                  <div className="text-sm text-gray-600">{party.name}</div>
                  <div className="text-xs text-gray-500">
                    {party.incorporation_state}, {party.incorporation_country}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Governing Law Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Scale className="h-5 w-5" />
              Governing Law
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-2">
              <div>
                <dt className="text-sm text-gray-500">Jurisdiction</dt>
                <dd className="font-medium">
                  {contract.agreement.governing_law.state},{' '}
                  {contract.agreement.governing_law.country}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Most Favored Country</dt>
                <dd className="font-medium">
                  {contract.agreement.governing_law.most_favored_country}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Risks Section */}
      {contract.agreement.risks && contract.agreement.risks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Risk Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {contract.agreement.risks.map((risk, index) => (
                <Alert key={index} variant="default">
                  <AlertTitle className="flex items-center justify-between">
                    <span>{risk.risk_type}</span>
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${getRiskBadgeColor(
                        risk.level
                      )}`}
                    >
                      {risk.level}
                    </span>
                  </AlertTitle>
                  <AlertDescription className="mt-2">
                    <p className="font-medium">{risk.description}</p>
                    <p className="mt-1 text-sm text-gray-600">
                      Impact: {risk.impact}
                    </p>
                    <p className="text-sm text-gray-500">
                      Related to: {risk.related_clause}
                    </p>
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Obligations Section */}
      {contract.agreement.obligations &&
        contract.agreement.obligations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Obligations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {contract.agreement.obligations.map((obligation, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-gray-200 p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <p className="font-medium">{obligation.description}</p>
                        <p className="text-sm text-gray-600">
                          Due:{' '}
                          {new Date(obligation.due_date).toLocaleDateString()}
                        </p>
                        {obligation.recurring && (
                          <p className="text-sm text-gray-600">
                            Recurs: {obligation.recurrence_pattern}
                          </p>
                        )}
                        {obligation.reminder_days > 0 && (
                          <p className="text-sm text-gray-600">
                            Reminder: {obligation.reminder_days} days before due
                            date
                          </p>
                        )}
                      </div>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${getStatusBadgeColor(
                          obligation.status
                        )}`}
                      >
                        {obligation.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

      {/* Industry Patterns */}
      <Card>
        <CardHeader>
          <CardTitle>Industry Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium">Industry</h4>
              <p className="text-gray-600">
                {contract.agreement.industry_patterns.industry}
              </p>
            </div>
            {contract.agreement.industry_patterns.unusual_clauses.length >
              0 && (
              <div>
                <h4 className="font-medium">Unusual Clauses</h4>
                <ul className="list-inside list-disc text-gray-600">
                  {contract.agreement.industry_patterns.unusual_clauses.map(
                    (clause, index) => (
                      <li key={index}>{clause}</li>
                    )
                  )}
                </ul>
              </div>
            )}
            <div>
              <h4 className="font-medium">Common Patterns</h4>
              <ul className="list-inside list-disc text-gray-600">
                {contract.agreement.industry_patterns.common_patterns.map(
                  (pattern, index) => (
                    <li key={index}>{pattern}</li>
                  )
                )}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

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
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Contract Analysis</h2>
        {userData && (
          <UserProfile
            email={userData.email}
            name={userData.name}
            onLogout={signOut}
          />
        )}
      </div>
      {!processingState.isComplete && (
        <ProcessingModal
          messages={processingState.messages}
          isComplete={processingState.isComplete}
          currentPhase={processingState.currentPhase}
          progress={processingState.progress}
        />
      )}

      {processingState.isComplete && (
        <div className="space-y-4">
          {contracts.length > 0 ? (
            <Accordion type="single" collapsible className="space-y-4">
              {contracts.map((contract) => {
                const envelopeId = contract.agreement.envelope_id;
                // Fetch documents when rendering each contract
                if (!documentsMap[envelopeId] && !loadingDocs[envelopeId]) {
                  fetchDocuments(envelopeId);
                }

                return (
                  <AccordionItem
                    key={envelopeId}
                    value={envelopeId}
                    className="rounded-lg border border-gray-200 bg-white px-6 py-4 shadow-sm transition-shadow duration-200 hover:shadow-md"
                  >
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex w-full items-center justify-between">
                        <div className="space-y-1 text-left">
                          <h3 className="text-xl font-semibold">
                            {contract.agreement.agreement_name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            Type: {contract.agreement.agreement_type} | ID:{' '}
                            {envelopeId}
                          </p>
                        </div>
                        <div className="mr-4 flex items-center">
                          {loadingDocs[envelopeId] ? (
                            <LoadingSpinner
                              size="sm"
                              className="text-blue-500"
                            />
                          ) : documentsMap[envelopeId]?.length > 0 ? (
                            <DocumentDownload
                              envelopeId={envelopeId}
                              documentId={
                                documentsMap[envelopeId][0].document_id
                              }
                              fileName={documentsMap[envelopeId][0].name}
                            />
                          ) : null}
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <ContractContent contract={contract} />
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>
          ) : (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
              <p className="text-gray-600">No analyzed contracts found</p>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default ContractsAnalysis;
