export type ProcessingPhase =
  | 'download'
  | 'pdf_to_json'
  | 'json_to_graph'
  | 'terminate';

// Common types
export type ProcessingStatus =
  | 'started'
  | 'in_progress'
  | 'completed'
  | 'error'
  | 'batch_progress'
  | 'batch_completed'
  | 'terminated';

export type ProcessingType = 'individual' | 'batch';

// Individual envelope progress types
interface IndividualProgress {
  current_document: string;
  completed: number;
  total: number;
  percentage: number;
}

// Base interface for stored messages (with timestamp)
interface StoredMessageBase {
  timestamp: string;
}

// Individual message types
export interface IndividualStartedMessage extends StoredMessageBase {
  type: 'individual';
  status: 'started';
  envelope_id: string;
  total_documents: number;
  phase: ProcessingPhase;
}

export interface IndividualProgressMessage extends StoredMessageBase {
  type: 'individual';
  status: 'in_progress';
  envelope_id: string;
  progress: IndividualProgress;
  phase: ProcessingPhase;
}

export interface IndividualCompletedMessage extends StoredMessageBase {
  type: 'individual';
  status: 'completed';
  envelope_id: string;
  files: string[];
  phase: ProcessingPhase;
}

export interface IndividualErrorMessage extends StoredMessageBase {
  type: 'individual';
  status: 'error';
  envelope_id: string;
  error: string;
  phase: ProcessingPhase;
}

// Batch progress types
interface OverallProgress {
  completed_envelopes: number;
  total_envelopes: number;
  completed_documents: number;
  total_documents: number;
  percentage: number;
}

interface EnvelopeStatus {
  total_documents: number;
  completed_documents: number;
  status: 'pending' | 'completed';
}

interface CurrentEnvelopeInfo {
  id: string;
  current_document: string;
  completed: number;
  total: number;
}

export interface BatchProgressMessage extends StoredMessageBase {
  type: 'batch';
  status: 'batch_progress';
  overall_progress: OverallProgress;
  current_envelope?: CurrentEnvelopeInfo;
  envelope_statuses: Record<string, EnvelopeStatus>;
  phase: ProcessingPhase;
}

export interface BatchCompletedMessage extends StoredMessageBase {
  type: 'batch';
  status: 'batch_completed';
  overall_progress: OverallProgress;
  envelope_statuses: Record<string, EnvelopeStatus>;
  phase: ProcessingPhase;
}

interface TerminateMessage extends StoredMessageBase {
  type: 'terminate';
  status: 'terminated';
  phase: 'terminate';
  terminate: boolean;
}

// Union type for all webhook messages
export type StoredWebhookMessage =
  | IndividualStartedMessage
  | IndividualProgressMessage
  | IndividualCompletedMessage
  | IndividualErrorMessage
  | BatchProgressMessage
  | BatchCompletedMessage
  | TerminateMessage;

// For incoming messages (without timestamp)
export type WebhookMessage = Omit<StoredWebhookMessage, 'timestamp'>;

// Type for tracking overall processing state
export interface ProcessingState {
  isComplete: boolean;
  progress: number;
  messages: StoredWebhookMessage[];
  currentPhase: ProcessingPhase;
}
