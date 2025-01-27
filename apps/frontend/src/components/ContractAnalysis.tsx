import React, { useEffect } from 'react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ContractContent } from './ContractContent';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from '@/components/ui/accordion';
import type { Contract, Document } from '@/types/contracts';
import { DocumentDownload } from './DocumentDownload';

interface ContractsAnalysisProps {
  loading: boolean;
  error: string | null;
  contracts: Contract[];
  documentsMap: Record<string, Document[]>;
  loadingDocs: Record<string, boolean>;
  processingState: { isComplete: boolean }; // Only need isComplete now
  onFetchDocuments: (envelopeId: string) => Promise<void>;
}

const ContractsAnalysis: React.FC<ContractsAnalysisProps> = ({
  loading,
  error,
  contracts,
  documentsMap,
  loadingDocs,
  processingState,
  onFetchDocuments
}) => {
  // Single useEffect to handle all document fetching
  useEffect(() => {
    contracts.forEach((contract) => {
      const envelopeId = contract.agreement.envelope_id;
      if (!documentsMap[envelopeId] && !loadingDocs[envelopeId]) {
        onFetchDocuments(envelopeId);
      }
    });
  }, [contracts, documentsMap, loadingDocs, onFetchDocuments]);

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
      <h2 className="mb-6 text-xl font-semibold">Contract Analysis</h2>

      {processingState.isComplete && (
        <div className="space-y-4">
          {contracts.length > 0 ? (
            <Accordion type="single" collapsible className="space-y-4">
              {contracts.map((contract) => {
                const envelopeId = contract.agreement.envelope_id;

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

export { ContractsAnalysis };
