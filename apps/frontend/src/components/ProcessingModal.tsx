import React, { useRef, useEffect } from 'react';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { File, Check, Clock, RefreshCw, AlertTriangle } from 'lucide-react';
import type {
  StoredWebhookMessage,
  ProcessingStatus,
  ProcessingPhase
} from '@/types/webhook';

interface ProcessingModalProps {
  messages: StoredWebhookMessage[];
  isComplete: boolean;
  currentPhase: ProcessingPhase;
  progress: number;
}

export const ProcessingModal = ({
  messages,
  isComplete,
  currentPhase,
  progress
}: ProcessingModalProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getStatusIcon = (status: ProcessingStatus) => {
    switch (status) {
      case 'started':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'in_progress':
      case 'batch_progress':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
      case 'batch_completed':
        return <Check className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <File className="h-4 w-4 text-gray-500" />;
    }
  };

  const getPhaseLabel = (phase: ProcessingPhase) => {
    switch (phase) {
      case 'download':
        return 'Downloading Documents';
      case 'pdf_to_json':
        return 'Converting PDFs';
      case 'json_to_graph':
        return 'Creating Knowledge Graph';
      default:
        return 'Processing';
    }
  };

  const getPhaseColor = (phase: ProcessingPhase) => {
    switch (phase) {
      case 'download':
        return 'text-blue-700 bg-blue-100';
      case 'pdf_to_json':
        return 'text-purple-700 bg-purple-100';
      case 'json_to_graph':
        return 'text-green-700 bg-green-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const getPhaseOrder = (phase: ProcessingPhase): number => {
    const order: Record<ProcessingPhase, number> = {
      download: 1,
      pdf_to_json: 2,
      json_to_graph: 3,
      terminate: 4
    };
    return order[phase];
  };

  // const isPhaseComplete = (phase: ProcessingPhase): boolean => {
  //   return messages.some(
  //     (msg) =>
  //       msg.type === 'batch' &&
  //       msg.status === 'batch_completed' &&
  //       msg.phase === phase
  //   );
  // };

  const formatMessage = (msg: StoredWebhookMessage) => {
    const phasePrefix = `[${getPhaseLabel(msg.phase)}] `;

    if (msg.type === 'individual') {
      switch (msg.status) {
        case 'started':
          return `${phasePrefix}Started processing envelope ${msg.envelope_id} (${msg.total_documents} documents)`;
        case 'in_progress':
          return `${phasePrefix}Processing ${msg.progress.current_document} (${msg.progress.completed}/${msg.progress.total})`;
        case 'completed':
          return `${phasePrefix}Completed processing: ${msg.files.join(', ')}`;
        case 'error':
          return `${phasePrefix}Error processing envelope ${msg.envelope_id}: ${msg.error}`;
        default:
          return 'Unknown status';
      }
    } else {
      switch (msg.status) {
        case 'batch_progress':
          const currentDoc = msg.current_envelope
            ? ` - Processing ${msg.current_envelope.current_document}`
            : '';
          return `${phasePrefix}Overall progress: ${msg.overall_progress.completed_documents}/${msg.overall_progress.total_documents} documents (${msg.overall_progress.percentage}%)${currentDoc}`;
        case 'batch_completed':
          return `${phasePrefix}Completed: ${msg.overall_progress.completed_envelopes}/${msg.overall_progress.total_envelopes} envelopes processed`;
        default:
          return 'Unknown batch status';
      }
    }
  };

  const phases: ProcessingPhase[] = [
    'download',
    'pdf_to_json',
    'json_to_graph'
  ];

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/50">
      <Card className="mx-4 w-full max-w-xl bg-white shadow-xl">
        <CardHeader>
          <CardTitle className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {!isComplete ? (
                  <RefreshCw className="h-5 w-5 animate-spin text-blue-500" />
                ) : (
                  <Check className="h-5 w-5 text-green-500" />
                )}
                <span>Processing Documents</span>
              </div>
              <span className="text-lg font-semibold text-blue-600">
                {progress}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              {phases.map((phase, index) => (
                <React.Fragment key={phase}>
                  {index > 0 && <div className="h-px w-4 bg-gray-300" />}
                  <div
                    className={`flex items-center gap-2 rounded-full px-3 py-1 text-sm ${
                      phase === currentPhase
                        ? getPhaseColor(phase)
                        : getPhaseOrder(phase) < getPhaseOrder(currentPhase)
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    {getPhaseOrder(phase) < getPhaseOrder(currentPhase) && (
                      <Check className="h-4 w-4" />
                    )}
                    {phase === currentPhase && !isComplete && (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    )}
                    <span>{getPhaseLabel(phase)}</span>
                  </div>
                </React.Fragment>
              ))}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-64 rounded-md border">
            <div className="space-y-3 p-4" ref={scrollRef}>
              {messages.map((msg, index) => (
                <div key={index} className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-gray-500">
                      {formatTime(msg.timestamp)}
                    </span>
                    {getStatusIcon(msg.status)}
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        msg.type === 'batch'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {msg.type}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${getPhaseColor(msg.phase)}`}
                    >
                      {getPhaseLabel(msg.phase)}
                    </span>
                  </div>
                  <p className="pl-6 text-sm text-gray-700">
                    {formatMessage(msg)}
                  </p>
                </div>
              ))}
            </div>
          </ScrollArea>
          <div className="mt-6 space-y-2">
            <Progress value={progress} className="h-2" />
            <p className="text-center text-sm text-gray-500">
              {!isComplete
                ? `${getPhaseLabel(currentPhase)}...`
                : 'All documents have been processed successfully!'}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
