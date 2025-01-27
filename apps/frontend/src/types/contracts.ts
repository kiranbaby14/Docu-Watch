import { ProcessingState } from './webhook';

export interface Party {
  role: string;
  name: string;
  incorporation_country: string;
  incorporation_state: string;
}

export interface Risk {
  risk_type: string;
  description: string;
  level: string;
  impact: string;
  related_clause?: string;
}

export interface Obligation {
  description: string;
  due_date: string;
  recurring: boolean;
  recurrence_pattern: string;
  status: string;
  reminder_days: number;
}

export interface Document {
  document_id: string;
  name: string;
  type: string;
  uri: string;
}

export interface GoverningLaw {
  country: string;
  state: string;
  most_favored_country: string;
}

export interface IndustryPatterns {
  industry: string;
  unusual_clauses: string[];
  common_patterns: string[];
}

export interface Agreement {
  agreement_name: string;
  agreement_type: string;
  effective_date: string;
  expiration_date: string;
  renewal_term: string;
  Notice_period_to_Terminate_Renewal: string;
  parties: Party[];
  governing_law: GoverningLaw;
  risks: Risk[];
  obligations: Obligation[];
  industry_patterns: IndustryPatterns;
  email_subject: string;
  envelope_id: string;
  documents?: Document[];
}

export interface Contract {
  agreement: Agreement;
}

export interface ContractAnalysisProps {
  loading: boolean;
  error: string | null;
  contracts: Contract[];
  documentsMap: Record<string, Document[]>;
  loadingDocs: Record<string, boolean>;
  processingState: ProcessingState;
  userData: UserData | null;
  onFetchDocuments: (envelopeId: string) => Promise<void>;
  onLogout: () => void;
}

export interface UserData {
  email: string;
  name: string;
}
